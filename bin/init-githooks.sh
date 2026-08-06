#!/bin/bash

ROOT_DIR=$(git rev-parse --show-toplevel)

ln "${ROOT_DIR}"/bin/pre-commit-hook.sh "${ROOT_DIR}"/.git/hooks/pre-commit
