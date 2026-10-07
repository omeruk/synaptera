"""Step 0 additional analyses: cross-check against the FlyWire Codex v783 downloads (read only).

No Codex file enters the model as a parameter; the LIF parameters, the synapse list and the NT
signs come from Connectivity_783.parquet. The files are read from ~/Downloads
(--codex-dir) and are not copied into the repository.

  1 root_id match: Completeness_783 (138,639) ⊂ neurons.csv (139,255)?
    parquet (pre, post, count, sign) ↔ connections_princeton (>=5 synapses, summed over neuropils)
  2 NT: APL, KC, lLN1_bc and the neurons whose parquet sign disagrees with the Codex nt_type
  3 neuropil: neuropil distribution of the input synapses of the persistent-state core
    (--persist-npz, P0_perch 200-500 ms) and of the asymmetric DNs (neuropil_synapse_table)
  4 T4/T5 -> LPTC -> DN path, per hemisphere with neuropil columns (connections_princeton)
  5 L/R counts: T4a-d/T5a-d, HS, VS; column_assignment, visual_neuron_types,
    consolidated_cell_types, classification, annotations

    env -u PYTHONPATH python scripts/diag/a0_codex.py [--codex-dir ~/Downloads] [--persist-npz a0_counts_main_s0.npz]
"""
import argparse
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from flight import groups as G  # noqa: E402

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 200)

DN_ASYM = ["DNa02", "DNp15", "DNb06", "DNp22", "DNp20", "DNa01", "DNa03", "DNp07", "DNp10"]
LPTC = ["HSN", "HSE", "HSS", "VS", "H2", "LPLC2", "LPLC1", "LLPC1", "LLPC2", "LLPC3", "LPC1", "LPC2",
        "Nod", "CH", "H1", "LPi"]


def section(t):
    print("\n" + "=" * 100 + f"\n{t}\n" + "=" * 100)


def load(codex, name, **kw):
    return pd.read_csv(os.path.join(codex, f"{name}.csv.gz"), **kw)


def rootid_check(codex, rid, con):
    section("1  root_id uyumu")
    neu = load(codex, "neurons", usecols=["root_id"])
    s_codex, s_sim = set(neu.root_id), set(rid.tolist())
    print(f"neurons.csv {len(s_codex):,}; Completeness_783 {len(s_sim):,}; sim ∩ codex {len(s_sim & s_codex):,}; "
          f"sim − codex {len(s_sim - s_codex)}; codex − sim {len(s_codex - s_sim)}")
    cls = load(codex, "classification", usecols=["root_id", "super_class"]).set_index("root_id")
    extra = cls.reindex(sorted(s_codex - s_sim))["super_class"].fillna("(none)")
    print("codex − sim, super_class:", extra.value_counts().to_dict())
    pr = load(codex, "connections_princeton", usecols=["pre_root_id", "post_root_id", "neuropil", "syn_count", "nt_type"])
    agg = pr.groupby(["pre_root_id", "post_root_id"], sort=False)["syn_count"].sum()
    par = con.set_index(["Presynaptic_ID", "Postsynaptic_ID"])["Connectivity"]
    both = agg.index.intersection(par.index)
    d = agg.loc[both].to_numpy() - par.loc[both].to_numpy()
    print(f"princeton (>=5/neuropil) pairs {len(agg):,}; parquet pairs {len(par):,}; common {len(both):,}")
    print(f"  synapse counts equal in common pairs: {100 * (d == 0).mean():.2f}%  (median difference {np.median(d):.0f}, "
          f"max |difference| {np.abs(d).max()})")
    only_pr = agg.index.difference(par.index)
    print(f"  pairs in princeton but not in parquet {len(only_pr):,}; "
          f"pairs with >=5 synapses in parquet but not in princeton {int((par >= 5).sum() - (par.loc[both] >= 5).sum()):,}")
    return pr


def nt_check(codex, rid, ann, con):
    section("2  NT prediction (neurons.csv) and parquet sign")
    nt = load(codex, "neurons").set_index("root_id").reindex(rid)
    ct = ann["cell_type"].reindex(rid).astype(str).to_numpy()
    cols = ["nt_type", "nt_type_score", "ach_avg", "gaba_avg", "glut_avg", "da_avg", "ser_avg", "oct_avg"]
    for lab, m in (("APL", ct == "APL"), ("lLN1_bc", ct == "lLN1_bc")):
        print(f"\n{lab} ({m.sum()}):")
        print(nt.loc[m, cols].assign(side=ann["side"].reindex(rid).to_numpy()[m]).to_string())
    kc = pd.Series(ct).str.startswith("KC").to_numpy()
    print(f"\nKC ({kc.sum()}): nt_type {nt.loc[kc, 'nt_type'].value_counts().to_dict()}; "
          f"nt_type_score medyan {nt.loc[kc, 'nt_type_score'].median():.2f}, "
          f"ach_avg median {nt.loc[kc, 'ach_avg'].median():.2f}, KC with <0.5 {(nt.loc[kc, 'nt_type_score'] < 0.5).sum()}")
    # parquet sign per presynaptic neuron
    sgn = con.groupby("Presynaptic_ID")["Excitatory"].first().reindex(rid)
    exc_nt = nt["nt_type"].isin(["ACH"])
    inh_nt = nt["nt_type"].isin(["GABA", "GLUT"])
    known = sgn.notna() & nt["nt_type"].notna()
    mism = known & (((sgn > 0) & inh_nt) | ((sgn < 0) & exc_nt))
    other = known & ~exc_nt & ~inh_nt
    print(f"\nparquet sign vs Codex nt_type (presynaptic neurons {int(known.sum()):,}): mismatch {int(mism.sum())}; "
          f"DA/SER/OCT (in parquet {sgn[other].map({1: '+', -1: '-'}).value_counts().to_dict()})")
    # auto-synapses / LN self excitation
    selfe = con[(con.Presynaptic_ID == con.Postsynaptic_ID) & (con.Excitatory > 0)]
    lab = ann["cell_type"].reindex(selfe.Presynaptic_ID).astype(str).to_numpy()
    nts = nt["nt_type"].reindex(selfe.Presynaptic_ID).to_numpy()
    sc = nt["nt_type_score"].reindex(selfe.Presynaptic_ID).to_numpy()
    gaba = nt["gaba_avg"].reindex(selfe.Presynaptic_ID).to_numpy()
    ln = pd.Series(lab).str.contains("LN").to_numpy()
    print(f"excitatory autapses (pre == post): {len(selfe):,} neurons; {ln.sum()} of them are LN types")
    if ln.any():
        t = pd.DataFrame(dict(type=lab[ln], nt=nts[ln], score=sc[ln], gaba=gaba[ln],
                              syn=selfe.Connectivity.to_numpy()[ln]))
        print(t.groupby("type").agg(n=("nt", "size"), nt=("nt", lambda x: x.value_counts().to_dict()),
                                    score=("score", "median"), gaba=("gaba", "median"),
                                    syn=("syn", "sum")).sort_values("n", ascending=False).head(15).to_string())
    # the LN population: how many LNs are predicted ACh (excitatory in the model)
    lns = ann.reindex(rid)["cell_class"].astype(str).str.contains("ALLN").to_numpy()
    print(f"\nAL local neurons (cell_class ALLN*: {lns.sum()}): nt_type {nt.loc[lns, 'nt_type'].value_counts().to_dict()}")
    return nt


def persist_mask(path, rid):
    if not path or not os.path.exists(path):
        return None
    R = np.load(path)
    key = "P0_perch__off200_500"
    return R[key] > 0 if key in R else None


def neuropil_check(codex, rid, ann, pmask):
    section("3  neuropil distribution (neuropil_synapse_table, input synapses)")
    nps = load(codex, "neuropil_synapse_table").set_index("root_id").reindex(rid).fillna(0)
    inc = [c for c in nps.columns if c.startswith("input synapses in ")]
    X = nps[inc].to_numpy(np.float64)
    names = [c.replace("input synapses in ", "") for c in inc]
    tot = X.sum(0)
    if pmask is not None:
        pin = X[pmask].sum(0)
        df = pd.DataFrame(dict(persist=pin, frac_persist=pin / pin.sum(), frac_brain=tot / tot.sum()), index=names)
        df["enrich"] = df.frac_persist / df.frac_brain
        ct = ann["cell_type"].reindex(rid).astype(str).fillna("?")
        print(f"persistent core (P0_perch, >=1 spike 200-500 ms after the cut): {pmask.sum()} neurons; "
              f"most frequent types: {ct[pmask].str.replace(r'_.*', '', regex=True).value_counts().head(8).to_dict()}")
        print(df.sort_values("persist", ascending=False).head(14).round(3).to_string())
        # side split of the core
        side = ann["side"].reindex(rid).astype(str).to_numpy()
        print("core side:", pd.Series(side[pmask]).value_counts().to_dict(),
              "| KC core side:", pd.Series(side[pmask & ct.str.startswith("KC").to_numpy()]).value_counts().to_dict())
    dn = pd.read_csv(G.PATH_DN)
    dn["type"] = dn.cell_type.astype(str)
    print("\ninput synapses of the asymmetric readouts (L | R), 5 largest neuropils; total input L/R")
    for t in DN_ASYM:
        rows = []
        for s in ("left", "right"):
            ids = dn.loc[(dn.type == t) & (dn.side == s), "root_id"]
            v = nps.reindex(ids)[inc].sum(0)
            v.index = names
            rows.append(v)
        d = pd.DataFrame(rows, index=["L", "R"]).T
        d = d[(d.L + d.R) > 0]
        top = d.assign(s=d.L + d.R).sort_values("s", ascending=False).head(5)
        print(f"  {t:6s} tot {int(d.L.sum()):5d}/{int(d.R.sum()):5d} | "
              + ", ".join(f"{k} {int(r.L)}/{int(r.R)}" for k, r in top.iterrows()))


def path_check(pr, rid, ann, col):
    section("4  T4/T5 -> LPTC -> DN path (connections_princeton, >=5 synapses, neuropil columns)")
    t45 = col[col["type"].isin(G.T45_TYPES)].set_index("root_id")
    ct = ann["cell_type"].fillna("?").astype(str)
    side = ann["side"].astype(str)
    dn = pd.read_csv(G.PATH_DN).set_index("root_id")
    e = pr[pr.pre_root_id.isin(t45.index)].copy()
    e["hemi"] = t45["hemisphere"].reindex(e.pre_root_id).to_numpy()
    e["post_type"] = ct.reindex(e.post_root_id).fillna("?").to_numpy()
    print("T4/T5 outputs, hemisphere × neuropil (synapses):")
    print(e.pivot_table(index="neuropil", columns="hemi", values="syn_count", aggfunc="sum", fill_value=0)
          .sort_values("left", ascending=False).head(6).to_string())
    lp = e[e.post_type.str.match(r"^(" + "|".join(LPTC) + r")")]
    lp = lp.assign(pt=lp.post_type.str.replace(r"^(VS)\d*.*$", r"\1", regex=True))
    print("\nT4/T5 -> LPTC tipleri (sinaps), hemisfer:")
    print(lp.pivot_table(index="pt", columns="hemi", values="syn_count", aggfunc="sum", fill_value=0)
          .assign(asym=lambda d: (d.left - d.right) / (d.left + d.right)).round(3).to_string())
    # stage 2: LPTC (by side) -> asymmetric DNs
    lptc_ids = ann.index[ct.str.match(r"^(" + "|".join(LPTC) + r")").to_numpy()]
    e2 = pr[pr.pre_root_id.isin(lptc_ids) & pr.post_root_id.isin(dn.index)].copy()
    e2["pre_t"] = ct.reindex(e2.pre_root_id).fillna("?").str.replace(r"^(VS)\d*.*$", r"\1", regex=True).to_numpy()
    e2["pre_s"] = side.reindex(e2.pre_root_id).str[0].str.upper().to_numpy()
    e2["dn"] = dn["cell_type"].reindex(e2.post_root_id).astype(str).to_numpy()
    e2["dn_s"] = dn["side"].reindex(e2.post_root_id).astype(str).str[0].str.upper().to_numpy()
    e2 = e2[e2.dn.isin(DN_ASYM)]
    print("\nLPTC -> asymmetric DN (synapses; row = LPTC_side, column = DN_side, neuropil):")
    print(e2.pivot_table(index=["dn", "pre_t", "pre_s"], columns=["dn_s"], values="syn_count", aggfunc="sum",
                         fill_value=0).to_string())
    print("\nLPTC -> DN neuropils:", e2.groupby("neuropil").syn_count.sum().sort_values(ascending=False).head(8).to_dict())
    # all direct inputs of the asymmetric DNs, per side: total synapses and top presynaptic types
    print("\nall direct inputs of the asymmetric DNs (>=5), total L/R and the presynaptic types with the largest difference:")
    e3 = pr[pr.post_root_id.isin(dn.index)].copy()
    e3["dn"] = dn["cell_type"].reindex(e3.post_root_id).astype(str).to_numpy()
    e3["dn_s"] = dn["side"].reindex(e3.post_root_id).astype(str).str[0].str.upper().to_numpy()
    e3["pre_t"] = ct.reindex(e3.pre_root_id).fillna("?").to_numpy()
    e3["rel"] = np.where(side.reindex(e3.pre_root_id).str[0].str.upper().to_numpy() == e3.dn_s, "i", "c")
    e3["sgn"] = np.where(e3.nt_type.isin(["GABA", "GLUT"]), -1, 1) * e3.syn_count
    for t in ["DNa02", "DNp15", "DNb06", "DNp22"]:
        d = e3[e3.dn == t]
        pv = d.pivot_table(index=["pre_t", "rel"], columns="dn_s", values="sgn", aggfunc="sum", fill_value=0)
        pv["diff"] = pv.get("L", 0) - pv.get("R", 0)
        tot = d.groupby("dn_s").syn_count.sum().to_dict()
        net = d.groupby("dn_s").sgn.sum().to_dict()
        print(f"  {t}: total {tot}, signed net {net}")
        print(pv.reindex(pv["diff"].abs().sort_values(ascending=False).index).head(6).to_string())


def count_check(codex, rid, ann, col):
    section("5  L/R counts: T4/T5 sub-types, HS, VS (across sources)")
    vnt = load(codex, "visual_neuron_types").set_index("root_id")
    cct = load(codex, "consolidated_cell_types").set_index("root_id")
    cls = load(codex, "classification").set_index("root_id")
    sim = set(rid.tolist())
    types = list(G.T45_TYPES)
    rows = {}
    for t in types:
        a = col[col["type"] == t]
        v = vnt[vnt["type"] == t]
        c = cct[cct["primary_type"] == t]
        an = ann[ann["cell_type"].astype(str) == t]
        rows[t] = {
            "colassign L/R": f"{(a.hemisphere == 'left').sum()}/{(a.hemisphere == 'right').sum()}",
            "vis_types L/R": f"{(v.side == 'left').sum()}/{(v.side == 'right').sum()}",
            "consol L/R": "/".join(str((cls["side"].reindex(c.index) == s).sum()) for s in ("left", "right")),
            "annot L/R": f"{(an.side == 'left').sum()}/{(an.side == 'right').sum()}",
            "sim ∩ vt": int(len(set(v.index) & sim)),
            "vt − col": int(len(set(v.index) - set(a.root_id))),
        }
    print(pd.DataFrame(rows).T.to_string())
    for t in ("HSN", "HSE", "HSS", "VS", "H2"):
        m = vnt["type"].astype(str).str.match(rf"^{t}") if t == "VS" else vnt["type"] == t
        ma = ann["cell_type"].astype(str).str.match(rf"^{t}\d*$") if t == "VS" else ann["cell_type"].astype(str) == t
        print(f"  {t:4s} visual_neuron_types L/R {(vnt[m].side == 'left').sum()}/{(vnt[m].side == 'right').sum()}"
              f" | annotations L/R {(ann[ma].side == 'left').sum()}/{(ann[ma].side == 'right').sum()}")
    # column coverage per hemisphere
    t45 = col[col["type"].isin(types)]
    print("\ncolumn coverage (column_assignment, all types / T4-T5):")
    for h in ("left", "right"):
        a = col[col.hemisphere == h]
        b = t45[t45.hemisphere == h]
        per = b.groupby("column_id").size()
        full = b.groupby("column_id")["type"].nunique()
        print(f"  {h:5s}: columns {a.column_id.nunique()} (with T4/T5 {b.column_id.nunique()}), T4/T5 {len(b)}; "
              f"columns with all 8 sub-types {(full == 8).sum()}; mean T4/T5 per column {per.mean():.2f}")
    lc = set(t45[t45.hemisphere == "left"].column_id)
    rc = set(t45[t45.hemisphere == "right"].column_id)
    print(f"  same column_id in both hemispheres: {len(lc & rc)}; only L {len(lc - rc)}, only R {len(rc - lc)}")


def main(a):
    codex = os.path.expanduser(a.codex_dir)
    rid = G.load_root_ids()
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False).set_index("root_id")
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_ID", "Postsynaptic_ID", "Connectivity", "Excitatory"])
    col = pd.read_csv(G.PATH_COLUMNS)
    pr = rootid_check(codex, rid, con)
    nt_check(codex, rid, ann, con)
    del con
    neuropil_check(codex, rid, ann, persist_mask(a.persist_npz, rid))
    path_check(pr, rid, ann, col)
    count_check(codex, rid, ann, col)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--codex-dir", default="~/Downloads")
    ap.add_argument("--persist-npz", default=None)
    main(ap.parse_args())
