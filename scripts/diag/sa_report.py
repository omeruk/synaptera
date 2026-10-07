"""Stage A report (SPEC_SENSORY_INPUTS §3.2b): an --olfaction-full run next to final_sB, read-only from
the HDF5 files. Markdown to stdout.

    env -u PYTHONPATH python scripts/diag/sa_report.py NEW_H5 REF_H5 [--smoke SMOKE_H5 ...]

Sections: active neurons, neuropil table, KC sparseness per window, DN / MN rates per window, DN L-R vs
odour asymmetry, behaviour, criteria B-K1..B-K4 (driven = orn_all / orn_food, vbnd / t45, sugar, leg_sugar).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flight import config as cfg  # noqa: E402
from flight import groups as G  # noqa: E402
from flight.readouts import READOUT_TYPES  # noqa: E402
from sb_report import DATA, DT, Run, fmt, neuron_sets  # noqa: E402

INPUTS = ("orn_all_L", "orn_all_R", "orn_all_C", "orn_food_L", "orn_food_R", "orn_food_C", "leg_sugar")


class RunA(Run):
    def __init__(self, path):
        super().__init__(path)
        fl = self.meta["flags"]
        names = []
        if fl.get("olfaction_full"):
            names += ["orn_all_L", "orn_all_R", "orn_all_C"]
        if fl.get("leg_grn"):
            names += ["leg_sugar"]
        for n in names:
            self.driven[self.groups[n]] = True
        self.label = ("A" if fl.get("olfaction_full") else "?") + (" graded" if fl.get("apl_graded") else " spiking")


def k1(r, npl):
    und = ~r.driven
    m = (r.step >= 0) & und[r.nidx]
    per = np.bincount(r.step[m], weights=r.cnt[m], minlength=r.n_cl) / (und.sum() * DT)
    q = r.n_cl // 4
    first, last = per[:q].mean(), per[-q:].mean()
    df = pd.DataFrame(dict(npl=npl, r=r.rate)).groupby("npl")["r"].mean()
    return r.rate[und].mean(), first, last, df.idxmax(), df.max()


def criteria(r, npl, sets, name, out):
    mean_u, first, last, top, topv = k1(r, npl)
    ok = mean_u < 5 and last <= 1.5 * first and topv <= 50
    out(f"- **B-K1 leakage excitation ({name}): {'PASSED' if ok else 'FAILED'}** — undriven mean {mean_u:.3f} Hz (< 5); "
        f"last/first 25 % = {last:.3f}/{first:.3f} = {last / max(first, 1e-12):.2f} (≤ 1.5); highest neuropil mean "
        f"{top} {topv:.2f} Hz (≤ 50).")
    pr = r.meta["persist_net_rate_hz"]
    if len(pr) >= 40:
        last200 = float(np.mean(pr[-8:]))
        fb = next((i for i, x in enumerate(pr) if x < 0.1), None)
        out(f"- **B-K2 ({name}, 1 s cut-off): {'PASSED' if last200 < 0.1 else 'FAILED'}** — last 200 ms mean {last200:.4f} Hz; "
            f"first step < 0.1 Hz {fb}; 100–200 ms mean {np.mean(pr[4:8]):.4f} Hz; perch network mean "
            f"{np.mean(r.meta['perch_net_rate_hz']):.2f} Hz; cut-off course: "
            + " ".join(f"{x:.2f}" for x in pr[::5]) + " Hz (every 5th step).")
    elif len(pr) >= 8:
        v = float(np.mean(pr[4:8]))
        out(f"- B-K2 ({name}, {len(pr)} step cut-off): per step {' '.join(f'{x:.3f}' for x in pr)} Hz; 100–200 ms mean "
            f"{v:.3f} Hz ({'< 0.1, passed' if v < 0.1 else '≥ 0.1, FAILED'}).")
    st, bt, rss = r.b["step_time"].mean(), r.b["brain_time"].mean(), r.meta["peak_rss_gb"]
    out(f"- **B-K3 ({name}): {'PASSED' if st <= 2.0 and rss <= 8 else 'FAILED'}** — mean step {st:.3f} s, brain {bt:.3f} s, "
        f"tepe RSS {rss:.2f} GB.")
    mn9 = sets["MN9"]
    c = (r.set_counts(mn9["L"]) + r.set_counts(mn9["R"])) / ((len(mn9["L"]) + len(mn9["R"])) * DT)
    cl, nc = c[r.n_pre:], r.b["platform_contact"] == 0
    val = cl[nc].mean() if nc.any() else float("nan")
    out(f"- **B-K4 MN9 without contact ({name}): {'PASSED' if val < 10 else 'FAILED'}** — {val:.2f} Hz ({nc.sum()} steps without contact); "
        f"perch {c[:cfg.CALIB_STEPS].mean():.2f} Hz; with contact {cl[~nc].mean() if (~nc).any() else float('nan'):.1f} Hz.")


def kc_table(runs, kc, out):
    out("| window | " + " | ".join(f"{n} KC ≥1 spike % | {n} KC mean Hz" for n, _ in runs) + " |")
    out("|---|" + "---|---|" * len(runs))
    wins = {n: r.windows()[0] for n, r in runs}
    for k in wins[runs[0][0]]:
        cells = []
        for n, r in runs:
            st = wins[n].get(k, [])
            if len(st) == 0:
                cells += ["–", "–"]
                continue
            m = np.isin(r.step, st) & np.isin(r.nidx, kc)
            per = np.bincount(r.nidx[m], weights=r.cnt[m], minlength=r.N)[kc]
            cells += [f"{100 * (per > 0).mean():.1f}", f"{per.sum() / (len(kc) * len(st) * DT):.2f}"]
        out(f"| {k} ({len(wins[runs[0][0]][k])} steps) | " + " | ".join(cells) + " |")


def lr_odor(r, sets, out, name):
    b = r.b
    on = b["wings_on"].astype(bool)
    x = {"I_asym": b["I_asym"][on], "odor_L−R": (b["odor_L"] - b["odor_R"])[on],
         "ORN besin L−R Hz": (b["olf_rate_L"] - b["olf_rate_R"])[on]}
    ro = b["dn_readout"][on].astype(float)                 # (n, types, 2) counts per 25 ms
    ys = {t: ro[:, READOUT_TYPES.index(t), 0] - ro[:, READOUT_TYPES.index(t), 1] for t in ("DNa02", "DNp15", "DNp07",
                                                                                        "DNp10", "DNp01")}
    ys["all DNs"] = (b["all_dn_L"] - b["all_dn_R"])[on].astype(float)
    out(f"**{name}** (wings on {on.sum()} steps; Pearson r, left − right count; |r| < 0.18 ≈ p > 0.05)\n")
    out("| DN L−R | " + " | ".join(x) + " |\n|---|" + "---|" * len(x))
    for t, y in ys.items():
        cells = []
        for v in x.values():
            cells.append("–" if y.std() == 0 or v.std() == 0 else f"{np.corrcoef(y, v)[0, 1]:+.2f}")
        out(f"| {t} | " + " | ".join(cells) + " |")
    out(f"\nOdour asymmetry range: I_asym {x['I_asym'].min():+.3f}…{x['I_asym'].max():+.3f}; ORN besin L−R "
        f"{x['ORN besin L−R Hz'].min():+.1f}…{x['ORN besin L−R Hz'].max():+.1f} Hz.\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("new")
    ap.add_argument("ref")
    ap.add_argument("--smoke", nargs="*", default=[])
    a = ap.parse_args()
    new, ref = RunA(a.new), RunA(a.ref)
    new.label = "A"
    ref.label = "final_sB"
    runs = (("A", new), ("final_sB", ref))
    root_ids = G.load_root_ids()
    out = print
    npz = np.load(DATA / "neuron_neuropil.npz")
    npl = np.where(npz["frac"] > 0, npz["neuropils"][npz["dominant"]], "(none)")
    sets = neuron_sets(root_ids)
    sets["DNg02"] = {"L": new.groups["dng02_L"], "R": new.groups["dng02_R"]}
    _, kc = G.apl_kc_indices(root_ids)

    out(f"# Stage A raporu: `{new.path.name}` vs `{ref.path.name}`\n")
    out(f"Closed-loop steps: A {new.n_cl}, final_sB {ref.n_cl}; seed {new.meta['seed']} / {ref.meta['seed']}; "
        f"git {new.meta['git_hash']} / {ref.meta['git_hash']}; APL: {new.meta['apl'].get('mechanism')}\n")

    out("## Active neurons (closed loop, >=1 spike)\n")
    out("| | A n | A % | final_sB n | final_sB % |\n|---|---|---|---|---|")
    for name, f in (("Total", lambda r: np.ones(r.N, bool)), ("Driven input neurons", lambda r: r.driven),
                    ("Undriven neurons", lambda r: ~r.driven)):
        v = []
        for _, r in runs:
            m = f(r)
            act = (r.count_cl[m] > 0).sum()
            v += [f"{act:,} / {m.sum():,}", f"{100 * act / m.sum():.2f}"]
        out(f"| {name} | " + " | ".join(v) + " |")
    out("| Network mean Hz | " + " | ".join(f"{r.rate.mean():.2f} | " for _, r in runs).rstrip(" |") + " |")
    out("| Undriven mean Hz | " + " | ".join(f"{r.rate[~r.driven].mean():.3f} | " for _, r in runs).rstrip(" |") + " |\n")

    out("## By dominant neuropil (L/R pooled; mean Hz = all neurons, active Hz = active neurons only)\n")
    out("| neuropil | n | A active | A % | A mean Hz | A active Hz | final_sB active | final_sB % | final_sB mean Hz |")
    out("|---|---|---|---|---|---|---|---|---|")
    df = pd.DataFrame(dict(npl=npl, rA=new.rate, rR=ref.rate))
    tot = df.groupby("npl").size().sort_values(ascending=False)
    for k in tot.index:
        g = df[df["npl"] == k]
        if len(g) < 100:
            continue
        aA, aR = (g["rA"] > 0).sum(), (g["rR"] > 0).sum()
        out(f"| {k} | {len(g):,} | {aA:,} | {100 * aA / len(g):.1f} | {g['rA'].mean():.2f} | "
            f"{fmt(g.loc[g['rA'] > 0, 'rA'].mean())} | {aR:,} | {100 * aR / len(g):.1f} | {g['rR'].mean():.2f} |")
    small = [k for k in tot.index if tot[k] < 100]
    sm = df[df["npl"].isin(small)]
    out(f"| with <100 neurons: {len(small)} neuropil | {len(sm):,} | {(sm['rA'] > 0).sum()} | | {sm['rA'].mean():.2f} | | "
        f"{(sm['rR'] > 0).sum()} | | {sm['rR'].mean():.2f} |\n")
    from flight.olfaction_full import orn_groups
    orn = np.zeros(new.N, bool)
    for v in orn_groups(root_ids).values():
        orn[v] = True
    al = (npl == "AL") & ~orn
    out(f"AL without ORNs ({al.sum():,} neuron; PN/LN vb.): A ort. {new.rate[al].mean():.2f} Hz, active "
        f"{100 * (new.count_cl[al] > 0).mean():.1f} %; final_sB ort. {ref.rate[al].mean():.2f} Hz. "
        f"All ORNs ({orn.sum():,}): A ort. {new.rate[orn].mean():.2f} Hz; driven ORNs "
        f"({(orn & new.driven).sum():,}): {new.rate[orn & new.driven].mean():.2f} Hz.\n")

    out("## KC sparseness (5,177 KC; fraction with >=1 spike in the window, and mean rate)\n")
    kc_table(runs, kc, out)
    out("")

    out("## DN / MN rates (Hz per neuron, L / R) by window\n")
    for name, r in runs:
        w, td = r.windows()
        out(f"**{name}** (touchdown step {td}; window step counts: " + ", ".join(f"{k} {len(v)}" for k, v in w.items())
            + ")\n")
        out("| | n L/R | " + " | ".join(w) + " |\n|---|---|" + "---|" * len(w))
        for t, d in sets.items():
            per = {s: r.set_counts(d[s]) for s in "LR"}
            cells = []
            for k, st in w.items():
                if len(st) == 0:
                    cells.append("–")
                    continue
                v = [per[s][st + r.n_pre].sum() / (len(d[s]) * len(st) * DT) for s in "LR"]
                cells.append(f"{v[0]:.1f} / {v[1]:.1f}")
            out(f"| {t} | {len(d['L'])}/{len(d['R'])} | " + " | ".join(cells) + " |")
        out("")

    out("## DN left−right difference and odour direction (descriptive; the direction term is fixed by ablation)\n")
    for name, r in runs:
        lr_odor(r, sets, out, name)

    out("## Behaviour\n")
    out("| | A | final_sB |\n|---|---|---|")

    def beh(r):
        b = r.b
        _, td = r.windows()
        fd = np.flatnonzero(b["is_feeding"] > 0)
        return {
            "touchdown step (t s)": f"{td} ({b['t'][td]:.3f})" if td is not None else "none",
            "touchdown speed mm/s": fmt(float(b["speed"][td]), 1) if td is not None else "–",
            "distance to food min / final mm": f"{b['dist_to_food'].min():.1f} / {b['dist_to_food'][-1]:.1f}",
            "feeding steps (first)": f"{len(fd)} ({fd[0] if len(fd) else '–'})",
            "tower contact steps": int(b["tower_contact"].sum()),
            "max tower penetration mm": f"{float(b['tower_penetration'].max()):.4f}",
            "turn_brain (ablation baseline) mean": f"{b['turn_brain'].mean():+.3f}",
            "turn_brain share (sum|brain|/sum|total|)": fmt(r.meta.get("turn_share", {}).get("brain_over_total"), 3),
            "mean step s / brain s": f"{b['step_time'].mean():.3f} / {b['brain_time'].mean():.3f}",
            "tepe RSS GB": f"{r.meta['peak_rss_gb']:.2f}",
            "perch network mean Hz": f"{np.mean(r.meta['perch_net_rate_hz']):.2f}",
        }
    bb, br = beh(new), beh(ref)
    for k in bb:
        out(f"| {k} | {bb[k]} | {br[k]} |")
    out("")

    out("## Criteria (SPEC §3.2b / §3.3b)\n")
    criteria(new, npl, sets, "full run A", out)
    criteria(ref, npl, sets, "final_sB", out)
    for s in a.smoke:
        sm = RunA(s)
        criteria(sm, npl, sets, f"smoke {sm.path.name}", out)


if __name__ == "__main__":
    main()
