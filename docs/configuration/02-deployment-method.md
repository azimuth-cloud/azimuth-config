# Deployment method

`azimuth-ops` supports two deployment methods - `singlenode` and `ha`.

!!! info "Networking automation"

    `azimuth-ops` will create an internal network, onto which all nodes for the deployment
    will be placed. It will also create a router connecting the internal network to the
    external network where floating IPs are allocated.

## Single node

In this deployment method, a single node is provisioned with [OpenTofu](https://opentofu.org/)
and configured as a [K3s](https://k3s.io/) cluster. The full Azimuth stack is then deployed
onto this cluster.

!!! warning

    This deployment method is only suitable for development or demonstration.

To use the single node deployment method, use the `singlenode` environment in your `ansible.cfg`:

```ini  title="ansible.cfg"
[defaults]
inventory = ../base/inventory,../singlenode/inventory,./inventory
```

The following variables must be set to define the properties of the K3s node:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# The ID of the external network
infra_external_network_id: "<network id>"

# The floating IP to which to wildcard DNS entry has been assigned
infra_fixed_floatingip: "<pre-allocated floating ip>"

# The ID of the flavor to use for the K3s node
# A flavor with at least 4 CPUs and 16GB RAM is recommended
infra_flavor_id: "<flavor id>"

# The size of the volume to use for K3s cluster data
infra_data_volume_size: 100
```

## Highly-available (HA)

For the HA deployment method, OpenTofu is also used to provision a single node that is
configured as a K3s cluster. However rather than hosting the Azimuth components, as in
the single node case, this K3s cluster is only configured as a
[Cluster API management cluster](https://cluster-api.sigs.k8s.io/user/concepts.html#management-cluster).

Cluster API on the K3s cluster is then used to manage a HA cluster, in the same project
and on the same network. The Azimuth stack is then deployed onto this cluster.

To use the HA deployment method, use the `ha` environment in your `ansible.cfg`:

```ini  title="ansible.cfg"
[defaults]
inventory = ../base/inventory,../ha/inventory,./inventory
```

The following variables must be set to define the properties of the K3s node and the
Cluster API managed nodes:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# The ID of the external network
infra_external_network_id: "<network id>"

# The ID of the flavor to use for the K3s node
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

# The pre-allocated floating IP to which to wildcard DNS entry has been assigned
capi_cluster_addons_ingress_load_balancer_ip: "<pre-allocated floating ip>"

# The pre-allocated floating IP for the Zenith SSHD server
zenith_sshd_service_load_balancer_ip: "<pre-allocated floating ip>"
```
