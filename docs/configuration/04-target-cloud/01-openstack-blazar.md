# OpenStack Blazar

!!! warning  "Technology preview"

    Blazar support is currently in technology preview and under active development.

    Its possible how this feature works may radically change in a future release.

When available on the target cloud, Azimuth is able to make use of
[Blazar](https://docs.openstack.org/blazar/latest/), an OpenStack service for reserving
cloud resources. When Blazar support is enabled, Azimuth is able to create reservations
for platforms and deploy platforms into those reservations.

Currently, Azimuth is using Blazar to give users better feedback about when the cloud is full,
meaning that their platform cannot be created right now. This is a common issue with
"fixed capacity" clouds, where there is more demand for resources than available capacity.

When creating a platform, users must specify how long they need that platform for. Azimuth
translates this information, along with the parameters for the platform, into a request for
a Blazar reservation (starting now) that can accomodate the requested platform. If this is
successful then Azimuth creates the platform using the reserved resources. If it is not
successful, Azimuth reports that the cloud is not able to accomodate the platform as currently
configured and the user may try again with different parameters.

!!! info  "Future work"

    Blazar also supports creating reservations that start in the future, e.g. "can I have three
    machines of flavor X and two of flavor Y for two weeks starting tomorrow". This is useful for
    cases where it is known advance when resources will be required, and they can be reserved for
    that time. In the future, Azimuth will support creating platforms that start in the future
    using this mechanism.

## Blazar flavor plugin

Azimuth relies on the new
[Blazar flavor plugin](https://opendev.org/openstack/blazar/src/branch/master/blazar/plugins/flavor/flavor_plugin.py)
that allows resources to be reserved in Blazar using existing Nova flavors. When creating a
reservation, the required number of servers of each flavor is specified and Blazar reserves
the corresponding resources from its pool of hosts.

Azimuth does not currently support the host reservation or instance reservation plugins.

There is active work on the Blazar flavor plugin to improve the support for VMs with GPUs
attached, and to allow [Ironic](https://docs.openstack.org/ironic/latest/) bare-metal nodes
to be added as possible flavor reservation targets.

Currently, Azimuth only supports the case where all projects are able to access all configured
Nova flavors via Blazar.

For more information on Blazar, and how to add hosts into Blazar's control, please see the
[Blazar documentation](https://docs.openstack.org/blazar/latest/cli/flavor-based-instance-reservation.html).

## Coral Credits

Blazar has support for
[delegating to an external service](https://docs.openstack.org/blazar/latest/admin/usage-enforcement.html#externalservicefilter)
to determine whether a reservation is permitted.

[Coral Credits](https://github.com/stackhpc/coral-credits) is a new open-source service for
facilitating sharing of resources using credit allocations. It implements the API required
for Blazar to call out to it, allowing the creation of Blazar reservations to be constrained
by the available credits for a project.

Coral Credits can be deployed as part of an Azimuth installation using the following:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
coral_credits_enabled: yes
```

For Details on how to configure Blazar to use Coral Credits as an enforcement plugin, and how
to configure the credit allocations for each OpenStack project, see the
[Coral Credits documentation](https://github.com/stackhpc/coral-credits/blob/main/README.md#blazar-configuration).

## Azimuth configuration

To enable "time-limited" platforms in Azimuth, i.e. platforms that are automatically deleted
at a specified time in the future, set the following variable:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_scheduling_enabled: true
```

When this variable is set, Azimuth users will be required to specify an end time for any
platforms that they create.

!!! warning  "Platforms cannot be extended"

    Currently, Azimuth does **not** support extending the end time for a platform.

By default, this **does not** use Blazar reservations - Azimuth just ensures that the platform is
deleted at the requested time. This is still useful to help to prevent resource squatting on clouds
where Blazar is not available. However platforms can still encounter issues when the cloud is full
because the resources are not reserved for the platform as they are in Blazar.

To tell Azimuth to create Blazar reservations for platforms, set the following variable:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_schedule_operator_blazar_enabled: true
```

When this variable is set, Azimuth will attempt to create a Blazar lease for each platform. If
the creation of the Blazar lease fails, Azimuth will report whether the problem was due to cloud
capacity or being limited by credits. If the Blazar lease is created successfully, Azimuth will
create the platform using the reserved resources.
