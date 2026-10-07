"""Smell part 2/4 robustness records (SPEC_SENSORY_INPUTS §3.4b; recorded, NOT criteria).

For each model in --variants (published = reference, N1, N2 = MODEL VARIANTS, not the published model), seeds 501-503:
  (i)  no input: olfaction_full brain, all inputs 0 Hz for 1 s (40 steps) from the fresh state; whole-network mean rate over the
       last 200 ms (steps 32-39) and over the whole second; "silent" iff < 0.1 Hz in the last 200 ms (trivial from rest, see SPEC);
  (ii) sugar GRN -> MN9 open loop (scripts/diag/a1_mn9.py 'sugar_only'): final-configuration brain (olfaction=False), sugar 100 Hz, all
       other inputs 0, 1 s, MN9 mean rate (L, R) over steps 10-39 (250-1000 ms) against MN9_THRESHOLD_HZ.

    env -u PYTHONPATH python scripts/diag/so_nt_robust.py --out DIR --variants N1 N2 published
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts", "diag"))

import numpy as np  # noqa: E402

SEEDS = [501, 502, 503]
DT = 0.025


def run(variants, out):
    from brian2 import seed as brian_seed
    from flight.brain import FlightBrain, SpikeCounter
    from flight.readouts import Readouts
    from flight.vnc_bridge import MN9_THRESHOLD_HZ
    from so_o1 import VARIANTS
    res = {}
    for v in variants:
        res[v] = {"i_no_input": [], "ii_sugar_mn9": [], "mn9_threshold_hz": MN9_THRESHOLD_HZ}
        b = FlightBrain(seed=SEEDS[0], olfaction_full=True, apl_graded=False, verbose=False, **VARIANTS[v])
        b.net.store("fresh")
        for sd in SEEDS:
            b.net.restore("fresh")
            brian_seed(sd)
            b.counter = SpikeCounter(b.spk_mon, b.n)
            tot = np.zeros(40)
            for k in range(40):
                b.silence_inputs()
                _, c = b.step()
                tot[k] = c.sum()
                b.counter.t_chunks, b.counter.i_chunks = [], []
            last, whole = tot[32:40].sum() / (b.n * 8 * DT), tot.sum() / (b.n * 40 * DT)
            res[v]["i_no_input"].append(dict(seed=sd, last200ms_hz=float(last), whole_s_hz=float(whole), silent=bool(last < 0.1)))
            print(v, "(i)", sd, res[v]["i_no_input"][-1], flush=True)
        del b
        b = FlightBrain(seed=SEEDS[0], olfaction=False, apl_graded=False, verbose=False, **VARIANTS[v])
        mn9 = Readouts(b.root_ids).local["MN9"]
        b.net.store("fresh")
        for sd in SEEDS:
            b.net.restore("fresh")
            brian_seed(sd)
            b.counter = SpikeCounter(b.spk_mon, b.n)
            on = np.zeros(b.n)
            for k in range(40):
                b.silence_inputs()
                b.set_rates(sugar=100.0)
                _, c = b.step()
                if k >= 10:
                    on += c
                b.counter.t_chunks, b.counter.i_chunks = [], []
            hz = (float(on[mn9["L"]].sum() / 0.75), float(on[mn9["R"]].sum() / 0.75))
            res[v]["ii_sugar_mn9"].append(dict(seed=sd, mn9_L_hz=hz[0], mn9_R_hz=hz[1], mean_hz=float(np.mean(hz)),
                                               above_threshold=bool(np.mean(hz) > MN9_THRESHOLD_HZ)))
            print(v, "(ii)", sd, res[v]["ii_sugar_mn9"][-1], flush=True)
        del b
        json.dump(res, open(f"{out}/robust.json", "w"), indent=1)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="robust")
    ap.add_argument("--variants", nargs="+", default=["N1", "N2", "published"])
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    open(f"{a.out}/START_ROBUST", "a").write(f"{stamp} variants={a.variants}\n")
    print(f"start {stamp} variants={a.variants}", flush=True)
    t0 = time.time()
    run(a.variants, a.out)
    open(f"{a.out}/DONE_ROBUST", "w").write(f"done {time.time() - t0:.0f} s\n")
