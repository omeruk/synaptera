"""Decision-step controller (every 25 ms) of the brain-only path: yaw / collective / pitch / phases.

Pure functions; every term is returned separately so the HDF5 can record the
contribution of each one. Terms and their origin:

  turn_bias  = turn_dn   (BRAIN: VNC-bridge DNp15 readout, flight/vnc_bridge.py); the odor,
               FlyVis and all-DN terms are recorded as 0 on this path (the hybrid path adds
               them in flight/hybrid.py). The earlier all-DN/odor/FlyVis sum of the
               --legacy-control path was removed (archive/adapted_originals/).
  pitch_bias = pitch_odor + pitch_alt + pitch_ventral (+ take-off boost) -> lift fraction
    pitch_odor    = 0.8*tanh(10*I_grad) HAND-MADE mapping of the up/down odor gradient
    pitch_alt     = -v_z/400 mm/s       HAND-MADE vertical-speed damping (no target altitude)
    pitch_ventral                        HAND-MADE ventral reflex near the surface below
  No connectome term on the collective: DNg02 (25 neurons) is silent in this
  model (SPEC, Stage 2/4) and is only recorded, as are DNa01/DNa02 ("steer").
  pitch_down (body tilt, forward speed): cruise 12 deg (HAND-MADE); braking
  nose-up in the landing response (HAND-MADE trigger).

Sign: turn_bias > 0 -> larger left amplitude -> right turn (as in walking:
odor stronger on the right -> I_asym > 0 -> turn right).
"""
import numpy as np

from flight import config as cfg
from flight import quasi_steady as qs


def turn_terms_brain(turn_dn, s_hat):
    """brain-control Step 2: the yaw command is the VNC-bridge DN readout only
    (flight/vnc_bridge.py); odor, b_loom and all-DN terms are off (recorded as 0)."""
    return dict(turn_bias=float(turn_dn), turn_odor=0.0, turn_dn=float(turn_dn), turn_loom=0.0,
                dn_lr_delta=float(s_hat))


def pitch_terms(I_grad, v_z, height_above, phase, ablate_odor=False):
    odor = 0.0 if ablate_odor else cfg.ODOR_GRAD_K * float(np.tanh(cfg.ODOR_GRAD_GAIN * I_grad))
    alt = -float(v_z) / cfg.VZ_DAMP_REF
    ventral = 0.0
    if phase == "cruise" and height_above < cfg.VENTRAL_H:
        ventral = cfg.VENTRAL_K * (1.0 - max(height_above, 0.0) / cfg.VENTRAL_H)
    boost = cfg.TAKEOFF_LIFT if phase == "takeoff" else 0.0
    total = odor + alt + ventral + boost
    return dict(pitch_bias=total, pitch_odor=odor, pitch_alt=alt, pitch_ventral=ventral,
                pitch_takeoff=boost)


def body_pitch_target(phase, v_fwd):
    """Nose-down tilt (rad). v_fwd: horizontal speed along the heading (mm/s).
    Cruise: fixed 12 deg. Approach: hold the landing speed. Feed-forward tilt of
    LAND_SPEED (linear drag: tilt ~ speed, from the cruise calibration) plus the
    braking slope (20 deg per 100 mm/s) on both sides: nose-up while faster,
    nose-down while slower. The Stage 4 version only braked (tilt 0 below
    LAND_SPEED), so after braking the fly hovered in place and never reached
    the platform."""
    if phase == "cruise":
        return np.radians(cfg.CRUISE_PITCH_DEG)
    if phase == "approach":
        ff = cfg.CRUISE_PITCH_DEG * cfg.LAND_SPEED / cfg.TERMINAL_SPEED_REF
        deg = ff - cfg.LAND_BRAKE_PITCH_DEG * (v_fwd - cfg.LAND_SPEED) / 100.0
        return np.radians(np.clip(deg, -cfg.LAND_BRAKE_PITCH_DEG, cfg.CRUISE_PITCH_DEG))
    return 0.0


def wing_command(turn_bias, pitch_bias, pitch_down, params, wings_on=True):
    if not wings_on:
        return qs.WingCommand(0.0, 0.0, 0.0, on=False), 1.0
    lift = float(np.clip(1.0 + pitch_bias, *cfg.LIFT_FRAC_RANGE))
    a = qs.hover_amplitude(params, abs(pitch_down)) * np.sqrt(lift)
    aL, aR = qs.turn_to_amplitudes(turn_bias, a, cfg.TURN_DPHI_DEG)
    return qs.WingCommand(aL, aR, params.f0), lift


class PhaseMachine:
    """Brain-only flight phases: takeoff -> cruise -> approach -> touchdown -> landed.
    Takeoff lasts TAKEOFF_STEPS decisions; cruise becomes approach when the platform's retinal
    expansion exceeds LAND_EXPANSION_TRIG; touchdown = TOUCHDOWN_LEGS tarsi on the platform for
    TOUCHDOWN_STEPS consecutive decisions (cruise or approach). After touchdown the fly is "landed";
    feeding is the MN9 decision (flight/vnc_bridge.py), not a phase.
    start="landed": the run begins standing on the food platform (--start-on-platform, experiment design)."""

    def __init__(self, dt, start="takeoff"):
        self.dt = dt
        self.phase = start
        self.t_in = 0              # decisions spent in the current phase
        self.touch_run = 0         # consecutive decisions with enough platform contacts

    def update(self, expansion, platform_legs):
        was = self.phase
        self.t_in += 1
        nxt = was
        if was == "takeoff" and self.t_in >= cfg.TAKEOFF_STEPS:
            nxt = "cruise"
        elif was == "cruise" and expansion > cfg.LAND_EXPANSION_TRIG:
            nxt = "approach"
        if was in ("cruise", "approach"):
            enough = platform_legs >= cfg.TOUCHDOWN_LEGS
            self.touch_run = self.touch_run + 1 if enough else 0
            if self.touch_run >= cfg.TOUCHDOWN_STEPS:
                nxt = "touchdown"
        elif was == "touchdown":
            nxt = "landed"
        if nxt != was:
            self.phase, self.t_in = nxt, 0
        return self.phase

    @property
    def wings_on(self):
        return self.phase in ("takeoff", "cruise", "approach")

    @property
    def landed(self):
        return self.phase in ("touchdown", "landed")
