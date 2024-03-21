# Azimuth Architecture

These docs look at the Azimuth Architecture from a deployer point of view.

For more details on Azimuth Architecture from a developer point of view, please see the
[Azimuth Architecture Developer Docs](https://github.com/stackhpc/azimuth/blob/master/docs/architecture.md).

## Azimuth Components

Lets look at the key parts of an Azimuth deployment,
working through them as they are setup by the
Ansible automation.

### Config git repository

The desired state is recorded in git.
Updating involves merging in the latest changes from the
[azimuth-config reference configuration](https://github.com/stackhpc/azimuth-config).

Good practice is to use a single git repository
for all your [Azimuth environments](./environments.md),
e.g. for both staging and production.
Similarly, `git-crypt` is recommended
for [encrypting secrets](./repository/secrets.md).

### Control host

This is where Ansible is run.

Ideally Ansible is run from within an ephemeral runner
created by [GitHub or GitLab automation](./deployment/automation.md).

### Ansible collection

TODO

### Deployment OpenStack Project

Azimuth is typically run within the OpenStack cloud it is targeting.

To isolate your Azimuth deployment from other workloads,
it is good practice to run Azimuth within a separate OpenStack project
dedicated to running Azimuth.
Moreover, production and staging deployments are typically
given their own separate OpenStack project.

### Seed VM with K3S

This VM is created using OpenTofu, within the deployment OpenStack project
used to deploy Azimuth.
We run [K3S](https://k3s.io/) in this VM.

For single node deployments, all services run here.

For HA deployments, K3S is used to run a
[Cluster API management cluster](https://cluster-api.sigs.k8s.io/user/concepts#management-cluster).
We then use the
[CAPI helm charts](https://github.com/stackhpc/capi-helm-charts)
to create a highly available kubernetes cluster.

!!! warning

    HA deployments require that [Octavia](https://docs.openstack.org/octavia/latest/index.html)
    is available on the target cloud to provide load-balancers for Azimuth components.

    For single node deployment, the seed VM is given a floating IP.

### Seed VM OpenTofu state

An [OpenTofu remote state store](./repository/terraform.md) must be configured
in order to persist the OpenTofu state used to create the Seed VM.

### Azimuth Management Kubernetes Cluster

For ha clusters, we run all Azimuth services in the HA K8s cluster.
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