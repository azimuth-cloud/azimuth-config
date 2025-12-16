# Accessing the HA cluster

HA clusters are provisioned using Cluster API on the K3s node. The Kubernetes API of the
HA cluster is not accessible to the internet, so the K3s node is used to access it.

On the K3s node, a kubeconfig file for the HA cluster is created in the `$HOME` directory
of the `ubuntu` user. You can activate this kubeconfig by setting the `KUBECONFIG` environment
variable, which allows you to access the HA cluster using `kubectl`:

```text
$ ./bin/seed-ssh
ubuntu@azimuth-staging-seed:~$ export KUBECONFIG=./kubeconfig-azimuth-staging.yaml
ubuntu@azimuth-staging-seed:~$ kubectl get po -n azimuth
NAME                                                          READY   STATUS    RESTARTS   AGE
azimuth-api-6847fcd6c8-746pc                                  1/1     Running   0          55m
azimuth-caas-operator-ara-79bcd7c5dd-k6zf5                    1/1     Running   0          55m
azimuth-caas-operator-7d55dddb5b-pm69d                        1/1     Running   0          55m
azimuth-capi-operator-metrics-57bbdfd8f4-9rqx4                1/1     Running   0          55m
azimuth-capi-operator-reloader-78f879c866-k4r5w               1/1     Running   0          55m
azimuth-capi-operator-789b5c8f44-2g4wx                        1/1     Running   0          55m
azimuth-identity-operator-778c87548b-dkcpn                    1/1     Running   0          55m
azimuth-ui-fc556-cjwq2                                        1/1     Running   0          55m
zenith-registrar-86df769979-z2cgb                             1/1     Running   0          55m
zenith-sshd-768794b88b-48rcf                                  1/1     Running   0          55m
zenith-sync-8f55f978c-v6czg                                   1/1     Running   0          55m
```
