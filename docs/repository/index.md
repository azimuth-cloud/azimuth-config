# Azimuth configuration repository

The `azimuth-config` repository provides best-practice configuration for Azimuth deployments
that can be inherited by site-specific configuration repositories using
[Git](https://git-scm.com/). Using Git makes it easy to pick up new Azimuth releases when
they become available.

## Initial repository setup

First make an empty Git repository using your service of choice (e.g.
[GitHub](https://github.com/) or [GitLab](https://about.gitlab.com/)), then execute the
following commands to turn the new empty repository into a copy of the `azimuth-config`
repository:

```sh
# Clone the azimuth-config repository
git clone https://github.com/azimuth-cloud/azimuth-config.git my-azimuth-config
cd my-azimuth-config

# Maintain the existing origin remote as upstream
git remote rename origin upstream

# Create a new origin remote for the repository location
git remote add origin git@<repo location>/my-azimuth-config.git

# Create a new main branch from devel
# This will be the branch that is deployed into production
git checkout -b main

# Push the main branch to the origin
git push --set-upstream origin main
```

You now have an independent copy of the `azimuth-config` repository that has a link back
to the source repository via the `upstream` remote.

!!! tip  "Branch protection rules"

    It is a good idea to apply branch protection rules to the `main` branch that enforce
    that all changes are made via a merge (or pull) request. This should ensure that changes
    are not accidentally pushed into production without being reviewed.

    Instructions are available on how to set this up for
    [GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule) or
    [GitLab](https://docs.gitlab.com/ee/user/project/protected_branches.html).


## Creating a new environment

Your new repository does not yet contain any site-specific configuration. The best way
to do this is to copy the `example` environment as a starting point:

```sh
cp -r ./environments/example ./environments/my-site
```

!!! tip  "Copy instead of rename"

    Copying the `example` environment, rather than just renaming it, avoids conflicts
    when synchronising changes from the `azimuth-config` repository where the `example`
    environment has changed.

Once you have your new environment, you can make the required changes for your site.

!!! tip  "Generating secrets"

    `azimuth-config` includes a utility that can be used to generate secrets for your
    environment:

    ```sh
    ./bin/generate-secrets --force my-site
    ```

    `--force` is required because the `example` environment includes an example secrets
    file that we want to overwrite with the generated secrets.

As you make changes to your environment, remember to commit and push them regularly:

```sh
git add ./environments/my-site
git commit -m "Made some changes to my environment"
git push
```

## Making changes to your configuration

Once you have an environment deployed, it is recommended to use a
[feature branch workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow)
when making changes to your configuration repository.

!!! tip "Automated deployments"

    The feature branch workflow works particularly well when you use a
    [continuous delivery approach to automate deployments](../deployment/automation.md).

In this workflow, the required changes are made on a branch in the configuration repository.
Once you are happy with the changes, you create a merge (or pull) request proposing the
changes to `main`. These changes can then be reviewed before being merged to `main`.

If you have automated deployments, the branch may even get a dynamic environment created
for it where the result of the changes can be verified before the merge takes place.

## Upgrading to a new Azimuth release

When a new Azimuth release becomes available, you will need to synchronise the changes
from `azimuth-config` into your site configuration repository in order to pick up new
component versions, upgraded dependencies and new images.

!!! info  "Choosing a release"

    The available releases, with associated release notes, can be reviewed on the
    [Azimuth releases page](https://github.com/azimuth-cloud/azimuth-config/releases).

!!! tip  "Automating upgrades"

    If you have automated deployments, which is recommended for a production installation,
    this process
    [can also be automated](../deployment/automation.md#automated-synchronisation-of-upstream-changes).

To upgrade your Azimuth configuration to a new release, use the following steps to create
a new branch containing the upgrade:

```sh
# Make sure the local checkout is up to date with any site-specific changes
git checkout main
git pull

# Fetch the tags from the upstream repo
git remote update

# Create a new branch to contain the Azimuth upgrade
git checkout -b upgrade/$RELEASE_TAG

# Merge in the tag for the new release
git merge $RELEASE_TAG
```

At this point, you will need to fix any conflicts where you have made changes to the same
files that have been changed by `azimuth-config`.

!!! danger  "Avoiding conflicts"

    To avoid conflicts, you should **never** directly modify any files that come from
    `azimuth-config` - instead you should use the environment layering to override
    variables where required, and copy files if necessary.

Once any conflicts have been resolved, you can commit and push the changes:

```sh
git commit -m "Upgrade Azimuth to $RELEASE_TAG"
git push --set-upstream origin upgrade/$RELEASE_TAG
```

You can now open a merge (or pull) request proposing the upgrade to your `main` branch
that can be reviewed like any other.
