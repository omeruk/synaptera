#!/usr/bin/env python
"""Side-by-side comparison video (1920x1080, 30 fps): left run | right run, cameras only.

Each half: follow camera (top, 960x500) and arena with 3D trail (bottom, 960x500), time and phase label.
The right arena camera is centred on the joint bounding box of both trajectories (ground to max altitude)
and zoomed out until all of it is in view; the left keeps the default arena camera.
Same qpos replay, wing motion blur, proboscis marker, platform look (camera-only colours: yellow drop, grey
platform) and phase-dependent follow-camera angle as render_flight_video_v2.py (its Scene / FollowCam are reused;
no simulation here). Frames are streamed; plt is not used per frame.

    env -u PYTHONPATH MUJOCO_GL=egl python render_flight_compare.py <left.h5> <right.h5> [--out x.mp4]
"""
import argparse
import os
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import cv2  # noqa: E402
import imageio  # noqa: E402
import numpy as np  # noqa: E402

from render_flight_video_v2 import (BG, FINAL_LABEL, MN9_THR, PHASE_COL, PHASE_LABEL, Run, Scene,  # noqa: E402
                                    final_key)

W, H = 1920, 1080
HEAD = 80
CH = (H - HEAD) // 2          # 500 per camera
CW = W // 2


def hex_bgr(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))    # RGB (the canvas is RGB)


def put(img, txt, org, scale=0.8, color=(255, 255, 255), thick=1):
    cv2.putText(img, txt, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thick + 3, cv2.LINE_AA)
    cv2.putText(img, txt, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick, cv2.LINE_AA)


def ascii_tr(s):
    return s.translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU"))


class Side:
    def __init__(self, path):
        self.run = Run(path)
        fl = self.run.flags
        self.scene = Scene(platform="neutral" if fl.get("platform_neutral") else "dark", cam_h=CH, cam_w=CW)
        self.label = FINAL_LABEL.get(final_key(path), self.run.path.stem)
        self.t_end = float(self.run.rt[-1])
        self.fcam = self.run.follow_cam()

    def render(self, fi):
        run, b, sc = self.run, self.run.b, self.scene
        t = float(run.rt[fi])
        k = run.step_at(t)
        wings = bool(b["wings_on"][k])
        al, ar = float(b["stroke_amp_L"][k]), float(b["stroke_amp_R"][k])
        th = sc.pose(run.qpos[fi], wings)
        img_f = sc.render_follow(th, wings, al, ar, float(b["stroke_freq"][k]), proboscis=bool(b["mn9_rate"][k] > MN9_THR),
                                 view=self.fcam.view(t))
        kk = max(k, 1)
        img_w = sc.render_arena(th, b["pos"][:kk:2], b["t"][:kk:2], self.t_end)
        half = np.empty((H - HEAD, CW, 3), np.uint8)
        half[:CH] = img_f
        half[CH:] = img_w
        ph = run.phase(k)
        put(half, ascii_tr(f"phase: {PHASE_LABEL.get(ph, ph)}"), (14, 34), 0.9, hex_bgr(PHASE_COL.get(ph, "#cccccc")), 2)
        put(half, f"z {b['pos'][k][2]:5.1f} mm   food {b['dist_to_food'][k]:6.1f} mm   MN9 {b['mn9_rate'][k]:5.1f} Hz",
            (14, 70), 0.72, thick=2)
        if b["mn9_rate"][k] > MN9_THR:
            put(half, "orange = proboscis marker (visual only)", (14, CH - 14), 0.72, (255, 170, 60), 2)
        return half, t


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("left")
    ap.add_argument("right")
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--png-frames", default=None, help="comma list of frame indices: write PNGs only")
    args = ap.parse_args(argv)
    L, R = Side(args.left), Side(args.right)
    pos = np.concatenate([L.run.b["pos"], R.run.b["pos"]])
    lo, hi = pos.min(0), pos.max(0)
    lo[2] = 0.0                                              # drop lines reach the ground
    R.scene.fit_arena(lo, hi)
    print(f"right arena camera: lookat {np.round(R.scene.cam_w.lookat, 1)}, distance {R.scene.cam_w.distance:.0f} mm")
    n = min(len(L.run.rt), len(R.run.rt))
    if args.max_frames:
        n = min(n, args.max_frames)
    out = Path(args.out) if args.out else L.run.path.with_name(
        f"compare_{final_key(args.left) or 'L'}_vs_{final_key(args.right) or 'R'}.mp4")
    frames = [int(x) for x in args.png_frames.split(",")] if args.png_frames else range(n)
    writer = None if args.png_frames else imageio.get_writer(str(out), fps=L.run.fps, codec="libx264", quality=8,
                                                              macro_block_size=8)
    t0 = time.time()
    for j, fi in enumerate(frames):
        canvas = np.empty((H, W, 3), np.uint8)
        canvas[:] = BG
        hl, t = L.render(fi)
        hr, _ = R.render(fi)
        canvas[HEAD:, :CW] = hl
        canvas[HEAD:, CW:] = hr
        canvas[HEAD:, CW - 1:CW + 1] = 200
        put(canvas, f"t = {t:5.2f} s  (x{float(L.run.meta.get('play_speed', 0.25)):g})", (W // 2 - 150, 34), 0.9,
            thick=2)
        put(canvas, ascii_tr(L.label), (14, 66), 0.8, thick=2)
        put(canvas, ascii_tr(R.label), (CW + 14, 66), 0.8, thick=2)
        if writer:
            writer.append_data(canvas)
        else:
            p = out.with_name(out.stem + f"_f{fi:04d}.png")
            imageio.imwrite(p, canvas)
            print(p)
        if j % 100 == 0:
            print(f"  frame {fi}/{n}  {(time.time() - t0) / (j + 1):.2f} s/frame", flush=True)
    if writer:
        writer.close()
        print(f"video written: {out}")


if __name__ == "__main__":
    main()
