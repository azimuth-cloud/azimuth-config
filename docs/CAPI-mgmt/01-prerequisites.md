# Prerequisites

Although described in greater detail
[here](https://stackhpc-kayobe-config.readthedocs.io/en/stackhpc-2025.1/configuration/magnum-capi.html#deployment-prerequisites),
a brief summary of the requirements for deploying a CAPI management cluster for Magnum will
be covered below.

Additionally, general instructions of how to deploy the CAPI management cluster can be found at the
following [link](https://stackhpc-kayobe-config.readthedocs.io/en/stackhpc-2025.1/configuration/magnum-capi.html).

## OpenStack cloud

This guide won't cover any of the kayobe-config
[requirements](http://stackhpc-kayobe-config.readthedocs.io/en/stackhpc-2025.1/configuration/magnum-capi.html#kayobe-config)
and a baseline understanding of StackHPC’s Kayobe Config is assumed.

Documentation on `kayobe-config` can be found [here](https://stackhpc-kayobe-config.readthedocs.io/en/stackhpc-2025.1/).

### Networking

The Cluster API architecture relies on a CAPI management cluster in order to run Kubernetes operators
which directly interact with the OpenStack APIs.

This management cluster has two main requirements in order to operate:

<!-- markdownlint-disable MD007 -->

- Firstly, it must be capable of reaching the public OpenStack APIs.
- Secondly, the management cluster must be reachable from the control
  plane nodes on which the Magnum containers are running.
    - This is so that the Magnum conductor(s) may reach the management
    cluster’s API server address listed in the `kubeconfig`.
<!-- markdownlint-enable MD007 -->

### OpenStack project quotas

A standard high-availability (HA) deployment with a seed node, 3 control plane nodes and
3 worker nodes, requires the following resources:

<!-- markdownlint-disable MD007 -->

- 1 x network, 1 x subnet, 1 x router
- 1 x seed node (4 vCPU, 8 GB)
- 4 x control plane nodes (4 vCPU, 8 GB)
    - 3 x during normal operation, 4 x during rolling upgrade
- 4 x worker nodes (8 vCPU, 16 GB)
    - 3 x during normal operation, 4 x during rolling upgrade
- 3 x load-balancers
- 500GB Cinder storage
- 2 x floating IPs
    - One for accessing the seed node
    - One for the ingress controller for accessing HTTP services
<!-- markdownlint-enable MD007 -->

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
