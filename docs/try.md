# Try Azimuth

If you have access to a project on an OpenStack cloud, you can try Azimuth using the
`all-in-one` environment. This deploys the full Azimuth stack — including Zenith and
the Azimuth portal — onto a single Talos Linux node.

## Prerequisites

- [OpenTofu](https://opentofu.org/) ≥ 1.6
- [talosctl](https://www.talos.dev/latest/talos-guides/install/talosctl/)
- [flux](https://fluxcd.io/flux/installation/) CLI
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- An OpenStack project with a floating IP pool and sufficient quota
- An OpenStack [Application Credential](https://docs.openstack.org/keystone/latest/user/application_credentials.html)
- A Talos RAW image uploaded to Glance (see [Talos image guide](./talos-image.md))

## Deploy

```sh
cd tofu/environments/all-in-one

cat > terraform.tfvars <<EOF
openstack_auth_url                      = "https://cloud.example.com:5000"
openstack_application_credential_id     = "<id>"
openstack_application_credential_secret = "<secret>"
external_network_id                     = "<network-uuid>"
talos_image_id                          = "<glance-image-uuid>"
flavor_name                             = "m1.xlarge"
git_url                                 = "https://github.com/your-org/azimuth-config"
git_branch                              = "main"
# Optional — defaults to <floating-ip>.sslip.io
# base_domain = "azimuth.example.com"
EOF

tofu init
tofu apply
```

`tofu apply` will:

1. Allocate a floating IP on OpenStack
2. Generate a Talos machine config and provision the VM
3. Wait for `talosctl health` to confirm the cluster is ready
4. Run `flux install` and create the GitRepository + Kustomization pointing to
   `flux/clusters/all-in-one`
5. Create the `cluster-config` ConfigMap and `cluster-secrets` Secret in `flux-system`

## Monitor reconciliation

```sh
export KUBECONFIG=$PWD/.work/kubeconfig.yaml

# Watch Flux Kustomizations
flux get kustomizations --watch

# Watch HelmReleases
kubectl get helmreleases -A --watch
```

## Access Azimuth

Once all HelmReleases are `Ready`, open the Azimuth portal:

```sh
# Print the portal URL
echo "https://azimuth.$(tofu output -raw seed_ip).sslip.io"
```

Log in with the same credentials you use on the target OpenStack cloud.

## Tear down

```sh
tofu destroy
```

## Limitations

- Uses [sslip.io](https://sslip.io) for DNS — no DNS record required.
- TLS certificates are issued automatically by cert-manager using the ACME HTTP-01
  challenge (requires the floating IP to be reachable from the internet).
- Community images are uploaded as private images within the same project.
- This is a single-node topology — not suitable for production use.
