"""Smell comparison check (SPEC_SENSORY_INPUTS §3.4c, pre-registered): the upstream NeuroFly-style olfactory drive in our O1 set-up.

Published model (no variant), open loop, per run from the fresh state (net.restore + brian2.seed). 25 ms steps:
  drive  steps 0-39: the 2,279 neurons selected by the upstream walking script's regex (cell_class "olfactory": 2,275 ORNs + 4 untyped)
                     Poisson at 80 Hz each (upstream CIRCUIT_STIM_RATE), weight w_syn*f_poi, refractory 0; every other input 0 Hz
  cut    steps 40-79: all inputs 0 Hz (recording only)
PASS (per seed): AL and not-driven mean rate < 0.1 Hz in W1 = steps 44-47; the level passes iff 5/5 seeds pass.
The 4 untyped cells are not in the orn_all groups; they get an extra PoissonGroup + Synapses (same weight, rfc 0), added to the network before net.store.
One .npz per seed; existing files are skipped (resumable). Writes START_NF (local start time) and DONE_NF.

    env -u PYTHONPATH python scripts/diag/so_o1_nf.py --out DIR [--seeds ...] [--n-drive 40 --n-post 40]
    env -u PYTHONPATH python scripts/diag/so_o1_nf.py --report DIR
"""
import argparse
import glob
import json
import os
import sys
import time
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import numpy as np  # noqa: E402

DT = 0.025
RATE = 80.0  # upstream CIRCUIT_STIM_RATE (fly_brain_body_simulation.py L383)
SEEDS = [701, 702, 703, 704, 705]
N_DRIVE, N_POST = 40, 40
W1, W2, PN_WIN = (44, 48), (56, 60), (10, 40)
THR = 0.1
UPSTREAM_REGEX = "|".join(["olfactory", "olfactori", r"\born\b", "projection.neuron"])   # same keyword selection as upstream L303 (hash: nf_report.CITED); columns as at L292


def upstream_olfactory(root_ids):
    """Completeness-row indices selected by the upstream regex (same columns, lower-cased match)."""
    import pandas as pd
    from flight import groups as G
    r2i = G.root_to_index(root_ids)
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False)
    m = np.zeros(len(ann), bool)
    for c in ("cell_class", "cell_type", "super_class"):
        m |= ann[c].astype(str).str.lower().str.contains(UPSTREAM_REGEX, na=False, regex=True).to_numpy()
    ann = ann[m & ann["root_id"].isin(r2i).to_numpy()]
    return np.sort(ann["root_id"].map(r2i).to_numpy(np.int64))


def run(out, seeds, n_drive, n_post):
    from brian2 import seed as brian_seed, Hz, ms, PoissonGroup, Synapses
    from flight.brain import FlightBrain, SpikeCounter
    from flight.olfaction_full import GROUPS
    import so_o1
    todo = [s for s in seeds if not os.path.exists(f"{out}/nf_s{s}.npz")]
    print(f"{len(todo)} runs to do", flush=True)
    if not todo:
        return
    t0 = time.time()
    b = FlightBrain(seed=seeds[0], olfaction_full=True, apl_graded=False)  # published model
    assert b.l2g is None, "full brain expected (no DEV subnet)"
    up = upstream_olfactory(b.root_ids)
    in_groups = np.sort(np.concatenate([b.groups[k] for k in GROUPS]))
    assert np.isin(in_groups, up).all(), "an orn_all neuron is not in the upstream set"
    extra = np.setdiff1d(up, in_groups)
    print(f"upstream set {len(up)} = {len(in_groups)} in orn_all groups + {len(extra)} extra (untyped olfactory-class)", flush=True)
    pg = PoissonGroup(len(extra), rates=0 * Hz, name="poi_nf_extra")
    s = Synapses(pg, b.neu, "w : volt", on_pre="v += w", delay=b.params["t_dly"], name="poi_syn_nf_extra")
    s.connect(i=np.arange(len(extra)), j=extra)
    s.w = b.params["w_syn"] * b.params["f_poi"]
    b.neu.rfc[extra] = 0 * ms
    b.net.add(pg, s)
    driven = np.zeros(b.n, bool)
    driven[up] = True
    P = so_o1.pops(b.root_ids, driven)
    P["driven"] = np.flatnonzero(driven)
    b.net.store("fresh")
    print(f"build {time.time() - t0:.0f} s; driven {int(driven.sum())}; AL {len(P['AL'])} ALPN {len(P['ALPN'])}", flush=True)
    for sd in todo:
        t1 = time.time()
        b.net.restore("fresh")
        brian_seed(sd)
        b.counter = SpikeCounter(b.spk_mon, b.n)
        n_tot = n_drive + n_post
        pr = {p: np.zeros(n_tot) for p in P}
        drv_cnt = np.zeros((n_tot, len(P["driven"])), np.int16)
        rates = {k: RATE for k in GROUPS}
        for k in range(n_tot):
            b.silence_inputs()
            if k < n_drive:
                b.set_rates(**rates)
                pg.rates = RATE * Hz
            else:
                pg.rates = 0 * Hz
            _, c = b.step()
            for p, idx in P.items():
                pr[p][k] = c[idx].sum() / (len(idx) * DT)
            drv_cnt[k] = c[P["driven"]]
            b.counter.t_chunks, b.counter.i_chunks = [], []
        np.savez_compressed(f"{out}/nf_s{sd}.npz", seed=sd, rate=RATE, n_drive=n_drive, n_post=n_post, n_driven=int(driven.sum()),
                            n_extra=len(extra), driven_counts=drv_cnt, **{f"pop_{p}": v for p, v in pr.items()})
        print(f"seed={sd}: {time.time() - t1:.0f} s", flush=True)


def report(d):
    recs = []
    for f in sorted(glob.glob(f"{d}/nf_s*.npz")):
        z = np.load(f)
        nd = int(z["n_drive"])
        sl = lambda w: slice(nd + w[0] - 40, nd + w[1] - 40)  # noqa: E731
        cnt = z["driven_counts"]
        rec = dict(seed=int(z["seed"]), n_driven=int(z["n_driven"]))
        for p in ("AL", "not_driven", "driven"):
            rec[f"W1_{p}"] = float(z[f"pop_{p}"][sl(W1)].mean())
            rec[f"W2_{p}"] = float(z[f"pop_{p}"][sl(W2)].mean())
        rec["pass"] = rec["W1_AL"] < THR and rec["W1_not_driven"] < THR
        for p in ("AL", "ALPN", "PN_uni", "KC", "LH", "not_driven"):
            rec[f"drive_{p}"] = float(z[f"pop_{p}"][nd - 30:nd].mean())
        rec["frac_driven_spiking_W1"] = float((cnt[sl(W1)].sum(0) > 0).mean())
        rec["frac_driven_spiking_W2"] = float((cnt[sl(W2)].sum(0) > 0).mean())
        rec["frac_driven_spiking_post"] = float((cnt[nd:].sum(0) > 0).mean())
        recs.append(rec)
    npass = sum(r["pass"] for r in recs)
    summ = dict(n=len(recs), n_pass=int(npass), level_passes=bool(npass == 5 and len(recs) == 5), rate_hz=RATE)
    for r in recs:
        print(" ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in r.items()))
    print(json.dumps(summ))
    json.dump(dict(summary=summ, runs=recs), open(f"{d}/nf_summary.json", "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="o1_nf")
    ap.add_argument("--report")
    ap.add_argument("--seeds", type=int, nargs="*", default=SEEDS)
    ap.add_argument("--n-drive", type=int, default=N_DRIVE)
    ap.add_argument("--n-post", type=int, default=N_POST)
    a = ap.parse_args()
    if a.report:
        report(a.report)
    else:
        os.makedirs(a.out, exist_ok=True)
        stamp = datetime.now().astimezone().isoformat(timespec="seconds")
        with open(f"{a.out}/START_NF", "a") as f:
            f.write(f"{stamp}\n")
        print(f"start {stamp}", flush=True)
        run(a.out, a.seeds, a.n_drive, a.n_post)
        open(f"{a.out}/DONE_NF", "w").write("done\n")
