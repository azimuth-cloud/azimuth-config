# Disaster Recovery

CAPI management clusters can be configured to use [Velero](https://velero.io) as a disaster
recovery solution. Velero provides the ability to back up Kubernetes API resources to an object
store and has a plugin-based system to enable snapshotting of a cluster's persistent volumes.

<!-- prettier-ignore-start -->
!!! warning
    Backup and restore is only available for production-grade HA installations of clusters.
<!-- prettier-ignore-end -->

The playbooks install Velero on the HA management cluster and the Velero command-line-tool on the seed node.
Once configured with the appropriate credentials, the installation process will create a
[Schedule](https://velero.io/docs/latest/api-types/schedule/) on the HA cluster, which triggers a daily
backup at midnight and cleans up backups older which are more than 1 week old.

<!-- prettier-ignore-start -->
!!! note
    - The [AWS Velero plugin](https://github.com/vmware-tanzu/velero-plugin-for-aws) is used for S3 support.
    - The [CSI plugin](https://github.com/vmware-tanzu/velero-plugin-for-csi) for volume snapshots.
    - The CSI plugin uses Kubernetes generic support for [Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/).
        - This is implemented for OpenStack by the [Cinder CSI plugin](https://github.com/kubernetes/cloud-provider-openstack).
<!-- prettier-ignore-end -->

Information on how to configure and use disaster recovery can be found
[here](../configuration/15-disaster-recovery.md#configuration)
