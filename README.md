# azimuth-config <!-- omit in toc -->

**THIS IS A DUMMY CHANGE TO CHECK IF WORKFLOWS ARE TRIGGERED FROM EXTERNAL FORKS**

This repository contains utilities and reference configuration for deployments of
[Azimuth](https://github.com/stackhpc/azimuth), including all the required dependencies.

Azimuth is deployed using [Ansible](https://www.ansible.com/) with playbooks from the
[azimuth-ops Ansible collection](https://github.com/stackhpc/ansible-collection-azimuth-ops).

This repository is designed to be forked for a specific site and is structured into multiple
"environments", allowing common configuration to be shared but overridden where required
using a layered approach.

## Documentation

Documentation on deploying Azimuth can be found at https://stackhpc.github.io/azimuth-config/.

The documentation source is in the [docs](./docs/) directory of this repository.
