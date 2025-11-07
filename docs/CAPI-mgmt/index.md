# Configuring Standalone CAPI Management Clusters

In recent years, the kubernetes
[Cluster API project](https://cluster-api.sigs.k8s.io/) has been more widely adopted for the role as
the main driver for managing OpenStack infrastructure for container orchestration engines (COE), such as Magnum.
This is the same Cluster API (CAPI) used by Azimuth and thus their configuration and operations share a lot in common.
Therefore, this document will outline how to use
[azimuth-config](https://github.com/azimuth-cloud/azimuth-config) to deploy an Azimuth-free,
standalone CAPI management cluster, using Magnum as the chosen COE.

<!-- prettier-ignore-start -->
!!! note
    This deployment of a standalone Cluster API management cluster is, as the name suggests, able to work without the backing of another cloud infrastructure.

!!! note
    It is assumed that you have already followed the steps in setting up a configuration repository, and so have an environment for your site that is ready to be configured.
    See [Setting up a configuration repository](../repository/index.md).
<!-- prettier-ignore-end -->
