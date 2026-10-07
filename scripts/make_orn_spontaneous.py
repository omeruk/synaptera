"""data/orn_spontaneous_783.csv: spontaneous ORN rate per glomerulus (Stage A, SPEC_SENSORY_INPUTS §2.2).

Source of the rates: Hallem & Carlson 2006 (Cell 125:143-160, doi 10.1016/j.cell.2006.01.050),
spontaneous firing rate of each of the 24 receptors measured in the empty neuron, as transcribed
in the DoOR database (Münch & Galizia 2016, Sci Rep 6:21841; github.com/ropensci/DoOR.data,
formerly Dahaniel/DoOR.data): per-receptor csv `data/<receptor>.csv`, odorant row InChIKey "SFR",
column "Hallem.2006.EN". Receptor -> glomerulus from DoOR `data/door_mappings.csv` (column
`glomerulus`; used as provided by DoOR.data; the source papers of the mapping were not verified).

Rules (fixed before any run; no value invented):
  - a glomerulus whose receptor(s) have a Hallem.2006.EN SFR value gets that value;
  - a glomerulus with two co-expressed H&C receptors (DM3: Or47a + Or33b; DM5: Or85a + Or33b)
    gets their mean (VARSAYIM: the empty-neuron rates of single receptors do not say how a
    neuron expressing both fires);
  - every other glomerulus: 5 Hz (VARSAYIM, SPEC §2.2).
Other DoOR datasets' SFR values are listed in `door_other_sfr` for information only (not used).
Glomeruli are the 53 ORN_<glomerulus> cell types of flywire_annotations.tsv in the simulated network.

    env -u PYTHONPATH python scripts/make_orn_spontaneous.py [--door-dir DIR]
Without --door-dir the needed csv files are downloaded from the pinned DoOR.data commit.
"""
import argparse
import io
import os
import sys
import urllib.request

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from flight import groups as G  # noqa: E402

DOOR_REPO = "ropensci/DoOR.data"
DOOR_COMMIT = "db323a496577c4b4a72b5c2fcd1859e07521ffb5"
HC_COLUMN = "Hallem.2006.EN"
DEFAULT_HZ = 5.0
OUT = os.path.join(_ROOT, "data", "orn_spontaneous_783.csv")


def _read(name, door_dir):
    if door_dir:
        return pd.read_csv(os.path.join(door_dir, name), sep=";")
    url = f"https://raw.githubusercontent.com/{DOOR_REPO}/{DOOR_COMMIT}/data/{name}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return pd.read_csv(io.BytesIO(r.read()), sep=";")


def receptor_sfr(door_dir=None):
    """{receptor: (H&C 2006 SFR or nan, {other dataset: SFR})} for every mapped receptor."""
    m = _read("door_mappings.csv", door_dir)
    out = {}
    for rec in m["receptor"].dropna().unique():
        if rec in ("?",) or rec.startswith(("ab", "ac", "pb")):
            continue
        try:
            d = _read(f"{rec}.csv", door_dir)
        except Exception:
            continue
        s = d[d["InChIKey"] == "SFR"]
        if s.empty:
            continue
        vals = {c: float(s[c].iloc[0]) for c in d.columns[5:] if pd.notna(s[c].iloc[0])}
        out[rec] = (vals.pop(HC_COLUMN, np.nan), vals)
    return m, out


def build(door_dir=None):
    m, sfr = receptor_sfr(door_dir)
    root_ids = G.load_root_ids()
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"])
    ann = ann[ann["root_id"].isin(set(root_ids.tolist()))]
    orn = ann[ann["cell_type"].astype(str).str.startswith("ORN_")]
    rows = []
    for ct, grp in orn.groupby("cell_type"):
        glom = ct[4:]
        s = grp["side"].astype(str).str.lower()
        # receptors whose DoOR glomerulus string names this glomerulus (e.g. "DM5+DM3")
        recs = [r for r, g in zip(m["receptor"], m["glomerulus"].astype(str))
                if r in sfr and glom in g.replace("/", "+").split("+")]
        hc = {r: sfr[r][0] for r in recs if np.isfinite(sfr[r][0])}
        other = {f"{r}:{k}": v for r in recs for k, v in sfr[r][1].items()}
        if hc:
            hz = float(np.mean(list(hc.values())))
            src = "Hallem & Carlson 2006 (DoOR " + HC_COLUMN + " SFR)"
            if len(hc) > 1:
                src += "; co-expressed receptors, mean (VARSAYIM)"
        else:
            hz, src = DEFAULT_HZ, "VARSAYIM 5 Hz (no Hallem & Carlson 2006 receptor)"
        rows.append(dict(glomerulus=glom, cell_type=ct, n_L=int((s == "left").sum()), n_R=int((s == "right").sum()),
                         n_na=int((~s.isin(["left", "right"])).sum()),
                         receptors_hc2006=" ".join(f"{r}={v:g}" for r, v in hc.items()),
                         receptors_door=" ".join(recs), spont_hz=hz, source=src,
                         food=glom in G.FOOD_GLOMERULI,
                         door_other_sfr=" ".join(f"{k}={v:g}" for k, v in other.items())))
    df = pd.DataFrame(rows).sort_values("glomerulus").reset_index(drop=True)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--door-dir", default=None, help="local copy of DoOR.data/data (csv files)")
    a = ap.parse_args()
    df = build(a.door_dir)
    df.to_csv(OUT, index=False)
    hc = df["source"].str.startswith("Hallem")
    print(df[["glomerulus", "n_L", "n_R", "n_na", "receptors_hc2006", "spont_hz", "food"]].to_string())
    print(f"{len(df)} glomeruli, {int(hc.sum())} from Hallem & Carlson 2006, {int((~hc).sum())} at {DEFAULT_HZ} Hz; "
          f"{int(df[['n_L', 'n_R', 'n_na']].to_numpy().sum())} ORNs -> {OUT}")
