# Accessing the monitoring

As discussed in [Monitoring and alerting](../configuration/14-monitoring.md), the monitoring
dashboards are exposed as subdomains under `ingress_base_domain` and protected by a username
and password.
These are the administrator interfaces for the cluster hosting Azimuth.
Use the HTTP Basic Auth credentials set by the deployment operator.
The username defaults to `admin`; the password is set in `admin_dashboard_ingress_basic_auth_password` and has no default.
An OpenStack application credential or an Azimuth portal login does not grant access to these interfaces.
If you do not manage the installation, ask its operator for access.

If monitoring is enabled for your platform, use its service link in the portal and the [platform identity](../configuration/07-platform-identity.md) login.

## Grafana

Grafana is accessed as `grafana.<ingress base domain>`, e.g. `grafana.azimuth.example.org`,
and can be used to access various dashboards showing the health of the Azimuth installation
and its underlying Kubernetes cluster.
For example, there are dashboards for resource usage, network traffic, etcd, tenant Kubernetes and CaaS clusters, and Zenith services.
HA installations also provide dashboards for pod and systemd logs collected by Loki.
The single node monitoring stack does not include this log aggregation by default.

## Prometheus

Prometheus is accessed as `prometheus.<ingress base domain>`, and can be used to browse the
configured alerts and see which are firing or pending. It can also be used to make ad-hoc
queries of the metrics for the installation.

## Alertmanager

Alertmanager is accessed as `alertmanager.<ingress base domain>`, and can be used to manage
the firing alerts and configure silences if required.

## Helm dashboard

The Helm dashboard is accessed as `helm.<ingress base domain>`, and can be used to browse the
current state of the Helm releases on the cluster.
Write actions are disabled by default.
The dashboard also attempts to infer the health of the resources deployed by Helm, but it sometimes reports false positives.

## ARA

When CaaS is enabled, ARA is accessed as `ara.<ingress base domain>`.
It shows the recorded Ansible runs for CaaS appliances, including task results and failures.
See [Debugging Cluster-as-a-Service](caas.md) for further checks.

## Kubernetes resources

The Kubernetes Dashboard is no longer installed on the management cluster.
Use [kubectl](access-k3s.md) or [K9s](using-k9s.md) to inspect resources and pod logs.
For an HA installation, [target the HA cluster](access-ha.md) that hosts Azimuth.

Headlamp is an optional dashboard for tenant Kubernetes clusters.
When enabled for a cluster, it is available through that cluster's service links in the Azimuth portal.
It is not a management dashboard at `kubernetes.<ingress base domain>`.
