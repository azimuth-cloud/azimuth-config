# Recovery of the Seed Node

The Seed Node is not a mission-critical component, but is important
for any planned maintenance activities.

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

```
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

OpenStack provides the [instance rescue](https://docs.openstack.org/nova/latest/user/rescue.html)
service, in which an instance is temporarily booted with a clean
OS image with the original disk present as a secondary device.
This process can be instigated from the Horizon web interface,
or from the OpenStack command line:

```
openstack server rescue <seed-node>
```

Choose the same OS image that was originally used for the Seed Node
(this is the default choice on the command line).

The rescued Seed Node can be accessed using the seed-ssh script:

```
./bin/seed-ssh
```

Once access has been gained, recover the root filesystem using the
usual tools:

```
fsck -t ext4 /dev/vdb1
```

Once recovery has been completed, the Seed Node can be booted again
using the recovered root disk through an `unrescue` process, either
via Horizon or the OpenStack command line:

```
openstack server unrescue <seed-node>
```
