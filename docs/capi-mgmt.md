# Standalone CAPI Management Cluster

## Background

In recent years, the Kubernetes
[Cluster API (CAPI)](https://cluster-api.sigs.k8s.io) project has gained
adoption as a standard tool for declarative management of Kubernetes clusters on
a variety of (cloud and non-cloud) infrastructure providers. The
[Cluster API Provider OpenStack (CAPO)](https://cluster-api-openstack.sigs.k8s.io)
allows the same declarative tooling to be used for OpenStack-based Kubernetes
Clusters. [Recent innovations](https://stackhpc.com/magnum-clusterapi.html) in
the OpenStack Magnum project have allowed Magnum users to also leverage the
power of Cluster API.

Since Azimuth already uses Cluster API to provide it's Kubernetes functionality,
any Azimuth deployment is also a fully functioning
[CAPI management cluster](https://cluster-api.sigs.k8s.io/user/concepts#management-cluster)
(albeit with some additional components installed on top, such as
[Zenith](https://github.com/azimuth-cloud/zenith) and the Azimuth interface
itself). It is therefore possible (and encouraged) to re-use this management
cluster for other Cluster API services, such as interfacing with the
[Magnum CAPI Helm driver](https://opendev.org/openstack/magnum-capi-helm).

Alternatively, for operators who only require a CAPI management cluster but do
not want or need a full Azimuth deployment, the Azimuth Ansible deployment
tooling provides a stripped-down config environment to deploy only the core CAPI
components. The remainder of this document will outline how to use
azimuth-config to deploy an Azimuth-free, standalone CAPI management cluster
(e.g. for use with the Magnum CAPI Helm driver). For OpenStack operators using
OpenStack Kayobe, a companion guide for deploying the Magnum CAPI Helm driver
and configuring it to use the deployed CAPI management cluster can be found
[here](https://stackhpc-kayobe-config.readthedocs.io/en/stackhpc-2025.1/configuration/magnum-capi.html).

## OpenStack Prerequisites

The OpenStack prerequisites are largely the same as those for a full Azimuth
deployment, as described [here](./configuration/01-prerequisites.md), with the
following differences:

### Networking

([Main documentation](./configuration/01-prerequisites.md#networking))

The only networking requirement is that there is a network path between the CAPI
management cluster and the API server load balancer IP for each workload
clusters. This is achievable by either deploying all clusters on a
single tenant network shared between all OpenStack projects, or by ensuring all
tenant clusters use a load balancer with a public IP for their API server
(relevant CAPO docs
[here](https://cluster-api-openstack.sigs.k8s.io/clusteropenstack/configuration#api-server-floating-ip)).

A further constraint when driving Cluster API from Magnum is that the Magnum
conductor must be able to reach the management cluster's Kubernetes API server.
This can also be achieved either using public IPs or a routed VLAN provider
network in OpenStack which is attached to both the OpenStack control plane (for
the Magnum conductor) and available as an OpenStack tenant network (for
management cluster VMs).

### OpenStack project quotas

([Main documentation](./configuration/01-prerequisites/#openstack-project-quotas))

Floating IPs are not required for the ingress controller or the Zenith SSHD
server (since these are not deployed by default in the CAPI-only scenario). A
single floating IP for the seed node is still required unless suitable overrides
for the relevant
[infra variables](https://github.com/azimuth-cloud/ansible-collection-azimuth-ops/blob/main/roles/infra/defaults/main.yml)
are defined.

If the management cluster's API server is exposed using a public IP then
additional floating IP quota will be required.

### Wildcard DNS

([Main documentation](./configuration/01-prerequisites/#wildcard-dns))

Since a standalone CAPI management cluster deployment does not include Azimuth
or Zenith, a DNS entry is not required.

## Kubernetes configuration

All of the Kubernetes configuration options prefixed with `capi_cluster_` in the
main Azimuth [documentation section](./configuration/03-kubernetes-config.md)
are applicable to a standalone CAPI management cluster deployment.

However, a full Azimuth deployment uses the
[Azimuth CAPI operator](https://github.com/azimuth-cloud/azimuth-capi-operator/)
as a wrapper around Cluster API to provide additional functionality to workload
clusters. Since this operator is not part of the Kubernetes Cluster API project,
it is not deployed in the standalone CAPI management case. This means that all
variables in the referenced Kubernetes configuration documentation which are
prefixed with `azimuth_capi_operator_` will have no effect. All functionality
provided by the Azimuth CAPI operator-specific variables can instead be
configured directly in Cluster API on a per-workload-cluster basis.

## Monitoring and Alerting

Just like standard Azimuth deployments, a standalone CAPI management cluster is
deployed with standard monitoring tools, including
[Prometheus](https://prometheus.io/) for metric collection,
[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) for
alert generation based on those metrics and
[Loki](https://grafana.com/docs/loki/latest/) for log aggregation.

All sections of the [main documentation](./configuration/14-monitoring.md) are
applicable to a standalone CAPI management cluster deployment apart from the
'Accessing web interfaces' section. In the CAPI-only case, since there is no
ingress controller and no [wildcard DNS](#wildcard-dns) entry, the monitoring
and alerting services are only accessible from within the management cluster.
However, a
[convenience script](https://github.com/azimuth-cloud/azimuth-config/blob/stable/bin/port-forward)
is provided to allow access to the services via a combination of kubectl
port-forwarding and SSH tunnelling. After activating the appropriate config
environment, the script can be used from the repository root with

```bash
./bin/port-forward <service-name> <local-port>
```

So, for example, `./bin/port-forward grafana 3000` would make the CAPI
management cluster's Grafana instance accessible on your laptop at
`http://localhost:3000`. The list of service which can be port-forwarded can be
found
[here](https://github.com/azimuth-cloud/azimuth-config/blob/0592b6ea2bd01e5e4fec390e3e668f351d185f53/bin/port-forward#L32-L80)

## Disaster Recovery

Any production-ready CAPI management cluster should have a robust disaster
recovery solution. The Azimuth documentation on
[disaster recovery](./configuration/15-disaster-recovery) is directly applicable
to CAPI-only deployments and allows relevant CAPI Kubernetes resources to be
periodically backed up to an external S3 bucket. An Ansible playbook is also
provided in the event of an operator needing to
[restore from a backup](./configuration/15-disaster-recovery/#restoring-from-a-backup).
The sole difference between Azimuth and CAPI-only backups is that Azimuth
includes some Cinder volume snapshots as part of each backup, whereas all CAPI
states are stored in Kubernetes API resources, so Velero will only take an S3
backup of resource manifests and avoid creating any Cinder snapshots.
