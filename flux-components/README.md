# Customising Kubernetes Deployments using Flux

## Glossary

**Component**: The broadest view of a piece of functionality in the deployed
cluster, covers the whole stack. So the kube-prometheus-stack component is
the ability to monitor and alert, the component can be disabled, configured
and installed.

**Deployment**: The set of YAML that describes a component and how its applied
to a cluster, the raw manifests any flux options and deployed Kubernetes
objects in the final cluster (`HelmRelease`, `ConfigMaps` etc). A deployment
can be deployed, disabled, deleted, reconciled and configured.

**Manifests**: The YAML files that are bundled as Flux artifacts and moved in
and out of registries. Manifests are static and can be edited or updated.

## Assumptions and Rules

- Each directory under `flux-components` that is referenced in the CI workflow is
  built and pushed as a flux OCI artifact.
- Only the contents of `flux-components/azimuth-flux` are deployed manually, all other
  objects should be referenced from there directly or indirectly (it is the root of
  the tree)
- All YAML files in a Flux artifact will be treated as Kubernetes manifests and the
  controller will attempt to reconcile them to the cluster
- Secrets should be stored in the `secrets` directory/artifact in their `age` key
  encrypted form, `secrets` is the only artifact with a Kustomize controller that has
  the `age` private key and can decrypt secrets.
- There is nothing stopping the same object being defined twice ie in two different
  manifest YAML files/artifacts, this would be a bad thing, don't do it

## Helm Deployments

Each helm chart is defined by a Flux `HelmRelease` (from the `helm.toolkit.fluxcd.io`
API group).
The `HelmRelease` references a chart and version (or version range) and consumes chart
values from a list of `secrets` and `configMaps` defined in the `HelmRelease`.
The sources of values can be marked as optional and precedence is defined by list order:
sources later in the list take precedence over earlier sources.

Optional sources of values are used for user overrides, a user can define a `secret` or
`configMap` with the overrides, give it the name from the `HelmRelease` and it will
automatically be consumed.

### Naming scheme for helm deployments

Say we want to deploy the chart named `kube-prometheus-stack`:

- The `HelmRelease` is named after the chart: `kube-prometheus-stack`
- Any chart values defined by Azimuth are named with the suffix `-values-default`,
  eg `kube-prometheus-stack-values-default` for both `configMap`s and `secret`s
- The dangling hooks for user overrides are named with the suffix `-values`,
  eg `kube-prometheus-stack-values` for both `configMap`s and `secret`s

Literal manifests that need to be deployed separately to a chart but relate to
a chart should be named with a reference to the chart.

## Creating whole Kubernetes objects

As well as configuring Helm charts Flux artifacts can specify whole Kubernetes
objects as raw YAML manifests.
The manifests can be placed into any deployed Flux artifact, if an object
relates to a named component then we recommend placing it in the component's
artifact.
As well as being common sense this ensures the automatically applied metadata is
consistent.
All `.yaml` files under the artifact directory are rolled in to the Flux artifact
so they do not need to belong in a particular directory.

## The top-level Flux deployment

In the `azimuth-flux/` directory the top-level Kubernetes objects are defined.
This should include all `OCIRepository` objects pointing at a Flux manifest, and
the `Kustomization` objects that deploy those objects.
Namespaces should be created by the top level artifact so that `OCIRepository` and
`HelmRelease` objects can be put in them before they are made by helm.
All namespaces should be placed in `namespaces.yaml`.
There should not be any `HelmRelease`s defined in the top-level object.

All deployments of an Azimuth seed will need to refer to a top-level `azimuth-flux`
artifact.
As such it is possible for a user to place sources of Helm chart overrides in the
top-level artifact and avoid deploying any new artifacts (if they only want to
deploy the standard azimuth components with some helm chart overrides).

## Postbuild and static and dynamic cluster info

Flux supports [`postBuild`](https://fluxcd.io/flux/components/kustomize/kustomizations/#post-build-variable-substitution)
templating in Kubernetes objects, this means templating values from a `secret` or
`configMap`.
It behaves a little like Bash variable substitution where `${VAR}` references in
the manifests are substituted for the value of `VAR` in a config map or secret.
In order to use a source of values it must be specified in the `Kustomization` and
be in the same namespace.
A source of `postBuild` values can be marked as `optional: true` if it doesn't need
to exist.

The Ansible bootstrap of an Azimuth seed creates a `configMap` called
`dynamic-azimuth-info` in the `flux-system` namespace, this contains information
that is only available during deployment or is defined in the Ansible (hence
"dynamic").
Examples include:

- the domain of the Azimuth seed URLs
- the name of the SOPS private key secret
- top-level Flux artifact tag to deploy
- the scheme for admin dashboard URLs (http/https)

There is also provision to use an optional `static-azimuth-info` `configMap` in
the `flux-system` namespace.
This is meant to be used to store information that is static across Azimuth
deployments/Ansible runs.
As such it is deployed by the top-level Flux artifact.

Any `Kustomization`s deployed as part of Azimuth that need to refer to the
`cluster-info`s should be deployed into the `flux-system` namespace and use the
`targetNamespace` value to deploy the artifact into the correct place.

## Example Kustomization chain

The top-level Flux artifact is pulled and unpacked by the `FluxInstance` that
is bootstrapped by Ansible.

Example of bootstrapped FluxInstance:

```YAML
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
  annotations:
    fluxcd.controlplane.io/reconcileEvery: "1h"
    fluxcd.controlplane.io/reconcileTimeout: "10m"
spec:
  ... # Some near boilerplate to set which version of Flux we want to use and which controllers
  kustomize:
    patches:
      - target: # The bootstrapper can decrypt secrets
          kind: Kustomization
          name: flux-system
        patch: |
          - op: add
            path: /spec/decryption
            value:
              provider: sops
              secretRef:
                name: "{{ flux_sops_private_key_secret_name }}"
      - target: # The bootstrapper can use postBuild config to template top-level Flux artifact
          kind: Kustomization
          namespace: flux-system
        patch: |
          - op: add
            path: /spec/postBuild
            value:
              substituteFrom:
                - kind: ConfigMap
                  name: dynamic-azimuth-info
                - kind: ConfigMap
                  name: static-azimuth-info
                  optional: true
  sync:
    kind: OCIRepository
    url: "oci://ghcr.io/azimuth-cloud/azimuth-config/stack-hpc/azimuth-flux" # Repository for top level Flux artifact
    ref: "stackHPCRules" # Tag for top level Flux artifact
    path: "."
    interval: "30s"
```

An example of one component in the top level Flux artifact:

```YAML
apiVersion: source.toolkit.fluxcd.io/v1
kind: OCIRepository
metadata:
  name: kube-prometheus-stack # Same name as flux component
  namespace: monitoring-system # The namespace the component is deployed into
spec:
  interval: 5m0s # Check the OCI Repo for changes every 5 minutes
  url: oci://ghcr.io/azimuth-cloud/azimuth-config/stack-hpc/kube-prometheus-stack # The flux artifact to pull
  ref:
    tag: ${FLUX_ARTIFACT_TAG} # This will be templated out by the bootstrapped FluxInstance
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: kube-prometheus-stack # Same name as the flux-component
  namespace: flux-system # Needs access to the config maps postBuild
spec:
  interval: 10m # Reconcile the Kustomization every 10 minutes
  targetNamespace: monitoring-system # Deploy into this namespace
  sourceRef: # Use the artifact defined in the OCI Repo above
    kind: OCIRepository
    name: kube-prometheus-stack # Same name as the flux-component
    namespace: monitoring-system
  path: "." # Deploy everything in the artifact
  prune: true
  timeout: 1m
  postBuild:  # Do postBuild templating from the below sources
    substituteFrom:
      - kind: ConfigMap  # Use the Ansible-deployed config map to template
        name: dynamic-azimuth-info
      - kind: ConfigMap
        name: static-azimuth-info # Use the static flux deplpoyed config map if it exists
        optional: true
```

An example of the component:

```YAML
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: kube-prometheus-stack # Same name as flux component
  namespace: monitoring-system
spec:
  type: "oci" # This is an OCI Helm chart repo
  interval: 15m # Check the repo every 15 minutes
  url: oci://ghcr.io/prometheus-community/charts # Url of the repo
---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: kube-prometheus-stack # Same name as the chart
  namespace: monitoring-system
spec:
  interval: 30s # Reconcile the helm release every 30 seconds
  releaseName: kube-prometheus-stack
  chart:
    spec:
      chart: kube-prometheus-stack # Component name is same as chart but not required
      version: ">=87.0.0"
      sourceRef:
        kind: HelmRepository
        name: kube-prometheus-stack
  install:
    crds: CreateReplace
    strategy:
      name: RetryOnFailure
      retryInterval: 3m
    remediation:
      retries: 3 # Number of retries before giving up
      remediateLastFailure: true # Automatically remediate the last failure (helm uninstall)
  upgrade:
    force: true # Forces resource updates through a replacement strategy that avoids 3-way merge conflicts on client-side apply. Ignored when using server-side apply
    crds: CreateReplace
    strategy:
      name: RetryOnFailure
      retryInterval: 3m
    remediation:
      retries: 3 # Number of retries before giving up
      remediateLastFailure: true # Automatically remediate the last failure
      strategy: rollback # Rollback the upgrade if it runs out of retries
  valuesFrom:  # Where to pull chart values from
    - kind: ConfigMap
      name: kube-prometheus-stack-values-default # The "azimuth default" values
    - kind: ConfigMap
      name: kube-prometheus-stack-values # Optional user override values
      optional: true
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prom-stack-values-default # Name matches the one in the HelmRelease
  namespace: monitoring-system # Must be same namespace as the HelmRelease
data:
  values.yaml: | # Raw YAML values for the Helm chart
    crds:
      enabled: true
    defaultRules:
      disabled:
        # None of these are relevant in k3s context
        KubeSchedulerDown: true
        KubeProxyDown: true
    ... # etc and so on
```

## Creating and pushing Flux artifacts

To push the manifests to an OCI registry as a usable Flux artifact use `tools/push-artifact.sh`

```bash
push-artifact.sh [-h] [-d] [-c <registry_credentials>] <path_to_artifact_directory> <artifact_url> [<artifact_tag>]
```

`-d` will perform a dry run and print out the push command but not execute.

All files and directories under the given artifact directory will be packaged
into a tar and pushed to the given URL (if the URL doesn't start with `oci://`
it is automatically added).
If no artifact tag is supplied then `latest` is used.

## Notes about pushing to your own GHCR

To push to the GCHR under your user profile you can generate a GitHub token
and pass a creds option like `<username>:<token>` eg:

```bash
./tools/push-artifact.sh -c irt-shpc:${TOKEN} azimuth-flux oci://ghcr.io/irt-shpc/flux-test my-tag
```
