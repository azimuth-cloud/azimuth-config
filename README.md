# azimuth-config <!-- omit in toc -->

This repository contains utilities and reference configuration for deployments of
[Azimuth](https://github.com/azimuth-cloud/azimuth), including all the required dependencies.

Azimuth is deployed using [Ansible](https://www.ansible.com/) with playbooks from the
[azimuth-ops Ansible collection](https://github.com/azimuth-cloud/ansible-collection-azimuth-ops).

This repository is designed to be forked for a specific site and is structured into multiple
"environments", allowing common configuration to be shared but overridden where required
using a layered approach.

## Documentation

Documentation on deploying Azimuth can be found at <https://azimuth-config.readthedocs.io>.

For local checks and the OpenStack and Tilt workflow, see the
[development guide](./docs/developing/index.md).

The documentation source is in the [docs](./docs/) directory of this repository.

## Developing locally

### Previewing the documentation

Documentation changes can be previewed and checked without OpenStack or Kubernetes:

```sh
python3 -m venv .venv-docs
source .venv-docs/bin/activate
python -m pip install -r requirements-docs.txt
mkdocs serve
```

Open the local URL printed by MkDocs to preview the site.
Before submitting a change, check the complete site for build errors and broken page links:

```sh
mkdocs build --strict
```

### Linters

To run the GitHub Actions linters locally, use:

```sh
docker run --rm \
    -e RUN_LOCAL=true \
    --env-file "super-linter.env" \
    -v "$(pwd)":/tmp/lint \
    ghcr.io/super-linter/super-linter:v8.6.0
```

Note: For M-series Apple devices and other ARM processors, add `--platform linux/amd64`
as an extra argument to the above `docker run ...` command.

```sh
ansible-lint -c .ansible-lint.yml
```
