#!/usr/bin/env bash
# "Honest hybrid final" (SPEC_BRAIN_CONTROL.md): three runs, one after the other, same seed and n_steps.
#   (a) final_a  --hybrid
#   (b) final_b  --hybrid --ablate-dn DNp15
#   (c) final_c  brain only (v10 brainonly160 settings)
# All: full brain (not DEV), --no-olfaction, seed 3, 300 steps, no video in the simulation process.
# Videos are rendered from the HDF5 files after all three simulations have finished.
#
# Start (detached, survives the terminal):
#   mkdir -p logs/final && nohup bash run_final.sh > logs/final/nohup.out 2>&1 &
# Progress: tail -f logs/final/final_a.log ; finished runs: ls logs/final/DONE_*
# Wait without pgrep -f:  while kill -0 "$(cat logs/final/run_final.pid)" 2>/dev/null; do sleep 60; done
#
# Per run: logs/final/<name>.log (simulation output + /usr/bin/time -v, "Maximum resident set size" = peak RSS),
# marker logs/final/DONE_<name> (exit code, HDF5 path, peak RSS) written when the run ends (also on failure).
set -u
cd "$(dirname "$0")"
export MUJOCO_GL=egl
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
SEED=${SEED:-3}
N_STEPS=${N_STEPS:-300}
LOG=logs/final
mkdir -p "$LOG"
echo $$ > "$LOG/run_final.pid"
rm -f "$LOG"/DONE_final_a "$LOG"/DONE_final_b "$LOG"/DONE_final_c "$LOG"/DONE_ALL

run() {   # run <name> <extra args...>
    local name=$1; shift
    local log="$LOG/$name.log"
    echo "[$(date '+%F %T')] start $name: $*" | tee -a "$LOG/run_final.out"
    env -u PYTHONPATH /usr/bin/time -v "$PY" fly_flight_brain_body_simulation.py \
        --seed "$SEED" --n-steps "$N_STEPS" --no-olfaction --no-video --tag "$name" "$@" > "$log" 2>&1
    local rc=$?
    local h5 rss
    h5=$(grep -o 'HDF5 written: [^ ]*' "$log" | tail -1 | cut -d' ' -f3)
    rss=$(grep 'Maximum resident set size' "$log" | awk '{print $NF}')
    printf 'exit=%s\nh5=%s\npeak_rss_kb=%s\nfinished=%s\n' "$rc" "$h5" "$rss" "$(date '+%F %T')" > "$LOG/DONE_$name"
    echo "[$(date '+%F %T')] end $name: exit $rc, peak RSS ${rss:-?} kB, $h5" | tee -a "$LOG/run_final.out"
}

run final_a --hybrid
run final_b --hybrid --ablate-dn DNp15
run final_c

# videos from the HDF5 files (qpos replay; separate processes, after all simulations)
for name in final_a final_b final_c; do
    h5=$(grep '^h5=' "$LOG/DONE_$name" | cut -d= -f2)
    if [ -n "$h5" ] && [ -f "$h5" ]; then
        env -u PYTHONPATH "$PY" render_flight_video.py "$h5" > "$LOG/${name}_video.log" 2>&1 \
            || echo "video $name failed (see $LOG/${name}_video.log)" | tee -a "$LOG/run_final.out"
    fi
done
date '+%F %T' > "$LOG/DONE_ALL"
rm -f "$LOG/run_final.pid"
