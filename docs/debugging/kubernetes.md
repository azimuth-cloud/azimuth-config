# Debugging Kubernetes

As described in [Configuring Kubernetes](../configuration/kubernetes.md), Azimuth uses
[Cluster API](https://cluster-api.sigs.k8s.io/) to manage tenant Kubernetes clusters.

Cluster API resources are managed by releases of the
[stackhpc/capi-helm-charts/openstack-cluster Helm chart](https://github.com/stackhpc/capi-helm-charts/tree/main/charts/openstack-cluster),
which in turn are managed by the
[azimuth-capi-operator](https://github.com/stackhpc/azimuth-capi-operator) in response
to changes to instances of the Kubernetes CRD `clusters.azimuth.stackhpc.com` resources.
These resources are created, updated and delete in Kubernetes by the Azimuth API in
response to user actions.

The Azimuth API creates a namespace for each tenant, in which cluster resources are
created. These namespaces are of the form `az-<sanitized tenant name>`.

It is also important to note that the Kubernetes API servers for tenant clusters do
not use Octavia load balancers like the Azimuth HA cluster. Instead, the API servers
for tenant clusters are exposed via Zenith.

When issues occur with cluster provisioning, here are some things to try in order to
locate the issue.

## Cluster resource exists

First, check if the cluster resource exists in the tenant namespace:

```command  title="On the K3S node, targetting the HA cluster if deployed"
$ kubectl -n az-demo get cluster
NAME   LABEL  TEMPLATE      KUBERNETES VERSION   PHASE   NODE COUNT   AGE
demo   demo   kube-1-24-2   1.24.2               Ready   4            11d
```

If no cluster resource exists, check if the Kubernetes CRDs are installed:

```command  title="On the K3S node, targetting the HA cluster if deployed"
$ kubectl get crd | grep stackhpc
clusters.azimuth.stackhpc.com                                2022-05-03T14:56:20Z
clustertemplates.azimuth.stackhpc.com                        2022-05-03T14:56:20Z
```

If they do not exist, check if the `azimuth-capi-operator` is running:

```command  title="On the K3S node, targetting the HA cluster if deployed"
$ kubectl -n azimuth get po -l app.kubernetes.io/instance=azimuth-capi-operator
NAME                                     READY   STATUS    RESTARTS   AGE
azimuth-capi-operator-5c65c4b598-h2thx   1/1     Running   0          10d
```

## Helm release exists

The first thing that the `azimuth-capi-operator` does when it sees a new cluster resource
is make a Helm release:

```command  title="On the K3S node, targetting the HA cluster if deployed"
$ helm -n az-demo list -a
NAME   NAMESPACE      REVISION        UPDATED                                 STATUS          CHART                                   APP VERSION
demo   az-demo        1               2022-07-07 13:26:22.94084961 +0000 UTC  deployed        openstack-cluster-0.1.0-dev.0.main.161  a0bcee5
```

If the Helm release does not exist, restart the `azimuth-capi-operator`:

```sh  title="On the K3S node, targetting the HA cluster if deployed"
kubectl -n azimuth rollout restart deploy/azimuth-capi-operator
```

If the Helm release does not get created, even after a restart, check the logs
of the `azimuth-capi-operator` for any warnings or errors:

```sh  title="On the K3S node, targetting the HA cluster if deployed"
kubectl -n azimuth logs deploy/azimuth-capi-operator [-f]
```

## Cluster API resource status

If the Helm release is in the `deployed` status, the next thing to check is the
state of the Cluster API resources that were created:

```command  title="On the K3S node, targetting the HA cluster if deployed"
$ kubectl -n az-demo get cluster-api
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
resources should be `Running` with an associated `NODENAME` and the
`openstackmachine.infrastructure.cluster.x-k8s.io` resources should be `ACTIVE`.

If this is not the case, first check the interactive console of the cluster nodes in Horizon
to see if the nodes had any problems joining the cluster. Also
[check to see if the Zenith service](./zenith-services.md) for the API server was created
correctly - once all control plane nodes have registered correctly the `Endpoints` resource
for the service should have three entries.

If these all look OK, check the logs of the Cluster API providers for any errors:

```sh  title="On the K3S node, targetting the HA cluster if deployed"
kubectl -n capi-system logs deploy/capi-controller-manager
kubectl -n capi-kubeadm-bootstrap-system logs deploy/capi-kubeadm-bootstrap-controller-manager
kubectl -n capi-kubeadm-control-plane-system logs deploy/capi-kubeadm-control-plane-controller-manager
kubectl -n capo-system logs deploy/capo-controller-manager
```

## Addon job status

The `openstack-cluster` Helm chart deploys a set of
[Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) that
are responsible for deploying addons to the cluster, such as CNI, CNI and device plugins,
the ingress controller and the monitoring stack.

To check if any of these have failed, run the following:

```command  title="On the K3S node, targetting the HA cluster if deployed"
$ kubectl -n az-demo get job,po -l app.kubernetes.io/name=addons
NAME                                                               COMPLETIONS   DURATION   AGE
job.batch/demo-addons-ccm-openstack-install-738c1                  1/1           2m16s      11d
job.batch/demo-addons-cloud-config-install-e48df                   1/1           2m11s      11d
job.batch/demo-addons-cni-calico-install-09420                     1/1           2m28s      11d
job.batch/demo-addons-csi-cinder-install-85612                     1/1           8m37s      11d
job.batch/demo-addons-kube-prometheus-stack-client-install-4d5ec   1/1           11m        11d
job.batch/demo-addons-kube-prometheus-stack-install-ea10d          1/1           11m        11d
job.batch/demo-addons-kubeapps-client-install-ad5be                1/1           10m        11d
job.batch/demo-addons-kubeapps-install-100bf                       1/1           9m53s      11d
job.batch/demo-addons-kubernetes-dashboard-client-install-4fdfc    1/1           7m17s      11d
job.batch/demo-addons-kubernetes-dashboard-install-c83e3           1/1           7m6s       11d
job.batch/demo-addons-loki-stack-install-d34c2                     1/1           10m        11d
job.batch/demo-addons-mellanox-network-operator-install-dece6      1/1           8m11s      11d
job.batch/demo-addons-metrics-server-install-16e4f                 1/1           7m38s      11d
job.batch/demo-addons-node-feature-discovery-install-4eb76         1/1           7m29s      11d
job.batch/demo-addons-nvidia-gpu-operator-install-8b1be            1/1           8m41s      11d
job.batch/demo-addons-prometheus-operator-crds-install-54f7c       1/1           2m36s      11d

NAME                                                                 READY   STATUS      RESTARTS   AGE
pod/demo-addons-ccm-openstack-install-738c1--1-7rg89                 0/1     Completed   0          11d
pod/demo-addons-cloud-config-install-e48df--1-66zcs                  0/1     Completed   0          11d
pod/demo-addons-cni-calico-install-09420--1-vx8s8                    0/1     Completed   0          11d
pod/demo-addons-csi-cinder-install-85612--1-jpk87                    0/1     Completed   0          11d
pod/demo-addons-kube-prometheus-stack-client-install-4d5e--1-9b27b   0/1     Completed   0          11d
pod/demo-addons-kube-prometheus-stack-install-ea10d--1-wkrmv         0/1     Completed   0          11d
pod/demo-addons-kubeapps-client-install-ad5be--1-9hr5b               0/1     Completed   0          11d
pod/demo-addons-kubeapps-install-100bf--1-lcnl4                      0/1     Completed   0          11d
pod/demo-addons-kubernetes-dashboard-client-install-4fdfc--1-x2sfj   0/1     Completed   0          11d
pod/demo-addons-kubernetes-dashboard-install-c83e3--1-xbt8w          0/1     Completed   0          11d
pod/demo-addons-loki-stack-install-d34c2--1-wdllx                    0/1     Completed   0          11d
pod/demo-addons-mellanox-network-operator-install-dece6--1-qlszg     0/1     Completed   0          11d
pod/demo-addons-metrics-server-install-16e4f--1-5wf2p                0/1     Completed   0          11d
pod/demo-addons-node-feature-discovery-install-4eb76--1-vp9sm        0/1     Completed   0          11d
pod/demo-addons-nvidia-gpu-operator-install-8b1be--1-wjxbw           0/1     Completed   0          11d
pod/demo-addons-prometheus-operator-crds-install-54f7c--1-tk4w8      0/1     Completed   0          11d
```

If any of the pods have the status `CrashLoopBackOff`, take a look at the logs to see
what is going wrong.

## Zenith service issues

Zenith services are enabled on Kubernetes clusters using the
[Zenith operator](https://github.com/stackhpc/zenith/tree/main/operator). Each tenant
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

```command  title="Targetting the tenant cluster"
$ kubectl get zenith -A
NAMESPACE              NAME                                                       PHASE       UPSTREAM SERVICE                MITM ENABLED   MITM AUTH        AGE
kubeapps               client.zenith.stackhpc.com/kubeapps                        Available   kubeapps                        true           ServiceAccount   4d19h
kubernetes-dashboard   client.zenith.stackhpc.com/kubernetes-dashboard            Available   kubernetes-dashboard            true           ServiceAccount   4d19h
monitoring-system      client.zenith.stackhpc.com/kube-prometheus-stack           Available   kube-prometheus-stack-grafana   true           Basic            4d19h

NAMESPACE              NAME                                                            SECRET                                     PHASE   FQDN                                                             AGE
kubeapps               reservation.zenith.stackhpc.com/kubeapps                        kubeapps-zenith-credential                 Ready   gdxdxjtb9zy4g0jmrpyjqjts9vhjine4umzuy63nmt23c.apps.example.org   4d19h
kubernetes-dashboard   reservation.zenith.stackhpc.com/kubernetes-dashboard            kubernetes-dashboard-zenith-credential     Ready   mwqgcdrk77nva18uzcct3g7jlo7obi7zlbcgemuhk6nhk.apps.example.org   4d19h
monitoring-system      reservation.zenith.stackhpc.com/kube-prometheus-stack           kube-prometheus-stack-zenith-credential    Ready   zovdsnnesww2hiw074mvufvcfgczfbd2yhmuhsf3p59xa.apps.example.org   4d19h


$ kubectl get deploy,po -A -l app.kubernetes.io/managed-by=zenith-operator
NAMESPACE              NAME                                                          READY   UP-TO-DATE   AVAILABLE   AGE
kubeapps               deployment.apps/kubeapps-zenith-client                        1/1     1            1           4d19h
kubernetes-dashboard   deployment.apps/kubernetes-dashboard-zenith-client            1/1     1            1           4d19h
monitoring-system      deployment.apps/kube-prometheus-stack-zenith-client           1/1     1            1           4d19h

NAMESPACE              NAME                                                               READY   STATUS                   RESTARTS   AGE
kubeapps               pod/kubeapps-zenith-client-85c8c7ffb-fx5b4                         2/2     Running                  0          4d19h
kubernetes-dashboard   pod/kubernetes-dashboard-zenith-client-86c5fd9bd-2jfdb             2/2     Running                  0          4d19h
monitoring-system      pod/kube-prometheus-stack-zenith-client-b9986579d-qgp82            2/2     Running                  0          9h
```

!!! tip

    The kubeconfig for a tenant cluster is available in a secret in the tenant namespace:

    ```command  title="On the K3S node, targetting the HA cluster if deployed"
    $ kubectl -n az-demo get secret | grep kubeconfig
    demo-kubeconfig                                   cluster.x-k8s.io/secret               1      11d
    ```

If everything looks OK, try restarting the Zenith operator for the cluster:

```command  title="On the K3S node, targetting the HA cluster if deployed"
$ kubectl -n az-demo rollout restart deploy/demo-zenith-operator
```
