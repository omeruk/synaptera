"""Step 0 success criteria (SPEC_BRAIN_CONTROL.md) with the new inputs, full brain.

(a) persistence: every condition is followed by an input cut; network rate in
    0-100, 100-200, 200-500 ms after the cut (criterion: 100-200 ms < 0.1 Hz).
(b) L/R symmetry of the readout sets under symmetric stimulation:
    |L-R|/(L+R) < 0.2 (DNa02, DNg02, DNp01, DNp02/04/11, DNp07+DNp10, MN9).
(c) the R3 matrix with the new inputs (DN types x side, MN9, network stats).

Every condition starts from the same fresh state (net.restore). T4/T5 rates are
the per-step FlyVis sequences of a0_visual.py (a0_visual_rates.npz, 40 steps = 1 s);
food ORNs at the spontaneous 8 Hz unless the condition sets them; ascending 0
(--asc: separate brain with the legacy ascending group, AN conditions only).
Output: a0_counts[_asc]_s{seed}.npz (per-neuron counts per condition and window).

--apl-graded: graded APL output (flight/brain.py APL_GAIN); output a0_counts[_asc]_apl_s{seed}.npz.
--nt-silent broad|narrow: --nt-modulatory-silent variant; suffix _ntsB / _ntsN.

    env -u PYTHONPATH python scripts/diag/a0_criteria.py [--asc] [--apl-graded] [--seed 0] [--only NAME]
    env -u PYTHONPATH python scripts/diag/a0_criteria.py --report a0_counts_s0.npz [a0_counts_asc_s0.npz]
"""
import argparse
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from flight import config as cfg  # noqa: E402
from flight import groups as G  # noqa: E402

BASE = cfg.ORN_FOOD_RATE[0]
T_ON_STEPS = 40                       # 1 s
OFF_WINDOWS = ((0, 4), (4, 8), (8, 20))  # steps after the cut: 0-100, 100-200, 200-500 ms


def conditions(asc=False):
    """name -> dict(rates=..., vis=<visual condition or None>, sym=bool)."""
    o = dict(orn_food_L=BASE, orn_food_R=BASE)
    C = {
        "none": dict(rates={}, vis=None),
        "P0_perch": dict(rates=o, vis="perch", sym=True),          # scene not L/R symmetric
        "P1_air_static": dict(rates=o, vis="air_static", sym=True),
        "O_L150": dict(rates=dict(orn_food_L=150, orn_food_R=BASE), vis="perch"),
        "O_R150": dict(rates=dict(orn_food_L=BASE, orn_food_R=150), vis="perch"),
        "O_LR150": dict(rates=dict(orn_food_L=150, orn_food_R=150), vis="perch", sym=True),
        "O_LR60": dict(rates=dict(orn_food_L=60, orn_food_R=60), vis="perch", sym=True),
        "O_only_LR150": dict(rates=dict(orn_food_L=150, orn_food_R=150), vis=None, sym=True),
        "X_only_orn8": dict(rates=o, vis=None, sym=True),
        "X_only_vis_perch": dict(rates={}, vis="perch", sym=True),
        "X_only_vis_yawR": dict(rates={}, vis="yaw_R"),
        "Y_sym_static": dict(rates={}, vis="sym_static", sym=True),
        "Y_sym_prog": dict(rates={}, vis="sym_prog", sym=True),
        "Y_sym_prog_orn8": dict(rates=o, vis="sym_prog", sym=True),
        "V_yawR": dict(rates=o, vis="yaw_R"),
        "V_yawL": dict(rates=o, vis="yaw_L"),
        "V_prog": dict(rates=o, vis="progressive", sym=True),
        "V_loomL": dict(rates=o, vis="loom_L"),
        "V_loomR": dict(rates=o, vis="loom_R"),
        "S_sugar100": dict(rates=dict(sugar=100), vis=None),
        "S_sugar100_perch": dict(rates=dict(sugar=100, **o), vis="perch"),
    }
    if asc:
        C = {"A_asc22": dict(rates=dict(ascending=22.5, **o), vis="perch", sym=True),
             "A_asc100": dict(rates=dict(ascending=100, **o), vis="perch", sym=True),
             "A_asc22_only": dict(rates=dict(ascending=22.5), vis=None, sym=True)}
    return C


def run(args):
    from flight.brain import FlightBrain, SpikeCounter
    vis = dict(np.load(os.path.join(args.vis_dir, "a0_visual_rates.npz")))
    b = FlightBrain(seed=args.seed, asc_legacy=args.asc, apl_graded=args.apl_graded, nt_silent=args.nt_silent)
    b.net.store("fresh")
    kc_idx = G.apl_kc_indices(b.root_ids)[1]
    res = {}
    for name, c in conditions(args.asc).items():
        if args.only and not name.startswith(args.only):
            continue
        t0 = time.time()
        b.net.restore("fresh")
        b.counter = SpikeCounter(b.spk_mon, b.n)
        b.silence_inputs()
        on = np.zeros(b.n, np.int64)
        per_step = []
        for k in range(T_ON_STEPS):
            r = dict(c["rates"])
            if c["vis"]:
                r["t45_L"] = vis[f"{c['vis']}__t45_L"][k]
                r["t45_R"] = vis[f"{c['vis']}__t45_R"][k]
            b.set_rates(**r)
            _, cnt = b.step()
            if k >= 10:                 # 250-1000 ms: skip the onset transient
                on += cnt
            per_step.append(cnt.sum() / (b.n * 0.025))
        b.silence_inputs()
        off = []
        for k in range(OFF_WINDOWS[-1][1]):
            _, cnt = b.step()
            off.append(cnt)
        off = np.array(off)
        res[f"{name}__on"] = on.astype(np.int32)
        for w0, w1 in OFF_WINDOWS:
            res[f"{name}__off{w0 * 25}_{w1 * 25}"] = off[w0:w1].sum(0).astype(np.int32)
        res[f"{name}__rate_t"] = np.array(per_step, np.float32)
        offr = [off[w0:w1].sum() / (b.n * (w1 - w0) * 0.025) for w0, w1 in OFF_WINDOWS]
        kc = f" KC {100 * (on[kc_idx] > 0).mean():5.1f}%"
        print(f"{name:18s} on {on.sum() / (b.n * 0.75):6.3f} Hz active {100 * (on > 0).mean():5.1f}%{kc} | off "
              + " ".join(f"{x:.4f}" for x in offr) + f" Hz ({time.time() - t0:.0f}s)", flush=True)
        b.counter.t_chunks, b.counter.i_chunks = [], []
    out = f"a0_counts{'_asc' if args.asc else ''}{'_apl' if args.apl_graded else ''}{('_nts' + args.nt_silent[0].upper()) if args.nt_silent else ''}_s{args.seed}.npz"
    np.savez_compressed(out, **res)
    print("wrote", out)


# ── report ───────────────────────────────────────────────────────────────────
READ_SETS = {"DNa02": ["DNa02"], "DNg02": ["DNg02"], "DNp01": ["DNp01"],
             "DNp02/04/11": ["DNp02", "DNp04", "DNp11"], "DNp07+10": ["DNp07", "DNp10"]}
MATRIX_TYPES = ["DNa01", "DNa02", "DNa03", "DNb01", "DNb06", "DNg02", "DNp01", "DNp02", "DNp04", "DNp11",
                "DNp07", "DNp10", "DNp15", "DNp20", "DNp22", "DNp06", "DNg13"]


def report(paths):
    rid = G.load_root_ids()
    r2i = G.root_to_index(rid)
    g = G.build_groups(rid)
    dn = pd.read_csv(G.PATH_DN)
    dn = dn[dn.root_id.isin(r2i)].copy()
    dn["idx"] = dn.root_id.map(r2i)
    dn["type"] = dn.cell_type.astype(str).str.replace(r"^(DNg02)_.*$", r"\1", regex=True)
    dn["s"] = dn.side.astype(str).str[0].str.upper()
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False).set_index("root_id").reindex(rid)
    mn9 = {s[0].upper(): [r2i[r] for r in ann.index[(ann.cell_type.astype(str) == "CB0701") & (ann.side == s)]]
           for s in ("left", "right")}
    is_kc = ann.cell_type.astype(str).str.startswith("KC").to_numpy()
    R = {}
    for p in paths:
        R.update(dict(np.load(p)))
    names = sorted({k.split("__")[0] for k in R}, key=lambda n: list(R).index(f"{n}__on"))
    T_ON = 0.75

    def rate(c, idx):
        return c[idx].sum() / max(len(idx), 1) / T_ON

    print("\n(a) persistence: network mean rate after the input cut (Hz); criterion 100-200 ms < 0.1")
    print(f"{'condition':18s} {'on':>7s} {'0-100':>8s} {'100-200':>8s} {'200-500':>8s}  KC active 200-500 ms, DN spikes/s 200-500, KC active during stimulus")
    n = len(rid)
    for nm in names:
        on = R[f"{nm}__on"].sum() / (n * T_ON)
        o = [R[f"{nm}__off{a}_{b}"].sum() / (n * (b - a) / 1000) for a, b in ((0, 100), (100, 200), (200, 500))]
        late = R[f"{nm}__off200_500"]
        dnr = late[dn.idx].sum() / 0.3
        print(f"{nm:18s} {on:7.3f} {o[0]:8.4f} {o[1]:8.4f} {o[2]:8.4f}  {'PASS' if o[1] < 0.1 else 'FAIL'}  "
              f"KC {int((late[is_kc] > 0).sum())}, DN {dnr:.0f}/s, KC on {100 * (R[f'{nm}__on'][is_kc] > 0).mean():.1f}%")

    print("\n(b) L/R symmetry under symmetric stimulation: |L-R|/(L+R) (Hz per neuron L/R), criterion < 0.2")
    sym = {k: v.get("sym", False) for k, v in {**conditions(False), **conditions(True)}.items()}
    for nm in names:
        if not sym.get(nm):
            continue
        c = R[f"{nm}__on"]
        cells = []
        for lab, types in READ_SETS.items():
            L = rate(c, dn.idx[dn.type.isin(types) & (dn.s == "L")].to_numpy())
            Rr = rate(c, dn.idx[dn.type.isin(types) & (dn.s == "R")].to_numpy())
            cells.append((lab, L, Rr))
        cells.append(("MN9", rate(c, np.array(mn9["L"])), rate(c, np.array(mn9["R"]))))
        txt = []
        for lab, L, Rr in cells:
            if L + Rr == 0:
                txt.append(f"{lab} 0/0 silent")
            else:
                a = abs(L - Rr) / (L + Rr)
                txt.append(f"{lab} {L:.1f}/{Rr:.1f} {a:.2f}{'' if a < 0.2 else ' FAIL'}")
        print(f"  {nm:16s} " + " | ".join(txt))

    print("\n(c) R3 matrix, new inputs (Hz per neuron, 250-1000 ms; L/R)")
    rows = {}
    for nm in names:
        c = R[f"{nm}__on"]
        r = {t: f"{rate(c, dn.idx[(dn.type == t) & (dn.s == 'L')].to_numpy()):.0f}/"
                f"{rate(c, dn.idx[(dn.type == t) & (dn.s == 'R')].to_numpy()):.0f}" for t in MATRIX_TYPES}
        r["MN9"] = f"{rate(c, np.array(mn9['L'])):.0f}/{rate(c, np.array(mn9['R'])):.0f}"
        r["allDN L-R"] = f"{(c[g['dn_L']].sum() - c[g['dn_R']].sum()) / T_ON:.0f}"
        r["net Hz"] = f"{c.sum() / (n * T_ON):.2f}"
        r["KC act"] = int((c[is_kc] > 0).sum())
        rows[nm] = r
    df = pd.DataFrame(rows).T
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    half = len(MATRIX_TYPES) // 2 + 1
    print(df[MATRIX_TYPES[:half]].to_string())
    print(df[MATRIX_TYPES[half:] + ["MN9", "allDN L-R", "net Hz", "KC act"]].to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--asc", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--only", default=None)
    ap.add_argument("--apl-graded", action="store_true")
    ap.add_argument("--nt-silent", choices=("broad", "narrow"), default=None)
    ap.add_argument("--vis-dir", default=".")
    ap.add_argument("--report", nargs="+", default=None)
    a = ap.parse_args()
    if a.report:
        report(a.report)
    else:
        run(a)
