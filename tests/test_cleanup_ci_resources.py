import importlib.machinery
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from openstack import exceptions

SCRIPT = Path(__file__).parents[1] / "bin" / "cleanup-ci-resources"
MODULE_NAME = "cleanup_ci_resources_test_module"
LOADER = importlib.machinery.SourceFileLoader(MODULE_NAME, str(SCRIPT))
SPEC = importlib.util.spec_from_loader(MODULE_NAME, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = MODULE
LOADER.exec_module(MODULE)

CleanupRunner = MODULE.CleanupRunner
ConfigurationError = MODULE.ConfigurationError
ErrorRecord = MODULE.ErrorRecord

PROJECT_ID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SERVER_ID = "11111111-1111-1111-1111-111111111111"
VOLUME_ID = "22222222-2222-2222-2222-222222222222"
CUTOFF = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def make_connection():
    return SimpleNamespace(
        current_project_id=PROJECT_ID,
        compute=mock.Mock(),
        block_storage=mock.Mock(),
    )


def make_runner(connection=None, **kwargs):
    return CleanupRunner(connection or make_connection(), cutoff=CUTOFF, **kwargs)


def http_error(status_code):
    error = exceptions.HttpException()
    error.status_code = status_code
    return error


class QuietCleanupTestCase(unittest.TestCase):
    def setUp(self):
        self.logger_patcher = mock.patch.object(MODULE, "LOGGER")
        self.logger_mock = self.logger_patcher.start()
        self.addCleanup(self.logger_patcher.stop)


class ServerCleanupTests(QuietCleanupTestCase):
    def test_list_detail_404_is_idempotent(self):
        connection = make_connection()

        def servers(*, status, **kwargs):
            del kwargs
            if status == "BUILD":
                return [SimpleNamespace(id=SERVER_ID, name="stale-build-server")]
            return []

        connection.compute.servers.side_effect = servers
        connection.compute.get_server.side_effect = exceptions.ResourceNotFound()
        runner = make_runner(connection)

        runner.cleanup_resources()

        self.assertEqual(runner.stats.servers_selected, 1)
        self.assertEqual(runner.stats.servers_already_absent, 1)
        self.assertEqual(runner.stats.errors, [])
        warning = self.logger_mock.warning.call_args
        self.assertEqual(warning.args[-1], f"stale-build-server ({SERVER_ID})")
        connection.compute.delete_server.assert_not_called()

    def test_server_list_error_is_reported(self):
        connection = make_connection()

        def servers(*, status, **kwargs):
            del kwargs
            if status == "ACTIVE":
                raise http_error(504)
            return []

        connection.compute.servers.side_effect = servers
        runner = make_runner(connection)

        runner.cleanup_resources()

        self.assertEqual(len(runner.stats.errors), 1)
        self.assertEqual(runner.stats.errors[0].operation, "list")
        self.assertEqual(runner.stats.errors[0].error_code, "http_504")

    def test_server_delete_waits_before_cleaning_volume(self):
        connection = make_connection()
        events = []
        server = SimpleNamespace(
            id=SERVER_ID,
            name="test-server",
            attached_volumes=[{"id": VOLUME_ID}],
            key_name="azimuth-test-key",
        )
        connection.compute.get_server.return_value = server
        connection.compute.delete_server.side_effect = lambda *args, **kwargs: events.append("delete_server")
        connection.compute.wait_for_delete.side_effect = lambda *args, **kwargs: events.append("wait_server")

        def get_volume(*args, **kwargs):
            del args, kwargs
            events.append("get_volume")
            if events == ["get_volume"]:
                return SimpleNamespace(id=VOLUME_ID, name="test-volume")
            raise exceptions.ResourceNotFound()

        connection.block_storage.get_volume.side_effect = get_volume
        runner = make_runner(connection)

        runner.cleanup_server(SimpleNamespace(id=SERVER_ID), "ACTIVE")
        runner.cleanup_keypairs(runner.keypairs_to_delete)

        self.assertEqual(events, ["get_volume", "delete_server", "wait_server", "get_volume"])
        self.assertEqual(runner.stats.servers_deleted, 1)
        self.assertEqual(runner.stats.volumes_already_absent, 1)
        self.logger_mock.info.assert_any_call(
            "Deleting %s server %s with %d attached volume(s)",
            "ACTIVE",
            f"test-server ({SERVER_ID})",
            1,
        )
        self.logger_mock.info.assert_any_call(
            "Volume %s is already absent",
            f"test-volume ({VOLUME_ID})",
        )
        connection.compute.delete_keypair.assert_called_once_with("azimuth-test-key", ignore_missing=True)

    def test_server_delete_failure_does_not_delete_dependants(self):
        connection = make_connection()
        server = SimpleNamespace(
            id=SERVER_ID,
            attached_volumes=[{"id": VOLUME_ID}],
            key_name="azimuth-test-key",
        )
        connection.compute.get_server.return_value = server
        connection.compute.delete_server.side_effect = http_error(500)
        runner = make_runner(connection)

        runner.cleanup_server(SimpleNamespace(id=SERVER_ID), "ERROR")

        self.assertEqual(len(runner.stats.errors), 1)
        connection.compute.wait_for_delete.assert_not_called()
        connection.block_storage.delete_volume.assert_not_called()
        self.assertEqual(runner.keypairs_to_delete, set())


class VolumeCleanupTests(QuietCleanupTestCase):
    def test_in_use_volume_is_retried_after_server_deletion(self):
        connection = make_connection()
        connection.block_storage.get_volume.side_effect = [
            SimpleNamespace(id=VOLUME_ID, status="in-use"),
            SimpleNamespace(id=VOLUME_ID, status="available"),
        ]
        sleeps = []
        runner = make_runner(connection, sleep=sleeps.append)

        runner.cleanup_volume(VOLUME_ID)

        self.assertEqual(sleeps, [2])
        self.assertEqual(connection.block_storage.get_volume.call_count, 2)
        connection.block_storage.delete_volume.assert_called_once()
        connection.block_storage.wait_for_delete.assert_called_once()
        self.assertEqual(runner.stats.volumes_deleted, 1)
        self.assertEqual(runner.stats.errors, [])

    def test_volume_delete_404_is_idempotent(self):
        connection = make_connection()
        connection.block_storage.get_volume.return_value = SimpleNamespace(id=VOLUME_ID, status="available")
        connection.block_storage.delete_volume.side_effect = exceptions.ResourceNotFound()
        runner = make_runner(connection)

        runner.cleanup_volume(VOLUME_ID)

        self.assertEqual(runner.stats.volumes_already_absent, 1)
        self.assertEqual(runner.stats.errors, [])


class KeypairCleanupTests(QuietCleanupTestCase):
    def test_only_ticket_allowlisted_keypair_names_are_deleted(self):
        connection = make_connection()
        connection.compute.keypairs.return_value = [
            SimpleNamespace(name="azimuth-good"),
            SimpleNamespace(name="packer_good"),
            SimpleNamespace(name="default"),
            SimpleNamespace(name="ssh"),
            SimpleNamespace(name="None"),
            SimpleNamespace(name="azimuth-bad\nannotation"),
        ]
        runner = make_runner(connection)

        runner.collect_all_safe_keypairs()
        runner.cleanup_keypairs(runner.keypairs_to_delete)

        deleted = {call.args[0] for call in connection.compute.delete_keypair.call_args_list}
        self.assertEqual(deleted, {"azimuth-good", "packer_good"})


class ProjectGuardTests(QuietCleanupTestCase):
    def test_expected_project_mismatch_stops_cleanup(self):
        runner = make_runner(expected_project_id="different-project")

        with self.assertRaises(ConfigurationError):
            runner.validate_project()


class SafeLoggingTests(QuietCleanupTestCase):
    def test_sdk_exception_message_is_not_logged(self):
        runner = make_runner()
        secret = "do-not-print-this-token"

        runner.record_error("list", "server", SERVER_ID, exceptions.SDKException(secret))

        output = " ".join(str(call) for call in self.logger_mock.method_calls)
        self.assertNotIn(secret, output)
        self.assertIn("SDKException", output)


class SummaryTests(QuietCleanupTestCase):
    def test_summary_uses_a_readable_list(self):
        runner = make_runner()
        runner.project_id = PROJECT_ID
        runner.stats.servers_selected = 3
        runner.stats.servers_deleted = 2
        runner.stats.servers_already_absent = 1
        runner.stats.volumes_selected = 4
        runner.stats.volumes_deleted = 3
        runner.stats.volumes_already_absent = 1
        runner.stats.keypairs_deleted = 2
        runner.stats.errors.append(ErrorRecord("delete", "volume", VOLUME_ID, "http_400"))

        summary = runner.summary_markdown()

        self.assertIn(f"- Project: `{PROJECT_ID}`", summary)
        self.assertIn("- Servers: 3 selected, 2 deleted, 1 already absent", summary)
        self.assertIn("- Volumes: 4 selected, 3 deleted, 1 already absent", summary)
        self.assertIn("- Keypairs: 2 deleted", summary)
        self.assertIn("- Errors: **1**", summary)
        self.assertIn(f"  - `delete` `volume` `{VOLUME_ID}`: `http_400`", summary)
        self.assertNotIn("| Resource |", summary)
        self.assertTrue(summary.endswith("\n"))


if __name__ == "__main__":
    unittest.main()
