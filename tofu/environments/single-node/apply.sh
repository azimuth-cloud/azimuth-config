#!/usr/bin/env bash

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD='\033[1m'
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
DIM='\033[2m'
RESET='\033[0m'

step()  { echo -e "\n${CYAN}▶ $*${RESET}"; }
ok()    { echo -e "${GREEN}✓ $*${RESET}"; }
info()  { echo -e "${DIM}  $*${RESET}"; }
warn()  { echo -e "${YELLOW}⚠ $*${RESET}"; }
die()   { echo -e "${RED}✗ $*${RESET}" >&2; exit 1; }
dot()   { echo -n "${DIM}.${RESET}"; }

# ── Tofu provisioning ─────────────────────────────────────────────────────────
function apply_tofu() {
  step "Initialising OpenTofu"
  tofu init -upgrade

  step "Applying infrastructure (OpenStack + Talos seed + Flux bootstrap)"
  tofu apply
  ok "Tofu apply completed"
}

# ── Post-provisioning deployment ──────────────────────────────────────────────
function deploy() {
  export KUBECONFIG="$PWD/.work/kubeconfig.yaml"

  # ── cluster-overrides (phase 1 — FIP not yet known) ────────────────────────
  step "Creating cluster-overrides ConfigMap (phase 1)"
  NETWORK_ID=$(tofu output -json | jq -r ".internal_network_id.value")
  info "Workload cluster network: ${NETWORK_ID}"
  kubectl -n flux-system create configmap cluster-overrides \
    --from-literal=azimuth_cluster_flavor=cc1.large \
    --from-literal=azimuth_cluster_network_id="${NETWORK_ID}" \
    --from-literal=azimuth_cluster_base_domain=placeholder \
    --dry-run=client -o yaml \
  | kubectl apply -f -
  ok "cluster-overrides created"

  # ── Wait for CAPO CRDs and namespace ───────────────────────────────────────
  step "Waiting for CAPO to become ready"
  info "Waiting for capo-system namespace…"
  kubectl wait ns/capo-system --for=create --timeout=600s
  info "Waiting for OpenStackCluster CRD…"
  kubectl wait crds/openstackclusters.infrastructure.cluster.x-k8s.io --for=create
  ok "CAPO is ready"

  # ── Wait for workload OpenStackCluster to appear ───────────────────────────
  step "Waiting for workload cluster to be provisioned by CAPI"
  echo -n "  Waiting for azimuth-cluster object to appear "
  while ! kubectl get openstackcluster -n azimuth-cluster azimuth-cluster > /dev/null 2>&1; do
    sleep 10
    dot
  done
  echo
  info "azimuth-cluster object exists — waiting for READY=true…"
  kubectl wait openstackcluster -n azimuth-cluster azimuth-cluster \
    --for=jsonpath='{.status.ready}'=true --timeout=600s
  ok "Workload OpenStackCluster is ready"

  # ── Discover FIP and patch base domain (phase 2) ───────────────────────────
  step "Waiting for the workload cluster to be provisioned"
  while ! kubectl get openstackmachine -n azimuth-cluster -o json | jq -r ".items[0].status.ready" | grep true; do
    sleep 10
    dot
  done

  step "Discovering workload cluster floating IP"
  export KUBECONFIG=.work/kubeconfig.yaml
  FIP=$(kubectl get openstackmachine -n azimuth-cluster -o json \
    | jq -r ".items[0].status.addresses[] | select(.type == \"ExternalIP\").address")
  info "Workload node external IP: ${FIP}"
  
  info "Floating IP: ${FIP}"
  ok "Floating IP discovered: ${BOLD}${FIP}${RESET}"

  step "Patching cluster-overrides with base domain (phase 2)"
  kubectl -n flux-system patch configmap cluster-overrides \
    --type merge -p "{\"data\":{\"azimuth_cluster_base_domain\":\"${FIP}.sslip.io\"}}"
  ok "Base domain set to ${BOLD}${FIP}.sslip.io${RESET}"

  # ── Reconcile addons with the correct domain ───────────────────────────────
  step "Triggering Flux reconciliation of azimuth-cluster"
  flux -n flux-system reconcile kustomization azimuth-cluster
  ok "Flux reconciliation triggered"

  # ── Save workload cluster kubeconfig ───────────────────────────────────────
  step "Saving workload cluster kubeconfig"
  info "Waiting for kubeconfig secret to appear…"
  kubectl wait secrets -n azimuth-cluster azimuth-cluster-kubeconfig \
    --for=create --timeout=600s
  kubectl get secret -n azimuth-cluster azimuth-cluster-kubeconfig \
    -o jsonpath="{.data.value}" \
    | base64 -d > .work/azimuth.kubeconfig.yaml
  ok "Workload kubeconfig saved to .work/azimuth.kubeconfig.yaml"
  
  # ── Portal -────────────────────────────────────────────────────────────────
  step "Waiting for the Azimuth cluster to be available"
  info "Waiting for the portal to appear…"
  echo $RESET
  while ! curl -k --connect-timeout 1 "https://portal.${FIP}.sslip.io" >/dev/null 2>&1; do
    sleep 10
    dot
  done
  ok "Azimuth portal is UP."

  # ── Summary ────────────────────────────────────────────────────────────────
  echo
  echo -e "${BOLD}${GREEN}✓ Deployment complete${RESET}"
  echo -e "  Seed kubeconfig:    ${BOLD}.work/kubeconfig.yaml${RESET}"
  echo -e "  Workload kubeconfig:${BOLD}.work/azimuth.kubeconfig.yaml${RESET}"
  echo -e "  Azimuth portal:     ${BOLD}https://portal.${FIP}.sslip.io${RESET}"
}

# ── Entrypoint ─────────────────────────────────────────────────────────────────
echo -e "${BOLD}Azimuth single-node deployment${RESET}"
echo -e "${DIM}$(date -u '+%Y-%m-%d %H:%M:%S UTC')${RESET}"

if ! openstack server list > /dev/null 2>&1; then
  die "OpenStack credentials are not loaded (run: source openrc.sh)"
fi
ok "OpenStack credentials are valid"

apply_tofu
deploy