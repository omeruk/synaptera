"""Stage B report (SPEC_SENSORY_INPUTS §3.3b): a --vision-boundary run next to a reference run
(final_b), read-only from the HDF5 files. Markdown to stdout.

    env -u PYTHONPATH python scripts/diag/sb_report.py NEW_H5 REF_H5 [--smoke SMOKE_H5]

Sections: active neurons, neuropil table, hop table (BFS from each run's driven input neurons over
Connectivity_783.parquet), DN / MN rates per flight window, behaviour, criteria B-K1..B-K4, B-K6.
"""
import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from flight import config as cfg  # noqa: E402
from flight import groups as G  # noqa: E402
from flight.readouts import build_readouts  # noqa: E402

DT = 0.025
DATA = G.DATA_DIR


class Run:
    def __init__(self, path):
        self.path = Path(path)
        with h5py.File(path, "r") as f:
            self.meta = {k: (json.loads(v) if isinstance(v, str) and v[:1] in "[{" else v) for k, v in f["meta"].attrs.items()}
            self.b = {k: f["behavior"][k][:] for k in f["behavior"]}
            s = f["spikes"]
            self.step, self.nidx, self.cnt = s["step_idx"][:], s["neuron_idx"][:], s["count"][:].astype(np.int64)
            self.groups = {k: s["groups"][k][:] for k in s["groups"]}
            self.extra = {}
            if "vision_boundary" in f:
                self.extra = {k: f["vision_boundary"][k][:] for k in f["vision_boundary"]}
        self.n_cl = len(self.b["t"])
        self.n_pre = int(-self.step.min()) if len(self.step) else 0
        self.N = 138639
        m = self.step >= 0
        self.count_cl = np.bincount(self.nidx[m], weights=self.cnt[m], minlength=self.N)
        self.rate = self.count_cl / (self.n_cl * DT)
        self.vb = bool(self.meta["flags"].get("vision_boundary"))
        names = ("vbnd_L", "vbnd_R") if self.vb else ("t45_L", "t45_R")
        self.driven = np.zeros(self.N, bool)
        for n in names + ("sugar",):
            self.driven[self.groups[n]] = True
        if not self.meta["flags"].get("no_olfaction"):
            for n in ("orn_food_L", "orn_food_R", "orn_food_C"):
                self.driven[self.groups[n]] = True

    def set_counts(self, idx):
        """Per-step spike counts of a neuron set over all recorded steps (index = step + n_pre)."""
        m = np.isin(self.nidx, idx)
        return np.bincount(self.step[m] + self.n_pre, weights=self.cnt[m], minlength=self.n_pre + self.n_cl)

    def windows(self):
        ph = self.b["phase"]
        code = cfg.PHASE_CODE
        td = np.flatnonzero(ph == code["touchdown"])
        td = int(td[0]) if len(td) else None
        w = {"perch": np.arange(-self.n_pre, -self.n_pre + cfg.CALIB_STEPS), "takeoff": np.arange(0, 4)}
        for p in ("cruise", "approach", "descend"):
            w[p] = np.flatnonzero(ph == code[p])
        if td is not None:
            w["td -4..-1"] = np.arange(max(td - 4, 0), td)
            w["td 0..+3"] = np.arange(td, min(td + 4, self.n_cl))
        w["landed"] = np.flatnonzero(ph == code["landed"])
        return w, td


def neuron_sets(root_ids):
    r2i = G.root_to_index(root_ids)
    ro = build_readouts(root_ids)
    sets = {t: ro[t] for t in ("DNp07", "DNp10", "DNp15", "DNp01", "DNa02", "MN9")}
    dn = pd.read_csv(G.PATH_DN)
    s = dn["side"].astype(str).str.lower()
    sets["MDN"] = {k: G._idx(dn.loc[(dn["cell_type"] == "MDN") & (s == full), "root_id"], r2i)
                   for k, full in (("L", "left"), ("R", "right"))}
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_sub_class", "side"])
    nk = ann[ann["cell_sub_class"] == "neck_motor_neuron"]
    sets["neck MN"] = {k: G._idx(nk.loc[nk["side"] == full, "root_id"], r2i) for k, full in (("L", "left"), ("R", "right"))}
    return sets


def hop_shells(src, pre, post, N, max_hop=4):
    A = sp.csr_matrix((np.ones(len(pre), np.int8), (pre, post)), shape=(N, N))
    hop = np.full(N, -1)
    hop[src] = 0
    front = np.zeros(N, bool)
    front[src] = True
    for h in range(1, 64):
        nxt = (A.T @ front.astype(np.int8)) > 0
        nxt &= hop < 0
        if not nxt.any():
            break
        hop[nxt] = h
        front = nxt
    return np.where(hop > max_hop, max_hop, hop)


def fmt(x, nd=1):
    return "–" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{nd}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("new")
    ap.add_argument("ref")
    ap.add_argument("--smoke", default=None)
    a = ap.parse_args()
    new, ref = Run(a.new), Run(a.ref)
    runs = (("B", new), ("final_b", ref))
    root_ids = G.load_root_ids()
    out = print

    out(f"# Stage B raporu: `{new.path.name}` vs `{ref.path.name}`\n")
    out(f"Closed-loop steps: B {new.n_cl}, final_b {ref.n_cl}; seed {new.meta['seed']} / {ref.meta['seed']}; "
        f"git {new.meta['git_hash']} / {ref.meta['git_hash']}\n")

    # ── active neurons ──
    out("## Active neurons (closed loop, >=1 spike)\n")
    out("| | B n | B % | final_b n | final_b % |\n|---|---|---|---|---|")
    rows = [("Total", lambda r: np.ones(r.N, bool)), ("Driven input neurons", lambda r: r.driven),
            ("Undriven neurons", lambda r: ~r.driven)]
    for name, f in rows:
        v = []
        for _, r in runs:
            m = f(r)
            act = (r.count_cl[m] > 0).sum()
            v += [f"{act:,} / {m.sum():,}", f"{100 * act / m.sum():.2f}"]
        out(f"| {name} | " + " | ".join(v) + " |")
    out("| Network mean Hz | " + " | ".join(f"{r.rate.mean():.2f} | " for _, r in runs).rstrip(" |") + " |")
    out("| Undriven mean Hz | " + " | ".join(f"{r.rate[~r.driven].mean():.3f} | " for _, r in runs).rstrip(" |") + " |")
    out("")

    # ── neuropil ──
    npz = np.load(DATA / "neuron_neuropil.npz")
    npl = npz["neuropils"][npz["dominant"]]
    npl = np.where(npz["frac"] > 0, npl, "(none)")
    out("## By dominant neuropil (L/R pooled; mean Hz = all neurons, active Hz = active neurons only)\n")
    out("| neuropil | n | B active | B % | B mean Hz | B active Hz | final_b active | final_b % | final_b mean Hz |")
    out("|---|---|---|---|---|---|---|---|---|")
    df = pd.DataFrame(dict(npl=npl, rB=new.rate, rR=ref.rate))
    tot = df.groupby("npl").size().sort_values(ascending=False)
    npl_max = {}
    for k in tot.index:
        g = df[df["npl"] == k]
        aB, aR = (g["rB"] > 0).sum(), (g["rR"] > 0).sum()
        npl_max[k] = (g["rB"].mean(), g["rR"].mean())
        if len(g) < 100:
            continue
        out(f"| {k} | {len(g):,} | {aB:,} | {100 * aB / len(g):.1f} | {g['rB'].mean():.2f} | "
            f"{fmt(g.loc[g['rB'] > 0, 'rB'].mean())} | {aR:,} | {100 * aR / len(g):.1f} | {g['rR'].mean():.2f} |")
    small = [k for k in tot.index if tot[k] < 100]
    sm = df[df["npl"].isin(small)]
    out(f"| with <100 neurons: {len(small)} neuropil | {len(sm):,} | {(sm['rB'] > 0).sum()} | | {sm['rB'].mean():.2f} | | "
        f"{(sm['rR'] > 0).sum()} | | {sm['rR'].mean():.2f} |\n")

    # ── hops ──
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_Index", "Postsynaptic_Index"])
    pre, post = con["Presynaptic_Index"].to_numpy(), con["Postsynaptic_Index"].to_numpy()
    del con
    out("## Distance from the input neurons (directed shortest path, all edges; source = the driven inputs of that run)\n")
    out("| hop | B n | B active | B % | B mean Hz | final_b n | final_b active | final_b % | final_b mean Hz |")
    out("|---|---|---|---|---|---|---|---|---|")
    hops = {name: hop_shells(np.flatnonzero(r.driven), pre, post, r.N) for name, r in runs}
    for h, lab in ((0, "0 (input)"), (1, "1"), (2, "2"), (3, "3"), (4, "4+"), (-1, "unreachable")):
        v = []
        for name, r in runs:
            m = hops[name] == h
            act = (r.count_cl[m] > 0).sum()
            v += [f"{m.sum():,}", f"{act:,}", f"{100 * act / max(m.sum(), 1):.1f}", f"{r.rate[m].mean():.2f}" if m.any() else "–"]
        out(f"| {lab} | " + " | ".join(v) + " |")
    m = hops["final_b"]
    out("\nSame shells (by the T4/T5 + sugar source of final_b), in run B:\n")
    out("| hop (final_b source) | n | B active % | B mean Hz | final_b active % | final_b mean Hz |\n|---|---|---|---|---|---|")
    for h, lab in ((0, "0"), (1, "1"), (2, "2"), (3, "3"), (4, "4+"), (-1, "unreachable")):
        mm = m == h
        if not mm.any():
            continue
        out(f"| {lab} | {mm.sum():,} | {100 * (new.count_cl[mm] > 0).mean():.1f} | {new.rate[mm].mean():.2f} | "
            f"{100 * (ref.count_cl[mm] > 0).mean():.1f} | {ref.rate[mm].mean():.2f} |")
    out("")

    # ── DN windows ──
    sets = neuron_sets(root_ids)
    sets["DNg02"] = {"L": new.groups["dng02_L"], "R": new.groups["dng02_R"]}
    out("## DN / MN rates (Hz per neuron, L / R) by window\n")
    for name, r in runs:
        w, td = r.windows()
        out(f"**{name}** (touchdown step {td}; window step counts: "
            + ", ".join(f"{k} {len(v)}" for k, v in w.items()) + ")\n")
        out("| | n L/R | " + " | ".join(w) + " |\n|---|---|" + "---|" * len(w))
        for t, d in sets.items():
            cells = []
            per = {s: r.set_counts(d[s]) for s in "LR"}
            for k, st in w.items():
                if len(st) == 0:
                    cells.append("–")
                    continue
                v = [per[s][st + r.n_pre].sum() / (len(d[s]) * len(st) * DT) for s in "LR"]
                cells.append(f"{v[0]:.1f} / {v[1]:.1f}")
            out(f"| {t} | {len(d['L'])}/{len(d['R'])} | " + " | ".join(cells) + " |")
        out("")

    # ── behaviour ──
    out("## Behaviour\n")
    out("| | B | final_b |\n|---|---|---|")

    def beh(r):
        b = r.b
        w, td = r.windows()
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
        }
    bb, br = beh(new), beh(ref)
    for k in bb:
        out(f"| {k} | {bb[k]} | {br[k]} |")
    out("")

    # ── criteria ──
    out("## Criteria (SPEC §3.3b)\n")
    und = ~new.driven
    m = new.step >= 0
    m_u = m & und[new.nidx]
    per_step_u = np.bincount(new.step[m_u], weights=new.cnt[m_u], minlength=new.n_cl) / (und.sum() * DT)
    q = new.n_cl // 4
    first, last = per_step_u[:q].mean(), per_step_u[-q:].mean()
    mean_u = new.rate[und].mean()
    mx = max(npl_max.items(), key=lambda kv: kv[1][0])
    k1 = mean_u < 5 and last <= 1.5 * first and mx[1][0] <= 50
    out(f"- **B-K1 leakage excitation: {'PASSED' if k1 else 'FAILED'}** — undriven mean {mean_u:.3f} Hz (< 5); "
        f"last/first 25 % = {last:.3f}/{first:.3f} = {last / max(first, 1e-12):.2f} (≤ 1.5); "
        f"highest neuropil mean {mx[0]} {mx[1][0]:.2f} Hz (≤ 50).")
    pr = new.meta["persist_net_rate_hz"]
    k2full = float(np.mean(pr[4:8])) if len(pr) >= 8 else float("nan")
    out(f"- B-K2 (full run, 8 step cut-off): per step {' '.join(f'{x:.3f}' for x in pr)} Hz; 100–200 ms mean "
        f"{k2full:.3f} Hz ({'< 0.1, passed' if k2full < 0.1 else '≥ 0.1, failed'}).")
    if a.smoke:
        sm = Run(a.smoke)
        ps = sm.meta["persist_net_rate_hz"]
        last200 = float(np.mean(ps[-8:]))
        first_below = next((i for i, x in enumerate(ps) if x < 0.1), None)
        out(f"- **B-K2 (smoke, 1 s cut-off): {'PASSED' if last200 < 0.1 else 'FAILED'}** — last 200 ms mean {last200:.4f} Hz; "
            f"first step < 0.1 Hz {first_below} ({'%.0f ms' % (25 * (first_below + 1)) if first_below is not None else '–'}); "
            f"100–200 ms mean {np.mean(ps[4:8]):.4f} Hz; perch network mean {np.mean(sm.meta['perch_net_rate_hz']):.2f} Hz.")
    st_n, st_r = new.b["step_time"].mean(), ref.b["step_time"].mean()
    bt_n, bt_r = new.b["brain_time"].mean(), ref.b["brain_time"].mean()
    k3 = st_n <= 2.0 and new.meta["peak_rss_gb"] <= 8
    out(f"- **B-K3 step time / RAM: {'PASSED' if k3 else 'FAILED'}** — step {st_n:.3f} s vs final_b {st_r:.3f} s "
        f"({100 * (st_n / st_r - 1):+.1f} %); brain {bt_n:.3f} vs {bt_r:.3f} s ({100 * (bt_n / bt_r - 1):+.1f} %); "
        f"tepe RSS {new.meta['peak_rss_gb']:.2f} GB.")
    mn9 = sets["MN9"]
    for name, r in runs:
        c = (r.set_counts(mn9["L"]) + r.set_counts(mn9["R"])) / ((len(mn9["L"]) + len(mn9["R"])) * DT)
        cl = c[r.n_pre:]
        nc = r.b["platform_contact"] == 0
        perch = c[:cfg.CALIB_STEPS]
        val = cl[nc].mean() if nc.any() else float("nan")
        if name == "B":
            out(f"- **B-K4 MN9 without contact: {'PASSED' if val < 10 else 'FAILED'}** — {val:.2f} Hz ({nc.sum()} steps without contact); "
                f"perch {perch.mean():.2f} Hz; steps with contact {cl[~nc].mean() if (~nc).any() else float('nan'):.1f} Hz.")
        else:
            out(f"  - final_b: without contact {val:.2f} Hz, perch {perch.mean():.2f} Hz, with contact "
                f"{cl[~nc].mean() if (~nc).any() else float('nan'):.1f} Hz.")

    # K6
    out("\n### B-K6 double counting (realised / FlyVis target rate, closed-loop means)\n")
    types = [t.decode() for t in new.extra["types"]]
    rows = []
    for s in "LR":
        idx = new.extra[f"idx_{s}"]
        tc = new.extra[f"type_code_{s}"]
        tgt = new.extra[f"target_rate_mean_{s}"].astype(float)
        rows.append(pd.DataFrame(dict(t=[types[k] for k in tc], tgt=tgt, real=new.rate[idx])))
    d = pd.concat(rows)
    out("| type | n | target mean Hz | realised mean Hz | ratio (mean) | median ratio (target >= 1 Hz) | n (≥1 Hz) | note |")
    out("|---|---|---|---|---|---|---|---|")
    for t in types:
        g = d[d["t"] == t]
        h = g[g["tgt"] >= 1]
        med = float((h["real"] / h["tgt"]).median()) if len(h) else float("nan")
        rm = g["real"].mean() / g["tgt"].mean() if g["tgt"].mean() > 0 else float("nan")
        note = "double counting (> 1.5)" if med > 1.5 else ""
        out(f"| {t} | {len(g):,} | {g['tgt'].mean():.2f} | {g['real'].mean():.2f} | {fmt(rm, 2)} | {fmt(med, 2)} | "
            f"{len(h):,} | {note} |")
    out("\nT4/T5 mean ratio per type, with final_b:\n")
    out("| type | B target | B realised | B ratio | final_b target | final_b realised | final_b ratio |\n|---|---|---|---|---|---|---|")
    col = G.load_t45_columns()
    r2i = G.root_to_index(root_ids)
    col = col[col["root_id"].isin(r2i)]
    col["idx"] = col["root_id"].map(r2i)
    ttr = ref.b["t45_type_rate"]           # (n, 2, 8)
    for k, t in enumerate(G.T45_TYPES):
        g = d[d["t"] == t]
        tg_r = float(ttr[:, :, k].mean())
        idx = col.loc[col["type"] == t, "idx"].to_numpy()
        re_r = ref.rate[idx].mean()
        out(f"| {t} | {g['tgt'].mean():.2f} | {g['real'].mean():.2f} | {g['real'].mean() / g['tgt'].mean():.2f} | "
            f"{tg_r:.2f} | {re_r:.2f} | {re_r / tg_r:.2f} |")


if __name__ == "__main__":
    main()
