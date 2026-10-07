"""Flight constants: arena geometry (x20 scale), odor-field grid, phase codes.

LIF parameters, brain dt (0.1 ms) and the 25 ms decision step are NOT defined
here; they come from brain_model/model.py and must not change.

Units: mm, s. The fly itself is not scaled (~2.5 mm body).
"""
import numpy as np

SCALE = 20.0  # arena scale relative to the original spec (docs/UCUS_PROMPTU.md)

# ── Geometry (spec x SCALE) ─────────────────────────────────────────────────
# Axis-aligned boxes: ((x0, x1), (y0, y1), (z0, z1))
TOWER1 = ((160.0, 200.0), (-100.0, 160.0), (0.0, 200.0))
TOWER2 = ((280.0, 320.0), (60.0, 300.0), (0.0, 200.0))
TOWERS = (TOWER1, TOWER2)

# Vertical cylinders: (cx, cy, r, z_top); bottom at z = 0
TAKEOFF_PEDESTAL = (0.0, 0.0, 5.0, 19.5)
FOOD_PLATFORM = (440.0, 80.0, 10.0, 169.5)

FOOD_POS = np.array([440.0, 80.0, 170.0])   # odor source / food droplet centre
FOOD_DROP_RADIUS = 0.5                       # visual only (contype 0)
START_POS = np.array([0.0, 0.0, 20.0])       # thorax on the pedestal


def move_takeoff_pedestal(dx, dy):
    """--start-offset (EXPERIMENT DESIGN, SPEC_SENSORY_INPUTS §3.3f): shift the take-off pedestal, and with
    it the fly's start, by (dx, dy) mm. Every user reads cfg.TAKEOFF_PEDESTAL at call time (body geom and
    spawn, odor-field obstacle, surface_below, HDF5 geometry), so call this before any of them is built.
    The pedestal must stay inside the odor grid and clear of the towers."""
    global TAKEOFF_PEDESTAL, START_POS
    x, y, r, zt = TAKEOFF_PEDESTAL
    TAKEOFF_PEDESTAL = (x + float(dx), y + float(dy), r, zt)
    START_POS = START_POS + np.array([float(dx), float(dy), 0.0])
    cx, cy = TAKEOFF_PEDESTAL[:2]
    (gx0, gx1), (gy0, gy1), _ = ODOR_GRID_BOUNDS
    if not (gx0 < cx - r and cx + r < gx1 and gy0 < cy - r and cy + r < gy1):
        raise ValueError(f"pedestal at ({cx:g}, {cy:g}) leaves the odor grid {ODOR_GRID_BOUNDS[:2]}")
    for (x0, x1), (y0, y1), _ in TOWERS:
        if x0 - r <= cx <= x1 + r and y0 - r <= cy <= y1 + r:
            raise ValueError(f"pedestal at ({cx:g}, {cy:g}) overlaps a tower")
    return TAKEOFF_PEDESTAL

# ── 3D odor field (Dijkstra path distance around obstacles) ─────────────────
ODOR_GRID_BOUNDS = ((-60.0, 500.0), (-160.0, 360.0), (0.0, 300.0))
ODOR_GRID_RES = 5.0      # mm; towers are 8 voxels thick, platform 4 voxels wide
ODOR_D0 = 20.0           # mm; C = 1 / (1 + (d/ODOR_D0)^2) -> far field (d0/d)^2
                         # (walking: 1/max(d,1mm)^2, so d0 = 1 mm x SCALE)

# Antenna sampling offset (+-lateral for L/R, +-vertical for U/D).
# Real half-separation ~0.5 mm (walking uses 0.5). At x20 scale that gives
# |I_asym| < 0.005 over most of the route (Stage 1 measurement), so the
# controller uses l_eff = 10 mm: HAND-MADE stand-in for spatio-temporal odor
# sampling (casting) in flight; it keeps l/d at the walking level. I_asym/I_grad
# with the real 0.5 mm are always recorded too; --antenna-real steers with them.
ANTENNA_HALF_SEP_EFF = 10.0   # mm, used for steering by default (HAND-MADE)
ANTENNA_HALF_SEP_REAL = 0.5   # mm, recorded every step; steering with --antenna-real

# ── Physics (Stage 3) ───────────────────────────────────────────────────────
PHYSICS_DT = 1e-4                 # s; 250 physics steps per 25 ms decision
PHYSICS_STEPS_PER_DECISION = 250
ARENA_HALF_SIZE = (700.0, 600.0)  # ground plane half-extents (mm)
# Contact softening for obstacle geoms (CLAUDE.md). Fly-arena pairs keep FlyGym
# defaults (explicit pair values override geom values anyway).
OBSTACLE_SOLIMP = "0.9 0.999 0.001 0.5 2"
OBSTACLE_SOLREF = "0.02 1"

# Arena texture (brain-control Step 0; SPEC_BRAIN_CONTROL R4). Untextured, uniform
# surfaces give T4/T5 motion only at their edges. High-contrast checkers; one
# period = one dark + one light square. Periods keep >= ~10 deg at typical
# viewing distances (ommatidial acceptance ~5 deg). --untextured restores the
# old uniform colours for replay comparison.
TEXTURE_RGB = ((0.2, 0.2, 0.2), (0.8, 0.8, 0.8))
OBSTACLE_TEX_PERIOD = 20.0   # mm, towers / pedestal / food platform
GROUND_TEX_PERIOD = 40.0     # mm (FlyGym default: 0.3/0.4 grey, 140 mm)
# Food platform visual salience (brain-control Step 2, user decision 5; arena design, not a
# control term): the platform pillar and the droplet are uniformly dark (high contrast against
# the 0.2/0.8 checkers and the sky). --platform-neutral: same checker as the other obstacles.
PLATFORM_DARK_RGBA = (0.03, 0.03, 0.03, 1.0)

# Stroke-averaged wing model (flight/quasi_steady.py)
PHI0_DEG = 140.0          # hover stroke amplitude (Drosophila, Fry et al. 2003 order)
F0_HZ = 218.0             # wing-beat frequency
TERMINAL_SPEED_REF = 300.0  # mm/s at CRUISE_PITCH_DEG -> sets c_F (Stage 3 calibration)
CRUISE_PITCH_DEG = 12.0   # body nose-down tilt in cruise (HAND-MADE target)
ROT_DAMP_TAU = 0.05       # s; flapping counter-torque time constant (Hedrick 2009, order)
WING_ARM_LAT = 1.5        # mm; spanwise centre of lift from the body axis
TURN_DPHI_DEG = 5.0       # stroke-amplitude asymmetry per unit turn_bias (Phi_L-Phi_R = 2*5*turn)
YAW_RATE_PER_TURN = 5.0   # rad/s steady yaw rate per unit turn_bias (sets the yaw torque gain)

# Haltere reflex (HAND-MADE, stands in for the VNC haltere-wing reflex)
HALTERE_OMEGA_N = 200.0   # rad/s, roll/pitch attitude loop natural frequency. Flies correct
                          # roll perturbations within ~30 ms (Beatus et al. 2015) -> critically
                          # damped settling 5.8/w_n ~ 30 ms. (Stage 3 used 60 with a 60x inflated
                          # inertia, see flight/body.py; effectively much stiffer.)
HALTERE_ZETA = 1.0
HALTERE_YAW_TAU = 0.02    # s; total yaw damping time constant incl. counter-torque

# Leg poses: offsets (deg) from the walking standing pose (PreprogrammedSteps.default_pose).
# R-side roll/yaw offsets are mirrored. Checked visually (legs gathered under body).
TUCK_POSE_OFFSETS = {"FFemur": -40, "MFemur": -40, "HFemur": -40,
                     "FTibia": 75, "MTibia": 55, "HTibia": 60,
                     "FCoxa_roll": -25, "MCoxa_roll": -25, "HCoxa_roll": -25}
# Leg transitions (HAND-MADE, HAND): the PD joint target moves stand <-> tuck along a cosine
# ramp, updated every physics step (no single-step pose jump). Durations are VARSAYIM, mid-points
# of the SPEC_SENSORY_INPUTS.md §7.2 ranges (not yet checked against the cited papers):
#   tuck   (take-off, VNC tarsal reflex; Fraenkel 1932)                 50-100 ms -> 75 ms
#   extend (landing; Tammero & Dickinson 2002, van Breugel & Dickinson 2012) 100-200 ms -> 150 ms
LEG_TUCK_RAMP_S = 0.075
LEG_EXTEND_RAMP_S = 0.150
# --postures (SPEC_SENSORY_INPUTS §3.3d; HAND, VARSAYIM; offsets from the standing pose, set by rendering
# and a hover/standing check before any closed-loop run, never tuned on behaviour):
# flight pose instead of TUCK_POSE_OFFSETS: forelegs forward and folded under the head, middle and hind
# legs swept back along the abdomen (Coxa: - = forward, + = back; checked by rendering). No Drosophila
# leg-angle measurement in flight was found: the pose is the qualitative description, not a fit.
FLIGHT_POSE_OFFSETS = {"FCoxa": -35, "FFemur": -45, "FTibia": 75, "FCoxa_roll": -25,
                       "MCoxa": 30, "MFemur": 15, "MTibia": -25, "MCoxa_roll": -35,
                       "HCoxa": 30, "HFemur": 15, "HTibia": -25, "HCoxa_roll": -30}
# feeding: forelegs more flexed, hind legs more extended -> body ~6 deg nose-down on the pedestal
# (measured 5.7 deg before the runs; "slight forward lean", VARSAYIM). Ramp 0.3 s both ways (VARSAYIM).
FEED_POSE_OFFSETS = {"FFemur": -15, "FTibia": 30, "HFemur": 15, "HTibia": -20}
LEG_FEED_RAMP_S = 0.300
LEG_POSE_CODE = {"stand": 0, "tuck": 1, "feed": 2}

# ── Closed loop (Stage 4) ───────────────────────────────────────────────────
# Phase codes (HDF5 /behavior/phase, int8)
PHASES = ("perch", "takeoff", "cruise", "approach", "touchdown",
          "feed_extend", "feed_eat", "feed_retract", "landed", "descend")
# "landed" (brain-control Step 1): on the platform after touchdown; feeding is the MN9
# decision (flight/vnc_bridge.py), not a timed phase. The feed_* codes are kept so that the codes in recorded
# files stay valid (no phase of the current code uses them).
# "descend" (--hybrid only, flight/hybrid.py): HAND vertical descent over the platform.
PHASE_CODE = {p: i for i, p in enumerate(PHASES)}

CALIB_STEPS = 10          # 0.25 s pre-takeoff DN baseline (HAND-MADE normalisation)
TAKEOFF_STEPS = 10        # 0.25 s take-off phase
TAKEOFF_LIFT = 0.10       # extra lift fraction during take-off (HAND-MADE)
TOUCHDOWN_LEGS = 2        # tarsus-platform contacts needed ...
TOUCHDOWN_STEPS = 2       # ... on this many consecutive decisions (50 ms)

# Input rates (Hz)
ASC_RATE_MAX = 150.0      # r_asc = 150*(0.15 + 0.85*clip(|omega|/15, 0, 1))
ASC_OMEGA_REF = 15.0      # rad/s
OLF_RATE = (20.0, 150.0)  # normalised antenna odor 0..1 -> Hz
OLF_LOG_FLOOR = 1e-3      # odor normalisation: log10(C/1e-3)/3 clipped to 0..1
SEZ_RATE_FLIGHT, SEZ_RATE_FEED = 10.0, 150.0

# brain-control Step 0 inputs (SPEC_BRAIN_CONTROL.md). Ascending is 0 by default
# (--asc-legacy restores ASC_RATE_MAX mapping); LA>ME luminance input removed.
ORN_FOOD_RATE = (8.0, 150.0)  # food-glomerulus ORNs: spontaneous ~8 Hz (de Bruyne et al. 2001)
                              # -> normalised antenna odor 0..1; each antenna drives only its own ORNs
SUGAR_RATE_CONTACT = 100.0    # sugar GRNs while a tarsus touches the food platform (R0/Shiu protocol);
                              # VARSAYIM: labellar LB3 GRNs stand in for tarsal contact (no proboscis joint)
PERSIST_CUT_STEPS = 8         # after the perch calibration all brain inputs are cut for 200 ms
                              # (persistent-activity measurement, criterion (a)); FlyVis keeps running

# Turn (hybrid): turn_bias = clip(turn_brain + ODOR_TURN_K*tanh(ODOR_TURN_GAIN*I_asym) + b_loom, +-TURN_BIAS_MAX)
# (docs/ADAPTED_CODE.md D.3-D.5)
ODOR_TURN_GAIN = 20.0
ODOR_TURN_K = 2.0
TURN_BIAS_MAX = 2.5
# FlyVis T5 loom term b_loom: gain, per-step persistence, clamp (HAND-MADE; numbers as in the walking code)
FLYVIS_T5_GAIN, FLYVIS_DECAY, FLYVIS_BIAS_MAX = 0.5, 0.5, 0.15

# Collective (lift fraction): pitch_bias = 0.8*tanh(10*I_grad) - v_z/VZ_DAMP_REF + ventral
ODOR_GRAD_GAIN = 10.0
ODOR_GRAD_K = 0.8
VZ_DAMP_REF = 400.0       # mm/s; b_alt_hold = -v_z/VZ_DAMP_REF (HAND-MADE, no target altitude)
VENTRAL_H = 8.0           # mm; ventral reflex below this height over the surface beneath (HAND-MADE)
VENTRAL_K = 0.5
LIFT_FRAC_RANGE = (0.3, 1.8)

# Landing response (HAND-MADE trigger; van Breugel & Dickinson 2012)
LAND_EXPANSION_TRIG = 5.0   # 1/s; platform retinal expansion (d theta/dt)/theta
LAND_SPEED = 40.0           # mm/s target touchdown speed
LAND_BRAKE_PITCH_DEG = 20.0 # max nose-up while braking
