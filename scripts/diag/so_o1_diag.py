"""EXPLORATORY DIAGNOSTIC, post hoc; NOT part of O1 and not a criterion or a decision (REPORT.md §3.7).

One run identical to the O1 run (rate 10 Hz, seed 101; same protocol, same code path as scripts/diag/so_o1.py), but with
the spike count of EVERY neuron in EVERY 25 ms step stored (int16, shape steps x neurons), so that the persistent state
can be attributed to cell classes afterwards. Nothing is changed or tuned. The population traces of this run must equal
those of logs/smell/o1/o1_r10.0_s101.npz (checked by scripts/diag/o1_diag_report.py).

    env -u PYTHONPATH python scripts/diag/so_o1_diag.py --out logs/smell/o1_diag
"""
import argparse
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts", "diag"))

import numpy as np  # noqa: E402

import so_o1  # noqa: E402

RATE, SEED = 10.0, 101


def main(out):
    from brian2 import seed as brian_seed
    from flight.brain import FlightBrain, SpikeCounter
    from flight.olfaction_full import OlfactionFull, GROUPS
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    b = FlightBrain(seed=SEED, olfaction_full=True, apl_graded=False, nt_literature=False)
    olf = OlfactionFull(b.root_ids)
    driven = np.zeros(b.n, bool)
    food = np.zeros(b.n, bool)
    for k in GROUPS:
        driven[b.groups[k]] = True
        food[b.groups[k][olf.food[k]]] = True
    P = so_o1.pops(b.root_ids, driven)
    b.net.store("fresh")
    b.net.restore("fresh")
    brian_seed(SEED)
    b.counter = SpikeCounter(b.spk_mon, b.n)
    n_tot = so_o1.N_DRIVE + so_o1.N_POST
    cnt = np.zeros((n_tot, b.n), np.int16)
    pr = {p: np.zeros(n_tot) for p in P}
    food_rates = {k: np.where(olf.food[k], RATE, 0.0) for k in GROUPS}
    for k in range(n_tot):
        b.silence_inputs()
        if k < so_o1.N_DRIVE:
            b.set_rates(**food_rates)
        _, c = b.step()
        cnt[k] = c
        for p, idx in P.items():
            pr[p][k] = c[idx].sum() / (len(idx) * so_o1.DT)
        b.counter.t_chunks, b.counter.i_chunks = [], []
    np.savez_compressed(f"{out}/o1_diag_r{RATE}_s{SEED}.npz", rate=RATE, seed=SEED, counts=cnt, driven=driven, food=food,
                        **{f"pop_{p}": v for p, v in pr.items()})
    print(f"diagnostic run done in {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="o1_diag")
    main(ap.parse_args().out)
