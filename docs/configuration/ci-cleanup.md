# CI resource cleanup

`bin/cleanup-ci-resources` removes leftover OpenStack resources in the project selected by the cloud credentials.
The deletion rules and protected resource names are specific to Azimuth CI.

## Run the script

Use Python 3.12, as in the cleanup workflow, and install the SDK:

```sh
python -m pip install 'openstacksdk>=4,<5'
```

Configure `clouds.yaml` for the CI project and select the cloud with `OS_CLOUD`.
The script needs access to the Compute, Block Storage, Network and Load Balancer APIs, including FIP port-forwarding.
Neutron deletions require `revision-if-match` support and a resource revision to prevent deletion if the resource changes after the check.
If either is missing, the script keeps the resource and logs a warning.

```sh
# Dry run: inspect candidates without deleting resources.
OS_CLOUD=leafcloud python bin/cleanup-ci-resources

# Delete eligible resources, including unused floating IPs.
OS_CLOUD=leafcloud python bin/cleanup-ci-resources --delete-resources

# Delete eligible keypairs only.
OS_CLOUD=leafcloud python bin/cleanup-ci-resources --delete-all-keypairs
```

`--delete-all-keypairs` performs real keypair deletion even without `--delete-resources`.
Supply both flags to delete both resources and keypairs.

A dry run checks the current cloud state without simulating parent deletion, so it may not report resources that become eligible later in a real cleanup run.

## Deletion rules

Servers use a **six-hour** age limit.
Other resources use **24 hours**, except for keypairs and the follow-up cleanup described below.
To change these limits, edit `SERVER_RETENTION_HOURS` and `UNUSED_RESOURCE_HOURS`.

| Resource        | Required conditions, in addition to the age limit                                                                                                         |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Servers         | `ACTIVE`, `BUILD`, `ERROR` or `SHUTOFF`, unlocked, and no task other than deletion. Attached volumes must pass the snapshot and backup checks.            |
| Volumes         | `available`, no attachment in Cinder or Nova, and no snapshot or backup.                                                                                  |
| Floating IPs    | No port, router, fixed IP or port-forwarding use. Release the allocation using Neutron's delete API.                                                      |
| Ports           | `DOWN`, no owner, device, host binding or trunk membership. No Nova, forwarding or LB reference. Any attached FIPs must also qualify for release.         |
| Security groups | No port uses the group, and no other group's rule refers to it. The group's own rules are deleted with it.                                                |
| Load balancers  | Provisioning status is `ACTIVE` or `ERROR`. Every backend and health-check address must match unused project ports. LBs without members can also qualify. |
| Routers         | No FIPs or custom routes. Connected subnets must be unused and not protected. Remove interfaces and the gateway before deleting the router.               |
| Subnets         | No workload ports or LB references. Neutron-managed DHCP ports can remain.                                                                                |
| Networks        | No ports, subnets or LB VIP references.                                                                                                                   |
| Keypairs        | Name starts with `azimuth-` or `packer_`, and no server owned by the same user uses that key name. Requested manually, with no age limit.                 |

Age normally means time since `updated_at`.
Resources other than servers use `created_at` when no update time is present.
Servers in `ERROR` or with a deletion task use `created_at`, because deletion can change their update time.
Times without a timezone, such as Cinder's `2026-09-07T09:03:43.000000`, are read as UTC.
The script skips resources with missing required timestamps.

The server policy can delete an old `ACTIVE` server even if its test has not finished.

### Resources to keep

The script keeps network `portal-internal`, router `portal-router`, security group `SSH`, security groups named `default` in any letter case, and keypair `azimuth-stackhpc-large-deploy`.
Shared security groups and shared, external or default networks are also kept.

Keeping a network also keeps its subnets.
Unused workload ports on that network can still qualify for cleanup.
Snapshots, backups, server groups and Glance images are not cleanup targets.

## Cleanup order and retries

Cleanup runs in this order:

```text
Servers -> Load balancers -> Floating IPs -> Volumes -> Ports
        -> Security groups -> Routers -> Subnets -> Networks
```

The script reads current details before deletion and waits for removal to finish.
It retries server deletion and gives volumes time to detach.
It does not force-delete resources or reset service state.
Octavia cascade deletion removes an LB and its children after the backend checks pass.

Before deleting a server or LB, the script records its attached FIP IDs.
Once the parent is gone, those FIPs can be released in the same run without another 24-hour wait.
Volumes recorded before server deletion receive the same age exception, but all usage checks still apply.
An old unused port holding eligible FIPs is deleted first.
The script then rechecks and releases its FIPs.

Retry state and IDs needed for follow-up cleanup stay in memory for that run.
If the run stops, the next run scans OpenStack again and applies the normal rules.

API failures are reported and block the affected cleanup.
Cleanup of other resources continues, and a run with recorded errors exits with status 1.
Results are written to the console and, in GitHub Actions, to the step summary.

## Floating IP reservations and CI teardown

Azimuth can reserve a FIP before Neutron shows an association.
Cleanup cannot see this reservation and may release that FIP before provisioning starts.
The team has accepted this race for the current CI cleanup policy.

The CI destroy action releases the ingress and Zenith SSHD addresses recorded in `ci.env` during teardown.
It checks the project, address and environment description before deleting by ID.
It tries both allocations even if one fails.
The scheduled script handles project-wide leftovers instead of running after every test.

## Keypair scope

Keypairs belong to a user, so the script checks server references across that user's projects.
This requires permission to list servers across projects.
The lookup is skipped when there are no candidate keys.
Deleting a keypair record does not remove keys already installed in a VM.

## Evidence behind the rules

The review used 217 inventory snapshots from the Leafcloud CI project, collected from September to October 2026.
An `available` volume still had a Nova reference, and the `SSH` and `default` security groups were used again after long idle periods.
These observations support checking dependencies and keeping shared infrastructure.

Existing cleanup, gaps between snapshots and irregular manual FIP releases mean the data cannot establish a safe age limit or prove continuous inactivity.
Six and 24 hours are operational policies, not thresholds proven by the snapshots.

## GitHub workflow

The cleanup workflow runs every two hours at eight minutes past the hour (UTC).
Scheduled runs delete eligible resources, except keypairs.
Manual runs default to dry-run, and only the default branch can enable deletion.

`TARGET_CLOUD` selects the repository's default cloud.
A manual run can enter `arcus` or `leafcloud`, or leave the input blank to use `TARGET_CLOUD`.
`OS_CLOUDS` provides the cloud configuration.
Only one cleanup run can target a given cloud at a time.

## Local tests

The tests use mocked OpenStack APIs and do not connect to a cloud:

```sh
python -m unittest discover -s tests -p 'test_cleanup_ci_resources.py'
```
