# Try Azimuth

If you have access to a project on an OpenStack cloud, you can try Azimuth!

The [azimuth-config repository](https://github.com/azimuth-cloud/azimuth-config)
contains a special [environment](./environments.md) called `demo` that will
provision a short-lived Azimuth deployment **for demonstration purposes
only**. This environment attempts to infer all required configuration from
the target OpenStack cloud - if this process is unsuccessful, an error will
be produced.

!!! danger

    Inferring configuration in the way that the `demo` environment does is
    **not recommended** as it is not guaranteed to produce the same result
    each time. For production deployments it is better to be explicit.

    To get started with a production deployment, see the
    [best practice guide](./best-practice.md).

## Deploying a demo instance

The Azimuth deployment requires a
[clouds.yaml](https://docs.openstack.org/python-openstackclient/latest/configuration/index.html#clouds-yaml)
to run. Ideally, this should be an
[Application Credential](https://docs.openstack.org/keystone/latest/user/application_credentials.html).

Once you have a `clouds.yaml`, run the following to deploy the Azimuth demo
environment:

```sh
# Set OpenStack configuration variables
export OS_CLOUD=openstack
export OS_CLIENT_CONFIG_FILE=/path/to/clouds.yaml

# Clone the azimuth-config repository
git clone https://github.com/azimuth-cloud/azimuth-config
cd azimuth-config

# Set up the virtual environment
./bin/ensure-venv

# Activate the demo environment
source ./bin/activate demo

# Install Ansible dependencies
ansible-galaxy install -f -r requirements.yml

# Deploy Azimuth
ansible-playbook azimuth_cloud.azimuth_ops.provision
```

The URL for the Azimuth UI is printed at the end of the playbook run. The
credentials you use to authenticate with Azimuth are the same as you would
use with the underlying OpenStack cloud.

!!! warning

    Azimuth is deployed using Ansible, which
    [does not support Windows as a controller](https://docs.ansible.com/ansible/2.5/user_guide/windows_faq.html#can-ansible-run-on-windows).
    Azimuth deployment has been tested on Linux and macOS.

## Limitations

The demo deployment has a number of limitations in order to give it the best
chance of running on any given cloud:

  * It uses the
    [single node deployment method](./configuration/02-deployment-method.md#single-node).
  * [Community images](./configuration/09-community-images.md) are uploaded
    as private images, so Azimuth will only be able to provision Kubernetes
    clusters and Cluster-as-a-Service appliances in the same project as it
    is deployed in.
  * [sslip.io](https://sslip.io) is used to provide DNS. This avoids the need
    for a DNS entry to be provisioned in advance.
  * TLS is disabled for [ingress](./configuration/06-ingress.md), allowing the
    Azimuth to work even when the deployment is not reachable from the
    internet (*outbound* internet connectivity is still required).
  * Verification of SSL certificates for the OpenStack API is disabled,
    allowing Azimuth to work even when the target cloud uses a custom CA.
  * The deployment secrets are **not secret**, as they are stored in plain
    text in the `azimuth-config` repository on GitHub.
