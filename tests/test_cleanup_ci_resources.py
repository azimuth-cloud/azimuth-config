import importlib.machinery
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from openstack import exceptions
from openstack.block_storage.v3.volume import Volume
from openstack.network.v2.port import Port

SCRIPT = Path(__file__).parents[1] / "bin" / "cleanup-ci-resources"
MODULE_NAME = "cleanup_ci_resources_test_module"
LOADER = importlib.machinery.SourceFileLoader(MODULE_NAME, str(SCRIPT))
SPEC = importlib.util.spec_from_loader(MODULE_NAME, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = MODULE
LOADER.exec_module(MODULE)

PROJECT_ID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SERVER_ID = "11111111-1111-1111-1111-111111111111"
VOLUME_ID = "22222222-2222-2222-2222-222222222222"
FIP_ID = "33333333-3333-3333-3333-333333333333"
PORT_ID = "44444444-4444-4444-4444-444444444444"
NOW = datetime(2026, 10, 9, 12, tzinfo=timezone.utc)
OLD_TIME = (NOW - timedelta(hours=48)).isoformat()


def resource(kind, **changes):
    fields = {
        "id": {"server": SERVER_ID, "volume": VOLUME_ID, "floating_ip": FIP_ID, "port": PORT_ID}.get(kind, kind),
        "name": f"test-{kind}",
        "project_id": PROJECT_ID,
        "created_at": OLD_TIME,
        "updated_at": OLD_TIME,
    }
    fields.update(
        {
            "server": {
                "status": "ACTIVE",
                "is_locked": False,
                "task_state": None,
                "attached_volumes": [],
                "key_name": None,
                "user_id": "ci-user",
            },
            "volume": {"status": "available", "attachments": []},
            "floating_ip": {
                "status": "DOWN",
                "port_id": None,
                "router_id": None,
                "fixed_ip_address": None,
                "revision_number": 5,
            },
            "port": {
                "status": "DOWN",
                "device_id": "",
                "device_owner": "",
                "binding_host_id": "",
                "binding_profile": {},
                "binding_vif_type": "unbound",
                "fixed_ips": [],
                "security_group_ids": [],
                "network_id": "test-network",
                "revision_number": 5,
            },
            "security_group": {"security_group_rules": [], "is_shared": False, "revision_number": 5},
            "network": {"is_shared": False, "is_router_external": False, "revision_number": 5},
            "subnet": {"network_id": "test-network", "revision_number": 5},
            "router": {"routes": [], "external_gateway_info": {}, "revision_number": 5},
            "keypair": {"user_id": "ci-user", "fingerprint": "known-fingerprint"},
            "load_balancer": {
                "provisioning_status": "ACTIVE",
                "vip_port_id": "vip-port",
                "vip_subnet_id": "vip-subnet",
                "vip_network_id": "vip-network",
            },
        }.get(kind, {})
    )
    return SimpleNamespace(**{**fields, **changes})


def detach_floating_ip(floating_ip):
    floating_ip.status = "DOWN"
    floating_ip.port_id = None
    floating_ip.router_id = None
    floating_ip.fixed_ip_address = None
    floating_ip.updated_at = NOW.isoformat()
    floating_ip.revision_number += 1


def http_error(status_code):
    error = exceptions.HttpException()
    error.status_code = status_code
    return error


class CleanupTestCase(unittest.TestCase):
    def setUp(self):
        logger = mock.patch.object(MODULE, "LOGGER")
        self.logger_mock = logger.start()
        self.addCleanup(logger.stop)
        self.reset_cloud()

    def reset_cloud(self):
        self.connection = SimpleNamespace(
            current_project_id=PROJECT_ID,
            compute=mock.Mock(),
            block_storage=mock.Mock(),
            network=mock.Mock(),
            load_balancer=mock.Mock(),
        )
        self.items = {}
        self.events = []
        methods = {
            "compute": {"server": "servers", "keypair": "keypairs"},
            "block_storage": {"volume": "volumes", "snapshot": "snapshots", "backup": "backups"},
            "network": {
                "floating_ip": "ips",
                "port": "ports",
                "security_group": "security_groups",
                "router": "routers",
                "subnet": "subnets",
                "network": "networks",
            },
            "load_balancer": {
                "load_balancer": "load_balancers",
                "pool": "pools",
                "member": "members",
            },
        }
        for proxy_name, kinds in methods.items():
            proxy = getattr(self.connection, proxy_name)
            for kind, plural in kinds.items():
                self.items[kind] = {}
                getattr(proxy, plural).side_effect = lambda *args, kind=kind, **kwargs: self.listed(kind, kwargs)
                singular = "ip" if kind == "floating_ip" else kind
                getattr(proxy, f"get_{singular}").side_effect = lambda identifier, kind=kind, **kwargs: self.get(
                    kind, identifier
                )
                getattr(proxy, f"delete_{singular}").side_effect = lambda item, kind=kind, **kwargs: self.events.append(
                    f"delete:{kind}"
                )
            proxy.wait_for_delete.side_effect = self.disappears
        self.connection.network.floating_ip_port_forwardings.return_value = []
        self.connection.network.find_extension.return_value = SimpleNamespace(alias="revision-if-match")
        self.connection.compute.server_interfaces.return_value = []
        self.connection.compute.volume_attachments.side_effect = lambda server, **kwargs: [
            SimpleNamespace(id=attachment["id"], volume_id=attachment["id"], server_id=server.id)
            for attachment in self.get("server", server).attached_volumes
        ]

    def make_runner(self, **changes):
        options = {"now": NOW, "delete_resources": True, "sleep": mock.Mock()}
        return MODULE.CleanupRunner(self.connection, **{**options, **changes})

    def add(self, kind, item=None, **changes):
        item = item or resource(kind, **changes)
        self.items[kind][item.name if kind == "keypair" else item.id] = item
        return item

    def server_with_volume(self, *, volume_updated_at=OLD_TIME):
        server = self.add("server", attached_volumes=[{"id": VOLUME_ID}])
        volume = self.add(
            "volume", status="in-use", attachments=[{"server_id": server.id}], updated_at=volume_updated_at
        )
        return server, volume

    def get(self, kind, identifier):
        if not isinstance(identifier, str):
            identifier = getattr(identifier, "id", None) or identifier.name
        if identifier not in self.items[kind]:
            raise exceptions.ResourceNotFound()
        return self.items[kind][identifier]

    def listed(self, kind, query):
        selected = list(self.items[kind].values())
        for field in ("device_id", "port_id", "volume_id", "network_id", "router_id"):
            if field in query:
                selected = [item for item in selected if getattr(item, field, None) == query[field]]
        return selected

    def disappears(self, item, **kwargs):
        del kwargs
        for kind, items in self.items.items():
            for identifier, candidate in list(items.items()):
                if candidate is item:
                    self.events.append(f"wait:{kind}")
                    del items[identifier]
                    if kind == "server":
                        for attachment in item.attached_volumes:
                            volume = self.items["volume"].get(attachment["id"])
                            if volume:
                                volume.status = "available"
                                volume.attachments = []
                    return

    def assert_no_mutations(self):
        for name in ("compute", "block_storage", "network", "load_balancer"):
            calls = getattr(self.connection, name).method_calls
            self.assertEqual([call for call in calls if call[0].startswith(("delete_", "remove_", "update_"))], [])


class CiExecutionTests(CleanupTestCase):
    def test_ci_keep_list_overrides_disposable_scope(self):
        self.add("network", id="test-network", name="portal-internal")
        self.add("subnet", id="portal-subnet")
        self.add("router", id="portal-router", name="portal-router")
        for name in ("SSH", "Default", "default"):
            self.add("security_group", id=f"group-{name}", name=name)
        self.add("keypair", name="azimuth-stackhpc-large-deploy")
        self.add("keypair", name="azimuth-disposable")
        self.make_runner(delete_all_keypairs=True).run()
        self.connection.network.delete_network.assert_not_called()
        self.connection.network.delete_subnet.assert_not_called()
        self.connection.network.delete_router.assert_not_called()
        self.connection.network.delete_security_group.assert_not_called()
        self.connection.compute.delete_keypair.assert_called_once()
        self.assertEqual(self.connection.compute.delete_keypair.call_args.args[0].name, "azimuth-disposable")

    def test_copied_script_has_no_sibling_module_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "standalone-cleanup"
            shutil.copyfile(SCRIPT, target)
            result = subprocess.run(
                [sys.executable, str(target), "--help"], cwd=target.parent, check=False, capture_output=True, text=True
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--delete-resources", result.stdout)
        self.assertIn("--delete-all-keypairs", result.stdout)

    def test_missing_authenticated_project_prevents_cloud_mutations(self):
        self.connection.current_project_id = None
        with self.assertRaises(MODULE.ConfigurationError):
            self.make_runner().run()
        self.assert_no_mutations()

    def test_resource_from_another_project_is_not_deleted(self):
        self.add("server", project_id="another-project")
        self.make_runner().run()
        self.assert_no_mutations()

    def test_dry_run_issues_no_cloud_mutations(self):
        for kind in ("server", "volume", "port"):
            self.add(kind)
        self.make_runner(delete_resources=False).run()
        self.assert_no_mutations()

    def test_empty_project_is_not_repeatedly_fully_scanned(self):
        self.make_runner().run()
        for name, method in (("compute", "servers"), ("block_storage", "volumes"), ("network", "ports")):
            self.assertLessEqual(getattr(getattr(self.connection, name), method).call_count, 2)
        self.connection.compute.keypairs.assert_not_called()
        self.assert_no_mutations()

    def test_octavia_list_failure_blocks_dependent_ports_but_not_servers_or_volumes(self):
        self.add("server")
        self.add("volume")
        self.add("port")
        self.connection.load_balancer.load_balancers.side_effect = http_error(503)
        runner = self.make_runner()
        runner.run()
        self.connection.compute.delete_server.assert_called_once()
        self.connection.block_storage.delete_volume.assert_called_once()
        self.connection.network.delete_port.assert_not_called()
        self.connection.load_balancer.load_balancers.assert_called()
        self.assertTrue(
            any(error.resource_type == "load_balancer" and error.error_code == "http_503" for error in runner.errors)
        )

    def test_detail_lookup_treats_only_not_found_as_absence(self):
        runner = self.make_runner()
        for kind, proxy, method in (
            ("server", self.connection.compute, "get_server"),
            ("volume", self.connection.block_storage, "get_volume"),
            ("floating_ip", self.connection.network, "get_ip"),
        ):
            with self.subTest(resource=kind):
                lookup = getattr(proxy, method)
                lookup.side_effect = exceptions.ResourceNotFound()
                self.assertIsNone(runner.get_resource(kind, "missing-resource"))
                forbidden = http_error(403)
                lookup.side_effect = forbidden
                with self.assertRaises(exceptions.HttpException) as raised:
                    runner.get_resource(kind, "hidden-resource")
                self.assertIs(raised.exception, forbidden)


class ServerCleanupTests(CleanupTestCase):
    def test_servers_older_than_six_hours_are_selected(self):
        selected = self.add("server", updated_at=(NOW - timedelta(hours=7)).isoformat())
        self.add("server", id="young-server", updated_at=(NOW - timedelta(hours=5)).isoformat())
        runner = self.make_runner()
        runner.run()
        self.connection.compute.delete_server.assert_called_once_with(selected, ignore_missing=True)
        self.assertEqual(runner.stats["server.deleted"], 1)

    def test_error_server_age_uses_creation_time(self):
        self.add("server", status="ERROR", updated_at=NOW.isoformat())
        self.make_runner().run()
        self.connection.compute.delete_server.assert_called_once()

    def test_list_detail_404_is_idempotent(self):
        self.add("server")
        self.connection.compute.get_server.side_effect = exceptions.ResourceNotFound()
        runner = self.make_runner()
        runner.run()
        self.connection.compute.delete_server.assert_not_called()
        self.assertEqual(runner.errors, [])

    def test_locked_server_is_preserved(self):
        self.add("server", is_locked=True)
        self.make_runner().run()
        self.connection.compute.delete_server.assert_not_called()

    def test_server_changes_are_rechecked_before_delete(self):
        for changes in ({"is_locked": True}, {"updated_at": NOW.isoformat()}):
            with self.subTest(changes=changes):
                self.reset_cloud()
                old = self.add("server")
                self.connection.compute.get_server.side_effect = [old, resource("server", **changes)]
                self.make_runner().run()
                self.connection.compute.delete_server.assert_not_called()
                self.connection.compute.wait_for_delete.assert_not_called()

    def test_confirmed_server_deletion_precedes_volume_delete(self):
        self.server_with_volume()
        self.make_runner().run()
        self.assertIn("wait:server", self.events)
        self.assertIn("delete:volume", self.events)
        self.assertLess(self.events.index("wait:server"), self.events.index("delete:volume"))

    def test_failed_server_delete_preserves_dependants(self):
        self.server_with_volume()
        self.connection.compute.delete_server.side_effect = http_error(500)
        runner = self.make_runner()
        runner.run()
        self.connection.compute.wait_for_delete.assert_not_called()
        self.connection.block_storage.delete_volume.assert_not_called()
        self.assertTrue(runner.errors)

    def test_final_server_timeout_is_bounded_and_preserves_volume(self):
        self.server_with_volume()
        self.connection.compute.wait_for_delete.side_effect = exceptions.ResourceTimeout()
        runner = self.make_runner()
        runner.run()
        self.assertEqual(self.connection.compute.delete_server.call_count, 2)
        self.connection.block_storage.delete_volume.assert_not_called()
        self.assertTrue(runner.errors)

    def test_retry_keeps_volumes_seen_before_attachments_change(self):
        server, first = self.server_with_volume(volume_updated_at=NOW.isoformat())
        second = self.add(
            "volume",
            id="second-volume",
            status="in-use",
            attachments=[{"server_id": SERVER_ID}],
            updated_at=NOW.isoformat(),
        )
        attempts = 0

        def wait(item, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                first.status, first.attachments = "available", []
                server.attached_volumes = [{"id": second.id}]
                server.updated_at = NOW.isoformat()
                raise exceptions.ResourceTimeout()
            self.disappears(item, **kwargs)

        self.connection.compute.wait_for_delete.side_effect = wait
        runner = self.make_runner()
        runner.run()
        self.assertEqual(self.connection.compute.delete_server.call_count, 2)
        self.assertEqual(
            {call.args[0].id for call in self.connection.block_storage.delete_volume.call_args_list},
            {first.id, second.id},
        )
        self.assertEqual(runner.errors, [])

    def test_failed_server_followups_do_not_leak_into_the_next_server_cleanup(self):
        failed, preserved = self.server_with_volume(volume_updated_at=NOW.isoformat())
        completed = self.add("server", id="second-server", attached_volumes=[{"id": "second-volume"}])
        removed = self.add(
            "volume",
            id="second-volume",
            status="in-use",
            attachments=[{"server_id": completed.id}],
            updated_at=NOW.isoformat(),
        )

        def wait(item, **kwargs):
            if item is failed:
                preserved.status, preserved.attachments = "available", []
                failed.attached_volumes = []
                failed.updated_at = NOW.isoformat()
                raise exceptions.ResourceTimeout()
            self.disappears(item, **kwargs)

        self.connection.compute.wait_for_delete.side_effect = wait
        runner = self.make_runner()
        runner.run()
        self.connection.block_storage.delete_volume.assert_called_once_with(removed, ignore_missing=True)
        self.assertIn(failed.id, self.items["server"])
        self.assertIn(preserved.id, self.items["volume"])
        self.assertTrue(runner.errors)

    def test_server_disappearing_between_retries_still_releases_its_dependants(self):
        server, volume = self.server_with_volume(volume_updated_at=NOW.isoformat())
        port = self.add("port", status="ACTIVE", device_owner="compute:nova", device_id=server.id)
        ip = self.add("floating_ip", status="ACTIVE", port_id=port.id, fixed_ip_address="192.0.2.5")
        self.connection.compute.wait_for_delete.side_effect = exceptions.ResourceTimeout()
        runner = self.make_runner()

        def concurrent_teardown(_delay):
            self.disappears(server)
            detach_floating_ip(ip)

        runner.sleep.side_effect = concurrent_teardown
        runner.run()
        self.connection.compute.delete_server.assert_called_once()
        self.connection.block_storage.delete_volume.assert_called_once_with(volume, ignore_missing=True)
        self.connection.network.delete_ip.assert_called_once_with(ip, ignore_missing=True, if_revision=6)
        self.assertEqual(runner.stats["server.absent"], 1)
        self.assertEqual(runner.errors, [])

    def test_server_disappearing_at_retry_final_recheck_still_releases_its_dependants(self):
        server, volume = self.server_with_volume(volume_updated_at=NOW.isoformat())
        port = self.add("port", status="ACTIVE", device_owner="compute:nova", device_id=server.id)
        ip = self.add("floating_ip", status="ACTIVE", port_id=port.id, fixed_ip_address="192.0.2.5")
        self.connection.compute.wait_for_delete.side_effect = exceptions.ResourceTimeout()
        reads = 0

        def get_server(identifier):
            nonlocal reads
            reads += 1
            if reads == 5:
                self.disappears(server)
                detach_floating_ip(ip)
            return self.get("server", identifier)

        self.connection.compute.get_server.side_effect = get_server
        runner = self.make_runner()
        runner.run()
        self.connection.compute.delete_server.assert_called_once()
        self.connection.block_storage.delete_volume.assert_called_once_with(volume, ignore_missing=True)
        self.connection.network.delete_ip.assert_called_once_with(ip, ignore_missing=True, if_revision=6)
        self.assertEqual(runner.stats["server.absent"], 1)
        self.assertEqual(runner.stats["server.deleted"], 0)
        self.assertEqual(runner.errors, [])

    def test_accepted_delete_retries_after_timestamp_change_but_stops_for_new_lock(self):
        for locked in (False, True):
            with self.subTest(newly_locked=locked):
                self.reset_cloud()
                server, _ = self.server_with_volume(volume_updated_at=NOW.isoformat())
                server.fault = {"code": 500, "message": "MessagingTimeout", "details": "secret-token"}
                attempts = 0

                def wait(item, server=server, locked=locked, **kwargs):
                    nonlocal attempts
                    attempts += 1
                    if attempts == 1:
                        server.updated_at = NOW.isoformat()
                        server.is_locked = locked
                        raise exceptions.ResourceTimeout("secret-token")
                    self.disappears(item, **kwargs)

                self.connection.compute.wait_for_delete.side_effect = wait
                runner = self.make_runner()
                runner.run()
                self.assertEqual(self.connection.compute.delete_server.call_count, 1 if locked else 2)
                self.assertEqual(self.connection.block_storage.delete_volume.call_count, 0 if locked else 1)
                self.assertEqual(runner.stats["server.deleted"], int(not locked))
                self.assertTrue(
                    all("force" not in call.kwargs for call in self.connection.compute.delete_server.call_args_list)
                )
                self.assertNotIn("secret-token", " ".join(str(call) for call in self.logger_mock.method_calls))


class DependencyTests(CleanupTestCase):
    def test_available_volume_with_nova_reference_is_not_deleted(self):
        self.add("server", updated_at=NOW.isoformat(), attached_volumes=[{"id": VOLUME_ID}])
        self.add("volume")
        self.make_runner().run()
        self.connection.block_storage.delete_volume.assert_not_called()

    def test_volume_snapshot_reference_prevents_delete(self):
        self.add("volume")
        self.add("snapshot", volume_id=VOLUME_ID)
        self.make_runner().run()
        self.connection.block_storage.delete_volume.assert_not_called()

    def test_unknown_cinder_attachments_are_not_treated_as_empty(self):
        item = Volume.existing(
            id=VOLUME_ID,
            status="available",
            created_at=OLD_TIME,
            updated_at=OLD_TIME,
            **{"os-vol-tenant-attr:tenant_id": PROJECT_ID},
        )
        self.add("volume", item)
        self.make_runner().run()
        self.connection.block_storage.delete_volume.assert_not_called()

    def test_backup_api_failure_blocks_volume_but_not_server(self):
        self.add("server")
        self.add("volume")
        self.connection.block_storage.backups.side_effect = http_error(403)
        runner = self.make_runner()
        runner.run()
        self.connection.compute.delete_server.assert_called_once()
        self.connection.block_storage.delete_volume.assert_not_called()
        self.assertTrue(runner.errors)

    def test_fip_referenced_port_without_conditional_delete_support_is_preserved(self):
        self.add("port")
        self.add("floating_ip", status="ACTIVE", port_id=PORT_ID, fixed_ip_address="192.0.2.1")
        self.connection.network.find_extension.return_value = None
        self.make_runner().run()
        self.connection.network.delete_port.assert_not_called()
        self.connection.network.delete_ip.assert_not_called()

    def test_service_owned_port_is_not_deleted_as_an_orphan(self):
        self.add("port", device_owner="network:ha_router_replicated_interface", device_id="router-id")
        self.make_runner().run()
        self.connection.network.delete_port.assert_not_called()

    def test_unknown_port_binding_is_not_treated_as_unbound(self):
        item = Port.existing(
            id=PORT_ID,
            project_id=PROJECT_ID,
            status="DOWN",
            device_owner="",
            device_id="",
            created_at=OLD_TIME,
            updated_at=OLD_TIME,
        )
        self.add("port", item)
        self.make_runner().run()
        self.connection.network.delete_port.assert_not_called()

    def test_old_unassociated_floating_ip_is_released(self):
        for status in ("DOWN", "ERROR"):
            with self.subTest(status=status):
                self.reset_cloud()
                ip = self.add("floating_ip", status=status)
                self.make_runner().run()
                self.connection.network.delete_ip.assert_called_once_with(ip, ignore_missing=True, if_revision=5)

    def test_neutron_resources_without_integer_revision_are_preserved(self):
        for kind in ("floating_ip", "port", "security_group", "router", "subnet", "network"):
            for revision in (None, "5", True, 5.0):
                with self.subTest(resource=kind, revision=revision):
                    self.reset_cloud()
                    item = self.add(kind, revision_number=revision)
                    if kind == "subnet":
                        self.add("network", id=item.network_id)
                    self.make_runner().cleanup_one(kind, item)
                    self.assert_no_mutations()

    def test_neutron_deletion_requires_conditional_delete_support(self):
        self.add("floating_ip")
        self.add("port")
        self.connection.network.find_extension.return_value = None
        self.make_runner().run()
        self.assert_no_mutations()

    def test_failed_revision_support_lookup_is_reported_without_deleting(self):
        self.add("floating_ip")
        self.add("port")
        self.connection.network.find_extension.side_effect = http_error(403)
        runner = self.make_runner()
        runner.run()
        self.assert_no_mutations()
        self.assertTrue(runner.errors)

    def test_idle_unreferenced_port_can_be_deleted(self):
        for fields in (
            {},
            {"allowed_address_pairs": [{"ip_address": "192.0.2.10"}]},
            {"resource_request": {"resources": {"NET_BW_EGR_KILOBIT_PER_SEC": 1000}}},
            {"fixed_ips": None},
        ):
            with self.subTest(fields=fields):
                self.reset_cloud()
                port = self.add("port", **fields)
                self.make_runner().run()
                self.connection.network.delete_port.assert_called_once_with(port, ignore_missing=True, if_revision=5)

    def test_port_binding_or_trunk_membership_prevents_orphan_deletion(self):
        for fields in (
            {"binding_host_id": "compute-host"},
            {"binding_profile": {"allocation": "placement-resource-provider"}},
            {"binding_vif_type": "ovs"},
            {"trunk_details": {"trunk_id": "trunk-id"}},
        ):
            with self.subTest(fields=fields):
                self.reset_cloud()
                self.add("port", allowed_address_pairs=[{"ip_address": "192.0.2.10"}], **fields)
                self.make_runner().run()
                self.connection.network.delete_port.assert_not_called()

    def test_nova_interface_reference_blocks_ownerless_port_deletion(self):
        self.add("port")
        self.add("server", updated_at=NOW.isoformat())
        self.connection.compute.server_interfaces.return_value = [SimpleNamespace(port_id=PORT_ID)]
        self.make_runner().run()
        self.connection.network.delete_port.assert_not_called()

    def test_forwarding_reference_blocks_port_deletion(self):
        self.add("port")
        self.add("floating_ip")
        self.connection.network.floating_ip_port_forwardings.return_value = [SimpleNamespace(internal_port_id=PORT_ID)]
        self.make_runner().run()
        self.connection.network.delete_port.assert_not_called()

    def test_forwarding_read_failure_blocks_fip_but_not_server(self):
        self.add("server")
        self.add("floating_ip")
        self.connection.network.floating_ip_port_forwardings.side_effect = http_error(403)
        runner = self.make_runner()
        runner.run()
        self.connection.compute.delete_server.assert_called_once()
        self.connection.network.delete_ip.assert_not_called()
        self.assertTrue(runner.errors)

    def test_freshly_detached_old_floating_ip_is_preserved(self):
        self.add("floating_ip", updated_at=NOW.isoformat())
        self.make_runner().run()
        self.connection.network.delete_ip.assert_not_called()

    def test_security_group_referenced_by_port_is_preserved(self):
        self.add("security_group", id="group-id")
        self.add(
            "port", status="ACTIVE", device_owner="compute:nova", device_id="server-id", security_group_ids=["group-id"]
        )
        self.make_runner().run()
        self.connection.network.delete_security_group.assert_not_called()

    def test_security_group_rules_only_block_deletion_for_other_groups(self):
        for own_rules, other_rules, delete in (
            (None, [], True),
            ([{"remote_group_id": "group-id"}], [], True),
            ([], None, False),
            ([], [{"remote_group_id": "group-id"}], False),
        ):
            with self.subTest(own_rules=own_rules, other_rules=other_rules):
                self.reset_cloud()
                group = self.add("security_group", id="group-id", security_group_rules=own_rules)
                self.add(
                    "security_group", id="other-group", security_group_rules=other_rules, updated_at=NOW.isoformat()
                )
                self.make_runner().run()
                self.assertEqual(self.connection.network.delete_security_group.call_count, int(delete))
                if delete:
                    self.connection.network.delete_security_group.assert_called_once_with(
                        group, ignore_missing=True, if_revision=5
                    )

    def test_shared_network_is_preserved(self):
        self.add("network", is_shared=True)
        self.make_runner().run()
        self.connection.network.delete_network.assert_not_called()

    def test_router_interface_removed_before_router_subnet_and_network(self):
        self.add("network", id="test-network")
        self.add("subnet", id="test-subnet")
        self.add("router", id="test-router")
        self.add(
            "port",
            device_owner="network:ha_router_replicated_interface",
            device_id="test-router",
            fixed_ips=[{"ip_address": "192.0.2.1", "subnet_id": "test-subnet"}],
        )
        self.make_runner().run()
        self.connection.network.remove_interface_from_router.assert_called_once()
        self.connection.network.delete_port.assert_not_called()
        self.connection.network.delete_router.assert_called_once()
        self.connection.network.delete_subnet.assert_called_once()
        self.connection.network.delete_network.assert_called_once()
        self.assertLess(self.events.index("delete:router"), self.events.index("delete:subnet"))
        self.assertLess(self.events.index("delete:subnet"), self.events.index("delete:network"))

    def test_protected_subnet_blocks_router_interface_removal(self):
        self.add("network", id="test-network", name="portal-internal")
        self.add("subnet", id="test-subnet")
        self.add("router", id="test-router")
        self.add(
            "port",
            device_owner="network:ha_router_replicated_interface",
            device_id="test-router",
            fixed_ips=[{"ip_address": "192.0.2.1", "subnet_id": "test-subnet"}],
        )
        self.make_runner().run()
        self.connection.network.remove_interface_from_router.assert_not_called()
        self.connection.network.delete_router.assert_not_called()

    def test_router_interface_without_subnet_identity_is_preserved(self):
        for fixed_ips in (None, [], [{"ip_address": "192.0.2.1"}]):
            with self.subTest(fixed_ips=fixed_ips):
                self.reset_cloud()
                self.add("router", id="test-router")
                self.add(
                    "port",
                    device_owner="network:ha_router_replicated_interface",
                    device_id="test-router",
                    fixed_ips=fixed_ips,
                )
                self.make_runner().run()
                self.connection.network.remove_interface_from_router.assert_not_called()
                self.connection.network.delete_router.assert_not_called()


class LoadBalancerTests(CleanupTestCase):
    def load_balancer_with_member(self, **changes):
        lb = self.add("load_balancer")
        self.add("pool", loadbalancers=[{"id": lb.id}])
        self.add("member", **{"address": "192.0.2.5", "subnet_id": None, **changes})
        return lb

    def test_empty_load_balancer_uses_parent_cascade(self):
        self.add("load_balancer")
        self.make_runner().run()
        self.connection.load_balancer.delete_load_balancer.assert_called_once()
        self.assertTrue(self.connection.load_balancer.delete_load_balancer.call_args.kwargs.get("cascade"))
        self.connection.load_balancer.delete_pool.assert_not_called()
        self.connection.load_balancer.delete_listener.assert_not_called()
        self.connection.load_balancer.listeners.assert_not_called()
        self.connection.load_balancer.get_health_monitor.assert_not_called()

    def test_load_balancer_with_active_backend_is_preserved(self):
        self.load_balancer_with_member(subnet_id="backend-subnet")
        self.add(
            "port",
            status="ACTIVE",
            device_owner="compute:nova",
            device_id="live-server",
            fixed_ips=[{"ip_address": "192.0.2.5", "subnet_id": "backend-subnet"}],
        )
        self.make_runner().run()
        self.connection.load_balancer.delete_load_balancer.assert_not_called()

    def test_missing_member_subnet_does_not_block_unrelated_port(self):
        self.load_balancer_with_member()
        self.add("port", fixed_ips=[{"ip_address": "192.0.2.8", "subnet_id": "other-subnet"}])

        self.make_runner().run()

        self.connection.network.delete_port.assert_called_once()
        self.connection.load_balancer.delete_load_balancer.assert_not_called()

    def test_backend_port_reference_does_not_require_matching_member_subnet(self):
        for member_subnet in (None, "different-access-subnet"):
            with self.subTest(member_subnet=member_subnet):
                self.reset_cloud()
                self.load_balancer_with_member(subnet_id=member_subnet)
                port = self.add("port", fixed_ips=[{"ip_address": "192.0.2.5", "subnet_id": "backend-subnet"}])

                self.make_runner().cleanup_one("port", port)

                self.connection.network.delete_port.assert_not_called()

    def test_idle_backend_without_member_subnet_allows_cascade(self):
        lb = self.load_balancer_with_member()
        self.add("port", fixed_ips=[{"ip_address": "192.0.2.5", "subnet_id": "backend-subnet"}])

        self.make_runner().cleanup_one("load_balancer", lb)

        self.connection.load_balancer.delete_load_balancer.assert_called_once_with(
            lb, ignore_missing=True, cascade=True
        )

    def test_nova_reference_prevents_cascade_for_idle_backend(self):
        lb = self.load_balancer_with_member()
        self.add("port", fixed_ips=[{"ip_address": "192.0.2.5", "subnet_id": "backend-subnet"}])
        self.add("server", updated_at=NOW.isoformat())
        self.connection.compute.server_interfaces.return_value = [SimpleNamespace(port_id=PORT_ID)]

        self.make_runner().cleanup_one("load_balancer", lb)

        self.connection.load_balancer.delete_load_balancer.assert_not_called()

    def test_unmatched_member_endpoint_preserves_load_balancer(self):
        for field in ("address", "monitor_address"):
            with self.subTest(field=field):
                self.reset_cloud()
                lb = self.load_balancer_with_member(**{field: "203.0.113.5", "subnet_id": "access-subnet"})
                if field == "monitor_address":
                    self.add("port", fixed_ips=[{"ip_address": "192.0.2.5", "subnet_id": "backend-subnet"}])
                self.make_runner().cleanup_one("load_balancer", lb)
                self.connection.load_balancer.delete_load_balancer.assert_not_called()

    def test_duplicate_address_on_active_port_in_other_network_blocks_cascade(self):
        lb = self.load_balancer_with_member()
        self.add("port", fixed_ips=[{"ip_address": "192.0.2.5", "subnet_id": "backend-subnet"}])
        self.add(
            "port",
            id="other-port",
            network_id="other-network",
            status="ACTIVE",
            device_owner="compute:nova",
            device_id="other-server",
            fixed_ips=[{"ip_address": "192.0.2.5", "subnet_id": "other-subnet"}],
        )

        self.make_runner().cleanup_one("load_balancer", lb)

        self.connection.load_balancer.delete_load_balancer.assert_not_called()

    def test_missing_member_address_keeps_port_and_load_balancer(self):
        self.load_balancer_with_member(address=None)
        self.add("port", fixed_ips=[{"ip_address": "192.0.2.8", "subnet_id": "backend-subnet"}])

        self.make_runner().run()

        self.connection.network.delete_port.assert_not_called()
        self.connection.load_balancer.delete_load_balancer.assert_not_called()

    def test_monitor_address_reference_is_protected_and_normalized(self):
        self.load_balancer_with_member(monitor_address="2001:0db8:0:0:0:0:0:5")
        port = self.add("port", fixed_ips=[{"ip_address": "2001:db8::5", "subnet_id": "monitor-subnet"}])

        self.make_runner().cleanup_one("port", port)

        self.connection.network.delete_port.assert_not_called()

    def test_unknown_port_addresses_cannot_establish_unused_backend(self):
        lb = self.load_balancer_with_member()
        self.add("port", fixed_ips=None)

        self.make_runner().cleanup_one("load_balancer", lb)

        self.connection.load_balancer.delete_load_balancer.assert_not_called()

    def test_malformed_addresses_preserve_load_balancer_and_port(self):
        # ipaddress accepts integers and booleans, but OpenStack address fields must be strings.
        for field in ("address", "monitor_address", "fixed_ip"):
            for value, valid_address in (
                (3221225989, "192.0.2.5"),
                (True, "0.0.0.1"),
                (False, "0.0.0.0"),
                ("not-an-ip", "192.0.2.5"),
            ):
                with self.subTest(field=field, value=value):
                    self.reset_cloud()
                    member_fields = {"address": valid_address}
                    if field != "fixed_ip":
                        member_fields[field] = value
                    self.load_balancer_with_member(**member_fields)
                    self.add(
                        "port",
                        fixed_ips=[
                            {
                                "ip_address": value if field == "fixed_ip" else valid_address,
                                "subnet_id": "backend-subnet",
                            }
                        ],
                    )

                    self.make_runner().run()

                    self.connection.load_balancer.delete_load_balancer.assert_not_called()
                    self.connection.network.delete_port.assert_not_called()

    def test_subnet_clearance_uses_access_subnet_and_backend_address(self):
        cases = (
            ("unrelated subnet", {}, "other-subnet", "198.51.100.0/24", True),
            (
                "routed access subnet",
                {"address": "203.0.113.5", "subnet_id": "access-subnet"},
                "access-subnet",
                "192.0.2.0/24",
                False,
            ),
            ("default VIP access subnet", {}, "vip-subnet", "198.51.100.0/24", False),
            ("backend subnet without port", {"subnet_id": "access-subnet"}, "backend-subnet", "192.0.2.0/24", False),
            ("unknown subnet CIDR", {}, "other-subnet", None, False),
            ("unknown member address", {"address": None}, "other-subnet", "198.51.100.0/24", False),
        )
        for name, member_fields, subnet_id, cidr, expected in cases:
            with self.subTest(case=name):
                self.reset_cloud()
                self.load_balancer_with_member(**member_fields)
                subnet = resource("subnet", id=subnet_id, cidr=cidr)

                self.assertEqual(self.make_runner().subnet_clear(subnet), expected)


class FloatingIpReleaseTests(CleanupTestCase):
    def parent_with_fip(self, kind):
        parent = self.add(kind)
        port_id = PORT_ID if kind == "server" else parent.vip_port_id
        self.add(
            "port",
            id=port_id,
            status="ACTIVE",
            device_id=parent.id if kind == "server" else f"lb-{parent.id}",
            device_owner="compute:nova" if kind == "server" else "Octavia",
        )
        floating_ip = self.add(
            "floating_ip", status="ACTIVE", port_id=port_id, router_id="router-id", fixed_ip_address="192.0.2.5"
        )
        return parent, floating_ip

    def test_parent_fip_is_released_after_confirmed_deletion(self):
        for kind in ("server", "load_balancer"):
            with self.subTest(parent=kind):
                self.reset_cloud()
                parent, floating_ip = self.parent_with_fip(kind)
                self.add("floating_ip", id="unrelated-new-allocation", updated_at=NOW.isoformat())
                proxy = self.connection.compute if kind == "server" else self.connection.load_balancer

                def wait(item, floating_ip=floating_ip, **kwargs):
                    self.connection.network.delete_ip.assert_not_called()
                    self.disappears(item, **kwargs)
                    detach_floating_ip(floating_ip)

                proxy.wait_for_delete.side_effect = wait
                self.make_runner().run()
                self.connection.network.delete_ip.assert_called_once_with(
                    floating_ip, ignore_missing=True, if_revision=6
                )
                self.assertLess(self.events.index(f"wait:{kind}"), self.events.index("delete:floating_ip"))
                self.assertNotIn(parent.id, self.items[kind])
                if kind == "load_balancer":
                    proxy.delete_load_balancer.assert_called_once_with(parent, ignore_missing=True, cascade=True)

    def test_timed_out_parent_does_not_authorize_immediate_fip_release(self):
        _, floating_ip = self.parent_with_fip("server")

        def wait(item, **kwargs):
            detach_floating_ip(floating_ip)
            raise exceptions.ResourceTimeout()

        self.connection.compute.wait_for_delete.side_effect = wait
        runner = self.make_runner(server_attempts=1)
        runner.run()
        self.assertTrue(runner.errors)
        self.connection.network.delete_ip.assert_not_called()

    def test_parent_fip_reattached_elsewhere_is_preserved(self):
        _, floating_ip = self.parent_with_fip("server")

        def wait(item, **kwargs):
            self.disappears(item, **kwargs)
            floating_ip.port_id = "another-live-port"
            floating_ip.updated_at = NOW.isoformat()
            floating_ip.revision_number += 1

        self.connection.compute.wait_for_delete.side_effect = wait
        self.make_runner().run()
        self.connection.network.delete_ip.assert_not_called()

    def test_parent_fip_with_new_forwarding_after_capture_is_preserved(self):
        _, floating_ip = self.parent_with_fip("server")

        def wait(item, **kwargs):
            self.disappears(item, **kwargs)
            detach_floating_ip(floating_ip)
            self.connection.network.floating_ip_port_forwardings.return_value = [
                SimpleNamespace(internal_port_id="another-port")
            ]

        self.connection.compute.wait_for_delete.side_effect = wait
        self.make_runner().run()
        self.connection.network.delete_ip.assert_not_called()


class OrphanPortFloatingIpTests(CleanupTestCase):
    def orphan_with_fip(self, **port_changes):
        port = self.add("port", fixed_ips=[{"ip_address": "192.0.2.5", "subnet_id": "test-subnet"}], **port_changes)
        ip = self.add(
            "floating_ip", status="ACTIVE", port_id=port.id, router_id="router-id", fixed_ip_address="192.0.2.5"
        )

        def wait(item, **kwargs):
            self.disappears(item, **kwargs)
            if item is port:
                detach_floating_ip(ip)

        self.connection.network.wait_for_delete.side_effect = wait
        return port, ip

    def test_orphan_port_is_conditionally_deleted_before_its_fip_is_released(self):
        for status in ("ACTIVE", "ERROR"):
            with self.subTest(status=status):
                self.reset_cloud()
                _, ip = self.orphan_with_fip()
                ip.status = status
                self.make_runner().run()
                self.connection.network.delete_port.assert_called_once()
                self.assertEqual(self.connection.network.delete_port.call_args.kwargs["if_revision"], 5)
                self.connection.network.delete_ip.assert_called_once_with(ip, ignore_missing=True, if_revision=6)
                self.assertLess(self.events.index("wait:port"), self.events.index("delete:floating_ip"))

    def test_recent_allocation_preserves_port_and_all_allocations(self):
        self.orphan_with_fip()
        self.add("floating_ip", id="second-allocation", port_id=PORT_ID, updated_at=NOW.isoformat())
        self.make_runner().run()
        self.assert_no_mutations()

    def test_ineligible_port_preserves_attached_fip(self):
        for changes in (
            {"updated_at": NOW.isoformat()},
            {"device_owner": "compute:nova", "device_id": "live-server"},
            {"revision_number": None},
        ):
            with self.subTest(changes=changes):
                self.reset_cloud()
                self.orphan_with_fip(**changes)
                self.make_runner().run()
                self.assert_no_mutations()

    def test_nova_reference_appearing_before_port_delete_preserves_both(self):
        self.orphan_with_fip()
        self.add("server", updated_at=NOW.isoformat())
        self.connection.compute.server_interfaces.side_effect = [[], [SimpleNamespace(port_id=PORT_ID)]]
        self.make_runner().run()
        self.assert_no_mutations()

    def test_port_revision_conflict_does_not_release_fip(self):
        self.orphan_with_fip()
        self.connection.network.delete_port.side_effect = http_error(412)
        runner = self.make_runner()
        runner.run()
        self.assertTrue(runner.errors)
        self.connection.network.delete_ip.assert_not_called()

    def test_fip_updated_during_final_reference_check_preserves_port(self):
        port, ip = self.orphan_with_fip()
        reads = 0

        def ips(**query):
            nonlocal reads
            if "port_id" not in query:
                reads += 1
                if reads == 2:
                    ip.updated_at = NOW.isoformat()
            return self.listed("floating_ip", query)

        self.connection.network.ips.side_effect = ips
        self.make_runner().cleanup_one("port", port)
        self.assert_no_mutations()

    def test_port_delete_timeout_does_not_release_fip(self):
        self.orphan_with_fip()
        self.connection.network.wait_for_delete.side_effect = exceptions.ResourceTimeout()
        runner = self.make_runner()
        runner.run()
        self.assertTrue(runner.errors)
        self.connection.network.delete_ip.assert_not_called()

    def test_reassigned_fip_is_preserved_after_port_deletion(self):
        port, ip = self.orphan_with_fip()

        def wait(item, **kwargs):
            self.disappears(item, **kwargs)
            if item is port:
                ip.port_id = "another-port"
                ip.revision_number += 1

        self.connection.network.wait_for_delete.side_effect = wait
        self.make_runner().run()
        self.connection.network.delete_port.assert_called_once()
        self.connection.network.delete_ip.assert_not_called()

    def test_port_forwarding_prevents_detaching_fip(self):
        self.orphan_with_fip()
        self.connection.network.floating_ip_port_forwardings.return_value = [SimpleNamespace(internal_port_id=PORT_ID)]
        self.make_runner().run()
        self.assert_no_mutations()

    def test_port_on_protected_portal_network_remains_eligible(self):
        self.orphan_with_fip()
        self.add("network", id="test-network", name="portal-internal")
        self.make_runner().run()
        self.connection.network.delete_port.assert_called_once()
        self.connection.network.delete_ip.assert_called_once()
        self.connection.network.delete_network.assert_not_called()

    def test_dry_run_does_not_detach_or_release(self):
        self.orphan_with_fip()
        self.make_runner(delete_resources=False).run()
        self.assert_no_mutations()


class VolumeRetryTests(CleanupTestCase):
    def test_newly_updated_standalone_volume_is_preserved_before_delete(self):
        old = self.add("volume")
        fresh = resource("volume", updated_at=NOW.isoformat())
        self.connection.block_storage.get_volume.side_effect = [old, fresh]
        self.make_runner().run()
        self.connection.block_storage.delete_volume.assert_not_called()
        self.connection.block_storage.wait_for_delete.assert_not_called()

    def test_async_detach_is_retried_after_confirmed_server_deletion(self):
        available = self.add("volume")
        detaching = resource("volume", status="detaching", attachments=[{"server_id": SERVER_ID}])
        responses = iter([detaching, available])
        self.connection.block_storage.get_volume.side_effect = lambda identifier: next(responses, available)
        runner = self.make_runner()
        runner.cleanup_volume(VOLUME_ID, followup=True)
        self.connection.block_storage.delete_volume.assert_called_once()
        runner.sleep.assert_called_once_with(2)
        self.assertEqual(runner.stats["volume.deleted"], 1)

    def test_transient_volume_delete_400_is_retried(self):
        self.add("volume")
        self.connection.block_storage.delete_volume.side_effect = [http_error(400), None]
        runner = self.make_runner()
        runner.run()
        self.assertEqual(self.connection.block_storage.delete_volume.call_count, 2)
        runner.sleep.assert_called_once_with(2)
        self.assertEqual(runner.errors, [])

    def test_volume_delete_404_is_idempotent(self):
        self.add("volume")
        self.connection.block_storage.delete_volume.side_effect = exceptions.ResourceNotFound()
        runner = self.make_runner()
        runner.run()
        self.assertEqual(runner.errors, [])
        self.assertEqual(runner.stats["volume.absent"], 1)


class KeypairTests(CleanupTestCase):
    def test_manual_keypair_only_mode_does_not_delete_workloads(self):
        self.add("server")
        self.add("keypair", name="azimuth-key")
        runner = self.make_runner(delete_resources=False, delete_all_keypairs=True)
        runner.run()
        self.connection.compute.delete_keypair.assert_called_once()
        self.connection.compute.delete_server.assert_not_called()
        self.assertIn("Resource cleanup: skipped", runner.summary_markdown())
        self.assertIn("Keypair cleanup: apply", runner.summary_markdown())

    def test_manual_keypair_cleanup_requires_allowed_prefix(self):
        for name in ("azimuth-test", "packer_test", "customer old", "default", "customer-keep"):
            self.add("keypair", name=name)
        self.make_runner(delete_all_keypairs=True).run()
        deleted = {call.args[0].name for call in self.connection.compute.delete_keypair.call_args_list}
        self.assertEqual(deleted, {"azimuth-test", "packer_test"})

    def test_keypair_reference_depends_on_matching_name_and_user(self):
        for key_name, user_id, delete in (
            ("azimuth-key", "ci-user", False),
            ("azimuth-key", None, False),
            ("unrelated-key", None, True),
            ("azimuth-key", "another-user", True),
        ):
            with self.subTest(server_key=key_name, server_user=user_id):
                self.reset_cloud()
                key = self.add("keypair", name="azimuth-key")
                self.add("server", key_name=key_name, user_id=user_id, updated_at=NOW.isoformat())
                self.make_runner(delete_all_keypairs=True).run()
                self.assertEqual(self.connection.compute.delete_keypair.call_count, int(delete))
                if delete:
                    self.assertIs(self.connection.compute.delete_keypair.call_args.args[0], key)

    def test_cross_project_permissions_are_needed_only_for_candidate_keys(self):
        for name, candidate in (("customer-key", False), ("azimuth-test", True)):
            with self.subTest(key=name):
                self.reset_cloud()
                self.add("server")
                self.add("keypair", name=name)
                self.add("keypair", name="azimuth-stackhpc-large-deploy")

                def servers(**query):
                    if query.get("all_projects"):
                        raise http_error(403)
                    return self.listed("server", query)

                self.connection.compute.servers.side_effect = servers
                runner = self.make_runner(delete_all_keypairs=True)
                runner.run()
                self.connection.compute.delete_server.assert_called_once()
                self.connection.compute.delete_keypair.assert_not_called()
                self.assertEqual(
                    any(call.kwargs.get("all_projects") for call in self.connection.compute.servers.call_args_list),
                    candidate,
                )
                self.assertEqual(bool(runner.errors), candidate)


class SafeLoggingTests(CleanupTestCase):
    def test_exception_response_body_is_not_logged(self):
        self.add("server")
        self.connection.compute.servers.side_effect = exceptions.SDKException("sensitive-response-body")
        runner = self.make_runner()
        runner.run()
        self.assertTrue(runner.errors)
        self.assertNotIn("sensitive-response-body", " ".join(str(call) for call in self.logger_mock.method_calls))


class ResourceParsingTests(unittest.TestCase):
    def test_openstack_timestamps_normalize_to_utc_and_preserve_fractional_seconds(self):
        expected = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
        fractional = expected.replace(microsecond=123456)
        cases = (
            ("2026-10-01T12:00:00Z", expected),
            ("2026-10-01T14:00:00+02:00", expected),
            ("2026-10-01T12:00:00.123456Z", fractional),
            ("2026-10-01T14:00:00.123456+02:00", fractional),
            ("2026-10-01T12:00:00.123456", fractional),
            (datetime(2026, 10, 1, 12), expected),
            (datetime(2026, 10, 1, 14, tzinfo=timezone(timedelta(hours=2))), expected),
        )
        for value, normalized in cases:
            with self.subTest(value=value):
                self.assertEqual(MODULE.resource_datetime(value), normalized)

    def test_missing_or_invalid_timestamps_cannot_establish_retention_age(self):
        for value in (None, "", "not-a-time", "2026-10-01", "2026-02-30T12:00:00Z", 123456, True):
            with self.subTest(value=value):
                self.assertIsNone(MODULE.resource_datetime(value))


if __name__ == "__main__":
    unittest.main()
