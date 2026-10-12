# Zenith Application Proxy

The Zenith application proxy is enabled by default in the reference configuration. To disable
it, just set:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_apps_enabled: no
```

For all deployments, Zenith requires a secret key to be configured. This is used to sign and
verify the single-use tokens issued by the registrar (see the Zenith architecture document
for details):

```yaml title="environments/my-site/inventory/group_vars/all/secrets.yml"
zenith_registrar_subdomain_token_signing_key: "<some secret key>"
```

<!-- prettier-ignore-start -->
!!! tip
    This key must be a long, random string - at least 32 bytes (256 bits) is required.
    azimuth-config includes a utility for generating secrets for an environment:
    ```sh
    ./bin/generate-secrets [--force] <environment-name>
    ```

!!! danger
    This key should be kept secret. If you want to keep it in Git - which is recommended - then it [must be encrypted](../repository/secrets.md).
<!-- prettier-ignore-end -->

## SSHD load-balancer IP address

<!-- prettier-ignore-start -->
!!! note "HA deployments only"
    This section only applies to HA deployments.
<!-- prettier-ignore-end -->

In a HA deployment, the Zenith SSHD server has a dedicated load-balancer with its own IP address.
The floating IP to use for this load balancer must be pre-allocated and specified using the
following variable:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
zenith_sshd_service_load_balancer_ip: "<ip address>"
```

## SSHD port number

By default, the Zenith SSHD server will use port `22` on a dedicated IP address for a HA
deployment and port `2222` on the pre-allocated floating IP for a single node deployment
(port `22` is used for regular SSH to configure the node).

This can be changed using the following variable, if required:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
zenith_sshd_service_port: 22222
```
