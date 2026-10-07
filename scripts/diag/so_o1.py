"""Smell circuit part 1/4, O1 (SPEC_SENSORY_INPUTS §3.4a, pre-registered): open loop, no resting ORN input.

Full brain, per run from the fresh state (net.restore + brian2.seed). 25 ms steps:
  drive  steps 0-39: the 298 food-glomerulus ORNs (both sides) Poisson at rate r, every other input 0 Hz
  cut    steps 40-79: all inputs 0 Hz (recording only)
PASS (per rate, per seed): AL and not-driven mean rate < 0.1 Hz in W1 = steps 44-47 (100-200 ms after the cut);
a rate passes iff 5/5 seeds pass. Recorded: PN response (steps 10-39), W2 = steps 56-59, time courses.
One .npz per (rate, seed); existing files are skipped (resumable). Writes START_O1 (local start time) and DONE_O1.

Part 2/4 (SPEC §3.4b): --variant N1 (--nt-impute) or N2 (--nt-impute --nt-literature) runs the same protocol on a MODEL VARIANT,
not the published model; the default "published" is the model of the part 1/4 run (unchanged code path).

    env -u PYTHONPATH python scripts/diag/so_o1.py --out DIR [--variant published|N1|N2] [--rates ...] [--seeds ...] [--n-drive 40 --n-post 40]
    env -u PYTHONPATH python scripts/diag/so_o1.py --report DIR
"""
import argparse
import glob
import json
import os
import sys
import time
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402

DT = 0.025
RATES = [10.0, 15.3, 23.5, 36.1, 55.4, 85.0, 130.3, 200.0]
SEEDS = [101, 102, 103, 104, 105]
N_DRIVE, N_POST = 40, 40
W1, W2, PN_WIN = (44, 48), (56, 60), (10, 40)
THR = 0.1


def pops(root_ids, driven):
    import pandas as pd
    from flight import groups as G
    z = np.load(os.path.join(_ROOT, "data", "neuron_neuropil.npz"), allow_pickle=True)
    nps = list(z["neuropils"])
    dom = z["dominant"]
    _, kc = G.apl_kc_indices(root_ids)
    r2i = G.root_to_index(root_ids)
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_class", "cell_sub_class"])
    ann = ann[ann["root_id"].isin(r2i) & (ann["cell_class"].astype(str) == "ALPN")]
    alpn = ann["root_id"].map(r2i).to_numpy(np.int64)
    uni = ann.loc[ann["cell_sub_class"].astype(str) == "uniglomerular", "root_id"].map(r2i).to_numpy(np.int64)
    return dict(AL=np.flatnonzero((dom == nps.index("AL")) & ~driven), KC=kc,
                LH=np.flatnonzero(dom == nps.index("LH")), ALPN=np.sort(alpn), PN_uni=np.sort(uni),
                not_driven=np.flatnonzero(~driven))


VARIANTS = {"published": dict(nt_impute=False, nt_literature=False),
            "N1": dict(nt_impute=True, nt_literature=False),
            "N2": dict(nt_impute=True, nt_literature=True)}


def run(out, rates, seeds, n_drive, n_post, variant="published"):
    from brian2 import seed as brian_seed
    from flight.brain import FlightBrain, SpikeCounter
    from flight.olfaction_full import OlfactionFull, GROUPS
    from flight import groups as G
    todo = [(r, s) for r in rates for s in seeds if not os.path.exists(f"{out}/o1_r{r}_s{s}.npz")]
    print(f"{len(todo)} runs to do", flush=True)
    if not todo:
        return
    t0 = time.time()
    b = FlightBrain(seed=seeds[0], olfaction_full=True, apl_graded=False, **VARIANTS[variant])
    if variant != "published":
        print(f"MODEL VARIANT {variant}, not the published model: {b.nt_imp_info}", flush=True)
    olf = OlfactionFull(b.root_ids)
    driven = np.zeros(b.n, bool)
    for k in GROUPS:
        driven[b.groups[k]] = True
    P = pops(b.root_ids, driven)
    import pandas as pd
    r2i = G.root_to_index(b.root_ids)
    dn = pd.read_csv(G.PATH_DN)
    dn = dn[dn["root_id"].isin(r2i)]
    dn_idx = dn["root_id"].map(r2i).to_numpy(np.int64)
    b.net.store("fresh")
    print(f"build {time.time() - t0:.0f} s; AL {len(P['AL'])} ALPN {len(P['ALPN'])} DN {len(dn_idx)}", flush=True)
    for r, sd in todo:
        t1 = time.time()
        b.net.restore("fresh")
        brian_seed(sd)
        b.counter = SpikeCounter(b.spk_mon, b.n)
        n_tot = n_drive + n_post
        pr = {p: np.zeros(n_tot) for p in P}
        dn_c = np.zeros((n_tot, len(dn_idx)), np.int16)
        food_rates = {}
        for k in GROUPS:
            food_rates[k] = np.where(olf.food[k], r, 0.0)
        for k in range(n_tot):
            if k < n_drive:
                b.silence_inputs()
                b.set_rates(**food_rates)
            else:
                b.silence_inputs()
            _, c = b.step()
            for p, idx in P.items():
                pr[p][k] = c[idx].sum() / (len(idx) * DT)
            dn_c[k] = c[dn_idx]
            b.counter.t_chunks, b.counter.i_chunks = [], []
        np.savez_compressed(f"{out}/o1_r{r}_s{sd}.npz", rate=r, seed=sd, variant=variant, n_drive=n_drive, n_post=n_post,
                            dn_root_idx=dn_idx, dn_counts=dn_c, n_food_driven=int(sum(v.sum() for v in olf.food.values())),
                            **{f"pop_{p}": v for p, v in pr.items()})
        print(f"r={r} seed={sd}: {time.time() - t1:.0f} s", flush=True)


def report(d):
    rows = {}
    for f in sorted(glob.glob(f"{d}/o1_r*_s*.npz")):
        z = np.load(f)
        r, s = float(z["rate"]), int(z["seed"])
        nd = int(z["n_drive"])
        sl = lambda w: slice(nd + w[0] - 40, nd + w[1] - 40)  # noqa: E731  (windows are in steps from t=0 with 40 drive steps)
        rec = dict(seed=s)
        for p in ("AL", "not_driven"):
            rec[f"W1_{p}"] = float(z[f"pop_{p}"][sl(W1)].mean())
            rec[f"W2_{p}"] = float(z[f"pop_{p}"][sl(W2)].mean())
        rec["pass"] = rec["W1_AL"] < THR and rec["W1_not_driven"] < THR
        for p in ("ALPN", "PN_uni"):
            rec[f"drive_{p}"] = float(z[f"pop_{p}"][nd - 30:nd].mean())
        for p in ("AL", "KC", "LH", "not_driven"):
            rec[f"drive_{p}"] = float(z[f"pop_{p}"][nd - 30:nd].mean())
        rows.setdefault(r, []).append(rec)
    out = {}
    print("rate  pass  W1_AL(min-max)  W1_nd(min-max)  W2_AL(mean)  W2_nd(mean)  ALPN_drive(mean)  PNuni_drive(mean)")
    for r in sorted(rows):
        L = rows[r]
        npass = sum(x["pass"] for x in L)
        out[r] = dict(n=len(L), n_pass=npass, passed=npass == 5 and len(L) == 5, runs=L)
        f = lambda k: [x[k] for x in L]  # noqa: E731
        print(f"{r:6.1f} {npass}/{len(L)} {min(f('W1_AL')):.3f}-{max(f('W1_AL')):.3f} {min(f('W1_not_driven')):.3f}-"
              f"{max(f('W1_not_driven')):.3f} {np.mean(f('W2_AL')):.3f} {np.mean(f('W2_not_driven')):.3f} "
              f"{np.mean(f('drive_ALPN')):.2f} {np.mean(f('drive_PN_uni')):.2f}")
    pn = [np.mean([x["drive_ALPN"] for x in rows[r]]) for r in sorted(rows)]
    inv = int(sum(b < a for a, b in zip(pn, pn[1:])))
    passing = [r for r in sorted(rows) if out[r]["passed"]]
    fails = [r for r in sorted(rows) if out[r]["n_pass"] < out[r]["n"]]
    summ = dict(pn_monotone=inv == 0, pn_inversions=inv, lockup_onset_lowest_rate_with_a_failing_seed=fails[0] if fails else None,
                rates_passing_5of5=passing, o2_rate=max(passing) if passing else None,
                decision="O2 may run at the highest 5/5 rate" if passing else "no rate passes: odour stays off, O2 not run")
    print(json.dumps(summ))
    json.dump(dict(summary=summ, rates={str(k): v for k, v in out.items()}), open(f"{d}/o1_summary.json", "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="o1")
    ap.add_argument("--report")
    ap.add_argument("--variant", choices=list(VARIANTS), default="published")
    ap.add_argument("--rates", type=float, nargs="*", default=RATES)
    ap.add_argument("--seeds", type=int, nargs="*", default=SEEDS)
    ap.add_argument("--n-drive", type=int, default=N_DRIVE)
    ap.add_argument("--n-post", type=int, default=N_POST)
    a = ap.parse_args()
    if a.report:
        report(a.report)
    else:
        os.makedirs(a.out, exist_ok=True)
        with open(f"{a.out}/START_O1", "a") as f:
            f.write(f"{datetime.now().astimezone().isoformat(timespec='seconds')} variant={a.variant}\n")
        print(f"start {datetime.now().astimezone().isoformat(timespec='seconds')} variant={a.variant}", flush=True)
        run(a.out, a.rates, a.seeds, a.n_drive, a.n_post, a.variant)
        open(f"{a.out}/DONE_O1", "w").write("done\n")
