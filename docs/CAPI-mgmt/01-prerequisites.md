# Prerequisites

Although described in greater detail
[here](https://stackhpc-kayobe-config.readthedocs.io/en/stackhpc-2025.1/configuration/magnum-capi.html#deployment-prerequisites),
a brief summary of the requirements for deploying a CAPI management cluster for Magnum will
be covered below.

Additionally, general instructions of how to deploy the CAPI management cluster can be found at the
following [link](https://stackhpc-kayobe-config.readthedocs.io/en/stackhpc-2025.1/configuration/magnum-capi.html).

## OpenStack cloud

This guide won't cover any OpenStack requirements which this cluster may be running on
and a baseline understanding of OpenStack is assumed.

### Networking

The Cluster API architecture relies on a CAPI management cluster in order to run Kubernetes operators
which directly interact with the cloud APIs. In the OpenStack case, the [Cluster API Provider OpenStack (CAPO)](https://github.com/kubernetes-sigs/cluster-api-provider-openstack) is used.

This management cluster has two main requirements in order to operate:


<!-- markdownlint-disable MD007 -->
<!-- prettier-ignore-start -->

- Firstly, it must be capable of reaching the public OpenStack APIs.
- Secondly, the management cluster must be reachable from the control
  plane nodes on which the Magnum containers are running.

    - This is so that the Magnum conductor(s) may reach the management
      cluster’s API server address listed in the `kubeconfig`.

<!-- prettier-ignore-end -->
<!-- markdownlint-enable MD007 -->

### OpenStack project quotas

For a production-ready, highly-available (HA) deployment with a seed node, 3 control plane nodes and
3 worker nodes, the recommended capacity of available resources in your project should be sufficient for:


- 1 x network, 1 x subnet, 1 x router
- 1 x seed node (4 vCPU, 8 GB)
- 3 x control plane nodes (4 vCPU, 8 GB) + 1 x extra when undergoing a rolling upgrade
- 3 x worker nodes (8 vCPU, 16 GB) + 1 x extra when undergoing a rolling upgrade

There are further suggested resources, as per the [following](../configuration/01-prerequisites.md#openstack-project-quotas),
but these are optional.

However, as with any of the configuration here, tailor these values to whatever
best suits your needs and usecases!

<!-- prettier-ignore-start -->
!!! tip
    It is recommended to have a separate OpenStack project for each concrete environment that is being deployed, for example a staging and production CAPI management clusters, particularly for high-availability (HA) deployments.
<!-- prettier-ignore-end -->

## Application Credential

You should create an
[Application Credential](https://docs.openstack.org/keystone/latest/user/application_credentials.html)
for the project and save the resulting `clouds.yaml` as `./environments/<name>/clouds.yaml`.

<!-- prettier-ignore-start -->
!!! warning
    Each concrete environment should have a separate application credential.
<!-- prettier-ignore-end -->
