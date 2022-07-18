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

`azimuth-config` includes a mixin environment -
[community_images](https://github.com/stackhpc/azimuth-config/tree/main/environments/community_images) -
that defines a default set of images. To use these defaults, just include the inventory for
the environment in your `ansible.cfg`:

```ini  title="ansible.cfg"
[defaults]
inventory = ../base/inventory,../ha/inventory,../community_images/inventory,../kubernetes_templates/inventory,./inventory
```

!!! warning

    The `community_images` environment auto-wires image IDs for the K3S node, the HA Kubernetes
    cluster, the default Kubernetes templates and the default Cluster-as-a-Service appliances.

    If you choose not to use the `community_images` environment, for example if you prefer to
    upload public images via a separate process, you will need to set these image IDs yourself.

    Please see the
    [environment variables](https://github.com/stackhpc/azimuth-config/tree/main/environments/community_images/inventory/group_vars/all.yml)
    for more details on the variables that need to be set.

## Referencing uploaded images

The IDs of the uploaded images are made available in the variable `infra_community_image_info`,
which can be used to refer to the images elsewhere in your Azimuth configuration, e.g.:

```yaml
azimuth_caas_stackhpc_workstation_image: "{{ infra_community_image_info.workstation_20220711_2135 }}"
```

## Image conversion

`azimuth-ops` is able to convert images from a "source" format to a "target" format for the
target cloud. The majority of images available for download are in `qcow2` format, and this
is the format in which images built from `azimuth-images` are distributed. However your cloud
may require images to be uploaded in a different format, e.g. `raw` or `vmdk`.

To specify the target format for your cloud, just set the following (the default is `qcow2`):

```yaml
infra_community_images_target_disk_format: raw
```

When this differs from the source format for an image, `azimuth-ops` will convert the image
using [qemu-img convert](https://linux.die.net/man/1/qemu-img) before uploading it to the
target cloud.

## Custom images

If you want to upload custom images as part of your Azimuth installation, for example to support
a custom Cluster-as-a-Service appliance or for older Kubernetes versions, you can use the
`infra_community_images_extra` variable:

```yaml
infra_community_images_extra:
  debian_11_20220711_1073:
    name: debian-11-generic-amd64-20220711-1073
    source_url: https://cloud.debian.org/images/cloud/bullseye/20220711-1073/debian-11-generic-amd64-20220711-1073.qcow2
    source_disk_format: qcow2
    container_format: bare
    disk_format: "{{ infra_community_images_target_disk_format }}"
```

The ID of this image can then be referred to elsewhere in your Azimuth configuration using:

```yaml
my_custom_caas_appliance_image: "{{ infra_community_image_info.debian_11_20220711_1073 }}"
```

!!! warning

    The keys that identify image specifications in `infra_community_images_extra` are assumed to
    be **immutable**, i.e. they will always point at the exact same image. `azimuth-ops` will
    only download, convert and upload images to the target cloud for keys that it has not seen
    before.

    For this reason, it is recommended to include a timestamp or build reference in the key
    in order to identify different images that serve the same purpose (e.g. different builds
    of the same pipeline).
