"""Write data/nt_modulatory_silent_783.csv for --nt-modulatory-silent (SPEC_BRAIN_CONTROL,
Step 0 decisions II, decision 1): simulated neurons whose FlyWire Codex v783 neurons.csv
nt_type is DA, SER or OCT, or has no prediction (nt_type NaN, nt_type_score 0).
Columns: root_id, nt_type (DA/SER/OCT/none), nt_type_score. Run once. The variant
(broad: all rows; narrow: DA/SER/OCT only) and the input-neuron exception are applied
in flight/brain.py.

    env -u PYTHONPATH python scripts/make_nt_silent.py [--codex-dir ~/Downloads]
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd  # noqa: E402

from flight import groups as G  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--codex-dir", default="~/Downloads")
a = ap.parse_args()
nt = pd.read_csv(os.path.join(os.path.expanduser(a.codex_dir), "neurons.csv.gz"),
                 usecols=["root_id", "nt_type", "nt_type_score"]).set_index("root_id")
rid = G.load_root_ids()
missing = set(rid.tolist()) - set(nt.index)
if missing:
    raise SystemExit(f"{len(missing)} simulated neurons not in neurons.csv")
nt = nt.reindex(rid)
none = nt["nt_type"].isna()
if not (nt.loc[none, "nt_type_score"] == 0).all():
    raise SystemExit("nt_type NaN with a non-zero score")
sel = nt["nt_type"].isin(G.NT_MODULATORY) | none
out = nt[sel].reset_index().rename(columns={"index": "root_id"})
out["nt_type"] = out["nt_type"].fillna("none")
out.to_csv(G.PATH_NT_SILENT, index=False, float_format="%.2f")
print(f"{len(out):,} of {len(rid):,} neurons:", out["nt_type"].value_counts().to_dict())
