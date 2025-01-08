# Local customisations

Azimuth allows a few site-specific customisations to be made, if required.

## User and Operator Documentation

As part of the standard Azimuth deployment procedure, a copy of the generic user and operator
documentation sites are published on separate subdomains of the Azimuth ingress URL. For an Azimuth
instance hosted at `portal.azimuth.example.com`, the documentation can be accessed at
`user.docs.azimuth.example.com` and `admin.docs.azimuth.example.com` respectively. The operator
documentation is protected by the same username and password as the
[admin dashboards](../configuration/14-monitoring.md#accessing-web-interfaces).

### Site-specific documentation

The default configuration for the user and operator documentation will build a local copy
of the [upstream documentation](https://github.com/azimuth-cloud/azimuth-config/tree/stable/docs);
however, the following configuration can be used to instead build the documentation from a
downstream azimuth-config repository:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
mkdocs_operator_docs_repo: https://<your-github-or-gitlab-repo>
mkdocs_operator_docs_branch: <optional-non-default-branch>
mkdocs_user_docs_repo: https://<your-github-or-gitlab-repo>
mkdocs_user_docs_branch: <optional-non-default-branch>
```

This allows Azimuth operators to build up their own set of internal documentation pages specific to
their Azimuth deployment. A set of
[example files](https://github.com/azimuth-cloud/azimuth-config/tree/stable/docs/site-example/)
are provided as part of the upstream repository as a starting point for structuring your site-specific
operator documentation. You will also need to uncomment (or add your own items to) the relevant `nav`
entries in your local [mkdocs.yml](https://github.com/azimuth-cloud/azimuth-config/tree/stable/mkdocs.yml)
file. For more information on how to customise your local documentation see the official
[MkDocs website](https://www.mkdocs.org).

!!! tip

    In order to minimise the potential for merge conflicts when synchronising the latest upstream changes
    into a downstream azimuth-config repository, it is recommended that any site specific docs are placed
    in a separate set of files / folders under the `docs` directory. An example structure is provided
    [here](https://github.com/azimuth-cloud/azimuth-config/tree/stable/docs/site-example/).

If the downstream configuration is hosted in a private repository, then SSH-based authentication
must be used to allow the documentation build process *read-only* access to the repository. To set
up this authentication, an SSH keypair must first be created using (a command similar to):

```sh
ssh-keygen -t ed25519 -f azimuth-docs-key -N "" -C "-- Azimuth config repository deploy key"
```

The generated private key should then be stored as an encrypted secret inside the environment's
`secrets.yml` file:

```yaml  title="environments/my-site/inventory/group_vars/all/secrets.yml"
mkdocs_deploy_ssh_private_key: |
  <private-key>
```

and the public key must be added to the config repository as a 'deploy key' (see relevant
[GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys#deploy-keys)
or [GitLab](https://docs.gitlab.com/ee/user/project/deploy_keys/) docs for more details).

Finally, the target repository URL(s) should be updated to use an SSH-based git remote address e.g. `git@github.com:my-org/azimuth-config` instead of `https://github.com/my-org/azimuth-config`.

!!! tip

    The documentation publishing feature works by checking out a local copy of the repository inside a Kubernetes
    init container and then running `mkdocs`. To debug authentication or build issues, start by checking the logs
    of the relevant `operator_docs` or `user_docs` init container on the Azimuth management cluster.

<!-- TODO: Think about how to refresh docs when docs change but mkdocs Helm release values don't. -->
<!-- When working with site-specific documentation for deployments managed via GitLab [CI/CD](../deployment/automation.md) it is also advisable to edit the `.gitlab-ci.yml` workflow file to include the `docs/` directory in the list of watched files for the production deployment job (i.e. the `changes` list in the `deploy_production` section). This ensures that any changes made to site-specific documentation will be automatically incorporated into the published documentation pages. -->

## User Interface Theming

The Azimuth UI is built using the [Bootstrap frontend toolkit](https://getbootstrap.com/),
which provides a grid system and several built-in components.

Bootstrap is built to be customisable - please consult the
[Bootstrap documentation](https://getbootstrap.com/docs/5.3/customize/overview/) for more
information on how to do this. Several websites also provide free and paid themes for
Bootstrap - by default, Azimuth uses the [Pulse theme](https://bootswatch.com/pulse/) from
the [Bootswatch project](https://bootswatch.com/).

### Replacing the Bootstrap theme

It is possible to replace the Bootstrap theme completely by pointing to a different
compiled CSS file. For example, the following configuration tells Azimuth to use the
[Zephyr theme from Bootswatch](https://bootswatch.com/zephyr/):

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_theme_bootstrap_css_url: https://bootswatch.com/5/zephyr/bootstrap.css
```
!!! tip

    In order for the theming changes to take effect you may need to do a hard refresh of
    the page due to the aggressive nature of CSS caching.

    Mac: <kbd>⇧ Shift</kbd> + <kbd>⌘ Command</kbd> + <kbd>R</kbd>
    Windows: <kbd> ctrl</kbd> + <kbd>⇧ Shift</kbd> + <kbd>R</kbd> / <kbd> ctrl</kbd> + <kbd> F5</kbd>

### Injecting custom CSS

In addition to replacing the entire theme, Azimuth also allows custom CSS to be injected.
This can be useful for applying small tweaks, or making modifications to the Azimuth UI
that are not part of your chosen theme.

In particular, custom CSS can be used to add a logo to the navigation bar. For example,
the following snippet adds the Azimuth logo to the navigation bar instead of the cloud
label:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_theme_custom_css: |
  .navbar-brand {
    background-size: auto 100%;
    background-repeat: no-repeat;
    text-indent: -9999px;

    background-image: url('https://raw.githubusercontent.com/azimuth-cloud/azimuth/master/branding/azimuth-logo-white-text.png');
    height: 60px;
    width: 220px;
  }
```

!!! tip

    The image must already be available somewhere on the internet - Azimuth does not
    currently have support for hosting the logo itself.

    The `height` and `width` should be adjusted to match the aspect ratio of your logo
    and the desired size in the Azimuth UI.

!!! warning

    If you are using the default Pulse theme, make sure to include the following at the
    top of your custom CSS:

    ```css
    @import url(/pulse-overrides.css);
    ```

    This is because Azimuth has some Pulse-specific tweaks that you will need to keep.
    For more details, see the
    [CSS file](https://github.com/azimuth-cloud/azimuth/blob/master/ui/assets/pulse-overrides.css),
    which has comments indicating why these are necessary.
