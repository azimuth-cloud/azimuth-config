# Deploying Azimuth

## Python dependencies

The Python requirements for an Azimuth deployment host, including Ansible itself,
are contained in
[requirements.txt](https://github.com/azimuth-cloud/azimuth-config/blob/stable/requirements.txt)
and must be installed before you can proceed with a deployment. It is recommended
to use a [virtual environment](https://docs.python.org/3/library/venv.html) in order
to keep the dependencies isolated from other Python applications on the host.

`azimuth-config` includes a utility script that will create a Python virtual
environment in the configuration directory and install the required dependencies:

```sh
./bin/ensure-venv
```

If it exists, this virtual environment will be activated as part of the environment
activation (see below).

If you prefer to manage your own virtual environments then you must ensure that
the correct environment is activated and has the required dependencies installed
before continuing. For example, if you use [pyenv](https://github.com/pyenv/pyenv)
you can set the `PYENV_VERSION` environment variable
[in your azimuth-config environment](../environments.md#linux-environment-variables):

```sh  title="env"
PYENV_VERSION=azimuth-config
```

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
you want to deploy to has been activated, run the following command to
deploy Azimuth:

```sh
# Install or update Ansible dependencies
ansible-galaxy install -f -r ./requirements.yml

# Run the provision playbook from the azimuth-ops collection
# The inventory is picked up from the ansible.cfg file in the environment
ansible-playbook azimuth_cloud.azimuth_ops.provision
```

## Tearing down an environment

`azimuth-ops` is also able to tear down an Azimuth environment, including the
K3s and HA Kubernetes clusters as required.

After activating the environment that you want to tear down, run the following:

```sh
ansible-playbook azimuth_cloud.azimuth_ops.destroy
```
