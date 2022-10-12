# Deployment method

`azimuth-ops` supports two deployment methods - `singlenode` and `ha`.

!!! info "Networking automation"

    `azimuth-ops` will create an internal network, onto which all nodes for the deployment
    will be placed. It will also create a router connecting the internal network to the
    external network where floating IPs are allocated.

## Single node

In this deployment method, a single node is provisioned with [Terraform](https://www.terraform.io/)
and configured as a [K3S](https://k3s.io/) cluster. The full Azimuth stack is then deployed
onto this cluster.

!!! warning

    This deployment method is only suitable for development or demonstration.

To use the single node deployment method, use the `singlenode` environment in your `ansible.cfg`:

```ini  title="ansible.cfg"
[defaults]
inventory = ../base/inventory,../singlenode/inventory,./inventory
```

The following variables must be set to define the properties of the K3S node:

```yaml
# The ID of the external network
infra_external_network_id: "<network id>"

# The floating IP to which to wildcard DNS entry has been assigned
infra_fixed_floatingip: "<pre-allocated floating ip>"

# The ID of the flavor to use for the K3S node
# A flavor with at least 4 CPUs and 16GB RAM is recommended
infra_flavor_id: "<flavor id>"

# The size of the volume to use for K3S cluster data
infra_data_volume_size: 100
```

## Highly-available (HA)

For the HA deployment method, Terraform is also used to provision a single node that is
configured as a K3S cluster. However rather than hosting the Azimuth components, as in
the single node case, this K3S cluster is only configured as a
[Cluster API management cluster](https://cluster-api.sigs.k8s.io/user/concepts.html#management-cluster).

Cluster API on the K3S cluster is then used to manage a HA cluster, in the same project
and on the same network. The Azimuth stack is then deployed onto this cluster.

To use the HA deployment method, use the `ha` environment in your `ansible.cfg`:

```ini  title="ansible.cfg"
[defaults]
inventory = ../base/inventory,../ha/inventory,./inventory
```

The following variables must be set to define the properties of the K3S node and the
Cluster API managed nodes:

```yaml
# The ID of the external network
infra_external_network_id: "<network id>"

# The ID of the flavor to use for the K3S node
# A flavor with at least 2 CPUs and 8GB RAM is recommended
infra_flavor_id: "<flavor id>"

# The name of the flavor to use for control plane nodes
# A flavor with at least 2 CPUs, 8GB RAM and 100GB root disk is recommended
capi_cluster_control_plane_flavor: "<flavor name>"

# The name of the flavor to use for worker nodes
# A flavor with at least 4 CPUs, 16GB RAM and 100GB root disk is recommended
capi_cluster_worker_flavor: "<flavor name>"

# The number of worker nodes
capi_cluster_worker_count: 3

# The floating IP to which to wildcard DNS entry has been assigned
capi_cluster_addons_ingress_load_balancer_ip: "<pre-allocated floating ip>"
```

## Availability Zones for Kubernetes nodes

!!! tip "Also applies to tenant Kubernetes clusters"

    The concepts in this section apply to any Kubernetes clusters created using
    Cluster API, i.e. the HA cluster in a HA deployment and tenant clusters.

    The variable names differ slightly for the two cases.

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

```yaml
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

```yaml
#### For the HA cluster ####

# Indicate that the failure domain should be omitted for control plane nodes
capi_cluster_control_plane_omit_failure_domain: true
# Specify no failure domain for worker nodes
capi_cluster_worker_failure_domain: null

#### For tenant clusters ####
azimuth_capi_operator_capi_helm_control_plane_omit_failure_domain: true
azimuth_capi_operator_capi_helm_worker_failure_domain: null
```
