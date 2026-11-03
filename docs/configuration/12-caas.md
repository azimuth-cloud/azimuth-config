# Cluster-as-a-Service (CaaS)

Cluster-as-a-Service (CaaS) in Azimuth allows self-service platforms to be provided to
users that are deployed and configured using a combination of [Ansible](https://www.ansible.com/),
[OpenTofu](https://opentofu.org/) and [Packer](https://www.packer.io/), stored in
a [Git](https://git-scm.com/) repository.

CaaS support in Azimuth is implemented by the
[Azimuth CaaS operator](https://github.com/azimuth-cloud/azimuth-caas-operator).
The operator executes Ansible playbooks using
[ansible-runner](https://ansible.readthedocs.io/projects/runner/en/stable/) in response
to Azimuth creating and modifying instances of the
[custom resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
that it exposes:

`clustertypes.caas.azimuth.stackhpc.com`
: A cluster type represents an available appliance, e.g. "workstation" or "Slurm cluster".
This CRD defines the Git repository, version and playbook that will be used to deploy
clusters of the specified type, along with metadata for generating the UI and any
global variable such as image UUIDs.

`clusters.caas.azimuth.stackhpc.com`
: A cluster represents the combination of a cluster type with values collected from the user.
The CaaS operator tracks the status of the `ansible-runner` executions for the cluster and
reports it on the CRD for Azimuth to consume.

## Disabling CaaS

CaaS support is enabled by default in the reference configuration. To disable it, just
set:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_clusters_enabled: no
```

## Standard Appliances

The standard appliances include the
[StackHPC Slurm appliance](https://github.com/stackhpc/ansible-slurm-appliance), the
[Linux Workstation appliance](https://github.com/azimuth-cloud/caas-workstation) and
[RStudio](https://github.com/azimuth-cloud/caas-r-studio-server).
These are enabled by default when CaaS is enabled.

### StackHPC Slurm appliance

The Slurm appliance allows users to deploy [Slurm](https://slurm.schedmd.com/documentation.html)
clusters for running batch workloads. The clusters include the [Open OnDemand](https://openondemand.org/)
web interface and a monitoring stack with web dashboards, both of which are exposed using
Zenith.

To disable the Slurm appliance, use the following:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_stackhpc_slurm_appliance_enabled: no
```

### Linux Workstation appliance

The Linux Workstation appliance allows users to provision a workstation that is accessible
via a web-browser using [Apache Guacamole](https://guacamole.apache.org/). Guacamole provides
a web-based virtual desktop and a console, and is exposed using Zenith. A simple monitoring
stack is also available, exposed via Zenith.

To disable the Linux Workstation appliance, use the following:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_workstation_enabled: no
```

A workstation variant with external SSH access is also enabled by default. To disable
only that variant, set `azimuth_caas_workstation_ssh_enabled: no`.

### repo2docker appliance

The repo2docker appliance allows users to deploy a [Jupyter Notebook](https://jupyter.org/)
server, exposed via Zenith, from a [repo2docker](https://repo2docker.readthedocs.io/en/latest/)
compliant repository. A simple monitoring stack is also available, exposed via Zenith.

This appliance is marked as deprecated on the [`azimuth-ops` main branch](https://github.com/azimuth-cloud/ansible-collection-azimuth-ops/pull/1430).
It remains enabled by default in `azimuth-ops` 0.34.0 when CaaS is enabled.

To disable the repo2docker appliance, use the following:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_repo2docker_enabled: no
```

### R-studio appliance

The R-studio appliance allows users to deploy an
[R-studio server](https://posit.co/products/open-source/rstudio-server/)
instance running on a cloud VM. A simple monitoring stack is also provided,
with both the R-studio and monitoring services exposed via Zenith.

To disable the R-studio appliance, use the following:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_rstudio_enabled: no
```

## Custom appliances

It is possible to make custom appliances available in the Azimuth interface for users to deploy.
For more information on building a CaaS-compatible appliance, please see the
[sample appliance](https://github.com/azimuth-cloud/azimuth-sample-appliance).

Custom appliances can be specified in your Azimuth configuration. For example, the following will configure the sample appliance as an available cluster type.
Replace `<image-uuid>` with the UUID of an image on your OpenStack cloud that meets the appliance's requirements. Images can be uploaded using the
[community images configuration](./09-community-images.md#custom-images).

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_cluster_templates_overrides:
  sample-appliance:
    # Access control annotations
    annotations: {}
    # The cluster type specification
    spec:
      # The git URL of the appliance
      gitUrl: https://github.com/azimuth-cloud/azimuth-sample-appliance.git
      # The branch, tag or commit id to use
      # For production, it is recommended to use a fixed tag or commit ID
      gitVersion: main
      # The name of the playbook to use
      playbook: sample-appliance.yml
      # The URL of the metadata file
      uiMetaUrl: https://raw.githubusercontent.com/azimuth-cloud/azimuth-sample-appliance/main/ui-meta/sample-appliance.yml
      # Dict of extra variables for the appliance
      extraVars:
        # Use the UUID of an image suitable for this appliance
        cluster_image: "<image-uuid>"
```

<!-- prettier-ignore-start -->
!!! info "Access control"
    See Access control for more details on the access control annotations.
    [Access control](./13-access-control.md).
<!-- prettier-ignore-end -->
