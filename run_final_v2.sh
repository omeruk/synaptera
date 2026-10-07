#!/usr/bin/env bash
# Final-v2 (SPEC_SENSORY_INPUTS §3.3c): input set sB = --vision-boundary --no-olfaction, DNp15 reference
# data/dn_lr_reference_sB.json, leg ramps (default). Full brain (not DEV), seed 3, 300 steps, no video.
#   DNP15=active  (validation passed):  (a) final_v2a --hybrid
#                                       (b) final_v2b --hybrid --ablate-dn DNp15
#                                       (c) final_v2c brain only
#   DNP15=ablated (validation failed):  (a) final_v2a --hybrid --ablate-dn DNp15
#                                       (b) skipped (a is already ablated)
#                                       (c) final_v2c brain only --ablate-dn DNp15
# Start (detached):
#   DNP15=ablated nohup bash run_final_v2.sh > logs/final_v2/nohup.out 2>&1 &
# Progress: tail -f logs/final_v2/final_v2a.log ; finished runs: ls logs/final_v2/DONE_*
# Wait without pgrep -f:  while kill -0 "$(cat logs/final_v2/run_final_v2.pid)" 2>/dev/null; do sleep 60; done
# Per run: logs/final_v2/<name>.log (+ /usr/bin/time -v), marker DONE_<name> (exit, HDF5, peak RSS).
set -u
cd "$(dirname "$0")"
export MUJOCO_GL=egl
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
SEED=${SEED:-3}
N_STEPS=${N_STEPS:-300}
DNP15=${DNP15:?set DNP15=active or DNP15=ablated}
LOG=logs/final_v2
mkdir -p "$LOG"
echo $$ > "$LOG/run_final_v2.pid"
rm -f "$LOG"/DONE_final_v2a "$LOG"/DONE_final_v2b "$LOG"/DONE_final_v2c "$LOG"/DONE_ALL

run() {   # run <name> <extra args...>
    local name=$1; shift
    local log="$LOG/$name.log"
    echo "[$(date '+%F %T')] start $name: $*" | tee -a "$LOG/run_final_v2.out"
    env -u PYTHONPATH /usr/bin/time -v "$PY" fly_flight_brain_body_simulation.py \
        --seed "$SEED" --n-steps "$N_STEPS" --vision-boundary --no-olfaction \
        --dn-reference data/dn_lr_reference_sB.json --no-video --tag "$name" "$@" > "$log" 2>&1
    local rc=$?
    local h5 rss
    h5=$(grep -o 'HDF5 written: [^ ]*' "$log" | tail -1 | cut -d' ' -f3)
    rss=$(grep 'Maximum resident set size' "$log" | awk '{print $NF}')
    printf 'exit=%s\nh5=%s\npeak_rss_kb=%s\nfinished=%s\n' "$rc" "$h5" "$rss" "$(date '+%F %T')" > "$LOG/DONE_$name"
    echo "[$(date '+%F %T')] end $name: exit $rc, peak RSS ${rss:-?} kB, $h5" | tee -a "$LOG/run_final_v2.out"
}

case "$DNP15" in
    active)
        run final_v2a --hybrid
        run final_v2b --hybrid --ablate-dn DNp15
        run final_v2c ;;
    ablated)
        run final_v2a --hybrid --ablate-dn DNp15
        echo "final_v2b skipped: final_v2a is already ablated" | tee -a "$LOG/run_final_v2.out"
        run final_v2c --ablate-dn DNp15 ;;
    *) echo "DNP15 must be active or ablated"; exit 2 ;;
esac
date '+%F %T' > "$LOG/DONE_ALL"
rm -f "$LOG/run_final_v2.pid"
