"""Vision follow-up (SPEC_SENSORY_INPUTS §3.5b): collect the rendered rates, render receding-front, apply the input check.

Conditions 4, 5, 6, 7, 8, 10 are copied unchanged from the §3.5 render (logs/vis_dn/vd_rates.npz; deterministic); only
condition 11 (receding-front) is rendered, with the same procedure as scripts/diag/vd_render.py. Writes OUT/vl_rates.npz
and OUT/vl_input_check.json (pre-registered input check, window W_loom = steps 48-55).

    env -u PYTHONPATH python scripts/diag/vl_render.py --out logs/vis_loom
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

import numpy as np  # noqa: E402

W_LOOM, W_REC, W_ON = (48, 56), (24, 32), (20, 28)
MIN_A_IN, MIN_RATIO = 0.05, 3.0
COND = [4, 5, 6, 7, 8, 10, 11]


def a_in(rl, rr):
    return float((rl - rr) / (rl + rr + 1.0))


def input_check(rates):
    g = lambda c, e, w: float(rates[f"c{c:02d}__vbnd_{e}"][w[0]:w[1]].mean())  # noqa: E731
    gl, gr = g(10, "L", W_LOOM), g(10, "R", W_LOOM)
    ll, lr = g(4, "L", W_LOOM), g(5, "R", W_LOOM)
    a4, a5 = a_in(g(4, "L", W_LOOM), g(4, "R", W_LOOM)), a_in(g(5, "L", W_LOOM), g(5, "R", W_LOOM))
    req1 = bool(ll >= MIN_RATIO * gl and lr >= MIN_RATIO * gr)
    req2 = bool(np.sign(a4) != np.sign(a5) and min(abs(a4), abs(a5)) >= MIN_A_IN)
    rec = {}
    for c in COND:
        rec[c] = {w: dict(L=g(c, "L", win), R=g(c, "R", win), A_in=a_in(g(c, "L", win), g(c, "R", win)))
                  for w, win in (("W_loom", W_LOOM), ("W_rec", W_REC), ("W_on", W_ON))}
    return dict(driven_eye_loom_left_L=ll, driven_eye_loom_right_R=lr, grey_L=gl, grey_R=gr,
                ratio_left=ll / gl, ratio_right=lr / gr, req1_ratio_ge_3=req1,
                A_in_loom_left=a4, A_in_loom_right=a5, req2_asymmetry=req2, passed=bool(req1 and req2),
                expected_signs_recorded_not_criteria=dict(loom_left_positive=bool(a4 > 0), loom_right_negative=bool(a5 < 0)),
                per_condition_recorded_not_criteria=rec,
                verdict="input check passed" if req1 and req2 else "input too weak, not testable")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="logs/vis_loom")
    ap.add_argument("--src", default="logs/vis_dn/vd_rates.npz")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    with open(f"{a.out}/START_RENDER", "a") as f:
        f.write(datetime.now().astimezone().isoformat(timespec="seconds") + "\n")
    t0 = time.time()
    src = np.load(a.src)
    out = {f"c{c:02d}__vbnd_{e}": src[f"c{c:02d}__vbnd_{e}"] for c in (4, 5, 6, 7, 8, 10) for e in "LR"}
    import mujoco
    from flight import groups as G
    from flight import vis_stim as S
    from flight import vision_boundary as VB
    from flight.body import FlightBody
    body = FlightBody(spawn_pos=(0, 0, 100), spawn_yaw=0.0, legs="tuck", enable_vision=True)
    mujoco.mj_forward(body.m, body.d)
    rays = S.camera_rays(body.m, body.d, body.root)
    from flygym.vision import Retina
    retina = Retina()
    rid = G.load_root_ids()
    groups = G.build_groups(rid)
    groups.update(VB.boundary_groups(rid))
    eyes = VB.BoundaryEyes({"L": groups["vbnd_L"], "R": groups["vbnd_R"]})
    eyes.reset()
    rl, rr = [], []
    for k in range(S.N_STEPS):
        act, _ = eyes.step(S.step_frames(11, k, rays, retina))
        r = eyes.rates(act)
        rl.append(r["L"].astype(np.float32))
        rr.append(r["R"].astype(np.float32))
    out["c11__vbnd_L"], out["c11__vbnd_R"] = np.array(rl), np.array(rr)
    np.savez_compressed(f"{a.out}/vl_rates.npz", **out)
    chk = input_check(out)
    json.dump(chk, open(f"{a.out}/vl_input_check.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in chk.items() if k != "per_condition_recorded_not_criteria"}, indent=1), flush=True)
    print(f"render done in {time.time() - t0:.0f} s", flush=True)
    open(f"{a.out}/DONE_RENDER", "w").write(chk["verdict"] + "\n")


if __name__ == "__main__":
    main()
