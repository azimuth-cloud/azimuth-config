# Kubernetes only mode

<!-- prettier-ignore-start -->
!!! warning
    This mode is still experimental and in early development!
<!-- prettier-ignore-end -->

- Kubernetes only is an environment/set of features designed to allow azimuth to run WITHOUT openstack on any Kubernetes cluster.
- It is currently in alpha, so some features may not work as intended.
- While Azimuth itself can run without Openstack, it depends on the Openstack API to create most of its platforms so this version can only deploy a limited subset of Azimuth apps.

## Install

### Assumptions/Warnings

- The Kubernetes cluster being targeted is a single node k3s cluster.
- HA mode is not required.
- The host VM targeted by the playbook is Ubuntu 22.04-24.04 or similar.
- `k3s.yaml` has read permissions set properly so other tools can access it - `sudo chmod 744 /etc/rancher/k3s/k3s.yaml`
- existing ingress controllers like `traefik` may conflict with the `nginx` ingress controller setup here.
- CaaS apps will not work as they rely on Openstack API calls.
- Community images will not work as they rely on Openstack API calls.

### Deployment

``` bash 
# Clone the azimuth-config repository
git clone https://github.com/azimuth-cloud/azimuth-config
cd azimuth-config

# Setup the hosts file to point at your VM
vim environments/existing-k8s/inventory/hosts

# If the IP of the cluster is not the IP of the host VM, replace the automatic assignment of 'infra_external_ip' with your IP of the cluster (or override it when running the playbook)
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

# Deploy Azimuth
ansible-playbook azimuth_cloud.azimuth_ops.setup_existing_k3s
```

### Azimuth setup

#### Tenancy creation

- azimuth requires `tenancies` to be setup to create groups of users who can access/own resources.
- your tenancy can be managed using CD through `flux`, which will read a repository and then apply the config files there to the cluster.
- you can then push tenancies or app templates to the repository, and flux will automatically make them available inside your azimuth deployment
- the repository also includes a setup script that automates setting up a new tenancy, pushes the files to your repository and then enables flux to track that repository

``` bash 
#clone the tennancy config repository on a machine that has a kubeconfig for the cluster
git clone  https://github.com/azimuth-cloud/azimuth-tenant-config
cd azimuth-tenant-config

# Run the setup script (for a more detailed explanation of what the script is doing see the tennancy repository readme)
python3 bin/bootstrap.py --type kubeconfig \
--cred-file path/to/your-kubeconfig.yml \
--name script-tennant \
--azimuth-kubeconfig /etc/rancher/k3s/k3s.yaml \
--git-remote-url <URL for your flux repo> \
--oidc-admin-username tenancy-admin \
--oidc-admin-email <your-email-on-OIDC-service>

```

#### OIDC setup

OIDC has now been setup on Azimuth, but it needs to be linked with the external provider before it can work.

- go to the admin keycloak console at `http://identity.apps.<your_ip>.sslip.io/admin/master/console/` 
- Login with the username "admin" and the password in `.../existing_k8s/inventory/group_vars/all/secrets.yml`
- switch to the realm `azimuth-users`
- go down to `identity providers`

##### with GitHub

- select GitHub from the list of options
- on another page, go to your GitHub account and open `settings -> developer settings -> OAuth apps`
- create a new OAuth app
- set the homepage URL to `http://identity.apps.<your-azimuth-ip>.sslip.io`
- set the callback URL to `http://identity.apps.<your-azimuth-ip>.sslip.io/realms/azimuth-users/broker/github/endpoint`
- create the app
- Copy the `Client ID` field over to the setup page on Keycloak
- Generate a new client secret on GitHub, and copy it over
- generate the new Identity provider on Keycloak

- once an OIDC provider has been setup, users can go to user login page at `http://identity.apps.<your-azimuth-ip>.sslip.io/` and select it as a login option

### Notes

- This setup may work in HA mode but has not been tested
- This setup will not work with other kubernetes distros as the kubeconfig path will be wrong, but could be adapted.

- [sslip.io](https://sslip.io) is used to provide DNS. This avoids the need for a DNS entry to be provisioned in advance.
- TLS is disabled for [ingress](https://azimuth-config.readthedocs.io/en/stable/configuration/06-ingress/), allowing the Azimuth to work even when the deployment is not reachable from the internet (_outbound_ internet connectivity is still required). CHECK THIS??)
- The deployment secrets are **not secret**, as they are stored in plain text in the `azimuth-config` repository on GitHub. (CHECK THIS??)
