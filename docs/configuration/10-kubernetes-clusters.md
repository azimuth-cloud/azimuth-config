# Kubernetes clusters

Kubernetes support in Azimuth is implemented using [Cluster API](https://cluster-api.sigs.k8s.io/)
with the [OpenStack provider](https://github.com/kubernetes-sigs/cluster-api-provider-openstack).
Support for cluster addons is provided by the
[Cluster API addon provider](https://github.com/stackhpc/cluster-api-addon-provider), which
provides functionality for installing [Helm](https://helm.sh/) charts and additional manifests.

Azimuth provides an opinionated interface on top of Cluster API by implementing
[its own Kubernetes operator](https://github.com/stackhpc/azimuth-capi-operator).
This operator exposes two
[custom resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
which are used by the Azimuth API to manage Kubernetes clusters:

`clustertemplates.azimuth.stackhpc.com`
: A cluster template represents a "type" of Kubernetes cluster. In particular, this is used
  to provide different Kubernetes versions, but can also be used to provide advanced
  options, e.g. networking configuration or additional addons that are installed by default on
  the cluster. Cluster templates can be deprecated, e.g. when a new Kubernetes version is released,
  resulting in a warning being shown to the user that they should upgrade.

`clusters.azimuth.stackhpc.com`
: A cluster represents the user-facing definition of a Kubernetes cluster. It references a
  template, from which the Kubernetes version and other advanced options are taken, but allows
  the user to specify one or more node groups and toggle a few simple options such as
  auto-healing and whether the monitoring stack is deployed on the cluster.

For each `Cluster`, the operator manages a release of the
[openstack-cluster Helm chart](https://github.com/stackhpc/capi-helm-charts/tree/main/charts/openstack-cluster).
The Helm release in turn manages Cluster API resources for the cluster, including addons.

To get the values for the release, the operator first derives some values from the `Cluster`
object which are merged with the values defined in the referenced template. The result of
that merge is then merged with any global configuration that has been specified before being
passed to Helm.

## Disabling Kubernetes

Kubernetes support is enabled by default in the reference configuration. To disable it, just
set:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_kubernetes_enabled: no
```

### Tenancy-based Access Controls

Alternatively, Kubernetes support can be restricted on a per-tenancy basis using the following variables:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# List of allowed tenancy IDs
azimuth_capi_operator_cluster_templates_tenancy_allow_list:
# List of denied tenancy IDs
azimuth_capi_operator_cluster_templates_tenancy_deny_list:
# Regex pattern to allow tenancies by name
azimuth_capi_operator_cluster_templates_tenancy_allow_regex:
# Regex pattern to block tenancies by name
azimuth_capi_operator_cluster_templates_tenancy_deny_regex:
```

In the event that a given tenancy matches more than one of the above restrictions,
the following priorities are applied:
 - IDs are prioritized over Regex pattern matches (e.g. if a tenancy ID is 
present in the 'deny' list *and* the tenancies name matches an 'allow' pattern then access is *denied*)
- Deny is prioritized over allow (e.g. if a tenancy ID is present in both 'allow' and 'deny' lists then
access is *denied*)
- The presence of either (or both) of the 'allow' restrictions are defined then a deny-by-default policy is enacted so that
any tenancies not matching the one of the 'allow' specifications are denied

!!! info

    Restricting access to Kubernetes cluster templates automatically applies the same
    access restrictions to all [Kubernetes Apps](./11-kubernetes-apps.md).

Any restrictions which are applied to tenancies where clusters are already deployed will not delete existing clusters.
Instead, new cluster creation will be disabled and the 'update' and 'upgrade' functionality on existing clusters will also
be disabled so that only the 'delete' operation remains available.

## Kubernetes configuration

Kubernetes configuration is very similar for both the
[Azimuth HA cluster](./02-deployment-method.md#highly-available-ha) and tenant Kubernetes
clusters, since both are deployed using Cluster API. The
[Kubernetes configuration](./03-kubernetes-config.md) section discusses the possible options
for networking, volumes and availability zones in detail.

## Cluster templates

`azimuth-ops` is able to manage the available Kubernetes cluster templates using the
variable `azimuth_capi_operator_cluster_templates`. This variable is a dictionary that
maps cluster template names to their specifications, and represents the **current** (i.e.
not deprecated) cluster templates. `azimuth-ops` will *not* remove cluster templates,
but it will mark any templates that are not present in this variable as deprecated.

By default, `azimuth-ops` will ensure a cluster template is present for the latest
patch version of each Kubernetes release that is currently maintained. These templates
are configured so that Kubernetes nodes will go onto the Azimuth `portal-internal`
network for the project in which the cluster is being deployed.

### Disabling the default templates

To disable the default templates, just set the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_capi_operator_cluster_templates_default: {}
```

### Custom cluster templates

If you want to include custom cluster templates in addition to the default templates,
e.g. for advanced networking configurations, you can specify them using the variable
`azimuth_capi_operator_cluster_templates_extra`.

For example, the following demonstrates how to configure a template where the cluster
worker nodes have two networks attached - the control plane nodes and workers are all
attached to the Azimuth internal network but the workers are attached to an additional
SR-IOV capable network:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_capi_operator_cluster_templates_extra:
  # The index in the dict is the template name
  kube-1-24-2-multinet:
    # A human-readable label for the template
    label: v1.24.2 / multinet
    # A brief description of the template
    description: >-
      Kubernetes 1.24.2 with HA control plane and high-performance networking.
    # Values for the openstack-cluster Helm chart
    values:
      # Specify the image and version for the cluster
      # These are the only required values
      kubernetesVersion: 1.24.2
      machineImageId: "{{ community_images_image_ids.kube_1_24 }}"
      # Use the portal-internal network as the main cluster network
      clusterNetworking:
        internalNetwork:
          networkFilter:
            tags: portal-internal
      # Configure an extra SR-IOV port on worker nodes using an SR-IOV capable network
      nodeGroupDefaults:
        machineNetworking:
          ports:
            - {}
            - network:
                tags: sriov-vlan
              securityGroups: []
              vnicType: direct
```

## Harbor registry

`azimuth-ops` is able to manage a [Harbor registry](https://goharbor.io/) as part of an Azimuth
installation. This registry is primarily used as a
[proxy cache](https://goharbor.io/docs/2.1.0/administration/configure-proxy-cache/)
to limit the number of times that images that are pulled directly from the internet.

If enabled, the Harbor registry will be made available at `registry.<ingress base domain>`,
e.g. `registry.azimuth.example.org` and will be configured for tenant clusters by default.

By default, a single proxy cache is defined for [Docker Hub](https://hub.docker.com/) in order
to mitigate [rate limiting](https://docs.docker.com/docker-hub/download-rate-limit/).

!!! tip

    If you have a Docker Hub mirror available, you can
    [configure Kubernetes clusters to use it](./03-kubernetes-config.md#docker-hub-mirror)
    instead of deploying Harbor.

    In this case, you should [disable Harbor](#disabling-harbor) by setting:

    ```yaml
    harbor_enabled: no
    ```

Harbor is enabled by default, and requires two secrets to be set:

```yaml  title="environments/my-site/inventory/group_vars/all/secrets.yml"
# The admin password for Harbor
harbor_admin_password: "<secure password>"

# The secret key for Harbor
# This MUST be exactly 16 alphanumeric characters
harbor_secret_key: "<secure secret key>"
```

!!! danger

    These values should be kept secret. If you want to keep them in Git - which is recommended -
    then they [must be encrypted](../repository/secrets.md).

### Disabling Harbor

The Harbor registry can be disabled entirely:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
harbor_enabled: no

### Additional proxy caches

By default, only Docker Hub has a proxy cache. Additional proxy caches can be configured
for other registries, if desired:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
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

    Defining authentication for the upstream registries is not currently supported,
    i.e. only public repositories can be proxied.
