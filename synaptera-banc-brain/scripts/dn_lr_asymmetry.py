"""Left/right input asymmetry of the descending neurons (FlyWire v783 as loaded by the Shiu et al. model; analysis only).

For every DN cell type with exactly one left and one right neuron: total input synapses per side and the ratio R/L,
the distribution of |log2(R/L)|, the rank of the readout types of flight/readouts.py, and the input-synapse ratio R/L of
whole super classes. Reading: synaptera-banc-brain/02_MODEL_FIZIK_TEST_ANALIZI.md section 1.4.

    env -u PYTHONPATH python synaptera-banc-brain/scripts/dn_lr_asymmetry.py [--root .] > synaptera-banc-brain/veri/dn_lr_asymmetry.txt
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

READOUT_TYPES = ("DNp15", "DNa02", "DNa01", "DNp10", "DNp07", "DNp01", "DNp02", "DNp04", "DNp11", "DNp06", "DNa03",
                 "DNb01", "DNb06", "DNp20")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    root = Path(ap.parse_args(argv).root)

    rid = pd.read_csv(root / "brain_model/Completeness_783.csv", index_col=0).index.to_numpy(np.int64)
    n = len(rid)
    con = pd.read_parquet(root / "brain_model/Connectivity_783.parquet",
                          columns=["Postsynaptic_Index", "Connectivity", "Excitatory"])
    post, cnt, sgn = (con[c].to_numpy() for c in ("Postsynaptic_Index", "Connectivity", "Excitatory"))
    insyn = np.bincount(post, weights=cnt, minlength=n)
    exc = np.bincount(post, weights=np.where(sgn > 0, cnt, 0), minlength=n)
    del con

    r2i = pd.Series(np.arange(n), index=rid)
    dn = pd.read_csv(root / "brain_model/descending_neurons.csv")
    dn["i"] = r2i.reindex(dn["root_id"]).to_numpy()
    dn = dn.dropna(subset=["i"]).astype({"i": int})
    dn = dn[dn["side"].isin(["left", "right"])]
    dn["insyn"], dn["exc"] = insyn[dn["i"]], exc[dn["i"]]
    g = dn.groupby(["cell_type", "side"]).agg(n=("i", "size"), insyn=("insyn", "sum"), exc=("exc", "sum")).unstack("side")
    g = g.dropna()
    g = g[(g[("n", "left")] == 1) & (g[("n", "right")] == 1)]
    ratio = g[("insyn", "right")] / g[("insyn", "left")]
    lg = np.log2(ratio)

    print(f"paired single-neuron DN types: {len(g)}")
    print(f"median |log2 R/L|: {lg.abs().median():.3f}; fraction |log2| > 0.5 (1.41x): {(lg.abs() > 0.5).mean():.3f}; "
          f"> 1 (2x): {(lg.abs() > 1).mean():.3f}; median signed log2 R/L: {lg.median():.3f}")
    print("type  in_syn_L  in_syn_R  exc_L  exc_R  R/L  rank_of_|log2|")
    for t in READOUT_TYPES:
        if t in g.index:
            rank = int((lg.abs() >= abs(lg[t])).sum())
            print(f"{t}  {int(g.loc[t, ('insyn', 'left')])}  {int(g.loc[t, ('insyn', 'right')])}  "
                  f"{int(g.loc[t, ('exc', 'left')])}  {int(g.loc[t, ('exc', 'right')])}  {ratio[t]:.2f}  {rank}/{len(g)}")
    s = ratio.sort_values()
    print("most left-heavy:", ", ".join(f"{t} {v:.2f}" for t, v in s.head(8).items()))
    print("most right-heavy:", ", ".join(f"{t} {v:.2f}" for t, v in s.tail(8).items()))

    ann = pd.read_csv(root / "brain_model/flywire_annotations.tsv", sep="\t", low_memory=False,
                      usecols=["root_id", "side", "super_class"]).drop_duplicates("root_id").set_index("root_id").reindex(rid)
    side, sc = ann["side"].to_numpy(), ann["super_class"].to_numpy()
    for c in ("optic", "central", "visual_projection", "descending"):
        left, right = insyn[(sc == c) & (side == "left")].sum(), insyn[(sc == c) & (side == "right")].sum()
        print(f"{c}: input synapses R/L {right / left:.3f}")
    print(f"all: neurons L/R {(side == 'left').sum()}/{(side == 'right').sum()}, input synapses R/L "
          f"{insyn[side == 'right'].sum() / insyn[side == 'left'].sum():.3f}")


if __name__ == "__main__":
    main()
