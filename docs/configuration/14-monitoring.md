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

In addition to the monitoring and alerting stack, several additional dashboards are installed:

  * The [Kubernetes dashboard](https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/)
    for browsing the current state of Kubernetes resources.
  * The [Helm dashboard](https://github.com/komodorio/helm-dashboard) for browsing the current
    state of Helm releases.
  * The [Consul UI](https://developer.hashicorp.com/consul/tutorials/certification-associate-tutorials/get-started-explore-the-ui)
    for browsing the Consul state (used by Cluster-as-a-Service and Zenith).
  * The [ARA Records Ansible (ARA)](https://ara.recordsansible.org/) web interface for browsing the
    Ansible playbook runs that have been recorded for operations on Cluster-as-a-Service appliances.

All the dashboards that access Kubernetes resources are configured to be read-only.

## Accessing web interfaces

The monitoring and alerting web dashboards are exposed as subdomains under the `ingress_base_domain`:

  * `grafana` for the Grafana dashboards
  * `prometheus` for the Prometheus web interface
  * `alertmanager` for the Alertmanager web interface
  * `consul` for the Consul UI
  * `ara` for the ARA web interface
  * `helm` for the Helm dashboard
  * `kubernetes` for the Kubernetes dashboard

The dashboards are protected by a username and password (using
[HTTP Basic Auth](https://en.wikipedia.org/wiki/Basic_access_authentication)).
The username is `admin` and a strong password must be set in your configuration:

```yaml  title="environments/my-site/inventory/group_vars/all/secrets.yml"
admin_dashboard_ingress_basic_auth_password: "<secure password>"
```

!!! warning  "Sensitive information"

    The dashboards allow read-only access to the internals of your Azimuth installation.
    As such you should ensure that a strong password is used, and take care when sharing
    it.

!!! tip

    `azimuth-config` includes a utility for generating secrets for an environment:

    ```sh
    ./bin/generate-secrets [--force] <environment-name>
    ```

!!! danger

    This password should be kept secret. If you want to keep the password in Git - which is
    recommended - then it [must be encrypted](../repository/secrets.md).

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
