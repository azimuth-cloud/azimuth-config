# Community images

Azimuth requires a number of specialised images to be available on the target cloud for
Cluster-as-a-Service appliances and Kubernetes clusters.

Images for Kubernetes and CaaS appliances, with the exception of Slurm, are built using
[Packer](https://www.packer.io/) from the definitions in the
[azimuth-images repository](https://github.com/stackhpc/azimuth-images). For Kubernetes,
we make use of the recipes from the upstream
[Cluster API image-builder](https://github.com/kubernetes-sigs/image-builder/tree/master/images/capi).

Each [release of azimuth-images](https://github.com/stackhpc/azimuth-images/releases) has
an associated manifest that describes the images in the release and where to download them
from, along with some additional metadata. The Azimuth deployment playbooks are able to
consume these manifests.

Images for the Slurm cluster appliance are built using Packer from definitions in the
[slurm-image-builder respository](https://github.com/stackhpc/slurm_image_builder), with builds uploaded
[here](https://object.arcus.openstack.hpc.cam.ac.uk/swift/v1/AUTH_3a06571936a0424bb40bc5c672c4ccb1/openhpc-images/).

`azimuth-ops` is able to download, convert (if required) and then create
[Glance images](https://docs.openstack.org/glance/latest/) on the target cloud from these sources.
Images are uploaded as
[community images](https://wiki.openstack.org/wiki/Glance-v2-community-image-visibility-design)
meaning they are accessible by all projects in the target cloud, but not included by default
when listing images in Horizon, the OpenStack CLI or the OpenStack API.

By default, `azimuth-ops` uploads the set of images that are needed to support Azimuth's
functionality and auto-wires them into the correct places for the K3S node, the HA Kubernetes
cluster, the default Kubernetes templates and the default Cluster-as-a-Service appliances.

## Image properties

Properties can be set on the uploaded images, if required. The properties are given as
strings of the form `key=value` in the following variable:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
community_images_custom_properties:
  - 'prop1=value1'
  - 'prop2=value2'
```

## Image conversion

Images can be converted from a "source" format to a "target" format for the target cloud. The
majority of images available for download are in `qcow2` format, and this is the format in
which images built from `azimuth-images` are distributed. However your cloud may require
images to be uploaded in a different format, e.g. `raw` or `vmdk`.

To specify the target format for your cloud, just set the following (the default is `qcow2`):

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
community_images_disk_format: raw
```

When this differs from the source format for an image, `azimuth-ops` will convert the image
using [qemu-img convert](https://linux.die.net/man/1/qemu-img) before uploading it to the
target cloud.

## Disabling community images

It is possible to prevent `azimuth-ops` from uploading any images, even the default ones,
by setting the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
community_images: {}
```

!!! warning

    If community images are disabled you will need to ensure suitable images are
    uploaded via another mechanism, and the correct variables populated with the
    image IDs in your Azimuth configuration. See the
    [azimuth-ops roles](https://github.com/stackhpc/ansible-collection-azimuth-ops/tree/main/roles)
    for more details.

## Custom images

### Modifying existing images

Building custom images is supported in Azimuth. For introductory purposes this guide will focus on only adding a single program to a custom image. There will also be a brief introduction to upstreaming images and 'Continuous Integration' at the end of this guide.

To begin building custom images for Azimuth, the ideal starting point is using the 'azimuth-images' repository as a base. To begin exploring, clone the repository as below:

```git clone https://github.com/stackhpc/azimuth-images.git```

The first point of focus will be on the ``ansible`` directory. This directory contains playbooks that add configuration and packages to the 'base' images. In the case of a Workstation appliance, base images will typically be an empty Ubuntu image, these playbooks are used to add VNC/Guacamole configuration, Podman and Zenith support allowing these images to be used in the Azimuth ecosystem.

In the ``roles`` directory the indivdual components are modularised as Ansible roles, in this architecture it is possible to re-purpose code that may be used on multiple different applicances/images (e.g. Zenith). To make a direct change to the Workstation appliance, the ``linux-webconsole`` role can be edited to include new packages. To have Ansible install 'GNU Octave' as an example, the `main.yml` playbook can be modified as below:

```
- name: Install Octave
  apt:
    name: octave
    state: present
```
Now the playbook has been modified to install another package, 'Packer' can now be used to generate the new image. Using Packer requires access to a cloud with a floating IP. Assuming cloud access, a Packer configuration file is addtionally required for Packer to have information about the cloud it's constructing the image on. The configuration file used for building images on Sausage Cloud (sausage.pkvars.hcl) looks like this:

```
source_image_name = "packer-d32bd27c-3b34-4fab-b8ad-e491147a60da"

network = "4ca2399f-3040-4686-82fa-e99bd50d215a"
floating_ip = "842fd1f3-0e6f-42e2-aa42-045cf58535b9"
security_groups = ["default"]

flavor = "cumberland"
distro_name = "ubuntu-jammy"
ssh_username = "ubuntu"
volume_size = 20
```
To begin the Packer build process for the Workstation image,the following command can be run where $PATH_TO_VARS_FILE is the location of the Packer configuration file:

```
packer build --on-error=ask -var-file=$PATH_TO_VARS_FILE packer/linux-desktop.pkr.hcl
```
The build process should be visible in the console log, eventually during runtime the Ansible task added to the webconsole role earlier should be visible in the logs completing successfully. Installing the desktop environment will take a long time, expect this build process to take over 30 minutes depending on the cloud hardware. After build completion, the OpenStack image ID will be printed to the console by Packer. To use this in an Azimuth configuration, the ``azimuth_caas_stackhpc_workstation_image`` variable will need to be assigned with the image id generated from Packer and declared in the ``azimuth-config`` enviornment.

### Upstream contributions

 Upstream contributions can be directed to the StackHPC Community Images [repository](https://github.com/stackhpc/azimuth-images). To do this, you will need to commit, push and create a pull request. (Hint: If you've followed the guide this far, your changes are already in the correct repository and ready to be pushed!)

### The role of Continuous Integration

You may have wondered during this guide how changes you push to GitHub are built, tested and distributed. GitHub Actions are utilised in the community images repoistory for building, testing and publishing new images continuously on new changes. The ``.github`` directory in the community images repository contains all the CI configuration used. The ``pr.yml`` GitHub workflow is the most relevent workflow for our particular use case. Following the upstream guide above, if you made a pull request you'll notice a new workflow being initialised, this workflow will build images relevent to the Ansible modified to ensure your changes do not contain fatal Ansible syntax errors. (Note: This stage of the CI may not always pick up broken changes, such as the case of broken packages).

If your changes were approved and passed the build workflow, you can now merge it into the 'main' branch and new build workflow will be triggered on merging. Following a successful build workflow, the image created will not be deleted as it is in the pull request workflow. To make this image public, it is required to create a GitHub tag, which will trigger the ``tag.yml`` workflow and the manifest for the new images built will be made public for new deployments.

### Applying external images

If you want to upload external images as part of your Azimuth installation, for example to support
a custom Cluster-as-a-Service appliance or for older Kubernetes versions, you can use the
`community_images_extra` variable:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
community_images_extra:
  # Key, used to refer to the image ID
  debian_11:
    # The name of the image to create on the target cloud
    name: debian-11-generic-amd64-20220711-1073
    # The URL of the source image
    source_url: https://cloud.debian.org/images/cloud/bullseye/20220711-1073/debian-11-generic-amd64-20220711-1073.qcow2
    # The disk format of the source image
    source_disk_format: qcow2
    # The container format of the source image
    container_format: bare
```

The ID of this image can then be referred to elsewhere in your Azimuth configuration using:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
my_custom_caas_appliance_image: "{{ community_images_image_ids.debian_11 }}"
```

!!! warning

    It is assumed that the `name` in a community image specification refers to a unique image.
    `azimuth-ops` will only download, convert and upload images to the target cloud for names
    that do not already exist.

    For this reason, it is recommended to include a timestamp or build reference in the image
    name in order to identify different images that serve the same purpose (e.g. different builds
    of the same pipeline).
