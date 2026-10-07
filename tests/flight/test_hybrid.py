"""--hybrid (flight/hybrid.py): HAND terms, phases, term bookkeeping, sparse spike counts."""
import os

os.environ.setdefault("MUJOCO_GL", "egl")

import h5py
import numpy as np
import pytest

from flight import config as cfg
from flight import hybrid as H
from flight import quasi_steady as qs
from flight.recorder import SparseSpikeCounts, output_stem

TOP = cfg.FOOD_PLATFORM[3]
CX, CY = cfg.FOOD_PLATFORM[:2]


def test_odor_turn_only_in_takeoff_and_cruise():
    assert H.turn_hand(0.05, "cruise") == pytest.approx(cfg.ODOR_TURN_K * np.tanh(cfg.ODOR_TURN_GAIN * 0.05))
    for ph in ("approach", "descend", "touchdown", "landed"):
        assert H.turn_hand(0.05, ph) == 0.0
    assert H.turn_hand(0.05, "cruise", ablate_odor=True) == 0.0


def test_altitude_hand_terms():
    # cruise below the floor: climb assist, never a brake
    th = H.thrust_hand("cruise", 50.0, 0.0, I_grad=0.0)
    assert th["alt"] > 0 and th["odor"] == 0
    assert H.thrust_hand("cruise", 190.0, 100.0)["alt"] == 0.0         # above the floor, climbing: no brake
    # approach: target platform top + clearance, both directions
    assert H.thrust_hand("approach", TOP + H.APPROACH_CLEAR + 10, 0.0)["alt"] < 0
    assert H.thrust_hand("approach", TOP + H.APPROACH_CLEAR - 10, 0.0)["alt"] > 0
    assert H.thrust_hand("approach", TOP + H.APPROACH_CLEAR, 0.0, I_grad=0.5)["total"] == pytest.approx(0.0)
    # descend: sink at LAND_VZ
    assert H.thrust_hand("descend", 180.0, -H.LAND_VZ)["total"] == pytest.approx(0.0)
    assert H.thrust_hand("takeoff", 20.0, 0.0)["boost"] == cfg.TAKEOFF_LIFT


def test_approach_tilt_points_at_the_platform_in_the_world_frame():
    for heading in (0.0, 1.0, -2.5):
        pos = np.array([CX - 50.0, CY, 177.0])                         # platform due +x
        pd, rr, v = H.tilt_hand("approach", pos, np.zeros(3), heading)
        h = np.array([np.cos(heading), np.sin(heading)])
        r = np.array([np.sin(heading), -np.cos(heading)])
        tilt = pd * h + rr * r
        assert tilt[0] > 0 and abs(tilt[1]) < 1e-9                    # towards +x whatever the heading
        assert np.hypot(pd, rr) <= np.radians(H.TILT_MAX_DEG) + 1e-12
        assert v == pytest.approx(min(cfg.TERMINAL_SPEED_REF, H.V_GAIN * 50.0))
    # fast towards the platform and close: brake (tilt backwards)
    pd, rr, _ = H.tilt_hand("approach", np.array([CX - 5.0, CY, 177.0]), np.array([200.0, 0, 0]), 0.0)
    assert pd < 0
    assert H.tilt_hand("cruise", np.zeros(3), np.zeros(3), 0.0)[0] == pytest.approx(np.radians(cfg.CRUISE_PITCH_DEG))


def test_phase_sequence():
    pm = H.HybridPhases()
    far = np.array([0.0, 0.0, 50.0])
    for _ in range(cfg.TAKEOFF_STEPS):
        pm.update(far, np.zeros(3), 0)
    assert pm.phase == "cruise" and pm.wings_on and not pm.legs_extended
    pm.update(np.array([CX - 50, CY, 177.0]), np.zeros(3), 0)
    assert pm.phase == "approach" and pm.legs_extended
    pm.update(np.array([CX - 2, CY, 177.0]), np.array([100.0, 0, 0]), 0)
    assert pm.phase == "approach"                                      # too fast to descend
    pm.update(np.array([CX - 2, CY, 177.0]), np.array([10.0, 0, 0]), 0)
    assert pm.phase == "descend" and pm.wings_on
    for _ in range(cfg.TOUCHDOWN_STEPS):
        pm.update(np.array([CX, CY, 170.5]), np.zeros(3), cfg.TOUCHDOWN_LEGS)
    assert pm.phase == "touchdown" and pm.landed and not pm.wings_on
    pm.update(np.array([CX, CY, 170.5]), np.zeros(3), 6)
    assert pm.phase == "landed" and "descend" in cfg.PHASE_CODE


def test_turn_total_clipped_sum_and_reflex_inverse():
    assert H.combine_turn(0.3, -0.5, 0.1) == pytest.approx(-0.1)
    assert H.combine_turn(2.0, 2.0, 0.0) == cfg.TURN_BIAS_MAX
    p = qs.make_params(1e-3, 9810.0, np.diag([1e-4, 1e-4, 1e-4]), cfg)
    turn = 0.7
    aL, aR = qs.turn_to_amplitudes(turn, 140.0, cfg.TURN_DPHI_DEG)
    _, tq, _ = qs.aero_wrench(np.eye(3), np.zeros(3), np.zeros(3), qs.WingCommand(aL, aR, p.f0), p)
    assert qs.yaw_torque_to_turn(tq[2], p, cfg.TURN_DPHI_DEG) == pytest.approx(turn)


def test_sparse_spike_counts():
    sc = SparseSpikeCounts(local_to_global=np.array([5, 7, 9]))
    sc.add(-2, np.array([0, 3, 0]))
    sc.add(0, np.array([1, 0, 2]))
    s, i, c = sc.arrays()
    assert s.tolist() == [-2, 0, 0] and i.tolist() == [7, 5, 9] and c.tolist() == [3, 1, 2]
    assert s.dtype == np.int32 and i.dtype == np.int32 and c.dtype == np.uint8


def test_name_and_flags():
    import fly_flight_brain_body_simulation as sim
    assert output_stem(3, hybrid=True, ablate_dn=["DNp15"]) == "flight_v3_hybrid_ablDN-DNp15"
    assert sim.parse_args(["--hybrid", "--ablate-dn", "DNp15"]).ablate_dn == ["DNp15"]
    a = sim.parse_args(["--hybrid", "--no-olfaction"])
    assert a.no_olfaction and not a.ablate_odor          # brain input off, HAND odor navigation on


@pytest.fixture(scope="module")
def h5hyb(tmp_path_factory):
    import fly_flight_brain_body_simulation as sim
    d = tmp_path_factory.mktemp("hyb")
    return sim.main(["--hybrid", "--n-steps", "3", "--dev-subnet", "--no-video", "--sim-dir", str(d),
                     "--version", "0"])


def test_hybrid_smoke_hdf5(h5hyb):
    assert h5hyb.name == "flight_v0_DEV_hybrid_data.h5"
    with h5py.File(h5hyb, "r") as f:
        b = f["behavior"]
        tot = np.clip(b["turn_brain"][:] + b["turn_hand"][:] + b["turn_flyvis"][:], -cfg.TURN_BIAS_MAX,
                      cfg.TURN_BIAS_MAX)
        np.testing.assert_allclose(b["turn_total"][:], tot, atol=1e-12)
        np.testing.assert_allclose(b["turn_bias"][:], b["turn_total"][:])
        assert np.all(b["wings_on"][:] == 1) and np.all(np.isfinite(b["turn_reflex"][:]))
        s = f["spikes"]
        assert int(s["count"][:].sum()) == len(s["all/t"])              # sparse counts = every spike
        n_pre = cfg.CALIB_STEPS + cfg.PERSIST_CUT_STEPS
        assert s["step_idx"][:].min() == -n_pre and s["step_idx"][:].max() == 2
        assert f["render/qvel"].shape[0] == f["render/qpos"].shape[0]
        m = f["meta"].attrs
        assert '"hybrid": true' in m["flags"] and "brain_over_total" in m["hybrid"]


def test_no_brain_steer_name_and_flags():
    import fly_flight_brain_body_simulation as sim
    assert output_stem(4, hybrid=True, vision_boundary=True, no_brain_steer=True) == "flight_v4_hybrid_sB_noBrSteer"
    assert sim.parse_args(["--hybrid", "--no-brain-steer"]).no_brain_steer


@pytest.fixture(scope="module")
def h5nbs(tmp_path_factory):
    import fly_flight_brain_body_simulation as sim
    d = tmp_path_factory.mktemp("nbs")
    return sim.main(["--hybrid", "--no-brain-steer", "--head-reflex", "--postures", "--n-steps", "3", "--dev-subnet", "--no-video",
                     "--sim-dir", str(d), "--version", "0"])


def test_no_brain_steer_term_is_exactly_zero(h5nbs):
    """--no-brain-steer: turn_brain is 0 (not the perch-baseline constant); the readout is recorded."""
    assert h5nbs.name == "flight_v0_DEV_hybrid_noBrSteer_head_pose_data.h5"
    with h5py.File(h5nbs, "r") as f:
        b = f["behavior"]
        assert np.all(b["turn_brain"][:] == 0.0) and np.all(b["turn_dn"][:] == 0.0)
        assert np.all(np.isfinite(b["steer_norm"][:]))
        tot = np.clip(b["turn_hand"][:] + b["turn_flyvis"][:], -cfg.TURN_BIAS_MAX, cfg.TURN_BIAS_MAX)
        np.testing.assert_allclose(b["turn_total"][:], tot, atol=1e-12)
        assert '"no_brain_steer": true' in f["meta"].attrs["flags"]


def test_head_reflex_recorded(h5nbs):
    from flight import head_reflex as HR
    with h5py.File(h5nbs, "r") as f:
        b = f["behavior"]
        assert b["head_q"].shape == (3, 3) and np.all(np.abs(b["head_q_absmax"][:]) <= HR.THETA_MAX + 1e-9)
        assert np.all(b["head_turn_sub_lt"][:] <= b["head_turn_sub"][:])
        assert '"kp": 190.0' in f["meta"].attrs["head_reflex"]
        assert '"postures": true' in f["meta"].attrs["flags"] and "flight_pose_offsets_deg" in f["meta"].attrs["postures"]
        lp = b["leg_pose"][:]
        assert set(lp.tolist()) <= {0, 1}       # pedestal / take-off: stand or flight pose, never feed
