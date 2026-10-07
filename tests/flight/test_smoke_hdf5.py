"""Stage 4: closed-loop smoke (DEV subnet, 3 steps) -> HDF5 schema and shapes.

Builds the DEV subnet (~10 s) and FlyVis; about 30-40 s in total.
"""
import os

os.environ.setdefault("MUJOCO_GL", "egl")

import h5py
import numpy as np
import pytest

from flight import config as cfg
from flight.recorder import BEHAVIOR_FIELDS

N = 3


@pytest.fixture(scope="module")
def h5file(tmp_path_factory):
    import fly_flight_brain_body_simulation as sim
    d = tmp_path_factory.mktemp("sim")
    out = sim.main(["--n-steps", str(N), "--dev-subnet", "--no-video", "--sim-dir", str(d), "--version", "0"])
    return out


def test_name_marks_dev(h5file):
    assert h5file.name == "flight_v0_DEV_data.h5"


def test_schema_and_shapes(h5file):
    with h5py.File(h5file, "r") as f:
        assert set(f.keys()) >= {"meta", "behavior", "spikes", "positions", "odor_field_3d", "render"}
        m = f["meta"].attrs
        for k in ("n_steps", "decision_interval", "brain_dt", "physics_dt", "scale", "play_speed", "fps",
                  "flags", "seed", "git_hash", "timestamp", "geometry", "lif_params", "group_counts",
                  "peak_rss_gb", "step_time_mean", "dn_baseline"):
            assert k in m, k
        assert m["n_steps"] == N and bool(m["dev_subnet"])
        assert m["decision_interval"] == pytest.approx(0.025) and m["brain_dt"] == pytest.approx(1e-4)
        b = f["behavior"]
        assert set(b.keys()) == set(BEHAVIOR_FIELDS)
        for k, (shp, _) in BEHAVIOR_FIELDS.items():
            assert b[k].shape == (N,) + shp, k
        np.testing.assert_allclose(b["t"][:], 0.025 * np.arange(1, N + 1), atol=1e-9)
        assert np.all(b["phase"][:] == cfg.PHASE_CODE["takeoff"])
        np.testing.assert_allclose(b["turn_bias"][:], b["turn_odor"][:] + b["turn_dn"][:] + b["turn_loom"][:],
                                   atol=1e-12)
        assert np.all(b["dng02_L"][:] >= 0) and np.all(b["all_dn_L"][:] > 0)
        t, i = f["spikes/all/t"][:], f["spikes/all/i"][:]
        assert t.dtype == np.float32 and i.dtype == np.int32 and len(t) == len(i) > 0
        assert i.max() < 138_639                          # global indices even on the DEV subnet
        assert len(f["spikes/groups/dng02_L"]) + len(f["spikes/groups/dng02_R"]) == 25
        p = f["positions"]
        assert len(p["x"]) == len(p["z"]) == len(p["idx"]) > 100_000
        assert f["odor_field_3d/conc"].shape == f["odor_field_3d/blocked"].shape
        r = f["render"]
        # 0.25x real time at 30 fps -> 3 frames per 25 ms decision
        assert r["qpos"].shape[0] == len(r["t"]) == 3 * N
        assert np.all(np.diff(r["t"][:]) > 0)
        # per-step sparse spike counts of every neuron = the full spike list; qvel for replay
        sp = f["spikes"]
        assert int(sp["count"][:].sum()) == len(t)
        assert sp["step_idx"][:].max() == N - 1 and sp["neuron_idx"][:].max() < 138_639
        assert r["qvel"].shape[0] == r["qpos"].shape[0]


def test_video_frames_are_1920x1280(h5file, tmp_path):
    """Stage 5: qpos replay video from the smoke HDF5; HDF5 written before the mp4."""
    import imageio
    import render_flight_video as rv
    out = rv.main([str(h5file), "--max-frames", "6", "--out", str(tmp_path / "v.mp4")])
    rd = imageio.get_reader(str(out), format="ffmpeg")
    shapes = [fr.shape for _, fr in zip(range(20), rd)]
    rd.close()
    assert len(shapes) == 6 and set(shapes) == {(1280, 1920, 3)}
    assert os.path.getmtime(h5file) < os.path.getmtime(out)


def test_thirteen_plots(h5file, tmp_path):
    import generate_flight_plots as gp
    out = gp.main([str(h5file), "--out", str(tmp_path / "plots")])
    names = sorted(p.name for p in out.glob("*.png"))
    assert len(names) == 13 and names[0].startswith("01_") and names[-1].startswith("13_")
