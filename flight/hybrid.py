"""--hybrid: the honest hybrid controller ("honest hybrid final", SPEC_BRAIN_CONTROL; Turkish heading "Dürüst hibrit final").

Every motor term carries one label and is recorded separately in the HDF5:

  HAND   hand-made (HAND-MADE), not from the connectome:
           turn_hand   odor-gradient navigation: ODOR_TURN_K*tanh(ODOR_TURN_GAIN*I_asym)
                       (the legacy/walking map, l_eff = 10 mm); take-off/cruise only
           thrust_hand collective (lift fraction - 1). Cruise: odor vertical gradient (legacy
                       map) + a climb-only floor at the platform top + APPROACH_CLEAR; approach:
                       altitude target platform top (169.5) + APPROACH_CLEAR; descend: sink rate.
                       The VNC flight program has no altitude target and DNg02 is silent
                       (SPEC Step 3), so altitude is entirely HAND.
           pitch_hand  body nose-down tilt (rad) = forward thrust; roll_hand: body right bank
                       (rad). Cruise: fixed 12 deg. Approach/descent: horizontal position
                       controller towards the platform centre (world frame, independent of
                       heading). Reads the platform geometry, like the legacy landing trigger.
           phases      take-off timer, approach radius, descent, touchdown, leg extension.
  BRAIN  turn_brain = -K_STEER * s_hat(DNp15)  (vnc_bridge.Bridge.steer, POST-HOC readout,
         K_STEER unchanged). Feeding = MN9 (CB0701) > 10 Hz only (Bridge.proboscis).
  FLYVIS turn_flyvis = b_loom, FlyVis T5 L/R (FlyVis network, not FlyWire; walking constants).
  REFLEX haltere PD (flight/quasi_steady.py) acts every physics sub-step; its yaw damping is
         recorded as turn_reflex = the turn_bias that would give the same wing yaw torque
         (it is NOT part of the command, turn_total).

turn_total = clip(turn_brain + turn_hand + turn_flyvis, +-TURN_BIAS_MAX) is the wing command.

Why v7 hung in the air 29 mm from the food (diagnosis, flight_v7_data.h5 and v8_DEV):
  1. The approach trigger (expansion > 5/s) fired at d = 30 mm while flying at 300 mm/s;
     the one-sided brake then left tilt 0 below 40 mm/s -> drag stopped the fly (fixed in
     5cc0786 for the legacy path).
  2. Altitude came only from the odor I_grad term, which holds the THORAX at the drop
     height (z 170); the extended tarsi hang 1.5-3 mm lower, below the platform top 169.5,
     so the fly met the pillar's side (v8_DEV: stuck at r = 10.7 mm, v = 0).
  3. Near the source the odor turn loop is unstable (gain ~86/s, 25 ms ZOH): heading
     oscillates +-7 deg and the forward-only speed control cannot remove a lateral offset.
  HAND fix here: an altitude target above the platform top (APPROACH_CLEAR), a world-frame
  horizontal position controller in approach (speed ~ distance, independent of heading),
  odor turn off in approach, and a vertical descent only once the thorax is over the platform.
  Checked without a brain (scripts/diag/hyb_landing.py): touchdown at 3.0 s, 0 tower contacts;
  with the recorded v10 DNp15 turn series added as a brain stand-in (offsets 0/40/80):
  touchdown 3.7 / 4.1 / 2.85 s, one intra-step tower touch (0.012 mm) at offset 80.
  The HAND constants were set in these brain-free runs, not in runs with the brain.
"""
import numpy as np

from flight import config as cfg
from flight import quasi_steady as qs

# ── HAND constants (HAND-MADE; set from geometry/cruise calibration, not fitted to success) ──
PLATFORM_TOP = cfg.FOOD_PLATFORM[3]      # 169.5 mm
APPROACH_CLEAR = 8.0      # mm: thorax target above the platform top (tarsi hang <= 3 mm lower)
Z_GAIN = 2.0              # 1/s: altitude error -> vertical-speed target
VZ_MAX = 150.0            # mm/s: climb/sink speed limit
LAND_VZ = 30.0            # mm/s: descent speed onto the platform
R_APPROACH = 100.0        # mm: horizontal distance to the platform centre that starts the approach
                          # (clear of tower 2: its nearest edge is 120 mm from the centre)
V_GAIN = 3.0              # 1/s: approach speed target = min(cruise, V_GAIN * distance)
R_DESCEND = 4.0           # mm: descend when the thorax is this close (horizontally) to the
V_DESCEND = 40.0          # mm/s  centre and slower than this (platform radius 10 mm)
TILT_MAX_DEG = cfg.LAND_BRAKE_PITCH_DEG  # 20 deg: body tilt limit of the position controller
BRAKE_DEG_PER_100 = cfg.LAND_BRAKE_PITCH_DEG  # 20 deg per 100 mm/s velocity error (legacy brake slope)

HYBRID_PHASES = ("takeoff", "cruise", "approach", "descend", "touchdown", "landed")


def altitude_target(phase):
    return PLATFORM_TOP + APPROACH_CLEAR


def thrust_hand(phase, z, v_z, I_grad=0.0, ablate_odor=False):
    """Collective (lift fraction - 1), all HAND. Returns dict total, odor, alt, boost, vz_des.
    takeoff/cruise: odor vertical gradient (legacy map ODOR_GRAD_K*tanh(ODOR_GRAD_GAIN*I_grad);
      the 3D odor field routes over the towers) + a climb-only assist towards the floor
      PLATFORM_TOP + APPROACH_CLEAR (never brakes a climb: with the legacy -v_z damping the fly
      reached tower 1 at z 181 and hit its face, scripts/diag/hyb_landing.py);
    approach: altitude target PLATFORM_TOP + APPROACH_CLEAR (no odor term);
    descend: sink at LAND_VZ."""
    odor, boost = 0.0, 0.0
    if phase == "descend":
        vz_des = -LAND_VZ
        alt = (vz_des - float(v_z)) / cfg.VZ_DAMP_REF
    elif phase == "approach":
        vz_des = float(np.clip(Z_GAIN * (altitude_target(phase) - z), -VZ_MAX, VZ_MAX))
        alt = (vz_des - float(v_z)) / cfg.VZ_DAMP_REF
    else:
        vz_des = float(np.clip(Z_GAIN * (altitude_target(phase) - z), 0.0, VZ_MAX))
        alt = max(vz_des - float(v_z), 0.0) / cfg.VZ_DAMP_REF
        if not ablate_odor:
            odor = cfg.ODOR_GRAD_K * float(np.tanh(cfg.ODOR_GRAD_GAIN * I_grad))
        boost = cfg.TAKEOFF_LIFT if phase == "takeoff" else 0.0
    return dict(total=odor + alt + boost, odor=odor, alt=alt, boost=boost, vz_des=vz_des)


def turn_hand(I_asym, phase, ablate_odor=False):
    """Odor steering (docs/ADAPTED_CODE.md D.3): K*tanh(G*I_asym), positive = turn right.
    Active in takeoff/cruise only. Over the platform the odor loop is unstable (v7 diagnosis 3:
    with it on, the fly circled at d_xy 4-6 mm for 5 s in hyb_landing.py) and the approach
    controller works in the world frame, heading-free."""
    if ablate_odor or phase not in ("takeoff", "cruise"):
        return 0.0
    return cfg.ODOR_TURN_K * float(np.tanh(cfg.ODOR_TURN_GAIN * I_asym))


def platform_offset(pos):
    """Horizontal vector from the thorax to the platform centre (mm)."""
    cx, cy = cfg.FOOD_PLATFORM[:2]
    return np.array([cx - pos[0], cy - pos[1]])


def tilt_hand(phase, pos, vel, heading):
    """(pitch_down, roll_right) body tilt targets in rad and the horizontal speed target.
    Cruise: fixed CRUISE_PITCH_DEG. Approach/descend: world-frame horizontal velocity loop,
    v_des towards the platform centre, |v_des| = min(TERMINAL_SPEED_REF, V_GAIN*d);
    tilt = feed-forward (linear drag, cruise calibration) - brake slope * (v - v_des)."""
    if phase in ("takeoff", "touchdown", "landed"):
        return 0.0, 0.0, 0.0
    if phase == "cruise":
        return np.radians(cfg.CRUISE_PITCH_DEG), 0.0, cfg.TERMINAL_SPEED_REF
    off = platform_offset(pos)
    d = float(np.linalg.norm(off))
    speed = min(cfg.TERMINAL_SPEED_REF, V_GAIN * d)
    v_des = off / max(d, 1e-9) * speed
    ff = np.radians(cfg.CRUISE_PITCH_DEG) / cfg.TERMINAL_SPEED_REF
    brake = np.radians(BRAKE_DEG_PER_100) / 100.0
    tilt = ff * v_des - brake * (np.asarray(vel[:2]) - v_des)       # world horizontal tilt vector
    n = float(np.linalg.norm(tilt))
    tmax = np.radians(TILT_MAX_DEG)
    if n > tmax:
        tilt *= tmax / n
    h = np.array([np.cos(heading), np.sin(heading)])
    r = np.array([np.sin(heading), -np.cos(heading)])
    return float(tilt @ h), float(tilt @ r), speed


class HybridPhases:
    """takeoff (timed) -> cruise -> approach (d_xy < R_APPROACH) -> descend (over the platform,
    slow) -> touchdown (TOUCHDOWN_LEGS tarsi on the platform for TOUCHDOWN_STEPS) -> landed.
    All HAND. Feeding is not a phase: MN9 > threshold while landed (vnc_bridge)."""

    def __init__(self):
        self.phase = "takeoff"
        self.t_in = 0
        self.touch_run = 0

    def update(self, pos, vel, platform_legs):
        p = self.phase
        self.t_in += 1
        nxt = p
        d = float(np.linalg.norm(platform_offset(pos)))
        v_h = float(np.linalg.norm(vel[:2]))
        if p == "takeoff" and self.t_in >= cfg.TAKEOFF_STEPS:
            nxt = "cruise"
        elif p == "cruise" and d < R_APPROACH:
            nxt = "approach"
        elif p == "approach" and d < R_DESCEND and v_h < V_DESCEND and pos[2] > PLATFORM_TOP:
            nxt = "descend"
        if p in ("cruise", "approach", "descend"):
            self.touch_run = self.touch_run + 1 if platform_legs >= cfg.TOUCHDOWN_LEGS else 0
            if self.touch_run >= cfg.TOUCHDOWN_STEPS:
                nxt = "touchdown"
        elif p == "touchdown":
            nxt = "landed"
        if nxt != p:
            self.phase, self.t_in = nxt, 0
        return self.phase

    @property
    def wings_on(self):
        return self.phase in ("takeoff", "cruise", "approach", "descend")

    @property
    def legs_extended(self):
        return self.phase in ("approach", "descend", "touchdown", "landed")

    @property
    def landed(self):
        return self.phase in ("touchdown", "landed")


def wing_command(turn_total, thrust, pitch_down, roll_right, params, wings_on=True):
    """As controller.wing_command, with the hover amplitude for the total tilt."""
    if not wings_on:
        return qs.WingCommand(0.0, 0.0, 0.0, on=False), 1.0
    lift = float(np.clip(1.0 + thrust, *cfg.LIFT_FRAC_RANGE))
    tilt = float(np.arccos(np.clip(np.cos(pitch_down) * np.cos(roll_right), -1.0, 1.0)))
    a = qs.hover_amplitude(params, tilt) * np.sqrt(lift)
    aL, aR = qs.turn_to_amplitudes(turn_total, a, cfg.TURN_DPHI_DEG)
    return qs.WingCommand(aL, aR, params.f0), lift


def combine_turn(turn_brain, turn_hand_, turn_flyvis):
    return float(np.clip(turn_brain + turn_hand_ + turn_flyvis, -cfg.TURN_BIAS_MAX, cfg.TURN_BIAS_MAX))
