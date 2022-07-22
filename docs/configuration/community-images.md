# Community images

Azimuth requires a number of specialised images to be available on the target cloud for
Cluster-as-a-Service appliances and Kubernetes clusters.

Images for the workstation and repo2docker appliances are built using
[Packer](https://www.packer.io/) from the definitions in the
[azimuth-images repository](https://github.com/stackhpc/azimuth-images). The results of these
builds are uploaded
[here](https://object.arcus.openstack.hpc.cam.ac.uk/swift/v1/AUTH_f0dc9cb312144d0aa44037c9149d2513/azimuth-images-prerelease/)
for consumption by Azimuth deployments.

For Kubernetes, we use the [OSISM builds](https://minio.services.osism.tech/openstack-k8s-capi-images)
of the Cluster API images from the
[Kubernetes image-builder](https://github.com/kubernetes-sigs/image-builder/tree/master/images/capi).

`azimuth-ops` is able to download, convert (if required) and then create
[Glance images](https://docs.openstack.org/glance/latest/) on the target cloud from these sources.
Images are uploaded as
[community images](https://wiki.openstack.org/wiki/Glance-v2-community-image-visibility-design)
meaning they are accessible by all projects in the target cloud, but not included by default
when listing images in Horizon or via the CLI or API.

By default, `azimuth-ops` creates a  set of images that are needed to support Azimuth's
functionality and auto-wires them into the correct places for the K3S node, the HA Kubernetes
cluster, the default Kubernetes templates and the default Cluster-as-a-Service appliances.

## Referencing uploaded images

The IDs of the uploaded images are made available in the variable `community_images_image_ids`, which
can be used to refer to the images elsewhere in your Azimuth configuration, e.g.:

```yaml
azimuth_caas_stackhpc_workstation_image: "{{ community_images_image_ids.workstation_20220711_2135 }}"
```

## Image conversion

`azimuth-ops` is able to convert images from a "source" format to a "target" format for the
target cloud. The majority of images available for download are in `qcow2` format, and this
is the format in which images built from `azimuth-images` are distributed. However your cloud
may require images to be uploaded in a different format, e.g. `raw` or `vmdk`.

To specify the target format for your cloud, just set the following (the default is `qcow2`):

```yaml
community_images_disk_format: raw
```

When this differs from the source format for an image, `azimuth-ops` will convert the image
using [qemu-img convert](https://linux.die.net/man/1/qemu-img) before uploading it to the
target cloud.

## Disabling community images

It is possible to prevent `azimuth-ops` from uploading any images, even the default ones,
by setting the following:

```yaml
community_images: {}
```

!!! warning

    If community images are disabled you will need to ensure suitable images are
    uploaded via another mechanism, and the correct variables populated with the
    image IDs in your Azimuth configuration. See the
    [azimuth-ops roles](https://github.com/stackhpc/ansible-collection-azimuth-ops/tree/main/roles)
    for more details.

## Custom images

If you want to upload custom images as part of your Azimuth installation, for example to support
a custom Cluster-as-a-Service appliance or for older Kubernetes versions, you can use the
`community_images_extra` variable:

```yaml
community_images_extra:
  debian_11_20220711_1073:
    name: debian-11-generic-amd64-20220711-1073
    source_url: https://cloud.debian.org/images/cloud/bullseye/20220711-1073/debian-11-generic-amd64-20220711-1073.qcow2
    source_disk_format: qcow2
    container_format: bare
```

The ID of this image can then be referred to elsewhere in your Azimuth configuration using:

```yaml
my_custom_caas_appliance_image: "{{ community_images_image_ids.debian_11_20220711_1073 }}"
```

!!! warning

    The image specifications in `community_images_extra` are assumed to be **immutable**, i.e.
    they will never change. It is also assumed that the names refer to unique images.
    `azimuth-ops` will only download, convert and upload images to the target cloud for names
    that do not already exist.

    For this reason, it is recommended to include a timestamp or build reference in the image
    name in order to identify different images that serve the same purpose (e.g. different builds
    of the same pipeline).
