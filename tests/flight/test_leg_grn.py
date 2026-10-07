"""Leg GRNs (--leg-grn, SPEC_SENSORY_INPUTS §2.4, §3.2b): sugar-like subset chosen by connectivity only.

Data file, reproducibility of the selection (reads the parquet), group by root_id, input names, stem, CLI.
"""
import numpy as np
import pandas as pd
import pytest

from flight import groups as G
from flight.brain import input_names
from flight.recorder import output_stem

N_LEG, N_SEL = 74, 12


@pytest.fixture(scope="module")
def root_ids():
    return G.load_root_ids()


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(G.PATH_LEG_SUGAR)


def test_file(df, root_ids):
    assert len(df) == N_LEG and df["root_id"].is_unique
    assert set(df["root_id"]) <= set(root_ids.tolist())
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False,
                      usecols=["root_id", "super_class", "cell_class", "cell_sub_class"]).set_index("root_id")
    a = ann.reindex(df["root_id"])
    assert (a["super_class"] == "sensory_ascending").all() and (a["cell_class"] == "gustatory").all()
    assert (a["cell_sub_class"] == G.LEG_GRN_SUBCLASS).all()
    assert int(df["selected"].sum()) == N_SEL
    assert (df["selected"] == (df["knn_frac"] > 0.5)).all()
    assert set(df.loc[df["selected"], "side"]) == {"left", "right"}


@pytest.mark.slow
def test_selection_reproducible(df):
    new, loo = G.select_leg_sugar_grns()
    np.testing.assert_array_equal(new["root_id"].to_numpy(), df["root_id"].to_numpy())
    np.testing.assert_array_equal(new["selected"].to_numpy(), df["selected"].to_numpy())
    np.testing.assert_allclose(new["knn_frac"].to_numpy(), df["knn_frac"].to_numpy(), atol=0.006)
    assert loo["n_sugar"] == 129 and loo["n_bitter"] == 65
    assert loo["tp"] == 129 and loo["fp"] == 0


def test_group(root_ids, df):
    g = G.leg_sugar_group(root_ids)["leg_sugar"]
    assert len(g) == N_SEL and np.all(np.diff(g) > 0)
    assert set(root_ids[g].tolist()) == set(df.loc[df["selected"], "root_id"])
    assert not set(g) & set(G.build_groups(root_ids)["sugar"])


def test_names_stem_cli():
    assert "leg_sugar" in input_names(leg_grn=True) and "leg_sugar" not in input_names()
    assert output_stem(2, hybrid=True, olfaction_full=True, vision_boundary=True, leg_grn=True) \
        == "flight_v2_hybrid_sA_sB_legGRN"
    from fly_flight_brain_body_simulation import parse_args
    assert parse_args(["--leg-grn"]).leg_grn and not parse_args([]).leg_grn
