"""EXPLORATORY DIAGNOSTIC (post hoc; not a criterion or a decision): who sustains the persistent state after the input is
cut? Reads logs/smell/o1_diag/o1_diag_r10.0_s101.npz (scripts/diag/so_o1_diag.py; one run, 10 Hz, seed 101, spike
count of every neuron in every 25 ms step) and the connectome. Markdown to stdout.

Windows (25 ms steps; drive = steps 0-39): drive 250-1000 ms = steps 10-39; W1 = steps 44-47 (100-200 ms after the cut);
W2 = steps 56-59 (400-500 ms after the cut). Rate = mean spikes per neuron per second; active = share of cells with >= 1 spike
in the window. Synaptic weights are the model's: `Excitatory x Connectivity` of Connectivity_783 (sign x synapse count).

    env -u PYTHONPATH python scripts/diag/o1_diag_report.py [--dir logs/smell/o1_diag]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "diag"))
from flight import groups as G  # noqa: E402
import so_o1  # noqa: E402

DT = so_o1.DT
CONF = {"yüksek": "high", "orta": "medium"}   # Turkish values stored in data/nt_literature_783.csv
WIN = {"drive": (10, 40), "W1": so_o1.W1, "W2": so_o1.W2}


def annotate():
    root_ids = G.load_root_ids()
    r2i = G.root_to_index(root_ids)
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False,
                      usecols=["root_id", "cell_class", "cell_sub_class", "cell_type", "hemibrain_type", "super_class", "top_nt"])
    ann = ann[ann["root_id"].isin(r2i)].copy()
    ann["idx"] = ann["root_id"].map(r2i).astype(np.int64)
    full = pd.DataFrame(index=np.arange(len(root_ids)))
    for c in ("cell_class", "cell_sub_class", "cell_type", "hemibrain_type", "super_class", "top_nt"):
        full[c] = ann.set_index("idx")[c].astype(object).reindex(full.index)
    return root_ids, full


def classes(full, food, orn_all, dom_lh):
    cc, cs, ct = full["cell_class"].astype(str), full["cell_sub_class"].astype(str), full["cell_type"].astype(str)
    m = lambda x: np.asarray(x, bool)  # noqa: E731
    alpn = m(cc == "ALPN")
    d = [("ORN, driven (food glomeruli)", food), ("ORN, not driven", orn_all & ~food),
         ("PN, uniglomerular (ALPN)", alpn & m(cs == "uniglomerular")),
         ("PN, multiglomerular (ALPN)", alpn & m(cs == "multiglomerular")),
         ("PN, other ALPN", alpn & ~m(cs.isin(["uniglomerular", "multiglomerular"]))),
         ("LN (ALLN)", m(cc == "ALLN")), ("ALIN", m(cc == "ALIN")), ("ALON", m(cc == "ALON")),
         ("Kenyon cells", m(cc == "Kenyon_Cell")), ("APL", m(ct == "APL")), ("MBON", m(cc == "MBON")),
         ("LHLN", m(cc == "LHLN")), ("LHCENT", m(cc == "LHCENT"))]
    covered = np.zeros(len(full), bool)
    for _, k in d:
        covered |= k
    d.append(("all other neurons", ~covered))
    d.append(("(overlapping) neurons with dominant neuropil LH", dom_lh))
    return d


def rate(cnt, idx, w):
    a, e = WIN[w]
    return cnt[a:e][:, idx].sum() / (max(len(idx), 1) * (e - a) * DT)


def active(cnt, idx, w):
    a, e = WIN[w]
    return float((cnt[a:e][:, idx].sum(0) >= 1).mean()) if len(idx) else 0.0


def main(dir=str(ROOT / "logs" / "smell" / "o1_diag")):
    z = np.load(f"{dir}/o1_diag_r10.0_s101.npz")
    cnt = z["counts"].astype(np.int64)
    driven, food = z["driven"], z["food"]
    ref = np.load(ROOT / "logs" / "smell" / "o1" / "o1_r10.0_s101.npz")
    dmax = max(float(np.abs(z[f"pop_{p}"] - ref[f"pop_{p}"]).max()) for p in ("AL", "KC", "LH", "ALPN", "not_driven"))
    print(f"- Reproduction check: the population traces (AL, KC, LH, ALPN, not-driven; 80 steps) of this run differ from the "
          f"O1 run `o1_r10.0_s101` by at most {dmax:.1e} Hz.")
    root_ids, full = annotate()
    dom = np.load(ROOT / "data" / "neuron_neuropil.npz", allow_pickle=True)
    nps = list(dom["neuropils"])
    cls = classes(full, food, driven, dom["dominant"] == nps.index("LH"))
    print()
    print("| cell class | cells | rate during the drive, 250–1000 ms (Hz) | rate W1, 100–200 ms after the cut (Hz) | "
          "active in W1 | rate W2, 400–500 ms after the cut (Hz) | active in W2 |")
    print("|---|---|---|---|---|---|---|")
    for lab, k in cls:
        idx = np.flatnonzero(k)
        print(f"| {lab} | {len(idx):,} | {rate(cnt, idx, 'drive'):.2f} | {rate(cnt, idx, 'W1'):.2f} | "
              f"{100 * active(cnt, idx, 'W1'):.1f} % | {rate(cnt, idx, 'W2'):.2f} | {100 * active(cnt, idx, 'W2'):.1f} % |")
    tot = cnt[WIN["W1"][0]:WIN["W1"][1]].sum()
    print()
    print(f"- Whole network in W1: {tot:,} spikes from {int((cnt[WIN['W1'][0]:WIN['W1'][1]].sum(0) >= 1).sum()):,} of "
          f"{cnt.shape[1]:,} neurons.")
    # --- LN types
    ct = full["cell_type"].astype(str)
    ct = ct.where(ct != "nan", "(untyped " + full["cell_class"].astype(str) + ")")
    ln = np.flatnonzero(full["cell_class"].astype(str) == "ALLN")
    rows = []
    for t, idx in pd.Series(ln).groupby(ct.iloc[ln].values):
        idx = idx.to_numpy()
        rows.append((t, len(idx), rate(cnt, idx, "drive"), rate(cnt, idx, "W1"), active(cnt, idx, "W1"), rate(cnt, idx, "W2")))
    rows.sort(key=lambda r: -r[3])
    on = [r for r in rows if r[3] > 0]
    print()
    print(f"**LN types (ALLN, {len(rows)} types), those with a spiking cell in W1 ({len(on)} types), by W1 rate:**")
    print()
    print("| LN type | cells | rate during the drive (Hz) | rate W1 (Hz) | active in W1 | rate W2 (Hz) |")
    print("|---|---|---|---|---|---|")
    for t, n, rd, r1, a1, r2 in on:
        print(f"| {t} | {n} | {rd:.2f} | {r1:.2f} | {100 * a1:.1f} % | {r2:.2f} |")
    # --- top 20 types
    typ = ct
    rows = []
    for t, idx in pd.Series(np.arange(len(typ))).groupby(typ.values):
        idx = idx.to_numpy()
        rows.append((t, len(idx), rate(cnt, idx, "W1"), active(cnt, idx, "W1"), rate(cnt, idx, "W2"),
                     str(full["cell_class"].iloc[idx[0]])))
    rows.sort(key=lambda r: (-r[2], r[0]))
    print()
    print("**The 20 cell types with the highest mean rate in W1** (all types, any size; ties by name):")
    print()
    print("| cell type | cell class | cells | rate W1 (Hz) | active in W1 | rate W2 (Hz) |")
    print("|---|---|---|---|---|---|")
    for t, n, r1, a1, r2, c in rows[:20]:
        print(f"| {t} | {c} | {n} | {r1:.2f} | {100 * a1:.1f} % | {r2:.2f} |")
    # --- ORN inputs
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_Index", "Postsynaptic_Index", "Connectivity",
                                               "Excitatory x Connectivity"])
    pre, post = con["Presynaptic_Index"].to_numpy(np.int64), con["Postsynaptic_Index"].to_numpy(np.int64)
    w, sw = con["Connectivity"].to_numpy(np.int64), con["Excitatory x Connectivity"].to_numpy(np.int64)
    a, e = WIN["W1"]
    spk_pre = cnt[a:e].sum(0)                       # spikes of every presynaptic neuron in W1
    orn_w1 = driven & (spk_pre >= 1)
    pcls = [(n, k) for n, k in cls if n in ("ORN, driven (food glomeruli)", "ORN, not driven", "PN, uniglomerular (ALPN)",
                                            "PN, multiglomerular (ALPN)", "PN, other ALPN", "LN (ALLN)", "ALIN", "ALON")]
    pc = np.full(len(full), len(pcls), np.int64)    # presynaptic class id (first match), last = anything else
    for i, (_, k) in reversed(list(enumerate(pcls))):
        pc[k] = i
    names = [n for n, _ in pcls] + ["any other neuron"]
    n_orn_w1 = int(orn_w1.sum())
    print()
    print(f"**Do the ORNs themselves fire after the cut?** In W1, {n_orn_w1} of {int(driven.sum()):,} ORNs "
          f"({100 * n_orn_w1 / driven.sum():.1f} %) spike at least once "
          f"(driven food ORNs: {int((food & (spk_pre >= 1)).sum())} of {int(food.sum())}; not-driven ORNs: "
          f"{int(((driven & ~food) & (spk_pre >= 1)).sum())} of {int((driven & ~food).sum())}); "
          f"in W2: {int((driven & (cnt[WIN['W2'][0]:WIN['W2'][1]].sum(0) >= 1)).sum())}.")
    print()
    print("Synaptic input of the ORNs (connectome, model signs). Columns: ORN set; incoming synapses (all stored connections, "
          "no threshold); excitatory share of the synapses; then, for the ORNs that spike in W1 only, the presynaptic "
          "spikes in W1 weighted by synapse count and sign (spikes × synapses).")
    print()
    print("| ORN set | cells | incoming synapses | of which from ORNs / PNs / LNs / other | excitatory share (all inputs) | "
          "excitatory share (from ORNs) | excitatory share (from PNs) | excitatory share (from LNs) |")
    print("|---|---|---|---|---|---|---|---|")
    sets = [("driven food ORNs", food), ("not-driven ORNs", driven & ~food), ("all ORNs", driven),
            ("ORNs spiking in W1", orn_w1)]
    for lab, k in sets:
        m = k[post]
        c = pc[pre[m]]
        tot_s = w[m].sum()
        by = lambda ids: w[m][np.isin(c, ids)].sum()  # noqa: E731
        ex = lambda ids: (lambda mm: 100 * w[m][mm & (sw[m] > 0)].sum() / max(w[m][mm].sum(), 1))(np.isin(c, ids))  # noqa: E731
        allm = np.ones_like(c, bool)
        exa = 100 * w[m][sw[m] > 0].sum() / max(tot_s, 1)
        print(f"| {lab} | {int(k.sum()):,} | {tot_s:,} | {100 * by([0, 1]) / tot_s:.1f} % / {100 * by([2, 3, 4]) / tot_s:.1f} % / "
              f"{100 * by([5]) / tot_s:.1f} % / {100 * by([6, 7, 8]) / tot_s:.1f} % | {exa:.1f} % | {ex([0, 1]):.1f} % | "
              f"{ex([2, 3, 4]):.1f} % | {ex([5]):.1f} % |")
    print()
    print("Input events that the spiking ORNs received in W1 (presynaptic spikes in W1 × synapse count; excitatory / inhibitory), "
          "by presynaptic class:")
    print()
    print("| presynaptic class | spikes in W1 | excitatory events | inhibitory events |")
    print("|---|---|---|---|")
    m = orn_w1[post]
    ev = spk_pre[pre[m]] * sw[m]
    tot_e, tot_i = ev[ev > 0].sum(), -ev[ev < 0].sum()
    for i, nm in enumerate(names):
        mm = pc[pre[m]] == i
        pos, neg = ev[mm & (ev > 0)].sum(), -ev[mm & (ev < 0)].sum()
        print(f"| {nm} | {int(spk_pre[pc == i].sum()):,} | {pos:,} ({100 * pos / max(tot_e, 1):.1f} %) | "
              f"{neg:,} ({100 * neg / max(tot_i, 1):.1f} %) |")
    print()
    print(f"- Events onto the spiking ORNs in W1: {tot_e:,} excitatory, {tot_i:,} inhibitory "
          f"(excitatory share {100 * tot_e / max(tot_e + tot_i, 1):.1f} %).")
    pt = ct.to_numpy()[pre[m]]
    df = pd.DataFrame({"type": pt, "ev": ev})
    g = df.groupby("type")["ev"].agg(exc=lambda x: x[x > 0].sum(), inh=lambda x: -x[x < 0].sum())
    g["cells"] = pd.Series(pre[m]).groupby(pt).nunique()
    g = g[g["exc"] > 0].sort_values("exc", ascending=False).head(10)
    lit = pd.read_csv(G.DATA_DIR / "nt_literature_783.csv").set_index("cell_type")
    print()
    print("The 10 presynaptic cell types that supply most of the excitatory events onto the spiking ORNs in W1. "
          "\"Model sign\" = share of the type's output synapses that are excitatory in `Connectivity_783`; "
          "literature transmitter, confidence and Codex `nt_type` of the cells are from `data/nt_literature_783.csv` "
          "(SPEC_SENSORY_INPUTS §3.2c; only the 370 types of that table are listed there, — = not in it; `NaN` = no Codex transmitter, "
          "which the model treats as excitatory). `top_nt` = most frequent transmitter prediction in the FlyWire annotations "
          "(number of cells / cells of the type); it is not the source of the model sign:")
    print()
    print("| presynaptic type | cell class | presynaptic cells | excitatory events | inhibitory events | "
          "share of all excitatory events | model sign (excitatory output synapses) | literature transmitter (confidence) | Codex nt_type | top_nt (annotation) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for t, r in g.iterrows():
        idx = np.flatnonzero((ct == t).to_numpy())
        o = np.isin(pre, idx)
        ex_out = 100 * w[o & (sw > 0)].sum() / max(w[o].sum(), 1)
        li = lit.loc[t] if t in lit.index else None
        ltxt = f"{li['fast_nt']} ({CONF.get(li['confidence'], li['confidence'])})" if li is not None and isinstance(li["fast_nt"], str) else "—"
        ctxt = str(li["codex_nt"]) if li is not None else "—"
        ntm = full["top_nt"].astype(str).iloc[idx].value_counts()
        print(f"| {t} | {full['cell_class'].iloc[idx[0]]} | {int(r['cells'])} | {int(r['exc']):,} | {int(r['inh']):,} | "
              f"{100 * r['exc'] / max(tot_e, 1):.1f} % | {ex_out:.0f} % | {ltxt} | {ctxt} | {ntm.index[0]} ({ntm.iloc[0]}/{len(idx)}) |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "logs" / "smell" / "o1_diag"))
    main(ap.parse_args().dir)
