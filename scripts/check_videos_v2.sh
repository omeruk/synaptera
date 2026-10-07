#!/usr/bin/env bash
# ffprobe duration / frame count / size for each v2 video + 3 PNG frames each (plots/flight/v2_video_frames/).
# Usage: bash scripts/check_videos_v2.sh video1.mp4 [video2.mp4 ...]
set -u
OUT=plots/flight/v2_video_frames
mkdir -p "$OUT"
for v in "$@"; do
    [ -f "$v" ] || { echo "missing: $v"; continue; }
    info=$(ffprobe -v error -select_streams v:0 -count_frames \
        -show_entries stream=width,height,r_frame_rate,nb_read_frames -show_entries format=duration -of csv=p=0 "$v" | tr '\n' ' ')
    echo "$(basename "$v"): width,height,fps,frames / duration = $info"
    stem=$(basename "$v" .mp4)
    for ts in 2.0 15.0 25.0; do     # title card ends at 3 s; sim frames 3-33 s
        ffmpeg -v error -y -ss "$ts" -i "$v" -frames:v 1 "$OUT/${stem}_at${ts}s.png"
        echo "  $OUT/${stem}_at${ts}s.png"
    done
done
