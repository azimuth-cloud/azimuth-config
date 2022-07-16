# Deploying Azimuth

## Activating an environment

Before you can make a deployment, you must first activate an environment:

```sh
source ./bin/activate production
```

This script must be `source`d rather than just executed as it exports environment variables into
the current shell that are used to configure the deployment.

## Deploying Azimuth

Once you are happy with any configuration changes and an environment has been activated,
run the following commands to deploy Azimuth:

```sh
# Install or update requirements
ansible-galaxy install -f -r ./requirements.yml
# Run the provision playbook from the azimuth-ops collection
# The inventory is picked up from the ansible.cfg file in the active environment
ansible-playbook stackhpc.azimuth_ops.provision
```

## Accessing a seed node / single-node cluster

Seed nodes / single-node clusters are deployed using Terraform and the IP address and SSH key
for accessing the node are in the Terraform state for the environment.

This repository contains a utility script - [seed-ssh](./bin/seed-ssh) - that will extract
these details from the Terraform state for the active environment and use them to execute an
SSH command to access the provisioned node.

Once on the node, you can use `kubectl` to inspect the state of the Kubernetes cluster. It
is already configured with the correct kubeconfig file.

## Accessing a HA cluster

HA clusters are provisioned using Cluster API on the seed node. The Kubernetes API of the
a HA cluster is not accessible to the internet, so access is via the seed node.

Once on the seed node, a kubeconfig file for the HA cluster will be available in the `$HOME`
directory of the `ubuntu` user. You can activate this kubeconfig by setting the `KUBECONFIG`
environment variable, which allows you to access the HA cluster using `kubectl`:

```
$ source ./bin/activate production
$ ./bin/seed-ssh
ubuntu@azimuth-production-seed:~$ export KUBECONFIG=./kubeconfig-azimuth-production.yaml
ubuntu@azimuth-production-seed:~$ kubectl get po -n azimuth
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