"""Geometry test of condition 11 (receding-front) of SPEC_SENSORY_INPUTS §3.5b. No neural data, no FlyVis."""
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


def test_recede_front_is_time_reversal_of_loom_front(rays):
    for t0 in (0.0, 0.05, 0.124, 0.3, 0.7, 0.95, 1.0):
        assert abs(S.size_at(11, t0) - S.size_at(6, 1.0 - t0)) < 1e-9
        assert np.array_equal(S.luminance(11, t0, rays), S.luminance(6, 1.0 - t0, rays))


def test_recede_front_sizes_and_centre(rays):
    assert abs(S.size_at(11, 0.0) - 90.0) < 1e-6 and abs(S.size_at(11, 0.1) - 90.0) < 1e-6
    assert abs(S.size_at(11, 0.3) - float(S.loom_size(0.7))) < 1e-9 and abs(S.size_at(11, 0.3) - 21.0) < 0.1
    c = np.array([1.0, 0.0, 0.0])
    dark = S.luminance(11, 0.0, rays) < 0.3
    assert dark.any() and (rays[dark] @ c).min() > np.cos(np.radians(45)) - 1e-9


def test_windows_are_mirror_images():
    # W_rec = steps 24-31 (100-300 ms) shows the frames of W_loom (700-900 ms) in reverse order
    for k in range(24, 32):
        for j in range(2):
            t = ((k - 20) * 2 + j + 1) * 0.0125
            assert 0.1 - 1e-9 <= t <= 0.3 + 1e-9
            assert 0.7 - 1e-9 <= 1.0 - t <= 0.9 + 1e-9
            assert abs(S.size_at(11, t) - S.size_at(6, 1.0 - t)) < 1e-9
