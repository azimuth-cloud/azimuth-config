#! /usr/ben/env bash

set -e

export KUBECONFIG=.work/kubeconfig.yaml
if kubectl get cluster -n azimuth-cluster azimuth-cluster > /dev/null 2>&1; then
    kubectl delete cluster -n azimuth-cluster azimuth-cluster --wait --timeout=600s
fi

tofu destroy

rm -f .work/talosconfig .work/azimuth.kubeconfig.yaml .work/kubeconfig.yaml
