# azimuth-config <!-- omit in toc -->

This repository contains reference configuration and infrastructure-as-code for deployments of
[Azimuth](https://github.com/azimuth-cloud/azimuth), including all required dependencies.

Azimuth is deployed using [OpenTofu](https://opentofu.org/) to provision a
[Talos Linux](https://www.talos.dev/) Kubernetes node on OpenStack, and
[FluxCD](https://fluxcd.io/) for GitOps-driven application delivery.

## Architecture

```
OpenTofu (provisioning)
├── OpenStack: network, security groups, floating IP, Cinder volume
├── Talos Linux node (immutable OS, zero-SSH, API-driven)
├── Talos machine config injected as user_data
├── Kubernetes cluster bootstrap via talosctl
└── FluxCD bootstrap (flux install + kustomization)

Git repo (GitOps — flux/)
├── clusters/<environment>/   ← Flux Kustomizations per environment
│   ├── apps.yaml             → flux/apps/
│   └── capi-providers.yaml   → CAPI CoreProvider + InfrastructureProvider
└── apps/                     ← shared HelmRelease manifests
    ├── cert-manager/
    ├── ingress-nginx/
    ├── sealed-secrets/
    ├── cluster-api/          ← capi-operator + CAPO
    ├── azimuth-capi-operator/
    ├── zenith/
    ├── azimuth/
    └── kube-prometheus-stack/
```

### Environment taxonomy

| Environment  | Seed VM topology | Workload cluster       | Zenith + Azimuth portal |
|--------------|-----------------|------------------------|-------------------------|
| `all-in-one` | Talos, 1 node   | none (seed = workload) | On the seed VM          |
| `single-node`| Talos, 1 node (management) | CAPO → 1 node | On the workload cluster |
| `multi-node` | Talos, 1 node (management) | CAPO → 3 nodes | On the workload cluster |

The seed VM always runs CAPI + CAPO. Only `all-in-one` runs the Azimuth portal directly on it.

## Quick start

### Prerequisites

- [OpenTofu](https://opentofu.org/) ≥ 1.6
- [talosctl](https://www.talos.dev/latest/talos-guides/install/talosctl/)
- [flux](https://fluxcd.io/flux/installation/) CLI
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- A Talos RAW image uploaded to OpenStack Glance (see [docs/talos-image.md](./docs/talos-image.md))
- An OpenStack Application Credential

### Deploy all-in-one

```sh
cd tofu/environments/all-in-one

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
openstack_auth_url                      = "https://cloud.example.com:5000"
openstack_application_credential_id     = "<id>"
openstack_application_credential_secret = "<secret>"
external_network_id                     = "<network-uuid>"
talos_image_id                          = "<glance-image-uuid>"
flavor_name                             = "m1.xlarge"
git_url                                 = "https://github.com/your-org/azimuth-config"
git_branch                              = "main"
EOF

tofu init
tofu apply
```

Access the Azimuth portal at `https://azimuth.<floating-ip>.sslip.io`.

### Deploy single-node

```sh
cd tofu/environments/single-node

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
openstack_auth_url                      = "https://cloud.example.com:5000"
openstack_application_credential_id     = "<id>"
openstack_application_credential_secret = "<secret>"
external_network_id                     = "<network-uuid>"
talos_image_id                          = "<glance-image-uuid>"
flavor_id                               = "m1.xlarge"
git_url                                 = "https://github.com/your-org/azimuth-config"
git_branch                              = "main"
EOF

tofu init
tofu apply
```

After `tofu apply`, create the `cluster-overrides` ConfigMap with the OpenStack flavor
for the Azimuth workload cluster. This value is cloud-specific and is not managed by Tofu:

```sh
KUBECONFIG=.work/kubeconfig.yaml \
kubectl -n flux-system create configmap cluster-overrides \
  --from-literal=azimuth_cluster_flavor=<flavor-name-or-id> \
  --dry-run=client -o yaml | kubectl apply -f -
```

Flux will then provision the workload cluster via CAPO and deploy the Azimuth portal on it.

## Documentation

Full documentation is in the [docs/](./docs/) directory:

- [Talos image preparation](./docs/talos-image.md)
- [Environment taxonomy](./docs/environments.md)
- [Try Azimuth](./docs/try.md)
- [Production checklist](./docs/production.md)
