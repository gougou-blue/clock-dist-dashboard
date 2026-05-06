#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

cd "$REPO_ROOT"

: "${PROJ_ARCHIVE:=/nfs/site/disks/nwp_arc_proj_archive/}"
: "${PYTHON_BIN:=python3}"

export PROJ_ARCHIVE

OUTPUT_PATH=${1:-public/data/latest.json}

"$PYTHON_BIN" -m dashboard.main \
  --scan-mcss-release-tree \
  --output "$OUTPUT_PATH"

"$PYTHON_BIN" scripts/summarize_dashboard_payload.py "$OUTPUT_PATH"
