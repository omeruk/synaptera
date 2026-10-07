"""Step 2 (direction): visual sequences for the open-loop tests, through the real input path
(FlyGym eyes -> FlyVis -> per-neuron T4/T5 rates, flight/visual_input.py).

Synthetic (no arena; the same image in both eyes before the right-eye mirror):
  syn_yaw_ccw  grating image moving left in both eyes: left eye front-to-back, right eye
               back-to-front = the world turning counter-clockwise (seen from above), as when
               the fly turns right. Optomotor response: turn LEFT.
  syn_yaw_cw   the opposite: optomotor response turn RIGHT.
Arena (kinematic, as a0_visual.py; the fly body is moved, no physics):
  plat_{dark|neutral}_{az}  hovering 150 mm south of the food platform at z = 150 mm (below the
               platform top, so the pillar is a vertical bar), heading so that the platform is at
               azimuth az deg (+ = left), flying forward at 60 mm/s for 1 s. dark = Step 2 arena
               (uniformly dark platform), neutral = the platform has the obstacle checker.
Output: a2_visual_rates.npz (per condition t45_L (40, 5901), t45_R (40, 5921), azimuth per step).

    env -u PYTHONPATH python scripts/diag/a2_visual.py
    env -u PYTHONPATH python scripts/diag/a2_visual.py --vision-boundary [--no-platform]
--vision-boundary: through the FlyVis boundary layer, keys __vbnd_L/R, output a2_visual_rates_vb.npz.
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

from flight import config as cfg  # noqa: E402
from flight import groups as G  # noqa: E402
from flight import visual_input as V  # noqa: E402
from flight.body import FlightBody  # noqa: E402

N_STEPS, DT, SUB = 40, 0.025, V.VIS_SUBFRAMES
AZIMUTHS = (-60, -30, -15, 0, 15, 30, 60)
DIST, Z, SPEED = 150.0, 150.0, 60.0


def azimuth(pos, heading):
    """Platform azimuth in the fly's horizontal frame (deg, + = left)."""
    cx, cy = cfg.FOOD_PLATFORM[:2]
    a = np.arctan2(cy - pos[1], cx - pos[0]) - heading
    return float(np.degrees((a + np.pi) % (2 * np.pi) - np.pi))


KEY = "t45"


def synthetic(eyes, direction):
    n = N_STEPS * SUB
    g = list(V.grating_frames(direction, n))
    eyes.reset()
    rl, rr = [], []
    for k in range(N_STEPS):
        a, _ = eyes.step([g[i] for i in range(k * SUB, (k + 1) * SUB)])
        r = eyes.rates(a)
        rl.append(r["L"].astype(np.float32))
        rr.append(r["R"].astype(np.float32))
    return np.array(rl), np.array(rr)


def platform_run(eyes, style, az):
    cx, cy = cfg.FOOD_PLATFORM[:2]
    p0 = np.array([cx, cy - DIST, Z])              # south of the platform
    heading = np.pi / 2 - np.radians(az)           # platform (north) at azimuth az
    b = FlightBody(spawn_pos=tuple(p0), spawn_yaw=heading, legs="tuck", enable_vision=True, platform=style)
    adr = b.m.jnt_qposadr[b.m.body_jntadr[b.root]]
    q_start = b.d.qpos[adr:adr + 3].copy()
    q0 = b.d.qpos[adr + 3:adr + 7].copy()
    fwd = np.array([np.cos(heading), np.sin(heading), 0.0])
    eyes.reset()
    rl, rr, azs = [], [], []
    for k in range(N_STEPS):
        frames = []
        for j in range(SUB):
            t = (k * SUB + j + 1) * DT / SUB
            b.d.qpos[adr:adr + 3] = q_start + fwd * SPEED * t
            b.d.qpos[adr + 3:adr + 7] = q0
            mujoco.mj_forward(b.m, b.d)
            frames.append(b.update_vision().copy())
        a, _ = eyes.step(frames)
        r = eyes.rates(a)
        rl.append(r["L"].astype(np.float32))
        rr.append(r["R"].astype(np.float32))
        azs.append(azimuth(p0 + fwd * SPEED * (k + 1) * DT, heading))
    del b
    return np.array(rl), np.array(rr), np.array(azs)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--vision-boundary", action="store_true")
    ap.add_argument("--no-platform", action="store_true", help="synthetic yaw conditions only")
    a = ap.parse_args(argv)
    rid = G.load_root_ids()
    groups = G.build_groups(rid)
    if a.vision_boundary:
        from flight import vision_boundary as VB
        groups.update(VB.boundary_groups(rid))
        eyes = VB.BoundaryEyes({"L": groups["vbnd_L"], "R": groups["vbnd_R"]})
        k = "vbnd"
    else:
        eyes = V.FlyVisEyes({"L": groups["t45_L"], "R": groups["t45_R"]})
        k = KEY
    out = {}
    for name, d in (("syn_yaw_ccw", (-1, 0)), ("syn_yaw_cw", (1, 0))):
        out[f"{name}__{k}_L"], out[f"{name}__{k}_R"] = synthetic(eyes, d)
        print(name, out[f"{name}__{k}_L"][10:].mean(), out[f"{name}__{k}_R"][10:].mean(), flush=True)
    for style in (() if a.no_platform else ("dark", "neutral")):
        for az in AZIMUTHS:
            n = f"plat_{style}_{az}"
            out[f"{n}__{k}_L"], out[f"{n}__{k}_R"], out[f"{n}__az"] = platform_run(eyes, style, az)
            print(f"{n:18s} az {out[f'{n}__az'][0]:+.1f} -> {out[f'{n}__az'][-1]:+.1f} deg, {k} L "
                  f"{out[f'{n}__{k}_L'][10:].mean():.1f} R {out[f'{n}__{k}_R'][10:].mean():.1f} Hz", flush=True)
    np.savez_compressed("a2_visual_rates_vb.npz" if a.vision_boundary else "a2_visual_rates.npz", **out)


if __name__ == "__main__":
    main()
