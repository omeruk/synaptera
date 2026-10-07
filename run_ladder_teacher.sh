#!/usr/bin/env bash
# Training ladder, round 1 (SPEC_SENSORY_INPUTS §3.6): the n1 teacher flights from the 16 training/validation starts
# (ids 1-16 of the §3.6 table), n1 command of run_starts.sh with --start-offset/--start-yaw and --record-readout.
# Exam starts 17-22 are NOT in this script. One flight at a time, detached, DONE marker per flight.
# Start (detached):  nohup bash run_ladder_teacher.sh > logs/ladder/teacher/nohup.out 2>&1 &
# Wait without pgrep -f:  while kill -0 "$(cat logs/ladder/teacher/run.pid)" 2>/dev/null; do sleep 60; done
set -u
cd "$(dirname "$0")"
export MUJOCO_GL=egl
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
N_STEPS=${N_STEPS:-300}
LOG=logs/ladder/teacher
REC=logs/ladder/teacher/records
SIM=logs/ladder/teacher/sim
mkdir -p "$LOG" "$REC" "$SIM"
echo $$ > "$LOG/run.pid"

run() {   # run <id> <dx> <dy> <yaw>
    local id=$1 dx=$2 dy=$3 yaw=$4
    local name; name=$(printf 'lt%02d' "$id")
    [ -e "$LOG/DONE_$name" ] && return 0
    local log="$LOG/$name.log"
    echo "[$(date '+%F %T')] start $name: offset $dx $dy yaw $yaw seed $((100 + id))" | tee -a "$LOG/run.out"
    env -u PYTHONPATH /usr/bin/time -v "$PY" fly_flight_brain_body_simulation.py \
        --seed $((100 + id)) --n-steps "$N_STEPS" --vision-boundary --no-olfaction \
        --dn-reference data/dn_lr_reference_sB.json --no-brain-steer --head-reflex --postures \
        --no-video --hybrid --tag "$name" --start-offset "$dx" "$dy" --start-yaw "$yaw" \
        --sim-dir "$SIM" --record-readout "$REC" > "$log" 2>&1
    local rc=$?
    local h5 rss badq
    h5=$(grep -o 'HDF5 written: [^ ]*' "$log" | tail -1 | cut -d' ' -f3)
    rss=$(grep 'Maximum resident set size' "$log" | awk '{print $NF}')
    badq=$(grep -c 'BADQACC' "$log")
    printf 'exit=%s\nid=%s\noffset=%s %s\nyaw=%s\nh5=%s\npeak_rss_kb=%s\nbadqacc_warnings=%s\nfinished=%s\n' "$rc" "$id" "$dx" "$dy" "$yaw" "$h5" "$rss" \
        "$badq" "$(date '+%F %T')" > "$LOG/DONE_$name"
    echo "[$(date '+%F %T')] end $name: exit $rc, peak RSS ${rss:-?} kB, BADQACC lines $badq, $h5" | tee -a "$LOG/run.out"
}

# SPEC §3.6 table, ids 1-16 (training 1-12, validation 13-16), order fixed
run 1 24.9 -14.2 59.3
run 2 -22.1 3.9 -34.7
run 3 7.2 -18.3 46.6
run 4 32.8 -26.8 -23.4
run 5 31.7 25.7 7.8
run 6 39.6 -37.8 47.6
run 7 7.7 -14.0 5.8
run 8 -15.5 -21.5 12.3
run 9 9.7 22.9 40.0
run 10 28.9 28.6 42.8
run 11 -17.6 -0.1 -11.6
run 12 -8.2 -38.3 -56.4
run 13 -8.1 -23.1 43.1
run 14 -29.7 -35.9 10.7
run 15 39.9 -4.7 -58.2
run 16 -35.9 28.2 46.2
echo "[$(date '+%F %T')] all 16 done" | tee -a "$LOG/run.out"
touch "$LOG/DONE_ALL"
