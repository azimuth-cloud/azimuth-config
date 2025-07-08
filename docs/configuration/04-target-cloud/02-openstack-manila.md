# OpenStack Manila

<!-- prettier-ignore-start -->
!!! warning "Technology preview"
    Manila support is currently in technology preview and under active development.
    It's possible how this feature works may radically change in a future release.
<!-- prettier-ignore-end -->

[Manila](https://docs.openstack.org/manila/latest/) is the OpenStack service for providing shared
read-write-many filesystems for OpenStack workloads.

## Project share

<!-- prettier-ignore-start -->
!!! warning "Limited platform support"
    Currently, only the `Slurm` and `Linux Workstation` platforms support the project share.
    Support for the other reference platforms is planned for the future.

!!! warning "Limited share type and protocol support"
    Azimuth will use the default share type for the project, unless there is only one share type available. Azimuth also assumes that this share type supports the CephFS share protocol.
<!-- prettier-ignore-end -->

When Manila is available, Azimuth is able to provide a filesystem to platforms that is shared
across all the platforms in a project, and persists beyond the lifetime of any single platform.
The shared filesystem is mounted at `/project` within each platform, and data written to `/project`
by one platform will be available to all the other platforms.

To enable project shares in Azimuth, set the following variable to the size (in GB) that you want
to use for the project shares:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_openstack_manila_project_share_gb: 100
```

For example, with this configuration Azimuth will ensure that a 100GB Manila share exists for each
tenancy and make that available to platforms.

<!-- prettier-ignore-start -->
!!! warning "Resizing of shares is not supported"
    If you increase the share size in your Azimuth configuration, new shares will be created at the new size but existing shares **will not** be resized.
    Existing shares can be resized manually using the OpenStack CLI or Horizon dashboard.
<!-- prettier-ignore-end -->

Ansible-based platforms will receive the following variables that can be use to configure the share:

```yaml
cluster_project_manila_share: true
cluster_project_manila_share_name: "azimuth-project-share"
cluster_project_manila_share_user: "proj-<project_id>"
```

!!! warning "Project shares are not backed up"

```text
There is no automated backup or snapshotting of project shares.
```

## Storage network automation

In order to access a Manila share, platforms need to be able to route to the storage service that
is providing the share. This often requires an additional network to be attached to the machines
that make up a platform.

Azimuth has the ability to detect and attach an additional network that is used for connecting
to storage. Similar to the
[internal and external network detection](./index.md#networking-configuration), Azimuth uses the
[Neutron resource tag](https://docs.openstack.org/neutron/latest/contributor/internals/tag.html)
`portal-storage` to identify the storage network.

If the storage network supports
[SR-IOV](https://en.wikipedia.org/wiki/Single-root_input/output_virtualization), Azimuth is also
able to utilise this which can improve performance when talking to the storage.

When Azimuth finds a network with the `portal-storage` tag, Ansible-based platforms will receive
the following Ansible variable containing the name of the network, allowing them to connect a
second NIC to it:

```yaml
cluster_storage_network: "name-of-portal-storage-network"
```

To specify that SR-IOV should be used on this network, set the following in your Azimuth
configuration:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_operator_global_extravars_overrides:
  cluster_storage_vnic_type: direct
```

Additional Kubernetes templates can also be defined that are aware of the storage network - see
[Custom cluster templates](../10-kubernetes-clusters.md#custom-cluster-templates) for an example.
