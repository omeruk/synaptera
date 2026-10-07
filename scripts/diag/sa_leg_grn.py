"""Leg GRN short test (SPEC_SENSORY_INPUTS §2.4, §3.2b; pre-registered, no tuning).

Full brain (no input set other than leg_sugar), open loop, seeds 0/1/2 from the fresh state: only the
selected sugar-like leg GRNs (data/leg_sugar_grn_783.csv) at cfg.SUGAR_RATE_CONTACT = 100 Hz for 1 s;
labellar sugar GRNs and every other input 0. MN9 (CB0701) L/R Hz over 0-1000 ms (and 250-1000 ms).
Question: MN9 L/R mean over the 3 seeds > 10 Hz? Reported as is.
Reference row (same protocol, labellar sugar GRNs only) for comparison with R0/K5.

    env -u PYTHONPATH python scripts/diag/sa_leg_grn.py [--seeds 0 1 2]
"""
import argparse
import json
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402

DT, N_ON = 0.025, 40


def main(seeds):
    from brian2 import seed as brian_seed
    from flight import config as cfg
    from flight.brain import FlightBrain, SpikeCounter
    from flight.readouts import Readouts
    t0 = time.time()
    b = FlightBrain(seed=seeds[0], olfaction=False, leg_grn=True)
    ro = Readouts(b.root_ids)
    mn9 = ro.local["MN9"]
    b.net.store("fresh")
    print(f"build {time.time() - t0:.0f} s; leg_sugar {len(b.local['leg_sugar'])} neurons", flush=True)
    out = {}
    for cond, rates in (("leg_only", dict(leg_sugar=cfg.SUGAR_RATE_CONTACT)),
                        ("labellar_only", dict(sugar=cfg.SUGAR_RATE_CONTACT))):
        for sd in seeds:
            b.net.restore("fresh")
            brian_seed(sd)
            b.counter = SpikeCounter(b.spk_mon, b.n)
            b.silence_inputs()
            b.set_rates(**rates)
            c_all = np.zeros((N_ON, 2))
            leg_hz = 0.0
            for k in range(N_ON):
                _, c = b.step()
                c_all[k] = [c[mn9["L"]].sum(), c[mn9["R"]].sum()]
                leg_hz += c[b.local["leg_sugar"]].sum()
                b.counter.t_chunks, b.counter.i_chunks = [], []
            n = np.array([len(mn9["L"]), len(mn9["R"])])
            full = c_all.sum(0) / (n * N_ON * DT)
            late = c_all[10:].sum(0) / (n * (N_ON - 10) * DT)
            out[f"{cond}_s{sd}"] = dict(mn9_LR_0_1000=full.round(2).tolist(), mn9_LR_250_1000=late.round(2).tolist(),
                                        mn9_mean=float(full.mean()),
                                        leg_grn_rate=float(leg_hz / (len(b.local["leg_sugar"]) * N_ON * DT)))
            print(cond, sd, out[f"{cond}_s{sd}"], flush=True)
    for cond in ("leg_only", "labellar_only"):
        m = float(np.mean([out[f"{cond}_s{sd}"]["mn9_mean"] for sd in seeds]))
        out[f"{cond}_mean"] = m
        print(f"{cond}: MN9 L/R ort., 3 seed: {m:.2f} Hz -> {'> 10 Hz' if m > 10 else '<= 10 Hz'}")
    with open("sa_leg_grn.json", "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    main(ap.parse_args().seeds)
