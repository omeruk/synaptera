"""Vision screen (SPEC_SENSORY_INPUTS §3.5): render the 10 stimuli through the existing FlyVis -> boundary-layer path.

Body-frame stimuli (flight/vis_stim.py) -> raw eye images -> Retina -> BoundaryEyes (FlyVis + boundary-layer transduction).
60 steps of 25 ms per condition (20 grey + 40 stimulus), FlyVis reset before each condition. Deterministic: rendered once for all seeds.
Writes OUT/vd_rates.npz (c01..c10 __vbnd_L/_R float32 (60, n)) and OUT/vd_input_check.json (the pre-registered input check).

    env -u PYTHONPATH python scripts/diag/vd_render.py --out logs/vis_dn
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

os.environ.setdefault("MUJOCO_GL", "egl")
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import mujoco  # noqa: E402
import numpy as np  # noqa: E402

from flight import groups as G  # noqa: E402
from flight import vis_stim as S  # noqa: E402
from flight import vision_boundary as VB  # noqa: E402
from flight.body import FlightBody  # noqa: E402

WIN = (28, 60)          # steps 28-59 = 200-1000 ms after onset (onset = step 20)
MIN_A_IN = 0.05


def a_in(rl, rr):
    return float((rl - rr) / (rl + rr + 1.0))


def input_check(rates, tcode, fw_types):
    """Pre-registered input check: yaw on T4a+T5a neurons, loom on all boundary-layer neurons."""
    sel = {s: np.isin(tcode[s], [fw_types.index(t) for t in ("T4a", "T5a")]) for s in ("L", "R")}
    res = {}
    for c in range(1, 11):
        L, R = rates[f"c{c:02d}__vbnd_L"][WIN[0]:WIN[1]], rates[f"c{c:02d}__vbnd_R"][WIN[0]:WIN[1]]
        res[c] = dict(A_in_all=a_in(L.mean(), R.mean()), A_in_T4aT5a=a_in(L[:, sel["L"]].mean(), R[:, sel["R"]].mean()),
                      mean_L=float(L.mean()), mean_R=float(R.mean()))
    yaw = [res[1]["A_in_T4aT5a"], res[2]["A_in_T4aT5a"]]
    loom = [res[4]["A_in_all"], res[5]["A_in_all"]]
    ok_yaw = bool(np.sign(yaw[0]) != np.sign(yaw[1]) and min(abs(x) for x in yaw) >= MIN_A_IN)
    ok_loom = bool(np.sign(loom[0]) != np.sign(loom[1]) and min(abs(x) for x in loom) >= MIN_A_IN)
    exp = dict(yaw_cw_negative=bool(yaw[0] < 0), yaw_ccw_positive=bool(yaw[1] > 0),
               loom_left_positive=bool(loom[0] > 0), loom_right_negative=bool(loom[1] < 0))
    return dict(per_condition=res, yaw_pass=ok_yaw, loom_pass=ok_loom, passed=ok_yaw and ok_loom,
                expected_signs_recorded_not_criteria=exp,
                verdict="input check passed" if ok_yaw and ok_loom else "input check failed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="logs/vis_dn")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    with open(f"{a.out}/START_RENDER", "a") as f:
        f.write(datetime.now().astimezone().isoformat(timespec="seconds") + "\n")
    t0 = time.time()
    body = FlightBody(spawn_pos=(0, 0, 100), spawn_yaw=0.0, legs="tuck", enable_vision=True)
    mujoco.mj_forward(body.m, body.d)
    rays = S.camera_rays(body.m, body.d, body.root)
    from flygym.vision import Retina
    retina = Retina()
    rid = G.load_root_ids()
    groups = G.build_groups(rid)
    groups.update(VB.boundary_groups(rid))
    eyes = VB.BoundaryEyes({"L": groups["vbnd_L"], "R": groups["vbnd_R"]})
    out = {}
    for c in range(1, 11):
        t1 = time.time()
        eyes.reset()
        rl, rr = [], []
        for k in range(S.N_STEPS):
            act, _ = eyes.step(S.step_frames(c, k, rays, retina))
            r = eyes.rates(act)
            rl.append(r["L"].astype(np.float32))
            rr.append(r["R"].astype(np.float32))
        out[f"c{c:02d}__vbnd_L"], out[f"c{c:02d}__vbnd_R"] = np.array(rl), np.array(rr)
        print(f"c{c:02d} {S.CONDITIONS[c]:15s} window mean Hz L {np.array(rl)[WIN[0]:WIN[1]].mean():6.2f} "
              f"R {np.array(rr)[WIN[0]:WIN[1]].mean():6.2f} ({time.time() - t1:.0f} s)", flush=True)
    chk = input_check(out, eyes.tcode, list(eyes.fw_types))
    np.savez_compressed(f"{a.out}/vd_rates.npz", **out)
    json.dump(chk, open(f"{a.out}/vd_input_check.json", "w"), indent=1)
    print(json.dumps({k: chk[k] for k in ("yaw_pass", "loom_pass", "passed", "verdict", "expected_signs_recorded_not_criteria")}),
          flush=True)
    print(f"render done in {time.time() - t0:.0f} s", flush=True)
    open(f"{a.out}/DONE_RENDER", "w").write("done\n")


if __name__ == "__main__":
    main()
