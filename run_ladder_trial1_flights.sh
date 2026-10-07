#!/usr/bin/env bash
# Training ladder round 2, trial 1, step D (SPEC_SENSORY_INPUTS §3.6): the 3 trained readouts fly the 4 validation starts (13-16),
# brain seed 100 + id, order: arm real, shuffled, bypass; within an arm start 13, 14, 15, 16. n1 flags + --readout-model.
# 12 flights, one at a time, detached, DONE marker per flight. Exam starts 17-22 are NOT in this script.
# Start (detached):  nohup bash run_ladder_trial1_flights.sh > logs/ladder/trial1/nohup.out 2>&1 &
# Wait without pgrep -f:  while kill -0 "$(cat logs/ladder/trial1/run.pid)" 2>/dev/null; do sleep 60; done
set -u
cd "$(dirname "$0")"
export MUJOCO_GL=egl
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
T=logs/ladder/trial1
mkdir -p $T/records $T/sim
echo $$ > $T/run.pid

run() {   # run <arm> <id> <dx> <dy> <yaw>
    local arm=$1 id=$2 dx=$3 dy=$4 yaw=$5
    local name; name=$(printf 't1%s_v%02d' "$arm" "$id")
    [ -e "$T/DONE_$name" ] && return 0
    local extra=""
    [ "$arm" = "shuffled" ] && extra="--shuffle-seed 901"
    echo "[$(date '+%F %T')] start $name: offset $dx $dy yaw $yaw seed $((100 + id))" | tee -a $T/run.out
    env -u PYTHONPATH /usr/bin/time -v "$PY" fly_flight_brain_body_simulation.py \
        --seed $((100 + id)) --n-steps 300 --vision-boundary --no-olfaction \
        --dn-reference data/dn_lr_reference_sB.json --no-brain-steer --head-reflex --postures \
        --no-video --hybrid --tag "$name" --start-offset "$dx" "$dy" --start-yaw "$yaw" \
        --sim-dir $T/sim --record-readout $T/records --readout-model logs/ladder/readouts/trial1_$arm.npz $extra > $T/$name.log 2>&1
    local rc=$?
    local h5 rss badq
    h5=$(grep -o 'HDF5 written: [^ ]*' "$T/$name.log" | tail -1 | cut -d' ' -f3)
    rss=$(grep 'Maximum resident set size' "$T/$name.log" | awk '{print $NF}')
    badq=$(grep -c 'BADQACC' "$T/$name.log")
    printf 'exit=%s\narm=%s\nid=%s\noffset=%s %s\nyaw=%s\nh5=%s\npeak_rss_kb=%s\nbadqacc_warnings=%s\nfinished=%s\n' "$rc" "$arm" "$id" "$dx" "$dy" "$yaw" "$h5" "$rss" \
        "$badq" "$(date '+%F %T')" > "$T/DONE_$name"
    echo "[$(date '+%F %T')] end $name: exit $rc, peak RSS ${rss:-?} kB, BADQACC lines $badq, $h5" | tee -a $T/run.out
}

for arm in real shuffled bypass; do
    # SPEC §3.6 table, validation starts 13-16
    run $arm 13 -8.1 -23.1 43.1
    run $arm 14 -29.7 -35.9 10.7
    run $arm 15 39.9 -4.7 -58.2
    run $arm 16 -35.9 28.2 46.2
done
echo "[$(date '+%F %T')] all 12 done" | tee -a $T/run.out
touch $T/DONE_ALL
