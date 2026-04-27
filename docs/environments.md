# Environments

An Azimuth deployment is structured around **environments** — each environment pairs an
OpenTofu configuration (infrastructure provisioning) with a Flux cluster path (GitOps
application delivery).

## Environment taxonomy

| Environment  | Seed VM topology | Workload cluster       | Zenith + Azimuth portal |
|--------------|-----------------|------------------------|-------------------------|
| `all-in-one` | Talos, 1 node   | none (seed = workload) | On the seed VM          |
| `single-node`| Talos, 1 node (management) | CAPO → 1 node | On the workload cluster |
| `multi-node` | Talos, 1 node (management) | CAPO → 3 nodes | On the workload cluster |

The seed VM always runs **CAPI + CAPO** and serves as the management cluster.
`all-in-one` is the simplest topology: there is no separate workload cluster, and
Zenith and the Azimuth portal run directly on the seed VM.

## Structure

```
tofu/
├── modules/
│   ├── openstack-infra/    ← OpenStack network, security groups, VM, volumes
│   ├── talos-node/         ← Talos machine config + cluster bootstrap
│   └── flux-bootstrap/     ← flux install + GitRepository + Kustomization
└── environments/
    ├── all-in-one/         ← flux_path = flux/clusters/all-in-one
    └── single-node/        ← flux_path = flux/clusters/single-node

flux/
├── clusters/
│   ├── all-in-one/         ← Kustomization → flux/apps/ (full stack)
│   └── single-node/        ← Kustomization → flux/apps/ (full stack)
└── apps/                   ← shared HelmRelease manifests (environment-agnostic)
    ├── _sources/
    ├── cert-manager/
    ├── ingress-nginx/
    ├── sealed-secrets/
    ├── cluster-api/
    ├── capi-providers/
    ├── azimuth-capi-operator/
    ├── zenith/
    ├── azimuth/
    └── kube-prometheus-stack/
```

All environments share the same `flux/apps/` manifests. Environment-specific values
(base domain, token signing key) are injected at reconcile time via a ConfigMap and a
Secret created during `tofu apply`.

## Variable injection

The `flux-bootstrap` module creates two Kubernetes objects in `flux-system` before
Flux reconciles:

| Object | Kind | Key | Source |
|--------|------|-----|--------|
| `cluster-config` | ConfigMap | `base_domain` | `var.base_domain` (defaults to `<floating-ip>.sslip.io`) |
| `cluster-secrets` | Secret | `zenith_token_signing_key` | `random_password` resource (32 chars) |

HelmRelease manifests reference these values via `${variable}` syntax and
`postBuild.substituteFrom` in the root Kustomization.

## Adding a new environment

1. Create `tofu/environments/<name>/` — copy `all-in-one/` and change `flux_path`.
2. Create `flux/clusters/<name>/apps.yaml` and `capi-providers.yaml` — copy from `all-in-one/`.
3. If the new environment needs a different app set, create `flux/apps-<variant>/` and
   point `apps.yaml` to it.
