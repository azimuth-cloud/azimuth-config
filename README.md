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
├── clusters/<environment>/         ← Flux Kustomizations per environment
│   ├── apps.yaml                   → flux/apps/  (cert-manager, sealed-secrets, CAPI…)
│   ├── capi-providers.yaml         → CAPI CoreProvider + InfrastructureProvider (Talos)
│   ├── azimuth.yaml                → flux/azimuth/  (portal — all-in-one only)
│   └── azimuth-cluster.yaml        → flux/workload/azimuth-cluster/  (single-node only)
├── apps/                           ← seed infrastructure
│   ├── _sources/                   ← HelmRepository definitions
│   ├── cert-manager/
│   ├── sealed-secrets/
│   ├── cluster-api/                ← capi-operator + CAPO
│   ├── cluster-api-addon-provider/
│   └── capi-janitor/
├── azimuth/                        ← Azimuth portal + operators (all-in-one or seed)
│   ├── ingress-nginx/
│   ├── kube-prometheus-stack/
│   ├── loki-stack/
│   ├── zenith/
│   ├── azimuth/
│   ├── azimuth-capi-operator/
│   └── …
└── workload/azimuth-cluster/       ← CAPI workload cluster manifests (single-node)
    ├── cluster.yaml                ← OpenStackCluster + Cluster
    ├── control-plane.yaml          ← TalosControlPlane + OpenStackMachineTemplate
    ├── addons.yaml                 ← HelmRelease (cluster-addons chart)
    └── openstack-credentials.yaml  ← clouds.yaml Secret
```

### Environment taxonomy

| Environment  | Seed VM topology            | Workload cluster | Azimuth portal          |
|--------------|-----------------------------|------------------|-------------------------|
| `all-in-one` | Talos, 1 node               | none (seed = workload) | On the seed VM    |
| `single-node`| Talos, 1 node (management)  | CAPO → 1 node    | On the workload cluster |

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
openstack_region_name                   = "RegionOne"
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

# Copy and fill in the variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your OpenStack credentials, image ID, Git URL, etc.

# Run the fully-automated deployment script
bash apply.sh
```

`apply.sh` handles the full lifecycle end-to-end:
1. `tofu init && tofu apply` — provisions the seed VM, pre-allocates the FIP, bootstraps Flux
2. Creates the `cluster-overrides` ConfigMap with network/flavor/placeholder domain
3. Waits for CAPI + CAPO to become ready
4. Waits for the CAPO `OpenStackCluster` object to reach `READY=true`
5. Discovers the workload node floating IP from `openstackmachine` status
6. Patches `cluster-overrides` with the real base domain (`<fip>.sslip.io`)
7. Triggers `flux reconcile kustomization azimuth-cluster`
8. Saves the workload cluster kubeconfig to `.work/azimuth.kubeconfig.yaml`
9. Polls until the Azimuth portal responds

On completion, outputs:

```
  Seed kubeconfig:     .work/kubeconfig.yaml
  Workload kubeconfig: .work/azimuth.kubeconfig.yaml
  Azimuth portal:      https://portal.<fip>.sslip.io
```

## Documentation

Full documentation is in the [docs/](./docs/) directory:

- [Talos image preparation](./docs/talos-image.md)
- [Environment taxonomy](./docs/environments.md)
- [Try Azimuth](./docs/try.md)
- [Production checklist](./docs/production.md)
