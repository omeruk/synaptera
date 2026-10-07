"""Smell part 2/4, step 0 (SPEC_SENSORY_INPUTS §3.4b): audit of the neurotransmitter signs of the model. No simulation.

(a) neurons without a Codex v783 nt_type prediction ("empty"): count, the sign the published model gives them, the share of all
    output synapses they carry, super-class / dominant-neuropil distribution; also the neurons without an annotation top_nt.
(b) antennal-lobe local neurons (cell_class ALLN, all types): cells, model sign, annotation top_nt / top_nt_conf, known_nt, output
    synapses, share of the LN output synapses that the model treats as excitatory.
(c) ALLN types whose cells do not agree on the prediction.
(d) what the N1 rule (data/nt_impute_783.csv, scripts/make_nt_impute.py) changes: neurons, edges, synapses, per variant (N2 = N1 + the
    --nt-literature rule, applied after N1).
Numbers come from Connectivity_783.parquet, flywire_annotations.tsv, data/neuron_neuropil.npz, data/nt_modulatory_silent_783.csv,
data/nt_literature_783.csv and data/nt_impute_783.csv only (all in the repository).

    env -u PYTHONPATH .../envs/neurofly/bin/python scripts/diag/nt_audit.py [--json OUT.json]   # markdown tables to stdout
"""
import argparse
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from flight import groups as G  # noqa: E402


def pct(a, b):
    return f"{100.0 * a / b:.1f} %" if b else "—"


def load():
    rid = G.load_root_ids()
    n = len(rid)
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_Index", "Postsynaptic_Index", "Connectivity", "Excitatory"])
    pre = con["Presynaptic_Index"].to_numpy(np.int64)
    w = con["Connectivity"].to_numpy(np.int64)
    s = con["Excitatory"].to_numpy(np.int64)
    exc = np.bincount(pre, weights=w * (s > 0), minlength=n).astype(np.int64)
    inh = np.bincount(pre, weights=w * (s < 0), minlength=n).astype(np.int64)
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False).drop_duplicates("root_id").set_index("root_id").reindex(rid)
    ann["exc"], ann["inh"] = exc, inh
    ann["sign"] = np.where(exc + inh > 0, np.where(exc > 0, 1, -1), 0)
    sil = pd.read_csv(G.PATH_NT_SILENT)
    r2i = G.root_to_index(rid)
    empty = np.zeros(n, bool)
    empty[sil.loc[sil["nt_type"] == "none", "root_id"].map(r2i).to_numpy(np.int64)] = True
    ann["codex_empty"] = empty
    z = np.load(os.path.join(_ROOT, "data", "neuron_neuropil.npz"), allow_pickle=True)
    ann["np_dom"] = np.asarray(z["neuropils"])[np.asarray(z["dominant"])]
    return rid, con, ann


def audit_a(ann):
    e = ann[ann["codex_empty"]]
    tot = int(ann["exc"].sum() + ann["inh"].sum())
    out = {"n_empty": int(len(e)), "n_neurons": int(len(ann)),
           "sign_pos": int((e["sign"] == 1).sum()), "sign_neg": int((e["sign"] == -1).sum()),
           "sign_none": int((e["sign"] == 0).sum()),
           "syn_total": tot, "syn_empty": int(e["exc"].sum() + e["inh"].sum()),
           "syn_empty_exc": int(e["exc"].sum()), "syn_empty_inh": int(e["inh"].sum()),
           "edges_total": None,
           "annot_top_nt_nan": int(ann["top_nt"].isna().sum()),
           "annot_top_nt_nan_and_codex_empty": int((ann["top_nt"].isna() & ann["codex_empty"]).sum()),
           "empty_with_annot_top_nt": e["top_nt"].fillna("NaN").value_counts().to_dict(),
           "empty_no_cell_type": int(e["cell_type"].isna().sum()),
           "super_class": {}, "np_dom": {}}
    for k, col in (("super_class", "super_class"), ("np_dom", "np_dom")):
        a = ann.groupby(ann[col].fillna("(none)"))["codex_empty"].agg(["sum", "size"])
        a = a[a["sum"] > 0].sort_values("sum", ascending=False)
        out[k] = {i: [int(r["sum"]), int(r["size"])] for i, r in a.iterrows()}
    return out


def audit_b(ann):
    l = ann[ann["cell_class"] == "ALLN"].copy()
    l["ct"] = l["cell_type"].fillna("(no type)")
    rows = []
    for t, g in l.groupby("ct"):
        nt = g["top_nt"].fillna("NaN").value_counts()
        kn = g["known_nt"].dropna().unique().tolist()
        ex, ih = int(g["exc"].sum()), int(g["inh"].sum())
        rows.append(dict(type=t, cells=int(len(g)), codex_empty=int(g["codex_empty"].sum()),
                         model_sign_exc_share=ex / (ex + ih) if ex + ih else None,
                         top_nt=";".join(f"{k}{v}" for k, v in nt.items()),
                         top_nt_conf=float(g["top_nt_conf"].mean()) if g["top_nt_conf"].notna().any() else None,
                         known_nt=" | ".join(kn) if kn else "", out_syn=ex + ih, out_syn_exc=ex))
    rows.sort(key=lambda r: -r["out_syn"])
    tot = sum(r["out_syn"] for r in rows)
    exc = sum(r["out_syn_exc"] for r in rows)
    pred = l["top_nt"].fillna("NaN")
    by_pred = {k: [int((pred == k).sum()), int(l.loc[pred == k, "exc"].sum()), int(l.loc[pred == k, "inh"].sum())]
               for k in pred.unique()}
    return dict(n_cells=int(len(l)), n_types=int(len(rows)), n_codex_empty=int(l["codex_empty"].sum()),
                out_syn=tot, out_syn_exc=exc, rows=rows, by_top_nt=by_pred)


def audit_c(ann):
    l = ann[ann["cell_class"] == "ALLN"].copy()
    l["ct"] = l["cell_type"].fillna("(no type)")
    inc = []
    for t, g in l.groupby("ct"):
        nt = g["top_nt"].fillna("NaN")
        signs = set(g.loc[g["sign"] != 0, "sign"])
        ne = int(g["codex_empty"].sum())
        reasons = []
        if nt.nunique() > 1:
            reasons.append("annotation top_nt differs between cells")
        if 0 < ne < len(g):
            reasons.append("some cells have no Codex nt_type, others have")
        if len(signs) > 1:
            reasons.append("model sign differs between cells")
        if reasons:
            inc.append(dict(type=t, cells=int(len(g)), codex_empty=ne, top_nt=";".join(f"{k}{v}" for k, v in nt.value_counts().items()),
                            model_signs=sorted(int(x) for x in signs), reasons=reasons,
                            out_syn=int(g["exc"].sum() + g["inh"].sum())))
    inc.sort(key=lambda r: -r["out_syn"])
    return inc


def audit_d(rid, con, ann):
    """Per variant: neurons / edges / synapses whose sign changes (computed from the same rule the brain applies)."""
    pre = con["Presynaptic_Index"].to_numpy(np.int64)
    w = con["Connectivity"].to_numpy(np.int64)
    s = con["Excitatory"].to_numpy(np.int64)
    n = len(rid)
    imp = pd.read_csv(G.PATH_NT_IMPUTE)
    r2i = G.root_to_index(rid)
    sgn1 = np.zeros(n, np.int64)
    ii = imp["root_id"].map(r2i).to_numpy(np.int64)
    sgn1[ii] = imp["imputed_sign"].to_numpy()
    lidx, lsgn, ltyp = G.nt_literature_indices(rid)
    sgn2 = sgn1.copy()
    sgn2[lidx] = lsgn                       # literature rule applied after N1: it wins where both apply

    def count(sign_of):
        m = sign_of[pre] != 0
        new = np.where(m, sign_of[pre], s)
        ch = new != s
        chn = np.unique(pre[ch])
        return dict(neurons_with_rule=int((sign_of != 0).sum()), neurons_changed=int(len(chn)),
                    edges_changed=int(ch.sum()), edges_total=int(len(pre)),
                    synapses_changed=int(w[ch].sum()), synapses_total=int(w.sum()),
                    syn_exc_to_inh=int(w[ch & (s > 0)].sum()), syn_inh_to_exc=int(w[ch & (s < 0)].sum()),
                    neurons_pos_to_neg=int(len(np.unique(pre[ch & (s > 0)]))),
                    neurons_neg_to_pos=int(len(np.unique(pre[ch & (s < 0)]))))
    N1 = count(sgn1)
    N2 = count(sgn2)
    # N2 alone-literature part and the overlap with N1
    LIT = count(np.where(np.isin(np.arange(n), lidx), np.isin(np.arange(n), lidx) * 0 + _fill(n, lidx, lsgn), 0))
    ann_t = ann["cell_type"].to_numpy(object)
    changed = {}
    for name, sg in (("N1", sgn1), ("N2", sgn2)):
        ch_idx = np.unique(pre[(sg[pre] != 0) & (np.where(sg[pre] != 0, sg[pre], s) != s)])
        ct = pd.Series(ann_t[ch_idx]).fillna("(no type)").value_counts()
        changed[name] = {k: int(v) for k, v in ct.head(15).items()}
    both = int(np.sum((sgn1 != 0) & np.isin(np.arange(n), lidx)))
    is_ln = (ann["cell_class"] == "ALLN").to_numpy()
    aln = {}
    for name, sg in (("N1", sgn1), ("N2", sgn2)):
        ch = (sg[pre] != 0) & (np.where(sg[pre] != 0, sg[pre], s) != s)
        rows = {}
        for i in np.unique(pre[ch]):
            if is_ln[i]:
                t = ann_t[i] if isinstance(ann_t[i], str) else "(no type)"
                r = rows.setdefault(t, [0, 0, 0])
                m = ch & (pre == i)
                r[0] += 1
                r[1] += int(w[m & (s > 0)].sum())
                r[2] += int(w[m & (s < 0)].sum())
        aln[name] = rows
    return dict(N1=N1, N2=N2, literature_alone=LIT, neurons_in_both_rules=both, top_types_changed=changed, alln_changed=aln)


def _fill(n, idx, sgn):
    a = np.zeros(n, np.int64)
    a[idx] = sgn
    return a


def md(a, b, c, d, brief=False):
    L = []
    L.append("**(a) Neurons without a Codex v783 nt_type prediction (\"empty\").**\n")
    L.append(f"- Empty neurons: **{a['n_empty']:,}** of {a['n_neurons']:,} ({pct(a['n_empty'], a['n_neurons'])}); neurons without an "
             f"annotation `top_nt`: {a['annot_top_nt_nan']:,} ({a['annot_top_nt_nan_and_codex_empty']:,} of them also empty in Codex nt_type).")
    L.append(f"- Sign the published model gives the empty neurons (`Excitatory` of `Connectivity_783`): **excitatory {a['sign_pos']:,}**, "
             f"**inhibitory {a['sign_neg']:,}**, no output synapses {a['sign_none']:,}.")
    L.append(f"- Output synapses of the empty neurons: {a['syn_empty']:,} of {a['syn_total']:,} ({pct(a['syn_empty'], a['syn_total'])}); "
             f"treated as excitatory {a['syn_empty_exc']:,} ({pct(a['syn_empty_exc'], a['syn_empty'])}), as inhibitory {a['syn_empty_inh']:,}.")
    L.append(f"- Annotation `top_nt` of the empty neurons: " + ", ".join(f"{k} {v:,}" for k, v in a["empty_with_annot_top_nt"].items()) + ".")
    L.append(f"- Empty neurons without an annotation `cell_type`: {a['empty_no_cell_type']:,}.\n")
    L.append("| super class | empty neurons | all neurons | share empty |\n|---|---|---|---|")
    for k, (e, t) in a["super_class"].items():
        L.append(f"| {k} | {e:,} | {t:,} | {pct(e, t)} |")
    L.append("\n| dominant neuropil (top 12 by empty neurons) | empty neurons | all neurons | share empty |\n|---|---|---|---|")
    for k, (e, t) in list(a["np_dom"].items())[:12]:
        L.append(f"| {k} | {e:,} | {t:,} | {pct(e, t)} |")
    L.append("\n**(b) Antennal-lobe local neurons (ALLN, all types).**\n")
    L.append(f"- {b['n_cells']} cells, {b['n_types']} cell types (cells without a type grouped as \"(no type)\"); Codex-empty cells: {b['n_codex_empty']}.")
    L.append(f"- Output synapses of the ALLN: {b['out_syn']:,}; **treated as excitatory by the model: {b['out_syn_exc']:,} ({pct(b['out_syn_exc'], b['out_syn'])})**.")
    L.append("- By annotation `top_nt` of the cell (cells, excitatory output synapses, inhibitory output synapses): " +
             "; ".join(f"{k}: {v[0]} cells, {v[1]:,} / {v[2]:,}" for k, v in sorted(b["by_top_nt"].items(), key=lambda kv: -kv[1][1] - kv[1][2])) + ".\n")
    L.append("| LN type | cells | Codex-empty cells | model sign (excitatory output synapses) | `top_nt` (annotation, cells) | mean `top_nt_conf` | `known_nt` (annotation) | output synapses |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in b["rows"][:(15 if brief else None)]:
        sg = "—" if r["model_sign_exc_share"] is None else f"{100 * r['model_sign_exc_share']:.0f} %"
        cf = "—" if r["top_nt_conf"] is None else f"{r['top_nt_conf']:.2f}"
        L.append(f"| {r['type']} | {r['cells']} | {r['codex_empty']} | {sg} | {r['top_nt']} | {cf} | {r['known_nt'] or '—'} | {r['out_syn']:,} |")
    if brief:
        L.append(f"\n(15 of {b['n_types']} LN types shown, by output synapses; the full table is the output of `scripts/diag/nt_audit.py`.)")
    L.append(f"\n**(c) LN types whose cells do not agree: {len(c)} of {b['n_types']}.**\n")
    L.append("| LN type | cells | Codex-empty cells | `top_nt` (annotation, cells) | model signs present | what differs | output synapses |\n|---|---|---|---|---|---|---|")
    for r in c[:(10 if brief else None)]:
        L.append(f"| {r['type']} | {r['cells']} | {r['codex_empty']} | {r['top_nt']} | {','.join('+' if x > 0 else '−' for x in r['model_signs'])} | {'; '.join(r['reasons'])} | {r['out_syn']:,} |")
    if brief:
        L.append(f"\n(10 of {len(c)} shown, by output synapses.)")
    L.append("\n**(d) What the variants change (whole brain; rule in SPEC §3.4b).**\n")
    L.append("| variant | neurons with a rule | neurons whose sign changes | excitatory→inhibitory / inhibitory→excitatory neurons | edges changed | synapses changed (of total) | exc→inh synapses | inh→exc synapses |\n|---|---|---|---|---|---|---|---|")
    for name in ("N1", "N2"):
        x = d[name]
        L.append(f"| {name} | {x['neurons_with_rule']:,} | {x['neurons_changed']:,} | {x['neurons_pos_to_neg']:,} / {x['neurons_neg_to_pos']:,} | "
                 f"{x['edges_changed']:,} of {x['edges_total']:,} | {x['synapses_changed']:,} of {x['synapses_total']:,} ({pct(x['synapses_changed'], x['synapses_total'])}) | "
                 f"{x['syn_exc_to_inh']:,} | {x['syn_inh_to_exc']:,} |")
    x = d["literature_alone"]
    L.append(f"\n- The `--nt-literature` rule alone changes {x['neurons_changed']} neurons / {x['edges_changed']:,} edges (SPEC §3.2c: 24 neurons in 8 types); "
             f"{d['neurons_in_both_rules']} neurons have a rule in both N1 and the literature table (the literature sign wins in N2).")
    for name in ("N1", "N2"):
        L.append(f"- Cell types with most changed neurons, {name}: " + ", ".join(f"{k} {v}" for k, v in d["top_types_changed"][name].items()) + ".")
    L.append("\n**(e) ALLN cells whose sign changes** (cells, exc→inh synapses, inh→exc synapses of those cells):\n")
    for name in ("N1", "N2"):
        r = d["alln_changed"][name]
        tot = [sum(v[i] for v in r.values()) for i in range(3)]
        L.append(f"- {name}: **{tot[0]} cells in {len(r)} types**, {tot[1]:,} exc→inh and {tot[2]:,} inh→exc synapses ("
                 f"{pct(tot[1] + tot[2], b['out_syn'])} of the ALLN output synapses): " +
                 (", ".join(f"{k} {v[0]} ({v[1]:,}/{v[2]:,})" for k, v in sorted(r.items(), key=lambda kv: -(kv[1][1] + kv[1][2]))) or "none") + ".")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    rid, con, ann = load()
    A, B, C, D = audit_a(ann), audit_b(ann), audit_c(ann), audit_d(rid, con, ann)
    if a.json:
        json.dump(dict(a=A, b=B, c=C, d=D), open(a.json, "w"), indent=1, default=str)
    print(md(A, B, C, D))


if __name__ == "__main__":
    main()
