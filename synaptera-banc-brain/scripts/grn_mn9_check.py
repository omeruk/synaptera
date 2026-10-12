"""Independent open-loop check with the unmodified Shiu et al. model (brain_model/model.py, Shiu PoissonInput protocol):
MN9 (CB0701) rate when the labellar sugar GRNs (data/sugar_grn_783.csv) or the connectivity-selected leg GRNs
(data/leg_sugar_grn_783.csv) are driven. Full brain, Brian2 (cython), one fresh network per condition and seed; ~1-3 min
per 1 s condition on one CPU core. Reading: synaptera-banc-brain/02_CONNECTOME_MODEL_PHYSICS_TESTS.md section 5.3.

    env -u PYTHONPATH python synaptera-banc-brain/scripts/grn_mn9_check.py <repo root> synaptera-banc-brain/results/grn_mn9.json [t_run_s] [seeds ...]
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
T_RUN = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
SEEDS = [int(s) for s in sys.argv[4:]] or [0, 1]
sys.path.insert(0, str(ROOT / "brain_model"))
from brian2 import Hz, Network, PoissonInput, ms, prefs, second  # noqa: E402
from brian2 import seed as bseed  # noqa: E402
from model import create_model, default_params  # noqa: E402

prefs.codegen.target = "cython"
comp = pd.read_csv(ROOT / "brain_model/Completeness_783.csv", index_col=0)
r2i = pd.Series(np.arange(len(comp)), index=comp.index)
ann = pd.read_csv(ROOT / "brain_model/flywire_annotations.tsv", sep="\t", low_memory=False,
                  usecols=["root_id", "cell_type", "side"]).drop_duplicates("root_id")
mn9 = r2i.reindex(ann.loc[ann.cell_type == "CB0701", "root_id"]).dropna().astype(int).to_numpy()
sugar = r2i.reindex(pd.read_csv(ROOT / "data/sugar_grn_783.csv").root_id).dropna().astype(int).to_numpy()
shiu = r2i.reindex(pd.read_csv(ROOT / "data/sugar_grn_783.csv").query("source == 'shiu2023'").root_id).dropna().astype(int).to_numpy()
leg = pd.read_csv(ROOT / "data/leg_sugar_grn_783.csv")
leg_sel = r2i.reindex(leg.loc[leg.selected, "root_id"]).dropna().astype(int).to_numpy()
leg_all = r2i.reindex(leg.root_id).dropna().astype(int).to_numpy()
conds = [("shiu_left_20@100Hz", shiu, 100), ("labellar_36@100Hz", sugar, 100), ("leg_SA_VTV_2_12@100Hz", leg_sel, 100),
         ("leg_SA_VTV_2_12@200Hz", leg_sel, 200), ("leg_all_74@100Hz", leg_all, 100), ("none", np.array([], int), 0)]
params = dict(default_params)
res = []
for seed in SEEDS:
    for name, idx, rate in conds:
        t0 = time.time()
        bseed(seed)
        neu, syn, mon = create_model(str(ROOT / "brain_model/Completeness_783.csv"),
                                     str(ROOT / "brain_model/Connectivity_783.parquet"), params)
        pois = []
        for i in idx:
            pois.append(PoissonInput(target=neu[int(i)], target_var="v", N=1, rate=rate * Hz,
                                     weight=params["w_syn"] * params["f_poi"]))
            neu[int(i)].rfc = 0 * ms
        net = Network(neu, syn, mon, *pois)
        net.run(T_RUN * second)
        sp_i = np.asarray(mon.i[:])
        cnt = np.bincount(sp_i, minlength=len(comp))
        r = dict(seed=seed, cond=name, n_driven=int(len(idx)), rate_in=rate,
                 mn9_hz=[float(c / T_RUN) for c in cnt[mn9]], driven_mean_hz=float(cnt[idx].mean() / T_RUN) if len(idx) else 0.0,
                 n_active=int((cnt > 0).sum()), total_spikes=int(cnt.sum()), wall_s=round(time.time() - t0, 1))
        print(json.dumps(r), flush=True)
        res.append(r)
        del net, neu, syn, mon, pois
OUT.write_text(json.dumps(res, indent=1))
