"""Stage 3: body physics (FlyGym + stroke-averaged xfrc), no brain input.

Physics runs at ~4 ms per 0.1 ms step, so this file takes ~2 minutes.
"""
import os

os.environ.setdefault("MUJOCO_GL", "egl")

import numpy as np
import pytest

from flight import config as cfg
from flight import quasi_steady as qs
from flight.body import FlightBody

OPEN_AIR = (-40.0, -140.0, 100.0)   # away from towers, pedestal and platform


def decisions(seconds):
    return int(round(seconds / (cfg.PHYSICS_STEPS_PER_DECISION * cfg.PHYSICS_DT)))


# ── pure model ──────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def params():
    I = np.diag([1.2e-4, 5.1e-4, 5.1e-4])   # measured whole-fly inertia (tuck), g*mm^2
    return qs.make_params(1.027e-3, 9810.0, I, cfg)


def test_hover_amplitude_gives_weight(params):
    a = qs.hover_amplitude(params)
    assert a == pytest.approx(cfg.PHI0_DEG)
    F, T, info = qs.aero_wrench(np.eye(3), np.zeros(3), np.zeros(3), qs.WingCommand(a, a, cfg.F0_HZ), params)
    np.testing.assert_allclose(F, [0, 0, params.weight], rtol=1e-12)
    np.testing.assert_allclose(T, 0, atol=1e-12)
    th = np.radians(12)
    assert 2 * qs.wing_lift(qs.hover_amplitude(params, th), cfg.F0_HZ, params) * np.cos(th) == pytest.approx(params.weight)


def test_turn_sign_in_wrench(params):
    aL, aR = qs.turn_to_amplitudes(1.0, cfg.PHI0_DEG, cfg.TURN_DPHI_DEG)
    assert aL > aR
    _, T, _ = qs.aero_wrench(np.eye(3), np.zeros(3), np.zeros(3), qs.WingCommand(aL, aR, cfg.F0_HZ), params)
    assert T[2] < 0      # clockwise from above = right turn
    assert T[0] > 0      # left wing lifts more -> bank right (left side up)


def test_counter_force_opposes_velocity(params):
    a = cfg.PHI0_DEG
    v = np.array([100.0, -50.0, 20.0])
    F, _, _ = qs.aero_wrench(np.eye(3), v, np.zeros(3), qs.WingCommand(a, a, cfg.F0_HZ), params)
    drag = F - np.array([0, 0, params.weight])
    np.testing.assert_allclose(drag, -params.c_F * v)


def test_desired_up():
    np.testing.assert_allclose(qs.desired_up(0.3, 0.0), [0, 0, 1])
    z = qs.desired_up(0.0, np.radians(12))          # nose-down tilts lift forward (+x)
    assert z[0] > 0 and z[1] == pytest.approx(0)
    z = qs.desired_up(0.0, 0.0, np.radians(10))     # right bank tilts lift to the right (-y)
    assert z[1] < 0


# ── MuJoCo body ─────────────────────────────────────────────────────────────
def test_hover_1s_without_brain():
    b = FlightBody(spawn_pos=OPEN_AIR, legs="tuck")
    p = b.params
    assert p.weight == pytest.approx(b.mass * 9810.0)
    a = qs.hover_amplitude(p)
    cmd = qs.WingCommand(a, a, p.f0)
    z0 = b.state()["pos"][2]
    zmax = 0.0
    for _ in range(decisions(1.0)):
        r = b.step(cmd)
        zmax = max(zmax, abs(b.state()["pos"][2] - z0))
    assert zmax < 0.5
    assert r["badqacc"] == 0


def test_tower_crash_400mm_s():
    # 12 mm in front of tower 1's face (x = 160), flying straight into it
    b = FlightBody(spawn_pos=(148.0, 30.0, 100.0), legs="tuck")
    p = b.params
    a = qs.hover_amplitude(p)
    b.set_velocity([400.0, 0.0, 0.0])
    cmd = qs.WingCommand(a, a, p.f0)
    xmax = -np.inf
    for _ in range(4):
        r = b.step(cmd)
        xmax = max(xmax, b.state()["pos"][0])
    assert b.state()["vel"][0] < 0          # it hit the wall and bounced
    assert b.max_tower_penetration > 0      # contact actually happened
    assert b.max_tower_penetration < 0.1    # mm
    assert r["badqacc"] == 0
    assert xmax < cfg.TOWER1[0][0]          # COM never inside the tower


def test_platform_touchdown_detected():
    cx, cy, _, zt = cfg.FOOD_PLATFORM
    b = FlightBody(spawn_pos=(cx, cy, zt + 1.5), legs="stand")
    off = qs.WingCommand(0, 0, 0, on=False)
    b.step(off, n_steps=500)
    c = b.contacts()
    assert c["platform_legs"].sum() >= 2
    assert not c["tower_contact"]
    assert b.state()["pos"][2] > zt       # resting on top, not fallen through


def test_terminal_speed_at_cruise_pitch():
    b = FlightBody(spawn_pos=OPEN_AIR, legs="tuck")
    p = b.params
    th = np.radians(cfg.CRUISE_PITCH_DEG)
    a = qs.hover_amplitude(p, th)
    cmd = qs.WingCommand(a, a, p.f0)
    for _ in range(decisions(1.0)):
        b.step(cmd, pitch_down=th)
    v = b.state()["vel"]
    speed = np.hypot(v[0], v[1])
    print(f"\n[terminal speed] tilt {cfg.CRUISE_PITCH_DEG} deg: {speed:.1f} mm/s, vz {v[2]:+.2f}")
    assert 200.0 <= speed <= 400.0
    assert v[0] > 0 and abs(v[2]) < 5.0


def test_positive_turn_bias_yaws_right():
    b = FlightBody(spawn_pos=OPEN_AIR, legs="tuck")
    p = b.params
    aL, aR = qs.turn_to_amplitudes(0.5, qs.hover_amplitude(p), cfg.TURN_DPHI_DEG)
    cmd = qs.WingCommand(aL, aR, p.f0)
    h0 = b.state()["heading"]
    for _ in range(decisions(0.25)):
        b.step(cmd)
    s = b.state()
    dh = np.angle(np.exp(1j * (s["heading"] - h0)))
    print(f"\n[turn] turn_bias 0.5: heading {np.degrees(dh):+.1f} deg in 0.25 s, "
          f"yaw rate {s['omega'][2]:+.2f} rad/s, bank {np.degrees(np.arcsin(s['R'][2, 1])):+.2f} deg (right +)")
    assert dh < 0 and s["omega"][2] < 0


def _tilt_deg(R):
    return float(np.degrees(np.arccos(np.clip(R[2, 2], -1.0, 1.0))))


def _gust_response(axis, haltere=True, pulse=0.05, after=0.2, chunk=50):
    """Hover, then a 50 ms body-axis torque pulse (roll: axis 0, pitch: axis 1).
    Pulse size: the reflex's static stiffness x 0.35 rad (~20 deg if held).
    Returns (peak tilt deg, tilt deg at pulse end + `after`, body rates rad/s then)."""
    b = FlightBody(spawn_pos=OPEN_AIR, legs="tuck")
    p = b.params
    a = qs.hover_amplitude(p)
    cmd = qs.WingCommand(a, a, p.f0)
    b.step(cmd, n_steps=1000)                        # 0.1 s settle
    tau_b = np.zeros(3)
    tau_b[axis] = p.kp_att[axis] * 0.35
    dt_chunk = chunk * cfg.PHYSICS_DT
    peak = 0.0
    for _ in range(int(round(pulse / dt_chunk))):
        R = b.state()["R"]
        b.step(cmd, n_steps=chunk, haltere=haltere, ext_torque=R @ tau_b)
        peak = max(peak, _tilt_deg(b.state()["R"]))
    for _ in range(int(round(after / dt_chunk))):
        b.step(cmd, n_steps=chunk, haltere=haltere)
        peak = max(peak, _tilt_deg(b.state()["R"]))
    s = b.state()
    return peak, _tilt_deg(s["R"]), s["R"].T @ s["omega"], b.badqacc_count() - b.badqacc0


@pytest.mark.parametrize("axis,name", [(0, "roll"), (1, "pitch")])
def test_haltere_recovers_gust_within_200ms(axis, name):
    peak, tilt, w_b, badq = _gust_response(axis)
    print(f"\n[gust {name}] peak tilt {peak:.1f} deg, 0.2 s after pulse {tilt:.3f} deg, "
          f"body rates {np.round(w_b, 3)} rad/s")
    assert peak > 5.0                  # the pulse really tilted the body
    assert tilt < 1.0 and tilt < 0.1 * peak
    assert np.all(np.abs(w_b[:2]) < 0.5)
    assert badq == 0


def test_without_haltere_gust_is_not_recovered():
    """Control: the recovery comes from the (HAND-MADE) haltere reflex, not the aero model."""
    peak, tilt, _, _ = _gust_response(0, haltere=False)
    print(f"\n[gust roll, no haltere] peak {peak:.1f} deg, 0.2 s after pulse {tilt:.1f} deg")
    assert tilt > 0.5 * peak


@pytest.mark.parametrize("deg", [30.0, -30.0])
def test_yaw_pulse_passive_rotation(deg):
    """--yaw-perturb (brain-control Step 2 decisions (b)): with turn 0 the 0.1 s body-z torque pulse
    turns the hovering fly by ~deg (first order: passive rotation = deg), + = left; the rate then decays."""
    b = FlightBody(spawn_pos=OPEN_AIR, legs="tuck")
    p = b.params
    a = qs.hover_amplitude(p)
    cmd = qs.WingCommand(a, a, p.f0)
    b.step(cmd, n_steps=1000)
    T = b.yaw_pulse_torque(deg, 0.1)
    h0 = b.state()["heading"]
    for _ in range(decisions(0.1)):
        b.step(cmd, ext_torque=b.state()["R"][:, 2] * T)
    for _ in range(decisions(0.15)):
        b.step(cmd)
    s = b.state()
    dh = float(np.degrees(np.angle(np.exp(1j * (s["heading"] - h0)))))
    print(f"\n[yaw pulse {deg:+.0f}] heading {dh:+.1f} deg, yaw rate {s['omega'][2]:+.3f} rad/s after 0.15 s")
    assert abs(dh - deg) < 3.0
    assert abs(s["omega"][2]) < 0.2


def test_textured_arena_and_subframe_render():
    """Step 0: obstacles drawn by visual-only checker meshes, collision primitives
    invisible but unchanged; body.step(render_at=...) returns the eye frames."""
    import mujoco
    b = FlightBody(spawn_pos=(120.0, 20.0, 100.0), legs="tuck", enable_vision=True)
    m = b.m
    for name in ("tower1", "tower2", "pedestal", "food_platform"):
        g = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, name)
        v = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"viz_tex_{name}")
        assert g >= 0 and v >= 0
        assert m.geom_rgba[g][3] == 0 and m.geom_rgba[v][3] == 1
        assert m.geom_contype[v] == 0 and m.geom_conaffinity[v] == 0
        np.testing.assert_allclose(m.geom_solref[g], [0.02, 1])
    # no contact pair involves a texture mesh
    viz = {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"viz_tex_{n}") for n in ("tower1", "food_platform")}
    assert not viz & set(m.pair_geom1) and not viz & set(m.pair_geom2)
    # the tower in front is textured: ommatidia that see the uniform tower in the
    # untextured arena (most common value) see a high-contrast pattern here
    v_tex = b.update_vision().max(axis=2)
    b0 = FlightBody(spawn_pos=(120.0, 20.0, 100.0), legs="tuck", enable_vision=True, textured=False)
    v_flat = b0.update_vision().max(axis=2)
    vals, cnt = np.unique(np.round(v_flat, 3), return_counts=True)
    tower = np.abs(v_flat - vals[cnt.argmax()]) < 2e-3
    assert tower.sum() > 200
    assert v_flat[tower].std() < 0.01 and v_tex[tower].std() > 0.1
    r = b.step(qs.WingCommand(0, 0, 0, on=False), n_steps=20, render_at=(10, 20))
    assert len(r["frames"]) == 2 and r["frames"][0].shape == (2, 721, 2)


def test_dark_platform_is_visual_only():
    """Step 2 arena design: the food platform (and droplet) is uniformly dark and seen darker
    than with the checker; contacts and solref unchanged; other obstacles keep the checker."""
    import mujoco
    b = FlightBody(spawn_pos=(440.0, -70.0, 150.0), spawn_yaw=np.pi / 2, legs="tuck", enable_vision=True,
                   platform="dark")
    m = b.m
    v = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "viz_tex_food_platform")
    g = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "food_platform")
    np.testing.assert_allclose(m.geom_rgba[v], cfg.PLATFORM_DARK_RGBA)
    assert m.geom_matid[v] == -1 and m.geom_contype[v] == 0 and m.geom_rgba[g][3] == 0
    np.testing.assert_allclose(m.geom_solref[g], [0.02, 1])
    t = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "viz_tex_tower1")
    assert m.geom_matid[t] >= 0
    dark = b.update_vision().max(axis=2)
    neutral = FlightBody(spawn_pos=(440.0, -70.0, 150.0), spawn_yaw=np.pi / 2, legs="tuck", enable_vision=True,
                         platform="neutral").update_vision().max(axis=2)
    diff = neutral - dark
    assert (diff > 0.05).sum() > 5 and (diff < -0.05).sum() == 0


def test_leg_transition_ramps_without_single_step_jump():
    """Take-off tuck and landing extension (HAND ramps): the PD joint target moves along a cosine
    ramp, so no physics step and no 25 ms decision step jumps to the new pose."""
    b = FlightBody(spawn_pos=OPEN_AIR, legs="stand")
    p = b.params
    a = qs.hover_amplitude(p)
    cmd = qs.WingCommand(a, a, p.f0)
    for legs, ramp_s, start, end in (("tuck", cfg.LEG_TUCK_RAMP_S, b.stand_pose, b.tuck_pose),
                                     ("stand", cfg.LEG_EXTEND_RAMP_S, b.tuck_pose, b.stand_pose)):
        full = np.abs(end - start).max()
        n = int(round(ramp_s / cfg.PHYSICS_DT))
        b.set_legs(legs)
        targets = [b.leg_target.copy()]
        for _ in range(n):
            b.step(cmd, n_steps=1)
            targets.append(b.leg_target.copy())
            assert np.allclose(b.d.ctrl[b._act_ids], b.leg_target)
        steps = np.abs(np.diff(targets, axis=0)).max(axis=1)
        assert full > np.radians(30)
        # cosine ramp: max slope pi/2 * full / n per physics step
        assert steps.max() <= np.pi / 2 * full / n * 1.01
        # after one decision step the target is still well short of the end pose
        frac = np.abs(targets[cfg.PHYSICS_STEPS_PER_DECISION] - start).max() / full
        assert 0.0 < frac < 0.8
        assert np.allclose(targets[-1], end) and not b.leg_ramp_active
        b.set_legs(legs)                      # same pose again: no new ramp
        assert not b.leg_ramp_active
    assert b.badqacc_count() - b.badqacc0 == 0


# ── --head-reflex (flight/head_reflex.py, SPEC_SENSORY_INPUTS §3.3d) ─────────
def test_head_joint_axes_and_no_actuators_without_flag():
    """FlyGym joint names vs measured axes: Head_roll = thorax z (yaw), Head = y (pitch), Head_yaw = x
    (roll); the eye cameras sit on the Head; without the flag the model has no neck actuators."""
    import mujoco
    from flight import head_reflex as HR
    b = FlightBody(spawn_pos=OPEN_AIR, legs="tuck")
    m, d = b.m, b.d
    R = d.xmat[b.thorax].reshape(3, 3)
    for a in HR.AXES:
        jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{b.fly.name}/{HR.JOINTS[a]}")
        ax = R.T @ d.xaxis[jid]
        assert np.argmax(np.abs(ax)) == HR.THORAX_AXIS[a] and ax[HR.THORAX_AXIS[a]] > 0.99
    for i in range(m.ncam):
        bid = m.cam_bodyid[i]
        while bid and bid != b.head_body:
            bid = m.body_parentid[bid]
        assert bid == b.head_body
    hb = FlightBody(spawn_pos=OPEN_AIR, legs="tuck", head_reflex=True)
    assert hb.m.nu == m.nu + 3 and b.head is None


def test_head_reflex_turn_stabilises_gaze_within_limits():
    """Sustained right/left turns in the air: no BADQACC; |head angle| <= 15 deg on every sub-step;
    B-H3: on most turning sub-steps the gaze yaw rate is smaller than the body yaw rate; the head
    counter-rotates (target sign opposite to the body yaw rate)."""
    from flight import head_reflex as HR
    b = FlightBody(spawn_pos=OPEN_AIR, legs="tuck", head_reflex=True)
    p = b.params
    a = qs.hover_amplitude(p)
    n_turn = n_lt = 0
    qmax = np.zeros(3)
    for turn in (0.5, -0.5):
        aL, aR = qs.turn_to_amplitudes(turn, a, cfg.TURN_DPHI_DEG)
        for k in range(decisions(0.25)):
            r = b.step(qs.WingCommand(aL, aR, p.f0))
            h = r["head"]
            n_turn += h["turn_sub"]
            n_lt += h["turn_sub_lt"]
            qmax = np.maximum(qmax, h["q_absmax"])
            if k == 4:     # turning steadily, before any reset
                assert np.sign(h["target"][0]) == -np.sign(h["body_yaw_rate"]) != 0
                assert abs(h["gaze_yaw_rate"]) < abs(h["body_yaw_rate"])
    print(f"\n[head] turning sub-steps {n_turn}, |gaze|<|body| {n_lt / n_turn:.2f}, "
          f"max |q| {np.degrees(qmax).round(1)} deg, yaw resets {b.head.n_resets}")
    assert b.badqacc_count() - b.badqacc0 == 0
    assert np.all(qmax <= HR.THETA_MAX + 1e-9)
    assert n_turn > 1000 and n_lt / n_turn > 0.5


# ── --postures (SPEC_SENSORY_INPUTS §3.3d) ──────────────────────────────────
def test_flight_pose_forelegs_forward_mid_hind_back_and_tracked_in_hover():
    """Flight pose: fore-leg tarsi in front of the middle-leg coxae, hind-leg tarsi behind the hind coxae;
    reached by the PD ramp in hover without BADQACC; no feed pose without the flag."""
    import mujoco
    b = FlightBody(spawn_pos=OPEN_AIR, legs="stand", postures=True)
    p = b.params
    a = qs.hover_amplitude(p)
    cmd = qs.WingCommand(a, a, p.f0)
    b.set_legs("tuck")
    for _ in range(decisions(0.25)):
        b.step(cmd)
    m, d = b.m, b.d
    R = d.xmat[b.thorax].reshape(3, 3)

    def x_body(name):
        return float(R[:, 0] @ (d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{b.fly.name}/{name}")]
                                - d.xpos[b.thorax]))
    for s in "LR":
        assert x_body(f"{s}FTarsus5") > x_body(f"{s}MCoxa")
        assert x_body(f"{s}HTarsus5") < x_body(f"{s}HCoxa")
    names = list(b.fly.actuated_joints)
    q = np.array([d.qpos[m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{b.fly.name}/{n}")]]
                  for n in names])
    assert np.degrees(np.abs(q - b.tuck_pose)).max() < 3.0
    assert b.badqacc_count() - b.badqacc0 == 0
    with pytest.raises(ValueError):
        FlightBody(spawn_pos=OPEN_AIR, legs="tuck").set_legs("feed")


def test_feed_pose_leans_forward_and_back_smoothly():
    """On the pedestal: stand -> feed pitches the body nose-down by 3-10 deg over the 0.3 s ramp
    (no single-step jump), feed -> stand returns within 1 deg; no BADQACC."""
    b = FlightBody(legs="stand", postures=True)
    b.set_legs("stand", adhesion=1.0)
    off = qs.WingCommand(0, 0, 0, on=False)

    def pitch():
        return float(np.degrees(np.arcsin(-b.state()["R"][2, 0])))     # + = nose down
    for _ in range(8):
        b.step(off)
    p0 = pitch()
    b.set_legs("feed")
    assert b._ramp[3] == int(round(cfg.LEG_FEED_RAMP_S / cfg.PHYSICS_DT))
    for _ in range(decisions(0.5)):
        b.step(off)
    p1 = pitch()
    b.set_legs("stand")
    for _ in range(decisions(0.5)):
        b.step(off)
    p2 = pitch()
    print(f"\n[feed pose] pitch stand {p0:+.2f} -> feed {p1:+.2f} -> stand {p2:+.2f} deg (nose-down +)")
    assert 3.0 <= p1 - p0 <= 10.0 and abs(p2 - p0) < 1.0
    assert b.badqacc_count() - b.badqacc0 == 0
