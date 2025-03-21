# Disaster Recovery

Azimuth uses [Velero](https://velero.io) as a disaster recovery solution. Velero provides the
ability to back up Kubernetes API resources to an object store and has a plugin-based system
to enable snapshotting of a cluster's persistent volumes.

!!! warning

    Backup and restore is only available for production-grade HA installations of Azimuth.

The Azimuth playbooks install Velero on the HA management cluster and the Velero CLI tool
on the seed node. Once configured with the appropriate credentials, the installation process
will create a [Schedule](https://velero.io/docs/latest/api-types/schedule/) on the HA cluster,
which triggers a daily backup at midnight and cleans up backups older which are more than 1 week old.

The
[AWS Velero plugin](https://github.com/vmware-tanzu/velero-plugin-for-aws) is used for S3 support
and the
[CSI plugin](https://github.com/vmware-tanzu/velero-plugin-for-csi) for volume snapshots.
The CSI plugin uses Kubernetes generic support for
[Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/), which is
implemented for OpenStack by the
[Cinder CSI plugin](https://github.com/kubernetes/cloud-provider-openstack).

## Configuration

To enable backup and restore functionality, the following variables must be set in your environment:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# Enable Velero
velero_enabled: true

# The URL of the S3 storage endpoint
velero_s3_url: <object-store-endpoint-url>

# The name of the bucket to use for backups
velero_bucket_name: <bucket-name>
```

!!! warning  "Bucket must already exist"

    The specified bucket must already exist - neither azimuth-ops nor Velero will create it.

You will also need to consult the documentation for your S3 provider to obtain S3 credentials for
the bucket, and add the access key ID and secret to the following variables:

```yaml  title="environments/my-site/inventory/group_vars/all/secrets.yml"
# Access key ID and secret for accessing the S3 bucket
velero_aws_access_key_id: <s3-access-key-id>
velero_aws_secret_access_key: <s3-secret-value>
```

!!! tip  "Generating credentials for Keystone-integrated Ceph Object Gateway"

    If the S3 target is
    [Ceph Object Gateway integrated with Keystone](https://docs.ceph.com/en/latest/radosgw/keystone/),
    a common configuration with OpenStack clouds, S3 credentials can be generated using the following:

    ```sh
    openstack ec2 credentials create
    ```

!!! danger

    The S3 credentials should be kept secret. If you want to keep them in Git - which is recommended -
    then they [must be encrypted](../repository/secrets.md).

## Velero CLI

The Velero installation process also installs the Velero CLI on the Azimuth seed node, which can be
used to inspect the state of the backups:

```sh  title="On the seed node, with the kubeconfig for the HA cluster exported"
# List the configured backup locations
velero backup-location get

# List the backups and their statuses
velero backup get
```

See `velero -h` for other useful commands.

## Restoring from a backup

To restore from a backup, you must first know the name of the target backup. This can be inferred
from the object names in S3 if the Velero CLI is no longer available.

Once you have the name of the backup to restore, run the following command with your environment
activated (similar to a provision):

```bash
ansible-playbook azimuth_cloud.azimuth_ops.restore \
  -e velero_restore_backup_name=<backup name>
```

This will provision a new HA cluster, restore the backup onto it and then bring the installation
up-to-date with your configuration.

## Performing ad-hoc backups

In order to perform ad-hoc backups using the same config parameters as the installed backup schedule,
run the following Velero CLI command from the seed node:

```sh  title="On the seed node, with the kubeconfig for the HA cluster exported"
velero backup create --from-schedule default
```

This will begin the backup process in the background. The status of this backup (and others) can be
viewed with the `velero backup get` command shown above.

!!! tip

    Ad-hoc backups will have the same time-to-live as the configured schedule backups (default = 7 days).
    To change this, pass the `--ttl <hours>` option to the `velero backup create` command.

## Modifying the backup schedule

The following config options are available for modifying the regular backup schedule:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# Whether or not to perform scheduled backups
velero_backup_schedule_enabled: true
# Name for backup schedule kubernetes resource
velero_backup_schedule_name: default
# Schedule to use for backups (defaults to every day at midnight)
# See https://en.wikipedia.org/wiki/Cron for format options
velero_backup_schedule: "0 0 * * *"
# Time-to-live for existing backups (defaults to 1 week)
# See https://pkg.go.dev/time#ParseDuration for duration format options
velero_backup_ttl: "168h"
```

!!! note

    Setting `velero_backup_schedule_enabled: false` does not prevent the backup schedule from being
    installed - instead it sets the schedule state to `paused`.

    This allows for ad-hoc backups to still be run on demand using the configured backup parameters.
