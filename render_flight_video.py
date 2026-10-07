#!/usr/bin/env python
"""HDF5 -> 1920x1280 flight video (qpos replay; no simulation here).

Layout
    top    1920x640  brain: frontal soma projection of every neuron, spike glow
                     (tau 80 ms, updated incrementally; one float32 vector)
    bottom 2 x 960x640
           (1) close follow camera (~8 mm behind/above the fly, follows yaw)
           (2) wide fixed arena camera; the 2.5 mm fly is drawn as a render-only
               marker (scene geom, no physics) with its trail

The recorded qpos is replayed into the same FlyGym model. Wings have no joints
in the model and no dynamics in the simulation (forces are stroke-averaged):
they are flapped here only visually by rotating the wing bodies (body_quat) with
the recorded stroke amplitudes; the apparent flap rate is not 218 Hz.

Memory: every frame is streamed with writer.append_data, then plt.close(fig);
no frame list is kept. Run with `env -u PYTHONPATH` and MUJOCO_GL=egl.

    python render_flight_video.py simulations/flight_v9_smoke_data.h5 --max-frames 30
"""
import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import h5py  # noqa: E402
import imageio  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mujoco  # noqa: E402
import numpy as np  # noqa: E402

from flight import config as cfg  # noqa: E402
from flight.body import FlightBody  # noqa: E402

W, H = 1920, 1280
PW, PH = 960, 640                 # bottom panels
BRAIN_H = 640
GLOW_TAU = 0.08                   # s
FLAP_CYCLES_PER_FRAME = 0.37      # visual only (218 Hz cannot be shown at 30 fps)
BG = np.array([11, 13, 18], np.uint8)

# Brain-panel colours (RGB) for the input/output groups; everything else "hot".
GROUP_COLORS = {
    "olf": (90, 220, 120), "vis": (90, 160, 255), "ascending": (255, 150, 50),
    "dn": (255, 70, 70), "sez": (230, 90, 230), "brain_mn": (230, 90, 230),
}
OTHER_COLOR = (255, 225, 140)


def group_color_table(n, groups):
    col = np.tile(np.array(OTHER_COLOR, np.float32), (n, 1))
    for name, idx in groups.items():
        key = next((k for k in GROUP_COLORS if name.startswith(k)), None)
        if key and not name.startswith(("dng02", "dnp01")):
            col[idx] = GROUP_COLORS[key]
    return col


class BrainPanel:
    """Rasterised frontal projection; each neuron is a 2x2 px dot."""

    def __init__(self, x, z, idx, n, groups, w=W, h=BRAIN_H, margin=24):
        sx = (w - 2 * margin) / (x.max() - x.min())
        sz = (h - 2 * margin) / (z.max() - z.min())
        s = min(sx, sz)
        ox = (w - s * (x.max() - x.min())) / 2
        oz = (h - s * (z.max() - z.min())) / 2
        self.px = np.clip((ox + s * (x - x.min())).astype(int), 0, w - 2)
        self.py = np.clip((h - 1 - oz - s * (z - z.min())).astype(int), 0, h - 2)
        self.idx = idx
        self.w, self.h = w, h
        self.col = group_color_table(n, groups)[idx]
        bg = np.empty((h, w, 3), np.uint8)
        bg[:] = BG
        for dy in (0, 1):
            for dx in (0, 1):
                bg[self.py + dy, self.px + dx] = (48, 52, 62)
        self.bg = bg

    def image(self, glow):
        img = self.bg.copy()
        a = np.clip(glow[self.idx], 0.0, 1.0)
        on = a > 0.03
        if on.any():
            c = (self.col[on] * a[on, None]).astype(np.uint8)
            flat = img.reshape(-1, 3)
            for dy in (0, 1):
                for dx in (0, 1):
                    lin = (self.py[on] + dy) * self.w + self.px[on] + dx
                    for ch in range(3):
                        np.maximum.at(flat[:, ch], lin, c[:, ch])
        return img


def add_sphere(scn, pos, r, rgba):
    if scn.ngeom >= scn.maxgeom:
        return
    mujoco.mjv_initGeom(scn.geoms[scn.ngeom], mujoco.mjtGeom.mjGEOM_SPHERE, np.array([r, 0, 0]),
                        np.asarray(pos, float), np.eye(3).ravel(), np.asarray(rgba, np.float32))
    scn.ngeom += 1


def add_segment(scn, a, b, width, rgba):
    if scn.ngeom >= scn.maxgeom or np.linalg.norm(np.subtract(b, a)) < 1e-6:
        return
    g = scn.geoms[scn.ngeom]
    mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_CAPSULE, np.zeros(3), np.zeros(3), np.eye(3).ravel(),
                        np.asarray(rgba, np.float32))
    mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_CAPSULE, width, np.asarray(a, float), np.asarray(b, float))
    scn.ngeom += 1


def quat_z(deg):
    h = np.radians(deg) / 2
    return np.array([np.cos(h), 0.0, 0.0, np.sin(h)])


def video_path(h5):
    h5 = Path(h5)
    return h5.with_name(h5.name.replace("_data.h5", "_video.mp4"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("h5")
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--start-frame", type=int, default=0, help="for quick checks; glow starts empty")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else video_path(args.h5)

    f = h5py.File(args.h5, "r")
    meta = {k: f["meta"].attrs[k] for k in f["meta"].attrs}
    fps = int(meta.get("fps", 30))
    calib_t = float(meta["calib_steps"]) * float(meta["decision_interval"])   # spikes: brain clock
    dev = bool(meta.get("dev_subnet", False))
    b = {k: f["behavior"][k][:] for k in ("t", "phase", "speed", "dist_to_food", "pos", "stroke_amp_L",
                                           "stroke_amp_R", "turn_odor", "turn_dn", "turn_loom",
                                           "is_feeding", "sez_out_rate")}
    codes = {v: k for k, v in json.loads(f["behavior/phase"].attrs["codes"]).items()}
    rt = f["render/t"][:]
    f0 = args.start_frame
    nfr = len(rt) - f0 if args.max_frames is None else min(len(rt) - f0, args.max_frames)
    spk_t = f["spikes/all/t"][:]
    spk_i = f["spikes/all/i"][:]
    groups = {k: f["spikes/groups"][k][:] for k in f["spikes/groups"]}
    pos = {k: f["positions"][k][:] for k in ("x", "z", "idx")}
    n = int(max(spk_i.max(initial=0), pos["idx"].max(), max(g.max(initial=0) for g in groups.values()))) + 1
    brain = BrainPanel(pos["x"], pos["z"], pos["idx"], n, groups)
    glow = np.zeros(n, np.float32)

    body = FlightBody(legs="stand")
    m, d = body.m, body.d
    name = body.fly.name
    wing = {s: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{name}/{s}Wing") for s in "LR"}
    wing_rest = {s: m.body_quat[wing[s]].copy() for s in "LR"}
    renderer = mujoco.Renderer(m, PH, PW)
    cam_f = mujoco.MjvCamera()
    cam_f.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam_f.distance, cam_f.elevation = 8.0, -18.0
    cam_w = mujoco.MjvCamera()
    cam_w.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam_w.lookat[:] = (230.0, 90.0, 70.0)
    cam_w.distance, cam_w.azimuth, cam_w.elevation = 760.0, 90.0, -38.0   # from the south
    trail = []
    az = None

    print(f"render {nfr} frames -> {out}")
    writer = imageio.get_writer(str(out), fps=fps, codec="libx264", quality=8, macro_block_size=16)
    q_ds = f["render/qpos"]
    s0 = int(np.searchsorted(spk_t, rt[f0] + calib_t - 1.0 / fps, side="right"))
    t_prev = rt[f0] - 1.0 / fps
    for fi in range(f0, f0 + nfr):
        t = rt[fi]
        k = int(np.clip(np.searchsorted(b["t"], t + 1e-9), 0, len(b["t"]) - 1))   # decision in progress
        # spikes: incremental glow (brain clock = run clock + calibration)
        s1 = int(np.searchsorted(spk_t, t + calib_t, side="right"))
        glow *= np.float32(np.exp(-(t - t_prev) / GLOW_TAU))
        if s1 > s0:
            glow += np.bincount(spk_i[s0:s1], minlength=n).astype(np.float32)
        s0, t_prev = s1, t

        # body: qpos replay + visual wing flapping
        d.qpos[:] = q_ds[fi]
        d.qvel[:] = 0.0
        phase = codes.get(int(b["phase"][k]), "?")
        flying = phase in ("takeoff", "cruise", "approach")
        for s, sign in (("L", 1.0), ("R", -1.0)):
            if flying:
                amp = b["stroke_amp_L" if s == "L" else "stroke_amp_R"][k]
                ang = 0.5 * amp * np.sin(2 * np.pi * FLAP_CYCLES_PER_FRAME * fi)
                m.body_quat[wing[s]] = quat_z(sign * ang)
            else:
                m.body_quat[wing[s]] = wing_rest[s]
        mujoco.mj_forward(m, d)
        th = d.xpos[body.thorax].copy()
        R = d.xmat[body.thorax].reshape(3, 3)
        head = np.degrees(np.arctan2(R[1, 0], R[0, 0]))
        az = head if az is None else az + 0.2 * (((head - az) + 180) % 360 - 180)
        if not trail or np.linalg.norm(th - trail[-1]) > 2.0:
            trail.append(th)

        cam_f.lookat[:] = th
        cam_f.azimuth = az
        renderer.update_scene(d, camera=cam_f)
        img_f = renderer.render().copy()
        renderer.update_scene(d, camera=cam_w)
        scn = renderer.scene
        for a_, b_ in zip(trail[:-1], trail[1:]):
            add_segment(scn, a_, b_, 1.2, (1.0, 0.85, 0.2, 0.9))
        add_segment(scn, trail[-1], th, 1.2, (1.0, 0.85, 0.2, 0.9))
        add_sphere(scn, th, 5.0, (1.0, 0.2, 0.2, 1.0))
        add_sphere(scn, cfg.FOOD_POS + np.array([0, 0, 3.0]), 3.0, (1.0, 0.8, 0.1, 1.0))
        img_w = renderer.render().copy()

        fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
        fig.patch.set_facecolor(BG / 255)
        ax = fig.add_axes([0, 0.5, 1, 0.5])
        ax.imshow(brain.image(glow), interpolation="nearest")
        ax.set_axis_off()
        title = "NeuroFly flight: FlyWire v783 LIF brain + FlyGym body, closed loop"
        if dev:
            title += "   [DEV subnet: NOT a result]"
        ax.text(0.01, 0.97, title, transform=ax.transAxes, color="w", fontsize=15, va="top")
        ax.text(0.01, 0.90, f"t = {t:6.3f} s   phase: {phase}", transform=ax.transAxes, color="w",
                fontsize=13, va="top", family="monospace")
        ax.text(0.01, 0.05, "spikes (glow 80 ms)  ", transform=ax.transAxes, color="#bbbbbb", fontsize=11,
                bbox=dict(facecolor=BG / 255, alpha=0.8, lw=0))
        for j, (lab, c) in enumerate((("olfactory", "olf"), ("LA>ME (vision)", "vis"), ("ascending", "ascending"),
                                      ("descending", "dn"), ("SEZ in/out", "sez"), ("other", None))):
            rgb = np.array(GROUP_COLORS.get(c, OTHER_COLOR)) / 255
            ax.text(0.13 + 0.085 * j, 0.05, "■ " + lab, transform=ax.transAxes, color=rgb, fontsize=11,
                    bbox=dict(facecolor=BG / 255, alpha=0.8, lw=0))
        for rect, img, lab in (([0, 0, 0.5, 0.5], img_f, "close follow"),
                               ([0.5, 0, 0.5, 0.5], img_w, "arena (fly = red marker, render only)")):
            a2 = fig.add_axes(rect)
            a2.imshow(img)
            a2.set_axis_off()
            a2.text(0.015, 0.97, lab, transform=a2.transAxes, color="w", fontsize=12, va="top",
                    bbox=dict(facecolor="black", alpha=0.45, lw=0))
        p = b["pos"][k]
        info = (f"speed {b['speed'][k]:5.0f} mm/s   z {p[2]:5.1f} mm   food {b['dist_to_food'][k]:5.1f} mm\n"
                f"turn: odor {b['turn_odor'][k]:+.2f}  DN {b['turn_dn'][k]:+.3f}  loom {b['turn_loom'][k]:+.3f}\n"
                f"SEZ out (brain_mn) {b['sez_out_rate'][k]:5.1f} Hz")
        fig.text(0.51, 0.025, info, color="w", fontsize=11, family="monospace",
                 bbox=dict(facecolor="black", alpha=0.5, lw=0))
        fig.text(0.01, 0.012, "wings flapped for display only (stroke-averaged aero); haltere reflex, "
                 "odor maps, landing trigger: hand-made", color="#cccccc", fontsize=10,
                 bbox=dict(facecolor="black", alpha=0.5, lw=0))
        fig.canvas.draw()
        writer.append_data(np.asarray(fig.canvas.buffer_rgba())[..., :3])
        plt.close(fig)
        if (fi - f0) % 50 == 0:
            print(f"  frame {fi}/{nfr} t={t:.3f}s [{phase}]")
    writer.close()
    renderer.close()
    f.close()
    print(f"video written: {out}")
    return out


if __name__ == "__main__":
    main()
