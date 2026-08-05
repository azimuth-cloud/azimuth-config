# Scheduling

Azimuth allows scheduling of the ddeletion of CaaS and Kubernetes clusters. The creating user picks the lifetime of their platform at creation time, and Azimuth will delete the platform when it expires.

By default, no scheduling features are enabled. Azimuth configuration allows:

- Allowing scheduling, but giving users' free choice as to the lifetime of their platforms.
- Allowing scheduling, and enforcing a maximum lifetime across all platforms.
- Allowing scheduling, and enforcing a maximum lifetime on a per-platform basis using annotations.

## Enabling scheduling globally

To enable scheduling globally, add azimuth_scheduling_enabled to the appropriate configuration file.
This will enable users creating new platforms to pick a deletion time when the platforms are created.
Existing platforms will be unnafected.

```yaml title="environments/my-site/inventory/group_vars/all/secrets.yml"
azimuth_scheduling_enabled: true
```

## Annotations

Scheduling is implemented using annotations that are applied to instances of the
`clustertemplates.azimuth.stackhpc.com` and
`clustertypes.caas.azimuth.stackhpc.com` resources for Kubernetes cluster templates,
and CaaS cluster types respectively.
It is not possible to set maximum lifetimes for individual apps inside a kubernetes cluster,
only the cluster itself.

The annotations is the same for all platform types:

- `scheduling.azimuth.stackhpc.com/max-lifetime-hours`
  A an integer number of hours which will be the maximum lifetime for the platform.

<!-- prettier-ignore-start -->
!!! warning "No annotations means infinite lifetime"
    If no scheduling are present, then that platform has no maximum lifetime.
<!-- prettier-ignore-end -->

## Built-in platform types

`azimuth-ops` supports a number of variables that can be used to apply scheduling
to the built-in platform types.

The following variables allow default lifetimes to be set **for all built-in
platform types**:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_max_platform_lifetime_hours: 20
```

These can be overridden for specific platform types if required:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
# The following apply to all Kubernetes cluster templates
azimuth_capi_operator_max_lifetime_hours: 24

# Each CaaS cluster type has specific variables, e.g.:
azimuth_caas_stackhpc_workstation_max_lifetime_hours: 200
```
