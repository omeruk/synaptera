"""Vision screen (SPEC_SENSORY_INPUTS §3.5b follow-up; same procedure as vd_run.py): open-loop brain runs, spike counts of all DNs.

Published model (FlightBrain, vision_boundary=True, olfaction=False; no variant). Per (seed, condition): fresh state
(net.restore + brian2.seed), all inputs 0 Hz except the boundary-layer rates of OUT/vl_rates.npz (60 steps of 25 ms:
20 grey + 40 stimulus). Records the per-step spike counts of all 1,299 DNs (int16) to OUT/vl_c{cond:02d}_s{seed}.npz;
existing files are skipped (resumable). --null: degree-preserving shuffled connectome (permutation seed = simulation seed),
grey (condition 10) excluded.

    env -u PYTHONPATH python scripts/diag/vl_run.py --rates logs/vis_loom/vl_rates.npz --out logs/vis_loom/disc --seeds 511 512 513
    env -u PYTHONPATH python scripts/diag/vl_run.py --rates logs/vis_loom/vl_rates.npz --out logs/vis_loom/null --seeds 811 ... --null
"""
import argparse
import os
import sys
import time
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402

N_STEPS = 60
CONDS = [4, 5, 6, 7, 8, 11, 10]      # SPEC §3.5b: loom L/R/front, receding L/R/front, grey


def run(rates_path, out, seeds, null):
    import pandas as pd
    from brian2 import seed as brian_seed
    from flight import groups as G
    from flight.brain import FlightBrain, SpikeCounter
    rates = np.load(rates_path)
    conds = [c for c in CONDS if not (null and c == 10)]
    dn = pd.read_csv(G.PATH_DN)
    for sd in seeds:
        todo = [c for c in conds if not os.path.exists(f"{out}/vl_c{c:02d}_s{sd}.npz")]
        if not todo:
            continue
        t0 = time.time()
        b = FlightBrain(seed=sd, olfaction=False, verbose=False, vision_boundary=True, shuffle_seed=sd if null else None)
        r2i = G.root_to_index(b.root_ids)
        d = dn[dn["root_id"].isin(r2i)]
        dn_idx = d["root_id"].map(r2i).to_numpy(np.int64)
        b.net.store("fresh")
        print(f"seed {sd}{' (SHUFFLED connectome)' if null else ''}: build {time.time() - t0:.0f} s, {len(todo)} conditions", flush=True)
        for c in todo:
            t1 = time.time()
            L, R = rates[f"c{c:02d}__vbnd_L"], rates[f"c{c:02d}__vbnd_R"]
            b.net.restore("fresh")
            brian_seed(sd)
            b.counter = SpikeCounter(b.spk_mon, b.n)
            b.silence_inputs()
            cnt = np.zeros((N_STEPS, len(dn_idx)), np.int16)
            for k in range(N_STEPS):
                b.set_rates(vbnd_L=L[k], vbnd_R=R[k], sugar=0.0)
                _, ct = b.step()
                cnt[k] = ct[dn_idx]
                b.counter.t_chunks, b.counter.i_chunks = [], []
            np.savez_compressed(f"{out}/vl_c{c:02d}_s{sd}.npz", cond=c, seed=sd, null=null, dn_root_idx=dn_idx, dn_counts=cnt)
            print(f"seed {sd} c{c:02d}: {time.time() - t1:.0f} s", flush=True)
        del b


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rates", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--null", action="store_true")
    ap.add_argument("--tag", default="RUN")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    with open(f"{a.out}/START_{a.tag}", "a") as f:
        f.write(f"{datetime.now().astimezone().isoformat(timespec='seconds')} seeds={a.seeds} null={a.null}\n")
    print(f"start {datetime.now().astimezone().isoformat(timespec='seconds')}", flush=True)
    run(a.rates, a.out, a.seeds, a.null)
    open(f"{a.out}/DONE_{a.tag}", "w").write("done\n")
