# Debugging Cluster-as-a-Service

In order to debug issues with CaaS deployments, it is often useful to access the AWX UI.

Similar to the monitoring, this interface is only accessible inside the cluster. To
access it, use the following command:

```sh
./bin/port-forward awx 8052
```

The AWX UI will then be available at <http://localhost:8052>.

Sign in to AWX as the `admin` user with the password that you set in
[Configuring CaaS](../configuration/11-caas.md#awx-admin-password).

Once inside, you can look at the details of the recently executed jobs, check that
the inventories look correct and check the permissions assigned to teams.

!!! tip

    You can also make changes in the AWX UI that will be reflected in the cluster types
    and clusters available in Azimuth.

    However make sure you know what you are doing!
