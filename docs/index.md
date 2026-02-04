# Azimuth Operator Documentation

This documentation describes how to manage deployments of
[Azimuth](https://github.com/azimuth-cloud/azimuth), including all the required dependencies.

## Deploying Azimuth

Azimuth is deployed using [Ansible](https://www.ansible.com/) with playbooks from the
[azimuth-ops Ansible collection](https://github.com/azimuth-cloud/ansible-collection-azimuth-ops),
driven by configuration derived from the
[azimuth-config reference configuration](https://github.com/azimuth-cloud/azimuth-config).

The `azimuth-config` repository is designed to be forked for a specific site and is structured
into multiple [environments](environments.md). This structure allows common configuration to be
shared but overridden where required using composition of environments.

To try out Azimuth on your OpenStack cloud, you can follow [these instructions](./try.md)
to get a simple single-node deployment.

For a production-ready deployment, you should follow the steps in the
[production configuration document](./production.md).

## Structure of an Azimuth deployment

A fully-featured Azimuth deployment consists of many components, such as
[Zenith](https://github.com/azimuth-cloud/zenith), [Cluster API](https://cluster-api.sigs.k8s.io/)
and the [CaaS operator](https://github.com/azimuth-cloud/azimuth-caas-operator), which
require a [Kubernetes](https://kubernetes.io/) cluster to run.

However when you consider an Azimuth deployment as a whole, the only _real_ dependency is
an [OpenStack](https://www.openstack.org/) cloud to target - we can create a Kubernetes
cluster within an OpenStack project on the target cloud to host our Azimuth deployment.
This is exactly what the playbooks in the `azimuth-ops` collection will do, when driven by
a configuration derived from `azimuth-config`.

Alternatively, an experimental [kubernetes only mode](./configuration/17-standalone-mode.md) is currently in development which can deploy Azimuth onto any Kubernetes cluster (with limited functionality).

There are two methods that `azimuth-ops` can use to deploy Azimuth and all of its
dependencies:

1. Onto a managed single-node [K3s](https://k3s.io/) cluster in an OpenStack project.
2. Onto a managed highly-available Kubernetes cluster in an OpenStack project.

Option 1 is useful for development or demo deployments, but is not suitable for a production
deployment.

Option 2 is the recommended deployment mechanism for most deployments. In this mode,
[OpenTofu](https://opentofu.org/), an open-source fork of [Terraform](https://www.terraform.io/),
is used to provision a single-node K3s cluster that is configured as a
[Cluster API](https://cluster-api.sigs.k8s.io/) management cluster. Cluster API is then
used to provision a highly-available Kubernetes cluster in the same OpenStack project
onto which Azimuth is deployed.

<!-- prettier-ignore-start -->
!!! warning
    Option 2 requires that Octavia is available on the target cloud to provide load-balancers for Azimuth components.
    See [Octavia](https://docs.openstack.org/octavia/latest/index.html).
<!-- prettier-ignore-end -->
