#!/bin/bash

if [[ -z "$SOPS_AGE_KEY" ]]; then
  echo "Must set SOPS_AGE_KEY env var"
  exit 1
fi

sops --age="${SOPS_AGE_KEY}" \
  --decrypt \
  --encrypted-regex '^(data|stringData)$' \
  $1
