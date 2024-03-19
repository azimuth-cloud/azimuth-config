# Azimuth Operator Documentation

This documentation describes how to manage deployments of
[Azimuth](https://github.com/stackhpc/azimuth),
including all the required dependencies.

## Try Azimuth on your OpenStack cloud

If you have access to a project on an OpenStack cloud, you can try Azimuth!
You don't need admin level access.

To try out Azimuth on your OpenStack cloud, you can follow [these instructions](./try.md)
to get a simple deployment running within a single VM in your OpenStack cloud.

## Getting started with a Production Azimuth

Azimuth is deployed using [Ansible](https://www.ansible.com/) with playbooks from the
[azimuth-ops Ansible collection](https://github.com/stackhpc/ansible-collection-azimuth-ops),
driven by configuration derived from the
[azimuth-config reference configuration](https://github.com/stackhpc/azimuth-config).

The `azimuth-config` repository is designed to be forked for a specific site and is structured
into multiple [environments](#environments). This structure allows common configuration to be
shared but overridden where required using composition of environments.

For a production-ready deployment, you should follow the steps in the
[getting started documentation](./best-practice.md).

## Understating Azimuth Architecture

If you want to know more about how Azimuth is architected,
and better understand its security model,
please read
[Azimuth Architecture](./architecture.md)

## Developing Azimuth

For a developer setup, please see [developing azimuth](./developing/index.md).