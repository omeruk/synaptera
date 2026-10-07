#!/usr/bin/env bash
# Training ladder round 2, trial 1, steps A and B (SPEC_SENSORY_INPUTS §3.6 + round-2 clarifications):
#   A1 audit: teacher flight 2 replayed into the published brain with its own seed; DN counts must be identical (else stop)
#   A2 the 16 teacher flights replayed into the shuffled connectome (seed 901), Brian seed 100 + id
#   B  the three readouts fitted from the 12 training flights (scripts/ladder_fit.py)
# One run at a time, detached, DONE markers. No exam start (17-22) appears here.
# Start (detached):  nohup bash run_ladder_trial1_prep.sh > logs/ladder/prep_nohup.out 2>&1 &
# Wait without pgrep -f:  while kill -0 "$(cat logs/ladder/prep.pid)" 2>/dev/null; do sleep 60; done
set -u
cd "$(dirname "$0")"
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
L=logs/ladder
mkdir -p $L/replay_audit $L/replay_shuffled $L/readouts
echo $$ > $L/prep.pid
log() { echo "[$(date '+%F %T')] $*" | tee -a $L/prep.out; }

if [ ! -e $L/replay_audit/DONE ]; then
    log "audit: flight 2 -> published brain"
    env -u PYTHONPATH $PY scripts/ladder_replay.py --id 2 --brain real --audit --out $L/replay_audit > $L/replay_audit/lt02.log 2>&1
    rc=$?
    if [ $rc -ne 0 ] || ! grep -q '"dn_identical": true' $L/replay_audit/lt02_real_replay.json 2>/dev/null; then
        log "AUDIT FAILED or crashed (exit $rc): stop, nothing else is run"
        touch $L/replay_audit/STOP
        exit 1
    fi
    echo "exit=0 finished=$(date '+%F %T')" > $L/replay_audit/DONE
    log "audit passed (DN counts identical)"
fi

for id in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16; do
    n=$(printf 'lt%02d' $id)
    [ -e $L/replay_shuffled/DONE_$n ] && continue
    log "shuffled replay $n"
    env -u PYTHONPATH /usr/bin/time -v $PY scripts/ladder_replay.py --id $id --brain shuffled --out $L/replay_shuffled > $L/replay_shuffled/$n.log 2>&1
    rc=$?
    echo "exit=$rc finished=$(date '+%F %T')" > $L/replay_shuffled/DONE_$n
    log "  $n exit $rc"
done
touch $L/replay_shuffled/DONE_ALL

log "fit trial 1"
env -u PYTHONPATH $PY scripts/ladder_fit.py > $L/readouts/fit_trial1.log 2>&1
log "fit exit $?"
touch $L/prep.DONE
