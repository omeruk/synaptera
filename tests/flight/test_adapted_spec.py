"""Checks written from docs/ADAPTED_CODE.md section D (specification of the re-implemented parts)."""
import numpy as np
import pandas as pd
import pytest

from flight import config as cfg
from flight import groups as G
from flight import hybrid as H
from flight import sensors as S


# ── D.3 turn_hand ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("I", [-0.3, -0.01, 0.0, 0.004, 0.05, 2.0])
def test_turn_hand_formula_and_saturation(I):
    assert H.turn_hand(I, "takeoff") == cfg.ODOR_TURN_K * float(np.tanh(cfg.ODOR_TURN_GAIN * I))
    assert abs(H.turn_hand(I, "cruise")) <= cfg.ODOR_TURN_K


def test_turn_hand_constants_and_sign():
    assert (cfg.ODOR_TURN_K, cfg.ODOR_TURN_GAIN) == (2.0, 20.0)
    assert H.turn_hand(0.5, "cruise") > 0 > H.turn_hand(-0.5, "cruise")
    assert np.isnan(H.turn_hand(float("nan"), "cruise"))
    assert H.turn_hand(0.5, "cruise", ablate_odor=True) == 0.0


# ── D.4 LoomBias ─────────────────────────────────────────────────────────────
def test_loom_bias_update_rule():
    assert (cfg.FLYVIS_T5_GAIN, cfg.FLYVIS_DECAY, cfg.FLYVIS_BIAS_MAX) == (0.5, 0.5, 0.15)
    lb = S.LoomBias()
    p = lb(0.0, 0.0)
    assert p == 0.0
    p = lb(0.0, 0.2)                                  # drive = -g*(L-R) = +0.1, smoothed with d = 0.5
    assert p == pytest.approx(0.05)
    q = lb(0.1, 0.1)                                  # no asymmetry: decays by the factor d
    assert q == pytest.approx(0.5 * p)


def test_loom_bias_clamps_and_keeps_state():
    assert S.LoomBias()(0.0, 100.0) == 0.15
    lb = S.LoomBias()
    assert lb(100.0, 0.0) == -0.15
    assert lb(0.0, 0.0) == pytest.approx(-0.075)      # 0.5 * (-0.15)
    assert np.isnan(S.LoomBias()(float("nan"), 0.0))


# ── D.1 annotation groups ────────────────────────────────────────────────────
def _tables():
    ann = pd.DataFrame({
        "root_id": [10, 11, 12, 13, 14, 15, 16, 17, 99],
        "cell_class": ["olfactory", "ORN", "ascending", "LA>ME", "LA>ME", "brain_motor_neuron", None, "x", "olfactory"],
        "cell_type": ["a", "b", "c", "d", "e", "f", "SEZ_x", "Gustatory", "z"],
        "super_class": ["s", "s", "ascending", "s", "s", "s", "s", "s", "s"],
        "side": ["left", " Right ", "left", "left", "right", "center", "left", None, "left"],
    })
    dn = pd.DataFrame({
        "root_id": [20, 21, 22, 23, 24, 25],
        "cell_type": ["DNg02_a", "DNg02", "DNa01", "DNa02", "DNp01", "DNg021"],
        "side": ["left", "right", "left", "right", "left", "bogus"],
    })
    return ann, dn


def test_annotation_groups_follow_the_spec():
    ann, dn = _tables()
    roots = [10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 25]      # 99 is not in the brain
    r2i = G.root_to_index(roots)
    ann = ann[ann["root_id"].isin(r2i)].reset_index(drop=True)
    g = G._annotation_groups(ann, dn, r2i)
    row = lambda *r: [r2i[x] for x in r]
    assert g["ascending"].tolist() == row(12)
    assert g["olf_L"].tolist() == row(10) and g["olf_R"].tolist() == row(11) and g["olf_C"].tolist() == []
    assert g["sez"].tolist() == row(16, 17)                    # case-insensitive, any of the three columns
    assert g["vis_L"].tolist() == row(13) and g["vis_R"].tolist() == row(14)
    assert g["brain_mn"].tolist() == row(15)
    assert g["dn_L"].tolist() == row(20, 22, 24) and g["dn_R"].tolist() == row(21, 23)
    assert g["dn_C"].tolist() == row(25)
    assert g["dng02_L"].tolist() == row(20) and g["dng02_R"].tolist() == row(21)   # DNg021 is not DNg02
    assert g["steer_L"].tolist() == row(22) and g["steer_R"].tolist() == row(23)
    assert g["dnp01"].tolist() == row(24)
    assert all(v.dtype == np.int64 for v in g.values())


def test_la_me_without_side_is_an_error():
    ann, dn = _tables()
    ann.loc[3, "side"] = None
    r2i = G.root_to_index(list(ann["root_id"]) + list(dn["root_id"]))
    with pytest.raises(ValueError):
        G._annotation_groups(ann, dn, r2i)


# ── D.2 neuron_positions ─────────────────────────────────────────────────────
def test_neuron_positions_fallbacks(tmp_path):
    tsv = tmp_path / "ann.tsv"
    pd.DataFrame({
        "root_id": [3, 1, 2, 4, 7],
        "soma_x": [30.0, np.nan, 20.0, np.nan, 1.0], "soma_y": [3.0, np.nan, np.nan, np.nan, 1.0],
        "pos_x": [0.0, 10.0, 0.0, np.nan, 0.0], "pos_y": [0.0, 1.0, 2.0, np.nan, 0.0],
    }).to_csv(tsv, sep="\t", index=False)
    p = G.neuron_positions([1, 2, 3, 4], path_ann=tsv)                    # 7 not in the brain; 4 has no position
    assert p["idx"].tolist() == [0, 1, 2] and p["idx"].dtype == np.int32
    assert p["x"].tolist() == [10.0, 20.0, 30.0] and p["z"].tolist() == [-1.0, -2.0, -3.0]
    assert p["x"].dtype == np.float32 and p["z"].dtype == np.float32
