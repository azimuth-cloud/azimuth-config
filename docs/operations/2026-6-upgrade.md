# Upgrading Azimuth or Standalone CAPI Management Clusters to 2026.6.x

## Background

It is imperative that these steps are followed **before** upgrading to azimuth-config 2026.6.x.
They apply if you are upgrading Azimuth, or a Standalone CAPI Management Cluster for Magnum.

azimuth-config 2026.6.x introduced an updated version of cluster-api-provider-openstack, alongside updated CustomResoureDefinitions for CAPO objects: `openstackclusters`, `openstackclustertemplates`, `openstackmachines` and `openstackmachinetemplates`.

In cases where Cluster API management clusters have existed for a long time, it is possible that old versions of these objects exist in the cluster, which can prevent the upgrade from succeeding, requiring nasty interventions to allow it to do so, and possibly incurring data loss.

Alongside this, CAPO changed Neutron security groups applied to ports attached to tenant cluster worker nodes to restrict more incoming traffic, which particularly affected users with Ingress controllers (or other Kubernetes `LoadBalancer` type services) running behind Octavia **OVN** loadbalancers, (**not Amphora**). Most cases of this are handled directly by azimuth-config and ansible-collection-azimuth-ops, but Standalone CAPI Management Cluster deployments where **both the OVN and Amphora** Octavia loadbalancer providers are available on the cloud **and** `openstack_loadbalancer_provider` is set to `amphora` in azimuth-config, should take extra steps during the upgrade to azimuth-config 2026.6.x to ensure that external traffic to any tenant Magnum clusters with Kubernetes `LoadBalancer` type services is not disrupted.

Finally, when a Standalone CAPI Management Cluster used for magnum-capi-helm is upgraded past 2026.6.x, it is important that the default capi-helm-charts version is raised >=0.26.1. This ensures that upgraded and new Magnum tenant cluster worker nodes are assigned security group rules permissive enough to allow external traffic to reach ports behind Kubernetes `LoadBalancer` type services when Octavia OVN Loadbalancers are used.

## Actions

Because of the repository branching model chosen for azimuth-config, it is not possible to go back and fix these issues in the deployment configuration, therefore there are manual actions to take before upgrading a an Azimuth or a Standalone CAPI Management Cluster to azimuth-config 2026.6.x.

To ensure that the target cluster is in a state for the upgrade to apply successfully and not disrupt user traffic, take the following steps:

## Ensure CAPO resources are upgraded (Azimuth and Standalone CAPI Management Clusters)

### Targeting k3s

1. [Access the seed node using SSH](../debugging/access-k3s.md):

   ```bash
   ./bin/seed-ssh
   ```

2. Check for versions other than `v1beta1` in `status.storedVersions` on CAPO `CustomResourceDefinitions`:

   ```bash
   for i in openstackclusters openstackclustertemplates openstackmachines openstackmachinetemplates; do
     kubectl get customresourcedefinitions ${i}.infrastructure.cluster.x-k8s.io -o jsonpath={.status.storedVersions}
   done
   ```

   - If anything other than `["v1beta1"]["v1beta1"]["v1beta1"]["v1beta1"]` appears in the output, progress to the next step (step 3).
   - If `["v1beta1"]["v1beta1"]["v1beta1"]["v1beta1"]`appears in the output, progress to [Targeting the HA management cluster](#targeting-the-ha-management-cluster).

3. Replace all `openstackmachinetemplates` (this ensures that they are stored at version `v1beta1` in etcd):

   ```bash
   kubectl get openstackmachinetemplates -A -o json | kubectl replace -f -
   ```

4. Patch CAPO CustomResourceDefinitions to only have `v1beta1` in their `status.storedVersions`:

   ```bash
   for i in openstackclusters openstackclustertemplates openstackmachines openstackmachinetemplates; do
     kubectl patch customresourcedefinitions ${i}.infrastructure.cluster.x-k8s.io --subresource=status --type=merge -p '{"status":{"storedVersions":["v1beta1"]}}'
   done
   ```

### Targeting the HA management cluster

1. Set the `KUBECONFIG` environment variable to the path to the [HA management cluster kubeconfig](../debugging/access-ha.md).

2. Confirm that any installed Helm releases of `openstack-cluster` are using a CHART > 0.11.0:

   ```bash
   helm list -aA | grep -e openstack-cluster -e NAME
   NAME                                	NAMESPACE              	REVISION	UPDATED                                	STATUS  	CHART                                              	APP VERSION
   ai-factory                          	az-ai-factory          	10      	2025-12-04 10:09:55.80390334 +0000 UTC 	deployed	openstack-cluster-0.15.0                           	8ba80f0
   ai-platform                         	az-datascience         	27      	2026-05-21 07:51:40.106200696 +0000 UTC	deployed	openstack-cluster-0.19.2                           	15f9663
   container-ssh                       	az-datascience         	1       	2026-08-20 12:46:45.064161192 +0000 UTC	deployed	openstack-cluster-0.27.0                           	89334f5
   data-platform                        az-data-platform    	11115   	2026-07-14 13:04:55.701120608 +0000 UTC	deployed	openstack-cluster-0.19.2                           	15f9663
   dbrepo-ci-cd                        	az-data-db           	29      	2026-08-04 10:32:13.57906988 +0000 UTC 	deployed	openstack-cluster-0.20.0                           	a5a975c
   dbrepo-staging                      	az-data-db           	10      	2026-08-04 10:32:21.12659442 +0000 UTC 	deployed	openstack-cluster-0.20.0                           	a5a975c
   dbrepo-test                         	az-data-db           	20      	2026-08-04 10:32:26.68875398 +0000 UTC 	deployed	openstack-cluster-0.20.0                           	a5a975c
   gitlab-runners                      	az-gitlab-runners      	7       	2026-08-04 08:17:29.720914089 +0000 UTC	deployed	openstack-cluster-0.20.0                           	a5a975c
   jaas-production                     	az-jaas-production     	79      	2026-07-17 13:28:23.43049949 +0000 UTC 	deployed	openstack-cluster-0.19.2                           	15f9663
   jaas-science                        	az-data-jaas        	60      	2026-08-04 09:30:40.201534802 +0000 UTC	deployed	openstack-cluster-0.20.0                           	a5a975c
   k8s-accel                            az-e101-accel         	2       	2026-08-05 09:33:43.055067369 +0000 UTC	deployed	openstack-cluster-0.20.0                           	a5a975c
   mlflow                              	az-data-jaas-staging	63      	2026-08-04 11:34:19.945313453 +0000 UTC	deployed	openstack-cluster-0.20.0                           	a5a975c
   mlops-skeleton-test                 	az-tarot             	10      	2026-06-24 11:54:07.196543353 +0000 UTC	deployed	openstack-cluster-0.19.2                           	15f9663
   mlops-test                          	az-tarot             	2       	2025-10-02 07:43:49.950208119 +0000 UTC	deployed	openstack-cluster-0.15.0                           	8ba80f0
   ```

   - This example shows all `openstack-cluster` releases are using a chart > 0.11.0.
   - **If there are releases using charts at 0.11.0 and older, then they must be updated to use more recent chart versions. The upgrade to 2026.6.x must be paused until users have updated their clusters, either using the Azimuth portal UI, or the Magnum CLI.**

3. Check for versions other than `v1beta1` in `status.storedVersions` on CAPO `CustomResourceDefinitions`:

   ```bash
   for i in openstackclusters openstackclustertemplates openstackmachines openstackmachinetemplates; do
     kubectl get customresourcedefinitions ${i}.infrastructure.cluster.x-k8s.io -o jsonpath={.status.storedVersions}
   done
   ```

   - If anything other than `["v1beta1"]["v1beta1"]["v1beta1"]["v1beta1"]` appears in the output, progress to step 4.
   - If `["v1beta1"]["v1beta1"]["v1beta1"]["v1beta1"]` appears in the output and you are upgrading a Standalone CAPI Management Cluster for magnum-capi-helm, proceed to [Fix tenant worker node security groups (Standalone CAPI Management Clusters for magnum-capi-helm only)](#fix-tenant-worker-node-security-groups-standalone-capi-management-clusters-for-magnum-capi-helm-only). If you are upgrading an Azimuth that does not also act as a CAPI Management Cluster for magnum-capi-helm, it is safe to proceed with the upgrade to 2026.6.x without any further action.

4. Replace all `openstackmachinetemplates` (this ensures that they are stored at version `v1beta1` in etcd). It is safe to just replace `openstackmachinetemplates` as all other objects should be automatically stored at apiVersion `v1beta1` when they are (re)created by a Helm release using `openstack-cluster>0.11.0`.

   ```bash
   kubectl get openstackmachinetemplates -A -o json | kubectl replace -f -
   ```

5. Patch CAPO `CustomResourceDefinitions` to only have `v1beta1` in their `status.storedVersions`:

```bash
for i in openstackclusters openstackclustertemplates openstackmachines openstackmachinetemplates; do
  kubectl patch customresourcedefinitions ${i}.infrastructure.cluster.x-k8s.io --subresource=status --type=merge -p '{"status":{"storedVersions":["v1beta1"]}}'
done
```

## Fix tenant worker node security groups (Standalone CAPI Management Clusters for magnum-capi-helm only)

### OpenStack CLI

1. Determine if the cloud has multiple Octavia loadbalancer providers using

   ```bash
   openstack loadbalancer provider list
   ```

   - If there are multiple loadbalancer providers available i.e. both `ovn` and `amphora` are listed in the output of the above command, proceed to [In azimuth-config](#in-azimuth-config).
   - If there is a single loadbalancer provider available, either `ovn` or `amphora`, it is safe to proceed with the upgrade to 2026.6.x without any further action.

### In azimuth-config

1. Determine if `openstack_loadbalancer_provider` is set to `amphora` in azimuth-config using

   ```bash
   grep -r openstack_loadbalancer_provider environments/
   ```

   If there are two loadbalancer providers available on the cloud, then this will always be set to either `ovn` or `amphora` for your environment.
   - If `openstack_loadbalancer_provider` is set to `amphora` proceed to [Targeting the HA management cluster](#targeting-the-ha-management-cluster_1).
   - If `openstack_loadbalancer_provider` is set to `ovn`, it is safe to proceed with the upgrade to 2026.6.x without any further action.

### Targeting the HA management cluster

1. [Access the seed node using SSH](../debugging/access-k3s.md)

   ```bash
   ./bin/seed-ssh
   ```

2. Set the `KUBECONFIG` environment variable to the path to the [HA management cluster kubeconfig](../debugging/access-ha.md).

3. Check for `openstackclusters` that use OVN loadbalancers:

   ```bash
   kubectl get openstackclusters -A -o jsonpath={.items[*].spec.apiServerLoadBalancer.provider} | grep -i ovn
   ```

   - If output from the above command contains `ovn`, proceed to step 4.
   - If the output from the above command is empty, it is safe to proceed with the upgrade to 2026.6.x without any further action.

4. [Pause reconciliation on all CAPI clusters](./maintenance.md/#tenant-clusters):

   ```bash
   kubectl annotate --all --all-namespaces clusters.cluster.x-k8s.io cluster.x-k8s.io/paused=true
   ```

5. Proceed with the upgrade playbook, either [manually](../deployment/index.md#deploying-an-environment) or triggered by [continuous deployment](../deployment/automation.md) if available.

6. Patch `openstackcluster` objects to ensure that their worker nodes retain the same security group rules after the upgrade:

   ```bash
   kubectl get openstackclusters.infrastructure.cluster.x-k8s.io -A --no-headers -o custom-columns="NS:.metadata.namespace,NAME:.metadata.name" | while read -r namespace name; do
        echo "Patching OpenStackCluster: $name in namespace: $namespace..."
        kubectl patch openstackclusters.infrastructure.cluster.x-k8s.io -n $namespace $name --type merge --patch='{"spec":{"managedSecurityGroups":{"workerNodesSecurityGroupRules":[{"direction":"ingress","etherType":"IPv4","name":"Worker nodePort TCP","portRangeMax":32767,"portRangeMin":30000,"protocol":"tcp","remoteIPPrefix":"0.0.0.0/0"},{"direction":"ingress","etherType":"IPv4","name":"Worker nodePort UDP","portRangeMax":32767,"portRangeMin":30000,"protocol":"udp","remoteIPPrefix":"0.0.0.0/0"}]}}}'
   done
   ```

7. [Unpause reconciliation on all CAPI clusters](./maintenance.md/#tenant-clusters):

   ```bash
   kubectl annotate --all --all-namespaces clusters.cluster.x-k8s.io cluster.x-k8s.io/paused-
   ```
