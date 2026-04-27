# Talos Linux — Image pour OpenStack

## Génération de l'image

1. Aller sur https://factory.talos.dev/
2. Choisir la version (ex. v1.9.5)
3. Sélectionner les extensions nécessaires :
   - `siderolabs/openstack-cloud-controller-manager` (si cloud-controller-manager OpenStack est utilisé)
   - `siderolabs/iscsi-tools` (pour les volumes Cinder avec iSCSI)
4. Télécharger le format **OpenStack (.qcow2)**

## Upload dans Glance

```bash
# Via CLI OpenStack
openstack image create "talos-v1.9.5" \
  --file talos-v1.9.5-openstack-amd64.qcow2 \
  --disk-format qcow2 \
  --container-format bare \
  --property os_type=linux \
  --property hw_vif_multiqueue_enabled=true \
  --private

# Récupérer l'ID pour terraform.tfvars
openstack image show "talos-v1.9.5" -f value -c id
```

## Via OpenTofu (upload automatique)

Ajouter dans `tofu/environments/single-node/main.tf` :

```hcl
resource "openstack_images_image_v2" "talos" {
  name             = "talos-v1.9.5"
  local_file_path  = "talos-v1.9.5-openstack-amd64.qcow2"
  container_format = "bare"
  disk_format      = "qcow2"
  properties = {
    os_type                    = "linux"
    hw_vif_multiqueue_enabled  = "true"
  }
}
```

Puis référencer `openstack_images_image_v2.talos.id` comme `talos_image_id`.

## Accès au cluster après provisioning

```bash
# Vérifier le statut du nœud Talos
talosctl --talosconfig tofu/environments/single-node/.work/talosconfig \
  health --nodes <FLOATING_IP>

# Récupérer le kubeconfig
export KUBECONFIG=tofu/environments/single-node/.work/kubeconfig.yaml
kubectl get nodes

# Vérifier les HelmRelease FluxCD
kubectl get helmreleases -A
```
