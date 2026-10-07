"""Stage A (--olfaction-full, SPEC_SENSORY_INPUTS §2.2): every typed ORN at its glomerulus' spontaneous rate.

Groups orn_all_L/R/C: all 2,275 neurons of the 53 ORN_<glomerulus> cell types (flywire_annotations.tsv),
by root_id -> Completeness row, side = antenna of origin (C: side na). They replace orn_food_L/R/C.
Rate of an ORN of glomerulus g (Hz):
    r = r_spont,g + food_g * (R_ODOR - r_spont,g) * f
r_spont,g from data/orn_spontaneous_783.csv (Hallem & Carlson 2006 via DoOR, else 5 Hz VARSAYIM;
scripts/make_orn_spontaneous.py); food_g = g in FOOD_GLOMERULI (DM1 DM2 DM4 VA2 VM2 DP1m); R_ODOR =
cfg.ORN_FOOD_RATE[1] (150 Hz); f = odor_norm of the ipsilateral antenna (L: left, R: right, C: mean of
both, as orn_food_C). The other 47 glomeruli stay at their spontaneous rate (no odour model for them).
"""
import numpy as np
import pandas as pd

from flight import config as cfg
from flight import groups as G

PATH_TABLE = G.DATA_DIR / "orn_spontaneous_783.csv"
GROUPS = ("orn_all_L", "orn_all_R", "orn_all_C")
R_ODOR = cfg.ORN_FOOD_RATE[1]


def load_table(path=PATH_TABLE):
    return pd.read_csv(path)


def _orn_ann(root_ids):
    r2i = G.root_to_index(root_ids)
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"])
    ann = ann[ann["root_id"].isin(r2i) & ann["cell_type"].astype(str).str.startswith("ORN_")].copy()
    ann["idx"] = ann["root_id"].map(r2i).astype(np.int64)
    ann["glom"] = ann["cell_type"].astype(str).str[4:]
    ann["sd"] = G._side(ann["side"]).map({"left": "L", "right": "R"}).fillna("C")
    return ann.sort_values("idx")


def orn_groups(root_ids):
    """{"orn_all_L"/"_R"/"_C": sorted Completeness row indices} of all typed ORNs."""
    ann = _orn_ann(root_ids)
    return {f"orn_all_{s}": ann.loc[ann["sd"] == s, "idx"].to_numpy(np.int64) for s in "LRC"}


class OlfactionFull:
    """Per-neuron spontaneous rate and food mask in the group order of orn_groups()."""

    def __init__(self, root_ids, path=PATH_TABLE):
        tab = load_table(path).set_index("glomerulus")
        ann = _orn_ann(root_ids)
        missing = set(ann["glom"]) - set(tab.index)
        if missing:
            raise ValueError(f"glomeruli without a spontaneous rate: {sorted(missing)}")
        self.table = tab
        self.idx, self.spont, self.food, self.glom = {}, {}, {}, {}
        for s in "LRC":
            a = ann[ann["sd"] == s]
            k = f"orn_all_{s}"
            self.idx[k] = a["idx"].to_numpy(np.int64)
            self.glom[k] = a["glom"].to_numpy(str)
            self.spont[k] = tab.loc[a["glom"], "spont_hz"].to_numpy(float)
            self.food[k] = a["glom"].isin(G.FOOD_GLOMERULI).to_numpy()

    def rates(self, f_L, f_R):
        """{group: per-neuron rate array} for normalised antenna odour f_L, f_R in [0, 1]."""
        f = {"orn_all_L": f_L, "orn_all_R": f_R, "orn_all_C": 0.5 * (f_L + f_R)}
        out = {}
        for k, fk in f.items():
            fk = float(np.clip(fk, 0.0, 1.0))
            out[k] = self.spont[k] + self.food[k] * (R_ODOR - self.spont[k]) * fk
        return out

    def food_mean(self, rates, side):
        """Mean rate of the food-glomerulus ORNs of one side (recorded as olf_rate_L/R)."""
        k = f"orn_all_{side}"
        return float(rates[k][self.food[k]].mean())

    def summary(self):
        n = {k: len(v) for k, v in self.idx.items()}
        sp = np.concatenate(list(self.spont.values()))
        return dict(table=str(PATH_TABLE.relative_to(G.DATA_DIR.parent)), n=n, n_total=int(sum(n.values())),
                    n_food=int(sum(int(v.sum()) for v in self.food.values())),
                    spont_mean_hz=float(sp.mean()), spont_min_hz=float(sp.min()), spont_max_hz=float(sp.max()),
                    n_glomeruli=int(len(self.table)),
                    n_glomeruli_hc2006=int(self.table["source"].str.startswith("Hallem").sum()),
                    rule="r = r_spont,g + food_g*(R_ODOR - r_spont,g)*f, f = odor_norm (ipsilateral antenna)",
                    r_odor=R_ODOR, food_glomeruli=list(G.FOOD_GLOMERULI))
