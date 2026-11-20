# Monitoring and alerting

Azimuth installations come with a monitoring and alerting stack that uses [Prometheus](https://prometheus.io/) to collect metrics on various components of the Kubernetes cluster and the Azimuth components running on it, and to evaluate alert rules.
[Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) routes alert notifications and [Grafana](https://grafana.com/) visualises the metrics using a curated set of dashboards.

For OpenStack deployments, this stack runs on the K3s node in a single node installation, or on the HA cluster in an HA installation.
In [standalone mode](17-standalone-mode.md), monitoring is optional and is installed when `deploy_prometheus_stack: true` is set.

HA installations also include a log aggregation stack using [Loki](https://grafana.com/oss/loki/) and [Promtail](https://grafana.com/docs/loki/latest/send-data/promtail/) that collects logs from all the pods running on the HA cluster and the systemd services on each cluster node.
These logs are available in a dashboard in Grafana, where they can be filtered and searched.

The current HA defaults still use Promtail, which [reached end of life on 2 March 2026](https://grafana.com/docs/loki/latest/send-data/promtail/).
Grafana provides a [migration guide for Alloy](https://grafana.com/docs/loki/latest/setup/migrate/migrate-to-alloy/).

In addition to the monitoring and alerting stack, several additional dashboards are installed:

- The [Helm dashboard](https://github.com/komodorio/helm-dashboard) for browsing the current
  state of Helm releases.
  Write actions are disabled by default.
- The [ARA Records Ansible (ARA)](https://ara.recordsansible.org/) web interface for browsing the Ansible playbook runs that have been recorded for operations on Cluster-as-a-Service appliances, when CaaS is enabled.

The Kubernetes Dashboard is no longer installed on the management cluster.
Use [kubectl](../debugging/access-k3s.md) or [K9s](../debugging/using-k9s.md) to inspect its resources; for HA installations, [target the HA cluster](../debugging/access-ha.md).
Tenant Kubernetes clusters can use the optional Headlamp dashboard, accessed through their service links in the Azimuth portal.

## Accessing web interfaces

These interfaces are for the people operating the Azimuth installation.
Monitoring services exposed by individual platforms use [platform identity](07-platform-identity.md) instead.

The monitoring and alerting web dashboards are exposed as subdomains under the `ingress_base_domain` by default:

- `grafana` for the Grafana dashboards
- `prometheus` for the Prometheus web interface
- `alertmanager` for the Alertmanager web interface
- `ara` for the ARA web interface, when CaaS is enabled
- `helm` for the Helm dashboard

The dashboards are protected by a username and password (using
[HTTP Basic Auth](https://en.wikipedia.org/wiki/Basic_access_authentication)).
These credentials are separate from the OpenStack or OIDC credentials used to sign in to the Azimuth portal.
The default username is `admin`, configured by `admin_dashboard_ingress_basic_auth_username`.
Set a strong password in your configuration:

```yaml title="environments/my-site/inventory/group_vars/all/secrets.yml"
admin_dashboard_ingress_basic_auth_password: "<secure password>"
```

<!-- prettier-ignore-start -->
!!! warning "Sensitive information"
    These interfaces expose installation details, logs and administrative functions, such as creating Alertmanager silences.
    Use a strong password and restrict access to these interfaces.

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
    Persistent storage for Prometheus, Alertmanager and Loki is configured by default for HA deployments.
    The single node monitoring stack does not configure it by default.
<!-- prettier-ignore-end -->

In order for metrics, alert state (e.g. silences) and logs to persist across pod restarts,
we must configure Prometheus, Alertmanager and Loki to use persistent volumes to store
their data.

This is configured by default in an Azimuth HA installation, but you may wish to tweak the
retention periods and/or volume sizes based on your requirements and/or observed usage.

The following variables, shown with their default values, control the retention periods and
volume sizes for Alertmanager, Prometheus and Loki:

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

If your organisation uses [Slack](https://slack.com/), Alertmanager can be configured to send
alerts to a Slack channel using an [Incoming Webhook](https://api.slack.com/messaging/webhooks).

To enable Slack alerts, you must first
[create a webhook](https://api.slack.com/messaging/webhooks#create_a_webhook). This should
result in a URL of the form:

```text
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX #gitleaks:allow
```

This URL should be placed in the following variable to allow Azimuth's Alertmanager to send
alerts to Slack:

```yaml title="environments/my-site/inventory/group_vars/all/secrets.yml"
alertmanager_config_slack_webhook_url: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX #gitleaks:allow
```

To send critical and warning severity alerts to different Slack channels (different webhooks) extra configuration can be provided:

```yaml
alertmanager_config_slack_critical_webhook_url: https://...
alertmanager_config_slack_warning_webhook_url: https://...
```

The routing rules depend on the presence of the webhooks, details below:

| Default webhook | Critical webhook | Warning webhook | Critical messages      | Warning messages      |
| --------------- | ---------------- | --------------- | ---------------------- | --------------------- |
| -               | x                | x               | Go to critical channel | Go to warning channel |
| x               | -                | x               | Go to default channel  | Go to warning channel |
| x               | x                | -               | Go to critical channel | Go to default channel |
| x               | -                | -               | Go to default channel  | Go to default channel |
| -               | x                | -               | Config not deployed    | Config not deployed   |
| -               | -                | x               | Config not deployed    | Config not deployed   |

<!-- prettier-ignore-start -->
!!! danger
    The webhook URL should be kept secret. If you want to keep it in Git - which is recommended - then it must be encrypted.
    See [secrets](../repository/secrets.md).
<!-- prettier-ignore-end -->
