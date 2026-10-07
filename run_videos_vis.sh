#!/usr/bin/env bash
# n1 / n2 / n1 | n2 videos with the soft-dot brain panels (render only, no simulation), from the existing HDF5 files.
# New file names (*_en_vis.mp4); the earlier videos of run_videos_en.sh / run_videos_natural.sh are kept.
# Start (detached):  nohup bash run_videos_vis.sh > logs/video_vis/nohup.out 2>&1 &
# Finished: logs/video_vis/DONE_video_ALL ; wait without pgrep -f:
#   while kill -0 "$(cat logs/video_vis/run_videos.pid)" 2>/dev/null; do sleep 60; done
set -u
cd "$(dirname "$0")"
export MUJOCO_GL=egl
PY=${PY:-$HOME/miniforge3/envs/neurofly/bin/python}
LOG=logs/video_vis
mkdir -p "$LOG"
echo $$ > "$LOG/run_videos.pid"
N1=$(grep '^h5=' logs/natural/DONE_n1 | cut -d= -f2)
N2=$(grep '^h5=' logs/natural/DONE_n2 | cut -d= -f2)
OUT_N1=simulations/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change_en_vis.mp4
OUT_N2=simulations/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change_en_vis.mp4
OUT_CMP=simulations/flight_n1_vs_n2_v2_compare_en_vis.mp4

vid() {   # vid <name> <args...>
    local name=$1; shift
    env -u PYTHONPATH /usr/bin/time -v "$PY" render_flight_video_v2.py "$@" > "$LOG/$name.log" 2>&1
    local rc=$?
    printf 'exit=%s\nvideo=%s\npeak_rss_kb=%s\nfinished=%s\n' "$rc" \
        "$(grep -o 'video written: .*' "$LOG/$name.log" | cut -d' ' -f3)" \
        "$(grep 'Maximum resident set size' "$LOG/$name.log" | awk '{print $NF}')" "$(date '+%F %T')" \
        > "$LOG/DONE_video_$name"
}

vid n1 "$N1" --out "$OUT_N1" &
vid n2 "$N2" --out "$OUT_N2" &
vid compare "$N1" --compare "$N2" --out "$OUT_CMP" &
wait
date '+%F %T' > "$LOG/DONE_video_ALL"
rm -f "$LOG/run_videos.pid"
