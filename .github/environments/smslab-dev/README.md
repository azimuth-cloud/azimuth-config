# SMSLab Dev Environment

This environment is intended to be a simple dev environment, mainly for use
with Tilt.

It runs solely on the `stackhpc-ipv4-geneve` network, and can be deployed within
a personal project.

## Prerequisites

1. A personal project on SMSLab
2. An application credential issued from your personal project
3. [sshuttle](https://github.com/sshuttle/sshuttle) exposing the `stackhpc-ipv4-geneve`
   network to your local machine in a background terminal:
   ```bash
   sshuttle -r bastion.compute.sms-lab.cloud 172.16.0.0/23
   ```

## Azimuth docs

Follow the Developing Azimuth [docs](https://azimuth-config.readthedocs.io/en/stable/developing/),
with the following specific substitutions

### Creating a dev environment

```bash
# Activating an environment with a unique instance name
source ./bin/activate smslab-dev jbloggs-dev
```

### Using the dev environment

```bash
# Set OpenStack configuration variables
export OS_CLOUD=openstack
export OS_CLIENT_CONFIG_FILE=/path/to/clouds.yaml

# Activate the dev config environment with a specific instance name
#
# This means that resources created for the instance will not collide
# with other deployments that use the dev environment
source ./bin/activate smslab-dev jbloggs-dev

# Generate secrets locally for the active environment, if required
# DO NOT COMMIT THE GENERATED FILE TO GIT
./bin/generate-secrets

# Install Azimuth as usual
ansible-galaxy install -f -r requirements.yml
ansible-playbook azimuth_cloud.azimuth_ops.provision
```

### Logging in to the web UI

By default the "application credential" authenticator is enabled, which
allows login using the fields from an application credential. In order
to create platforms, you must use an **unrestricted** application credential
to authenticate with Azimuth .
