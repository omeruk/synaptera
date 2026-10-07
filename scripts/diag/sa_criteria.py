"""Stage A open-loop criteria (SPEC_SENSORY_INPUTS §3.2b, pre-registered): --olfaction-full, spiking vs graded APL.

Full brain, only orn_all_L/R/C driven (no vision, no sugar, no AN). Per seed, from the fresh state
(net.restore + brian2.seed). 25 ms steps:
  S 0-39 spontaneous | O 40-79 food odour f = 1 both antennae | P 80-139 spontaneous | X 140-179 all inputs 0
(i)   AL (dominant neuropil AL, driven ORNs excluded) and KC mean rate in steps 120-139 within
      max(0.2 * base, 0.1 Hz) of the base (steps 20-39)
(ii)  KC fraction with >= 1 spike in steps 50-79 in [5 %, 15 %]
(iii) MN9 (CB0701 L/R mean) over steps 0-139 < 10 Hz
K1    steps 0-139: not-driven mean < 5 Hz; last 25 % <= 1.5 x first 25 %; no dominant neuropil > 50 Hz
Recorded: X 100-200 ms (steps 144-147) network rate, AL/KC/LH time course, DN L/R.
Output: sa_criteria_<variant>[_food][_ntLit]_s<seed>.npz (per-step population rates + per-neuron counts per window).
Stage A2 (SPEC §3.2c): --nt-literature builds the brain with the literature NT signs; --food-only drives
only the 6 food glomeruli (orn_food_L/R/C; S/P cfg.ORN_FOOD_RATE[0] = 8 Hz, O cfg.ORN_FOOD_RATE[1] = 150 Hz)
instead of all ORNs; the driven set (excluded from AL and "not driven") is then orn_food.

    env -u PYTHONPATH python scripts/diag/sa_criteria.py --variant spiking|graded [--seeds 0 1 2] [--nt-literature] [--food-only]
    env -u PYTHONPATH python scripts/diag/sa_criteria.py --report sa_criteria_*.npz
"""
import argparse
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402

DT = 0.025
N_S, N_O, N_P, N_X = 40, 40, 60, 40
SEG = dict(base=(20, 40), odor_kc=(50, 80), post=(120, 140), all=(0, 140), first=(0, 35), last=(105, 140),
           x_100_200=(144, 148))
KC_RANGE = (0.05, 0.15)
MN9_MAX, K1_MEAN, K1_RATIO, K1_NP = 10.0, 5.0, 1.5, 50.0


def populations(root_ids, driven):
    from flight import groups as G
    z = np.load(os.path.join(_ROOT, "data", "neuron_neuropil.npz"), allow_pickle=True)
    nps = list(z["neuropils"])
    dom = z["dominant"]
    _, kc = G.apl_kc_indices(root_ids)
    al = np.flatnonzero((dom == nps.index("AL")) & ~driven)
    lh = np.flatnonzero(dom == nps.index("LH"))
    return dict(AL=al, KC=kc, LH=lh, MB_CA=np.flatnonzero(dom == nps.index("MB_CA")),
                not_driven=np.flatnonzero(~driven)), dom, nps


def run(variant, seeds, nt_literature=False, food_only=False):
    from brian2 import seed as brian_seed
    from flight import config as cfg
    from flight.brain import FlightBrain, SpikeCounter
    from flight.olfaction_full import OlfactionFull, GROUPS
    from flight.readouts import Readouts, READOUT_TYPES
    t0 = time.time()
    b = FlightBrain(seed=seeds[0], olfaction_full=not food_only, apl_graded=variant == "graded",
                    nt_literature=nt_literature)
    ro = Readouts(b.root_ids)
    driven = np.zeros(b.n, bool)
    if food_only:
        groups = ("orn_food_L", "orn_food_R", "orn_food_C")
        spont = {k: cfg.ORN_FOOD_RATE[0] for k in groups if k in b.inputs}
        odor = {k: cfg.ORN_FOOD_RATE[1] for k in groups if k in b.inputs}
    else:
        groups = GROUPS
        olf = OlfactionFull(b.root_ids)
        spont, odor = olf.rates(0.0, 0.0), olf.rates(1.0, 1.0)
    for k in groups:
        driven[b.groups[k]] = True
    tag = variant + ("_food" if food_only else "") + ("_ntLit" if nt_literature else "")
    pops, dom, nps = populations(b.root_ids, driven)
    b.net.store("fresh")
    print(f"build {time.time() - t0:.0f} s", flush=True)
    n_tot = N_S + N_O + N_P + N_X
    for sd in seeds:
        t1 = time.time()
        b.net.restore("fresh")
        brian_seed(sd)
        b.counter = SpikeCounter(b.spk_mon, b.n)
        pop_rate = {k: np.zeros(n_tot) for k in pops}
        net = np.zeros(n_tot)
        ro_c = np.zeros((n_tot, len(READOUT_TYPES), 2))
        win = {k: np.zeros(b.n, np.int32) for k in SEG}
        for k in range(n_tot):
            if k < N_S or N_S + N_O <= k < N_S + N_O + N_P:
                b.set_rates(**spont)
            elif k < N_S + N_O:
                b.set_rates(**odor)
            else:
                b.silence_inputs()
            _, c = b.step()
            for p, idx in pops.items():
                pop_rate[p][k] = c[idx].sum() / (len(idx) * DT)
            net[k] = c.sum() / (b.n * DT)
            ro_c[k] = ro.counts(c)
            for w, (a, e) in SEG.items():
                if a <= k < e:
                    win[w] += c
            b.counter.t_chunks, b.counter.i_chunks = [], []
        np.savez_compressed(f"sa_criteria_{tag}_s{sd}.npz", variant=tag, seed=sd, net=net,
                            ro_counts=ro_c, ro_n=ro.n, readout_types=np.array(READOUT_TYPES),
                            dominant=dom, neuropils=np.array(nps), driven=driven,
                            **{f"pop_{p}": v for p, v in pop_rate.items()},
                            **{f"idx_{p}": v for p, v in pops.items()},
                            **{f"win_{w}": v for w, v in win.items()})
        print(f"seed {sd}: {time.time() - t1:.0f} s", flush=True)
        report([f"sa_criteria_{tag}_s{sd}.npz"])


def evaluate(f):
    z = np.load(f, allow_pickle=True)
    r = dict(variant=str(z["variant"]), seed=int(z["seed"]))
    sl = lambda w: slice(*SEG[w])  # noqa: E731
    for p in ("AL", "KC"):
        base, post = z[f"pop_{p}"][sl("base")].mean(), z[f"pop_{p}"][sl("post")].mean()
        tol = max(0.2 * base, 0.1)
        r[f"i_{p}"] = (base, post, tol, abs(post - base) <= tol)
    kc = z["idx_KC"]
    frac = float((z["win_odor_kc"][kc] >= 1).mean())
    r["ii"] = (frac, KC_RANGE[0] <= frac <= KC_RANGE[1])
    types = list(z["readout_types"])
    m = types.index("MN9")
    n_mn9 = z["ro_n"][m]
    mn9 = z["ro_counts"][sl("all"), m, :].sum(0) / (n_mn9 * (SEG["all"][1] - SEG["all"][0]) * DT)
    r["iii"] = (float(mn9.mean()), mn9.mean() < MN9_MAX)
    nd = z["pop_not_driven"]
    mean_nd = nd[sl("all")].mean()
    ratio = nd[sl("last")].mean() / max(nd[sl("first")].mean(), 1e-12)
    cnt = z["win_all"].astype(float) / ((SEG["all"][1] - SEG["all"][0]) * DT)
    dom, nps = z["dominant"], list(z["neuropils"])
    np_rate = {(nps[i] if i >= 0 else "(none)"): float(cnt[dom == i].mean()) for i in np.unique(dom)}
    top = max(np_rate, key=np_rate.get)
    r["K1"] = (mean_nd, ratio, top, np_rate[top], mean_nd < K1_MEAN and ratio <= K1_RATIO and np_rate[top] <= K1_NP)
    r["x_100_200"] = float(z["net"][sl("x_100_200")].mean())
    r["seg_rates"] = {p: [float(z[f"pop_{p}"][a:e].mean()) for a, e in
                          ((20, 40), (50, 80), (80, 120), (120, 140), (144, 148), (160, 180))]
                      for p in ("AL", "KC", "LH", "MB_CA", "not_driven")}
    dn = {}
    for t in ("DNa02", "DNp15", "DNp07", "DNp10", "DNp01", "MN9"):
        i = types.index(t)
        n = np.maximum(z["ro_n"][i], 1)
        dn[t] = [tuple((z["ro_counts"][a:e, i, :].sum(0) / (n * (e - a) * DT)).round(1))
                 for a, e in ((20, 40), (50, 80), (120, 140))]
    r["dn"] = dn
    r["pass"] = r["i_AL"][3] and r["i_KC"][3] and r["ii"][1] and r["iii"][1] and r["K1"][4]
    return r


def report(files):
    ok = lambda x: "passed" if x else "FAILED"  # noqa: E731
    for f in files:
        r = evaluate(f)
        print(f"\n== {r['variant']} seed {r['seed']}: {'PASSED' if r['pass'] else 'FAILED'}")
        for p in ("AL", "KC"):
            b, q, t, o = r[f"i_{p}"]
            print(f"  (i) {p}: baseline {b:.3f} Hz, after 1.0-1.5 s {q:.3f} Hz, tol {t:.3f} -> {ok(o)}")
        print(f"  (ii) KC >=1 spike (odour 250-1000 ms) {100 * r['ii'][0]:.1f} % -> {ok(r['ii'][1])}")
        print(f"  (iii) MN9 steps 0-139 {r['iii'][0]:.2f} Hz -> {ok(r['iii'][1])}")
        m, ra, t, v, o = r["K1"]
        print(f"  K1 undriven {m:.3f} Hz, last/first {ra:.2f}, highest neuropil {t} {v:.1f} Hz -> {ok(o)}")
        print(f"  record: all inputs cut, 100-200 ms network {r['x_100_200']:.3f} Hz")
        print("  window rates (S last 500 ms | odour 250-1000 | cut-off 0-1 s | cut-off 1.0-1.5 s | X 100-200 | X 500-1000):")
        for p, v in r["seg_rates"].items():
            print(f"    {p:10s} " + " | ".join(f"{x:.3f}" for x in v))
        print("  DN L/R Hz (S son 500 ms | koku 250-1000 | kesme 1.0-1.5 s): "
              + "; ".join(f"{t} " + " ".join(f"{a}/{b}" for a, b in v) for t, v in r["dn"].items()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=("spiking", "graded"))
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--report", nargs="+")
    ap.add_argument("--nt-literature", action="store_true")
    ap.add_argument("--food-only", action="store_true")
    a = ap.parse_args()
    if a.report:
        report(a.report)
    else:
        run(a.variant, a.seeds, a.nt_literature, a.food_only)
