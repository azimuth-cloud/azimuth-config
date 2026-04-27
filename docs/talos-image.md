# Talos Linux — Image pour OpenStack

## Génération de l'image

1. Aller sur https://factory.talos.dev/
2. Choisir la version (ex. `v1.9.5`)
3. Sélectionner le **platform `openstack`** dans la liste des plateformes supportées
4. Télécharger le format **RAW** (pas QCOW2)

> L'image générée est un fichier `.raw`. Le platform `openstack` de la factory Talos
> inclut les drivers et la configuration nécessaires pour OpenStack (VirtIO, cloud-init minimal).

## Upload dans Glance

```bash
openstack image create "talos-v1.9.5" \
  --file talos-v1.9.5-openstack-amd64.raw \
  --disk-format raw \
  --container-format bare \
  --property os_type=linux \
  --property hw_vif_multiqueue_enabled=true \
  --private

# Récupérer l'ID pour terraform.tfvars
openstack image show "talos-v1.9.5" -f value -c id
```

## Via OpenTofu (upload automatique)

```hcl
resource "openstack_images_image_v2" "talos" {
  name             = "talos-v1.9.5"
  local_file_path  = "talos-v1.9.5-openstack-amd64.raw"
  container_format = "bare"
  disk_format      = "raw"
  properties = {
    os_type                   = "linux"
    hw_vif_multiqueue_enabled = "true"
  }
}
```

Puis référencer `openstack_images_image_v2.talos.id` comme `talos_image_id`.

## Accès au cluster après provisioning

```bash
# Vérifier le statut du nœud Talos
talosctl --talosconfig tofu/environments/all-in-one/.work/talosconfig \
  health --nodes <FLOATING_IP>

# Utiliser le kubeconfig
export KUBECONFIG=tofu/environments/all-in-one/.work/kubeconfig.yaml
kubectl get nodes

# Vérifier les HelmRelease FluxCD
kubectl get helmreleases -A
```
