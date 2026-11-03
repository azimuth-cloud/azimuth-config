# Scheduling

Azimuth allows scheduling of the deletion of CaaS and Kubernetes clusters. The creating user picks the lifetime of their platform at creation time, and Azimuth will delete the platform when it expires.

Apps managed by the apps operator, including those in standalone mode, do not support automatic expiry through Azimuth scheduling.

By default, no scheduling features are enabled. Azimuth configuration allows:

- Allowing scheduling, but giving users free choice as to the lifetime of their platforms.
- Allowing scheduling, and enforcing a maximum lifetime across all platforms.
- Allowing scheduling, and enforcing a maximum lifetime on a per-platform basis using annotations.

## Enabling scheduling globally

Set `azimuth_scheduling_enabled: true` in your environment's configuration and apply the updated deployment configuration.
Once applied, users can choose an expiry time when creating new CaaS or Kubernetes clusters.
If no maximum lifetime is configured, users can also create a platform without an expiry time.

Enabling scheduling does not add or change expiry times on existing platforms.

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_scheduling_enabled: true
```

## Annotations

Scheduling is implemented using annotations that are applied to instances of the
`clustertemplates.azimuth.stackhpc.com` and
`clustertypes.caas.azimuth.stackhpc.com` resources for Kubernetes cluster templates,
and CaaS cluster types respectively.
It is not possible to set maximum lifetimes for individual apps inside a Kubernetes cluster,
only the cluster itself.

The annotation is the same for all platform types:

- `scheduling.azimuth.stackhpc.com/max-lifetime-hours`
  An integer number of hours which will be the maximum lifetime for the platform.

<!-- prettier-ignore-start -->
!!! warning "No maximum lifetime"
    Without this annotation, there is no maximum lifetime. Any expiry time chosen by the user still applies.
<!-- prettier-ignore-end -->

## Built-in platform types

`azimuth-ops` supports a number of variables that can be used to apply scheduling
to the built-in platform types.

The following variable sets the maximum lifetime **for all built-in platform types**:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_max_platform_lifetime_hours: 20
```

These can be overridden for specific platform types if required:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
# The following applies to all Kubernetes cluster templates
azimuth_capi_operator_cluster_max_lifetime_hours: 24

# Each CaaS cluster type has specific variables, e.g.:
azimuth_caas_stackhpc_workstation_max_lifetime_hours: 200
```
