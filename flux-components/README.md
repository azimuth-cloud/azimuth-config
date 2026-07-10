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

- There is one HelmRelease per deployment directory contained in the `manifest.yaml`
- Any other YAML files in the deployment directory will be treated as Kubernetes
  manifest and the controller will attempt to reconcile them to the cluster
- Secrets should be stored in an `encrypted` directory in their `age` key encrypted form
- There is nothing stopping the same object being defined twice ie in two different
  manifest YAML files, this would be a bad thing, don't do it

## Deployments

Various helm chart deployments are made into the Azimuth management cluster
using Flux:

- `kube-prometheus-stack` - the monitoring stack, includes Prometheus, Grafana
  and AlertManager

The canonical names (in `monospace`) are important and used as keys to customise
each deployment.
Configuration extends as far as supplying arbitrary chart values to each
deployment and allowing different environments to specify overriding or extra
chart values.

### The base deployment

In the `base/` directory there is a directory per deployment containing the flat
default manifests.
When defining a configuration for an environment the base is copied over verbatim
and any changes applied to it.

### Environments

Any objects added to the final Flux artifact from the environment have a label
applied to them `azimuth/override-source:` that describes the environment and
deployment (or directory) they are sourced from.

#### Overriding or adding Helm chart values

In each environment there is an `overrides.yaml` file describing helm chart
overrides for the deployments.
It is a list of overrides where each follows the following form:

```YAML
- deployment_canonical_name: # (string)
    configMapName:  # name of the map to create in Kube (string)
    forceReload: # whether the helm release should be immediately reconciled when this changes (optional bool, default False)
    disabled: # whether the deployment should be disabled (optional bool, default False)
    values: # dict of chart values to apply to the release
```

eg.

```YAML
- kube-prometheus-stack:
    configMapName: prom-stack-values
    values:
      fullnameOverride: foo
```

The canonical name must match the directory name in the `base/` configuration.

The `configMapName` is used to name the created config map and to update the
`HelmRelease` list of `valuesFrom`, the name must be unique in the same
namespace as the `HelmRelease` to prevent clobbering.

If set the `forceReload` flag means that if a config map changes then flux will
immediately reconcile any `HelmRelease` objects using it.
Otherwise the reconciliation will occur on the `interval` defined in the release
itself.

If users want to specify multiple overrides per deployment they can and the
precedence is that the last specified values wins:

```YAML
- kube-prometheus-stack:
    configMapName: prom-stack-values
    values:
      fullnameOverride: foo
- kube-prometheus-stack:
    configMapName: prom-stack-values-two
    values:
      fullnameOverride: bar
```

In the above case both config maps will be created and the release object will
contain:

```YAML
...
  valuesFrom:
    - kind: ConfigMap
      name: prom-stack-values-default
    - kind: ConfigMap
      name: prom-stack-values
    - kind: ConfigMap
      name: prom-stack-values-two
...
```

The final value of `fullnameOverride: bar` will win.

#### Creating whole Kubernetes objects

As well as configuring Helm charts an environment can specify whole Kubernetes
objects as raw YAML manifests.
The manifests should be placed under `<environment>/manifests/`, if an object
relates to a named deployment in the base we recommend placing it in a
directory of the same name (ie `environment/nanifests/<deployment>`).
This is so the automatically applied metadata is consistent.
All raw `.yaml` manifests are rolled in to the Flux artifact so they do not need
to belong to a parent named deployment and users can create their own directory
structure.
If a manifest is not under a named deployment the label will contain the name of
the top-level directory below `<environment>/manifests/`.

NB: Raw manifests have no validation applied, the namespace must be correctly
set etc.

### Using kustomize for dynamic values

Flux has a feature called [PostBuild](https://fluxcd.io/flux/components/kustomize/kustomizations/#post-build-variable-substitution)
that can be used to inject dynamic config into Flux controlled objects.
It behaves a little like Bash variable substitution where `${VAR}` references in
the manifests are substituted for the value of `VAR` in a config map called
`cluster-info` located in the `flux-system` namespace.

This method can be used to insert the cluster domain at runtime as the domain
is generated dynamically during deployment.
There is a task in the Ansible playbook that bootstraps the Flux operator that
creates the config map.

It is possible to use more config maps as source and restrict them to certain
manifests.
Currently the Flux deployment system is set up to use on cluster-wide
kustomization object.
If users want to put other kustomization objects in their manifests they can but
there can be issues where if an object is watching any encrypted secret it needs
access to the SOPS key so be careful with the manifest path it controls.

### Creating and pushing Flux artifacts

To create the final manifests with the override objects and updated
`HelmReleases` use the Python script in `tools/`.
The script requires the name of an en environment (base is allowed and should
reproduce the default config).
The script copies the base config to a working directory, creates any extra
config maps required for overrides, updates `HelmRelease` objects to use the
overrides and copies any encrypted secrets from the named environment.
It can optionally take arguments to set the base and working directories.
The working and base paths should be defined relative to the Git repository root.

```bash
python tools/main.py <environment_name> [--working=<path_to_output_manifests>] [--base=<path_to_base_config>]
```

To push the manifests to an OCI registry as a usable Flux artifact use `tools/push-artifact.sh`

```bash
push-artifact.sh [-h] [-d] [-c <registry_credentials>] <path_to_artifact_directory> <artifact_url> [<artifact_tag>]
```

`-d` will perform a dry run and print out the push command but not execute.

All files and directories under the given artifact directory will be packaged
into a tar and pushed to the given URL (if the URL doesn't start with `oci://`
it is automatically added).
If no artifact tag is supplied then `latest` is used.

#### Notes about pushing to your own GHCR

To push to the GCHR under your user profile you can generate a GitHub token
and pass a creds option like `<username>:<token>` eg:

```bash
push-artifact.sh -c irt-shpc:${TOKEN} working/artifact oci://ghcr.io/irt-shpc/flux-test my-tag
```
