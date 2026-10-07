"""Write data/vision_boundary_783.csv + data/vision_boundary_types.json (--vision-boundary, Stage B).

Boundary rule, column assignment and its validation: flight/vision_boundary.py. Run once; the
selection is fixed before any behaviour.

    env -u PYTHONPATH python scripts/make_vision_boundary.py [--codex-dir ~/Downloads] [--out-dir data]

--out-dir writes the two files elsewhere (e.g. to compare them with the tracked ones without
overwriting them).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from flight import groups as G  # noqa: E402
from flight import vision_boundary as VB  # noqa: E402
from flight import visual_input as V  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--codex-dir", default=str(VB.PATH_CODEX_TYPES.parent),
                help="directory with the Codex download consolidated_cell_types.csv.gz")
ap.add_argument("--out-dir", default=str(VB.PATH_TABLE.parent))
a = ap.parse_args()
out_dir = Path(a.out_dir).expanduser()
out_dir.mkdir(parents=True, exist_ok=True)
path_table, path_types = out_dir / VB.PATH_TABLE.name, out_dir / VB.PATH_TYPES.name

rid = G.load_root_ids()
ct = VB.load_codex_types(rid, Path(a.codex_dir).expanduser() / VB.PATH_CODEX_TYPES.name)
net = V.load_flyvis_net()
import numpy as np  # noqa: E402

fv_types = list(dict.fromkeys(np.array(net.connectome.nodes.type[:]).astype(str)))
res, missing = VB.boundary_fractions(ct, fv_types)
print(res.to_string())
driven = res[res["driven"]]
print(f"driven: {len(driven)} FlyWire types, {int(driven['n'].sum())} neurons; FlyVis types not in v783: {missing}")
tab, val = VB.build_table(rid, ct, dict(zip(driven.index, driven["flyvis_type"])))
tab.to_csv(path_table, index=False)
info = dict(rule=f"driven if share of outgoing synapses (parquet Connectivity) to non-FlyVis-matched neurons "
                 f">= {VB.BOUNDARY_FRAC}", cell_types="Codex v783 consolidated_cell_types primary_type",
            flyvis_model=V.FLYVIS_MODEL, flyvis_types_not_in_v783=missing,
            types={t: dict(flyvis_type=r["flyvis_type"], n=int(r["n"]), syn_out=float(r["syn_out"]),
                           frac_out_nonflyvis=float(r["frac_out_nonflyvis"]), driven=bool(r["driven"]))
                   for t, r in res.iterrows()},
            n_driven_types=len(driven), n_driven_neurons=len(tab),
            n_column_assignment=int((tab["col_source"] == "column_assignment").sum()),
            n_centroid=int((tab["col_source"] != "column_assignment").sum()),  # all non-columnar (partner_mean + centroid); name kept from the tracked file
            centroid_sources=tab["col_source"].value_counts().to_dict(),
            column_rule="column_assignment; else partner_mean; else centroid", centroid_reference=VB.CENTROID_REF, surface_degree=VB.SURFACE_DEG,
            centroid_validation=val)
with open(path_types, "w") as f:
    json.dump(info, f, indent=1)
print(f"{path_table}: {len(tab)} neurons ({info['n_column_assignment']} columnar, {info['n_centroid']} inferred: "
      f"{info['centroid_sources']})")
for rule in ("partner_mean", "centroid"):
    v = val[rule]
    print(f"{rule} rule on {val['n']} columnar neurons (own column hidden): exact {v['exact']:.3f}, "
          f"<=1 {v['le1']:.3f}, <=2 {v['le2']:.3f}, median {v['median']}")
    print({k: round(x, 3) for k, x in v["per_type_le1"].items()})
print(val["surfaces"])
