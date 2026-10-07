"""Write brain_model/descending_neurons.csv (root_id, cell_type, top_nt, side): the descending neurons of
flywire_annotations.tsv (super_class == "descending") that are in Completeness_783.csv, in annotation order.

The flight code reads this file for the DN readouts. The copy in the development repository came from the
NeuroFly upstream repository; this script rebuilds it from the two files fetched by scripts/fetch_data.py
(Shiu et al. Completeness_783.csv, flyconnectome/flywire_annotations Supplemental_file1). Columns and
row order are those of the upstream file.

    env -u PYTHONPATH python scripts/make_descending_neurons.py [--out brain_model/descending_neurons.csv]
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = ROOT / "brain_model"


def build(path_ann=BRAIN_DIR / "flywire_annotations.tsv", path_comp=BRAIN_DIR / "Completeness_783.csv"):
    ann = pd.read_csv(path_ann, sep="\t", low_memory=False,
                      usecols=["root_id", "super_class", "cell_type", "top_nt", "side"])
    comp = pd.read_csv(path_comp, index_col=0)
    dn = ann[(ann["super_class"] == "descending") & ann["root_id"].isin(comp.index)]
    return dn[["root_id", "cell_type", "top_nt", "side"]]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(BRAIN_DIR / "descending_neurons.csv"))
    a = ap.parse_args(argv)
    df = build()
    df.to_csv(a.out, index=False)
    print(f"{a.out}: {len(df)} descending neurons "
          f"({(df['side'] == 'left').sum()} L, {(df['side'] == 'right').sum()} R)")


if __name__ == "__main__":
    main()
