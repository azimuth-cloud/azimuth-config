# Disaster Recovery

Azimuth provides a mechanism for backup and restore of the state of the management resources (seed node + management cluster) in an HA deployment. The core functionality is provided by [Velero](https://velero.io), which features a plugin system to allow for direct integration with services provided by the host cloud - we make use of the [OpenStack plugin](https://github.com/Lirt/velero-plugin-for-openstack) to interface with OpenStack Swift (to backup Kubernetes resource manifests) and OpenStack Cinder (to backup the management cluster's persistent volumes).

TODO: What about off-site backups?

## Configuration

To enable backup and restore functionality, the following variables should be set in your azimuth-config environment:

```yaml
velero_enabled: true
velero_bucket_name: <name-of-an-existing-bucket>
```

In order to authenticate with OpenStack, the management cluster's pre-existing CAPO cloud credentials secret is used by default. To provide a separate set of credentials, create a new app cred in OpenStack and then in **secrets.yml** (see [Managing secrets](../repository/secrets.md)) set the following variables:

```yaml
velero_openstack_use_existing_secret: false
velero_openstack_auth_url: 
velero_openstack_app_cred_id:
velero_openstack_app_cred_secret:
```

The Velero OpenStack plugin defaults to using Cinder's *snapshot* functionality to back up persistent volumes. This can be changed by setting:

```yaml
velero_cinder_volume_backup_method: <method>
```

See [plugin docs](https://github.com/Lirt/velero-plugin-for-openstack/blob/master/docs/installation-using-helm.md) for supported alternatives to `snapshot`.

With the above configuration in place, running the `stackhpc.azimuth_ops.provision` playbook will install the required Velero resources on the management infrastructure.

### Performing ad-hoc backups

An ansible playbook is provided within azimuth-ops to perform ad-hoc backups on demand:

```yaml
ansible-playbook stackhpc.azimuth_ops.backup
```

For convenience, the Velero installation process also installs the Velero CLI on the Azimuth seed node. To view the configured back up locations, we can use this CLI as so:

```sh
./bin/seed-ssh
velero --kubeconfig kubeconfig-<ha-cluster-name>.yaml backup-location get
```

or to view the list of backups in that location, along with their status and other relevant information, use

```sh
velero --kubeconfig kubeconfig-<ha-cluster-name>.yaml backup get
```

See `velero -h` for other useful commands.


For ad-hoc backups, the following settings can be adjusted as required:

```yaml
# Name to use for newly created ad-hoc backup (defaults to '<env-name>--<timestamp>')
velero_backup_name:
```

If the backup process is particularly slow (e.g. when snapshotting very large cinder volumes), the timeout can be adjusted with

```yaml
velero_backup_creation_timeout: <seconds>
```

### Scheduling backups

In addition to ad-hoc backups, a regular backup schedule may also be configured. The following config variables control this process:

```yaml
# Whether or not to create a regular backup schedule
velero_backup_schedule_enabled: false

# Name for backup schedule kubernetes resource
velero_backup_schedule_name: default

# Schedule to use for backups (defaults to every day at midnight)
# See https://en.wikipedia.org/wiki/Cron for format options
velero_backup_schedule_timings: "0 0 * * *"

# Time-to-live for existing backups (defaults to 2 week)
# See https://pkg.go.dev/time#ParseDuration for duration format options
velero_backup_schedule_ttl: "336h"
```

To install or update the configured backup schedule, re-run the `stackhpc.azimuth_ops.provision` playbook.

## Restoring from a backup

Similar to the ad-hoc backup process, azimuth-ops provides a playbook to use for restoring the management resources from an existing backup. Before running a restore, the following azimuth-config variables must be set:

```yaml
# Name of restore object to create
velero_restore_name: 
# Name of backup to use for restore process
velero_restore_backup_name: 
```

The default config also sets `velero_restore_strict: true` which prevents restore processes targeting an incomplete or otherwise failed backup.

Other relevant restore config options include:

```yaml
velero_restore_attempt_timeout: <seconds>

# Whether or not to attempt a restore of the monitoring
# data volumes from the cinder backup (default: true)
velero_restore_monitoring_data:
```

## Debugging Tips

