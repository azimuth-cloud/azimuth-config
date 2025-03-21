# Access control

Azimuth allows access to platform types to be restricted on a per-platform type and
per-tenant basis, allowing different platform types to be made available to different
tenants as required.

  * [Kubernetes cluster templates](./10-kubernetes-clusters.md#cluster-templates)
  * [Kubernetes app templates](./11-kubernetes-apps.md)
  * [CaaS cluster types](./12-caas.md)

By default, all of the platform types are available to all tenants.

!!! warning

    Any restrictions that are applied after platforms have already been created do
    **not** result in existing platforms being deleted.
    
    However the creation of new platforms will be restricted to the available platform
    types, and platforms deployed using platform types that are subsequently restricted
    will be limited to the `delete` action only.

## Annotations

Access control is implemented using annotations that are applied to instances of the
`clustertemplates.azimuth.stackhpc.com`, `apptemplates.azimuth.stackhpc.com` and
`clustertypes.caas.azimuth.stackhpc.com` resources for Kubernetes cluster templates,
Kubernetes apps and CaaS cluster types respectively.

The annotations are the same for all platform types, and the following annotations are
respected, in order of precedence:

  * `acl.azimuth.stackhpc.com/deny-list`  
    A comma-separated list of tenancy *IDs* that are not allowed to use the platform type.
  * `acl.azimuth.stackhpc.com/allow-list`  
    A comma-separated list of tenancy *IDs* that are allowed to use the platform type.
  * `acl.azimuth.stackhpc.com/deny-regex`  
    A regex where matching tenancy *names* are not allowed to use the platform type.
  * `acl.azimuth.stackhpc.com/allow-regex`  
    A regex where matching tenancy *names* are allowed to use the platform type.

In particular, the precedence order means that, for example:

  * A tenancy whose name matches the `allow-regex` but whose ID is in the `deny-list`
    is not able to use the platform type.
  * Similarly, a tenancy whose name matches the `deny-regex` but whose ID is in the
    `allow-list` is allowed to use the platform type.
  * A tenancy whose ID is in both the `allow-list` and `deny-list` is not allowed to
    use the platform type.

!!! warning  "No annotations means allow"

    If no access control annotations are present, then that platform type is available
    to all tenants.
    
!!! info  "Deny-by-default when allow annotations are present"

    The presence of at least one `allow` annotation triggers a deny-by-default policy,
    where tenants not matching an `allow` annotation are denied.

## Built-in platform types

`azimuth-ops` supports a number of variables that can be used to apply access controls
to the built-in platform types.

The following variables allow default access controls to be set **for all built-in
platform types**:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# List of denied tenancy IDs
platforms_tenancy_deny_list:
  - "<id1>"
  - "<id2>"
# List of allowed tenancy IDs
platforms_tenancy_allow_list:
  - "<id3>"
  - "<id4>"
# Regex pattern to deny tenancies by name
platforms_tenancy_deny_regex: "dev$"  # Deny any tenancy whose name ends with 'dev'
# Regex pattern to allow tenancies by name
platforms_tenancy_allow_regex: ".*"  # Allow all tenancies by default
```

These can be overridden for specific platform types if required:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# The following apply to all Kubernetes cluster templates
azimuth_capi_operator_cluster_template_tenancy_deny_list:
azimuth_capi_operator_cluster_template_tenancy_allow_list:
azimuth_capi_operator_cluster_template_tenancy_deny_regex:
azimuth_capi_operator_cluster_template_tenancy_allow_regex:

# Each Kubernetes app has specific variables, e.g.:
azimuth_capi_operator_app_templates_jupyterhub_tenancy_deny_list:
azimuth_capi_operator_app_templates_jupyterhub_tenancy_allow_list:
azimuth_capi_operator_app_templates_jupyterhub_tenancy_deny_regex:
azimuth_capi_operator_app_templates_jupyterhub_tenancy_allow_regex:

# Each CaaS cluster type has specific variables, e.g.:
azimuth_caas_workstation_tenancy_deny_list:
azimuth_caas_workstation_tenancy_allow_list:
azimuth_caas_workstation_tenancy_deny_regex:
azimuth_caas_workstation_tenancy_allow_regex:
```
