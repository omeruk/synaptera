#!/usr/bin/env bash
# Build the data bundle and the video folder next to the repository (never deletes; DEST must not exist).
#
#   bash scripts/make_data_bundle.sh [DEST] [VIDEOS_DEST]     # default ../synaptera_data_v1 ../synaptera_videos_v1
#
# The file list comes from tracing scripts/verify_report_final.py with strace (see scripts/make_data_bundle.py); the copies are
# sanitised (absolute paths) and described by MANIFEST.tsv, SHA256SUMS and README_DATA.md.
set -euo pipefail
cd "$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
DEST=${1:-../synaptera_data_v1}
VDEST=${2:-../synaptera_videos_v1}
# PYTHON must be the interpreter of the project environment (h5py, numpy), e.g. PYTHON=$HOME/miniforge3/envs/neurofly/bin/python
exec env -u PYTHONPATH "${PYTHON:-python}" scripts/make_data_bundle.py --dest "$DEST" --videos-dest "$VDEST"
