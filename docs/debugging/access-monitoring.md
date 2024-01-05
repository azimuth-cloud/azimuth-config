# Accessing the monitoring

The monitoring is currently only exposed inside the cluster, so it can only be accessed using
[kubectl port-forward](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/)
from the K3S node. However because the API is not accessible to the
internet, an
[SSH local forward](https://www.ssh.com/academy/ssh/tunneling/example#local-forwarding) must
be used from your local machine to the K3S node as well.

To simplify this process, the `azimuth-config` repository contains a utility script - 
[port-forward](https://github.com/stackhpc/azimuth-config/tree/main/bin/port-forward) -
that can be used to set up the double port-forward for particular cluster services.

To view monitoring dashboards in Grafana, use the following command to expose the Grafana
interface on a local port:

```sh
./bin/port-forward grafana 3000
```

This will make the Grafana interface available at <http://localhost:3000>. Log in with the default
credentials - `admin/prom-operator` - to access the dashboards.

In order to view firing alerts or configure silences, you can also access the Prometheus and
Alertmanager interfaces using the same method:

```sh
./bin/port-forward prometheus 9090
./bin/port-forward alertmanager 9093
```

These commands will expose the Prometheus and Alertmanager interfaces at <http://localhost:9090>
and <http://localhost:9093> respectively. Both these interfaces are unauthenticated, although
you must have sufficient access to set up the port forward via the K3S node.
