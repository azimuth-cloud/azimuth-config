# Environments

An Azimuth configuration repository is structured as multiple "environments" that can be
composed. Some of these environments are "concrete", meaning that they provide enough
information to make a deployment (e.g. development, staging, production), and some are
"mixin" environments providing common configuration that can be incorporated into concrete
environments using
[Ansible's support for multiple inventories](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html#using-multiple-inventory-sources).

A concrete environment must be "activated" before any operations can be performed.

Environments live in the `environments` directory of your configuration repository. A mixin
environment contains only `group_vars` files and an empty hosts file (so that Ansible treats
it as an inventory). A concrete environment must contain an `ansible.cfg` file defining the
"layering" of inventories and a `clouds.yaml` file containing an
[OpenStack Application Credential](https://docs.openstack.org/keystone/latest/user/application_credentials.html)
for the project into which Azimuth will be deployed.

## Using mixin environments

The following fragment demonstrates how to layer inventories in the `ansible.cfg` file for
a highly-available (HA) deployment:

```ini title="ansible.cfg"
[defaults]
inventory = ../base/inventory,../ha/inventory,./inventory
```

For a single node deployment, replace the `ha` environment with `singlenode`.

<!-- prettier-ignore-start -->
!!! tip
    If the same variable is defined in multiple inventories, the right-most inventory takes precedence.
<!-- prettier-ignore-end -->

## Available mixin environments

The following mixin environments are provided and maintained in this repository, and should
be used as the basis for your concrete environments:

`base`
: Contains the core configuration required to enable an environment and sets defaults.

`ha`
: Contains overrides that are specific to an HA deployment.

`singlenode`
: Contains overrides that are specific to a single-node deployment.

By keeping the `azimuth-config` repository as an upstream of your site configuration repository,
you can rebase onto or merge the latest configuration to pick up changes to these mixins.

The `azimuth-config` repository contains an example of a concrete environment in
[environments/example](https://github.com/azimuth-cloud/azimuth-config/tree/stable/environments/example)
that should be used as a basis for your own concrete environment(s).

Depending how many concrete environments you have, you may wish to define mixin environments
containing site-specific information that is common to several concrete environments, e.g. image
and flavor IDs or the location of an ACME server.

A typical layering of inventories might be:

```text
base -> singlenode -> site -> development
base -> ha -> site -> staging
base -> ha -> site -> production
```

## Linux environment variables

`azimuth-config` environments are able to define Linux environment variables that are exported
into the current shell when the environment is activated. This is accomplished by using
statements of the form:

```bash title="env"
MY_VAR="some value"
```

The
[azimuth-config activate script](https://github.com/azimuth-cloud/azimuth-config/tree/stable/bin/activate)
exports environment variables defined in the following files:

`env` and `env.secret`
: Contain environment variables that are common across all environments.

`environments/<env name>/env` and `environments/<env name>/env.secret`
: Contain environment variables that are specific to the environment.

In both cases, environment variables whose values should be kept private should be placed in
the `env.secret` variant and [should be encrypted](./repository/secrets.md).
