#!/usr/bin/env bash
# Vision screen (SPEC §3.5). Stages, one at a time, detached by the caller:
#   run_vd.sh render | discovery | validation | null
# Each stage writes logs/vis_dn/<stage>.log and a DONE_<STAGE> marker (with exit code) in logs/vis_dn.
cd "$(dirname "$0")/../.."
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
export MUJOCO_GL=egl
D=logs/vis_dn; mkdir -p $D
stage=$1
case $stage in
  render)     CMD="scripts/diag/vd_render.py --out $D" ;;
  discovery)  CMD="scripts/diag/vd_run.py --rates $D/vd_rates.npz --out $D/main --seeds 501 502 503 --tag DISC" ;;
  validation) CMD="scripts/diag/vd_run.py --rates $D/vd_rates.npz --out $D/main --seeds 601 602 603 604 605 --tag VAL" ;;
  null)       CMD="scripts/diag/vd_run.py --rates $D/vd_rates.npz --out $D/null --seeds 801 802 803 804 805 --null --tag NULL" ;;
  *) echo "usage: $0 render|discovery|validation|null"; exit 2 ;;
esac
echo "start $(date --iso-8601=seconds)" > $D/$stage.log
env -u PYTHONPATH $PY $CMD >> $D/$stage.log 2>&1
echo "exit $?" >> $D/$stage.log
date --iso-8601=seconds > $D/DONE_STAGE_$stage
