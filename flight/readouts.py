"""Pre-registered brain readouts (SPEC_BRAIN_CONTROL R2 table + Step 0 decisions).

Fixed from anatomy and literature before any behaviour was seen; never changed
afterwards. Every index comes from root_id -> Completeness_783.csv row
(descending_neurons.csv for DNs, annotations cell_type CB0701 for MN9).

  STEER_TYPES  DNa02 + DNp15 L/R   yaw (Step 2), both recorded. DNa02: ipsilateral turning in
               walking (Rayshubskiy et al.), flight role VARSAYIM; DNp15: HS/H2 1 hop (user
               decision, Step 0 decisions 2).
  STEER_DRIVE  DNp15 only drives the yaw command: POST-HOC choice after the Step 2 data
               (SPEC "Step 2 decisions"); DNa02 is recorded only.
  MN9          CB0701 L/R          proboscis motor neuron (Shiu et al. 2023; R0), Step 1.
  others       recorded only (looming DNp01/02/04/11/06, landing DNp07/10, contralateral
               looming DNa01/DNb01, optic-flow DNp20/DNb06, DNa03).
"""
import numpy as np
import pandas as pd

from flight import groups as G

STEER_TYPES = ("DNa02", "DNp15")   # normalised L-R computed and recorded for both
STEER_DRIVE = ("DNp15",)           # drives the yaw command (Step 2 decisions: POST-HOC, DNa02 recorded only)
MN9_TYPE = "CB0701"
READOUT_TYPES = ("DNa02", "DNp15", "MN9", "DNa01", "DNa03", "DNb01", "DNb06", "DNp20",
                 "DNp01", "DNp02", "DNp04", "DNp11", "DNp06", "DNp07", "DNp10")
SIDES = ("L", "R")


def build_readouts(root_ids, path_dn=G.PATH_DN, path_ann=G.PATH_ANN):
    """{type: {"L": idx, "R": idx}} with Completeness row indices (global)."""
    r2i = G.root_to_index(root_ids)
    dn = pd.read_csv(path_dn)
    ann = pd.read_csv(path_ann, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"])
    out = {}
    for t in READOUT_TYPES:
        src = ann[ann["cell_type"].astype(str) == MN9_TYPE] if t == "MN9" else dn[dn["cell_type"].astype(str) == t]
        s = src["side"].astype(str).str.lower()
        out[t] = {sd: G._idx(src.loc[s == full, "root_id"], r2i) for sd, full in (("L", "left"), ("R", "right"))}
        if not (len(out[t]["L"]) and len(out[t]["R"])):
            raise ValueError(f"readout {t}: missing side")
    return out


class Readouts:
    """Per-step spike counts of the readout sets from the per-neuron counts of FlightBrain.step().

    g2l: optional global -> local index map (DEV subnet); neurons outside the subnet are dropped."""

    def __init__(self, root_ids, g2l=None):
        self.sets = build_readouts(root_ids)
        self.local = {}
        for t, d in self.sets.items():
            self.local[t] = {}
            for s, idx in d.items():
                li = idx if g2l is None else g2l[idx]
                self.local[t][s] = li[li >= 0]
        self.n = np.array([[len(self.local[t][s]) for s in SIDES] for t in READOUT_TYPES])

    def counts(self, per_neuron):
        """(len(READOUT_TYPES), 2) int spike counts, rows in READOUT_TYPES order, columns L, R."""
        return np.array([[int(per_neuron[self.local[t][s]].sum()) for s in SIDES] for t in READOUT_TYPES])

    def rates(self, counts, dt):
        """Counts -> Hz per neuron."""
        return counts / (np.maximum(self.n, 1) * dt)

    @staticmethod
    def row(t):
        return READOUT_TYPES.index(t)
