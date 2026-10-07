"""Stroke-averaged (quasi-steady) wing forces + haltere reflex. Pure numpy.

Wings are not simulated; each wing produces a stroke-averaged lift
    F_w = (W/2) * (Phi_w/Phi0)^2 * (f/f0)^2
along the body-fixed stroke-plane normal (body +z; simplification: the
stroke plane is taken parallel to the body's horizontal plane, so "hover" is a
level body). Tilting the body tilts the force, so forward speed follows from
the physics. Flapping counter-force/torque (Hedrick et al. 2009):
    FCF = -c_F * s * v,   FCT = -c_T * s * omega,   s = f*mean(Phi)/(f0*Phi0)
Torques from the wings (body frame):
    roll = (F_L - F_R) * arm_lat            (physically coupled to the yaw command)
    yaw  = -k_yaw * (Phi_L - Phi_R)/Phi0    (larger left amplitude -> turn right)
Haltere reflex (HAND-MADE, VNC stand-in): roll/pitch attitude PD towards a
desired body "up" vector + yaw-rate damping.

Frames: world z up; body x forward, y left, z up (FlyGym/MuJoCo).
Units: mm, s, g -> force in uN (g*mm/s^2), torque in uN*mm.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class WingCommand:
    amp_L: float    # deg
    amp_R: float    # deg
    freq: float     # Hz
    on: bool = True  # False: wings folded, no aerodynamic force/torque


@dataclass
class FlightParams:
    weight: float        # uN (m*g)
    phi0: float          # deg
    f0: float            # Hz
    c_F: float           # uN*s/mm   translational counter-force coefficient
    c_T: float           # uN*mm*s   rotational counter-torque coefficient
    arm_lat: float       # mm
    k_yaw: float         # uN*mm per unit (Phi_L-Phi_R)/Phi0
    kp_att: np.ndarray   # (2,) roll, pitch attitude gains  uN*mm/rad
    kd_att: np.ndarray   # (2,) roll, pitch rate gains      uN*mm*s
    kd_yaw: float        # yaw-rate gain (haltere)          uN*mm*s


def make_params(mass, gravity, inertia_body, cfg):
    """Derive coefficients from the body (mass g, |g| mm/s^2, 3x3 inertia about COM
    in body axes, g*mm^2) and flight/config.py targets."""
    W = mass * gravity
    theta = np.radians(cfg.CRUISE_PITCH_DEG)
    # terminal speed at the cruise tilt with lift = W/cos(theta):
    # W*tan(theta) = c_F * s * v,   s = 1/sqrt(cos(theta))
    s_cruise = 1.0 / np.sqrt(np.cos(theta))
    c_F = W * np.tan(theta) / (s_cruise * cfg.TERMINAL_SPEED_REF)
    Ixx, Iyy, Izz = np.diag(inertia_body)
    c_T = Izz / cfg.ROT_DAMP_TAU
    wn, z = cfg.HALTERE_OMEGA_N, cfg.HALTERE_ZETA
    kp = np.array([Ixx, Iyy]) * wn ** 2
    kd = 2 * z * np.array([Ixx, Iyy]) * wn
    d_yaw_total = Izz / cfg.HALTERE_YAW_TAU
    kd_yaw = max(d_yaw_total - c_T, 0.0)
    # steady yaw rate per unit turn: k_yaw * (2*dphi/phi0) = d_yaw_total * rate
    k_yaw = d_yaw_total * cfg.YAW_RATE_PER_TURN / (2 * cfg.TURN_DPHI_DEG / cfg.PHI0_DEG)
    return FlightParams(W, cfg.PHI0_DEG, cfg.F0_HZ, c_F, c_T, cfg.WING_ARM_LAT, k_yaw,
                        kp, kd, kd_yaw)


def wing_lift(amp, freq, p):
    return 0.5 * p.weight * (amp / p.phi0) ** 2 * (freq / p.f0) ** 2


def hover_amplitude(p, tilt_rad=0.0, freq=None):
    """Symmetric amplitude whose vertical lift component equals the weight."""
    f = p.f0 if freq is None else freq
    return p.phi0 * (p.f0 / f) / np.sqrt(np.cos(tilt_rad))


def stroke_drive(cmd, p):
    return cmd.freq * 0.5 * (cmd.amp_L + cmd.amp_R) / (p.f0 * p.phi0)


def aero_wrench(R, v, omega, cmd, p):
    """Force/torque (world frame, about the COM) from the wings.
    R: body->world 3x3; v: COM velocity (world); omega: angular velocity (world)."""
    if not cmd.on:
        return np.zeros(3), np.zeros(3), dict(F_L=0.0, F_R=0.0, s=0.0)
    F_L = wing_lift(cmd.amp_L, cmd.freq, p)
    F_R = wing_lift(cmd.amp_R, cmd.freq, p)
    s = stroke_drive(cmd, p)
    force = (F_L + F_R) * R[:, 2] - p.c_F * s * np.asarray(v)
    tau_b = np.array([(F_L - F_R) * p.arm_lat, 0.0, -p.k_yaw * (cmd.amp_L - cmd.amp_R) / p.phi0])
    torque = R @ tau_b - p.c_T * s * np.asarray(omega)
    return force, torque, dict(F_L=F_L, F_R=F_R, s=s)


def desired_up(heading, pitch_down, roll_right=0.0):
    """Desired body +z (world) for a heading (rad, yaw), nose-down tilt and right bank."""
    h = np.array([np.cos(heading), np.sin(heading), 0.0])
    r = np.array([np.sin(heading), -np.cos(heading), 0.0])
    z = (np.cos(pitch_down) * np.cos(roll_right) * np.array([0.0, 0.0, 1.0])
         + np.sin(pitch_down) * h + np.sin(roll_right) * r)
    return z / np.linalg.norm(z)


def heading_of(R):
    return float(np.arctan2(R[1, 0], R[0, 0]))


def haltere_torque(R, omega, z_des, p):
    """HAND-MADE haltere reflex: attitude PD on roll/pitch, rate damping on yaw.
    Returns world-frame torque."""
    w_b = R.T @ np.asarray(omega)
    e_b = R.T @ np.cross(R[:, 2], z_des)       # rotation needed to bring body z to z_des
    tau_b = np.array([p.kp_att[0] * e_b[0] - p.kd_att[0] * w_b[0],
                      p.kp_att[1] * e_b[1] - p.kd_att[1] * w_b[1],
                      -p.kd_yaw * w_b[2]])
    return R @ tau_b


def yaw_torque_to_turn(tau_z, p, dphi_per_turn):
    """turn_bias whose wing yaw torque equals tau_z (body z, uN*mm): the inverse of the
    yaw term in aero_wrench, tau_z = -k_yaw * 2*dphi*turn / phi0."""
    return -float(tau_z) * p.phi0 / (p.k_yaw * 2.0 * dphi_per_turn)


def turn_to_amplitudes(turn_bias, amp_collective, dphi_per_turn):
    """turn_bias > 0 -> turn right -> larger LEFT amplitude."""
    d = dphi_per_turn * turn_bias
    return amp_collective + d, amp_collective - d
