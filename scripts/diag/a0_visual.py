"""Step 0 (c): visual conditions through the real input path.

Textured arena (FlyGym) -> both eyes, VIS_SUBFRAMES renders per 25 ms step ->
FlyVis -> per-neuron T4/T5 rates (flight/visual_input.py). The body is moved
kinematically (qpos set every render, no physics). 1 s = 40 steps per condition.
Output: a0_visual_rates.npz with, per condition, t45_L (40, 5901) and t45_R
(40, 5921) float32 rates in Hz, plus per-step (eye x subtype) means.

    env -u PYTHONPATH python scripts/diag/a0_visual.py
    env -u PYTHONPATH python scripts/diag/a0_visual.py --vision-boundary [--only perch air_static ...]
--vision-boundary: the same scenes through the FlyVis boundary layer (flight/vision_boundary.py);
keys {name}__vbnd_L / __vbnd_R (per-neuron rates in vbnd_L/R order), output a0_visual_rates_vb.npz.
"""
import argparse
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from scipy.spatial.transform import Rotation as Rot  # noqa: E402

from flight import groups as G  # noqa: E402
from flight import visual_input as V  # noqa: E402
from flight.body import FlightBody  # noqa: E402

N_STEPS = 40
DT = 0.025
SUB = V.VIS_SUBFRAMES

# name: (start position, yaw rate rad/s (+ = left/CCW), velocity mm/s, legs)
# perch: standing on the take-off pedestal (static). Open air: 60 mm up, heading +x.
# loom_L: tower1's south face (y = -100) on the fly's left, approached from 65 to 10 mm
# at 55 mm/s; loom_R: its north face (y = 160) on the right.
CONDITIONS = {
    "perch": (None, 0.0, (0, 0, 0)),
    "air_static": ((60, -60, 60), 0.0, (0, 0, 0)),
    "yaw_R": ((60, -60, 60), -np.radians(90), (0, 0, 0)),
    "yaw_L": ((60, -60, 60), +np.radians(90), (0, 0, 0)),
    "progressive": ((20, -60, 60), 0.0, (100, 0, 0)),
    "loom_L": ((180, -165, 100), 0.0, (0, 55, 0)),
    "loom_R": ((180, 225, 100), 0.0, (0, -55, 0)),
}


# Mirror-symmetric synthetic stimuli (no arena): the left-eye image and the mirrored
# right-eye image are identical in the FlyVis frame. sym_prog: standard grating
# front-to-back in both eyes; sym_static: the same grating, not moving.
SYNTHETIC = {"sym_prog": (1.0,), "sym_static": (0.0,)}


def synthetic(eyes, tf_scale):
    n = N_STEPS * SUB
    gL = list(V.grating_frames((-1, 0), n, tf=V.GRATING_TF_HZ * tf_scale))
    gR = list(V.grating_frames((1, 0), n, tf=V.GRATING_TF_HZ * tf_scale))
    eyes.reset()
    rl, rr, tm = [], [], []
    for k in range(N_STEPS):
        fr = [np.stack([gL[i][0], gR[i][1]]) for i in range(k * SUB, (k + 1) * SUB)]
        a, _ = eyes.step(fr)
        r = eyes.rates(a)
        rl.append(r["L"].astype(np.float32))
        rr.append(r["R"].astype(np.float32))
        tm.append(eyes.type_means(r))
    return rl, rr, tm


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--vision-boundary", action="store_true")
    ap.add_argument("--only", nargs="+", default=None, help="condition names (default: all)")
    opt = ap.parse_args(argv)
    rid = G.load_root_ids()
    groups = G.build_groups(rid)
    if opt.vision_boundary:
        from flight import vision_boundary as VB
        groups.update(VB.boundary_groups(rid))
        eyes = VB.BoundaryEyes({"L": groups["vbnd_L"], "R": groups["vbnd_R"]})
        key = "vbnd"
    else:
        eyes = V.FlyVisEyes({"L": groups["t45_L"], "R": groups["t45_R"]})
        key = "t45"
    keep = (lambda n: opt.only is None or n in opt.only)
    out = {}
    for name, (tf_scale,) in SYNTHETIC.items():
        if not keep(name):
            continue
        rl, rr, tm = synthetic(eyes, tf_scale)
        out[f"{name}__{key}_L"], out[f"{name}__{key}_R"], out[f"{name}__type_means"] = map(np.array, (rl, rr, tm))
        print(f"{name:12s} {key} mean Hz  L {np.array(rl)[10:].mean():5.1f}  R {np.array(rr)[10:].mean():5.1f}", flush=True)
    for name, (pos, yaw_rate, vel) in CONDITIONS.items():
        if not keep(name):
            continue
        b = FlightBody(spawn_pos=pos, legs="stand" if pos is None else "tuck", enable_vision=True)
        adr = b.m.jnt_qposadr[b.m.body_jntadr[b.root]]
        p0 = b.d.qpos[adr:adr + 3].copy()
        q0 = b.d.qpos[adr + 3:adr + 7].copy()
        eyes.reset()
        rl, rr, tm = [], [], []
        for k in range(N_STEPS):
            frames = []
            for j in range(SUB):
                t = (k * SUB + j + 1) * DT / SUB
                b.d.qpos[adr:adr + 3] = p0 + np.asarray(vel, float) * t
                R = Rot.from_rotvec([0, 0, yaw_rate * t]) * Rot.from_quat(q0[[1, 2, 3, 0]])
                b.d.qpos[adr + 3:adr + 7] = R.as_quat()[[3, 0, 1, 2]]
                mujoco.mj_forward(b.m, b.d)
                frames.append(b.update_vision().copy())
            a, _ = eyes.step(frames)
            r = eyes.rates(a)
            rl.append(r["L"].astype(np.float32))
            rr.append(r["R"].astype(np.float32))
            tm.append(eyes.type_means(r))
        out[f"{name}__{key}_L"] = np.array(rl)
        out[f"{name}__{key}_R"] = np.array(rr)
        out[f"{name}__type_means"] = np.array(tm)
        m = np.array(tm)[10:].mean(0)
        types = eyes.fw_types if opt.vision_boundary else G.T45_TYPES
        print(f"{name:12s} {key} mean Hz  L {np.array(rl)[10:].mean():5.1f}  R {np.array(rr)[10:].mean():5.1f} | "
              + " ".join(f"{t}:{m[0, i]:.0f}/{m[1, i]:.0f}" for i, t in enumerate(types)), flush=True)
        del b
    np.savez_compressed("a0_visual_rates_vb.npz" if opt.vision_boundary else "a0_visual_rates.npz", **out)


if __name__ == "__main__":
    main()
