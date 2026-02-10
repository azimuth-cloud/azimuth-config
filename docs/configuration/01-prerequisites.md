# Prerequisites

In order to deploy Azimuth, a small number of prerequisites must be fulfilled.

## OpenStack cloud

Currently, Azimuth is able to target OpenStack clouds with the following services enabled:

- Identity (Keystone)
- Image (Glance)
- Compute (Nova)
- Block storage (Cinder)
- Network (Neutron)
  - OVN and OVS/ML2 drivers supported
- Load balancer (Octavia)
  - Amphora and OVN drivers supported

Azimuth has no specific requirement on the version of OpenStack. It is known to work on
the OpenStack Train release and newer.

### Networking

OpenStack projects that are used for Azimuth deployments (infra projects), or into which
Azimuth will deploy platforms on behalf of users (workload projects), require access to a
network that is shared as `external` in Neutron, on which floating IPs can be allocated.

This network must provide egress to the internet, but does not need to provide ingress
from the internet. This network should be given the Neutron tag `portal-external` so that
it can be correctly detected by Azimuth, especially in the case where there are multiple
external networks.

<!-- prettier-ignore-start -->
!!! tip
    Adding the Neutron tag can be done using the OpenStack CLI (usually as admin):
<!-- prettier-ignore-end -->

```sh
openstack network set --tag portal-external ${external_network_name}
```

Machines provisioned as part of an Azimuth deployment, or as part of platforms in workload
projects, will be attached to a private network that is connected to this external network
using a router. These machines must be able to access the OpenStack API for the cloud in
which they are deployed.

### Cinder volumes and Kubernetes

[etcd](https://etcd.io), the distributed key-value store used by
[Kubernetes](https://kubernetes.io/), is
[extremely sensitive to slow disks](https://etcd.io/docs/latest/op-guide/hardware/#disks),
requiring _at least_ 50 sequential write IOPs.

The recommended OpenStack configuration is to use local disk on the hypervisor for
ephemeral root disks if possible. With this configuration, etcd _just about_ works with
spinning disk.

If Cinder volumes are used for the root disks of control plane nodes in a Kubernetes
cluster, they **must** be from an SSD-backed pool.

<!-- prettier-ignore-start -->
!!! danger
    Network-attached spinning disks **will not** be fast enough for etcd, resulting in performance and stability issues for Kubernetes clusters.
    In fact, even network-attached SSDs are not ideal as network instability can cause spikes in the latency, which etcd does not like.

!!! tip
    If you do not have much SSD capacity, it is possible to configure Kubernetes nodes so that etcd is on a separate block device, using a different volume type.
    See [etcd configuration](./03-kubernetes-config.md#etcd-configuration) for details.
<!-- prettier-ignore-end -->

### OpenStack project quotas

A standard high-availability (HA) deployment with a seed node, 3 control plane nodes and
3 worker nodes, requires the following resources:

- 1 x network, 1 x subnet, 1 x router
- 1 x seed node (4 vCPU, 8 GB)
- 4 x control plane nodes (4 vCPU, 8 GB)
  - 3 x during normal operation, 4 x during rolling upgrade
- 4 x worker nodes (8 vCPU, 16 GB)
  - 3 x during normal operation, 4 x during rolling upgrade
- 3 x load-balancers
- 500GB Cinder storage
- 3 x floating IPs
  - One for accessing the seed node
  - One for the ingress controller for accessing HTTP services
  - One for the Zenith SSHD server

<!-- prettier-ignore-start -->
!!! tip
    It is recommended to have a project for each concrete environment that is being deployed, particularly for high-availability (HA) deployments.
<!-- prettier-ignore-end -->

## Application Credential

You should create an
[Application Credential](https://docs.openstack.org/keystone/latest/user/application_credentials.html)
for the project and save the resulting `clouds.yaml` as `./environments/<name>/clouds.yaml`.

<!-- prettier-ignore-start -->
!!! warning
    Each concrete environment should have a separate application credential.
<!-- prettier-ignore-end -->

## Wildcard DNS

Zenith exposes HTTP services using random subdomains under a parent domain. This means that
Azimuth and Zenith require control of a entire subdomain, e.g. `*.azimuth.example.org`.

The Azimuth UI will be exposed as `portal.azimuth.example.org`, with Zenith services exposed
as `<random subdomain>.azimuth.example.org`. Azimuth leverages
[Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) as a
dynamically configurable HTTP proxy to route traffic from these domains to the correct services.

[ingress-nginx](https://github.com/kubernetes/ingress-nginx) is deployed as the ingress controller
and is exposed using a `LoadBalancer` service in Kubernetes. This results in an Octavia load-balancer
being deployed with a floating IP attached that routes traffic to the ingress controller.

In order for traffic to be routed correctly for these domains, a **wildcard** DNS record must exist
for `*.azimuth.example.org` that points at the floating IP of the load-balancer for the ingress
controller. **Azimuth does not manage this DNS record.**

## Transport Layer Security (TLS)

In order to provide secure connections to users, Azimuth needs to be able to obtain a TLS
certificate and private key for any of the subdomains under its wildcard domain.

This can be achieved in two ways:

1. Using a pre-existing wildcard TLS certificate for all subdomains
2. Using an ACME server (e.g. Let's Encrypt) to issue certificates dynamically

These approaches are discussed in more detail in the [Ingress section](../configuration/06-ingress.md).
