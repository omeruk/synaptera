"""Stage B (--vision-boundary, SPEC_SENSORY_INPUTS §2.1): FlyVis -> FlyWire boundary layer.

Data files (selection rule, columns, transduction constants), groups by root_id, the brain input
names, run-time rates of BoundaryEyes on uniform frames, the display-layer HDF5 stream and the CLI.
~30 s (FlyVis, Completeness, annotations; no parquet, no Brian2 network).
"""
import os

os.environ.setdefault("MUJOCO_GL", "egl")

import h5py
import numpy as np
import pandas as pd
import pytest

from flight import groups as G
from flight import vision_boundary as VB
from flight.brain import input_names

N_TYPES, N_NEURONS = 32, 34121
SUB_THRESHOLD = ("Tm2", "Mi9", "Mi2", "Mi4")     # SPEC §2.1: just below the rule, not driven


@pytest.fixture(scope="module")
def root_ids():
    return G.load_root_ids()


@pytest.fixture(scope="module")
def tab():
    return VB.load_table()


@pytest.fixture(scope="module")
def info():
    return VB.load_types()


@pytest.fixture(scope="module")
def vgroups(root_ids):
    return VB.boundary_groups(root_ids)


@pytest.fixture(scope="module")
def eyes(vgroups):
    return VB.BoundaryEyes({"L": vgroups["vbnd_L"], "R": vgroups["vbnd_R"]}, verbose=False)


def test_rule_and_table(tab, info, root_ids):
    assert len(tab) == N_NEURONS and tab["root_id"].is_unique
    assert tab["fw_type"].nunique() == N_TYPES == info["n_driven_types"]
    assert set(tab["root_id"]) <= set(root_ids.tolist())
    assert set(tab["hemisphere"]) == {"left", "right"}
    types = info["types"]
    driven = {t for t, d in types.items() if d["driven"]}
    assert driven == set(tab["fw_type"])
    for t, d in types.items():
        assert d["driven"] == (d["frac_out_nonflyvis"] >= VB.BOUNDARY_FRAC)
    for t in SUB_THRESHOLD:
        assert not types[t]["driven"]
    assert {f"T{k}{s}" for k in (4, 5) for s in "abcd"} <= driven


def test_columns(tab, info):
    col = pd.read_csv(G.PATH_COLUMNS).set_index("root_id")
    c = tab[tab["col_source"] == "column_assignment"]
    assert len(c) == 25096
    ref = col.loc[c["root_id"]]
    assert np.array_equal(ref["p"].to_numpy(), c["p"].to_numpy())
    assert np.array_equal(ref["q"].to_numpy(), c["q"].to_numpy())
    assert np.array_equal(ref["hemisphere"].to_numpy(), c["hemisphere"].to_numpy())
    assert set(tab["col_source"]) <= {"column_assignment", "partner_mean", "centroid_ME", "centroid_LO",
                                      "centroid_LOP"}
    # the inferred-column rule was chosen by this validation (own column hidden), before any behaviour
    v = info["centroid_validation"]
    assert v["partner_mean"]["le1"] > 0.95 and v["partner_mean"]["le1"] > v["centroid"]["le1"]
    # every neuron sits on a FlyVis column (nearest one outside the extent)
    assert (VB.hex_radius_flyvis(tab["u"], tab["v"]) <= 15).all()


def test_groups_by_root_id(vgroups, root_ids, tab):
    r2i = G.root_to_index(root_ids)
    L, R = vgroups["vbnd_L"], vgroups["vbnd_R"]
    assert len(L) + len(R) == N_NEURONS and not np.intersect1d(L, R).size
    for g in (L, R):
        assert np.all(np.diff(g) > 0)
    assert set(L) == {r2i[r] for r in tab.loc[tab["hemisphere"] == "left", "root_id"]}
    g = G.build_groups(root_ids)
    assert np.isin(g["t45_L"], L).all() and np.isin(g["t45_R"], R).all()


def test_input_names():
    base = input_names("v2", olfaction=False)
    vb = input_names("v2", olfaction=False, vision_boundary=True)
    assert "t45_L" in base and "vbnd_L" not in base
    assert "t45_L" not in vb and {"vbnd_L", "vbnd_R"} <= set(vb)
    assert [n for n in base if not n.startswith("t45_")] == [n for n in vb if not n.startswith("vbnd_")]


def test_transduction_file(eyes):
    tr = VB.load_transduction()
    assert len(tr["a0"]) == len(eyes.net.connectome.nodes.type[:])
    assert tr["r_max"] == 50.0 and tr["r_clip"] == 150.0 and tr["r_central"] == VB.R_CENTRAL
    assert set(tr["responses"]) == {"grating_a", "grating_b", "grating_c", "grating_d", "on_step", "off_step"}
    for t, v in tr["a_ref"].items():
        assert v == pytest.approx(max(tr["responses"][s][t] for s in tr["responses"]))
    assert eyes.unresponsive == ("Tm4",)


def test_eyes_mapping(eyes, vgroups):
    assert len(eyes.fw_types) == N_TYPES
    for s in "LR":
        assert len(eyes.node[s]) == len(vgroups[f"vbnd_{s}"])
        assert eyes.t45_mask[s].sum() > 5000
    tm = eyes.fw_types.index("Tm4")
    for s in "LR":
        assert np.isinf(eyes.aref[s][eyes.tcode[s] == tm]).all()


def _uniform(level, n=8):
    from flygym.vision import Retina
    hx = Retina().raw_image_to_hex_pxls(np.full((512, 450, 3), int(level * 255), np.uint8))
    return [np.stack([hx, hx])] * n


def test_rates_grey_on_off(eyes):
    eyes.reset()
    a, _ = eyes.step(_uniform(0.5, 2))
    r = eyes.rates(a)
    assert max(r["L"].max(), r["R"].max()) < 1.0            # grey steady state -> ~0 Hz
    assert eyes.display.dtype == np.float16 and eyes.display.shape == (2, len(eyes.display_nodes))
    for level, typ in ((0.8, "R7"), (0.2, "Tm1")):
        eyes.reset()
        for _ in range(10):                                  # 250 ms
            a, _ = eyes.step(_uniform(level, 2))
        r = eyes.rates(a)
        k = eyes.fw_types.index(typ)
        assert r["L"][eyes.tcode["L"] == k].mean() > 5.0, typ
        assert r["L"].max() <= 150.0 and np.isfinite(r["L"]).all()
        assert (r["L"][eyes.tcode["L"] == eyes.fw_types.index("Tm4")] == 0).all()
    v, tm = eyes.t45_view(r)
    assert tm.shape == (2, 8) and len(v["L"]) == eyes.t45_mask["L"].sum()
    assert eyes.type_means(r).shape == (2, N_TYPES)
    eyes.reset()


def test_display_stream_then_write_h5_append(eyes, tmp_path):
    p = tmp_path / "x_data.h5"
    w = VB.DisplayWriter(p, eyes)
    for k in (-2, -1, 0):
        w.add(k, np.zeros((2, len(eyes.display_nodes)), np.float16))
    w.close()
    with h5py.File(p, "a") as f:
        f.create_group("meta")
    with h5py.File(p, "r") as f:
        assert f["flyvis/activity"].shape == (3, 2, len(eyes.display_nodes))
        assert list(f["flyvis/step_idx"][:]) == [-2, -1, 0]
        assert set(np.char.decode(f["flyvis/node_type"][:]).tolist()) == set(eyes.display_types)
        assert len(f["flyvis/flywire_map/idx"]) > 10000
        assert "meta" in f


def test_cli_and_name():
    from fly_flight_brain_body_simulation import parse_args
    from flight.recorder import output_stem
    assert parse_args([]).vision_boundary is False
    assert parse_args(["--vision-boundary"]).vision_boundary is True
    assert output_stem(3, hybrid=True, vision_boundary=True) == "flight_v3_hybrid_sB"
    assert output_stem(3, hybrid=True) == "flight_v3_hybrid"
