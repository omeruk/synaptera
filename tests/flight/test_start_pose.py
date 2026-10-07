"""--start-offset / --start-yaw (SPEC_SENSORY_INPUTS §3.3f): defaults leave runs unchanged; the pedestal,
the odor-field obstacle and the spawn move together."""
import os

os.environ.setdefault("MUJOCO_GL", "egl")

import numpy as np
import pytest

from flight import config as cfg
from flight.recorder import output_stem

import fly_flight_brain_body_simulation as sim


@pytest.fixture
def restore_pedestal(monkeypatch):
    monkeypatch.setattr(cfg, "TAKEOFF_PEDESTAL", cfg.TAKEOFF_PEDESTAL)
    monkeypatch.setattr(cfg, "START_POS", cfg.START_POS.copy())


def test_defaults_unchanged():
    a = sim.parse_args(["--hybrid"])
    assert a.start_offset == [0.0, 0.0] and a.start_yaw == 0.0
    assert output_stem(44, hybrid=True, start_offset=a.start_offset, start_yaw=a.start_yaw) == "flight_v44_hybrid"


def test_output_name():
    assert output_stem(1, hybrid=True, start_offset=[40, 0], tag="b1") == "flight_v1_hybrid_start+40_+0_b1"
    assert output_stem(1, hybrid=True, start_yaw=-60, tag="b8") == "flight_v1_hybrid_startYaw-60_b8"


def test_excludes_other_spawns():
    with pytest.raises(SystemExit):
        sim.parse_args(["--start-yaw", "30", "--start-on-platform"])
    with pytest.raises(SystemExit):
        sim.parse_args(["--start-offset", "0", "40", "--spawn-air", "0", "0", "100", "0"])


def test_move_pedestal(restore_pedestal):
    x, y, r, zt = cfg.TAKEOFF_PEDESTAL
    assert cfg.move_takeoff_pedestal(-40, 40) == (x - 40, y + 40, r, zt)
    np.testing.assert_allclose(cfg.START_POS, [x - 40, y + 40, 20.0])
    with pytest.raises(ValueError, match="tower"):
        cfg.move_takeoff_pedestal(220, 0)       # into tower 1 (x 160-200)
    with pytest.raises(ValueError, match="odor grid"):
        cfg.move_takeoff_pedestal(-1000, 0)


def test_odor_field_obstacle_moves(restore_pedestal):
    from simulation_data.odor_field_3d import build_arena_odor_field
    cfg.move_takeoff_pedestal(40, 0)
    f = build_arena_odor_field(cfg)
    cx, cy, _, zt = cfg.TAKEOFF_PEDESTAL
    assert f.inside_solid(np.array([[cx, cy, zt / 2]]))[0]          # inside the moved pedestal
    assert not f.inside_solid(np.array([[0.0, 0.0, zt / 2]]))[0]    # the old place is free


def test_body_spawn(restore_pedestal):
    from flight.body import FlightBody
    cfg.move_takeoff_pedestal(0, -40)
    body = FlightBody(spawn_yaw=np.radians(60))
    s = body.state()
    assert s["pos"][0] == pytest.approx(0.0, abs=0.5) and s["pos"][1] == pytest.approx(-40.0, abs=0.5)
    assert np.degrees(s["heading"]) == pytest.approx(60.0, abs=1.0)
    import mujoco
    g = mujoco.mj_name2id(body.m, mujoco.mjtObj.mjOBJ_GEOM, "pedestal")
    if g < 0:                                     # MJCF attach may prefix arena names
        g = next(i for i in range(body.m.ngeom) if (body.m.geom(i).name or "").endswith("pedestal"))
    np.testing.assert_allclose(body.d.geom_xpos[g][:2], [0.0, -40.0], atol=1e-9)
