# Ingress

As mentioned in the prerequisites, Azimuth and Zenith expect to be given control of an entire
subdomain, e.g. `*.azimuth.example.org`, and this domain must be assigned to a pre-allocated
floating IP using a wildcard DNS entry.

To tell `azimuth-ops` what domain it should use, simply set the following variable:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
ingress_base_domain: azimuth.example.org
```

This will result in `azimuth-ops` using `portal.azimuth.example.org` for the Azimuth portal
interface, and Zenith will use domains of the form `<random subdomain>.azimuth.example.org`
for user-facing services. Other services deployed by Azimuth, such as
[Harbor](./10-kubernetes-clusters.md#harbor-registry) and the
[monitoring and alerting dashboards](./14-monitoring.md#accessing-web-interfaces) will
also be allocated subdomains under this domain.

## Transport Layer Security (TLS)

TLS for Azimuth can be configured in two ways:

### Pre-existing wildcard certificate

If you have a pre-existing **wildcard** TLS certificate issued for the ingress base domain,
you can use this to provide TLS for Azimuth and Zenith services.

<!-- prettier-ignore-start -->
!!! tip
    This is the recommended mechanism for production deployments, despite the lack of automation, for two reasons:
    - It is not affected by [rate limits](https://letsencrypt.org/docs/rate-limits/)
    - Zenith services become available faster as it avoids the overhead of obtaining a certificate per service

!!! warning
    It is your responsibility to renew the wildcard certificate before it expires.
    The Azimuth monitoring will produce alerts when the certificate is approaching its expiry date.
    See [Azimuth monitoring](./14-monitoring.md).
<!-- prettier-ignore-end -->

To configure a pre-existing wildcard certificate for ingress, just create the following files in your environment:

`environments/my-site/tls/tls.crt`
: Must contain the **full certificate chain**, with the most specific certificate at the top (e.g. the wildcard certificate), any intermediate certificates and the root CA at the bottom.

`environments/my-site/tls/tls.key`
: The corresponding private key for the wildcard certificate.

When these files exist in an environment, `azimuth-ops` will automatically pick them up
and use them.

<!-- prettier-ignore-start -->
!!! danger
    The TLS key should be kept secret. If you want to keep it in Git - which is recommended - then it [must be encrypted](../repository/secrets.md).

!!! info
    In the future, support for a wildcard certificate managed by cert-manager may be implemented.
    However this will require the use of a supported DNS provider in order to fulfil the DNS01 challenge (wildcard certificates cannot be issued for an HTTP01 challenge).
    See [cert-manager](https://cert-manager.io/) and [supported DNS providers](https://cert-manager.io/docs/configuration/acme/dns01/#supported-dns01-providers).
<!-- prettier-ignore-end -->

### Automated with cert-manager

`azimuth-ops` is able to configure `Ingress` resources for Azimuth and Zenith services so
that their TLS certificates are managed automatically using [cert-manager](https://cert-manager.io/).

In this configuration, a certificate is issued _for each separate subdomain_ by an
[ACME provider](https://en.wikipedia.org/wiki/Automatic_Certificate_Management_Environment)
using the
[HTTP-01 challenge type](https://letsencrypt.org/docs/challenge-types/#http-01-challenge).

By default, cert-manager is enabled and this mechanism will be used to issue TLS certificates
for Azimuth and Zenith services with no further configuration. The default ACME service is
[Let's Encrypt](https://letsencrypt.org/), which issues certificates that are trusted by
all major operating systems and browsers.

<!-- prettier-ignore-start -->
!!! danger "Let's Encrypt rate limits"
    Let's Encrypt imposes rate limits to ensure fair usage.
    At the time of writing, **the number of new certificates that can be issued is 50 per week per registed domain**. The "registered domain" is the part of the domain that is purchased from the registrar so, for an Azimuth deployment with an ingress base domain of `*.azimuth.example.org`, the Let's Encrypt rate limit is imposed on `example.org`.
    If there are a large number of Zenith services and the rate limit is reached, cert-manager will not be able to obtain a certificate and Azimuth and Zenith services will never become available.
    See [Let's Encrypt rate limits](https://letsencrypt.org/docs/rate-limits/)
<!-- prettier-ignore-end -->

#### Using another ACME provider

It is possible to configure the issuer to use a different ACME server, e.g. if your institution
has an ACME server that issues trusted certificates:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
# The name of the issuer
certmanager_acmehttp01issuer_name: example-acme
# The URL of the ACME endpoint
certmanager_acmehttp01issuer_server: https://acme.example.org
```

If ACME server requires External Account Binding (EAB) it needs to be enabled and credentials
added to encrypted secrets file:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
# Indicates whether an External Account Binding (EAB) is required
certmanager_acmehttp01issuer_eab_required: yes
```

```yaml title="environments/my-site/inventory/group_vars/all/secrets.yml"
# The key ID of the EAB
certmanager_acmehttp01issuer_eab_kid: "EXAMPLE_EAB_KID"
# The HMAC key of the EAB
certmanager_acmehttp01issuer_eab_key: "EXAMPLE_EAB_KEY"
```
