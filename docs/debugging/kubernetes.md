# Debugging Kubernetes

As described in [Configuring Kubernetes](../configuration/10-kubernetes-clusters.md),
Azimuth uses [Cluster API](https://cluster-api.sigs.k8s.io/) to manage tenant Kubernetes
clusters.

Cluster API resources are managed by releases of the
[openstack-cluster Helm chart](https://github.com/azimuth-cloud/capi-helm-charts/tree/main/charts/openstack-cluster),
which in turn are managed by the
[azimuth-capi-operator](https://github.com/azimuth-cloud/azimuth-capi-operator) in response
to changes to instances of the `clusters.azimuth.stackhpc.com` custom resource.
These instances are created, updated and deleted in Kubernetes by the Azimuth API in
response to user actions.

The Azimuth API creates a namespace for each project, in which cluster resources are
created. These namespaces are of the form `az-<sanitized project name>`.

It is also important to note that the Kubernetes API servers for tenant clusters do
not use Octavia load balancers like the Azimuth HA cluster. Instead, the API servers
for tenant clusters are exposed via Zenith.

When issues occur with cluster provisioning, here are some things to try in order to
locate the issue.

## Before you start

This guide covers Kubernetes clusters provisioned by Azimuth on OpenStack.
These checks require Kubernetes access to the Azimuth installation; an Azimuth portal login or an OpenStack application credential alone is not enough.
Run the provisioning checks against the cluster hosting Azimuth: the [K3s cluster](access-k3s.md) for a single node installation, or the [HA cluster](access-ha.md) for an HA installation.
The tenant cluster is the Kubernetes cluster created for a user.
The sections below say when to switch to that cluster's kubeconfig.

For development without deployment credentials, start with [Checks without a cloud](../developing/index.md#checks-without-a-cloud).

## Cluster resource exists

First, check if the Azimuth cluster resource exists in the tenant namespace.
The examples below use namespace `az-demo` and cluster name `demo`; replace these with your own values.

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n az-demo get clusters.azimuth.stackhpc.com
kubectl -n az-demo describe clusters.azimuth.stackhpc.com demo
```

If no cluster resource exists, check if the Kubernetes CRDs are installed:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl get crd clusters.azimuth.stackhpc.com clustertemplates.azimuth.stackhpc.com apptemplates.azimuth.stackhpc.com
```

If they do not exist, check if the `azimuth-capi-operator` is running:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n azimuth get pods -l app.kubernetes.io/instance=azimuth-capi-operator
```

## Helm release exists

The `azimuth-capi-operator` creates a Helm release with the same name and namespace as the Azimuth cluster resource:

```sh title="On the K3s node, targeting the HA cluster if deployed"
helm -n az-demo list --all
helm -n az-demo status demo
```

If the release is missing or failed, check the cluster resource's status and the operator logs for warnings or errors:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n az-demo describe clusters.azimuth.stackhpc.com demo
kubectl -n azimuth logs deploy/azimuth-capi-operator --tail=200
```

If the operator needs to be restarted after resolving an error:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n azimuth rollout restart deploy/azimuth-capi-operator
```

## Cluster API resource status

If the Helm release is in the `deployed` status, the next thing to check is the
state of the Cluster API resources that were created:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n az-demo get cluster-api
kubectl -n az-demo describe clusters.cluster.x-k8s.io demo
kubectl -n az-demo get events --sort-by=.metadata.creationTimestamp
```

The Cluster API resource `clusters.cluster.x-k8s.io` is distinct from the Azimuth cluster resource checked above.
Inspect its conditions and those of its machines for provisioning errors.
Ready machines should have an associated node name.

Check the add-ons separately:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n az-demo get helmreleases.addons.stackhpc.com,manifests.addons.stackhpc.com
```

The add-ons depend on the cluster template and the options selected for the cluster.
When enabled, the Headlamp add-on creates a `headlamp` Helm release in the tenant cluster's `headlamp` namespace.
Monitoring uses `kube-prometheus-stack` and `loki-stack` in `monitoring-system`.
The corresponding add-on resources should reach `Deployed`.

If resources are not becoming ready, check the interactive console of the cluster nodes in Horizon to see if the nodes had any problems joining the cluster.
Also
[check to see if the Zenith service](./zenith-services.md) for the API server was created
correctly - once all control plane nodes have registered correctly the `Endpoints` resource
for the service should have an entry for each control plane node (usually three).

If these all look OK, check the logs of the Cluster API providers for any errors:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n capi-system logs deploy/capi-controller-manager
kubectl -n capi-kubeadm-bootstrap-system logs deploy/capi-kubeadm-bootstrap-controller-manager
kubectl -n capi-kubeadm-control-plane-system logs deploy/capi-kubeadm-control-plane-controller-manager
kubectl -n capo-system logs deploy/capo-controller-manager
kubectl -n capi-addon-system logs deploy/cluster-api-addon-provider
```

### Recovering clusters stuck in failed state after network disruption

After a network outage, a cluster may retain a legacy `failureMessage` or `failureReason` even after connectivity has recovered.
These fields are deprecated in Cluster API.
The commands below explicitly use its `v1beta1` API, where they remain directly under `status`.

Inspect the affected cluster:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n az-demo get clusters.v1beta1.cluster.x-k8s.io demo -o yaml
```

A populated failure field does not by itself show that the error is stale.
Check the cluster's conditions, node health and controller logs first.
If the underlying problem has been resolved and only a stale failure remains, remove `status.failureMessage` and `status.failureReason` from that cluster:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n az-demo edit --subresource=status clusters.v1beta1.cluster.x-k8s.io/demo
```

## Accessing tenant clusters

The kubeconfigs for all tenant clusters are stored as secrets. First, you need
to find the name and namespace of the cluster you want to debug. This can be
seen from the list of clusters:

```command title="On the K3s node, targeting the HA cluster if deployed"
kubectl get cluster.cluster.x-k8s.io -A
```

Then, you can retrieve and decode the kubeconfig with the following:

```command title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n <namespace> get secret <clustername>-kubeconfig -o json | \
    jq -r '.data.value' | \
    base64 -d \
    > kubeconfig-tenant.yaml
```

This can now be used by exporting the path to this file:

```command title="On the K3s node, targeting the HA cluster if deployed"
export KUBECONFIG=kubeconfig-tenant.yaml
```

Subsequent `kubectl` and `helm` commands now target the tenant cluster.

## Zenith service issues

Zenith services are enabled on Kubernetes clusters using the
[Zenith operator](https://github.com/azimuth-cloud/zenith/tree/main/operator). Each tenant
Kubernetes cluster gets an instance of the operator that runs on the Azimuth cluster,
where it can reach the Zenith registrar to allocate subdomains, but watches the tenant
cluster for instances of the `reservation.zenith.stackhpc.com` and
`client.zenith.stackhpc.com` custom resources.

By creating instances of these resources in the tenant cluster, Kubernetes `Services` in
the target cluster can be exposed via Zenith.

If Zenith services are not becoming available for Kubernetes cluster services, follow the procedure for [debugging a Zenith service](./zenith-services.md) on the cluster hosting Azimuth.
Then use the tenant cluster's kubeconfig to check that its Zenith clients were created correctly and that their pods are running:

```sh title="Targeting the tenant cluster"
kubectl get reservations.zenith.stackhpc.com,clients.zenith.stackhpc.com -A
kubectl get deploy,pods -A -l app.kubernetes.io/managed-by=zenith-operator
```

When the dashboard add-on is enabled, look for `headlamp-client` in the `headlamp` namespace, pointing to the `headlamp` service.
When monitoring is enabled, look for `kube-prometheus-stack-client` in `monitoring-system`, pointing to `kube-prometheus-stack-grafana`.
Reservations should be `Ready` and clients should be `Available`.

Switch back to the cluster hosting Azimuth before running the commands below.
On the K3s node in a single node installation, run `unset KUBECONFIG`.
For an HA installation, select the HA kubeconfig as shown in [Accessing the HA cluster](access-ha.md).

<!-- prettier-ignore-start -->
!!! tip
    The kubeconfig for a tenant cluster is available in a secret in the tenant namespace:
    ```command title="On the K3s node, targeting the HA cluster if deployed"
    kubectl -n az-demo get secret | grep kubeconfig
    demo-kubeconfig                                   cluster.x-k8s.io/secret               1      11d
    ```
<!-- prettier-ignore-end -->

If everything looks OK, try restarting the Zenith operator for the cluster:

```command title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n az-demo rollout restart deploy/demo-zenith-operator
```
