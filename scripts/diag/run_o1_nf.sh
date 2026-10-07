#!/usr/bin/env bash
# Smell comparison check (SPEC §3.4c): upstream-style olfactory drive, 5 seeds, one process. Writes logs/smell/o1_nf and DONE_NF_RUN.
cd "$(dirname "$0")/../.."
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
mkdir -p logs/smell
echo "start $(date --iso-8601=seconds)" > logs/smell/o1_nf.log
env -u PYTHONPATH $PY scripts/diag/so_o1_nf.py --out logs/smell/o1_nf >> logs/smell/o1_nf.log 2>&1
echo "exit $?" >> logs/smell/o1_nf.log
date --iso-8601=seconds > logs/smell/DONE_NF_RUN
