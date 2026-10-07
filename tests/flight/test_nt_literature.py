"""--nt-literature (SPEC_SENSORY_INPUTS §3.2c): literature NT signs for the odour persistent-state cell types.

Table rule (data/nt_literature_783.csv), root_id mapping, the expected sign changes against the parquet,
CLI / file stem, and DEV-subnet brain builds with the flag off and on (DEV only, never a result):
|w| unchanged, sign = sign_lit for the table neurons, every other synapse identical.
"""
import re

import numpy as np
import pandas as pd
import pytest

from flight import groups as G
from flight.recorder import output_stem

# data/nt_literature_783.csv is only needed for --nt-literature and is not rebuilt by scripts/fetch_data.py
# (it needs the Stage A run outputs); without it this module is skipped.
pytestmark = pytest.mark.skipif(not G.PATH_NT_LIT.exists(),
                                reason=f"{G.PATH_NT_LIT.name} missing (see scripts/make_nt_literature.py)")

FAST = {"acetylcholine": 1, "gaba": -1, "glutamate": -1}
# REPORT_SENSORY_A2 §2.4: the only neurons whose model sign differs from the literature
CHANGED = {"il3LN6": 2, "lLN2P_b": 12, "v2LN36": 2, "DPM": 2, "PPL203": 2, "MBON05": 1, "DN1a": 1, "LHPV6o1": 2}


@pytest.fixture(scope="module")
def tab():
    return pd.read_csv(G.PATH_NT_LIT, keep_default_na=False)


@pytest.fixture(scope="module")
def root_ids():
    return G.load_root_ids()


@pytest.fixture(scope="module")
def lit(root_ids):
    return G.nt_literature_indices(root_ids)


@pytest.fixture(scope="module")
def parquet_sign(root_ids):
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_Index", "Excitatory"])
    s = np.zeros(len(root_ids), np.int64)
    s[con["Presynaptic_Index"].to_numpy()] = con["Excitatory"].to_numpy()
    return s


def test_table_rule(tab):
    assert tab["cell_type"].is_unique and len(tab) == 370
    assert set(tab["sign_lit"]) <= {-1, 0, 1}
    assert tab["source"].str.len().gt(0).all() and set(tab["confidence"]) <= {"yüksek", "orta"}
    for _, r in tab.iterrows():
        toks = {t.strip() for t in re.split(r"[;,|]", r["known_nt"])}
        fast = sorted(t for t in toks if t in FAST)
        if r["sign_lit"] != 0:
            assert len(fast) == 1 and FAST[fast[0]] == r["sign_lit"], r["cell_type"]
        if len(fast) != 1:
            assert r["sign_lit"] == 0, r["cell_type"]
    assert int((tab["sign_lit"] != 0).sum()) == 272
    t = tab.set_index("cell_type")
    assert t.loc["lLN1_bc", "sign_lit"] == 1 and t.loc["lLN1_bc", "n_change"] == 0
    assert "Eckstein" in t.loc["lLN1_bc", "source"]
    ch = t[t["n_change"] > 0]["n_change"].to_dict()
    assert ch == CHANGED


def test_indices_and_changes(root_ids, lit, tab, parquet_sign):
    idx, sgn, typ = lit
    assert np.all(np.diff(idx) > 0) and len(idx) == len(sgn) == len(typ)
    want = tab[tab["sign_lit"] != 0].set_index("cell_type")["sign_lit"]
    assert set(typ) <= set(want.index)
    np.testing.assert_array_equal(sgn, want.reindex(typ).to_numpy())
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "hemibrain_type"])
    ann = ann.drop_duplicates("root_id").set_index("root_id")
    t2 = ann["cell_type"].fillna(ann["hemibrain_type"]).reindex(root_ids[idx]).to_numpy(str)
    np.testing.assert_array_equal(t2, typ)
    has_out = parquet_sign[idx] != 0
    diff = has_out & (parquet_sign[idx] != sgn)
    got = pd.Series(typ[diff]).value_counts().to_dict()
    assert got == CHANGED and int(diff.sum()) == 24


def test_cli_and_stem():
    from fly_flight_brain_body_simulation import parse_args
    assert parse_args(["--nt-literature"]).nt_literature
    assert not parse_args([]).nt_literature
    with pytest.raises(SystemExit):
        parse_args(["--nt-literature", "--nt-modulatory-silent"])
    assert output_stem(3, hybrid=True, olfaction_full=True, vision_boundary=True, apl_graded=True,
                       nt_literature=True) == "flight_v3_hybrid_sA_sB_aplG_ntLit"
    assert "ntLit" not in output_stem(3, hybrid=True)


def test_dev_brain_signs(root_ids, lit, parquet_sign):
    """DEV subnet (never a result): flag off = parquet signs; flag on = |w| kept, sign_lit on table neurons."""
    from flight.brain import FlightBrain
    off = FlightBrain(dev_subnet=True, seed=0, verbose=False, olfaction_full=True)
    on = FlightBrain(dev_subnet=True, seed=0, verbose=False, olfaction_full=True, nt_literature=True)
    np.testing.assert_array_equal(off.l2g, on.l2g)
    i_off, i_on = np.asarray(off.syn.i[:]), np.asarray(on.syn.i[:])
    np.testing.assert_array_equal(i_off, i_on)
    np.testing.assert_array_equal(np.asarray(off.syn.j[:]), np.asarray(on.syn.j[:]))
    w0, w1 = np.asarray(off.syn.w_[:]), np.asarray(on.syn.w_[:])
    gpre = off.l2g[i_off]
    np.testing.assert_array_equal(np.sign(w0), parquet_sign[gpre])
    np.testing.assert_allclose(np.abs(w1), np.abs(w0))
    idx, sgn, _ = lit
    sign_of = np.zeros(len(root_ids), np.int64)
    sign_of[idx] = sgn
    m = sign_of[gpre] != 0
    assert m.any()
    np.testing.assert_array_equal(np.sign(w1[m]), sign_of[gpre[m]])
    np.testing.assert_array_equal(w1[~m], w0[~m])
    info = on.nt_lit_info
    assert info["n_edges_changed"] == int((np.sign(w1) != np.sign(w0)).sum()) > 0
    assert set(info["types_changed"]) <= set(CHANGED)
    assert off.nt_lit_info is None
    with pytest.raises(ValueError):
        FlightBrain(dev_subnet=True, seed=0, verbose=False, nt_literature=True, nt_silent="broad")
