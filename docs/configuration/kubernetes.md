# Kubernetes

Kubernetes support is enabled by default in the reference configuration. To disable it, just
set:

```yaml
azimuth_kubernetes_enabled: no
```

!!! tip

    The
    [azimuth_capi_operator role](https://github.com/stackhpc/ansible-collection-azimuth-ops/blob/main/roles/azimuth_capi_operator/defaults/main.yml)
    defines a number of variables that can be set to control the behaviour of tenant Kubernetes
    clusters provisioned using Azimuth.
    
    In general, any of the options available for the
    [stackhpc/capi-helm-charts/openstack-cluster Helm chart](https://github.com/stackhpc/capi-helm-charts/tree/main/charts/openstack-cluster)
    can be set using either the `azimuth_capi_operator_capi_helm_values_overrides` variable
    (for global configuration) or the `values` section for a specific Kubernetes template.

    However the default values should be sufficient for most deployments of Azimuth.

## Multiple external networks

In the case where multiple external networks are available to tenants, you must tell Azimuth
which one to use for floating IPs for Kubernetes services in tenant clusters:

```yaml
azimuth_capi_operator_external_network_id: "<network id>"
```

## Cluster templates

TODO

## Harbor registry

`azimuth-ops` is able to manage a [Harbor registry](https://goharbor.io/) as part of an Azimuth
installation, which is primarily used as a
[proxy cache](https://goharbor.io/docs/2.1.0/administration/configure-proxy-cache/)
to avoid pulling images from the internet. The Harbor registry will be made available at
`registry.<ingress base domain>`, e.g. `registry.apps.example.org`.

`azimuth-ops` will auto-wire use of the Harbor registry into tenant Kubernetes clusters for
registries that have a proxy cache defined.

Harbor is enabled by default, and requires two secrets to be set:

```yaml
# The admin password for Harbor
harbor_admin_password: "<secure password>"

# The secret key for Harbor
# This MUST be exactly 16 alphanumeric characters
harbor_secret_key: "<secure secret key>"
```

!!! danger

    These values should be kept secret. If you want to keep them in Git - which is recommended -
    then they [must be encrypted](../secrets.md).

### Disabling Harbor

The Harbor registry can be disabled entirely:

```yaml
harbor_enabled: no
```

### Additional proxy caches

By default, a single proxy cache is defined for [Docker Hub](https://hub.docker.com/) in order
to get around the [rate limit](https://docs.docker.com/docker-hub/download-rate-limit/).

!!! note

    Additional default proxy caches may be added in the future for common public repositories,
    e.g. [quay.io](https://quay.io/).

You can also define additional proxy caches for other registries:

```yaml
harbor_proxy_cache_extra_projects:
  quay.io:
    # The name of the project in Harbor
    name: quay-public

    # The type of the upstream registry, e.g.:
    #   aws-ecr
    #   azure-acr
    #   docker-hub
    #   docker-registry
    #   gitlab
    #   google-gcr
    #   harbor
    #   jfrog-artifactory
    #   quay-io
    type: quay-io

    # The endpoint URL for the registry
    url: https://quay.io
```

!!! warning

    Currently, `azimuth-ops` does not support defining authentication for the upstream registries,
    i.e. only public repositories are supported.
