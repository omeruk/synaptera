#!/usr/bin/env bash
# Start position / heading test (SPEC_SENSORY_INPUTS §3.3f): the n1 command of run_natural.sh unchanged (seed 3, --hybrid),
# only --start-offset / --start-yaw and --tag change. Full brain (not DEV), 300 steps, no video. One run at a time.
# Start (detached):  nohup bash run_starts.sh > logs/starts/nohup.out 2>&1 &
# Progress: tail -f logs/starts/run_starts.out ; finished runs: ls logs/starts/DONE_*
# Wait without pgrep -f:  while kill -0 "$(cat logs/starts/run_starts.pid)" 2>/dev/null; do sleep 60; done
set -u
cd "$(dirname "$0")"
export MUJOCO_GL=egl
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
SEED=${SEED:-3}
N_STEPS=${N_STEPS:-300}
LOG=logs/starts
mkdir -p "$LOG"
echo $$ > "$LOG/run_starts.pid"
rm -f "$LOG"/DONE_*

run() {   # run <tag> <start args...>
    local name=$1; shift
    local log="$LOG/$name.log"
    echo "[$(date '+%F %T')] start $name: $*" | tee -a "$LOG/run_starts.out"
    env -u PYTHONPATH /usr/bin/time -v "$PY" fly_flight_brain_body_simulation.py \
        --seed "$SEED" --n-steps "$N_STEPS" --vision-boundary --no-olfaction \
        --dn-reference data/dn_lr_reference_sB.json --no-brain-steer --head-reflex --postures \
        --no-video --hybrid --tag "$name" "$@" > "$log" 2>&1
    local rc=$?
    local h5 rss badq
    h5=$(grep -o 'HDF5 written: [^ ]*' "$log" | tail -1 | cut -d' ' -f3)
    rss=$(grep 'Maximum resident set size' "$log" | awk '{print $NF}')
    badq=$(grep -c 'BADQACC' "$log")
    printf 'exit=%s\nstart=%s\nh5=%s\npeak_rss_kb=%s\nbadqacc_warnings=%s\nfinished=%s\n' "$rc" "$*" "$h5" "$rss" \
        "$badq" "$(date '+%F %T')" > "$LOG/DONE_$name"
    echo "[$(date '+%F %T')] end $name: exit $rc, peak RSS ${rss:-?} kB, BADQACC lines $badq, $h5" | tee -a "$LOG/run_starts.out"
}

# SPEC §3.3f: 8 conditions, fixed order
run st_xp40 --start-offset 40 0
run st_xm40 --start-offset -40 0
run st_yp40 --start-offset 0 40
run st_ym40 --start-offset 0 -40
run st_yawp30 --start-yaw 30
run st_yawm30 --start-yaw -30
run st_yawp60 --start-yaw 60
run st_yawm60 --start-yaw -60
date '+%F %T' > "$LOG/DONE_ALL"
rm -f "$LOG/run_starts.pid"
