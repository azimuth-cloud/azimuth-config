# Cluster-as-a-Service (CaaS)

Cluster-as-a-Service (CaaS) is enabled by default in the reference documentation. To disable it,
just set:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_clusters_enabled: no
```

As discussed in the Azimuth architecture document, the appliances exposed to users via the
Azimuth UI are determined by
[projects](https://docs.ansible.com/ansible-tower/latest/html/userguide/projects.html) and
[job templates](https://docs.ansible.com/ansible-tower/latest/html/userguide/job_templates.html)
in [AWX](https://github.com/ansible/awx).

As used by CaaS, a project is essentially a Git repository containing Ansible playbooks, and
the job templates correspond to individual playbooks within those projects.

It is entirely possible to configure the available appliances using only the AWX UI. However
`azimuth-ops` allows you to define the available appliances using Ansible variables.

## AWX admin password

The only required configuration for CaaS is to set the admin password for AWX:

```yaml  title="environments/my-site/inventory/group_vars/all/secrets.yml"
awx_admin_password: "<secure password>"
```

!!! danger

    This password should be kept secret. If you want to keep the password in Git - which is
    recommended - then it [must be encrypted](../repository/secrets.md).

## StackHPC Appliances

By default, three appliances maintained by StackHPC are made available - the
[Slurm appliance](https://github.com/stackhpc/caas-slurm-appliance), the
[Linux Workstation appliance](https://github.com/stackhpc/caas-workstation) and the
[repo2docker appliance](https://github.com/stackhpc/caas-repo2docker).

### Slurm appliance

The Slurm appliance allows users to deploy [Slurm](https://slurm.schedmd.com/documentation.html)
clusters for running batch workloads. The clusters include the [Open OnDemand](https://openondemand.org/)
web interface and a monitoring stack with web dashboards, both of which are exposed using
Zenith.

To disable the Slurm appliance, use the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_stackhpc_slurm_appliance_enabled: no
```

The Slurm appliance requires the following configuration:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# The name of a flavor to use for Slurm login nodes
#   A flavor with at least 2 CPUs and 4GB RAM should be used
azimuth_caas_stackhpc_slurm_appliance_login_flavor_name: "<flavor name>"

# The name of a flavor to use for Slurm control nodes
#   A flavor with at least 2 CPUs and 4GB RAM should be used
azimuth_caas_stackhpc_slurm_appliance_control_flavor_name: "<flavor name>"
```

### Linux Workstation appliance

The Linux Workstation appliance allows users to provision a workstation that is accessible
via a web-browser using [Apache Guacamole](https://guacamole.apache.org/). Guacamole provides
a web-based virtual desktop and a console, and is exposed using Zenith. A simple monitoring
stack is also available, exposed via Zenith.

To disable the Linux Workstation appliance, use the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_stackhpc_workstation_enabled: no
```

### repo2docker appliance

The repo2docker appliance allows users to deploy a [Jupyter Notebook](https://jupyter.org/)
server, exposed via Zenith, from a [repo2docker](https://repo2docker.readthedocs.io/en/latest/)
compliant repository. A simple monitoring stack is also available, exposed via Zenith.

To disable the repo2docker appliance, use the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_stackhpc_repo2docker_enabled: no
```

## Custom appliances

It is possible to make custom appliances available in the Azimuth interface for users to deploy.
For more information on building a CaaS-compatible appliance, please see the
[sample appliance](https://github.com/stackhpc/azimuth-sample-appliance).

Custom appliances can be specified with the following configuration:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_caas_awx_extra_projects:
  - # The name of the appliance project in AWX
    name: StackHPC Sample Appliance
    # The git URL of the appliance
    gitUrl: https://github.com/stackhpc/azimuth-sample-appliance.git
    # The branch, tag or commit id to use
    # For production, it is recommended to use a fixed tag or commit ID
    gitVersion: master
    # The base URL for cluster metadata files
    metadataRoot: https://raw.githubusercontent.com/stackhpc/azimuth-sample-appliance/{gitVersion}/ui-meta
    # List of playbooks that correspond to appliances
    playbooks: [sample-appliance.yml]
    # Dict of extra variables for appliances
    #   The keys are the playbooks
    #   The values are maps of Ansible extra_vars for those playbooks
    #   The special key __ALL__ can be used to set common extra_vars for
    #     all playbooks in a project
    extraVars:
      __ALL__:
        # Use the ID of an Ubuntu 20.04 image that we asked azimuth-ops to upload
        cluster_image: "{{ community_images_image_ids.ubuntu_2004_20220712 }}"
```
