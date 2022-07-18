# Deploying Azimuth

## Activating an environment

Before you can deploy Azimuth, you must first activate an environment:

```sh
source ./bin/activate my-site
```

!!! warning

    This script must be `source`d rather than just executed as it exports
    environment variables into the current shell that are used to configure
    the deployment.

## Deploying an environment

Once you are happy with any configuration changes and the environment that
you want to deploy has been activated, run the following commands:

```sh
# Install or update requirements
ansible-galaxy install -f -r ./requirements.yml

# Run the provision playbook from the azimuth-ops collection
# The inventory is picked up from the ansible.cfg file in the environment
ansible-playbook stackhpc.azimuth_ops.provision
```

## Tearing down an environment

`azimuth-ops` is also able to tear down an Azimuth environment, including the
K3S and HA Kubernetes clusters as required.

After activating the environment that you want to tear down, run the following:

```sh
ansible-playbook stackhpc.azimuth_ops.destroy
```
