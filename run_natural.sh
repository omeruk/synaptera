#!/usr/bin/env bash
# Naturalness round (SPEC_SENSORY_INPUTS §3.3d): sB + --no-brain-steer (post-hoc control) + --head-reflex + --postures.
# Full brain (not DEV), seed 3, 300 steps, no video.
#   n1: --hybrid      n2: brain only
# Start (detached):
#   nohup bash run_natural.sh > logs/natural/nohup.out 2>&1 &
# Progress: tail -f logs/natural/n1.log ; finished runs: ls logs/natural/DONE_*
# Wait without pgrep -f:  while kill -0 "$(cat logs/natural/run_natural.pid)" 2>/dev/null; do sleep 60; done
set -u
cd "$(dirname "$0")"
export MUJOCO_GL=egl
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
SEED=${SEED:-3}
N_STEPS=${N_STEPS:-300}
LOG=logs/natural
mkdir -p "$LOG"
echo $$ > "$LOG/run_natural.pid"
rm -f "$LOG"/DONE_n1 "$LOG"/DONE_n2 "$LOG"/DONE_ALL

run() {   # run <name> <extra args...>
    local name=$1; shift
    local log="$LOG/$name.log"
    echo "[$(date '+%F %T')] start $name: $*" | tee -a "$LOG/run_natural.out"
    env -u PYTHONPATH /usr/bin/time -v "$PY" fly_flight_brain_body_simulation.py \
        --seed "$SEED" --n-steps "$N_STEPS" --vision-boundary --no-olfaction \
        --dn-reference data/dn_lr_reference_sB.json --no-brain-steer --head-reflex --postures \
        --no-video --tag "$name" "$@" > "$log" 2>&1
    local rc=$?
    local h5 rss badq
    h5=$(grep -o 'HDF5 written: [^ ]*' "$log" | tail -1 | cut -d' ' -f3)
    rss=$(grep 'Maximum resident set size' "$log" | awk '{print $NF}')
    badq=$(grep -c 'BADQACC' "$log")
    printf 'exit=%s\nh5=%s\npeak_rss_kb=%s\nbadqacc_warnings=%s\nfinished=%s\n' "$rc" "$h5" "$rss" "$badq" \
        "$(date '+%F %T')" > "$LOG/DONE_$name"
    echo "[$(date '+%F %T')] end $name: exit $rc, peak RSS ${rss:-?} kB, BADQACC lines $badq, $h5" | tee -a "$LOG/run_natural.out"
}

run n1 --hybrid
run n2
date '+%F %T' > "$LOG/DONE_ALL"
rm -f "$LOG/run_natural.pid"
