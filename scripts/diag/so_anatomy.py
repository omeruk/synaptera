"""Smell circuit part 1/4, step 0: anatomy only (no simulation). Results feed the O1/O2 pre-registration.

(a) food-glomerulus ORN counts (L/R/na) and ORN->PN synapse split ipsi/contra (PN side = annotation `side`
    of the postsynaptic ALPN cell; counts are Connectivity_783 `Connectivity`, already thresholded by the
    model files);
(b) presence / count / side of the requested descending-neuron types, in the model DN list and in all annotations;
(c) shortest paths ORN(food) -> DNa02 over edges with synapse count >= 5 (BFS layers, types on shortest paths).

    env -u PYTHONPATH python scripts/diag/so_anatomy.py [--out so_anatomy.json]
"""
import argparse
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import scipy.sparse as sp  # noqa: E402

from flight import groups as G  # noqa: E402

FOOD = G.FOOD_GLOMERULI
DN_QUERY = ["DNa02", "DNa01", "DNae001", "DNae014", "DNa15", "DNb01", "DNg02", "DNp03", "DNa04", "DNae002", "DNa05", "DNae004"]
SYN_MIN = 5
MAX_HOPS = 8


def compute():
    """All step-0 numbers as a dict (no simulation; ~3 s)."""
    root_ids = G.load_root_ids()
    r2i = G.root_to_index(root_ids)
    n = len(root_ids)
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False)
    ann = ann[ann["root_id"].isin(r2i)].copy()
    ann["idx"] = ann["root_id"].map(r2i).astype(np.int64)
    ann["sd"] = G._side(ann["side"]).map({"left": "L", "right": "R"}).fillna("na")
    ann = ann.set_index("idx").sort_index()
    ctype = ann["cell_type"].astype(str)
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_Index", "Postsynaptic_Index", "Connectivity"])
    pre = con["Presynaptic_Index"].to_numpy(np.int64)
    post = con["Postsynaptic_Index"].to_numpy(np.int64)
    w = con["Connectivity"].to_numpy(np.int64)
    out = {"n_neurons": int(n), "syn_min_graph": SYN_MIN}

    # ---- (a)
    orn = ann[ctype.str.startswith("ORN_")]
    gl = orn["cell_type"].str[4:]
    food_orn = orn[gl.isin(FOOD)]
    fg = food_orn["cell_type"].str[4:]
    a = {"glomeruli": list(FOOD), "per_glomerulus": {}}
    for g in FOOD:
        s = food_orn[fg == g]["sd"].value_counts()
        a["per_glomerulus"][g] = {k: int(s.get(k, 0)) for k in ("L", "R", "na")}
    s = food_orn["sd"].value_counts()
    a["total"] = {k: int(s.get(k, 0)) for k in ("L", "R", "na")}
    is_pn = (ann["cell_class"].astype(str) == "ALPN").to_numpy()
    side_arr = np.full(n, "na", dtype=object)
    side_arr[ann.index.to_numpy()] = ann["sd"].to_numpy()
    pn_mask = np.zeros(n, bool)
    pn_mask[ann.index.to_numpy()] = is_pn
    uni = np.zeros(n, bool)
    uni[ann.index.to_numpy()] = (ann["cell_sub_class"].astype(str) == "uniglomerular").to_numpy()

    def split(src_idx, label, pn_sel):
        src = np.zeros(n, bool)
        src[src_idx] = True
        m = src[pre] & pn_sel[post]
        ss, ps, ww = side_arr[pre[m]], side_arr[post[m]], w[m]
        d = {}
        for tag, sel in (("ipsi", (ss == ps) & (ss != "na")), ("contra", (ss != ps) & (ss != "na") & (ps != "na"))):
            d[tag] = int(ww[sel].sum())
        d["unassigned_side"] = int(ww.sum() - d["ipsi"] - d["contra"])
        d["ipsi_over_contra"] = d["ipsi"] / d["contra"] if d["contra"] else None
        d["ipsi_excess_pct"] = 100 * (d["ipsi"] / d["contra"] - 1) if d["contra"] else None
        d["n_pn_targets"] = int(np.unique(post[m]).size)
        return {label: d}

    a["orn_to_pn_synapses"] = {}
    a["orn_to_pn_synapses"].update(split(food_orn.index.to_numpy(), "food_ORN->all_ALPN", pn_mask))
    a["orn_to_pn_synapses"].update(split(food_orn.index.to_numpy(), "food_ORN->uniglomerular_ALPN", pn_mask & uni))
    a["orn_to_pn_synapses"].update(split(orn.index.to_numpy(), "all_53_glomeruli_ORN->all_ALPN", pn_mask))
    a["per_glomerulus_ipsi_over_contra"] = {}
    for g in FOOD:
        d = split(food_orn[fg == g].index.to_numpy(), g, pn_mask)[g]
        a["per_glomerulus_ipsi_over_contra"][g] = {k: d[k] for k in ("ipsi", "contra", "ipsi_over_contra")}
    # same-glomerulus PNs only (food glomerulus ORN -> PN named <g>_*)
    same = {}
    pn_type = ctype.reindex(range(n)).fillna("").to_numpy()
    for g in FOOD:
        sel = np.array([t.startswith(g + "_") or t.startswith(g + "+") for t in pn_type]) & pn_mask
        d = split(food_orn[fg == g].index.to_numpy(), g, sel)[g]
        same[g] = {k: d[k] for k in ("ipsi", "contra", "ipsi_over_contra", "n_pn_targets")}
    a["per_glomerulus_to_own_glomerulus_PN_by_name"] = same
    out["a_orn"] = a

    # ---- (b)
    dn = pd.read_csv(G.PATH_DN)
    dn = dn[dn["root_id"].isin(r2i)]
    b = {}
    for q in DN_QUERY:
        rec = {}
        mdn = dn[dn["cell_type"].astype(str) == q]
        rec["model_DN_list_exact"] = {k: int(v) for k, v in mdn["side"].value_counts().items()}
        mdn_p = dn[dn["cell_type"].astype(str).str.startswith(q)]
        rec["model_DN_list_prefix_types"] = {t: {k: int(v) for k, v in g["side"].value_counts().items()}
                                             for t, g in mdn_p.groupby("cell_type")}
        hit = ann[(ctype == q) | (ann["hemibrain_type"].astype(str) == q)]
        rec["annotations_cell_type_or_hemibrain_type"] = {
            "n": int(len(hit)), "cell_types": hit["cell_type"].astype(str).value_counts().to_dict(),
            "hemibrain_types": hit["hemibrain_type"].astype(str).value_counts().to_dict(),
            "super_class": hit["super_class"].astype(str).value_counts().to_dict()}
        syn = ann[ann["synonyms"].astype(str).str.contains(q, regex=False)]
        rec["annotations_in_synonyms"] = {"n": int(len(syn)), "cell_types": syn["cell_type"].astype(str).value_counts().to_dict()}
        b[q] = rec
    out["b_dn"] = b

    # ---- (c)
    ok = w >= SYN_MIN
    A = sp.csr_matrix((np.ones(ok.sum(), np.int8), (pre[ok], post[ok])), shape=(n, n))
    src = np.zeros(n, bool)
    src[food_orn.index.to_numpy()] = True
    tgt_idx = ann[ctype == "DNa02"].index.to_numpy()
    c = {"targets": {int(i): ann.loc[i, "sd"] for i in tgt_idx}, "n_source_orn": int(src.sum())}
    layers = [src.copy()]
    seen = src.copy()
    front = src.copy()
    for h in range(1, MAX_HOPS + 1):
        nxt = (A.T @ front.astype(np.int32)) > 0
        nxt &= ~seen
        layers.append(nxt)
        seen |= nxt
        front = nxt
        if nxt[tgt_idx].any():
            break
    hop = len(layers) - 1
    c["reached"] = bool(layers[-1][tgt_idx].any())
    c["min_hops"] = hop if c["reached"] else None
    c["per_target_hop"] = {int(i): next((k for k, L in enumerate(layers) if L[i]), None) for i in tgt_idx}
    if c["reached"]:
        # backward pruning: nodes on some shortest path source -> target
        on = [None] * (hop + 1)
        on[hop] = np.zeros(n, bool)
        on[hop][tgt_idx] = layers[hop][tgt_idx]
        for k in range(hop - 1, -1, -1):
            pred = (A @ on[k + 1].astype(np.int32)) > 0
            on[k] = pred & layers[k]
        c["layers_on_shortest_paths"] = []
        for k in range(hop + 1):
            ids = np.flatnonzero(on[k])
            vc = ctype.reindex(ids).fillna("?").value_counts()
            c["layers_on_shortest_paths"].append({"hop": k, "n_neurons": int(ids.size),
                                                  "top_types": {t: int(v) for t, v in vc.head(25).items()}})
        # share of shortest-path routes (edge-count weighted by path multiplicity) through KC / MBON32 / other types
        cnt = [None] * (hop + 1)
        cnt[0] = src.astype(np.float64)
        for k in range(1, hop + 1):
            cnt[k] = (A.T @ cnt[k - 1]) * layers[k]
        back = [None] * (hop + 1)
        back[hop] = on[hop].astype(np.float64)
        for k in range(hop - 1, -1, -1):
            back[k] = (A @ back[k + 1]) * on[k]
        tot = float((cnt[hop] * on[hop]).sum())
        c["n_shortest_paths_total"] = tot
        share = {}
        for k in range(1, hop):
            paths_through = cnt[k] * back[k]
            for t in np.unique(pn_type[on[k]]):
                sel = on[k] & (pn_type == t)
                share.setdefault(t, 0.0)
                share[t] = max(share[t], float(paths_through[sel].sum()) / tot)
        c["fraction_of_shortest_paths_through_type_at_any_intermediate_hop"] = {
            t: round(v, 4) for t, v in sorted(share.items(), key=lambda kv: -kv[1])[:30]}
        kc = np.zeros(n, bool)
        kc[ann[ann["cell_class"].astype(str) == "Kenyon_Cell"].index.to_numpy()] = True
        c["fraction_through_KC"] = float(sum((cnt[k] * back[k])[kc].sum() for k in range(1, hop)) / tot)
        mb = np.array([t.startswith("MBON32") for t in pn_type])
        c["fraction_through_MBON32"] = float(sum((cnt[k] * back[k])[mb].sum() for k in range(1, hop)) / tot)
        c["MBON32_cells"] = {int(i): str(ann.loc[i, "sd"]) for i in np.flatnonzero(mb)}
    out["c_paths"] = c
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="so_anatomy.json")
    args = ap.parse_args()
    out = compute()
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
