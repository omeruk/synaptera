#!/usr/bin/env bash
# v2 videos from the final HDF5 files (no simulation). Two chains in parallel (~1 GB RSS each):
#   chain 1: render_flight_video_v2.py final_a, final_b, final_c (change mode)
#   chain 2: render_flight_compare.py final_a | final_c
# Start: nohup bash run_videos_v2.sh > logs/videos_v2/nohup.out 2>&1 &
# Markers: logs/videos_v2/DONE_<name> (exit code, output), DONE_ALL when both chains end.
set -u
cd "$(dirname "$0")"
export MUJOCO_GL=egl
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
LOG=logs/videos_v2
mkdir -p "$LOG"
echo $$ > "$LOG/run_videos_v2.pid"
rm -f "$LOG"/DONE_*
h5() { grep '^h5=' "logs/final/DONE_$1" | cut -d= -f2; }

one() {   # one <name> <cmd...>
    local name=$1; shift
    env -u PYTHONPATH /usr/bin/time -v "$@" > "$LOG/$name.log" 2>&1
    local rc=$?
    printf 'exit=%s\nout=%s\nfinished=%s\n' "$rc" "$(grep -o 'video written: .*' "$LOG/$name.log" | cut -d' ' -f3)" \
        "$(date '+%F %T')" > "$LOG/DONE_$name"
}

(
    for r in final_a final_b final_c; do
        one "video_$r" "$PY" render_flight_video_v2.py "$(h5 $r)"
    done
) &
p1=$!
(
    one compare_a_c "$PY" render_flight_compare.py "$(h5 final_a)" "$(h5 final_c)" \
        --out simulations/compare_final_a_vs_final_c.mp4
) &
p2=$!
wait $p1 $p2
date '+%F %T' > "$LOG/DONE_ALL"
