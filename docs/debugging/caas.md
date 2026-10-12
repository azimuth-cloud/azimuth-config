# Debugging Cluster-as-a-Service

As described in [configuring CaaS](../configuration/12-caas.md), Azimuth uses
the [Azimuth CaaS operator](https://github.com/azimuth-cloud/azimuth-caas-operator) to
manage clusters.

The Azimuth API creates a namespace for each project in which instances of the
CaaS CRDs are created in order to create tenant clusters. These namespaces are
of the form `caas-<sanitized project id>`.

When issues occur with cluster provisioning, here are some things to try in order to
locate the issue.

## CRDs installed and operator running

First, check that the CaaS CRDs have been registered:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl get crd | grep caas
clusters.caas.azimuth.stackhpc.com                           2023-07-03T13:33:28Z
clustertypes.caas.azimuth.stackhpc.com                       2023-07-03T13:33:28Z
```

If they do not exist, check if the `azimuth-caas-operator` is running:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n azimuth get po -l app.kubernetes.io/instance=azimuth-caas-operator
NAME                                         READY   STATUS    RESTARTS   AGE
azimuth-caas-operator-ara-79bcd7c5dd-k6zf5   1/1     Running   0          18m
azimuth-caas-operator-7d55dddb5b-pm69d       1/1     Running   0          18m
```

## Cluster resource exists

Next, check if the cluster resource exists in the tenant namespace:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n caas-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx get cluster.caas
NAME          AGE
demo-ws      7m45s
demo-slurm   7m26s
```

Check the status of the cluster you want to debug:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n caas-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx describe cluster.caas demo-ws
Name:         demo-ws
Namespace:    caas-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
...
```

## Check if jobs were scheduled

The Azimuth CaaS operator schedules Kubernetes jobs that use
[ansible-runner](https://ansible.readthedocs.io/projects/runner/en/stable/) to
execute the required Ansible. If the operator is functioning properly, you should
see these jobs being created:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n caas-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx get job
NAME                      COMPLETIONS   DURATION   AGE
demo-slurm-create-pwqmh   0/1           14m        14m
demo-ws-create-9nx96      1/1           4m36s      14m
```

If the jobs are not being scheduled, check the logs of the CaaS operator to see
what is stopping them from being created:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n azimuth logs deploy/azimuth-caas-operator [-f]
```

If you need to restart the operator, you can use the following command:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n azimuth rollout restart deploy/azimuth-caas-operator
```

If the jobs are being scheduled, you can also check the pods that are created
to see if there are issues:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n caas-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx get po
NAME                            READY   STATUS      RESTARTS   AGE
demo-ws-create-9nx96-m2l97      0/1     Completed   0          21m
demo-slurm-create-pwqmh-jsbmk   0/1     Completed   0          20m
```

If any of the pods are getting stuck in the init phase, check the logs of the
init containers to see if there are issues checking out the appliance code or
installing the Ansible dependencies:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n caas-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx logs demo-ws-create-9nx96-m2l97 [-c [inventory|clone]]
```

## Check Ansible output

Azimuth includes a deployment of
[ARA Records Ansible (ARA)](https://ara.recordsansible.org/) that is used to record
Ansible playbook executions as they are run by the CaaS operator. If the job is getting
as far as starting to run Ansible, then ARA is a much easier way to debug the Ansible
for an appliance than wading through the Ansible logs from the job.

As discussed in [Monitoring and alerting](../configuration/14-monitoring.md), the ARA
web interface is exposed as `ara.<ingress base domain>`, e.g. `ara.azimuth.example.org`,
and is protected by a username and password.

Once inside, you can look at the details of the recently executed jobs, see which
tasks failed and what variables were set at the time.
