#!/usr/bin/env bash
# Multi-seed repeat (SPEC_SENSORY_INPUTS §3.3e): the n1/n2 commands of run_natural.sh unchanged, only --seed and --tag
# change (n1_s<seed>, n2_s<seed>). Full brain (not DEV), 300 steps, no video. One run at a time.
# Start (detached):  nohup bash run_seeds.sh > logs/seeds/nohup.out 2>&1 &
# Progress: tail -f logs/seeds/run_seeds.out ; finished runs: ls logs/seeds/DONE_*
# Wait without pgrep -f:  while kill -0 "$(cat logs/seeds/run_seeds.pid)" 2>/dev/null; do sleep 60; done
set -u
cd "$(dirname "$0")"
export MUJOCO_GL=egl
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
SEEDS=${SEEDS:-"10 11 12 13 14"}
N_STEPS=${N_STEPS:-300}
LOG=logs/seeds
mkdir -p "$LOG"
echo $$ > "$LOG/run_seeds.pid"
rm -f "$LOG"/DONE_*

run() {   # run <seed> <tag> <extra args...>
    local seed=$1 name=$2; shift 2
    local log="$LOG/$name.log"
    echo "[$(date '+%F %T')] start $name (seed $seed): $*" | tee -a "$LOG/run_seeds.out"
    env -u PYTHONPATH /usr/bin/time -v "$PY" fly_flight_brain_body_simulation.py \
        --seed "$seed" --n-steps "$N_STEPS" --vision-boundary --no-olfaction \
        --dn-reference data/dn_lr_reference_sB.json --no-brain-steer --head-reflex --postures \
        --no-video --tag "$name" "$@" > "$log" 2>&1
    local rc=$?
    local h5 rss badq
    h5=$(grep -o 'HDF5 written: [^ ]*' "$log" | tail -1 | cut -d' ' -f3)
    rss=$(grep 'Maximum resident set size' "$log" | awk '{print $NF}')
    badq=$(grep -c 'BADQACC' "$log")
    printf 'exit=%s\nseed=%s\nh5=%s\npeak_rss_kb=%s\nbadqacc_warnings=%s\nfinished=%s\n' "$rc" "$seed" "$h5" "$rss" \
        "$badq" "$(date '+%F %T')" > "$LOG/DONE_$name"
    echo "[$(date '+%F %T')] end $name: exit $rc, peak RSS ${rss:-?} kB, BADQACC lines $badq, $h5" | tee -a "$LOG/run_seeds.out"
}

for s in $SEEDS; do
    run "$s" "n1_s$s" --hybrid
    run "$s" "n2_s$s"
done
date '+%F %T' > "$LOG/DONE_ALL"
rm -f "$LOG/run_seeds.pid"
