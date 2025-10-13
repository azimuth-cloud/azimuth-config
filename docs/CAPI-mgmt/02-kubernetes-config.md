# Kubernetes configuration

The concepts in this section apply to any Kubernetes clusters created using Cluster API,
i.e. the HA cluster in a HA deployment and tenant clusters.

The variables used to configure HA deployments are the same as those for Azimuth and so
only a surface level of detail will be covered below. For further details visit the
[Azimuth Kubernetes configuration documentation](../configuration/03-kubernetes-config.md). 

## Images

The clusters deployed by the Cluster API (CAPI) driver make use of the Ubuntu Kubernetes images
built from the [azimuth-images repository](https://github.com/azimuth-cloud/azimuth-images), alongside
[capi-helm-charts](https://github.com/azimuth-cloud/capi-helm-charts) in order to provide the Helm charts
which define these clusters based on the image.

These two repositories have CI jobs regularly building and testing the images and Helm charts
for the latest Kubernetes versions. Therefore, it is important to update the cluster templates
on each cloud regularly.

<!-- prettier-ignore-start -->
!!! note
    These templates are tested as sets against specific CAPI management cluster versions. As such,
    it is vitally important to update the CAPI management cluster to the latest release before
    updating to the latest templates.

!!! note
    Information on community images and how they are built can be found [here](../configuration/09-community-images.md).
<!-- prettier-ignore-end -->

If required, it is possible to reference the image's IDs using the `community_images_image_ids`
variable. This, for example, could be used to create [custom Kubernetes templates](./10-kubernetes-clusters.md#custom-cluster-templates).

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
kube_1_25_image_id: "{{ community_images_image_ids.kube_1_25 }}"
kube_1_26_image_id: "{{ community_images_image_ids.kube_1_26 }}"
kube_1_27_image_id: "{{ community_images_image_ids.kube_1_27 }}"
```

## Docker Hub rate limits
<!-- prettier-ignore-start -->
!!! warning
    Docker Hub [imposes rate limits](https://docs.docker.com/docker-hub/download-rate-limit/)
    on image downloads, which can cause issues for both the HA cluster and, in particular,
    tenant clusters. This can be worked around by mirroring the images to a local registry.


!!! warning
    For more information please see [here](../configuration/03-kubernetes-config.md#docker-hub-mirror).
<!-- prettier-ignore-end -->

## Multiple external networks

In cases where multiple external networks are available, you must define which one the HA cluster
should use:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
#### For the HA cluster ####

# The ID of the external network to use
capi_cluster_external_network_id: "<network id>"
```

<!-- prettier-ignore-start -->
!!! note
    This does **not** currently respect the "portal-external" tag.
<!-- prettier-ignore-end -->

## Volume-backed instances

It is possible to use volume-backed instances if flavors predefined with large root disks are
not available on the target cloud.

<!-- prettier-ignore-start -->
!!! danger "etcd and spinning disks"
    The configuration options in this section should be used subject to the advice in the prerequisites.
    See [prerequisites](../configuration/01-prerequisites.md#cinder-volumes-and-kubernetes) about using Cinder volumes with Kubernetes.

!!! tip "etcd on a separate block device"
    If you only have a limited amount of SSD or, even better, local disk, available, consider placing etcd on a separate block device.
    See [etcd block device](#etcd-configuration) to make best use of the limited capacity.
<!-- prettier-ignore-end -->

The following variables can be used to configure Kubernetes clusters to use volume-backed instances
(i.e. using a Cinder volume as the root disk):

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
#### For the HA cluster ####

# The size of the root volumes for Kubernetes nodes
capi_cluster_root_volume_size: 100
# The volume type to use for root volumes for Kubernetes nodes
capi_cluster_root_volume_type: nvme

#### For tenant clusters ####

azimuth_capi_operator_capi_helm_root_volume_size: 100
azimuth_capi_operator_capi_helm_root_volume_type: nvme
```

<!-- prettier-ignore-start -->
!!! tip
    The available volume types can be listed using the OpenStack CLI:
    ```sh
    openstack volume type list
    ```
<!-- prettier-ignore-end -->

## Etcd configuration

As discussed [here](../configuration/01-prerequisites.md#cinder-volumes-and-kubernetes),
`etcd` is extremely sensitive to write latency. As such, it is possible
to configure `etcd` onto a separate block device, meaning the disk's volume
type can differ from the root disk, allowing efficient use of SSD-backed storage. 
More detail on this can be found [here](../configuration/03-kubernetes-config.md#etcd-configuration).

<!-- prettier-ignore-start -->
!!! tip "Use local disk for etcd whenever possible"
    Using local disk when possible minises the write latency for etcd and also eliminates network instability as a cause of latency problems.
<!-- prettier-ignore-end -->

The following variables are used to configure the etcd block device for an HA cluster:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
# Specifies the size of the etcd block device in GB
# This is typically between 2GB and 10GB - Amazon recommends 8GB for EKS
# Defaults to 0, meaning etcd stays on the root device
capi_cluster_etcd_blockdevice_size: 8

# The type of block device that will be used for etcd
# Specify "Volume" (the default) to use a Cinder volume
# Specify "Local" to use local disk (the flavor must support ephemeral disk)
capi_cluster_etcd_blockdevice_type: Volume

# The Cinder volume type to use for the etcd block device
# Only used if "Volume" is specified as block device type
# If not given, the default volume type for the cloud will be used
capi_cluster_etcd_blockdevice_volume_type: nvme

# The Cinder availability zone to use for the etcd block device
# Only used if "Volume" is specified as block device type
# Defaults to "nova"
capi_cluster_etcd_blockdevice_volume_az: nova
```

## Load-balancer provider

If the target cloud uses [OVN networking](https://www.ovn.org/en/), and the
[OVN Octavia provider](https://docs.openstack.org/ovn-octavia-provider/latest/admin/driver.html)
is enabled, then Kubernetes clusters should be configured to use the OVN provider for
any load-balancers that are created:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
openstack_loadbalancer_provider: ovn
```

<!-- prettier-ignore-start -->
!!! tip
    You can see the available load-balancer providers using the OpenStack CLI:
    ```sh
    openstack loadbalancer provider list
    ```
<!-- prettier-ignore-end -->

## Availability zones

By default, it is assumed that there is only a single
[availability zone (AZ)](https://docs.openstack.org/nova/latest/admin/availability-zones.html)
called `nova`. 

However, if the target cloud's AZ configuration and scheduling behaviours differ from
the default then some additional variables may be required, such as specifying the AZs
to use, both for the HA cluster and for tenant Kubernetes clusters.

<!-- prettier-ignore-start -->
!!! note
    Information on availability zones and scheduling behaviours can be found
    [here](../configuration/03-kubernetes-config.md#availability-zones).
<!-- prettier-ignore-end -->