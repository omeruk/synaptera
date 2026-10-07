"""Stage 4: controller terms (pure functions) and phase machine."""
import numpy as np
import pytest

from flight import config as cfg
from flight import controller as ctl
from flight import quasi_steady as qs
from flight import sensors as S


def test_brain_turn_terms_carry_only_the_dn_term():
    t = ctl.turn_terms_brain(0.3, 0.3)
    assert t["turn_bias"] == 0.3 and t["turn_dn"] == 0.3
    assert t["turn_odor"] == 0.0 and t["turn_loom"] == 0.0
    aL, aR = qs.turn_to_amplitudes(t["turn_bias"], 140.0, cfg.TURN_DPHI_DEG)
    assert aL > aR                      # larger left amplitude = right turn (test_body)


def test_odor_ablation_zeroes_the_pitch_odor_term():
    p = ctl.pitch_terms(0.1, 0.0, 50.0, "cruise", ablate_odor=True)
    assert p["pitch_odor"] == 0


def test_pitch_terms():
    p = ctl.pitch_terms(0.05, 100.0, 50.0, "cruise")
    assert p["pitch_odor"] > 0 and p["pitch_alt"] == pytest.approx(-100.0 / cfg.VZ_DAMP_REF)
    assert p["pitch_ventral"] == 0
    assert ctl.pitch_terms(0.0, 0.0, 2.0, "cruise")["pitch_ventral"] > 0
    assert ctl.pitch_terms(0.0, 0.0, 2.0, "approach")["pitch_ventral"] == 0
    assert ctl.pitch_terms(0.0, 0.0, 50.0, "takeoff")["pitch_takeoff"] == cfg.TAKEOFF_LIFT


def test_wing_command_lift_fraction():
    p = qs.make_params(1.027e-3, 9810.0, np.diag([1.2e-4, 5.1e-4, 5.1e-4]), cfg)
    cmd, lift = ctl.wing_command(0.0, 0.0, 0.0, p)
    assert lift == 1.0 and cmd.amp_L == pytest.approx(cfg.PHI0_DEG)
    cmd, lift = ctl.wing_command(0.0, 0.21, 0.0, p)
    assert 2 * qs.wing_lift(cmd.amp_L, cmd.freq, p) == pytest.approx(1.21 * p.weight)
    cmd, _ = ctl.wing_command(0.0, 0.0, 0.0, p, wings_on=False)
    assert not cmd.on


def test_body_pitch_target():
    assert ctl.body_pitch_target("cruise", 300) == pytest.approx(np.radians(cfg.CRUISE_PITCH_DEG))
    assert ctl.body_pitch_target("approach", 300) == pytest.approx(-np.radians(cfg.LAND_BRAKE_PITCH_DEG))
    # at the landing speed: only the feed-forward tilt that holds it (linear drag)
    ff = np.radians(cfg.CRUISE_PITCH_DEG * cfg.LAND_SPEED / cfg.TERMINAL_SPEED_REF)
    assert ctl.body_pitch_target("approach", cfg.LAND_SPEED) == pytest.approx(ff)
    # slower than the landing speed (e.g. after braking): nose-down, keeps moving forward
    assert ctl.body_pitch_target("approach", 0.0) > ff > 0
    assert ctl.body_pitch_target("approach", -500) == pytest.approx(np.radians(cfg.CRUISE_PITCH_DEG))
    assert ctl.body_pitch_target("takeoff", 100) == 0


def test_phase_machine():
    pm = ctl.PhaseMachine(0.025)
    for _ in range(cfg.TAKEOFF_STEPS):
        pm.update(0.0, 0)
    assert pm.phase == "cruise" and pm.wings_on
    pm.update(cfg.LAND_EXPANSION_TRIG + 1, 0)
    assert pm.phase == "approach"
    pm.update(0.0, 1)
    assert pm.phase == "approach"                              # one leg is not a landing
    for _ in range(cfg.TOUCHDOWN_STEPS):
        pm.update(0.0, 3)
    assert pm.phase == "touchdown" and not pm.wings_on and pm.landed
    assert pm.update(0.0, 6) == "landed" and pm.landed and not pm.wings_on
    assert [pm.update(0.0, 6) for _ in range(5)] == ["landed"] * 5


def test_sensor_maps():
    assert S.odor_norm(1.0) == 1.0 and S.odor_norm(1e-3) == 0.0
    assert S.rate(0.0, cfg.OLF_RATE) == 20.0 and S.rate(1.0, cfg.OLF_RATE) == 150.0
    assert S.ascending_rate(np.zeros(3)) == pytest.approx(22.5)          # walking baseline
    assert S.ascending_rate(np.array([0, 0, 100.0])) == pytest.approx(150.0)
    cx, cy, _, zt = cfg.FOOD_PLATFORM
    assert S.surface_below(cx, cy) == zt and S.surface_below(-40, -140) == 0.0
    assert S.surface_below(180, 0) == cfg.TOWER1[2][1]
    e = S.ExpansionRate(0.025)
    e(np.array([cx - 100.0, cy, zt]))
    v = e(np.array([cx - 100.0 + 300 * 0.025, cy, zt]))       # 300 mm/s towards it
    assert v == pytest.approx(300.0 / 100.0, rel=0.02)         # ~ v/d (backward difference)


def test_gaze_frame_removes_pitch_and_roll_from_odor_sampling():
    """Body tilt must not leak the forward gradient into I_grad (Stage 4 v7: the
    20 deg landing brake gave I_grad = -0.19 at the food's height -> dive)."""
    from scipy.spatial.transform import Rotation
    from flight.odor_field_3d import antenna_odor, build_arena_odor_field
    field = build_arena_odor_field()
    p = cfg.FOOD_POS + np.array([-25.0, -25.0, 0.0])        # food straight ahead, same height
    yaw = np.arctan2(25.0, 25.0)
    level = S.sample_odor(field, p, Rotation.from_euler("z", yaw).as_matrix())
    for pitch in (-20, 12):                                   # nose-up brake, cruise nose-down
        for roll in (0, 10):
            R = Rotation.from_euler("ZYX", [yaw, np.radians(pitch), np.radians(roll)]).as_matrix()
            o = S.sample_odor(field, p, R)
            assert o["I_grad"] == pytest.approx(level["I_grad"], abs=1e-12)
            assert o["I_asym"] == pytest.approx(level["I_asym"], abs=1e-12)
    assert abs(level["I_grad"]) < 0.02
    R = Rotation.from_euler("ZYX", [yaw, np.radians(-20), 0]).as_matrix()
    assert abs(antenna_odor(field, p, R, cfg.ANTENNA_HALF_SEP_EFF)["I_grad"]) > 0.1  # the old artefact
