"""README previews (GIF) and stills (PNG) cut from the existing *_en_vis.mp4 videos. No simulation, no re-render.

    env -u PYTHONPATH python scripts/make_media.py [--only gifs|stills] [--dry]

Moments are computed from the HDF5 run records (phase codes, platform contact, MN9, tower contact), never guessed.
Video frame j shows: j < TITLE_S*fps: title card; then render frame frames[j - TITLE_S*fps], with the frame list of
render_flight_video_v2.py (all frames up to FEED_SLOW_S after feeding onset at x0.25, then every FEED_SKIP-th frame).
The compare video uses the frame list of its first run (n1).
Output: media/preview_*.gif, media/stills/*.png and media/stills/stills.csv (the chosen moments).
"""
import argparse
import csv
import subprocess
import sys
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "simulations"
OUT = ROOT / "media"
V_N1 = SIM / "flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change_en_vis.mp4"
V_N2 = SIM / "flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change_en_vis.mp4"
V_CMP = SIM / "flight_n1_vs_n2_v2_compare_en_vis.mp4"
H_N1 = SIM / "flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_data.h5"
H_N2 = SIM / "flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_data.h5"
FPS, TITLE_S, FEED_SLOW_S, FEED_SKIP, PLAY = 30, 6.0, 1.0, 4, 0.25   # = render_flight_video_v2.py
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


class Rec:
    def __init__(self, path):
        with h5py.File(path, "r") as f:
            b = f["behavior"]
            self.t, self.phase = b["t"][:], b["phase"][:]
            self.pos, self.mn9 = b["pos"][:], b["mn9_rate"][:]
            self.feed, self.tower = b["is_feeding"][:], b["tower_contact"][:]
            self.rt = f["render/t"][:]
            self.codes = {v: k for k, v in __import__("json").loads(b["phase"].attrs["codes"]).items()}
        feed = np.flatnonzero(self.feed > 0)
        n = len(self.rt)
        if len(feed):
            self.t_fast = float(self.t[feed[0]]) + FEED_SLOW_S
            i0 = int(np.searchsorted(self.rt, self.t_fast - 1e-9))
            self.frames = np.r_[np.arange(i0), np.arange(i0, n, FEED_SKIP)]
        else:
            self.t_fast, self.frames = None, np.arange(n)

    def step_first(self, name):
        return int(np.flatnonzero(self.phase == {v: k for k, v in self.codes.items()}[name])[0])

    def vframe(self, t_sim):
        """Video frame index of the render frame for run time t_sim (step in progress: (t[k-1], t[k]])."""
        fi = int(np.searchsorted(self.rt, t_sim - 1e-9))
        j = int(np.searchsorted(self.frames, fi))
        return int(TITLE_S * FPS) + min(j, len(self.frames) - 1)

    def sim_of(self, j):
        return float(self.rt[self.frames[j - int(TITLE_S * FPS)]])


def run(cmd):
    print(" ".join(str(c) for c in cmd)[:240])
    subprocess.run(cmd, check=True)


LAYOUT_STACK = ("[0:v]{pre},split=2[a][b];"                                   # n1 / n2 videos: brain panels on top, camera + arena below
                "[a]drawbox=x=1318:y=346:w=52:h=30:color=black:t=fill,crop=1370:380:0:0,scale={w}:-2:flags=lanczos[top];"          # frontal + dorsal panels incl. header and class legend (no neuropil bars, no circuit boxes; the first letters of the neuropil label that reach into the crop are painted black)
                "[b]delogo=x=832:y=648:w=130:h=36,crop=1920:330:0:600,scale={w}:-2:flags=lanczos[bot];"   # follow camera + arena (no graph strip); the video's own speed label is removed
                "[top][bot]vstack")
LAYOUT_FULL = "[0:v]{pre},scale={w}:-2:flags=lanczos"                              # compare video: its own layout (brain only as a thumbnail), whole frame


def gif(src, j0, j1, speed, width, fps, out, label, layout, colors=256, dither="sierra2_4a"):
    """Frames j0..j1 of src, played `speed` times faster, layout crop(s), a caption bar below, palettegen/paletteuse."""
    bar = 30
    txt = OUT / "_caption.txt"                      # textfile: no filter-escaping of ':' or ','
    txt.write_text(label)
    pre = f"trim=start_frame={j0}:end_frame={j1 + 1},setpts=(PTS-STARTPTS)/{speed},fps={fps}"
    g = (layout.format(pre=pre, w=width) + f",pad=iw:ih+{bar}:0:0:black,"
         f"drawtext=fontfile={FONT}:textfile={txt}:fontcolor=white:fontsize=14:x=8:y=h-{bar}+8")
    pal = OUT / "_palette.png"
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", g + f",palettegen=max_colors={colors}:stats_mode=full", pal])
    run(["ffmpeg", "-v", "error", "-y", "-fflags", "+bitexact", "-i", src, "-i", pal, "-map_metadata", "-1",
         "-filter_complex", g + f"[x];[x][1:v]paletteuse=dither={dither}", "-loop", "0", "-flags", "+bitexact", out])
    pal.unlink()
    txt.unlink()


def still(src, j, out, crop=None):
    vf = f"select=eq(n\\,{j})" + (f",crop={crop}" if crop else "") + ",scale=1280:-2:flags=lanczos"
    run(["ffmpeg", "-v", "error", "-y", "-fflags", "+bitexact", "-i", src, "-vf", vf, "-frames:v", "1", "-map_metadata", "-1",
         "-flags", "+bitexact", out])


def plan():
    n1, n2 = Rec(H_N1), Rec(H_N2)
    k_td, k_to = n1.step_first("touchdown"), n1.step_first("takeoff")
    k_ap = n1.step_first("approach")
    mid = int(np.flatnonzero((n1.phase == {v: k for k, v in n1.codes.items()}["cruise"]) & (n1.pos[:, 0] >= 240))[0])  # between towers (x 200..280)
    k_feed = int(np.flatnonzero(n1.feed > 0)[0])
    k_hi = int(np.flatnonzero((n1.mn9 > 50) & (n1.feed > 0))[0])        # MN9 well above threshold, still in the x0.25 part
    k_n2 = int(np.flatnonzero(n2.tower > 0)[0])
    T = lambda r, k: float(r.t[k]) - 0.0125   # middle of the step: (t[k-1], t[k]]
    stills = [  # name, video, record, sim time, crop, description
        ("takeoff", V_N1, n1, T(n1, k_to + 6), None, "n1 take-off (phase 'takeoff', step %d)" % (k_to + 6)),
        ("cruise_between_towers", V_N1, n1, T(n1, mid), None, "n1 cruise, first step with x >= 240 mm (towers at x 160-200 and 280-320 mm)"),
        ("approach", V_N1, n1, T(n1, k_ap + 6), None, "n1 approach (phase 'approach', 6 steps after its start)"),
        ("touchdown", V_N1, n1, T(n1, k_td), None, "n1 touchdown step (phase 'touchdown', first feeding step)"),
        ("feeding_mn9_circuit", V_N1, n1, T(n1, k_hi), None, "n1 feeding, first step with MN9 > 50 Hz (x0.25 part)"),
        ("brain_panel_feeding", V_N1, n1, T(n1, k_hi), "BRAIN", "frontal and dorsal brain panels cropped from the same frame"),
        ("n2_first_tower_contact", V_N2, n2, T(n2, k_n2), None, "n2 first step with tower contact (step %d)" % k_n2),
        ("compare_view", V_CMP, n1, T(n1, k_td + 8), None, "compare video, 8 steps after n1 touchdown (n2 stays at the tower)"),
    ]
    return n1, n2, stills, dict(k_td=k_td, k_ap=k_ap, k_n2=k_n2, k_to=k_to)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=("gifs", "stills"))
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--brain-crop", default="1370:380:0:0")
    ap.add_argument("--gif-fps", type=int, default=15)
    ap.add_argument("--gif-width", type=int, default=900)
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    (OUT / "stills").mkdir(exist_ok=True)
    n1, n2, stills, k = plan()
    rows = []
    for name, vid, rec, t, crop, desc in stills:
        j = rec.vframe(t)
        rows.append((name, vid.name, j, round(rec.sim_of(j), 4), round(j / FPS, 3), desc))
        print(rows[-1])
        if not a.dry and a.only != "gifs":
            still(str(vid), j, str(OUT / "stills" / f"{name}.png"), a.brain_crop if crop == "BRAIN" else None)
    if not a.dry and a.only != "gifs":
        with open(OUT / "stills" / "stills.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["still", "video", "video_frame", "sim_time_s", "video_time_s", "moment"])
            w.writerows(rows)
    # GIF windows (sim seconds)
    t_n1 = (float(n1.t[k["k_to"]]) - 0.025, n1.t_fast)             # take-off .. end of the x0.25 feeding part
    t_n2 = (0.35, 2.15)
    t_cmp = (0.35, 2.55)
    spec = [("preview_n1", V_N1, n1, t_n1, 1.5, "n1 | hand-made route, brain feeding decision | playback x0.375", LAYOUT_STACK, 9.5e6),
            ("preview_n2", V_N2, n2, t_n2, 1.0, "n2 | brain only, hand-made flight programme | playback x0.25", LAYOUT_STACK, 6e6),
            ("preview_compare", V_CMP, n1, t_cmp, 1.0, "n1 vs n2 | playback x0.25", LAYOUT_FULL, 8e6)]
    for name, vid, rec, (ta, tb), sp, label, layout, limit in spec:
        j0, j1 = rec.vframe(ta), rec.vframe(tb)
        print(name, "sim", ta, tb, "frames", j0, j1, "video s", (j1 - j0 + 1) / FPS, "gif s", (j1 - j0 + 1) / FPS / sp)
        if a.dry or a.only == "stills":
            continue
        out = OUT / f"{name}.gif"
        for fps, width in ((a.gif_fps, a.gif_width), (12, a.gif_width), (12, 840)):   # size cascade: frame rate first, then width
            gif(str(vid), j0, j1, sp, width, fps, str(out), label, layout)
            size = out.stat().st_size
            print(f"{name}: {fps} fps, {width} px -> {size / 1e6:.2f} MB (limit {limit / 1e6:.1f} MB)")
            if size <= limit:
                break


if __name__ == "__main__":
    sys.exit(main())
