# Standalone Azimuth mode

<!-- prettier-ignore-start -->
!!! warning "Technology Preview"
    Standalone Azimuth mode is still experimental and in early development!
<!-- prettier-ignore-end -->

Standalone mode runs Azimuth without OpenStack and lets users deploy apps onto existing Kubernetes clusters configured for their tenancies.
It uses OIDC group membership to control access to tenancies and the null cloud provider to disable cloud resource management.

The [apps operator](https://github.com/azimuth-cloud/azimuth-apps-operator) deploys apps using FluxCD and the kubeconfig configured for each tenancy.
The cloud provider is configured globally and applies to all tenancies.

For more details on OIDC authentication, see the [identity architecture documentation](../architecture/identity.md#using-a-keycloak-realm).

## Assumptions/Warnings

- The host VM targeted by the playbook is Ubuntu 22.04-24.04 or similar.
- Existing ingress controllers such as Traefik may conflict with the Nginx ingress controller installed by Azimuth.
- Standalone mode does not provision OpenStack VMs or CaaS clusters. It also cannot create Kubernetes clusters through Cluster API (CAPI). Community images are unavailable.
- Automatic expiry through [Azimuth scheduling](18-scheduling.md) is not supported for apps managed by the apps operator.
- OIDC relies on Crossplane, which currently does not work with Velero.

## Deployment

### Development/VM

The standalone playbook prepares an existing Ubuntu VM and installs k3s to host Azimuth.

By default, the playbook will:

1. Set up system inotify limits and trust bundles
2. Install k3s
3. Install required command-line tools (kubectl, Helm, Flux, Kustomize, K9s)
4. Move the k3s kubeconfig to ~/.kube/config, and set file permissions
5. Deploy the ingress controller (and optionally the monitoring stack)
6. Deploy Azimuth

- All of these steps can be disabled if needed, for example If you are running the playbook against an existing VM with some tools preinstalled or are targeting an existing Kubernetes cluster from your local machine.
- Steps can be disabled in `environments/standalone/inventory/group_vars/all/variables.yml` by setting the appropriate variable to false.

- The VM needs to be Ubuntu 24.04 or similar, with at least 2 VCPUs, 8GB of ram and 30GB of disk space (with monitoring disabled, if monitoring is enabled then at least 50GB of disk space is recommended)
- Ports 6443, 443, 80, 22 and 2222 should be open.

```bash
# Clone the azimuth-config repository
git clone https://github.com/azimuth-cloud/azimuth-config
cd azimuth-config

# Setup the hosts file to point at your VM
vim environments/standalone/inventory/hosts

# Set up the virtual environment
./bin/ensure-venv

# Activate the standalone environment
source ./bin/activate standalone

# Install Ansible dependencies
ansible-galaxy install -f -r requirements.yml

# Generate deployment secrets
# N.B. these are excluded from git using .gitignore
./bin/generate-secrets

# Run playbook to setup your VM and deploy Azimuth
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

# Activate the standalone environment
source ./bin/activate standalone

# Install Ansible dependencies
ansible-galaxy install -f -r requirements.yml

# Generate deployment secrets
# N.B. these are excluded from git using .gitignore
./bin/generate-secrets

# Deploy Azimuth to the existing Kubernetes cluster
ansible-playbook azimuth_cloud.azimuth_ops.deploy
```

## Azimuth setup

### OIDC setup

OIDC authentication can be used for user accounts on Azimuth, but it requires some setup.

- Go to the admin Keycloak console at `http://identity.apps.<your_ip>.sslip.io/admin/master/console/`
- Login with the username `admin` and the `keycloak_admin_password` value in `environments/standalone/inventory/group_vars/all/secrets.yml`.
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
- To create a tenancy, follow the [experimental tenancy quickstart](https://github.com/azimuth-cloud/azimuth-tenant-config/blob/6f73c86baaa0863aa66d35b2e4e5b7e418dfeda7/docs/standalone-quickstart.md).
  It requires the `feat/crossplane-support` branch of `azimuth-tenant-config`, which has not yet been merged into `main`.
  In its `create-admin.py` example, use `--oidc-admin-email` for the federated authentication email.

## Notes

- [sslip.io](https://sslip.io) is used to provide DNS. This avoids the need for a DNS entry to be provisioned in advance.
- TLS is disabled for [ingress](https://azimuth-config.readthedocs.io/en/stable/configuration/06-ingress/), allowing the Azimuth to work even when the deployment is not reachable from the internet (_outbound_ internet connectivity is still required).
- When the standalone environment is active, `./bin/generate-secrets` writes deployment secrets in plain text to `environments/standalone/inventory/group_vars/all/secrets.yml`. Git ignores this file by default because it is listed in `.gitignore`.
