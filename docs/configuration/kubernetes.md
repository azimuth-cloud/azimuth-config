# Kubernetes

Kubernetes support in Azimuth is implemented using [Cluster API](https://cluster-api.sigs.k8s.io/)
with the [OpenStack provider](https://github.com/kubernetes-sigs/cluster-api-provider-openstack).

Azimuth provides an opinionated interface on top of Cluster API by implementing
[its own Kubernetes operator](https://github.com/stackhpc/azimuth-capi-operator).
This operator exposes two new
[custom resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
which are used by the Azimuth API to manage Kubernetes clusters:

`clustertemplates.azimuth.stackhpc.com`
: A cluster template represents a "type" of Kubernetes cluster. In particular, this is used
  to provide different Kubernetes versions, but can also be used to provide advanced configuration
  options, e.g. networking configuration or additional addons, that are not exposed to the
  end user. Cluster templates can be deprecated, e.g. when a new Kubernetes version is released,
  resulting in a warning being shown to the user that they should upgrade.

`clusters.azimuth.stackhpc.com`
: A cluster represents the user-facing definition of a Kubernetes cluster. It references a
  template, from which the Kubernetes version and other advanced options are taken, but allows
  the user to specify one or more node groups and toggle a few simple options such as
  auto-healing and whether the monitoring stack is deployed on the cluster.

For each `Cluster`, the operator manages a release of the
[stackhpc/capi-helm-charts/openstack-cluster Helm chart](https://github.com/stackhpc/capi-helm-charts/tree/main/charts/openstack-cluster).
The Helm release in turn manages Cluster API resources for the cluster along with
a number of [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
that manage the addons for the cluster.

To get the values for the release, the operator first derives some values from the `Cluster`
object which are merged with the values defined in the referenced template. The result of
that merge is then merged with any global configuration that has been specified before being
passed to Helm.

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

## Disabling Kubernetes

Kubernetes support is enabled by default in the reference configuration. To disable it, just
set:

```yaml
azimuth_kubernetes_enabled: no
```

## Multiple external networks

In the case where multiple external networks are available to tenants, you must tell Azimuth
which one to use for floating IPs for Kubernetes services in tenant clusters:

```yaml
azimuth_capi_operator_external_network_id: "<network id>"
```

## Images

When building a cluster, Cluster API requires that an image exists in the target cloud,
accessible to the target project, that has the correct version of
[kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/) and
[kubeadm](https://kubernetes.io/docs/reference/setup-tools/kubeadm/) available.

`azimuth-ops` is able to upload suitable images using the
[Community images functionality](./community-images.md). If you would prefer to manage the
images using another mechanism, suitable images can be built using the
[Kubernetes image-builder](https://github.com/kubernetes-sigs/image-builder/tree/master/images/capi).

The ID of the image for a particular Kubernetes version must be given in the cluster
template.

## Availability zones

By default, an Azimuth installation assumes that there is a single
[availability zone (AZ)](https://docs.openstack.org/nova/latest/admin/availability-zones.html)
called `nova` - this is the default set up and common for small-to-medium sized clouds.

If this is not the case for your target cloud, you can set some variables to determine
the availability zones that are used for Kubernetes nodes. The possible options are discussed in
[Availability Zones for Kubernetes nodes](./deployment-method.md#availability-zones-for-kubernetes-nodes).

The relevant variables are:

```yaml
# Indicates whether to omit the failure domain (AZ) from control plane nodes
azimuth_capi_operator_capi_helm_control_plane_omit_failure_domain: true

# The AZs to consider for control plane nodes
#   Only used if the flag above is false
azimuth_capi_operator_capi_helm_control_plane_failure_domains: [az1, az2]

# The AZ to use for workers
azimuth_capi_operator_capi_helm_worker_failure_domain: az1
# Set to null to omit the AZ from worker nodes
azimuth_capi_operator_capi_helm_worker_failure_domain: null
```

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

```yaml
azimuth_capi_operator_cluster_templates_default: {}
```

### Custom cluster templates

If you want to include custom cluster templates in addition to the default templates,
e.g. for advanced networking configurations, you can specify them using the following:

```yaml
azimuth_capi_operator_cluster_templates_extra:
  kube-1-24-2-sriov:
    label: v1.24.2 / SR-IOV
    description: >-
      Kubernetes 1.24.2 with HA control plane and high-performance networking.
    values:
      # Specify the image and version for the cluster
      global:
        kubernetesVersion: 1.24.2
      machineImageId: "{{ community_images_image_ids.kube_1_24_2 }}"
      # Use the network tagged for SR-IOV
      clusterNetworking:
        internalNetwork:
          networkFilter:
            tags: sriov-vlan
      # Use direct ports for the control plane and workers
      controlPlane:
        machineNetworking:
          ports:
            - vnicType: direct
      nodeGroupDefaults:
        machineNetworking:
          ports:
            - vnicType: direct
      # Because SR-IOV ports don't have any port security, we can tell
      # Calico that it only needs to apply the VXLAN at the cluster boundary
      # to avoid double-encapsulation
      addons:
        cni:
          calico:
            installation:
              calicoNetwork:
                ipPools:
                  - cidr: __KUBEADM_POD_CIDR__
                    encapsulation: VXLANCrossSubnet
```

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
    then they [must be encrypted](../repository/secrets.md).

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
