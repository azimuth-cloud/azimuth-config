# Kubernetes configuration

The concepts in this section apply to any Kubernetes clusters created using Cluster API,
i.e. the HA cluster in a HA deployment and tenant clusters.

The variable names differ slightly for the two cases.

## Images

When building a cluster, Cluster API requires that an image exists in the target cloud
that is accessible to the target project and has the correct version of
[kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/) and
[kubeadm](https://kubernetes.io/docs/reference/setup-tools/kubeadm/) available.

Suitable images are uploaded as part of an Azimuth deployment using the
[Community images functionality](./09-community-images.md) and the IDs are automatically
propagated where they are needed, i.e. for the
[Azimuth HA cluster](./02-deployment-method.md#highly-available-ha) and the
[Kubernetes cluster templates](./10-kubernetes-clusters.md#cluster-templates).

If required, e.g. for
[custom Kubernetes templates](./10-kubernetes-clusters.md#custom-cluster-templates), the
IDs of these images can be referenced using the `community_images_image_ids` variable:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
kube_1_25_image_id: "{{ community_images_image_ids.kube_1_25 }}"
kube_1_26_image_id: "{{ community_images_image_ids.kube_1_26 }}"
kube_1_27_image_id: "{{ community_images_image_ids.kube_1_27 }}"
```

## Docker Hub mirror

Docker Hub [imposes rate limits](https://docs.docker.com/docker-hub/download-rate-limit/)
on image downloads, which can cause issues for both the Azimuth HA cluster and, in particular,
tenant clusters. This can be worked around by mirroring the images to a local registry.

If you have a Docker Hub mirror available, this can be configured using the following variables:

```yaml
#### For the HA cluster ####

# The ID of the external network to use
capi_cluster_registry_mirrors:
  docker.io: ["https://docker-hub-mirror.example.org/v2"]

#### For tenant clusters ####

azimuth_capi_operator_capi_helm_registry_mirrors:
  docker.io: ["https://docker-hub-mirror.example.org/v2"]
```

!!! tip

    If you do not have a Docker Hub mirror available, one can be
    [deployed as part of an Azimuth deployment](./10-kubernetes-clusters.md#harbor-registry).
    This mirror will be automatically configured for tenant Kubernetes clusters.

    This mirror **cannot** be used for the Azimuth HA cluster as it is deployed on that
    cluster.

## Multiple external networks

In the case where multiple external networks are available, you must tell Azimuth which one
to use:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
#### For the HA cluster ####

# The ID of the external network to use
capi_cluster_external_network_id: "<network id>"

#### For tenant clusters ####

azimuth_capi_operator_external_network_id: "<network id>"
```

!!! note

    This does **not** currently respect the `portal-external` tag.

## Volume-backed instances

Flavors with 100GB root disks are recommended for Kubernetes nodes, both for the
Azimuth deployment and for tenant clusters.

If flavors with large root disks are not available on the target cloud, it is possible
to use volume-backed instances instead.

!!! danger  "etcd and spinning disks"

    The configuration options in this section should be used subject to the advice
    in the [prerequisites](./01-prerequisites.md#cinder-volumes-and-kubernetes) about
    using Cinder volumes with Kubernetes.

To configure Kubernetes clusters to use volume-backed instances (i.e. use a Cinder
volume as the root disk), the following variables can be used:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
#### For the HA cluster ####

# The size of the root volumes for Kubernetes nodes
capi_cluster_root_volume_size: 100
# The volume type to use for root volumes for Kubernetes nodes
capi_cluster_root_volume_type: nvme

#### For tenant clusters ####

azimuth_capi_operator_capi_helm_root_volume_size: 100
azimuth_capi_operator_capi_helm_root_volume_type: nvme
```

## Load-balancer provider

If the target cloud uses [OVN networking](https://www.ovn.org/en/), and the
[OVN Octavia driver](https://docs.openstack.org/ovn-octavia-provider/latest/admin/driver.html)
is enabled, then Kubernetes clusters should be configured to use the OVN provider for
any load-balancers that are created:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
#### For the HA cluster ####

# The provider for the API server load-balancer created by Cluster API
capi_cluster_apiserver_loadbalancer_provider: ovn
# The provider for load-balancers created for LoadBalancer services
capi_cluster_addons_openstack_loadbalancer_provider: ovn

#### For tenant clusters ####

# Tenant API servers are load-balanced using Zenith
# This variable applies to load-balancers created for LoadBalancer services
azimuth_capi_operator_capi_helm_openstack_loadbalancer_provider: ovn
```

## Availability zones

By default, an Azimuth installation assumes that there is a single
[availability zone (AZ)](https://docs.openstack.org/nova/latest/admin/availability-zones.html)
called `nova` - this is the default set up and common for small-to-medium sized clouds. If
this is not the case for your target cloud, you may need to set additional variables
specifying the AZs to use, both for the HA cluster and for tenant Kubernetes clusters.

The default behaviour when scheduling Kubernetes nodes using Cluster API is:

  * *All available AZs* are considered for control plane nodes, and Cluster API will
    attempt to spread the nodes across multiple AZs, if available.
  * Worker nodes are scheduled into the `nova` AZ explicitly. If this AZ does not exist,
    scheduling will fail.

If this default behaviour does not work for your target cloud, the following options are
available.

!!! note

    Cluster API refers to "failure domains" which, in the OpenStack provider,
    correspond to availability zones (AZs).

### Use specific availability zones

To specify the availability zones for Kubernetes nodes, the following variables can be used:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
#### For the HA cluster ####

# A list of failure domains that should be considered for control plane nodes
capi_cluster_control_plane_failure_domains: [az1, az2]
# The failure domain for worker nodes
capi_cluster_worker_failure_domain: az1

#### For tenant clusters ####

azimuth_capi_operator_capi_helm_control_plane_failure_domains: [az1, az2]
azimuth_capi_operator_capi_helm_worker_failure_domain: az1
```

### Ignore availability zones

It is possible to configure Cluster API clusters in such a way that AZs are *not specified at all*
for Kubernetes nodes. This allows other placement constraints such as
[flavor traits](https://docs.openstack.org/nova/latest/user/flavors.html#extra-specs-required-traits)
and [host aggregate](https://docs.openstack.org/nova/latest/admin/aggregates.html) to
be used, and a suitable AZ to be selected by OpenStack.

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
#### For the HA cluster ####

# Indicate that the failure domain should be omitted for control plane nodes
capi_cluster_control_plane_omit_failure_domain: true
# Specify no failure domain for worker nodes
capi_cluster_worker_failure_domain: null

#### For tenant clusters ####
azimuth_capi_operator_capi_helm_control_plane_omit_failure_domain: true
azimuth_capi_operator_capi_helm_worker_failure_domain: null
```
