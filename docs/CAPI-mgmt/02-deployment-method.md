# Deployment method

Due to deploying the CAPI management cluster for the purpose of being a COE's OpenStack API driver,
this document will be following a Highly-available (HA) deployment pattern.

<!-- prettier-ignore-start -->
!!! info "Networking automation"
    azimuth-ops will create an internal network, onto which all nodes for the deployment will be placed.
    It will also create a router connecting the internal network to the external network where floating IPs are allocated.
<!-- prettier-ignore-end -->

## Environments

Once the initial working repository has been configured, following
[these steps](https://azimuth-config.readthedocs.io/en/stable/repository/),
a template of the CAPI management cluster can be made by copying over the
``capi-mgmt-example`` environment directory into your own:

```sh 
cp -r ./environments/capi-mgmt-example ./environments/<site-name>
```

### Using mixin environments

"mixin"

### Linux environment variables

## Highly-available (HA)

For the HA deployment method, OpenTofu is also used to provision a single node that is
configured as a K3s cluster. However rather than hosting the Azimuth components, as in
the single node case, this K3s cluster is only configured as a
[Cluster API management cluster](https://cluster-api.sigs.k8s.io/user/concepts.html#management-cluster).

Cluster API on the K3s cluster is then used to manage a HA cluster, in the same project
and on the same network. The Azimuth stack is then deployed onto this cluster.

To use the HA deployment method, use the `ha` environment in your `ansible.cfg`:

```ini title="ansible.cfg"
[defaults]
inventory = ../base/inventory,../ha/inventory,./inventory
```

The following variables must be set to define the properties of the K3s node and the
Cluster API managed nodes:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
# The ID of the external network
infra_external_network_id: "<network id>"

# The ID of the flavor to use for the K3s node
# A flavor with at least 4 CPUs and 8GB RAM is recommended
# for production deployments since k3s upgrades can generate
# relatively high CPU load during k3s DBs migrations
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
