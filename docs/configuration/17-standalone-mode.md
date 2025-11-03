# Standalone Azimuth mode

<!-- prettier-ignore-start -->
!!! warning "Technology Preview"
    Standalone Azimuth mode is still experimental and in early development!
<!-- prettier-ignore-end -->

- Standalone mode is an environment/set of features designed to allow Azimuth to run WITHOUT Openstack on any Kubernetes cluster.
- It is currently in alpha, so some features may not work as intended.

- Previously, Azimuth authentication has been delegated to OpenStack Keystone. Azimuth now supports using OIDC group membership to authorise access to Azimuth tenancies. Each tenancy now has the required credentials for the configured Azimuth cloud provider.
- Azimuth defaults to using an OpenStack cloud provider, for the Standalone mode, we configure the null cloud provider via the environment config. Currently, the chosen cloud provider is a global Azimuth settings across all tenancies.
- For more details on OIDC authentication, see [identity docs](https://github.com/azimuth-cloud/azimuth-config/pull/188/files)
- All Azimuth platforms, when using the null cloud provider and OIDC auth, are currently provided by the [apps operator](https://github.com/azimuth-cloud/azimuth-apps-operator), which uses FluxCD resources to deploy apps on a remote K8s cluster, using the kubeconfig provided for the tenancy.

## Assumptions/Warnings

- The host VM targeted by the playbook is Ubuntu 22.04-24.04 or similar.
- Existing ingress controllers such as Traefik may conflict with the Nginx ingress controller installed by Azimuth.
- CaaS apps will not work as they currently rely on injecting OpenStack application credentials, however this could be reworked in the future.
<!--
CaaS apps create clusters using ansible and terraform, although the operator currently depends on injecting an OpenStack application credential. The Azimuth driver and operator need some re-work to support passing K8s credentials into ansible.
-->
- Community images and CAPI clusters will not work as they rely on Openstack API calls.
- OIDC relies on Crossplane, which currently does not work with Velero.

## Deployment

### Development/VM

- For quick and easy Azimuth deployment, a playbook has been created to setup a fresh Ubuntu VM to run Azimuth.

By default, the playbook will:

1. Setup system inotify limits limits and trust bundles
2. Install k3s
3. Install required command-line tools (kubectl, Helm, Flux, Kustomize, K9s)
4. Move the k3s kubeconfig to ~/.kube/config, and set file permissions
5. Deploy the ingress controller (and optionally the monitoring stack)
6. Deploy Azimuth

- All of these steps can be disabled if needed, for example If you are running the playbook against an existing VM with some tools preinstalled or are targeting an existing Kubernetes cluster from your local machine.
- Steps can be disabled in `environments/existing-k8s/inventory/group_vars/all/variables.yml` by setting the appropriate variable to false.

- The VM needs to be Ubuntu 24.04 or similar, with at least 2 VCPUs, 8GB of ram and 30GB of disk space (with monitoring disabled, if monitoring is enabled then at least 50GB of disk space is reccomended)
- Ports 6443, 443, 80, 22 and 2222 should be open.

```bash
# Clone the azimuth-config repository
git clone https://github.com/azimuth-cloud/azimuth-config
cd azimuth-config

# Setup the hosts file to point at your VM
vim environments/standalone/inventory/hosts

# Set up the virtual environment
./bin/ensure-venv

# Activate the demo environment
source ./bin/activate standalone

# Install Ansible dependencies
ansible-galaxy install -f -r requirements.yml

# Generate deployment secrets
# N.B. these are excluded from git using .gitignore
./bin/generate-secrets

# Run playbook to setup your VM amd Deploy Azimuth
ansible-playbook azimuth_cloud.azimuth_ops.deploy_standalone
```

### Into an existing cluster

#### Dependencies

##### Required tools on the host machine

- python3
- pip
- Kubectl
- Helm
- Kustomize
- Flux

- An admin kubeconfig for the cluster in the default `~/.kube/config` location. Alternatively, you can set `kubeconfig_path: "path/to/your/kubeconfig"` in the environment's variables file (or supply it as an extra var when running the playbook)

##### On the Kubernetes cluster

- Nginx ingress controller.
- The cluster needs to support load balancer service types. (e.g. [Service LB](https://docs.k3s.io/networking/networking-services#service-load-balancer) on k3s by default)

### Install

```bash
# Clone the azimuth-config repository
git clone https://github.com/azimuth-cloud/azimuth-config
cd azimuth-config

# If the IP of the cluster is not the IP of the host VM, replace the automatic assignment of 'infra_external_ip' with the external IP of your cluster
vim environments/standalone/inventory/group_vars/all/variables.yml

# Set up the virtual environment
./bin/ensure-venv

# Activate the demo environment
source ./bin/activate standalone

# Install Ansible dependencies
ansible-galaxy install -f -r requirements.yml

# Generate deployment secrets
# N.B. these are excluded from git using .gitignore
./bin/generate-secrets

# Run playbook to setup your VM amd Deploy Azimuth
ansible-playbook azimuth_cloud.azimuth_ops.deploy
```

## Azimuth setup

### OIDC setup

OIDC authentication can be used for user accounts on Azimuth, but it requires some setup.

- Go to the admin Keycloak console at `http://identity.apps.<your_ip>.sslip.io/admin/master/console/`
- Login with the username "admin" and the password in `../existing_k8s/inventory/group_vars/all/secrets.yml`
- Switch to the realm `azimuth-users`
- Navigate to `Identity Providers` in the sidebar.
- Setup your Identity Provider of choice (example instructions for a tested provider below).

#### GitHub

- Select GitHub from the list of options.
- On another page, go to your GitHub account and open `Settings -> Developer Settings -> OAuth apps`
- Create a new OAuth app.
- Set the homepage URL to `http://identity.apps.<your-azimuth-ip>.sslip.io`
- Set the callback URL to `http://identity.apps.<your-azimuth-ip>.sslip.io/realms/azimuth-users/broker/github/endpoint`
- Create the app.
- Copy the `Client ID` field over to the setup page on Keycloak.
- Generate a new client secret on GitHub, and copy it over.
- Generate the new Identity provider on Keycloak.
- Once the provider has been created, click on it to open the `Provider details` page
- Scroll down to `First login flow override`, and set it to `map-users-flow` (this maps users GitHub emails to their account emails)

- Once an OIDC provider has been setup, users can go to user login page at `http://identity.apps.<your-azimuth-ip>.sslip.io/` and select it as a login option.

### Tenancy creation

- Azimuth requires `tenancies` to be setup to create groups of users who can access external Kubernetes clusters assigned to each tenancy.
- Your tenancies can be managed using continuous deployment through `FluxCD`, which will read Kustomizations in a repository and apply their manifests to the cluster.
- Follow this [setup script](https://github.com/azimuth-cloud/azimuth-tenant-config/blob/feat/crossplane-support/docs/standalone-quickstart.md) to setup a tenancy for your Azimuth.

## Notes

- [sslip.io](https://sslip.io) is used to provide DNS. This avoids the need for a DNS entry to be provisioned in advance.
- TLS is disabled for [ingress](https://azimuth-config.readthedocs.io/en/stable/configuration/06-ingress/), allowing the Azimuth to work even when the deployment is not reachable from the internet (_outbound_ internet connectivity is still required).
- Standalone environment is currently based on the Azimuth demo environment, so the deployment secrets are **not secret**, as they are stored in plain text in the `azimuth-config` repository on GitHub.
