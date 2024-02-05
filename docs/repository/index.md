# Azimuth configuration repository

The `azimuth-config` repository provides best-practice configuration for Azimuth deployments
that can be inherited by site-specific configuration repositories using
[Git](https://git-scm.com/). Using Git makes it easy to periodically incorporate changes to
the best practice into the configuration for your site, e.g. to pick up new Azimuth versions,
updated images, CaaS appliance versions or Kubernetes versions.

## Initial repository setup

First make an empty Git repository using your service of choice (e.g.
[GitHub](https://github.com/) or [GitLab](https://about.gitlab.com/)), then execute the
following commands to turn the new empty repository into a copy of the `azimuth-config`
repository:

```sh
# Clone the azimuth-config repository
git clone https://github.com/stackhpc/azimuth-config.git my-azimuth-config

cd my-azimuth-config

# Maintain the existing origin remote so that we can periodically sync changes,
# but rename it to upstream
git remote rename origin upstream

# Create a new origin remote for the new repository location
git remote add origin git@<repo location>/my-azimuth-config.git

# Checkout stable to get the latest release
git checkout stable

# Create a new main branch for your local repo
git checkout -b main
git push --set-upstream origin main --tags
```

You now have an independent copy of the `azimuth-config` repository that has a link back
to the source repository via the `upstream` remote.

!!! tip

    This is a good point to add branch protection to your local
    repository, to ensure all changes are reviewed in a pull/merge request,
    and people do not accidentially push their changes into the branch
    used to deploy into production.


## Creating a new environment

Your new repository does not yet contain any site-specific configuration. The best way
to do this is to copy the `example` environment as a starting point:

```sh
cp -r ./environments/example ./environments/my-site
```

!!! tip

    Copying the `example` environment, rather than just renaming it, avoids conflicts
    when synchronising changes from the `azimuth-config` repository where the `example`
    environment has changed.

Once you have your new environment, you can make the required changes for your site.

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

## Synchronising changes from upstream

Over time, as Azimuth changes, the best-practice configuration will also change to point
at new Azimuth versions, upgraded dependencies and new images.

!!! tip

    This process
    [can be automated](../deployment/automation.md#automated-synchronisation-of-upstream-changes)
    if you have the tooling available.

The first step is to choose the release you want to apply.
You can review the latest release tags and the associated release notes here:
https://github.com/stackhpc/azimuth-config/releases

To incorporate the latest changes into your site-specific repository, use the following
to update your local checkout. First merge the tag you want to sync into a branch,
then use that branch to open a pull/merge request to your site-specific repository:

```sh
# get the latest local and upstream changes
git remote update
git checkout origin/main

# create a branch in which to merge the upstream changes
git checkout -b sync/<chosen-tag>
git merge <chosen-tag>
```

At this point, you will need to fix any conflicts where you have made changes to the same
files that have been changed by `azimuth-config`.

!!! danger  "Avoiding conflicts"

    To avoid conflicts, you should **never** directly modify any files that come from
    `azimuth-config` - instead you should use the environment layering to override
    variables where required, and copy files if necessary.

Once any conflicts have been resolved, you can commit and push the changes,
being sure to push the new tags you have pulled in from the upstream repo:

```sh
git commit -m "Merge changes from upstream"
git push --set-upstream origin sync/<chosen-tag> --tags
```

You can now follow the instructions to open a PR against your upstream repo.
