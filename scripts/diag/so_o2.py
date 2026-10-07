"""Smell part 2/4, O2 (SPEC_SENSORY_INPUTS §3.4a criteria, §3.4b variant and null control): does the left/right asymmetry of the odour
drive appear as a left/right difference in descending neurons (DNs)? Open loop, whole brain, MODEL VARIANT given by --variant
(N1 / N2; "published" = the published model). Not run unless the §3.4b decision rule selects a variant.

Conditions (1 s = 40 steps of 25 ms from the fresh state, food-glomerulus ORNs only, every other input 0 Hz):
  L    the 153 left food ORNs at rate r        R    the 145 right food ORNs at rate r
  sym  both sides at r                          none all inputs 0
Seeds: discovery 201-203, validation 301-305 (main); null control: shuffled connectomes 401-405 (permutation seed = simulation seed).
Recorded per run: spike counts of all 1,299 DNs per step (.npz). Rates are over steps 10-39 (250-1000 ms).

    env -u PYTHONPATH python scripts/diag/so_o2.py --out DIR --variant N1 --rate 55.4 [--null]
    env -u PYTHONPATH python scripts/diag/so_o2.py --report DIR
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
sys.path.insert(0, os.path.join(_ROOT, "scripts", "diag"))

import numpy as np  # noqa: E402

DT = 0.025
N_STEPS = 40
WIN = (10, 40)
CONDS = ("L", "R", "sym", "none")
DISCOVERY = [201, 202, 203]
VALIDATION = [301, 302, 303, 304, 305]
NULL_SEEDS = [401, 402, 403, 404, 405]
PRIMARY, SECONDARY = "DNa02", "DNae001"
TYPES = (PRIMARY, SECONDARY)


def run(out, variant, rate, seeds, shuffle=False):
    from brian2 import seed as brian_seed
    from flight.brain import FlightBrain, SpikeCounter
    from flight.olfaction_full import OlfactionFull, GROUPS
    from flight import groups as G
    from so_o1 import VARIANTS
    import pandas as pd
    for sd in seeds:
        todo = [c for c in CONDS if not os.path.exists(f"{out}/o2_{c}_s{sd}.npz")]
        if not todo:
            continue
        t0 = time.time()
        b = FlightBrain(seed=sd, olfaction_full=True, apl_graded=False, shuffle_seed=sd if shuffle else None, **VARIANTS[variant])
        olf = OlfactionFull(b.root_ids)
        r2i = G.root_to_index(b.root_ids)
        dn = pd.read_csv(G.PATH_DN)
        dn = dn[dn["root_id"].isin(r2i)]
        dn_idx = dn["root_id"].map(r2i).to_numpy(np.int64)
        b.net.store("fresh")
        print(f"seed {sd} ({'SHUFFLED connectome, ' if shuffle else ''}variant {variant}): build {time.time() - t0:.0f} s", flush=True)
        for c in todo:
            t1 = time.time()
            b.net.restore("fresh")
            brian_seed(sd)
            b.counter = SpikeCounter(b.spk_mon, b.n)
            on = {"L": (rate, 0.0), "R": (0.0, rate), "sym": (rate, rate), "none": (0.0, 0.0)}[c]
            dn_c = np.zeros((N_STEPS, len(dn_idx)), np.int16)
            for k in range(N_STEPS):
                b.silence_inputs()
                b.set_rates(orn_all_L=np.where(olf.food["orn_all_L"], on[0], 0.0),
                            orn_all_R=np.where(olf.food["orn_all_R"], on[1], 0.0),
                            orn_all_C=np.zeros(len(olf.food["orn_all_C"])))
                _, cnt = b.step()
                dn_c[k] = cnt[dn_idx]
                b.counter.t_chunks, b.counter.i_chunks = [], []
            np.savez_compressed(f"{out}/o2_{c}_s{sd}.npz", cond=c, seed=sd, rate=rate, variant=variant, shuffled=shuffle,
                                dn_root_id=dn["root_id"].to_numpy(), dn_type=dn["cell_type"].fillna("(no type)").to_numpy(str),
                                dn_side=dn["side"].astype(str).str.lower().to_numpy(), dn_counts=dn_c)
            print(f"  {c}: {time.time() - t1:.0f} s", flush=True)
        del b


# ---------------------------------------------------------------- analysis
def load(d):
    """{(cond, seed): dict(type, side, hz per cell)} from the npz files of one directory."""
    res = {}
    for f in sorted(glob.glob(f"{d}/o2_*_s*.npz")):
        z = np.load(f)
        hz = z["dn_counts"][WIN[0]:WIN[1]].sum(0) / ((WIN[1] - WIN[0]) * DT)
        res[(str(z["cond"]), int(z["seed"]))] = dict(type=z["dn_type"], side=z["dn_side"], hz=hz, rate=float(z["rate"]),
                                                     variant=str(z["variant"]))
    return res


def type_lr(r, t):
    """Sum of the per-cell Hz of the cells of DN type t on each side (left, right)."""
    m = r["type"] == t
    return float(r["hz"][m & (r["side"] == "left")].sum()), float(r["hz"][m & (r["side"] == "right")].sum())


def effect(l, r):
    return (l - r) / (l + r) if l + r > 0 else float("nan")


def criteria(res, t, seeds):
    """Pre-registered (i)-(iii) for DN type t on the given seeds. Returns dict with per-seed numbers and the verdicts."""
    per = {}
    for s in seeds:
        L, R, S, N = (type_lr(res[(c, s)], t) for c in CONDS)
        per[s] = dict(L=L, R=R, sym=S, none=N,
                      i_L=(L[0] > L[1]), i_R=(R[1] > R[0]),                       # strict; both 0 -> False (silent = fail)
                      ii=(S[0] + S[1] > 0 and abs(S[0] - S[1]) / (S[0] + S[1]) < 0.2),
                      iii=(abs(N[0] - N[1]) < 0.1),
                      eff=dict(L=effect(*L), R=effect(*R), sym=effect(*S), none=effect(*N)))
    v_i = all(p["i_L"] and p["i_R"] for p in per.values())
    v_ii = all(p["ii"] for p in per.values())
    v_iii = all(p["iii"] for p in per.values())
    return dict(per_seed=per, i=v_i, ii=v_ii, iii=v_iii, supported=v_i and v_ii and v_iii)


def exploratory(res, seeds):
    """Ranking on the discovery seeds: types whose L-R sign is + in L-only and - in R-only in ALL seeds, by mean |L-R|/(L+R)."""
    any_r = res[("L", seeds[0])]
    types = sorted(set(any_r["type"]))
    rows = []
    for t in types:
        ok, effs = True, []
        for s in seeds:
            L, R = type_lr(res[("L", s)], t), type_lr(res[("R", s)], t)
            dl, dr = L[0] - L[1], R[0] - R[1]
            ok &= dl > 0 and dr < 0
            effs += [abs(effect(*L)) if L[0] + L[1] > 0 else 0.0, abs(effect(*R)) if R[0] + R[1] > 0 else 0.0]
        if ok:
            rows.append(dict(type=t, mean_effect=float(np.mean(effs)),
                             mean_hz_L=float(np.mean([sum(type_lr(res[("L", s)], t)) for s in seeds]))))
    rows.sort(key=lambda r: -r["mean_effect"])
    return dict(n_types=len(types), n_consistent=len(rows), ranking=rows)


def report(d):
    out = {}
    main = {k: v for k, v in load(d).items() if k[1] < 400}
    if main:
        need = [(c, s) for c in CONDS for s in DISCOVERY + VALIDATION]
        out["complete"] = all(k in main for k in need)
        out["rate"] = next(iter(main.values()))["rate"]
        out["variant"] = next(iter(main.values()))["variant"]
        out["confirmatory"] = {t: criteria(main, t, VALIDATION) for t in TYPES}
        out["flywire_DNa01_reported_separately"] = criteria(main, "DNa01", VALIDATION)
        out["discovery_types"] = {t: criteria(main, t, DISCOVERY)["per_seed"] for t in TYPES}
        out["exploratory"] = exploratory(main, DISCOVERY)
        # all DN rates, per type and side, mean over validation seeds (recorded)
        types = sorted(set(next(iter(main.values()))["type"]))
        out["all_dn_rates"] = {t: {c: [float(np.mean([type_lr(main[(c, s)], t)[i] for s in VALIDATION])) for i in (0, 1)] for c in CONDS}
                               for t in types}
    nd = os.path.join(d, "null")
    if os.path.isdir(nd):
        nul = load(nd)
        out["null"] = {}
        for t in TYPES:
            rows = {}
            for s in NULL_SEEDS:
                if all((c, s) in nul for c in CONDS):
                    rows[s] = criteria(nul, t, [s])["supported"]
            out["null"][t] = dict(reproduces=rows, n_reproduce=int(sum(rows.values())), n_done=len(rows))
    json.dump(out, open(f"{d}/o2_summary.json", "w"), indent=1, default=float)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="o2")
    ap.add_argument("--variant", choices=["published", "N1", "N2"], default="N1")
    ap.add_argument("--rate", type=float)
    ap.add_argument("--null", action="store_true", help="shuffled-connectome null control (seeds 401-405) into OUT/null")
    ap.add_argument("--report")
    a = ap.parse_args()
    if a.report:
        r = report(a.report)
        print(json.dumps({k: v for k, v in r.items() if k in ("complete", "rate", "variant", "null")}, indent=1, default=float))
        for t, c in r.get("confirmatory", {}).items():
            print(t, "i", c["i"], "ii", c["ii"], "iii", c["iii"], "supported", c["supported"])
        e = r.get("exploratory")
        if e:
            print(f"exploratory: {e['n_consistent']} of {e['n_types']} DN types sign-consistent; top: {[x['type'] for x in e['ranking'][:10]]}")
    else:
        assert a.rate is not None, "--rate (the highest rate that passes O1 in 5/5 seeds for the selected variant)"
        out = os.path.join(a.out, "null") if a.null else a.out
        os.makedirs(out, exist_ok=True)
        stamp = datetime.now().astimezone().isoformat(timespec="seconds")
        with open(f"{out}/START_O2", "a") as f:
            f.write(f"{stamp} variant={a.variant} rate={a.rate} null={a.null}\n")
        print(f"start {stamp} variant={a.variant} rate={a.rate} null={a.null}", flush=True)
        run(out, a.variant, a.rate, NULL_SEEDS if a.null else DISCOVERY + VALIDATION, shuffle=a.null)
        open(f"{out}/DONE_O2", "w").write("done\n")
