# Community images

Azimuth requires a number of specialised images to be available on the target cloud for
Cluster-as-a-Service appliances and Kubernetes clusters.

Images for Kubernetes and CaaS appliances, with the exception of Slurm, are built using
[Packer](https://www.packer.io/) from the definitions in the
[azimuth-images repository](https://github.com/azimuth-cloud/azimuth-images). For Kubernetes,
we make use of the recipes from the upstream
[Cluster API image-builder](https://github.com/kubernetes-sigs/image-builder/tree/master/images/capi).

Each [release of azimuth-images](https://github.com/azimuth-cloud/azimuth-images/releases) has
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
functionality and auto-wires them into the correct places for the K3s node, the HA Kubernetes
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
    [azimuth-ops roles](https://github.com/azimuth-cloud/ansible-collection-azimuth-ops/tree/main/roles)
    for more details.

## Custom images

If you want to upload custom images as part of your Azimuth installation, for example to support
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
