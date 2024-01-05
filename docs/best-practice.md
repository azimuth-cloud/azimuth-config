# Best practice for deployments

This document guides you through the process of setting up a production-ready Azimuth
deployment following recommended best practice.

## Prerequisites

Before proceeding with an Azimuth deployment, you should ensure that the target cloud
meets the [prerequisites](./configuration/01-prerequisites.md).

## OpenStack projects

Azimuth is usually deployed on the cloud that is being targeted for workloads. It is
recommended to have three OpenStack projects for a production Azimuth deployment, to contain:

  * A highly-available (HA) production deployment, e.g. `azimuth-production`
  * A HA staging deployment, e.g. `azimuth-staging`
  * All-in-one (AIO) deployments for validating changes, e.g. `azimuth-cicd`

The production and staging projects must have
[sufficient quota](./configuration/01-prerequisites.md#prerequisites) for a HA Azimuth
deployment. The required quota in the CI/CD project will depend on the number of
proposed changes that are open concurrently.

## Repository

Before building your Azimuth configuration, you must first
[set up your configuration repository](./repository/index.md), including initialising
`git-crypt` for [encrypting secrets](./repository/secrets.md).

It is recommended to use a
[feature branch workflow](./repository/index.md#making-changes-to-your-configuration)
to make changes to your Azimuth configuration in a controlled way.

## Terraform state

Azimuth deployments use [Terraform](https://www.terraform.io/) to manage some parts of
the infrastructure.

A [Terraform remote state store](./repository/terraform.md#remote-state) must be configured
in order to persist the Terraform state across playbook executions. If GitLab is being
used for the repository, it is recommended to use
[GitLab-managed Terraform state](./repository/terraform.md#gitlab). If not,
[S3](./repository/terraform.md#s3) is the preferred approach.

## Environments

An Azimuth configuration repository contains multiple [environments](./environments.md),
some of which contain common configuration ("mixin" environments), and some of which
represent a deployment ("concrete" environments).

For a production deployment of Azimuth, there should be _at least two_ concrete environments
that are deployed from the `main` branch:

  * `production` - the Azimuth deployment that is provided to end users
  * `staging` - used to validate changes before pushing to production

Both of these environments should be
[highly-available](./configuration/02-deployment-method.md#highly-available-ha) deployments,
in order to fully test the upgrade process.

It is recommended to have a
[single node](./configuration/02-deployment-method.md#single-node) `aio` environment that
also follows the `production` environment as closely as possible. This can be used for
testing changes to the configuration before they are merged to `main`.

In order for validation in the `aio` and `staging` environments to be meaningful, the
configuration of these environments should be as similar to `production` as possible.
To do this, two site-specific mixins should be used:

  * `site` - contains configuration that is common between `aio`, `staging` and `production`,
    e.g. enabled features, available platforms
  * `site-ha` - contains configuration for the HA setup that is common between `staging`
    and `production`

The environments would then be layered as follows:

```
base --> singlenode --> site --> aio
base --> ha --> site --> site-ha --> staging
base --> ha --> site --> site-ha --> production
```

with only necessary differences configured in each environment, e.g. the ingress base domain, between `staging` and `production`.

## Continuous delivery

A production Azimuth deployment should use [continuous delivery](./deployment/automation.md),
where changes to the configuration are automatically deployed to the `aio` and `staging`
environments. The `ansible-playbook` command should **never** be executed manually.

The recommended approach is to automatically deploy an independent `aio` environment for each
feature branch, also known as
[per-branch dynamic review environments](deployment/automation/#per-branch-dynamic-review-environments).
This allows changes to be validated before they are merged to `main`.

Once a change is merged to `main`, it will be deployed automatically to the `staging` environment.
Merging to `main` will also create a job to deploy to `production`, but that job will require a
manual trigger. Once the change has been validated in `staging`, the job to deploy to `production`
can be actioned.

A
[sample GitLab CI/CD configuration](https://github.com/stackhpc/azimuth-config/tree/main/.gitlab-ci.yml.sample)
is provided that implements this workflow for GitLab-hosted repositories.

## Disaster recovery

Azimuth uses [Velero](https://velero.io/) to backup the data that is required to restore an
Azimuth instance in the event of a catastrophic failure. This functionality is not enabled by
default, as it requires credentials for an S3 bucket in which the backups will be stored.

It is recommended that [disaster recovery is enabled](./configuration/14-disaster-recovery.md) for
a production deployment.

## Configuration

You are now ready to begin adding configuration to your environments. When building an environment
for the first time, it is recommended to follow each documentation page in order, beginning with
the [Deployment method](./configuration/02-deployment-method.md).
