"""brain-control: pre-registered readout sets (flight/readouts.py)."""
import numpy as np
import pandas as pd
import pytest

from flight import groups as G
from flight.readouts import READOUT_TYPES, STEER_TYPES, Readouts, build_readouts


@pytest.fixture(scope="module")
def root_ids():
    return G.load_root_ids()


def test_sets_by_root_id(root_ids):
    """Every readout neuron is found through root_id -> Completeness row, one per side."""
    sets = build_readouts(root_ids)
    assert tuple(sets) == READOUT_TYPES and STEER_TYPES == ("DNa02", "DNp15")
    dn = pd.read_csv(G.PATH_DN)
    for t in ("DNa02", "DNp15", "DNa01", "DNp01"):
        for s, side in (("L", "left"), ("R", "right")):
            rid = dn.loc[(dn.cell_type == t) & (dn.side == side), "root_id"].to_numpy()
            assert list(root_ids[sets[t][s]]) == sorted(rid, key=lambda r: np.flatnonzero(root_ids == r)[0])
            assert len(sets[t][s]) == 1
    mn9 = root_ids[np.concatenate([sets["MN9"]["L"], sets["MN9"]["R"]])]
    assert set(mn9) == {720575940618238523, 720575940660219265}


def test_counts_and_rates(root_ids):
    ro = Readouts(root_ids)
    per = np.zeros(len(root_ids), int)
    per[ro.local["DNa02"]["L"]] = 3
    per[ro.local["MN9"]["R"]] = 2
    c = ro.counts(per)
    assert c.shape == (len(READOUT_TYPES), 2)
    assert c[Readouts.row("DNa02")].tolist() == [3, 0] and c[Readouts.row("MN9")].tolist() == [0, 2]
    np.testing.assert_allclose(ro.rates(c, 0.025)[Readouts.row("DNa02"), 0], 120.0)


def test_dev_map_drops_missing(root_ids):
    g2l = np.full(len(root_ids), -1)
    ro_full = build_readouts(root_ids)
    keep = ro_full["DNa02"]["L"][0]
    g2l[keep] = 0
    ro = Readouts(root_ids, g2l)
    assert ro.local["DNa02"]["L"].tolist() == [0] and len(ro.local["DNp15"]["L"]) == 0
