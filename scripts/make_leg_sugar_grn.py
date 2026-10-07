"""Write data/leg_sugar_grn_783.csv: all 74 leg GRNs (sensory_ascending / gustatory) with their kNN
sugar fraction and the selection (flight.groups.select_leg_sugar_grns; SPEC_SENSORY_INPUTS §2.4, §3.2b).
Fixed from connectivity only, before any behaviour. Run once; a test checks it is reproducible.

    env -u PYTHONPATH python scripts/make_leg_sugar_grn.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from flight import groups as G  # noqa: E402

df, loo = G.select_leg_sugar_grns()
df.to_csv(G.PATH_LEG_SUGAR, index=False, float_format="%.2f")
print(df.groupby(["cell_type", "side"])["selected"].agg(["sum", "count"]).to_string())
print(f"selected {int(df['selected'].sum())}/{len(df)}; pool LOO:", json.dumps(loo))
