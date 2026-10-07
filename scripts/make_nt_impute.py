"""Write data/nt_impute_783.csv for --nt-impute (MODEL VARIANT N1, SPEC_SENSORY_INPUTS §3.4b).

MODEL VARIANT, not the published model. Rule (fixed before any run, whole brain, no region-specific setting):
  * "empty" neuron = no Codex v783 nt_type prediction (neurons.csv nt_type NaN, score 0); 19,042 neurons. The set is checked against
    data/nt_modulatory_silent_783.csv (rows nt_type == "none").
  * Only empty neurons can change. A predicted cell votes with the sign of its PREDICTED transmitter under the model's own NT -> sign
    mapping (ACh, DA, 5-HT, OA -> +1; GABA, Glu -> -1; the published model treats every transmitter other than GABA/Glu as excitatory),
    weighted by its number of output synapses (sum of Connectivity over its output edges). It does NOT vote with the sign the published
    model happens to give it (473 of the 119,597 predicted cells with outputs have a model sign that differs from their prediction).
  * An empty neuron takes the sign of the weighted majority of the non-empty cells of the SAME annotation cell_type: sum > 0 -> +1,
    sum < 0 -> -1.
  * No cell_type (NaN), no non-empty peer with output synapses, a zero sum, or no output synapses of the neuron itself ->
    imputed_sign = 0: the neuron keeps its published sign.
Columns: root_id, cell_type, published_sign (+1/-1, 0 = no output synapses), imputed_sign (+1/-1/0), n_peers (non-empty
peers with outputs), peer_syn_pos, peer_syn_neg (peer output synapse counts by predicted sign).

    env -u PYTHONPATH $HOME/miniforge3/envs/neurofly/bin/python scripts/make_nt_impute.py [--codex-dir ~/Downloads]
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from flight import groups as G  # noqa: E402


PRED_SIGN = {"ACH": 1, "DA": 1, "SER": 1, "OCT": 1, "GABA": -1, "GLUT": -1}


def compute(codex_dir="~/Downloads"):
    """DataFrame of the empty neurons (one row each) with the published and the imputed sign."""
    rid = G.load_root_ids()
    n = len(rid)
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_Index", "Connectivity", "Excitatory"])
    pre = con["Presynaptic_Index"].to_numpy(np.int64)
    sgn_e = con["Excitatory"].to_numpy(np.int64)
    w = con["Connectivity"].to_numpy(np.int64)
    out_syn = np.bincount(pre, weights=w, minlength=n)
    lo = np.full(n, 2, np.int64)
    hi = np.full(n, -2, np.int64)
    np.minimum.at(lo, pre, sgn_e)
    np.maximum.at(hi, pre, sgn_e)
    has = out_syn > 0
    assert (lo[has] == hi[has]).all(), "the sign of a presynaptic neuron is not unique"
    published = np.where(has, lo, 0)
    r2i = G.root_to_index(rid)
    codex = pd.read_csv(os.path.join(os.path.expanduser(codex_dir), "neurons.csv.gz"),
                        usecols=["root_id", "nt_type", "nt_type_score"]).set_index("root_id").reindex(rid)
    assert (codex.loc[codex["nt_type"].isna(), "nt_type_score"] == 0).all()
    empty = codex["nt_type"].isna().to_numpy()
    sil = pd.read_csv(G.PATH_NT_SILENT)
    chk = np.zeros(n, bool)
    chk[sil.loc[sil["nt_type"] == "none", "root_id"].map(r2i).to_numpy(np.int64)] = True
    assert (chk == empty).all(), "empty set differs from data/nt_modulatory_silent_783.csv"
    pred = codex["nt_type"].map(PRED_SIGN).fillna(0).to_numpy(np.int64)
    assert set(codex["nt_type"].dropna().unique()) <= set(PRED_SIGN), "unexpected nt_type value"
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type"])
    ann = ann.drop_duplicates("root_id").set_index("root_id").reindex(rid)
    ct = ann["cell_type"].to_numpy(object)
    df = pd.DataFrame({"idx": np.arange(n), "cell_type": ct, "empty": empty, "published": published,
                       "pos": out_syn * (pred > 0), "neg": out_syn * (pred < 0)})
    peers = df[(~df["empty"]) & df["cell_type"].notna() & has]
    agg = peers.groupby("cell_type").agg(n_peers=("idx", "size"), peer_syn_pos=("pos", "sum"), peer_syn_neg=("neg", "sum"))
    out = df[df["empty"]].join(agg, on="cell_type")
    for c in ("n_peers", "peer_syn_pos", "peer_syn_neg"):
        out[c] = out[c].fillna(0).astype(np.int64)
    imp = np.sign((out["peer_syn_pos"] - out["peer_syn_neg"]).to_numpy()).astype(np.int64)
    imp[out["published"].to_numpy() == 0] = 0  # no output synapses of its own: nothing to change
    res = pd.DataFrame({"root_id": rid[out["idx"].to_numpy()], "cell_type": out["cell_type"].fillna("").to_numpy(),
                        "published_sign": out["published"].to_numpy(), "imputed_sign": imp,
                        "n_peers": out["n_peers"].to_numpy(), "peer_syn_pos": out["peer_syn_pos"].to_numpy(),
                        "peer_syn_neg": out["peer_syn_neg"].to_numpy()})
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--codex-dir", default="~/Downloads")
    res = compute(ap.parse_args().codex_dir)
    res.to_csv(G.PATH_NT_IMPUTE, index=False)
    ch = (res["imputed_sign"] != 0) & (res["imputed_sign"] != res["published_sign"])
    print(f"{len(res)} empty neurons; imputable {int((res['imputed_sign'] != 0).sum())}; sign changes {int(ch.sum())} "
          f"(+->- {int(((res['published_sign'] == 1) & (res['imputed_sign'] == -1)).sum())}, "
          f"-->+ {int(((res['published_sign'] == -1) & (res['imputed_sign'] == 1)).sum())}); wrote {G.PATH_NT_IMPUTE}")
