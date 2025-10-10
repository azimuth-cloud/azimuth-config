# Secret key

Azimuth requires a secret key that is used primarily for signing cookies:

```yaml title="environments/my-site/inventory/group_vars/all/secrets.yml"
azimuth_secret_key: "<some secret key>"
```

<!-- prettier-ignore-start -->
!!! tip
    This key should be a long, random string - at least 32 bytes (256 bits) is recommended.
<!-- prettier-ignore-end -->

`azimuth-config` includes a utility for generating secrets for an environment:

```sh
./bin/generate-secrets [--force] <environment-name>
```

<!-- prettier-ignore-start -->
!!! danger
    This key should be kept secret. If you want to keep it in Git - which is recommended - then it must be encrypted.
    See [secrets](../repository/secrets.md).
<!-- prettier-ignore-end -->
