# Standalone Azimuth mode

<!-- prettier-ignore-start -->
!!! warning

This mode is still experimental and in early development!

<!-- prettier-ignore-end -->

- Standalone mode is an environment/set of features designed to allow Azimuth to run WITHOUT Openstack on any Kubernetes cluster.
- It is currently in alpha, so some features may not work as intended.

- Previously, Azimuth authentication has been delegated to OpenStack Keystone. Azimuth now supports using OIDC group membership to authorise access to Azimuth tenancies. Each tenancy now has the required credentials for the configured Azimuth cloud provider.
- Azimuth defaults to using an OpenStack cloud provider, for the Standalone mode, we configure the null cloud provider via the environment config. Currently, the chosen cloud provider is a global Azimuth settings across all tenancies.
- For more details on OIDC authentication, and what happens when OpenStack cloud provider is used with OIDC auth see [these docs](https://github.com/azimuth-cloud/azimuth-config/pull/188/files)
- All Azimuth platforms, when using the null cloud provider and OIDC auth, are currently provided by the [new apps operator](https://github.com/azimuth-cloud/azimuth-apps-operator), which uses fluxCD resources to deploy apps on a remote K8s cluster, using the kubeconfig within the Azimuth tenancy k8s namespace.

## Install

### Assumptions/Warnings

- The host VM targeted by the playbook is Ubuntu 22.04-24.04 or similar.
- Existing ingress controllers such as `traefik` may conflict with the `nginx` ingress controller instaled by Azimuth.
- CaaS apps will not work as they currently rely on injecting OpenStack application credentials, however this could be reworked in the future.
<!--
CaaS apps create clusters using ansible and terraform, although the operator currently depends on injecting an OpenStack application credential. The Azimuth driver and operator need some re-work to support passing K8s credentials into ansible.
-->
- Community images and CAPI clusters will not work as they rely on Openstack API calls.
- OIDC relies on Crossplane, which currently does not work with Valero.

### Deployment

#### Development

- For quick and easy Azimuth deployment, a playbook has been created to setup a fresh Ubuntu VM to run Azimuth.

- By default, it sets up a new k3s cluster,
- Sets some system values,
- Installs fresh command-line tools,
- Sets up the kubeconfig,
- And deploys azimuth.

- The VM needs to be Ubuntu 24.04 or similar, with at least 2 VCPUs, 8GB of ram and 30GB of disk space (with monitoring disabled, if monitoring is enabled then at least 50GB of disk space is reccomended)

- If you are running the playbook against an existing VM with some tools preinstalled/ an existing k3s cluster/ etc then these steps can be disabled in `environments/existing-k8s/inventory/group_vars/all/variables.yml`

```bash
# Clone the azimuth-config repository
git clone https://github.com/azimuth-cloud/azimuth-config
cd azimuth-config

# Setup the hosts file to point at your VM
vim environments/existing-k8s/inventory/hosts

# Set up the virtual environment
./bin/ensure-venv

# Activate the demo environment
source ./bin/activate existing-k8s

# Install Ansible dependencies
ansible-galaxy install -f -r requirements.yml

# Generate deployment secrets
# N.B. these are excluded from git using .gitignore
./bin/generate-secrets

# Run playbook to setup your VM amd Deploy Azimuth
ansible-playbook azimuth_cloud.azimuth_ops.setup_existing_k3s
```

#### Into an existing cluster

##### Dependencies

On the machine running the playbook:

- k9s
- Kubectl
- Helm
- Kustomize
- Flux
  (you can run the setup_k3s playbook with all options other than install_cli_tools disabled to do this setup for you)

- admin kubeconfig for the cluster in the default `~/.kube/config` file.
- An OpenSSH server running setup to allow you to SSH in to localhost.

On the Kubernetes cluster:

- Nginx ingress controller.
- A spare floating IP for Zenith.

```bash
# Clone the azimuth-config repository
git clone https://github.com/azimuth-cloud/azimuth-config
cd azimuth-config

# If the IP of the cluster is not the IP of the host VM, replace the automatic assignment of 'infra_external_ip' with the external IP of your cluster
vim environments/existing-k8s/inventory/group_vars/all/variables.yml

# Set up the virtual environment
./bin/ensure-venv

# Activate the demo environment
source ./bin/activate existing-k8s

# Install Ansible dependencies
ansible-galaxy install -f -r requirements.yml

# Generate deployment secrets
# N.B. these are excluded from git using .gitignore
./bin/generate-secrets

# Run playbook to setup your VM amd Deploy Azimuth
ansible-playbook azimuth_cloud.azimuth_ops.deploy
```

### Azimuth setup

#### Tenancy creation

- Azimuth requires `tenancies` to be setup to create groups of users who can access external Kubernetes clusters assigned to each tenancy.
- Your tenancy can be managed using continuous deployment through `FluxCD`, which will read Kustomizations in a repository and apply their manifests to the cluster.
- [Azimth tenant config](https://github.com/azimuth-cloud/azimuth-tenant-config/) is a template for tenancies, [fork it](https://github.com/azimuth-cloud/azimuth-tenant-config/?tab=readme-ov-file#forkcopy-this-repository) so you have your own copy for Flux to reference.
- You can then push tenancies or app templates to the repository, and Flux will automatically make them available inside your Azimuth deployment.
- The repository also includes a setup script that automates setting up a new tenancy, pushes the files to your repository and then creates resources for Flux to track that repository.

```bash
#clone the tennancy config repository on a machine that has a kubeconfig for the cluster
git clone https://github.com/<you>/<your-tennant-config>
cd <your-tennant-config>

# Run the setup script (for a more detailed explanation of what the script is doing see the tennancy repository readme)
python3 bin/bootstrap.py --type kubeconfig \
--cred-file path/to/tennant/kubeconfig.yml \
--name script-tennant \
--azimuth-kubeconfig path/to/<admin kubeconfig for the cluster>.yml \
--git-remote-url <URL for your flux repo> \
--oidc-admin-username tenancy-admin \
--oidc-admin-email <your-email-on-OIDC-service>
```

#### OIDC setup

OIDC authentication can be used for user accounts on Azimuth, but it requires some setup.

- Go to the admin Keycloak console at `http://identity.apps.<your_ip>.sslip.io/admin/master/console/`
- Login with the username "admin" and the password in `.../existing_k8s/inventory/group_vars/all/secrets.yml`
- Switch to the realm `azimuth-users`
- Navigate to `Identity Providers` in the sidebar.
- Setup your Identity Provider of choice (example instructions for a tested provider below).

##### GitHub

- Select GitHub from the list of options.
- On another page, go to your GitHub account and open `settings -> developer settings -> OAuth apps`
- Create a new OAuth app.
- Set the homepage URL to `http://identity.apps.<your-azimuth-ip>.sslip.io`
- Set the callback URL to `http://identity.apps.<your-azimuth-ip>.sslip.io/realms/azimuth-users/broker/github/endpoint`
- Create the app.
- Copy the `Client ID` field over to the setup page on Keycloak.
- Generate a new client secret on GitHub, and copy it over.
- Generate the new Identity provider on Keycloak.

- Once an OIDC provider has been setup, users can go to user login page at `http://identity.apps.<your-azimuth-ip>.sslip.io/` and select it as a login option.

### Notes

- This setup may work in HA mode but has not been tested.
- [sslip.io](https://sslip.io) is used to provide DNS. This avoids the need for a DNS entry to be provisioned in advance.
- TLS is disabled for [ingress](https://azimuth-config.readthedocs.io/en/stable/configuration/06-ingress/), allowing the Azimuth to work even when the deployment is not reachable from the internet (_outbound_ internet connectivity is still required).
