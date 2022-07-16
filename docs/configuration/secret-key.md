# Secret key

Azimuth requires a secret key that is used primarily for signing cookies:

```yaml
azimuth_secret_key: "<some secret key>"
```

!!! tip

    This key should be a long, random string - at least 32 bytes (256 bits) is recommended.
    A suitable key can be generated using `openssl rand -hex 32`.

!!! danger

    This key should be kept secret. If you want to keep it in Git - which is recommended - then
    it [must be encrypted](../secrets.md).
