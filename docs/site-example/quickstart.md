# Operator Quickstart

This is an operator quickstart guide for the **_example-cloud_** Azimuth deployment.

## Getting started

To start working with the **_example-cloud_** Azimuth deployment a new operator first must be
granted access to the configuration repository's [encrypted secrets](../repository/secrets.md).
The recommended way to do so is using [GPG keys](../repository/secrets.md#granting-access-to-others).

The **_example-cloud_** Azimuth configuration is managed via CI/CD, meaning that the correct process for
applying configuration changes is to create a pull request into the **_example-cloud_** azimuth-config
repository and have it reviewed by another team member. Once the change has been approved, merging the
pull request will trigger an automatic deployment of the updated configuration to the Azimuth staging
environment. Once a change has been deployed and tested in staging, the equivalent CI job for deploying
the change to the production Azimuth environment should be triggered manually by an operator via the
<GitLab-or-GitHub> UI.

## Useful links

The **_example-cloud_** Azimuth includes a useful set of monitoring dashboards and tools for operators.
A general overview of the available tools can be found
[here](https://azimuth-config.readthedocs.io/en/stable/configuration/14-monitoring/) and the
_example-cloud_ instances

- _Insert list of links to Grafana, Alert Manager etc._

For an introduction to the available configuration options for an Azimuth deployment, see
[here](https://azimuth-config.readthedocs.io/en/stable/configuration/).

## Custom **_example-cloud_** Azimuth Apps

_Optional: Describe any custom site-specific Azimuth apps here and link to the relevant configuration
sections in the downstream azimuth-config repository._

## Notable **_example-cloud_** configuration

_Optional: Desribe any important ways in which this downstream configuration differs from the upstream Azimuth
defaults, e.g. custom networking or storage integrations or explicitly enabled or disabled experimental
features._
