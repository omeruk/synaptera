"""Geometry unit test of the body-frame visual stimuli (SPEC_SENSORY_INPUTS §3.5). No neural data, no FlyVis."""
import os

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
import pytest

from flight import vis_stim as S


@pytest.fixture(scope="module")
def rays():
    from flight.body import FlightBody
    b = FlightBody(spawn_pos=(0, 0, 100), spawn_yaw=0.0, legs="tuck", enable_vision=True)
    mujoco.mj_forward(b.m, b.d)
    return S.camera_rays(b.m, b.d, b.root)


def test_eye_axes(rays):
    az = S.azimuth(rays)
    assert 30 < az[0, S.H_PX // 2, S.W_PX // 2] < 90
    assert -90 < az[1, S.H_PX // 2, S.W_PX // 2] < -30


def test_grating_matches_formula(rays):
    lum = S.luminance(1, 0.1, rays)
    az = S.azimuth(rays)
    ref = 0.5 + 0.4 * np.sin(2 * np.pi * (az / 30.0 + 2.0 * 0.1))
    assert np.allclose(lum, ref)
    ccw = S.luminance(2, 0.1, rays)
    assert np.allclose(ccw, 0.5 + 0.4 * np.sin(2 * np.pi * (az / 30.0 - 2.0 * 0.1)))
    assert np.allclose(S.luminance(3, 0.7, rays), 0.5 + 0.4 * np.sin(2 * np.pi * az / 30.0))


def test_loom_size():
    assert abs(float(S.loom_size(0.0)) - 5.0) < 1e-6
    assert abs(float(S.loom_size(S.LOOM_T90)) - 90.0) < 1e-6 and abs(S.LOOM_T90 - 0.876) < 1e-3
    t = np.linspace(0, 1, 201)
    assert np.all(np.diff(S.loom_size(t)) >= -1e-9)
    for t0 in (0.0, 0.3, 0.8, 0.95, 1.0):
        assert abs(S.size_at(7, t0) - S.size_at(4, 1.0 - t0)) < 1e-9
        assert abs(S.size_at(8, t0) - S.size_at(5, 1.0 - t0)) < 1e-9


def test_disc_centres(rays):
    for cond, centre in ((4, 60.0), (5, -60.0), (6, 0.0)):
        c = np.array([np.cos(np.radians(centre)), np.sin(np.radians(centre)), 0.0])
        dark = S.luminance(cond, 1.0, rays) < 0.3         # 90 deg disc: every dark ray within 45 deg of the centre
        assert dark.any()
        assert (rays[dark] @ c).min() > np.cos(np.radians(45)) - 1e-9


def test_grey_and_flow(rays):
    assert np.allclose(S.luminance(10, 0.3, rays), 0.5)
    assert np.allclose(S.luminance(1, None, rays), 0.5)
    lum = S.luminance(9, 0.2, rays)
    assert np.isfinite(lum).all() and lum.min() >= 0.1 - 1e-9 and lum.max() <= 0.9 + 1e-9
