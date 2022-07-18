# Target cloud

The main piece of site-specific configuration required by Azimuth is the connection information
for the target OpenStack cloud.

Azimuth uses the
[Keystone Service Catalog](https://docs.openstack.org/keystone/latest/contributor/service-catalog.html)
to discover the endpoints for OpenStack services, so only needs to be told where to find the
Keystone v3 endpoint:

```yaml
azimuth_openstack_auth_url: https://openstack.example-cloud.org:5000/v3
```

Azimuth does not currently have support for specifying a custom CA for verifying TLS. If the
target cloud uses a TLS certificate that is not verifiable using the operating-system default
trustroots, TLS verification must be disabled:

```yaml
azimuth_openstack_verify_ssl: false
```

If you use a domain other than `default`, you will also need to tell Azimuth the name of the
domain to use when authenticating:

```yaml
azimuth_openstack_domain: my-domain
```

## Cloud name

Azimuth presents the name of the current cloud in various places in the interface. To configure
this, set the following variables:

```yaml
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
then Azimuth can be configured to obtain an OpenStack token from Keystone using the same flow
that Horizon does. To enable this, additional configuration is required for both Azimuth and Keystone
on the target cloud.

In your Azimuth configuration, enable the federated authenticator and tell it the provider to use:

```yaml
azimuth_authenticator_federated_enabled: yes
azimuth_authenticator_federated_provider: "<provider>"
```

This will result in Azimuth using URLs of the form `<auth url>/auth/OS-FEDERATION/websso/<provider>`
for authentication.

The Keystone configuration of the target cloud must also be modified to add Azimuth as a
[trusted dashboard](https://docs.openstack.org/keystone/latest/admin/federation/configure_federation.html#add-a-trusted-dashboard-websso),
otherwise it will be unable to retrieve a token via the federated flow. When configuring Azimuth as a
trusted dashboard, you must specify the URL that will receive token data - for an Azimuth deployment,
this URL is `https://[portal domain]/auth/federated/complete/`, where the portal domain depends on
the ingress configuration as described elsewhere in this document.

To also disable the password authenticator - so that federation is the only supported login - set
the following variable:

```yaml
azimuth_authenticator_password_enabled: no
```

To change the human-readable names for the authenticators, which are presented in the authentication
method selection form, use the following variables:

```yaml
azimuth_authenticator_password_label: "Username + Password"
azimuth_authenticator_federated_label: "Federated"
```

## Networking configuration

Azimuth uses
[Neutron resource tags](https://docs.openstack.org/neutron/latest/contributor/internals/tag.html)
to discover the networks it should use, and the tags it looks for are `portal-internal` and
`portal-external` for the internal and external networks respectively. These tags must be applied
by the cloud operator.

If it cannot find a tagged internal network, the default behaviour is for Azimuth to create an
internal network to use (and the corresponding router to attach it to the external network).

The discovery and auto-creation process is described in detail in
[Network discovery and auto-creation](https://github.com/stackhpc/azimuth/tree/master/docs/architecture.md#network-discovery-and-auto-creation).

To disable the auto-creation of internal networks, use the following:

```yaml
azimuth_openstack_create_internal_net: false
```

The CIDR of the auto-created subnet can also be changed, although it is the same for every project.
For example, you may need to do this if the default CIDR conflicts with resources elsewhere
on your network that machines provisioned by Azimuth need to access:

```yaml
# Defaults to 192.168.3.0/24
azimuth_openstack_internal_net_cidr: 10.0.3.0/24
```
