# Accessing the monitoring

As discussed in [Monitoring and alerting](../configuration/13-monitoring.md), the monitoring
dashboards are exposed as subdomains under `ingress_base_domain` and protected by a username
and password.

## Grafana

Grafana is accessed as `grafana.<ingress base domain>`, e.g. `grafana.azimuth.example.org`,
and can be used to access various dashboards showing the health of the Azimuth installation
and its underlying Kubernetes cluster. For example, there are dashboards for resource
usage, network traffic, etcd, tenant Kubernetes and CaaS clusters, Zenith services,
pod logs and systemd logs.

## Prometheus

Prometheus is accessed as `prometheus.<ingress base domain>`, and can be used to browse the
configured alerts and see which are firing or pending. It can also be used to make ad-hoc
queries of the metrics for the installation.

## Alertmanager

Alertmanager is accessed as `alertmanager.<ingress base domain>`, and can be used to manage
the firing alerts and configure silences if required.

## Kubernetes dashboard

The Kubernetes dashboard is accessed as `kubernetes.<ingress base domain>`, and can be used to
browse the current state of Kubernetes resources in the cluster. This includes streaming the
logs of current pods.

## Helm dashboard

The Helm dashboard is accessed as `helm.<ingress base domain>`, and can be used to browse the
current state of the Helm releases on the cluster. The dashboard does also attempt to infer
the health of the resources deployed by Helm, however this does sometimes report false-positives.
