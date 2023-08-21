# Overview

Azimuth supports two distinct classes of user-facing applications - namely, Kubernetes-based apps and so called Cluster-as-a-Service (CaaS) apps. Both appear similar from an end-user perspective; however, the technologies and workflows used in developing and provision instances of these apps are very different. The Kubernetes apps are essentially packaged Helm charts with a few minor customizations to enable Zenith integration and UI form inputs for selected chart values - these are deployed directly onto Azimuth-provisioned Kubernetes clusters. On the other hand, the CaaS appliances use Terraform to provision cloud resources directly and then run custom Ansible playbooks to configure the provisioned infrastructure.

The following sections will explain the key differences between the two classes of user platforms and provide a recommended workflow for developing new Azimuth apps and adding them to your deployment.

## Default app sources

All of the default Azimuth apps are open-source and publically availble on GitHub. The following is a non-exhaustive list of relevant repos:

- [azimuth-charts](https://github.com/stackhpc/azimuth-charts) hosts the standard set of Kubernetes apps created by StackHPC
- [azimuth-images](https://github.com/stackhpc/azimuth-images) hosts the [Packer](https://www.packer.io/) templates and build pipelines for pre-building OS images used in the default Azimuth CaaS appliances
- [caas-workstation](https://github.com/stackhpc/caas-workstation) hosts the Terraform templates and (most of) the Ansible code for the Linux Workstation Azimuth app (the remaining Ansible is built into the OS image via azimuth-images)
- [caas-slurm-appliance](https://github.com/stackhpc/caas-slurm-appliance) hosts the Terraform and Ansible for the Azimuth Slurm Cluster appliance
- [caas-rstudio-server](https://github.com/stackhpc/caas-r-studio-server) hosts the Terraform and Ansible for the Azimuth RStudio server CaaS appliance 