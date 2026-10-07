"""Write data/nt_literature_783.csv for --nt-literature (SPEC_SENSORY_INPUTS §3.2c, REPORT_SENSORY_A2 §2).

One row per cell type that takes part in the odour persistent state (scripts/diag/sa2_diag.py:
dominant neuropil AL, LH or MB_*, not an ORN, >= 1 spike in the input-cut window of the Stage A smokes
v17 or v18) and has a literature transmitter in flywire_annotations.tsv (known_nt / known_nt_source:
the literature compilation of Schlegel et al. 2024, Nature 634:139). Placeholder groups without a cell
type ("[class]") are skipped.

Sign rule (fixed before any run):
  * fast transmitters in known_nt (ignoring "-negative" entries, peptides, NO and amines):
    acetylcholine -> +1; gaba -> -1; glutamate -> -1 (the model's own NT->sign mapping, unchanged)
  * exactly one fast transmitter -> sign_lit = that sign; none (only DA/5-HT/OA/negatives) or more
    than one, or not every neuron of the type carries the same known_nt -> sign_lit = 0 (no
    literature sign; not touched)
Confidence (reported only, not used by the rule): "orta" if the only evidence is scRNA-seq, lineage-
or tract-based, or the type is matched to Shang et al. 2007 cholinergic eLNs by morphology; else "yüksek" (Turkish for "high"; kept: it is the value stored in data/nt_literature_783.csv).

    env -u PYTHONPATH .../envs/neurofly/bin/python scripts/make_nt_literature.py --diag sa2_diag_neurons.parquet
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from flight import groups as G  # noqa: E402

FAST = {"acetylcholine": 1, "gaba": -1, "glutamate": -1}
LOOP_NP = ("AL", "LH", "MB_CA", "MB_ML", "MB_PED", "MB_VL")
# Verified in the primary/secondary text this round (REPORT_SENSORY_A2 §2.2); appended to the source.
EXTRA = {"lLN1_bc": "Eckstein et al. 2024 (Cell 187:2574; discussion: broad unilateral 'ALl1 dorsal' LNs likely "
                    "cholinergic, lLN1_bc mispredicted DA/5-HT); Huang et al. 2010 (Neuron 67:1021)"}


def fast_nt(s):
    if not isinstance(s, str):
        return ()
    toks = {t.strip() for t in re.split(r"[;,]", s)}
    return tuple(sorted(t for t in toks if t in FAST))


def confidence(src, typ):
    s = src.lower()
    if "shang et al., 2007" in s:
        return "orta"
    if "lineage" in s or "tract based" in s:
        return "orta"
    if not any(k in s for k in ("immuno", "tapin", "easi-fish", "rnai", "intersection", "mcfo", "marcm")):
        return "orta"
    return "yüksek"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diag", required=True, help="sa2_diag_neurons.parquet (scripts/diag/sa2_diag.py)")
    ap.add_argument("--out", default=str(G.DATA_DIR / "nt_literature_783.csv"))
    a = ap.parse_args()
    d = pd.read_parquet(a.diag)
    rid = G.load_root_ids()
    assert np.array_equal(d["root_id"].to_numpy(), rid)
    act = (d["hz_spiking"] > 0) | (d["hz_graded"] > 0)
    loop = d[d["dom"].isin(LOOP_NP) & ~d["is_orn"] & act]
    tot_s, tot_g = d["drive_spiking"].sum(), d["drive_graded"].sum()
    rows = []
    for typ in sorted(set(loop["type"])):
        if typ.startswith("["):
            continue
        g = d[d["type"] == typ]
        kn = g["known_nt"].dropna()
        if kn.empty:
            continue
        fs = {fast_nt(k) for k in kn}
        f = next(iter(fs)) if len(fs) == 1 else ()
        sign = FAST[f[0]] if len(f) == 1 and len(kn) == len(g) else 0
        src = "; ".join(sorted(set(g["known_src"].dropna())))
        if typ in EXTRA:
            src += "; " + EXTRA[typ]
        lp = loop[loop["type"] == typ]
        rows.append(dict(
            cell_type=typ, n=len(g), n_loop_s=int((lp["hz_spiking"] > 0).sum()), n_loop_g=int((lp["hz_graded"] > 0).sum()),
            known_nt=" | ".join(sorted(set(kn))), fast_nt="/".join(f) if f else "",
            sign_lit=sign, source="Schlegel et al. 2024 known_nt: " + src, confidence=confidence(src, typ),
            model_sign=",".join(str(x) for x in sorted(set(g["sign"]))),
            n_change=int(((g["sign"] != sign) & (sign != 0)).sum()),
            codex_nt=",".join(f"{k}{v}" for k, v in g["codex_nt"].value_counts().items()),
            loop_drive_pct_s=round(100 * g["drive_spiking"].sum() / tot_s, 3),
            loop_drive_pct_g=round(100 * g["drive_graded"].sum() / tot_g, 3)))
    out = pd.DataFrame(rows)
    out.to_csv(a.out, index=False)
    ch = out[out["n_change"] > 0]
    print(f"{len(out)} types with a literature NT; sign_lit != 0: {(out['sign_lit'] != 0).sum()}; "
          f"changed: {len(ch)} types, {ch['n_change'].sum()} neurons")
    print(ch[["cell_type", "n", "fast_nt", "sign_lit", "model_sign", "n_change", "confidence",
              "loop_drive_pct_s", "loop_drive_pct_g"]].to_string(index=False))


if __name__ == "__main__":
    main()
