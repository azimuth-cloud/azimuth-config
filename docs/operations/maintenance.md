# Maintenance

## Pausing reconciliation of tenant and management clusters

Kubernetes clusters will automatically reconcile when resources are detected as
unavailable. Usually this is good, intended behaviour. However, if we have a
known period of time where statuses are expected to be incorrect or
unavailable, such as an outage window for OpenStack APIs, it is sensible 
pause reconciliation.

Reconciliation should be paused for all tenant clusters, and the CAPI management
cluster.

### Tenant clusters

Follow these steps to access the Seed VM and target the management cluster.

Apply the annotation ``cluster.x-k8s.io/paused=true`` to all clusters.

```bash
kubectl annotate --all --all-namespaces clusters.cluster.x-k8s.io cluster.x-k8s.io/paused=true
cluster.cluster.x-k8s.io/test-1 annotated
cluster.cluster.x-k8s.io/test-2 annotated
```

After the system is back in a stable state, remove the
``cluster.x-k8s.io/paused`` annotation.

```bash
kubectl annotate --all --all-namespaces clusters.cluster.x-k8s.io cluster.x-k8s.io/paused-
cluster.cluster.x-k8s.io/test-1 annotated
cluster.cluster.x-k8s.io/test-2 annotated
```

### Management cluster

Follow these steps to access the Seed VM and target the K3s cluster.

Get the name of the cluster.

```bash
kubectl get clusters.cluster.x-k8s.io
NAME           CLUSTERCLASS   PHASE         AGE    VERSION
cluster-name                  Provisioned   365d
```

Apply the annotation ``cluster.x-k8s.io/paused=true`` to the cluster.

```bash
kubectl annotate clusters.cluster.x-k8s.io/cluster-name cluster.x-k8s.io/paused=true
cluster.cluster.x-k8s.io/cluster-name annotated
```

After the system is back in a stable state, remove the
``cluster.x-k8s.io/paused`` annotation.

```bash
kubectl annotate clusters.cluster.x-k8s.io/cluster-name cluster.x-k8s.io/paused-
cluster.cluster.x-k8s.io/cluster-name annotated
```
