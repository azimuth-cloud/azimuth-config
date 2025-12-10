# Automated deployments

For a production installation of Azimuth, it is recommended to adopt a
[continuous delivery](https://en.wikipedia.org/wiki/Continuous_delivery) approach to
deployment rather than running deployment commands manually. Using this approach,
configuration changes are automatically deployed to test, staging and production
environments, although deployments to production typically include a manual approval.

<!-- prettier-ignore-start -->
!!! note "Continuous delivery vs continuous deployment"
    Continuous delivery is very similar to Continuous Deployment with the exception that in continuous deployment, production deployments are also fully automated with no manual intervention or approval. See [Continuous Deployment](https://en.wikipedia.org/wiki/Continuous_deployment).

!!! tip "Using a site mixin"
    To get the maximum benefit from automated deployments and the feature branch workflow, you should try to minimise the differences between the production, staging and dynamic review environments.
<!-- prettier-ignore-end -->

More information on [feature branch workflow](../repository/index.md#making-changes-to-your-configuration) and [dynamic review environments](#per-branch-dynamic-review-environments).

```text
The best way to do this is to use a site mixin that contains all the site-specific configuration that is common between your environments, e.g. extra community images, custom Kubernetes templates, networking configuration, and include it in each of your concrete environments.
```

See docs on [site mixin](../environments.md#using-mixin-environments).

## GitLab CI/CD

`azimuth-config` provides a
[sample configuration](https://github.com/azimuth-cloud/azimuth-config/blob/stable/.gitlab-ci.yml.sample)
for use with [GitLab CI/CD](https://docs.gitlab.com/ee/ci/) that demonstrates how to
set up continuous delivery for an Azimuth configuration repository.

<!-- prettier-ignore-start -->
!!! tip
    If you are using GitLab for your configuration repository, make sure you have configured it to use GitLab-managed Terraform state.
    More information on [GitLab-managed Terraform state](../repository/opentofu.md#gitlab).

!!! warning "Runner configuration"
    Configuration of GitLab runnersfor executing CI/CD jobs is beyond the scope of this documentation.
<!-- prettier-ignore-end -->

We assume that a runner is available to the configuration project that is able to execute user-specified images, e.g. using the Docker Kubernetes executors.

One option is to deploy a runner as a VM in an OpenStack project.

Links for information on [GitLab runners](https://docs.gitlab.com/runner/), [Docker executors](https://docs.gitlab.com/runner/executors/docker.html), [Kubernetes executors](https://docs.gitlab.com/runner/executors/kubernetes.html), and [VM in an OpenStack project](https://github.com/stackhpc/gitlab-runner-openstack).

### Automated deployment environments

The sample GitLab CI/CD configuration makes use of
[GitLab environments](https://docs.gitlab.com/ee/ci/environments/) to manage
deployments of Azimuth, where each GitLab environment uses a concrete configuration
environment in your repository. This is a one-to-one relationship except for
[per-branch dynamic review environments](#per-branch-dynamic-review-environments),
where multiple GitLab environments will use a single configuration environment.

If you are using GitLab-managed Terraform state, each _GitLab environment_ (not
configuration environment) will get it's own independent state.

The sample configuration defines the following deployment jobs:

1. Each commit to a branch other than `main` (e.g. a feature branch), triggers an
   automated deployment to a **branch-specific**
   [dynamic GitLab environment](https://docs.gitlab.com/ee/ci/environments/#create-a-dynamic-environment),
   using a single [concrete configuration environment](../environments.md). These
   environments are automatically destroyed when the associated merge request is
   closed.
2. Each commit to `main` triggers an automated deployment to staging using a
   [static GitLab environment](https://docs.gitlab.com/ee/ci/environments/#create-a-static-environment).
3. Each commit to `main` also creates a job for an automated deployment to
   production, also using a static environment. However this job requires a
   [manual trigger](https://docs.gitlab.com/ee/ci/environments/#configure-manual-deployments)
   before it will start.

To get started, just copy `.gitlab-ci.yml.sample` to `.gitlab-ci.yml` and amend
the environment names and paths to match the environments in your configuration.
The next commit will begin to trigger deployments.

#### Access to secrets

In order for the deployment jobs to access the [secrets](../repository/secrets.md)
in your configuration, you will need to provide the
[git-crypt key](../repository/secrets.md#granting-access-to-others) as a
[CI/CD variable for the project](https://docs.gitlab.com/ee/ci/variables/#add-a-cicd-variable-to-a-project).
The **base64-encoded** key should be stored in the `GIT_CRYPT_KEY_B64` variable
and made available to all branches:

```sh
git-crypt export-key - | base64
```

#### Per-branch dynamic review environments

The per-branch dynamic review environments are special in that multiple GitLab
environments are provisioned using a single configuration environment. This means
that the configuration environment must be capable of producing multiple
independent deployments.

In particular, it cannot use any fixed floating IPs which also means no fixed DNS entry.
Instead it must allocate an IP for itself and use a dynamic DNS service like
[sslip.io](https://sslip.io/) for the ingress domain. This is also how the
[demo environment](../try.md) works, and is the default if no fixed IP is specified.

<!-- prettier-ignore-start -->
!!! warning "Single node only"
    At present dynamic review environments **must be single node deployments**, as HA deployments do not support dynamically allocating a floating IP for the Ingress Controller.
    A single node is likely to be sufficient for a dynamic review environment, as a full HA deployment for every branch would consume a lot more resources. However you should ensure that you have a full HA deployment as a staging or pre-production environment in order to test that the configuration works.

!!! warning "Shared credentials"
    Per-branch dynamic review environments will share the `clouds.yaml` specified in the configuration environment, and hence will share an OpenStack project.
    This is not a problem, as multiple isolated deployments can happily coexist in the same project as long as they have different names, but you must ensure that the project has suitable quotas.

!!! tip "Activating per-branch review environments"
    Because a single configuration environment is used for multiple deployments, a slight variant of the usual environment activation must be used that specifies both the configuration environment and the GitLab environment name:
    ```sh
    source ./bin/activate "<configuration environment>" "<gitlab environment>"
    ```
    See [environment activation](./index.md#activating-an-environment).
<!-- prettier-ignore-end -->

A configuration environment for dynamic review environments is set up
[in the usual way](../configuration/index.md), subject to the caveats above. The
following is a minimal set of Ansible variables that will work for most clouds, when
combined with the `base` and `singlenode` mixin environments (plus any site-specific
mixin environments):

```yaml
# Configuration for the K3s node
infra_external_network_id: "<network id>"
infra_flavor_id: "<flavor id>"

# Azimuth cloud name
#   This can use the environment name if desired, e.g.:
azimuth_current_cloud_name: "{{ lookup('env', 'CI_ENVIRONMENT_SLUG') }}"
azimuth_current_cloud_label: "{{ lookup('env', 'CI_ENVIRONMENT_NAME') }}"

# "Secrets"
#   Since the dynamic environments are short-lived, there is not much
#   risk in using secrets that are not really secret for ease
admin_dashboard_ingress_basic_auth_password: admin
harbor_admin_password: admin
harbor_secret_key: abcdefghijklmnop
keycloak_admin_password: admin
zenith_registrar_subdomain_token_signing_key: abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789AA #gitleaks:allow
azimuth_secret_key: 9876543210ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcda00 #gitleaks:allow
```

### Automated upgrades

The sample configuration also includes a job that can automatically
[propose an Azimuth upgrade](../repository/index.md#upgrading-to-a-new-azimuth-release)
when a new release becomes available.

If the job detects a new release, it will create a new branch, merge the changes
into it and create an associated
[merge request](https://docs.gitlab.com/ee/user/project/merge_requests/).
If you also have
[per-branch dynamic review environments](#per-branch-dynamic-review-environments)
enabled, then this will automatically trigger a job to deploy the changes for review.

The job will only run for a
[scheduled pipeline](https://docs.gitlab.com/ee/ci/pipelines/schedules.html), so
to enable automated upgrades you must
[add a pipeline schedule](https://docs.gitlab.com/ee/ci/pipelines/schedules.html#add-a-pipeline-schedule)
for the `main` branch of your configuration repository with a suitable interval
(e.g. weekly).

Because the job needs to write to the repository and call the merge requests API,
the [CI/CD job token](https://docs.gitlab.com/ee/ci/jobs/ci_job_token.html) is not
sufficient. Instead, you must set the CI/CD variables `GITLAB_PAT_TOKEN` and
`GITLAB_PAT_USERNAME` for the scheduled pipeline, which should contain an access
token and the corresponding username respectively. The token must have permission
to write to the repository and the GitLab API.

If your GitLab project has
[Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)
available, then one of these can be used by specifying the associated
[bot user](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html#bot-users-for-projects).
Unfortunately, this is a paid feature and the only real alternative is to use a
[Personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html).

<!-- prettier-ignore-start -->
!!! danger
    Personal access tokens cannot be scoped to a project.
    Uploading a personal access token as a CI/CD variable means that other members of the project, and the CI/CD jobs that use it, will be able to see your token.
    Because of the lack of project scope, this means that a malicious actor may be able to obtain the token and use it to access your other projects.
    If you do not want to pay for Project access tokens, then you could register a separate service account that only belongs to your configuration project and issue a personal access token from that account instead.
<!-- prettier-ignore-end -->

## GitHub CI/CD

For site-specific configuration repositories hosted on GitHub, `azimuth-config` provides two sample workflows
for automated deployments to a test or staging environment
([example workflow](https://github.com/azimuth-cloud/azimuth-config/blob/stable/.github-deploy-staging.yml.sample))
and manually-triggered deployment to a production environment
([example workflow](https://github.com/azimuth-cloud/azimuth-config/blob/stable/.github-deploy-prod.yml.sample)).
These can be used with [GitHub Actions](https://docs.github.com/en/actions) to mimic some of the GitLab
functionality described above. Each sample file contains a top-level comment describing how to tailor these
workflows to a site-specific configuration repository.

An additional [upgrade-check](https://github.com/stackhpc/azimuth-config/blob/stable/.github-upgrade-check.yml.sample)
workflow is included which will regularly check for new upstream azimuth-config releases and automatically create a
pull request in the downstream azimuth-config repository when a new upstream version is available. See the comment
at the top of the sample workflow file for more details.
