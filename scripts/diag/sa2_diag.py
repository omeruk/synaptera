"""Stage A2 step 1 (read only): neuron types that take part in the persistent olfactory state, and their NT sources.

Source runs: the Stage A smoke runs (v17 spiking, v18 graded APL; --olfaction-full, seed 3,
--persist-steps 40). Cut-off window = the last 20 of the input cut-off steps (500–1000 ms after
the cut, all Poisson inputs 0). Every neuron that fires in this window "takes part" in the persistent loop.

Per type (flywire_annotations.tsv cell_type; else cell_class/super_class):
  n, n active in the cut-off window, mean Hz, share of cut-off spikes (%), in-loop output share:
  sum_{post active} |w| * r_pre / total (|w| = synapse count), sign in the model (parquet
  Excitatory), Codex v783 nt_type (including NaN) + score, annotations top_nt/top_nt_conf,
  known_nt + known_nt_source (compilation of Schlegel et al. 2024).
Only classes whose dominant neuropil is AL, LH, MB_* or whose type is known to be AL/LH/MB are listed.

    env -u PYTHONPATH .../envs/neurofly/bin/python scripts/diag/sa2_diag.py [--codex-dir ~/Downloads]
      -> sa2_diag_types.csv (current directory) + table on stdout
"""
import argparse
import os
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from flight import groups as G  # noqa: E402

RUNS = {"spiking": "flight_v17_hybrid_sA_sB_ablDN-DNp15_smoke_sA_data.h5",
        "graded": "flight_v18_hybrid_sA_sB_ablDN-DNp15_aplG_smoke_sA_data.h5"}
LOOP_NP = ("AL", "LH", "MB_CA", "MB_ML", "MB_PED", "MB_VL")
DT = 0.025


def cut_counts(path, n):
    with h5py.File(path) as f:
        st, ni, cn = f["spikes/step_idx"][:], f["spikes/neuron_idx"][:], f["spikes/count"][:]
        ps = int(f["meta"].attrs["persist_steps"])
    w0, w1 = -ps + ps // 2, 0                          # last half of the cut (500–1000 ms for 40 steps)
    m = (st >= w0) & (st < w1)
    nsteps = w1 - w0
    return np.bincount(ni[m], weights=cn[m], minlength=n) / (nsteps * DT), nsteps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codex-dir", default="~/Downloads")
    ap.add_argument("--sim-dir", default=str(ROOT / "simulations"))
    a = ap.parse_args()
    rid = G.load_root_ids()
    n = len(rid)
    ann = pd.read_csv(G.BRAIN_DIR / "flywire_annotations.tsv", sep="\t", low_memory=False,
                      usecols=["root_id", "super_class", "cell_class", "cell_type", "hemibrain_type", "top_nt",
                               "top_nt_conf", "known_nt", "known_nt_source"]).drop_duplicates("root_id")
    ann = ann.set_index("root_id").reindex(rid)
    cdx = pd.read_csv(os.path.join(os.path.expanduser(a.codex_dir), "neurons.csv.gz"),
                      usecols=["root_id", "nt_type", "nt_type_score"]).set_index("root_id").reindex(rid)
    npz = np.load(ROOT / "data/neuron_neuropil.npz")
    dom = npz["neuropils"][npz["dominant"]]
    dom[npz["dominant"] < 0] = "(none)"
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_Index", "Postsynaptic_Index", "Connectivity",
                                               "Excitatory"])
    pre, post = con["Presynaptic_Index"].to_numpy(), con["Postsynaptic_Index"].to_numpy()
    cnt, exc = con["Connectivity"].to_numpy().astype(float), con["Excitatory"].to_numpy()
    del con
    sign = np.zeros(n, int)
    sign[pre] = exc
    out_syn = np.bincount(pre, weights=cnt, minlength=n)

    ctype = ann["cell_type"].fillna(ann["hemibrain_type"]).fillna(
        "[" + ann["cell_class"].fillna(ann["super_class"]).fillna("?") + "]").to_numpy()
    df = pd.DataFrame(dict(root_id=rid, type=ctype, super_class=ann["super_class"].to_numpy(),
                           cell_class=ann["cell_class"].to_numpy(), dom=dom, sign=sign, out_syn=out_syn,
                           codex_nt=cdx["nt_type"].fillna("NaN").to_numpy(),
                           codex_score=cdx["nt_type_score"].to_numpy(),
                           top_nt=ann["top_nt"].to_numpy(), top_nt_conf=ann["top_nt_conf"].to_numpy(),
                           known_nt=ann["known_nt"].to_numpy(), known_src=ann["known_nt_source"].to_numpy()))
    for var, fn in RUNS.items():
        r, nsteps = cut_counts(Path(a.sim_dir) / fn, n)
        act = r > 0
        drive = np.bincount(pre[act[post]], weights=(cnt * r[pre])[act[post]], minlength=n)
        df[f"hz_{var}"], df[f"drive_{var}"] = r, drive
        print(f"{var}: cut-off {nsteps} steps, active {act.sum():,}, network mean {r.mean():.3f} Hz")
    is_orn = df["cell_class"].eq("olfactory").to_numpy() & df["super_class"].eq("sensory").to_numpy()
    df["is_orn"] = is_orn
    df.to_parquet("sa2_diag_neurons.parquet")

    loop = df[df["dom"].isin(LOOP_NP) & ~df["is_orn"]]
    tot = {v: (df[f"hz_{v}"].sum(), df[f"drive_{v}"].sum()) for v in RUNS}

    def agg(g):
        o = dict(n=len(g), dom=g["dom"].mode().iat[0], sign=",".join(map(str, sorted(set(g["sign"])))),
                 out_syn=int(g["out_syn"].sum()),
                 codex_nt="/".join(f"{k}{v}" for k, v in g["codex_nt"].value_counts().items()),
                 codex_score=g["codex_score"].median(),
                 top_nt="/".join(f"{k}{v}" for k, v in g["top_nt"].value_counts().items()),
                 top_conf=g["top_nt_conf"].median(),
                 known_nt=g["known_nt"].dropna().iat[0] if g["known_nt"].notna().any() else "",
                 known_src=g["known_src"].dropna().iat[0] if g["known_src"].notna().any() else "")
        for v in RUNS:
            h = g[f"hz_{v}"]
            o[f"act_{v}"] = int((h > 0).sum())
            o[f"hz_{v}"] = h.mean()
            o[f"spk%_{v}"] = 100 * h.sum() / tot[v][0]
            o[f"drv%_{v}"] = 100 * g[f"drive_{v}"].sum() / tot[v][1]
        return pd.Series(o)

    t = loop.groupby("type").apply(agg, include_groups=False).sort_values("drv%_spiking", ascending=False)
    t.to_csv("sa2_diag_types.csv")
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_colwidth", 40)
    for v in RUNS:
        print(f"AL/LH/MB (without ORNs) total: spike share {t[f'spk%_{v}'].sum():.1f} %, "
              f"in-loop output share {t[f'drv%_{v}'].sum():.1f} % ({v})")
    print(t[t["drv%_spiking"] > 0.2].round(2).to_string())
    nan = loop["codex_nt"].eq("NaN")
    low = (loop["codex_score"] < 0.5) & ~nan
    for v in RUNS:
        print(f"{v}: by Codex NT class (AL/LH/MB, without ORNs): n / active in cut-off / spike % / in-loop output % "
              f"(excitatory-signed part)")
        for nm, m in (("NaN", nan), ("score < 0.5", low), ("score >= 0.5", ~nan & ~low)):
            g = loop[m]
            print(f"  {nm:12s} {len(g):5d} {(g[f'hz_{v}'] > 0).sum():5d} "
                  f"{100 * g[f'hz_{v}'].sum() / tot[v][0]:5.1f} {100 * g[f'drive_{v}'].sum() / tot[v][1]:5.1f} "
                  f"({100 * g.loc[g['sign'] > 0, f'drive_{v}'].sum() / tot[v][1]:.1f})")


if __name__ == "__main__":
    main()
