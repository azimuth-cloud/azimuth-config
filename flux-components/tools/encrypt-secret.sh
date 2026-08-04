#!/bin/bash

if [[ -z "$SOPS_PUBLIC_KEY" ]]; then
  echo "Must set SOPS_PUBLIC_KEY env var"
  exit 1
fi

sops --age="${SOPS_PUBLIC_KEY}" \
  --encrypt \
  --encrypted-regex '^(data|stringData)$' \
  --in-place "$1"