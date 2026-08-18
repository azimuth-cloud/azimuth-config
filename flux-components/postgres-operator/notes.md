# Migration of postgres-operator to Flux

The `postgres-operator` was deployed using a kustomize file in the Ansible collection.
There is a Helm chart available and version 5.5.2 was the latest version in the pinned commit used by Ansible.

The operator is deployed without any value overrides.

## Todo Migration of database instances

There are two database deployments performed by Ansible and the `postgres-operator`:

- Keycloak
- Coral credits

This section will be updated when those migrations are completed.
