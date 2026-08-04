# Migration Notes

This deploys the [Kube-Prometheus-Stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
Helm chart with a small set of Azimuth-default overrides.
These overrides were lifted directly from the ansible playbooks so there should
be minimal migrations work, any Helm chart overrides set as user ansible
variables should be deployed into a `configMap` called
`kube-prometheus-stack-values` in the `monitoring-system` namespace.

## Migration of dashboards

The deployment automatically scrapes all namespaces for configMaps that are
labelled with `grafana_dashboard: "1"`.
Deploy the dashboard `configMap` into the namespace that it relates to as a
JSON map and add the label.
