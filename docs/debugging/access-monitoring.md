# Accessing the monitoring

!!! note

    The monitoring is only available for the HA deployment method.

The monitoring is currently only exposed inside the cluster, so it can only be accessed using
[kubectl port-forward](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/)
from the K3S node. However because the API is not accessible to the
internet, an
[SSH local forward](https://www.ssh.com/academy/ssh/tunneling/example#local-forwarding) must
be used from your local machine to the K3S node!

To simplify this process, the `azimuth-config` repository contains a utility script - 
[port-forward](https://github.com/stackhpc/azimuth-config/tree/main/bin/port-forward) -
that can be used to set a the double port-forward for particular cluster services.

To set up a port-forward to the [Grafana](https://grafana.com/) interface for the monitoring,
run the following command:

```sh
./bin/port-forward monitoring 8000
```

This will make the monitoring available at <http://localhost:8000>. Log in with the default
credentials - `admin/prom-operator` - to access the monitoring dashboards.
