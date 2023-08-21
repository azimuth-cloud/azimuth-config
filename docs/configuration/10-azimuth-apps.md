## Overview

Azimuth supports two distinct classes of user-facing applications - namely, Kubernetes-based apps and so called Cluster-as-a-Service (CaaS) apps. Both appear similar from an end-user perspective; however, the technologies and workflows used in developing and provision instances of these apps are very different. The Kubernetes apps are essentially packaged Helm charts with a few minor customizations to enable Zenith integration and UI form inputs for selected chart values - these are deployed directly onto Azimuth-provisioned Kubernetes clusters. On the other hand, the CaaS appliances use Terraform to provision cloud resources directly and then run custom Ansible playbooks to configure the provisioned infrastructure.

The following sections will explain the key differences between the two classes of user platforms and provide a recommended workflow for developing new Azimuth apps and adding them to your deployment.
