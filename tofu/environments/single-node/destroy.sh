#!/usr/bin/env bash

set -euo pipefail

# ── Colours (same as apply.sh) ────────────────────────────────────────────────
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

SEED_KUBECONFIG=".work/kubeconfig.yaml"
WORKLOAD_KUBECONFIG=".work/azimuth.kubeconfig.yaml"

kseed()     { KUBECONFIG="$SEED_KUBECONFIG"     kubectl "$@"; }
kworkload() { KUBECONFIG="$WORKLOAD_KUBECONFIG" kubectl "$@"; }

echo -e "${BOLD}Azimuth single-node destroy${RESET}"
echo -e "${DIM}$(date -u '+%Y-%m-%d %H:%M:%S UTC')${RESET}"

# ── Guard: OpenStack credentials ──────────────────────────────────────────────
if ! openstack server list > /dev/null 2>&1; then
  die "OpenStack credentials not loaded — run: source <openrc.sh>"
fi
ok "OpenStack credentials valid"

# ── 2. Suspend Flux to prevent re-creation during teardown ───────────────────
step "Suspending Flux kustomizations"
if [[ -f "$SEED_KUBECONFIG" ]] && kseed cluster-info > /dev/null 2>&1; then
  if kseed get kustomization -n flux-system azimuth-cluster > /dev/null 2>&1; then
    kseed patch kustomization -n flux-system azimuth-cluster \
      --type=merge -p '{"spec":{"suspend":true}}'
    info "azimuth-cluster kustomization suspended"
  fi
  ok "Flux suspended"
else
  warn "Seed cluster unreachable — Flux suspension skipped"
fi

# ── 3. Destroy Namespaces containing PVCs ─────────────────────────────────────
step "Destroying namespaces"
for ns in $(kworkload get pvc -o json -A | jq -r ".items[].metadata.namespace" | sort -u); do
    kworkload delete ns --wait $ns
done

# ── 4. Delete CAPI workload cluster ───────────────────────────────────────────
step "Deleting CAPI workload cluster"
if [[ -f "$SEED_KUBECONFIG" ]] && kseed get cluster -n azimuth-cluster azimuth-cluster > /dev/null 2>&1; then
  info "Deleting Cluster/azimuth-cluster (timeout 600s)…"
  kseed delete cluster -n azimuth-cluster azimuth-cluster --wait --timeout=600s
  ok "CAPI cluster deleted"
else
  info "CAPI cluster not found — skipping"
fi

# ── 5. Destroy OpenStack infrastructure ───────────────────────────────────────
step "Destroying OpenStack infrastructure with OpenTofu"
tofu destroy


# ── 6. Local file cleanup ─────────────────────────────────────────────────────
step "Cleaning up local files"
rm -f "$SEED_KUBECONFIG" ".work/talosconfig" "$WORKLOAD_KUBECONFIG"
ok "Local files removed"

echo -e "\n${BOLD}${GREEN}✓ Destroy complete${RESET}"
