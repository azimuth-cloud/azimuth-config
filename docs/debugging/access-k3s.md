# Accessing the K3s cluster

Both the single node and high-availability (HA) deployment methods have a K3s node that
is provisioned using Terraform. In the single node case, this is the cluster that actually
hosts Azimuth and all its dependencies. In the HA case, this cluster is configured as a
Cluster API management cluster for the HA cluster that actually runs Azimuth.

In both cases, the K3s node is deployed using Terraform and the IP address and SSH key
for accessing the node are in the Terraform state for the environment. The `azimuth-config`
repository contains a utility script - 
[seed-ssh](https://github.com/azimuth-cloud/azimuth-config/tree/stable/bin/seed-ssh) - that will
extract these details from the Terraform state for the active environment and use them to
execute an SSH command to access the provisioned node.

!!! warning  "Accessing an environment deployed using automation"

    If you are using `seed-ssh` to access an environment that is deployed using
    [automation](../deployment/automation.md), you still need to make sure that the
    Python and Ansible dependencies are installed in order for the script to work:

    ```sh
    # Ensure that the Python venv is set up
    ./bin/ensure-venv

    # Activate the target environment
    source ./bin/activate my-site

    # Install Ansible dependencies
    ansible-galaxy install -f -r requirements.yml

    # Execute the seed-ssh script
    ./bin/seed-ssh
    ```


Once on the node, you can use `kubectl` to inspect the state of the Kubernetes cluster. It
is already configured with the correct kubeconfig file:

```console
$ ./bin/seed-ssh
ubuntu@azimuth-staging-seed:~$ kubectl get po -A
NAMESPACE                           NAME                                                              READY   STATUS      RESTARTS       AGE
kube-system                         coredns-7796b77cd4-mk9gw                                          1/1     Running     0              2d
kube-system                         metrics-server-ff9dbcb6c-nbpjt                                    1/1     Running     0              2d
cert-manager                        cert-manager-webhook-5fd7d458f7-scwd8                             1/1     Running     0              2d
kube-system                         local-path-provisioner-84bb864455-r4vd2                           1/1     Running     0              2d
cert-manager                        cert-manager-66b6d6bf59-vzqrq                                     1/1     Running     0              2d
capi-system                         capi-controller-manager-7f45d4b75b-47cf4                          1/1     Running     0              2d
capi-kubeadm-control-plane-system   capi-kubeadm-control-plane-controller-manager-5f5d7fb49-684n9     1/1     Running     0              2d
cert-manager                        cert-manager-cainjector-856d4df858-bgs4d                          1/1     Running     0              2d
capo-system                         capo-controller-manager-5c9748574f-vnbzp                          1/1     Running     0              2d
capi-kubeadm-bootstrap-system       capi-kubeadm-bootstrap-controller-manager-c444455b5-zn4qw         1/1     Running     0              2d
default                             azimuth-staging-addons-cloud-config-install-9eeff--1-694x4        0/1     Completed   0              2d
default                             azimuth-staging-addons-cni-calico-install-0d58f--1-cjwzx          0/1     Completed   0              2d
default                             azimuth-staging-addons-ccm-openstack-install-bc2b0--1-jlb4b       0/1     Completed   0              2d
default                             azimuth-staging-addons-prometheus-operator-crds-instal--1-sn66s   0/1     Completed   0              2d
default                             azimuth-staging-addons-metrics-server-install-45390--1-rr5m6      0/1     Completed   0              2d
default                             azimuth-staging-addons-csi-cinder-install-53888--1-cg9gq          0/1     Completed   0              2d
default                             azimuth-staging-addons-ingress-nginx-install-478f3--1-p4hwb       0/1     Completed   0              2d
default                             azimuth-staging-addons-loki-stack-install-c8cd1--1-5z2wc          0/1     Completed   0              2d
default                             azimuth-staging-addons-kube-prometheus-stack-install-4--1-xgmvd   0/1     Completed   0              2d
default                             azimuth-staging-autoscaler-66cc55487c-qfpgn                       1/1     Running     0              2d
```
