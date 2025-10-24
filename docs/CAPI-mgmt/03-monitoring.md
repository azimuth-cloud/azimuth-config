# Monitoring and alerting

Just like standard Azimuth installations, CAPI management clusters are deployed with a
monitoring and alert stack, including [Prometheus](https://prometheus.io/) for metric collection
and [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) for alert generation
based on those metrics.

The monitoring stack is installed during the CAPI management cluster's deployment when the
[`provision_capi_mgmt`](https://github.com/azimuth-cloud/ansible-collection-azimuth-ops/blob/main/playbooks/provision_capi_mgmt.yml)
playbook, imports the `provision_cluster` playbook which, in turn, is responsible for calling
the [`kube_prometheus_stack` role](https://github.com/azimuth-cloud/ansible-collection-azimuth-ops/tree/main/roles/kube_prometheus_stack).

Apart from aforementioned monitoring services, there are also log aggregate services,
[Loki](https://grafana.com/oss/loki/) and [Promtail](https://grafana.com/docs/loki/latest/clients/promtail/),deployed as part of the stack. Further components of the deployed monitoring stack are covered in Azimuth's
[monitoring documents](../configuration/14-monitoring.md#monitoring-and-alerting).

## Accessing web interfaces

The monitoring and alerting web dashboards are currently exposed via the use of this
port-forwarding [script](https://github.com/azimuth-cloud/azimuth-config/blob/devel/bin/port-forward).
Once run, the various services will be available on the CAPI management cluster's floating
IP under the service subdomains. The following services are exposed:

- `grafana` for the Grafana dashboards
- `prometheus` for the Prometheus web interface
- `alertmanager` for the Alertmanager web interface
- `consul` for the Consul UI
- `ara` for the ARA web interface
- `helm` for the Helm dashboard
- `kubernetes` for the Kubernetes dashboard

The dashboards are protected by a username and password (using
[HTTP Basic Auth](https://en.wikipedia.org/wiki/Basic_access_authentication)).
The username is `admin` and a strong password must be set in your configuration:

```yaml title="environments/my-site/inventory/group_vars/all/secrets.yml"
admin_dashboard_ingress_basic_auth_password: "<secure password>"
```

<!-- prettier-ignore-start -->
!!! tip
    azimuth-config includes a utility for generating secrets for an environment:
    ```sh
    ./bin/generate-secrets [--force] <environment-name>
    ```

!!! danger
    This password should be kept secret. If you want to keep the password in Git - which is recommended - then it must be encrypted.
    See [secrets](../repository/secrets.md).
<!-- prettier-ignore-end -->

## Persistence and retention

<!-- prettier-ignore-start -->
!!! note
    Persistence is only configured for HA deployments.
<!-- prettier-ignore-end -->

By default, HA installations configure Prometheus, Alertmanager and Loki to use persistent volumes in order
for metrics, alert state (e.g. silences) and logs to persist across pod restarts.

As such, it is important to consider, due to the vast amount of storage that monitoring data and logs
are capable of consuming, how much storage is going to be dedicated to storing it (volume size), in
addition to, how long should the data be kept before it is discarded (retention period).
The variables controlling these for Alertmanager, Prometheus and Loki are shown below alongside
their default values:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
# Alertmanager retention and volume size
capi_cluster_addons_monitoring_alertmanager_retention: 168h
capi_cluster_addons_monitoring_alertmanager_volume_size: 10Gi

# Prometheus retention and volume size
capi_cluster_addons_monitoring_prometheus_retention: 90d
capi_cluster_addons_monitoring_prometheus_volume_size: 10Gi

# Loki retention and volume size
capi_cluster_addons_monitoring_loki_retention: 744h
capi_cluster_addons_monitoring_loki_volume_size: 10Gi
```

<!-- prettier-ignore-start -->
!!! danger
    Volumes can only be **increased** in size. Any attempt to reduce the size of a volume will be rejected.
<!-- prettier-ignore-end -->

## Slack alerts

If your organisation uses [Slack](https://slack.com/), it is possible to configure Alertmanager to send
condition-based alerts to a Slack channel using [Incoming Webhooks](https://api.slack.com/messaging/webhooks).

<!-- prettier-ignore-start -->
!!! danger
    The webhook URL should be kept secret. If you want to keep it in Git - which is recommended - then it must be encrypted.
    See [secrets](../repository/secrets.md).
<!-- prettier-ignore-end -->

The instructions on how to enable Slack alerts can be found in Azimuth's own Slack alerts
[documentation](../configuration/14-monitoring.md#slack-alerts).
