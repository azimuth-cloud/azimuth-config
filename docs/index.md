# Azimuth Operator Documentation

This documentation describes how to manage deployments of
[Azimuth](https://github.com/stackhpc/azimuth), including all the required dependencies.

Azimuth is deployed using [Ansible](https://www.ansible.com/) with playbooks from the
[azimuth-ops Ansible collection](https://github.com/stackhpc/ansible-collection-azimuth-ops),
driven by configuration derived from the
[azimuth-config reference configuration](https://github.com/stackhpc/azimuth-config).

The `azimuth-config` repository is designed to be forked for a specific site and is structured
into multiple [environments](#environments). This structure allows common configuration to be
shared but overridden where required using composition of environments.

## Structure of an Azimuth deployment

A fully-featured Azimuth deployment consists of many components, such as
[Zenith](https://github.com/stackhpc/zenith), [Cluster API](https://cluster-api.sigs.k8s.io/)
and the [CaaS operator](https://github.com/stackhpc/azimuth-caas-operator), which
require a [Kubernetes](https://kubernetes.io/) cluster to run.

However when you consider an Azimuth deployment as a whole, the only _real_ dependency is
an [OpenStack](https://www.openstack.org/) cloud to target - we can create a Kubernetes
cluster within an OpenStack project on the target cloud to host our Azimuth deployment.
This is exactly what the playbooks in the `azimuth-ops` collection will do, when driven by
a configuration derived from `azimuth-config`.

There are two methods that `azimuth-ops` can use to deploy Azimuth and all of its
dependencies:

  1. Onto a managed single-node [K3S](https://k3s.io/) cluster in an OpenStack project.
  2. Onto a managed highly-available Kubernetes cluster in an OpenStack project.

Option 1 is useful for development or demo deployments, but is not suitable for a production
deployment.

Option 2 is the recommended deployment mechanism for most deployments. In this mode,
[Terraform](https://www.terraform.io/) is used to provision a single-node K3S cluster
that is configured as a [Cluster API](https://cluster-api.sigs.k8s.io/) management
cluster. Cluster API is then used to provision a highly-available Kubernetes cluster in
the same OpenStack project onto which Azimuth is deployed.

!!! warning

    Option 2 requires that [Octavia](https://docs.openstack.org/octavia/latest/index.html)
    is available on the target cloud to provide load-balancers for Azimuth components.

## Configuring and deploying Azimuth

The rest of this documentation provides details on different aspects of building a
production-ready Azimuth configuration and using it to deploy Azimuth.

In the first instance it is recommended to follow the pages in order, implementing the
steps in your Azimuth configuration. Once you have a working configuration, you can
refer back to specific sections as needed.
