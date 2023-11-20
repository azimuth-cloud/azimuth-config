# Disaster Recovery

Azimuth uses [Velero](https://velero.io) as a disaster recovery solution. Velero provides the ability to both back up Kubernetes API resources (i.e. the raw yaml files) to an object store and also a plugin system to enable snapshotting of a cluster's persistent volumes.

The Azimuth functionality is provided via an azimuth-ops [role]() <**TODO: Link**> which installs the Velero Helm chart on the HA management cluster and the Velero CLI tool on the seed node. Once configured with the appropriate credentials, the installation process will create a [Schedule](https://velero.io/docs/latest/api-types/schedule/) on the HA cluster, which triggers a backup at <**TODO: Default interval**> and cleans up backups older than <**TODO: TTL**>.

## Configuration

To enable backup and restore functionality, the following variables should be set in your azimuth-config environment:

```yaml
velero_enabled: true
velero_s3_url: <object-store-endpoint-url>
velero_bucket_name: <name-of-an-existing-bucket>
```

and in your git-crypt encrypted `secrets.yml` file:

```yaml
velero_aws_access_key_id: <S3-access-key-id>
velero_aws_secret_access_key: <S3-secret-value>
```

With the above configuration in place, running the `stackhpc.azimuth_ops.provision` playbook will install the required Velero resources on the management infrastructure.

## Operations

For convenience, the Velero installation process also installs the Velero CLI on the Azimuth seed node. To view the configured back up locations, we can use the CLI as so:

```sh
./bin/seed-ssh
velero --kubeconfig kubeconfig-<ha-cluster-name>.yaml backup-location get
```

or to view the list of backups in that location, along with their status and other relevant information, use

```sh
velero --kubeconfig kubeconfig-<ha-cluster-name>.yaml backup get
```

See `velero -h` for other useful commands.

### Performing ad-hoc backups

In order to perform ad-hoc backups using the same config parameters as the installed backup schedule, run the following Velero CLI command from the seed node:

```sh
velero --kubeconfig kubeconfig-<ha-cluster-name>.yaml backup create --from-schedule default <backup-name>
```

This will begin the backup process in the background. The status of this backup (and others) can be viewed with the above `backup get` command.

### Modifying the backup schedule

The following config options are available for modifying the regular backup schedule:

```yaml
# Whether or not to create a regular backup schedule
velero_backup_schedule_enabled: true

# Name for backup schedule kubernetes resource
velero_backup_schedule_name: default

# Schedule to use for backups (defaults to every day at midnight)
# See https://en.wikipedia.org/wiki/Cron for format options
velero_backup_schedule_timings: "0 0 * * *"

# Time-to-live for existing backups (defaults to 1 week)
# See https://pkg.go.dev/time#ParseDuration for duration format options
velero_backup_schedule_ttl: "168h"
```

To install or update the configured backup schedule, re-run the `stackhpc.azimuth_ops.provision` playbook.

NOTE: Setting `velero_backup_schedule_enabled: false` does not prevent the backup schedule from being installed, instead it sets the schedule state to `paused`. This allows for ad-hoc backups to still be run on demand using the configured backup parameters.

## Restoring from a backup

The azimuth-ops role also provides a playbook to use for restoring the management resources from an existing backup. Before running a restore, the following azimuth-config variables must be set:

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

## Debugging

The Velero azimuth-ops role uses the AWS velero plugin for S3 support and the CSI plugin for volume snapshots (via the Kubernetes CSI snapshot controller and the implementation of this interface in the Cinder plugin for [cloud-provider-openstack](https://github.com/kubernetes/cloud-provider-openstack)).