# Platform Identity

In Azimuth, there are two kinds of users:

- **Platform Users** who are able to access one or more platforms deployed by Azimuth.
- **Platform Admins** who are able to sign in to Azimuth, manage the deployed platforms in a tenancy and administer access to those platforms.

Only Platform Admins need to have an OpenStack account. Each Azimuth tenancy has an
associated **Identity Realm** that provides the Platform Users for that tenancy and is
administered by the Platform Admins for the tenancy. This allow access to platforms to be
granted for users that do not have an OpenStack account.

This separation of Platform Users from OpenStack accounts opens up a wide range of use cases
that are not possible when platforms can only be accessed by users with OpenStack accounts.

## Example use case

Imagine that a project with quota on an OpenStack cloud wishes to host an open
workshop using Jupyter notebooks for teaching. In this case, they definitely don't want
to grant every workshop attendee access to OpenStack, as these users may not be trusted.

Using Azimuth, a trusted project member (i.e. a Project Admin) can deploy a JupyterHub
in Azimuth and create users in their Identity Realm for the workshop attendees.
These users can be granted access to JupyterHub for the duration of the workshop, and
at the end of the workshop their access can be revoked.

## Use of Keycloak

In order to accomplish this, every Azimuth installation includes an instance of
the [Keycloak](https://www.keycloak.org/) open-source identity management platform.
Each Azimuth tenancy (i.e. OpenStack project) has an associated
[realm](https://www.keycloak.org/docs/latest/server_admin/#configuring-realms)
in this Keycloak instance that is used to manage access to platforms deployed
in that tenancy. The realm provides authentication and authorization for
the Zenith services associated with the platforms in the tenancy using
[OpenID Connect (OIDC)](https://openid.net/connect/).

Each realm is created with two groups - `admins` and `platform-users`. Users who are
in the `platform-users` group for a realm are granted access to all platforms deployed
in the corresponding Azimuth tenancy. Users who are in the `admins` group are granted
admin status for the realm, meaning they can perform actions in the Keycloak admin
console such as:

- [Managing users](https://www.keycloak.org/docs/latest/server_admin/#assembly-managing-users_server_administration_guide)
- [Assigning users to groups](https://www.keycloak.org/docs/latest/server_admin/#proc-managing-groups_server_administration_guide)
- [Configuring authentication policies](https://www.keycloak.org/docs/latest/server_admin/#configuring-authentication_server_administration_guide),
  e.g. password requirements, multi-factor authentication
- [Integrating external identity providers](https://www.keycloak.org/docs/latest/server_admin/#_identity_broker)

The Keycloak realms created by Azimuth are configured with Azimuth as an identity
provider, so that Platform Admins who belong to a tenancy in Azimuth can sign in to
the corresponding realm using the Azimuth identity provider. Platform Admins who sign
in to a realm via Azimuth are automatically placed in the `admins` and `platform-users`
groups described above.

When a platform is deployed in an Azimuth tenancy a group is created in the corresponding
identity realm, and access to the platform is controlled by membership of this group. Each
Zenith service for the platform has a child group under the platform group that can be
used to grant access to a single service within a platform.

For example, the standard Linux Workstation platform (see
[Cluster-as-a-Service (CaaS)](../configuration/12-caas.md)) exposes two Zenith services -
"Web Console" and "Monitoring". If an instance of this platform is deployed with the name
`my-workstation`, then access to the "Web Console" service can be granted by either:

- Adding the user to the `platform-users` group.  
   This will also grant the user access to all other platforms in the tenancy.
- Adding the user to the `caas-my-workstation` group.  
   This will grant the user access to the "Web Console" and "Monitoring" services.
- Adding the user to the `caas-my-workstation/webconsole` group.  
   This will grant the user access to the "Web Console" service only.

## Keycloak admin password

The only required configuration for platform identity is to set the admin password for Keycloak:

```yaml title="environments/my-site/inventory/group_vars/all/secrets.yml"
keycloak_admin_password: "<secure password>"
```

<!-- prettier-ignore-start -->
!!! tip
    azimuth-config includes a utility for generating secrets for an environment:
    ```sh
    ./bin/generate-secrets [--force] <environment-name>
    ```

!!! danger
    This password should be kept secret. If you want to keep the password in Git - which is recommended - then it must be encrypted.
<!-- prettier-ignore-end -->

See [secrets](../repository/secrets.md).
