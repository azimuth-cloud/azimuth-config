# Azimuth Architecture

These docs look at the Azimuth Architecture from an operator's point of view.

For more details on Azimuth Architecture from a developer point of view, please see the
[Azimuth Architecture Developer Docs](https://github.com/stackhpc/azimuth/blob/master/docs/architecture.md).

## Azimuth Components

The following sections highlight the key parts of an Azimuth deployment,
working through them in the order that they are setup by the Ansible automation.

### Config git repository

The desired state is recorded in git.
Updating involves merging in the latest changes from the
[azimuth-config reference configuration](https://github.com/stackhpc/azimuth-config).

It is recommmended to use a single git repository
for all your [Azimuth environments](./environments.md),
e.g. for both staging and production.
Similarly, `git-crypt` should be used
for [encrypting secrets](./repository/secrets.md).

### Control host

This is where Ansible is run. Ideally, this should be from within an ephemeral runner
created by [GitHub or GitLab automation](./deployment/automation.md). The control host must
be able to reach the OpenStack public API endpoints for the target cloud.

### Ansible collection

The [azimuth-ops](https://github.com/stackhpc/ansible-collection-azimuth-ops/) Ansible collection
contains all of the roles and playbooks required to deploy and update Azimuth. The
[provision](https://github.com/stackhpc/ansible-collection-azimuth-ops/blob/main/playbooks/provision.yml)
playbook provides the main entry point into the Ansible collection.

### Deployment OpenStack Project

Azimuth management infrastructure is typically run within the OpenStack cloud it is targeting.

To isolate your Azimuth manangement infrastructure from other workloads,
it is good practice to run Azimuth within a separate dedicated OpenStack project.
Moreover, production and staging deployments are typically
given their own separate OpenStack project.

### Seed VM with K3S

This VM is created in the deployment OpenStack project using OpenTofu.
A light-weight [K3S](https://k3s.io/) cluster is run on the seed node, with all
K3S data stored in a dedicated Cinder volume mounted at `/var/lib/rancher/`,
allowing the seed VM to be upgraded or recreated without data loss (as long as the
Cinder volume is preserved).

For single node deployments, all Azimuth components run on the seed's K3S cluster.

For highly-available (HA) deployments, K3S is instead used to run a
[Cluster API management cluster](https://cluster-api.sigs.k8s.io/user/concepts#management-cluster).
which in turn uses [CAPI Helm charts](https://github.com/stackhpc/capi-helm-charts)
to create a highly-available Kubernetes cluster for hosting the Azimuth management components.

!!! warning

    HA deployments require that [Octavia](https://docs.openstack.org/octavia/latest/index.html)
    is available on the target cloud to provide load-balancers for Azimuth components.

    For single node deployment, the seed VM is given a floating IP.

### Seed VM OpenTofu state

An [OpenTofu remote state store](./repository/terraform.md) must be configured
in order to persist the OpenTofu state used to create the Seed VM. This state store is accessed,
for example, when [accessing the seed VM](https://stackhpc.github.io/azimuth-config/debugging/access-k3s/).

### Azimuth Management Kubernetes Cluster

For HA deployments, we run all Azimuth services in the HA K8s cluster.
For the single node deployment, we run everything in K3s on the seed VM.
For simplicity we call this the Azimuth Management Cluster.

For more details about the architecture of the Azimuth services, please see the
[Azimuth Architecture Developer Docs](https://github.com/stackhpc/azimuth/blob/master/docs/architecture.md).

### CaaS images, templates and workloads

TODO

### Kubernetes images, templates and workloads

TODO

### Kubernetes application templates

TODO

### Zenith

TODO

### Azimuth Ingress and SSL

Most Azimuth traffic goes through a single wildcard DNS entry.
This includes: ...

TODO

### Azimuth Monitoring and Alerting

TODO

### Workload OpenStack Projects

When a user logs into Azimuth, they select a tenancy.
This maps to a specific OpenStack Project.

### Azimuth CRDs

Azimuth doesn't have a database, as such.

TODO


### Backup and Disaster recovery

TODO

## Authentication and Authorization

Azimuth currently delegates all authentication and authorization to OpenStack.

In many ways, you can consider the Azimuth to be
a sophisticated OpenStack client,
similar to Horizon and the OpenStack CLI.

Any user with access to an OpenStack project,
will see that project listed as a tenancy within Azimuth.
In addition, people with access to that OpenStack project
get full access to all platforms created within that tenancy.

We make an assumption that all users with access to the OpenStack
API can elevate themselves to have "root access" within any VM
in that OpenStack project. This is a feature of OpenStack's APIs.

There are plans for "managed" tenancies within Azimuth,
where users do not get "root access".
This will depend on OpenStack efforts around adding the
project-reader role into 2024.1 release.
For more details, please see
[OpenStack consistent RBAC](https://governance.openstack.org/tc/goals/selected/consistent-and-secure-rbac.html).

### Upstairs and Downstairs

TODO

### Keycloak

TODO
