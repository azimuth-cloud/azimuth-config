# Target OpenStack cloud

The main piece of site-specific configuration required by Azimuth is the connection information
for the target OpenStack cloud.

Azimuth uses the
[Keystone Service Catalog](https://docs.openstack.org/keystone/latest/contributor/service-catalog.html)
to discover the endpoints for OpenStack services, so only needs to be told where to find the
Keystone v3 endpoint.

By default, the auth URL from the application credential used to deploy Azimuth will be used.
If you want Azimuth to target a different OpenStack cloud than the one it is deployed in, this
can be overridden:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_openstack_auth_url: https://openstack.example-cloud.org:5000/v3
```

!!! warning

    Make sure to include the trailing `/v3`, otherwise authentication will fail.

Azimuth does not currently have support for specifying a custom CA for verifying TLS. If the
target cloud uses a TLS certificate that is not verifiable using the operating-system default
trustroots, TLS verification must be disabled:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_openstack_verify_ssl: false
```

If you are using the password authenticator and use a domain other than `default`,
you will also need to tell Azimuth the name of the domain to use when authenticating:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_openstack_domain: my-domain
```

## Cloud name

Azimuth presents the name of the current cloud in various places in the interface. To configure
this, set the following variables:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# The machine-readable cloud name
azimuth_current_cloud_name: my-cloud

# The human-readable name for the cloud
azimuth_current_cloud_label: My Cloud
```

## Federated authentication

By default the password authenticator is enabled, which accepts a username and password and swaps
them for an OpenStack token. This requires no additional configuration.

If the target cloud consumes identities from an external provider via
[Keystone federation](https://docs.openstack.org/keystone/latest/admin/federation/introduction.html),
then Azimuth should be configured to obtain an OpenStack token from Keystone using the same flow
as Horizon. To enable this, additional configuration is required for both Azimuth and Keystone
on the target cloud.

First, the Keystone configuration of the target cloud must be modified to add Azimuth as a
[trusted dashboard](https://docs.openstack.org/keystone/latest/admin/federation/configure_federation.html#add-a-trusted-dashboard-websso),
otherwise it will be unable to retrieve a token via the federated flow. When configuring Azimuth as a
trusted dashboard, you must specify the URL that will receive token data, where the portal domain
depends on the [ingress configuration](../06-ingress.md):

```ini  title="Keystone configuration"
[federation]
trusted_dashboard = https://portal.azimuth.example.org/auth/federated/complete/
```

In your Azimuth configuration, enable the federated authenticator and tell it the provider and
protocol to use:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_authenticator_federated_enabled: yes
azimuth_authenticator_federated_provider: "<provider>"
azimuth_authenticator_federated_protocol: "<protocol>"
```

This will result in Azimuth using URLs of the following form for the federated authentication flow:

```
<auth url>/auth/OS-FEDERATION/identity_providers/<provider>/protocols/<protocol>/websso
```

The provider and protocol will depend on the Keystone configuration of the target OpenStack cloud.

To also disable the password authenticator - so that federation is the only supported login - set
the following variable:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_authenticator_password_enabled: no
```

To change the human-readable names for the authenticators, which are presented in the authentication
method selection form, use the following variables:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_authenticator_password_label: "Username + Password"
azimuth_authenticator_federated_label: "Federated"
```

## Networking configuration

Azimuth uses
[Neutron resource tags](https://docs.openstack.org/neutron/latest/contributor/internals/tag.html)
to discover the networks it should use, and the tags it looks for are `portal-internal` and
`portal-external` for the internal and external networks respectively. These tags must be applied
by the cloud operator.

!!! tip

    It is strongly recommended that you set the `portal-external` tag on an appropriate external network,
    even if you only have one external network, to avoid issues if new external networks are added to the
    cloud at a later date.

If it cannot find a tagged internal network, the default behaviour is for Azimuth to create an
internal network to use (and the corresponding router to attach it to the external network).

The discovery and auto-creation process is described in detail in
[Network discovery and auto-creation](https://github.com/azimuth-cloud/azimuth/tree/master/docs/architecture.md#network-discovery-and-auto-creation).

To disable the auto-creation of internal networks, use the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_openstack_create_internal_net: false
```

The CIDR of the auto-created subnet can also be changed, although it is the same for every project.
For example, you may need to do this if the default CIDR conflicts with resources elsewhere
on your network that machines provisioned by Azimuth need to access:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# Defaults to 192.168.3.0/24
azimuth_openstack_internal_net_cidr: 10.0.3.0/24
```

## Monitoring Cloud Capacity

Azimuth is able to federate cloud metrics from a Prometheus running within
your OpenStack cloud enviroment, such as the one deployed by
[stackhpc-kayobe-config](https://github.com/stackhpc/stackhpc-kayobe-config).

We also assume the [os-capacity exporter](https://github.com/stackhpc/os-capacity)
is being used to query the current capacity of your cloud, mostly using data from
OpenStack placement.

First you need to enable the project metrics and cloud metrics links within
Azimuth by configuring:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# Defaults to no
cloud_metrics_enabled: yes
```

You then need to tell Azimuth how to access the OpenStack cloud Prometheus:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
# hostname needed to match TLS certificate name
cloud_metrics_prometheus_host: "mycloud.example.com"
# ip that matches the above hostname
cloud_metrics_prometheus_ip: "<ip prometheus vip>"
cloud_metrics_prometheus_port: 9091
cloud_metrics_prometheus_basic_auth_username: "<basic-auth-username>"
cloud_metrics_prometheus_basic_auth_password: "<basic-auth-password>"
```
