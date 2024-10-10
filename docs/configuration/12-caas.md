# Cluster-as-a-Service (CaaS)

Cluster-as-a-Service (CaaS) in Azimuth allows self-service platforms to be provided to
users that are deployed and configured using a combination of [Ansible](https://www.ansible.com/),
[OpenTofu](https://opentofu.org/) and [Packer](https://www.packer.io/), stored in
a [git](https://git-scm.com/) repository.

CaaS support in Azimuth is implemented by the
[Azimuth CaaS operator](https://github.com/azimuth-cloud/azimuth-caas-operator).
The operator executes Ansible playbooks using
[ansible-runner](https://ansible.readthedocs.io/projects/runner/en/stable/) in response
to Azimuth creating and modifying instances of the
[custom resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
that it exposes:

`clustertypes.caas.azimuth.stackhpc.com`
: A cluster type represents an available appliance, e.g. "workstation" or "Slurm cluster".
  This CRD defines the git repository, version and playbook that will be used to deploy
  clusters of the specified type, along with metadata for generating the UI and any
  global variable such as image UUIDs.

`clusters.caas.azimuth.stackhpc.com`
: A cluster represents the combination of a cluster type with values collected from the user.
  The CaaS operator tracks the status of the `ansible-runner` executions for the cluster and
  reports it on the CRD for Azimuth to consume.

## Disabling CaaS

CaaS support is enabled by default in the reference configuration. To disable it, just
set:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_clusters_enabled: no
```

## Removing legacy AWX components

If you are migrating from an installation using the previous AWX implementation then
Azimuth itself will be reconfigured to use the CaaS CRD, but by default the AWX
installation will be left untouched in order to allow any legacy apps to be cleaned up.

To remove AWX components, an additional variable must be set when the `provision` playbook
is executed:

```sh
ansible-playbook azimuth_cloud.azimuth_ops.provision -e awx_purge=yes
```

## Standard Appliances

By default, three standard appliances are made available - the
[StackHPC Slurm appliance](https://github.com/stackhpc/ansible-slurm-appliance), the
[Linux Workstation appliance](https://github.com/azimuth-cloud/caas-workstation) and the
[repo2docker appliance](https://github.com/azimuth-cloud/caas-repo2docker).

### StackHPC Slurm appliance

The Slurm appliance allows users to deploy [Slurm](https://slurm.schedmd.com/documentation.html)
clusters for running batch workloads. The clusters include the [Open OnDemand](https://openondemand.org/)
web interface and a monitoring stack with web dashboards, both of which are exposed using
Zenith.

To disable the Slurm appliance, use the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_stackhpc_slurm_appliance_enabled: no
```

### Linux Workstation appliance

The Linux Workstation appliance allows users to provision a workstation that is accessible
via a web-browser using [Apache Guacamole](https://guacamole.apache.org/). Guacamole provides
a web-based virtual desktop and a console, and is exposed using Zenith. A simple monitoring
stack is also available, exposed via Zenith.

To disable the Linux Workstation appliance, use the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_workstation_enabled: no
```

### repo2docker appliance

The repo2docker appliance allows users to deploy a [Jupyter Notebook](https://jupyter.org/)
server, exposed via Zenith, from a [repo2docker](https://repo2docker.readthedocs.io/en/latest/)
compliant repository. A simple monitoring stack is also available, exposed via Zenith.

To disable the repo2docker appliance, use the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_repo2docker_enabled: no
```

### R-studio appliance

The R-studio appliance allows users to deploy an
[R-studio server](https://posit.co/products/open-source/rstudio-server/)
instance running on a cloud VM. A simple monitoring stack is also provided,
with both the R-studio and monitoring services exposed via Zenith.

To disable the R-studio appliance, use the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_rstudio_enabled: no
```

## Custom appliances

It is possible to make custom appliances available in the Azimuth interface for users to deploy.
For more information on building a CaaS-compatible appliance, please see the
[sample appliance](https://github.com/azimuth-cloud/azimuth-sample-appliance).

Custom appliances can be easily specified in your Azimuth configuration. For example,
the following will configure the sample appliance as an available cluster type:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
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
      uiMetaUrl: https://raw.githubusercontent.com/azimuth-cloud/azimuth-sample-appliance/main/ui-meta/sample-appliance.yaml
      # Dict of extra variables for the appliance
      extraVars:
        # Use the ID of an Ubuntu 20.04 image that we asked azimuth-ops to upload
        cluster_image: "{{ community_images_image_ids.ubuntu_2004_20220712 }}"
```

!!! info  "Access control"

    See [Access control](./13-access-control.md) for more details on the access
    control annotations.
