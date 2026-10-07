"""Step 1 (beslenme): MN9 under sugar contact with the --no-olfaction flight inputs, open loop.

Every condition from the same fresh state (net.restore), 1 s (MN9 counted 250-1000 ms),
full brain, olfaction=False (no food-ORN input). T4/T5 sequences from a0_visual.py
(a0_visual_rates.npz: perch = standing on the pedestal, progressive = forward flight
at 100 mm/s, yaw_R = turning in the air, air_static = hovering). Criterion (SPEC Step 1):
MN9 mean > MN9_THRESHOLD_HZ (flight/vnc_bridge.py) with sugar, also under the flight
visual baseline; 0 without sugar.

    env -u PYTHONPATH python scripts/diag/a1_mn9.py --vis-dir <dir of a0_visual_rates.npz> [--seeds 0 1 2]
"""
import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402

from flight.readouts import Readouts  # noqa: E402
from flight.vnc_bridge import MN9_THRESHOLD_HZ  # noqa: E402

CONDS = {"sugar_only": (100.0, None), "sugar_perch": (100.0, "perch"), "sugar_hover": (100.0, "air_static"),
         "sugar_prog": (100.0, "progressive"), "sugar_yawR": (100.0, "yaw_R"),
         "nosugar_perch": (0.0, "perch"), "nosugar_prog": (0.0, "progressive")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vis-dir", default=".")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--apl-graded", action="store_true")
    ap.add_argument("--nt-silent", default=None)
    a = ap.parse_args()
    from flight.brain import FlightBrain, SpikeCounter
    vis = dict(np.load(os.path.join(a.vis_dir, "a0_visual_rates.npz")))
    res = {k: [] for k in CONDS}
    for seed in a.seeds:
        b = FlightBrain(seed=seed, olfaction=False, apl_graded=a.apl_graded, nt_silent=a.nt_silent, verbose=False)
        ro = Readouts(b.root_ids)
        mn9 = ro.local["MN9"]
        b.net.store("fresh")
        for name, (sugar, v) in CONDS.items():
            b.net.restore("fresh")
            b.counter = SpikeCounter(b.spk_mon, b.n)
            b.silence_inputs()
            on = np.zeros(b.n)
            for k in range(40):
                r = dict(sugar=sugar)
                if v:
                    r["t45_L"], r["t45_R"] = vis[f"{v}__t45_L"][k], vis[f"{v}__t45_R"][k]
                b.set_rates(**r)
                _, c = b.step()
                if k >= 10:
                    on += c
            hz = (on[mn9["L"]].sum() / 0.75, on[mn9["R"]].sum() / 0.75)
            res[name].append(hz)
            print(f"seed {seed} {name:14s} MN9 L/R {hz[0]:5.1f}/{hz[1]:5.1f} Hz  mean {np.mean(hz):5.1f}", flush=True)
            b.counter.t_chunks, b.counter.i_chunks = [], []
        del b
    print(f"\nMN9 (Hz, mean over seeds {a.seeds}; threshold {MN9_THRESHOLD_HZ} Hz)")
    for name, v in res.items():
        v = np.array(v)
        m = v.mean(1)
        print(f"  {name:14s} L/R {v[:, 0].mean():5.1f}/{v[:, 1].mean():5.1f}  mean {m.mean():5.1f} ± {m.std():4.1f}  "
              f"{'> thr' if m.min() > MN9_THRESHOLD_HZ else ('0' if m.max() == 0 else '<= thr in some seed')}")


if __name__ == "__main__":
    main()
