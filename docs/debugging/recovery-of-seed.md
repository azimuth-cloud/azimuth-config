<!-- markdownlint-disable-file MD046 -->

# Recovery of the Seed Node

In an HA deployment, the Seed Node manages the separate HA cluster that runs Azimuth.
In a single node deployment, the Seed Node hosts Azimuth itself, so a failure interrupts the service.

If access to the Seed Node fails via the `./bin/seed-ssh` script,
and the Seed Node is effectively inaccessible, there are some methods
that can be applied to bring it back into service.

!!! tip "OpenStack Specific"

    This text assumes the Seed Node is deployed in an OpenStack cloud.

## Check Seed Node Console and Console Log

As an administrator, or a user with membership of the Azimuth service
project, the instance consoles and logs for Azimuth's CAPI management
cluster can be accessed. This should provide useful information
about the root cause of the Seed Node's issues.

A console log ending in text of this form indicates that the Seed
Node root filesystem has become corrupted and requires manual
operator intervention for recovery:

```sh
[/usr/sbin/fsck.ext4 (1) -- /dev/vda1] fsck.ext4 -a -C0 /dev/vda1
cloudimg-rootfs contains a file system with errors, check forced.
cloudimg-rootfs: Inodes that were part of a corrupted orphan linked list found.

cloudimg-rootfs: UNEXPECTED INCONSISTENCY; RUN fsck MANUALLY.
 (i.e., without -a or -p options)
fsck exited with status code 4
done.
Failure: File system check of the root filesystem failed
The root filesystem on /dev/vda1 requires a manual fsck


BusyBox v1.30.1 (Ubuntu 1:1.30.1-7ubuntu3.1) built-in shell (ash)
Enter 'help' for a list of built-in commands.

(initramfs)
```

## Recovery via OpenStack Rescue

OpenStack provides [instance rescue](https://docs.openstack.org/nova/latest/user/rescue.html), which temporarily boots an instance from a rescue image while making its original disk available for repair.
The original disk's device name depends on the rescue mode and image.
Rescue of volume-backed instances requires Compute API microversion 2.87 or later, a suitable rescue image and a compatible hypervisor configuration.
Consult the cloud operator's rescue instructions before proceeding.
Rescue can be started from Horizon or the OpenStack command line:

```sh
openstack server rescue "<seed-node>"
```

For a volume-backed Seed Node, select an image configured for stable device rescue and specify the required API microversion:

```sh
openstack --os-compute-api-version 2.87 server rescue \
  --image "<rescue-image-id>" "<seed-node>"
```

Access the rescued instance using its console or the SSH credentials supported by the rescue image.
The `seed-ssh` script works only if the rescue image accepts the deployment's SSH key for the `ubuntu` user:

```sh
./bin/seed-ssh
```

Use `lsblk -f` to identify the original root filesystem and check that it is unmounted before repairing it.
For example, if the original root filesystem is ext4 on `/dev/vdb1`, run:

```sh
sudo fsck -t ext4 /dev/vdb1
```

Once recovery has been completed, the Seed Node can be booted again
using the recovered root disk through an `unrescue` process, either
via Horizon or the OpenStack command line:

```sh
openstack server unrescue "<seed-node>"
```
