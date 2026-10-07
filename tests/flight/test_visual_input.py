"""brain-control Step 0: FlyVis -> FlyWire T4/T5 visual input.

Column alignment from both connectomes, eye convention (synthetic gratings and a
rendered yaw rotation), transduction constants, direction selectivity of the
resulting per-neuron rates. ~1-2 minutes (FlyVis, one FlyGym body, parquet read).
"""
import os

os.environ.setdefault("MUJOCO_GL", "egl")

import numpy as np
import pytest

from flight import groups as G
from flight import visual_input as V

TYPES = list(G.T45_TYPES)


@pytest.fixture(scope="module")
def groups():
    return G.build_groups(G.load_root_ids())


@pytest.fixture(scope="module")
def eyes(groups):
    return V.FlyVisEyes({"L": groups["t45_L"], "R": groups["t45_R"]}, verbose=False)


def test_lattice_op_maps_neighbours_to_neighbours():
    # FlyWire neighbours +-(1,0), +-(0,1), +-(1,1) -> FlyVis axial neighbours
    p = np.array([1, -1, 0, 0, 1, -1])
    q = np.array([0, 0, 1, -1, 1, -1])
    u, v, d = V.map_columns(p, q)
    assert np.allclose(d, 0)
    assert set(zip(u, v)) == {(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)}
    u, v, d = V.map_columns(np.array([0]), np.array([0]))
    assert (u[0], v[0], d[0]) == (0, 0, 0)


def test_alignment_from_connectomes(eyes):
    """Best point-group op = rotation 60 deg, no reflection, in both hemispheres;
    the Mi4/Mi9 (T4) and Tm9 (T5) offset vectors agree in direction."""
    res, vecs = V.fit_alignment(flyvis_edges=eyes.net.connectome.edges)
    for h in ("left", "right"):
        (s0, rot, refl), (s1, _, _) = res[h][0], res[h][1]
        assert (rot, refl) == (V.ALIGN_ROT, V.ALIGN_REFLECT)
        assert s0 > 1.5 * s1
        for t in ("T4a", "T4b", "T4c", "T4d"):
            for src in ("Mi4", "Mi9"):
                a, b = vecs[h][(t, src)]
                assert a @ b / np.linalg.norm(a) / np.linalg.norm(b) > 0.8, (h, t, src)
        for t in ("T5a", "T5b", "T5c", "T5d"):
            a, b = vecs[h][(t, "Tm9")]
            assert a @ b / np.linalg.norm(a) / np.linalg.norm(b) > 0.8, (h, t)


def test_every_t45_neuron_has_a_flyvis_node(eyes, groups):
    for s in "LR":
        assert len(eyes.node[s]) == len(groups[f"t45_{s}"])
        assert eyes.n_outside[s] < 0.1 * len(eyes.node[s])     # edge columns beyond radius 15


def _grating_rates(eyes, dir_L, dir_R, n_steps=40, skip=10):
    """Raw FlyGym frames: eye L image moving along dir_L, eye R along dir_R
    (x right, y down), VIS_SUBFRAMES frames per decision step. Mean per-neuron
    rate (Hz) per eye x subtype (2, 8)."""
    n = n_steps * V.VIS_SUBFRAMES
    gL = list(V.grating_frames(dir_L, n))
    gR = list(V.grating_frames(dir_R, n))
    eyes.reset()
    out = []
    for k in range(n_steps):
        fr = [np.stack([gL[i][0], gR[i][1]]) for i in range(k * V.VIS_SUBFRAMES, (k + 1) * V.VIS_SUBFRAMES)]
        a, _ = eyes.step(fr)
        if k >= skip:
            out.append(eyes.type_means(eyes.rates(a)))
    return np.mean(out, 0)


@pytest.fixture(scope="module")
def grating_rates(eyes):
    """World front-to-back = leftward in the FlyGym left-eye image (anterior right),
    rightward in the right-eye image (anterior left); upward = up in both."""
    return dict(ftb=_grating_rates(eyes, (-1, 0), (1, 0)), btf=_grating_rates(eyes, (1, 0), (-1, 0)),
                up=_grating_rates(eyes, (0, -1), (0, -1)), down=_grating_rates(eyes, (0, 1), (0, 1)))


def test_eye_convention_synthetic(grating_rates):
    """After the right-eye flip the same world direction drives the same subtype in
    both eyes: front-to-back T4a, back-to-front T4b, upward T4c (each > 2x the
    opposite direction), and the two eyes agree within 10 %.
    Known limitation of FlyVis flow/0000/000 (recorded, not fixed): T4d is not
    direction selective (down ~ up) and T5 selectivity is weak (T5b reversed)."""
    g = grating_rates
    i = {t: TYPES.index(t) for t in TYPES}
    for e in (0, 1):
        assert g["ftb"][e, i["T4a"]] > 2 * g["btf"][e, i["T4a"]]
        assert g["btf"][e, i["T4b"]] > 2 * g["ftb"][e, i["T4b"]]
        assert g["up"][e, i["T4c"]] > 2 * g["down"][e, i["T4c"]]
    for k in g:
        np.testing.assert_allclose(g[k][0], g[k][1], rtol=0.1, atol=2.0)


def test_rates_scale(eyes, grating_rates):
    """Grey -> ~0 Hz; the standard grating in a subtype's preferred direction gives
    ~R_MAX to T4a-c (a_ref is defined on that stimulus)."""
    eyes.reset()
    grey = np.full((2, 721, 2), 0.5, np.float32)
    a, _ = eyes.step([grey] * V.VIS_SUBFRAMES)
    r = eyes.rates(a)
    assert max(r["L"].mean(), r["R"].mean()) < 1.0
    g = grating_rates
    for t, k in (("T4a", "ftb"), ("T4b", "btf"), ("T4c", "up")):
        assert g[k][:, TYPES.index(t)] == pytest.approx(V.R_MAX, rel=0.2)


def test_eye_convention_rendered_yaw(eyes):
    """Rendered textured arena, body yawed right (clockwise from above): the left eye
    sees front-to-back motion (T4a), the right eye back-to-front (T4b)."""
    import mujoco
    from scipy.spatial.transform import Rotation as Rot
    from flight.body import FlightBody
    b = FlightBody(spawn_pos=(60, -60, 60), legs="tuck", enable_vision=True)
    adr = b.m.jnt_qposadr[b.m.body_jntadr[b.root]]
    q0 = b.d.qpos[adr + 3:adr + 7].copy()
    w = np.radians(90)                     # deg/s -> 1.1 deg per 12.5 ms frame

    def run(sign):
        eyes.reset()
        acc = []
        for k in range(40):
            R = Rot.from_rotvec([0, 0, sign * w * V.FLYVIS_DT * k]) * Rot.from_quat(q0[[1, 2, 3, 0]])
            b.d.qpos[adr + 3:adr + 7] = R.as_quat()[[3, 0, 1, 2]]
            mujoco.mj_forward(b.m, b.d)
            a, _ = eyes.step([b.update_vision().copy()])
            if k >= 10:
                acc.append([[a[s][eyes.type_code[s] == j].mean() for j in range(8)] for s in "LR"])
        return np.mean(acc, 0)

    d = run(-1) - run(+1)                  # yaw right minus yaw left
    a, bb = TYPES.index("T4a"), TYPES.index("T4b")
    assert d[0, a] > 0 and d[0, bb] < 0    # left eye: front-to-back
    assert d[1, bb] > 0 and d[1, bb] > 2 * d[1, a]   # right eye: back-to-front (scene is not uniform)


def test_transduction_constants_reproducible(eyes):
    d = V.calibrate_transduction(eyes)
    ref = V.load_transduction()
    for t in TYPES:
        np.testing.assert_allclose(d["a0"][t], ref["a0"][t], rtol=1e-4, atol=1e-6)
        assert d["a_ref"][t] == pytest.approx(ref["a_ref"][t], rel=1e-4, abs=1e-6), t
    assert ref["r_max"] == V.R_MAX and ref["dt"] == pytest.approx(V.FLYVIS_DT)
