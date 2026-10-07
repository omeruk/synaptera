"""Write data/sugar_grn_783.csv: Shiu sugar GRNs (left) + right homologs by connectivity
profile (flight.groups.select_sugar_homologs). Run once; the slow test checks it is reproducible.

    env -u PYTHONPATH python scripts/make_sugar_grn.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from flight import groups as G  # noqa: E402

df, loo = G.select_sugar_homologs()
df.to_csv(G.PATH_SUGAR, index=False, float_format="%.2f")
print(df["source"].value_counts().to_dict(), "left LOO:", loo)
