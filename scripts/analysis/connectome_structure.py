"""Structural analysis of the FlyWire v783 connectome as loaded by the Shiu et al. LIF model (analysis only; no simulation).

Reads brain_model/Completeness_783.csv, Connectivity_783.parquet, flywire_annotations.tsv and the derived
data/sugar_grn_783.csv, data/leg_sugar_grn_783.csv, brain_model/descending_neurons.csv (scripts/fetch_data.py).
Writes every number to a JSON file (docs/tr/analiz/veri/connectome_stats.json); the reading is in
docs/tr/analiz/02_MODEL_FIZIK_TEST_ANALIZI.md section 1.

Contents: global graph statistics; LIF arithmetic of the Shiu parameters; sugar / leg GRN -> MN9 hop distance and signed
linear influence; inputs of MN9, DNg02, DNp15, DNa02, DNa01, DNp01, DNp07, DNp10 by side; hop distance from T4/T5 and
VPNs to the DNs; antennal-lobe LN/PN excitation and leading eigenvalue; motor neurons in the model; left/right totals.

    env -u PYTHONPATH python scripts/analysis/connectome_structure.py [--root .] [--out docs/tr/analiz/veri/connectome_stats.json]
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

import argparse  # noqa: E402

_ap = argparse.ArgumentParser()
_ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
_ap.add_argument("--out", default=None)
_a = _ap.parse_args()
ROOT = Path(_a.root)
OUT = Path(_a.out) if _a.out else ROOT / "docs/tr/analiz/veri/connectome_stats.json"
R = {}

comp = pd.read_csv(ROOT / "brain_model/Completeness_783.csv", index_col=0)
rid = comp.index.to_numpy(np.int64)
N = len(rid)
r2i = pd.Series(np.arange(N), index=rid)
con = pd.read_parquet(ROOT / "brain_model/Connectivity_783.parquet")
pre = con["Presynaptic_Index"].to_numpy()
post = con["Postsynaptic_Index"].to_numpy()
cnt = con["Connectivity"].to_numpy().astype(np.int64)
sgn = con["Excitatory"].to_numpy()          # +1 / -1 per edge (presynaptic NT sign)
wsig = con["Excitatory x Connectivity"].to_numpy().astype(np.int64)
del con

ann = pd.read_csv(ROOT / "brain_model/flywire_annotations.tsv", sep="\t", low_memory=False)
ann = ann.drop_duplicates("root_id").set_index("root_id").reindex(rid)
sc = ann["super_class"].fillna("NA").to_numpy()
cc = ann["cell_class"].fillna("NA").to_numpy()
ct = ann["cell_type"].fillna(ann["hemibrain_type"]).fillna("NA").to_numpy()
side = ann["side"].fillna("NA").to_numpy()
top_nt = ann["top_nt"].fillna("NA").to_numpy()

# ── global ────────────────────────────────────────────────────────────────
indeg = np.bincount(post, minlength=N)
outdeg = np.bincount(pre, minlength=N)
insyn = np.bincount(post, weights=cnt, minlength=N)
outsyn = np.bincount(pre, weights=cnt, minlength=N)
exc_in = np.bincount(post, weights=np.where(sgn > 0, cnt, 0), minlength=N)
inh_in = np.bincount(post, weights=np.where(sgn < 0, cnt, 0), minlength=N)
pre_sign = np.zeros(N, int)
pre_sign[pre] = sgn
R["global"] = dict(
    neurons=int(N), edges=int(len(pre)), synapses=int(cnt.sum()),
    edges_exc=int((sgn > 0).sum()), edges_inh=int((sgn < 0).sum()),
    syn_exc=int(cnt[sgn > 0].sum()), syn_inh=int(cnt[sgn < 0].sum()),
    neurons_exc=int((pre_sign > 0).sum()), neurons_inh=int((pre_sign < 0).sum()), neurons_no_output=int((outdeg == 0).sum()),
    neurons_no_input=int((indeg == 0).sum()), self_loops=int((pre == post).sum()),
    min_edge_syn=int(cnt.min()), median_edge_syn=float(np.median(cnt)), max_edge_syn=int(cnt.max()),
    in_edges_mean=float(indeg.mean()), in_edges_median=float(np.median(indeg)), in_edges_max=int(indeg.max()),
    in_syn_mean=float(insyn.mean()), in_syn_median=float(np.median(insyn)), in_syn_p99=float(np.percentile(insyn, 99)),
    out_syn_max=int(outsyn.max()),
)
# reciprocity
key = pre.astype(np.int64) * N + post
rkey = post.astype(np.int64) * N + pre
R["global"]["reciprocal_edge_fraction"] = float(np.isin(key, rkey, assume_unique=False).mean())
R["super_class_neurons"] = pd.Series(sc).value_counts().to_dict()
R["side_neurons"] = pd.Series(side).value_counts().to_dict()
# synapse totals by super_class of pre and post
df = pd.DataFrame(dict(a=sc[pre], b=sc[post], n=cnt))
R["syn_by_class_pair_top"] = {f"{k[0]}->{k[1]}": int(v) for k, v in
                              df.groupby(["a", "b"])["n"].sum().sort_values(ascending=False).head(15).items()}
del df

# ── LIF arithmetic (Shiu parameters) ─────────────────────────────────────
tm, ts, w, gap = 20.0, 5.0, 0.275, 7.0
tpk = np.log(tm / ts) * tm * ts / (tm - ts)
A = w / (1 - tm / ts)
psp = -A * (np.exp(-tpk / tm) - np.exp(-tpk / ts))
R["lif"] = dict(psp_peak_mV=float(psp), t_peak_ms=float(tpk), synapses_coincident_to_threshold=float(gap / psp),
                mean_depol_per_synHz_mV=float(ts * w / 1000.0),
                synHz_for_threshold=float(gap / (ts * w / 1000.0)), poisson_input_kick_mV=w * 250)

# ── helpers ───────────────────────────────────────────────────────────────
A_exc = sp.csr_matrix((np.where(sgn > 0, cnt, 0).astype(float), (post, pre)), shape=(N, N))   # row post, col pre
A_all = sp.csr_matrix((wsig.astype(float), (post, pre)), shape=(N, N))
A_any = sp.csr_matrix((np.ones_like(cnt, float), (pre, post)), shape=(N, N))               # row pre -> post
A_any.eliminate_zeros()
A_excfw = sp.csr_matrix((np.where(sgn > 0, 1.0, 0.0), (pre, post)), shape=(N, N))
A_excfw.eliminate_zeros()


def idx_of(roots):
    roots = pd.Series(roots).astype(np.int64)
    return np.sort(r2i.reindex(roots).dropna().to_numpy(np.int64))


def by_type(t):
    return np.flatnonzero(ct == t)


def bfs_dist(M, seeds):
    """hop distance from the seed set along M (row = source)."""
    d = np.full(N, -1, int)
    d[seeds] = 0
    frontier = np.asarray(seeds)
    k = 0
    while len(frontier):
        k += 1
        nb = np.unique(M[frontier].indices)
        nb = nb[d[nb] < 0]
        d[nb] = k
        frontier = nb
        if k > 12:
            break
    return d


def inputs_summary(tgt, top=12):
    m = np.isin(post, tgt)
    df = pd.DataFrame(dict(pre=pre[m], n=cnt[m], s=sgn[m]))
    df["sc"] = sc[df["pre"]]
    df["ct"] = ct[df["pre"]]
    tot = int(df["n"].sum())
    return dict(total_in_syn=tot, exc=int(df.loc[df.s > 0, "n"].sum()), inh=int(df.loc[df.s < 0, "n"].sum()),
                by_super_class={k: int(v) for k, v in df.groupby("sc")["n"].sum().sort_values(ascending=False).items()},
                top_types={k: int(v) for k, v in df.groupby("ct")["n"].sum().sort_values(ascending=False).head(top).items()})


def direct(src, tgt):
    m = np.isin(pre, src) & np.isin(post, tgt)
    return int(cnt[m].sum()), int(wsig[m].sum())


def propagate(seeds, steps=4, scale=None):
    """Linear signed influence: x_{k+1} = W x_k with W = signed synapse count normalised by each neuron's
    total input synapses (BANC-style influence, no nonlinearity). Returns list of vectors."""
    deg = np.asarray(np.abs(A_all).sum(1)).ravel()
    Dinv = sp.diags(1.0 / np.maximum(deg, 1))
    W = Dinv @ A_all
    x = np.zeros(N)
    x[seeds] = 1.0
    acc = np.zeros(N)
    out = []
    for _ in range(steps):
        x = W @ x
        acc += x
        out.append(acc.copy())
    return out


# ── 1. sugar GRN -> MN9 ───────────────────────────────────────────────────
mn9 = by_type("CB0701")
sugar = idx_of(pd.read_csv(ROOT / "data/sugar_grn_783.csv")["root_id"])
leg = pd.read_csv(ROOT / "data/leg_sugar_grn_783.csv")
leg_sel = idx_of(leg.loc[leg["selected"], "root_id"])
leg_all = idx_of(leg["root_id"])
res = {}
for name, src in (("labellar_sugar_36", sugar), ("leg_sugar_SA_VTV_2_12", leg_sel), ("leg_GRN_all_74", leg_all)):
    d_exc = bfs_dist(A_excfw, src)
    d_any = bfs_dist(A_any, src)
    inf = propagate(src, 4)
    rank = {k + 1: int((inf[k] > inf[k][mn9].mean()).sum()) for k in range(4)}
    res[name] = dict(n=int(len(src)), direct_syn_to_MN9=direct(src, mn9),
                     hops_exc_to_MN9=[int(x) for x in d_exc[mn9]], hops_any_to_MN9=[int(x) for x in d_any[mn9]],
                     out_syn_total=int(outsyn[src].sum()), out_partners=int(len(np.unique(post[np.isin(pre, src)]))),
                     influence_MN9_steps=[float(inf[k][mn9].mean()) for k in range(4)],
                     neurons_above_MN9_influence=rank)
R["sugar_to_MN9"] = res
R["MN9_inputs"] = inputs_summary(mn9)

# ── 2. DNg02, DNp15, DNa02 inputs ─────────────────────────────────────────
dng02 = np.flatnonzero(pd.Series(ct).str.match(r"^DNg02(_|$)").to_numpy())
R["DNg02"] = dict(n=int(len(dng02)), **inputs_summary(dng02))
for t in ("DNp15", "DNa02", "DNa01", "DNp01", "DNp07", "DNp10"):
    idx = by_type(t)
    R[t] = {s: dict(n=int((side[idx] == s).sum()), **inputs_summary(idx[side[idx] == s], top=8)) for s in ("left", "right")}

# hop distance from visual input proxies (T4/T5 columnar + all optic-lobe VPN boundary proxy) to the DNs
t45 = np.flatnonzero(pd.Series(ct).str.match(r"^T[45][abcd]$").to_numpy())
vpn = np.flatnonzero(sc == "visual_projection")
d_t45 = bfs_dist(A_excfw, t45)
d_vpn = bfs_dist(A_excfw, vpn)
dns = idx_of(pd.read_csv(ROOT / "brain_model/descending_neurons.csv")["root_id"])
R["visual_reach"] = dict(
    n_t45=int(len(t45)), n_vpn=int(len(vpn)), n_dn=int(len(dns)),
    dn_hops_from_T45_exc=pd.Series(d_t45[dns]).value_counts().sort_index().to_dict(),
    dn_hops_from_VPN_exc=pd.Series(d_vpn[dns]).value_counts().sort_index().to_dict(),
    DNg02_hops_from_T45=[int(x) for x in d_t45[dng02]], DNg02_hops_from_VPN=[int(x) for x in d_vpn[dng02]],
    DNp15_hops_from_T45=[int(x) for x in d_t45[by_type("DNp15")]],
)

# ── 3. Antennal lobe recurrent excitation ─────────────────────────────────
al = np.flatnonzero(np.isin(cc, ["ALLN", "ALPN"]) | (pd.Series(ct).str.startswith("ORN_").to_numpy()))
alln = np.flatnonzero(cc == "ALLN")
alpn = np.flatnonzero(cc == "ALPN")
orn = np.flatnonzero(pd.Series(ct).str.startswith("ORN_").to_numpy())
R["AL"] = dict(n_ALLN=int(len(alln)), n_ALPN=int(len(alpn)), n_ORN=int(len(orn)),
               ALLN_model_sign={"exc": int((pre_sign[alln] > 0).sum()), "inh": int((pre_sign[alln] < 0).sum()),
                                "no_output": int((outdeg[alln] == 0).sum())},
               ALLN_top_nt=pd.Series(top_nt[alln]).value_counts().to_dict(),
               ALPN_model_sign={"exc": int((pre_sign[alpn] > 0).sum()), "inh": int((pre_sign[alpn] < 0).sum())})
inner = np.concatenate([alln, alpn])
isin = np.zeros(N, bool)
isin[inner] = True
m = isin[pre] & isin[post]
e_syn, i_syn = cnt[m & (sgn > 0)].sum(), cnt[m & (sgn < 0)].sum()
R["AL"]["LN_PN_internal_syn"] = dict(exc=int(e_syn), inh=int(i_syn))
# excitatory recurrent drive available inside LN+PN at 100 Hz presynaptic rate
rec_exc = np.bincount(post[m & (sgn > 0)], weights=cnt[m & (sgn > 0)], minlength=N)[inner]
rec_inh = np.bincount(post[m & (sgn < 0)], weights=cnt[m & (sgn < 0)], minlength=N)[inner]
thr = R["lif"]["synHz_for_threshold"]
R["AL"]["recurrent"] = dict(
    neurons_with_exc_rec_syn_ge_thr_at_100Hz=int((rec_exc * 100 >= thr).sum()),
    neurons_with_net_rec_syn_ge_thr_at_100Hz=int(((rec_exc - rec_inh) * 100 >= thr).sum()),
    of=int(len(inner)), thr_synHz=thr)
# leading eigenvalue of the excitatory LN/PN subnetwork, linearised gain g = tau_s*w*r_slope/gap (unit: per synapse)
sub = A_exc[inner][:, inner].astype(float)
subs = sp.csr_matrix(A_all[inner][:, inner].astype(float))
try:
    from scipy.sparse.linalg import eigs
    ev_e = eigs(sub, k=1, which="LR", return_eigenvectors=False)
    ev_s = eigs(subs, k=1, which="LR", return_eigenvectors=False)
    R["AL"]["leading_eig_exc_syn"] = float(np.real(ev_e[0]))
    R["AL"]["leading_eig_signed_syn"] = float(np.real(ev_s[0]))
except Exception as ex:  # noqa: BLE001
    R["AL"]["eig_error"] = str(ex)

# ── 4. motor outputs present in the brain-only model ─────────────────────
R["motor_in_model"] = dict(n=int((sc == "motor").sum()),
                           cell_class=pd.Series(cc[sc == "motor"]).value_counts().to_dict())
R["ascending_in_model"] = int((sc == "ascending").sum())
R["sensory_ascending_in_model"] = int((sc == "sensory_ascending").sum())

# ── 5. left/right asymmetry ──────────────────────────────────────────────
lr = {}
for s in ("left", "right"):
    msk = side == s
    lr[s] = dict(neurons=int(msk.sum()), in_syn=int(insyn[msk].sum()), out_syn=int(outsyn[msk].sum()),
                 dn=int(np.isin(np.flatnonzero(msk), dns).sum()))
R["left_right"] = lr

OUT.write_text(json.dumps(R, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print(f"written {OUT}")
