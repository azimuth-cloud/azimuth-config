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

## Cluster resource exists

First, check if the cluster resource exists in the tenant namespace:

```command title="On the K3s node, targetting the HA cluster if deployed"
$ kubectl -n az-demo get cluster
NAME   LABEL  TEMPLATE      KUBERNETES VERSION   PHASE   NODE COUNT   AGE
demo   demo   kube-1-24-2   1.24.2               Ready   4            11d
```

If no cluster resource exists, check if the Kubernetes CRDs are installed:

```command title="On the K3s node, targetting the HA cluster if deployed"
$ kubectl get crd | grep azimuth
apptemplates.azimuth.stackhpc.com                            2022-11-02T11:11:13Z
clusters.azimuth.stackhpc.com                                2022-11-02T10:53:26Z
clustertemplates.azimuth.stackhpc.com                        2022-11-02T10:53:26Z
```

If they do not exist, check if the `azimuth-capi-operator` is running:

```command title="On the K3s node, targetting the HA cluster if deployed"
$ kubectl -n azimuth get po -l app.kubernetes.io/instance=azimuth-capi-operator
NAME                                     READY   STATUS    RESTARTS   AGE
azimuth-capi-operator-5c65c4b598-h2thx   1/1     Running   0          10d
```

## Helm release exists

The first thing that the `azimuth-capi-operator` does when it sees a new cluster resource
is make a Helm release:

```command title="On the K3s node, targetting the HA cluster if deployed"
$ helm -n az-demo list -a
NAME   NAMESPACE      REVISION        UPDATED                                 STATUS          CHART                                   APP VERSION
demo   az-demo        1               2022-07-07 13:26:22.94084961 +0000 UTC  deployed        openstack-cluster-0.1.0-dev.0.main.161  a0bcee5
```

If the Helm release does not exist, restart the `azimuth-capi-operator`:

```sh title="On the K3s node, targetting the HA cluster if deployed"
kubectl -n azimuth rollout restart deploy/azimuth-capi-operator
```

If the Helm release does not get created, even after a restart, check the logs
of the `azimuth-capi-operator` for any warnings or errors:

```sh title="On the K3s node, targetting the HA cluster if deployed"
kubectl -n azimuth logs deploy/azimuth-capi-operator [-f]
```

## Cluster API resource status

If the Helm release is in the `deployed` status, the next thing to check is the
state of the Cluster API resources that were created:

```command title="On the K3s node, targetting the HA cluster if deployed"
$ kubectl -n az-demo get cluster-api
NAME                                                                  CLUSTER   BOOTSTRAP   TARGET NAMESPACE       RELEASE NAME                       PHASE      REVISION   AGE
manifests.addons.stackhpc.com/demo-cloud-config                       demo      true        openstack-system       cloud-config                       Deployed   1          11d
manifests.addons.stackhpc.com/demo-csi-cinder-storageclass            demo      true        openstack-system       csi-cinder-storageclass            Deployed   1          11d
manifests.addons.stackhpc.com/demo-kube-prometheus-stack-client       demo      true        monitoring-system      kube-prometheus-stack-client       Deployed   2          11d
manifests.addons.stackhpc.com/demo-kube-prometheus-stack-dashboards   demo      true        monitoring-system      kube-prometheus-stack-dashboards   Deployed   1          11d
manifests.addons.stackhpc.com/demo-kubernetes-dashboard-client        demo      true        kubernetes-dashboard   kubernetes-dashboard-client        Deployed   2          11d
manifests.addons.stackhpc.com/demo-loki-stack-dashboards              demo      true        monitoring-system      loki-stack-dashboards              Deployed   1          11d

NAME                                                             CLUSTER   BOOTSTRAP   TARGET NAMESPACE         RELEASE NAME                PHASE      REVISION   CHART NAME                           CHART VERSION         AGE
helmrelease.addons.stackhpc.com/dask-demo                        demo                  dask-demo                dask-demo                   Deployed   1          daskhub-azimuth                      0.1.0-dev.0.main.23   11d
helmrelease.addons.stackhpc.com/demo-ccm-openstack               demo      true        openstack-system         ccm-openstack               Deployed   1          openstack-cloud-controller-manager   1.3.0                 11d
helmrelease.addons.stackhpc.com/demo-cni-calico                  demo      true        tigera-operator          cni-calico                  Deployed   1          tigera-operator                      v3.23.3               11d
helmrelease.addons.stackhpc.com/demo-csi-cinder                  demo      true        openstack-system         csi-cinder                  Deployed   1          openstack-cinder-csi                 2.2.0                 11d
helmrelease.addons.stackhpc.com/demo-kube-prometheus-stack       demo      true        monitoring-system        kube-prometheus-stack       Deployed   1          kube-prometheus-stack                40.1.0                11d
helmrelease.addons.stackhpc.com/demo-kubernetes-dashboard        demo      true        kubernetes-dashboard     kubernetes-dashboard        Deployed   1          kubernetes-dashboard                 5.10.0                11d
helmrelease.addons.stackhpc.com/demo-loki-stack                  demo      true        monitoring-system        loki-stack                  Deployed   1          loki-stack                           2.8.2                 11d
helmrelease.addons.stackhpc.com/demo-mellanox-network-operator   demo      true        network-operator         mellanox-network-operator   Deployed   1          network-operator                     1.3.0                 11d
helmrelease.addons.stackhpc.com/demo-metrics-server              demo      true        kube-system              metrics-server              Deployed   1          metrics-server                       3.8.2                 11d
helmrelease.addons.stackhpc.com/demo-node-feature-discovery      demo      true        node-feature-discovery   node-feature-discovery      Deployed   1          node-feature-discovery               0.11.2                11d
helmrelease.addons.stackhpc.com/demo-nvidia-gpu-operator         demo      true        gpu-operator             nvidia-gpu-operator         Deployed   1          gpu-operator                         v1.11.1               11d

NAME                                                                CLUSTER   AGE
kubeadmconfig.bootstrap.cluster.x-k8s.io/demo-control-plane-5kjjt   demo     11d
kubeadmconfig.bootstrap.cluster.x-k8s.io/demo-control-plane-897r6   demo     11d
kubeadmconfig.bootstrap.cluster.x-k8s.io/demo-control-plane-x26zz   demo     11d
kubeadmconfig.bootstrap.cluster.x-k8s.io/demo-sm0-cc21616d-lddk6    demo     11d

NAME                                                                  AGE
kubeadmconfigtemplate.bootstrap.cluster.x-k8s.io/demo-sm0-cc21616d   11d

NAME                                                     CLUSTER  EXPECTEDMACHINES   MAXUNHEALTHY   CURRENTHEALTHY   AGE
machinehealthcheck.cluster.x-k8s.io/demo-control-plane   demo     3                  100%           3                11d
machinehealthcheck.cluster.x-k8s.io/demo-sm0             demo     1                  100%           1                11d

NAME                                             CLUSTER  REPLICAS   READY   AVAILABLE   AGE   VERSION
machineset.cluster.x-k8s.io/demo-sm0-c99fb7798   demo     1          1       1           11d   v1.24.2

NAME                                          CLUSTER  REPLICAS   READY   UPDATED   UNAVAILABLE   PHASE     AGE   VERSION
machinedeployment.cluster.x-k8s.io/demo-sm0   demo     1          1       1         0             Running   11d   v1.24.2

NAME                            PHASE         AGE   VERSION
cluster.cluster.x-k8s.io/demo   Provisioned   11d

NAME                                                CLUSTER  NODENAME                            PROVIDERID                                          PHASE     AGE   VERSION
machine.cluster.x-k8s.io/demo-control-plane-7p8zv   demo     demo-control-plane-7d76d0be-z6dm8   openstack:///f687f926-3cee-4550-91e5-32c2885708b0   Running   11d   v1.24.2
machine.cluster.x-k8s.io/demo-control-plane-9skvh   demo     demo-control-plane-7d76d0be-d2mcr   openstack:///ea91f79a-8abb-4cb9-a2ea-8f772568e93c   Running   11d   v1.24.2
machine.cluster.x-k8s.io/demo-control-plane-s8dhv   demo     demo-control-plane-7d76d0be-j64w6   openstack:///33a3a532-348a-4b93-ab19-d7d8cdb0daa4   Running   11d   v1.24.2
machine.cluster.x-k8s.io/demo-sm0-c99fb7798-qqk4j   demo     demo-sm0-7d76d0be-gdjwv             openstack:///ef9ae59c-bf20-44e0-831f-3798d25b7a06   Running   11d   v1.24.2

NAME                                                                   CLUSTER  INITIALIZED   API SERVER AVAILABLE   REPLICAS   READY   UPDATED   UNAVAILABLE   AGE   VERSION
kubeadmcontrolplane.controlplane.cluster.x-k8s.io/demo-control-plane   demo     true          true                   3          3       3         0             11d   v1.24.2

NAME                                                    CLUSTER  READY   NETWORK                                SUBNET                                 BASTION IP
openstackcluster.infrastructure.cluster.x-k8s.io/demo   demo     true    4b6b2722-ee5b-40ec-8e52-a6610e14cc51   73e22c49-10b8-4763-af2f-4c0cce007c82

NAME                                                                                 CLUSTER  INSTANCESTATE   READY   PROVIDERID                                          MACHINE
openstackmachine.infrastructure.cluster.x-k8s.io/demo-control-plane-7d76d0be-d2mcr   demo     ACTIVE          true    openstack:///ea91f79a-8abb-4cb9-a2ea-8f772568e93c   demo-control-plane-9skvh
openstackmachine.infrastructure.cluster.x-k8s.io/demo-control-plane-7d76d0be-j64w6   demo     ACTIVE          true    openstack:///33a3a532-348a-4b93-ab19-d7d8cdb0daa4   demo-control-plane-s8dhv
openstackmachine.infrastructure.cluster.x-k8s.io/demo-control-plane-7d76d0be-z6dm8   demo     ACTIVE          true    openstack:///f687f926-3cee-4550-91e5-32c2885708b0   demo-control-plane-7p8zv
openstackmachine.infrastructure.cluster.x-k8s.io/demo-sm0-7d76d0be-gdjwv             demo     ACTIVE          true    openstack:///ef9ae59c-bf20-44e0-831f-3798d25b7a06   demo-sm0-c99fb7798-qqk4j

NAME                                                                                   AGE
openstackmachinetemplate.infrastructure.cluster.x-k8s.io/demo-control-plane-7d76d0be   11d
openstackmachinetemplate.infrastructure.cluster.x-k8s.io/demo-sm0-7d76d0be             11d
```

The `cluster.cluster.x-k8s.io` resource should be `Provisioned`, the `machine.cluster.x-k8s.io`
resources should be `Running` with an associated `NODENAME`, the
`openstackmachine.infrastructure.cluster.x-k8s.io` resources should be `ACTIVE` and the
`{manifests,helmrelease}.addons.stackhpc.com` resources should all be `Deployed`.

If this is not the case, first check the interactive console of the cluster nodes in Horizon
to see if the nodes had any problems joining the cluster. Also
[check to see if the Zenith service](./zenith-services.md) for the API server was created
correctly - once all control plane nodes have registered correctly the `Endpoints` resource
for the service should have an entry for each control plane node (usually three).

If these all look OK, check the logs of the Cluster API providers for any errors:

```sh title="On the K3s node, targetting the HA cluster if deployed"
kubectl -n capi-system logs deploy/capi-controller-manager
kubectl -n capi-kubeadm-bootstrap-system logs deploy/capi-kubeadm-bootstrap-controller-manager
kubectl -n capi-kubeadm-control-plane-system logs deploy/capi-kubeadm-control-plane-controller-manager
kubectl -n capo-system logs deploy/capo-controller-manager
kubectl -n capi-addon-system logs deploy/cluster-api-addon-provider
```

### Recovering clusters stuck in failed state after network disruption

If the underlying cloud infrastructure has undergone maintenance or suffered
from temporary networking problems, clusters can get stuck in a 'Failed' state
even after the network is recovered and the cluster is otherwise fully
functional.
This is can happen when `failureMessage` and `failureReason` are set, which
Cluster API mistakenly interprets as an unrecoverable error and therefore
changes the cluster's status to `Failed`. There are ongoing discussions in the
Kubernetes community about resolving this mistaken interpretation of transient
networking errors but for now this failed status must be manually cleared.

If you think this is the case, you can check for affected clusters with the following command:

```command title="On the K3s node, targetting the HA cluster if deployed"
kubectl get cluster.cluster.x-k8s.io --all-namespaces -o json | jq -r '.items[] | "\(.metadata.name): \(.status.failureMessage) \(.status.failureReason)"'
```

Clusters where one or both of the `failure{Message,Reason}` fields is not
`null` are affected.
You can reset the status for an individual cluster by updating removing the
failure message and reason fields using
`kubectl edit --subresource=status clusters.cluster.x-k8s.io/<cluster-name>`.
Alternatively, you can apply a patch to all workload clusters at once using the
following command:

```command title="On the K3s node, targetting the HA cluster if deployed"
# Shell command to extract the list of failed clusters and generate the required `kubectl patch` command for each one
kubectl get cluster.cluster.x-k8s.io --all-namespaces -o json \
| jq -r '.items[] | select(.status.failureMessage or .status.failureReason) | "kubectl patch cluster.cluster.x-k8s.io \(.metadata.name) -n \(.metadata.namespace) --type=merge --subresource=status -p '\''{\"status\": {\"failureMessage\": null, \"failureReason\": null}}'\''"'
kubectl patch cluster.cluster.x-k8s.io demo1 -n az-demo --type=merge --subresource=status -p '{"status": {"failureMessage": null, "failureReason": null}}'
kubectl patch cluster.cluster.x-k8s.io demo2 -n az-demo --type=merge --subresource=status -p '{"status": {"failureMessage": null, "failureReason": null}}'
kubectl patch cluster.cluster.x-k8s.io demo3 -n az-demo --type=merge --subresource=status -p '{"status": {"failureMessage": null, "failureReason": null}}'
kubectl patch cluster.cluster.x-k8s.io demo4 -n az-demo --type=merge --subresource=status -p '{"status": {"failureMessage": null, "failureReason": null}}'

# Modification of the previous command which pipes the output into `sh` so that the `kubectl patch` commands are executed to fix the failed clusters
kubectl get cluster.cluster.x-k8s.io --all-namespaces -o json \
| jq -r '.items[] | select(.status.failureMessage or .status.failureReason) | "kubectl patch cluster.cluster.x-k8s.io \(.metadata.name) -n \(.metadata.namespace) --type=merge --subresource=status -p '\''{\"status\": {\"failureMessage\": null, \"failureReason\": null}}'\''"' \
| sh
cluster.cluster.x-k8s.io/demo1 patched
cluster.cluster.x-k8s.io/demo2 patched
cluster.cluster.x-k8s.io/demo3 patched
cluster.cluster.x-k8s.io/demo4 patched

```

## Accessing tenant clusters

The kubeconfigs for all tenant clusters are stored as secrets. First, you need
to find the name and namespace of the cluster you want to debug. This can be
seen from the list of clusters:

```command title="On the K3s node, targetting the HA cluster if deployed"
kubectl get cluster -A
```

Then, you can retrieve and decode the kubeconfig with the following:

```command title="On the K3s node, targetting the HA cluster if deployed"
kubectl -n <namespace> get secret <clustername>-kubeconfig -o json | \
    jq -r '.data.value' | \
    base64 -d \
    > kubeconfig-tenant.yaml
```

This can now be used by exporting the path to this file:

```command title="On the K3s node, targetting the HA cluster if deployed"
export KUBECONFIG=kubeconfig-tenant.yaml
```

## Zenith service issues

Zenith services are enabled on Kubernetes clusters using the
[Zenith operator](https://github.com/azimuth-cloud/zenith/tree/main/operator). Each tenant
Kubernetes cluster gets an instance of the operator that runs on the Azimuth cluster,
where it can reach the Zenith registrar to allocate subdomains, but watches the tenant
cluster for instances of the `reservation.zenith.stackhpc.com` and
`client.zenith.stackhpc.com` custom resources.

By creating instances of these resources in the tenant cluster, Kubernetes `Services` in
the target cluster can be exposed via Zenith.

If Zenith services are not becoming available for Kubernetes cluster services,
first follow the procedure for
[debugging a Zenith service](./zenith-services.md), including checking that the clients
were created correctly and that the pods are running:

```command title="Targetting the tenant cluster"
$ kubectl get zenith -A
NAMESPACE              NAME                                               PHASE       UPSTREAM SERVICE                MITM ENABLED   MITM AUTH        AGE
kubernetes-dashboard   client.zenith.stackhpc.com/kubernetes-dashboard    Available   kubernetes-dashboard            true           ServiceAccount   4d19h
monitoring-system      client.zenith.stackhpc.com/kube-prometheus-stack   Available   kube-prometheus-stack-grafana   true           Basic            4d19h

NAMESPACE              NAME                                                    SECRET                                    PHASE   FQDN                                                                AGE
kubernetes-dashboard   reservation.zenith.stackhpc.com/kubernetes-dashboard    kubernetes-dashboard-zenith-credential    Ready   mwqgcdrk77nva18uzcct3g7jlo7obi7zlbcgemuhk6nhk.azimuth.example.org   4d19h
monitoring-system      reservation.zenith.stackhpc.com/kube-prometheus-stack   kube-prometheus-stack-zenith-credential   Ready   zovdsnnesww2hiw074mvufvcfgczfbd2yhmuhsf3p59xa.azimuth.example.org   4d19h


$ kubectl get deploy,po -A -l app.kubernetes.io/managed-by=zenith-operator
NAMESPACE              NAME                                                  READY   UP-TO-DATE   AVAILABLE   AGE
kubernetes-dashboard   deployment.apps/kubernetes-dashboard-zenith-client    1/1     1            1           4d19h
monitoring-system      deployment.apps/kube-prometheus-stack-zenith-client   1/1     1            1           4d19h

NAMESPACE              NAME                                                      READY   STATUS    RESTARTS   AGE
kubernetes-dashboard   pod/kubernetes-dashboard-zenith-client-86c5fd9bd-2jfdb    2/2     Running   0          4d19h
monitoring-system      pod/kube-prometheus-stack-zenith-client-b9986579d-qgp82   2/2     Running   0          9h
```

<!-- prettier-ignore-start -->
!!! tip
    The kubeconfig for a tenant cluster is available in a secret in the tenant namespace:
    ```command title="On the K3s node, targetting the HA cluster if deployed"
    kubectl -n az-demo get secret | grep kubeconfig
    demo-kubeconfig                                   cluster.x-k8s.io/secret               1      11d
    ```
<!-- prettier-ignore-end -->

If everything looks OK, try restarting the Zenith operator for the cluster:

```command title="On the K3s node, targetting the HA cluster if deployed"
kubectl -n az-demo rollout restart deploy/demo-zenith-operator
```
