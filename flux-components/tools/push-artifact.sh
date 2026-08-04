#!/bin/bash
set -euo pipefail

Help() {
  # Display Help
  echo "Push a directory of Flux manifests to an OCI artifact."
  echo
  echo "Syntax: push-artifact.sh <ARTIFACT_DIR> <IMAGE_URL> [TAG]"
  echo "TAG will default to 'latest' if not supplied."
  echo "options:"
  echo "d     Dry run and don't execute push command."
  echo "c     Provide a creds option to flux push artifact."
  echo "h     Print this Help."
  echo
}

DRY_RUN=FALSE
CREDS=""
while getopts "hdc:" option; do
  case $option in
    h)
      Help
      exit
      ;;
    d)
      DRY_RUN=TRUE
      ;;
    c)
      CREDS=--creds=${OPTARG}
      ;;
    \?)
      echo "Error: Invalid option -$OPTARG"
      usage
      exit 1
      ;;
    :)
      echo "Error: Option -$OPTARG requires an argument."
      usage
      exit 1
      ;;
   esac
done
shift $((OPTIND - 1))

BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
BRANCH_TAG=${BRANCH_NAME##*/}

ARTIFACT_DIR=${1}
IMAGE_URL=${2}
TAG=${3:-${BRANCH_TAG}}

if [[ ${IMAGE_URL:0:6} != oci:// ]]; then
  IMAGE_URL=oci://${IMAGE_URL}
fi

SOURCE="$(git config --get remote.origin.url)"
REV="$(git tag --points-at HEAD)@sha1:$(git rev-parse HEAD)"

echo "Pushing ${ARTIFACT_DIR} to ${IMAGE_URL}:${TAG} with source:${SOURCE} and revision:${REV}"

if [[ ${DRY_RUN} == FALSE ]]; then
  flux push artifact "${IMAGE_URL}":"${TAG}" \
      --path="${ARTIFACT_DIR}" \
      --source="${SOURCE}" \
      --revision="${REV}" \
      "${CREDS}"
else
  echo "flux push artifact ${IMAGE_URL}:${TAG} \ "
  echo "  --path=${ARTIFACT_DIR} \ "
  echo "  --source=${SOURCE} \ "
  echo "  --revision=${REV} \ "
  echo "  ${CREDS}"
fi
