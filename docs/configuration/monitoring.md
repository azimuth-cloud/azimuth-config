# Monitoring and alerting

Azimuth installations come with a monitoring and alerting stack that uses
[Prometheus](https://prometheus.io/) to collect metrics on various components of the Kubernetes
cluster and the Azimuth components running on it,
[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) to produce alerts
based on those metrics and [Grafana](https://grafana.com/) to visualise the metrics using a
curated set of dashboards.

HA installations also include a log aggregation stack using [Loki](https://grafana.com/oss/loki/)
and [Promtail](https://grafana.com/docs/loki/latest/clients/promtail/) that collects logs
from all the pods running on the cluster and the systemd services on each cluster node.
These logs are available in a dashboard in Grafana, where they can be filtered and searched.

## Persistence and retention

!!! note

    Persistence is only configured for HA deployments.

In order for metrics, alert state (e.g. silences) and logs to persist across pod restarts,
we must configure Prometheus, Alertmanager and Loki to use persistent volumes to store
their data.

This is configured by default in an Azimuth HA installation, but you may wish to tweak the
retention periods and/or volume sizes based on your requirements and/or observed usage.

The following variables, shown with their default values, control the retention periods and
volume sizes for Alertmanager, Prometheus and Loki:

```yaml  title="environments/my-site/inventory/group_vars/all/variables.yml"
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

!!! danger

    Volumes can only be **increased** in size. Any attempt to reduce the size of a volume
    will be rejected.

## Slack alerts

If your organisation uses [Slack](https://slack.com/), Alertmanager can be configured to send
alerts to a Slack channel using an [Incoming Webhook](https://api.slack.com/messaging/webhooks).

To enable Slack alerts, you must first
[create a webhook](https://api.slack.com/messaging/webhooks#create_a_webhook). This should
result in a URL of the form:

```
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
```

This URL should be placed in the following variable to allow Azimuth's Alertmanager to send
alerts to Slack:

```yaml  title="environments/my-site/inventory/group_vars/all/secrets.yml"
alertmanager_config_slack_webhook_url: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
```

!!! danger

    The webhook URL should be kept secret. If you want to keep it in Git - which is recommended -
    then it [must be encrypted](../repository/secrets.md).
