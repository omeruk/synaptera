#!/usr/bin/env bash
# Smell part 2/4 (SPEC §3.4b): O1 under MODEL VARIANTS N1 then N2, one process at a time. Writes logs/smell/o1_N{1,2} and DONE_NT_O1.
cd "$(dirname "$0")/../.."
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
mkdir -p logs/smell
echo "start $(date --iso-8601=seconds)" > logs/smell/o1_nt.log
for v in N1 N2; do
  env -u PYTHONPATH $PY scripts/diag/so_o1.py --out logs/smell/o1_$v --variant $v >> logs/smell/o1_nt.log 2>&1
  echo "$v exit $?" >> logs/smell/o1_nt.log
done
date --iso-8601=seconds > logs/smell/DONE_NT_O1
