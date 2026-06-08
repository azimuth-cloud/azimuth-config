# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**azimuth-config** is a reference GitOps configuration repository for deploying [Azimuth](https://github.com/azimuth-cloud/azimuth), an OpenStack-based cloud platform. It is designed to be forked per site. The full stack layers:

1. **OpenTofu** provisions OpenStack VMs and networks
2. **Talos Linux** boots immutable Kubernetes nodes on those VMs
3. **FluxCD** applies all Kubernetes workloads declaratively from this repo
4. **Cluster API (CAPI/CAPO)** manages downstream workload cluster lifecycle

## Common Commands

### Environment setup
```bash
source bin/activate          # activate Python venv (creates it if missing)
```

### Infrastructure (run inside the relevant tofu/environments/<env>/ directory)
```bash
tofu init
tofu plan
tofu apply
```

### Local development
```bash
bin/tilt-up                  # start Tilt; auto-discovers sibling component checkouts
bin/tilt-images-apply        # build and deploy local images into the cluster
bin/port-forward             # forward a Kubernetes service port locally
bin/kube-connect             # fetch kubeconfig for a deployed cluster
```

### Operations
```bash
bin/generate-secrets         # generate secrets for a new deployment
bin/create-debug-bundle      # collect diagnostic artifacts
bin/run-tests                # run the Robot Framework test suite
bin/check-alerts             # validate Prometheus alerting rules
```

### Linting (also runs in CI on every PR)
```bash
ansible-lint                 # Ansible role/playbook lint
yamllint .                   # YAML lint (160 char line limit, see .yamllint.yml)
actionlint                   # GitHub Actions workflow lint
```

## Architecture

### Environment Types

| Environment | Seed VM | Workload Cluster | Use Case |
|---|---|---|---|
| `all-in-one` | 1-node Talos (seed = workload) | None | Dev / demo |
| `single-node` | 1-node Talos (mgmt only) | 1-node via CAPO | Testing / staging |
| multi-node | 1-node Talos (mgmt only) | 3-node via CAPO | HA / production |

### Configuration Injection

All environments share `flux/apps/` HelmRelease manifests. Runtime values are injected into every Flux Kustomization via three Kubernetes objects:

- `cluster-config` ConfigMap — infrastructure values (domain, cloud endpoints)
- `cluster-secrets` Secret — sensitive values (passwords, tokens)
- `cluster-overrides` ConfigMap — operator-provided, cloud-specific overrides

These are created by Tofu (`tofu/modules/flux-bootstrap/`) and referenced via `spec.postBuild.substituteFrom` in each `flux/clusters/<env>/*.yaml`.

### Flux App Layering

`flux/clusters/<env>/` → `flux/apps/` (shared HelmReleases) → `flux/azimuth/` (Azimuth portal) → `flux/workload/` (CAPI workload cluster)

Each app directory under `flux/apps/` contains a `kustomization.yaml` and a `helmrelease.yaml`. Helm chart sources are defined in `flux/apps/_sources/`.

### Tofu Module Structure

- `tofu/modules/openstack-infra/` — networks, security groups, floating IPs, volumes
- `tofu/modules/talos-node/` — Talos machine configuration and Kubernetes bootstrap
- `tofu/modules/flux-bootstrap/` — installs Flux, creates GitRepository + Kustomization, writes `cluster-config`/`cluster-secrets`

### Tilt Local Development

`Tiltfile` auto-discovers sibling checkouts of component repositories (azimuth, azimuth-capi-operator, zenith, etc.) by scanning the parent directory. If a sibling checkout exists, Tilt builds its image locally and overrides the Helm release image reference. Add a `tilt-settings.yaml` to control which components are developed locally.

## Key Files to Know

| File | Purpose |
|---|---|
| `tofu/environments/<env>/main.tf` | Entry point for environment provisioning |
| `flux/clusters/<env>/azimuth.yaml` | Top-level FluxCD Kustomization for an env |
| `flux/apps/_sources/` | HelmRepository definitions (chart sources) |
| `environments/base/` | Shared Ansible inventory base |
| `.yamllint.yml` | YAML lint rules (max line length 160) |
| `.ansible-lint.yml` | Ansible lint configuration |
| `super-linter.env` | super-linter profile (JSCPD and JS Standard disabled) |

## CI/CD

GitHub Actions workflows run:
- **On PR**: `lint.yml` (ansible-lint, yamllint, super-linter, actionlint)
- **Scheduled**: `test-singlenode.yml`, `test-ha.yml`, `test-backup-restore.yml`, `test-upgrade.yml` against real OpenStack clouds
- **Release**: `publish-release.yml`, `update-dependencies.yml`

Reusable actions live in `.github/actions/` (setup, provision, test, destroy, release-notes).
