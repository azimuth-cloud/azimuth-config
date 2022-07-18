# Accessing the HA cluster

HA clusters are provisioned using Cluster API on the K3S node. The Kubernetes API of the
HA cluster is not accessible to the internet, so the K3S node is used to access it.

On the K3S node, a kubeconfig file for the HA cluster is created in the `$HOME` directory
of the `ubuntu` user. You can activate this kubeconfig by setting the `KUBECONFIG` environment
variable, which allows you to access the HA cluster using `kubectl`:

```
$ ./bin/seed-ssh
ubuntu@azimuth-staging-seed:~$ export KUBECONFIG=./kubeconfig-azimuth-staging.yaml
ubuntu@azimuth-staging-seed:~$ kubectl get po -n azimuth
NAME                                               READY   STATUS    RESTARTS      AGE
awx-operator-controller-manager-7b4d9ffddd-k7bsq   2/2     Running   0             55m
awx-d864c46f8-bx6db                                4/4     Running   0             51m
awx-postgres-0                                     1/1     Running   0             52m
azimuth-api-6847fcd6c8-746pc                       1/1     Running   0             55m
azimuth-capi-operator-789b5c8f44-2g4wx             1/1     Running   0             55m
azimuth-ui-fc556-cjwq2                             1/1     Running   0             55m
consul-8zbnx                                       1/1     Running   0             55m
consul-kf8fl                                       1/1     Running   0             55m
consul-n4w2x                                       1/1     Running   0             55m
consul-server-0                                    1/1     Running   0             55m
consul-server-1                                    1/1     Running   0             55m
consul-server-2                                    1/1     Running   0             55m
zenith-registrar-86df769979-z2cgb                  1/1     Running   0             55m
zenith-sshd-768794b88b-48rcf                       1/1     Running   0             55m
zenith-sync-8f55f978c-v6czg                        1/1     Running   0             55m
```
