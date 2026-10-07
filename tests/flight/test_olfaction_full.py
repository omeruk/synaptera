"""Stage A (--olfaction-full, SPEC_SENSORY_INPUTS §2.2): all typed ORNs at their glomerulus' spontaneous rate.

Table (data/orn_spontaneous_783.csv), groups by root_id, rate rule, brain input names, file stem, CLI,
and one DEV-subnet brain build with the new Poisson groups (DEV only, never a result).
"""
import numpy as np
import pandas as pd
import pytest

from flight import config as cfg
from flight import groups as G
from flight import olfaction_full as OF
from flight.brain import input_names
from flight.recorder import output_stem

# data/orn_spontaneous_783.csv is not distributed in the public snapshot (THIRD_PARTY.md §3); it is rebuilt by
# scripts/fetch_data.py (scripts/make_orn_spontaneous.py). Without it this module is skipped.
pytestmark = pytest.mark.skipif(not OF.PATH_TABLE.exists(),
                                reason=f"{OF.PATH_TABLE.name} missing (scripts/fetch_data.py)")

N_ORN, N_GLOM, N_HC = 2275, 53, 23
# Hallem & Carlson 2006 spontaneous rates as transcribed in DoOR (Hallem.2006.EN, odorant SFR)
HC_SPOT = {"DM2": 4.0, "VA1v": 47.0, "DC1": 29.0, "DM4": 2.0, "VM2": 2.0, "DM3": 13.0, "DM5": 19.5}


@pytest.fixture(scope="module")
def root_ids():
    return G.load_root_ids()


@pytest.fixture(scope="module")
def tab():
    return OF.load_table()


@pytest.fixture(scope="module")
def olf(root_ids):
    return OF.OlfactionFull(root_ids)


def test_table(tab, root_ids):
    assert len(tab) == N_GLOM and tab["glomerulus"].is_unique
    assert int(tab[["n_L", "n_R", "n_na"]].to_numpy().sum()) == N_ORN
    hc = tab["source"].str.startswith("Hallem")
    assert int(hc.sum()) == N_HC
    assert (tab.loc[~hc, "spont_hz"] == 5.0).all()
    assert tab.loc[~hc, "source"].str.contains("VARSAYIM").all()
    assert (tab.loc[hc, "receptors_hc2006"].str.len() > 0).all()
    sp = tab.set_index("glomerulus")["spont_hz"]
    for g, v in HC_SPOT.items():
        assert sp[g] == v
    assert set(tab.loc[tab["food"], "glomerulus"]) == set(G.FOOD_GLOMERULI)


def test_groups_by_root_id(root_ids, olf):
    gr = OF.orn_groups(root_ids)
    assert sum(len(v) for v in gr.values()) == N_ORN
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "side"]).set_index("root_id")
    for s, side in (("L", "left"), ("R", "right")):
        idx = gr[f"orn_all_{s}"]
        assert np.all(np.diff(idx) > 0)
        assert (ann["side"].reindex(root_ids[idx]) == side).all()
        assert ann["cell_type"].reindex(root_ids[idx]).str.startswith("ORN_").all()
        np.testing.assert_array_equal(olf.idx[f"orn_all_{s}"], idx)
    gl = ann["cell_type"].reindex(root_ids[gr["orn_all_L"]]).str[4:].to_numpy()
    np.testing.assert_array_equal(gl, olf.glom["orn_all_L"])
    # the old food-ORN groups are a subset; no overlap with the other inputs
    g = G.build_groups(root_ids)
    allo = np.concatenate(list(gr.values()))
    for s in "LRC":
        assert set(g[f"orn_food_{s}"]) <= set(gr[f"orn_all_{s}"])
    for n in ("sugar", "t45_L", "t45_R", "ascending"):
        assert not set(g[n]) & set(allo)


def test_rates(olf):
    r0 = olf.rates(0.0, 0.0)
    for k in OF.GROUPS:
        np.testing.assert_allclose(r0[k], olf.spont[k])
    r = olf.rates(1.0, 0.0)
    L, R = "orn_all_L", "orn_all_R"
    assert np.all(r[L][olf.food[L]] == cfg.ORN_FOOD_RATE[1])
    np.testing.assert_allclose(r[L][~olf.food[L]], olf.spont[L][~olf.food[L]])
    np.testing.assert_allclose(r[R], olf.spont[R])
    rc = olf.rates(0.4, 0.8)["orn_all_C"]
    fc = olf.food["orn_all_C"]
    np.testing.assert_allclose(rc[fc], olf.spont["orn_all_C"][fc] + (150 - olf.spont["orn_all_C"][fc]) * 0.6)
    assert olf.food_mean(r, "L") == 150.0
    s = olf.summary()
    assert s["n_total"] == N_ORN and s["n_glomeruli_hc2006"] == N_HC
    assert s["n_food"] == 298   # = the orn_food groups (SPEC §1)


def test_input_names_and_stem():
    n = input_names(olfaction_full=True)
    assert {"orn_all_L", "orn_all_R", "orn_all_C"} <= set(n)
    assert not any(x.startswith("orn_food") for x in n)
    assert not any(x.startswith("orn_all") for x in input_names())
    with pytest.raises(ValueError):
        input_names(olfaction=False, olfaction_full=True)
    assert output_stem(5, hybrid=True, olfaction_full=True, vision_boundary=True, apl_graded=True) \
        == "flight_v5_hybrid_sA_sB_aplG"


def test_cli():
    from fly_flight_brain_body_simulation import parse_args
    a = parse_args(["--olfaction-full", "--vision-boundary", "--hybrid"])
    assert a.olfaction_full and not a.no_olfaction
    assert not parse_args([]).olfaction_full
    with pytest.raises(SystemExit):
        parse_args(["--olfaction-full", "--no-olfaction"])


def test_dev_brain_inputs():
    """DEV subnet (never a result): orn_all_* get PoissonGroups with the group sizes, rfc 0, no orn_food."""
    from brian2 import ms
    from flight.brain import FlightBrain
    b = FlightBrain(dev_subnet=True, seed=0, verbose=False, olfaction_full=True)
    assert not any(k.startswith("orn_food") for k in b.inputs)
    for k in OF.GROUPS:
        if len(b.local[k]):
            assert len(b.inputs[k]) == len(b.local[k])
            assert np.all(np.asarray(b.neu.rfc[b.local[k]] / ms) == 0)
    olf = OF.OlfactionFull(b.root_ids)
    b.set_rates(**{k: v for k, v in olf.rates(0.0, 0.0).items() if k in b.inputs})
    _, c = b.step()
    assert c[b.local["orn_all_L"]].sum() > 0
