#!/usr/bin/env bash
# R0: Shiu et al. sugar GRN -> MN9 conditions (two parallel chains). Run from an output directory.
D="$(cd "$(dirname "$0")" && pwd)"
P="env -u PYTHONPATH $HOME/miniforge3/envs/neurofly/bin/python $D/r0_sugar.py"
( $P 630 shiu 100 5; $P 630 shiu 200 5; $P 783 shiu 200 5; $P 783 shiu 50 5 ) > r0_a.log 2>&1 &
( $P 783 shiu 100 5; $P 783 flight 100 5; $P 783 sezgroup 150 3; $P 783 shiu 20 3 ) > r0_b.log 2>&1 &
wait
