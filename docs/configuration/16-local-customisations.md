# Local customisations

Azimuth allows a few site-specific customisations to be made, if required.

## User and Operator Documentation

The Azimuth UI includes a documentation link in the navigation bar at the top of the page.
By default, this link points to the
[generic Azimuth user documentation](https://azimuth-cloud.github.io/azimuth-user-docs/) that
covers usage of the reference appliances.

However it is recommended to change this link to point at local documentation that is specific
to your site, where possible. This documentation can include additional information, e.g.
how to get an account to use with Azimuth, which is out-of-scope for the generic documentation.

To change the documentation link, use the following variable:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_documentation_url: https://docs.example.org/azimuth
```

As part of the standard Azimuth deployment procedure, a copy of the generic user and operator
documentation sites are published on separate subdomains of the Azimuth ingress URL. For an Azimuth
hosted at `portal.azimuth.example.com`, the documentation can be accessed at `user.docs.azimuth.example.com`
and `admin.docs.azimuth.example.com` respectively. The operator documentation is protected by the same
username and password as the [admin dashboards](../debugging/access-monitoring.md).

### Site-specific documentation

The default configuration for the user and operator documentation will build a local copy of the
[upstream documentation](https://github.com/azimuth-cloud/azimuth-config/tree/stable/docs); however,
the following configuration can be used to instead build the documentation from a downstream azimuth-config
repository:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
mkdocs_operator_docs_repo: https://<your-github-or-gitlab-repo>
mkdocs_operator_docs_branch: <optional-non-default-branch>
mkdocs_user_docs_repo: https://<your-github-or-gitlab-repo>
mkdocs_user_docs_branch: <optional-non-default-branch>
```


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
