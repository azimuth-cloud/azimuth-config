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

Flux Kustomizations use `postBuild.substituteFrom` to inject runtime values into
manifests via `${variable}` syntax. Three sources are used, in order:

| Object | Kind | Managed by | Purpose |
|--------|------|------------|---------|
| `cluster-config` | ConfigMap | Tofu (`flux-bootstrap` module) | Infrastructure values: `base_domain`, `external_network_id`, `talos_image_id`, `kubernetes_version`, `azimuth_cluster_machine_name`, … |
| `cluster-secrets` | Secret | Tofu (`flux-bootstrap` module) | Sensitive values: `zenith_token_signing_key`, `azimuth_django_secret_key`, OpenStack credentials |
| `cluster-overrides` | ConfigMap | **Operator (kubectl)** | Cloud-specific values that cannot have a default: `azimuth_cluster_flavor`, `azimuth_cluster_network_id` |

`cluster-config` and `cluster-secrets` are created automatically by `tofu apply`.

`cluster-overrides` must be created manually by the operator after `tofu apply`, since
it contains values that are specific to each OpenStack cloud and cannot be determined
from the Tofu configuration alone:

| Variable | Description |
|----------|-------------|
| `azimuth_cluster_flavor` | OpenStack flavor name or ID for the workload cluster node |
| `azimuth_cluster_network_id` | OpenStack internal network ID on which workload cluster nodes are attached (`spec.network` in `OpenStackCluster`) |

```sh
KUBECONFIG=tofu/environments/single-node/.work/kubeconfig.yaml \
kubectl -n flux-system create configmap cluster-overrides \
  --from-literal=azimuth_cluster_flavor=<flavor-name-or-id> \
  --from-literal=azimuth_cluster_network_id=<network-uuid> \
  --dry-run=client -o yaml | kubectl apply -f -
```

The `azimuth-cluster` Kustomization will fail with a clear error if `cluster-overrides`
is absent, prompting the operator to create it before the workload cluster can be
provisioned.

## Adding a new environment

1. Create `tofu/environments/<name>/` — copy `all-in-one/` and change `flux_path`.
2. Create `flux/clusters/<name>/apps.yaml` and `capi-providers.yaml` — copy from `all-in-one/`.
3. If the new environment needs a different app set, create `flux/apps-<variant>/` and
   point `apps.yaml` to it.
