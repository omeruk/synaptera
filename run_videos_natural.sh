#!/usr/bin/env bash
# Final videos of the naturalness runs (render only, no simulation): n1 full, n2 full, n1 | n2 side by side.
# Start (detached):  nohup bash run_videos_natural.sh > logs/video_v2n/nohup.out 2>&1 &
# Finished: ls logs/video_v2n/DONE_* ; wait without pgrep -f:
#   while kill -0 "$(cat logs/video_v2n/run_videos.pid)" 2>/dev/null; do sleep 60; done
set -u
cd "$(dirname "$0")"
export MUJOCO_GL=egl
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
LOG=logs/video_v2n
mkdir -p "$LOG"
echo $$ > "$LOG/run_videos.pid"
rm -f "$LOG"/DONE_video_*
N1=$(grep '^h5=' logs/natural/DONE_n1 | cut -d= -f2)
N2=$(grep '^h5=' logs/natural/DONE_n2 | cut -d= -f2)
CMP=simulations/flight_n1_vs_n2_v2_compare.mp4

vid() {   # vid <name> <args...>
    local name=$1; shift
    env -u PYTHONPATH /usr/bin/time -v "$PY" render_flight_video_v2.py "$@" > "$LOG/$name.log" 2>&1
    local rc=$?
    printf 'exit=%s\nvideo=%s\npeak_rss_kb=%s\nfinished=%s\n' "$rc" \
        "$(grep -o 'video written: .*' "$LOG/$name.log" | cut -d' ' -f3)" \
        "$(grep 'Maximum resident set size' "$LOG/$name.log" | awk '{print $NF}')" "$(date '+%F %T')" \
        > "$LOG/DONE_video_$name"
}

vid n1 "$N1" &
vid n2 "$N2" &
vid compare "$N1" --compare "$N2" --out "$CMP" &
wait
date '+%F %T' > "$LOG/DONE_video_ALL"
rm -f "$LOG/run_videos.pid"
