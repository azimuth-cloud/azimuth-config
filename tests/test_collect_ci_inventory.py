import importlib.machinery
import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from openstack import exceptions

SCRIPT = Path(__file__).parents[1] / "bin" / "collect-ci-inventory"
MODULE_NAME = "collect_ci_inventory_test_module"
LOADER = importlib.machinery.SourceFileLoader(MODULE_NAME, str(SCRIPT))
SPEC = importlib.util.spec_from_loader(MODULE_NAME, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = MODULE
LOADER.exec_module(MODULE)

ConfigurationError = MODULE.ConfigurationError
InventoryCollector = MODULE.InventoryCollector

PROJECT_ID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
PROJECT_NAME = "ci-test-project"
SERVER_ID = "11111111-1111-4111-8111-111111111111"
VOLUME_ID = "22222222-2222-4222-8222-222222222222"
NETWORK_ID = "33333333-3333-4333-8333-333333333333"
SUBNET_ID = "44444444-4444-4444-8444-444444444444"
ROUTER_ID = "55555555-5555-4555-8555-555555555555"
PORT_ID = "66666666-6666-4666-8666-666666666666"
POOL_ID = "77777777-7777-4777-8777-777777777777"
MEMBER_ID = "88888888-8888-4888-8888-888888888888"
LOAD_BALANCER_ID = "99999999-9999-4999-8999-999999999999"


def make_connection():
    connection = SimpleNamespace(
        current_project_id=PROJECT_ID,
        compute=mock.Mock(),
        block_storage=mock.Mock(),
        network=mock.Mock(),
        load_balancer=mock.Mock(),
    )
    for method in ("servers", "server_groups", "keypairs"):
        getattr(connection.compute, method).return_value = []
    for method in ("volumes", "snapshots", "backups"):
        getattr(connection.block_storage, method).return_value = []
    for method in ("networks", "subnets", "routers", "ports", "security_groups", "ips"):
        getattr(connection.network, method).return_value = []
    for method in ("load_balancers", "listeners", "pools", "health_monitors", "members"):
        getattr(connection.load_balancer, method).return_value = []
    return connection


def make_collector(connection=None):
    return InventoryCollector(
        connection or make_connection(),
        expected_project_id=PROJECT_ID,
        project_name=PROJECT_NAME,
    )


def http_error(status_code):
    error = exceptions.HttpException()
    error.status_code = status_code
    return error


class QuietInventoryTestCase(unittest.TestCase):
    def setUp(self):
        self.logger_patcher = mock.patch.object(MODULE, "LOGGER")
        self.logger_mock = self.logger_patcher.start()
        self.addCleanup(self.logger_patcher.stop)


class ProjectGuardTests(QuietInventoryTestCase):
    def test_project_mismatch_stops_before_collection(self):
        connection = make_connection()
        connection.current_project_id = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        collector = make_collector(connection)

        with self.assertRaises(ConfigurationError):
            collector.validate_project()

        connection.compute.servers.assert_not_called()


class SourceContextTests(QuietInventoryTestCase):
    def test_reads_source_fields_from_their_environment_variables(self):
        environment = {
            "OS_CLOUD": "leafcloud",
            "GITHUB_EVENT_NAME": "schedule",
            "GITHUB_RUN_ATTEMPT": "2",
            "GITHUB_RUN_ID": "12345",
            "GITHUB_SHA": "abc123",
        }

        with mock.patch.dict(os.environ, environment, clear=True):
            source = MODULE.source_context()

        self.assertEqual(
            source,
            {
                "cloud": "leafcloud",
                "github_event_name": "schedule",
                "github_run_attempt": "2",
                "github_run_id": "12345",
                "github_sha": "abc123",
            },
        )


class CollectionTests(QuietInventoryTestCase):
    def test_collects_safe_dependency_records_with_read_calls_only(self):
        connection = make_connection()
        server = SimpleNamespace(
            id=SERVER_ID,
            name="test-server",
            status="ACTIVE",
            project_id=PROJECT_ID,
            key_name="azimuth-test",
            attached_volumes=[{"id": VOLUME_ID}],
            metadata={"zenith_registrar_token": "must-not-be-collected"},
        )
        connection.compute.servers.return_value = [server]
        connection.compute.get_server.return_value = server
        connection.block_storage.volumes.return_value = [
            SimpleNamespace(
                id=VOLUME_ID,
                name="test-volume",
                status="in-use",
                project_id=PROJECT_ID,
                attachments=[{"server_id": SERVER_ID}],
            )
        ]
        connection.network.ports.return_value = [
            SimpleNamespace(
                id=PORT_ID,
                name="router-port",
                status="ACTIVE",
                project_id=PROJECT_ID,
                network_id=NETWORK_ID,
                device_id=ROUTER_ID,
                device_owner="network:router_interface",
                fixed_ips=[{"subnet_id": SUBNET_ID}],
                security_group_ids=[],
            )
        ]
        pool = SimpleNamespace(id=POOL_ID, name="test-pool", project_id=PROJECT_ID, loadbalancers=[])
        connection.load_balancer.pools.return_value = [pool]
        connection.load_balancer.members.return_value = [
            SimpleNamespace(id=MEMBER_ID, name="test-member", project_id=PROJECT_ID, subnet_id=SUBNET_ID)
        ]
        collector = make_collector(connection)
        collector.validate_project()

        collector.collect_all()

        records = {(record.resource_type, record.resource_id): record for record in collector.records}
        self.assertEqual(records[("server", SERVER_ID)].relationships["volume_ids"], [VOLUME_ID])
        self.assertEqual(records[("volume", VOLUME_ID)].relationships["server_ids"], [SERVER_ID])
        self.assertEqual(records[("router_interface", PORT_ID)].relationships["router_ids"], [ROUTER_ID])
        self.assertEqual(records[("load_balancer_member", MEMBER_ID)].relationships["pool_ids"], [POOL_ID])
        self.assertEqual(collector.errors, [])
        self.assertNotIn("metadata", records[("server", SERVER_ID)].__dict__)
        connection.compute.servers.assert_called_once_with(details=False)
        connection.compute.get_server.assert_called_once_with(SERVER_ID)
        connection.compute.delete_server.assert_not_called()
        connection.block_storage.delete_volume.assert_not_called()
        connection.network.delete_port.assert_not_called()
        connection.load_balancer.delete_load_balancer.assert_not_called()
        connection.network.ports.assert_called_once_with(project_id=PROJECT_ID)
        connection.load_balancer.pools.assert_called_once_with(project_id=PROJECT_ID)

    def test_connects_octavia_port_to_load_balancer(self):
        collector = make_collector()
        port = SimpleNamespace(
            id=PORT_ID,
            name="octavia-vip-port",
            project_id=PROJECT_ID,
            device_owner="Octavia",
            device_id=f"lb-{LOAD_BALANCER_ID}",
        )

        record = collector.port_record(port)

        self.assertEqual(record.relationships["load_balancer_ids"], [LOAD_BALANCER_ID])

    def test_records_server_list_detail_mismatch(self):
        connection = make_connection()
        connection.compute.servers.return_value = [SimpleNamespace(id=SERVER_ID, name="ghost-server")]
        connection.compute.get_server.return_value = None
        collector = make_collector(connection)
        collector.validate_project()

        collector.collect_all()

        records = {(record.resource_type, record.resource_id): record for record in collector.records}
        self.assertIn(("server_detail_missing", SERVER_ID), records)
        self.assertEqual(collector.errors, [])
        connection.compute.servers.assert_called_once_with(details=False)
        connection.compute.get_server.assert_called_once_with(SERVER_ID)
        connection.compute.delete_server.assert_not_called()
        self.logger_mock.warning.assert_called_once_with(
            "Server %s (%s) was returned by list but is missing from the detail API",
            "ghost-server",
            SERVER_ID,
        )

    def test_one_service_failure_does_not_remove_other_inventory(self):
        connection = make_connection()
        server = SimpleNamespace(id=SERVER_ID, name="test-server", status="ERROR", project_id=PROJECT_ID)
        connection.compute.servers.return_value = [server]
        connection.compute.get_server.return_value = server
        connection.network.ports.side_effect = http_error(503)
        collector = make_collector(connection)
        collector.validate_project()

        collector.collect_all()

        self.assertIn(
            ("server", SERVER_ID), {(record.resource_type, record.resource_id) for record in collector.records}
        )
        self.assertEqual(len(collector.errors), 1)
        self.assertEqual(collector.errors[0].collection, "port")
        self.assertEqual(collector.errors[0].error_code, "http_503")

    def test_invalid_resource_does_not_stop_later_records(self):
        connection = make_connection()
        valid_server = SimpleNamespace(id=SERVER_ID, name="valid-server", project_id=PROJECT_ID)
        connection.compute.servers.return_value = [
            SimpleNamespace(id="", name="missing-id", project_id=PROJECT_ID),
            valid_server,
        ]
        connection.compute.get_server.return_value = valid_server
        collector = make_collector(connection)
        collector.validate_project()

        collector.collect_all()

        self.assertIn(SERVER_ID, {record.resource_id for record in collector.records})
        self.assertEqual(len(collector.errors), 1)
        self.assertEqual(collector.errors[0].collection, "server")
        self.assertEqual(collector.errors[0].error_code, "missing_id")


class OutputTests(QuietInventoryTestCase):
    def test_outputs_are_private_and_do_not_contain_omitted_metadata(self):
        secret = "must-not-be-collected"
        connection = make_connection()
        server = SimpleNamespace(
            id=SERVER_ID,
            name="=unsafe-csv-name",
            status="ACTIVE",
            project_id=PROJECT_ID,
            metadata={"zenith_registrar_token": secret},
        )
        connection.compute.servers.return_value = [server]
        connection.compute.get_server.return_value = server
        collector = make_collector(connection)
        collector.validate_project()
        collector.collect_all()

        with tempfile.TemporaryDirectory() as temporary_directory:
            previous_umask = os.umask(stat.S_IRWXG | stat.S_IRWXO)
            self.addCleanup(os.umask, previous_umask)
            output_dir = Path(temporary_directory) / "inventory"
            collector.write_outputs(
                output_dir,
                "2026-08-21T12:00:00+00:00",
                {"github_run_id": "12345", "github_run_attempt": "1", "github_sha": "abc123"},
            )
            inventory_text = (output_dir / "inventory.json").read_text(encoding="utf-8")
            inventory = json.loads(inventory_text)

            self.assertNotIn(secret, inventory_text)
            self.assertEqual(inventory["schema_version"], 1)
            self.assertEqual(inventory["records"][0]["name"], "")
            self.assertEqual(inventory["source"]["github_run_id"], "12345")
            self.assertTrue((output_dir / "inventory.csv").is_file())
            self.assertTrue((output_dir / "collection-errors.csv").is_file())
            self.assertTrue((output_dir / "summary.csv").is_file())
            self.assertEqual(stat.S_IMODE(output_dir.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE((output_dir / "inventory.json").stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
