# Customising the Azimuth configuration

The
[roles in the azimuth-ops collection](https://github.com/azimuth-cloud/ansible-collection-azimuth-ops/tree/main/roles)
support a vast array of variables to customise an Azimuth deployment. However `azimuth-ops`
endeavours to pick sensible defaults where appropriate, so this documentation focuses on
configuration that is required or commonly changed.

For more advanced cases, the role defaults files are extensively documented and can be
consulted directly.

<!-- prettier-ignore-start -->
!!! note
    Make sure you are familiar with the Azimuth and Zenith architectures before continuing.
    See [Azimuth](https://github.com/azimuth-cloud/azimuth/blob/master/docs/architecture.md) and [Zenith](https://github.com/azimuth-cloud/zenith/blob/main/docs/architecture.md).

!!! note
    It is assumed that you have already followed the steps in setting up a configuration repository, and so have an environment for your site that is ready to be configured.
    See [Setting up a configuration repository](../repository/index.md).
<!-- prettier-ignore-end -->
