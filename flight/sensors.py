"""Sensors for the flight loop: antenna odor, platform expansion, surface below.
Vision (FlyVis -> FlyWire T4/T5) is in flight/visual_input.py.

All inputs the controller or the brain sees are computed here from the body
state and the rendered compound-eye images; nothing reads the food position
except the odor field itself (the source of the odor) and the geometric
platform-expansion signal of the landing response (HAND-MADE, see config).
"""
import numpy as np

from flight import config as cfg
from flight.odor_field_3d import antenna_odor


# ── odor ─────────────────────────────────────────────────────────────────────
def gaze_frame(R):
    """Head sampling frame: body heading only, roll/pitch removed (columns =
    forward, left, world up). HAND-MADE stand-in for head/gaze stabilisation
    (flies hold the head level against body roll/pitch; related literature: Hengstenberg 1988).
    With the body frame, the 12 deg cruise tilt and the 20 deg landing brake
    mixed sin(pitch) x (forward gradient) into I_grad and the bank of a turn mixed
    the vertical gradient into I_asym (Stage 4 v7 run)."""
    h = float(np.arctan2(R[1, 0], R[0, 0]))
    c, s = np.cos(h), np.sin(h)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def sample_odor(field, pos, R, antenna_real=False):
    """Antenna odor with l_eff (steering, default) and the real l (always recorded),
    sampled in the gaze-stabilised frame. Returns dict: L, R, U, D, I_asym, I_grad
    (steering l) and I_asym_real, I_grad_real."""
    G = gaze_frame(R)
    real = antenna_odor(field, pos, G, cfg.ANTENNA_HALF_SEP_REAL)
    out = real if antenna_real else antenna_odor(field, pos, G, cfg.ANTENNA_HALF_SEP_EFF)
    out = dict(out)
    out["I_asym_real"] = real["I_asym"]
    out["I_grad_real"] = real["I_grad"]
    return out


def odor_norm(c):
    """Concentration (1 at food, ~(d0/d)^2 far) -> 0..1 on a 3-decade log scale."""
    return float(np.clip(np.log10(max(c, 1e-12) / cfg.OLF_LOG_FLOOR) / 3.0, 0.0, 1.0))


def rate(x, lo_hi):
    lo, hi = lo_hi
    return lo + float(np.clip(x, 0.0, 1.0)) * (hi - lo)


def ascending_rate(omega):
    return cfg.ASC_RATE_MAX * (0.15 + 0.85 * float(np.clip(np.linalg.norm(omega) / cfg.ASC_OMEGA_REF, 0, 1)))


# ── FlyVis motion bias b_loom (HAND-MADE gain; docs/ADAPTED_CODE.md D.4) ─────────
class LoomBias:
    """Turn term from the left-right difference of the FlyVis T5 activity, smoothed over decision steps.
    Positive output = turn right (away from the eye with more motion). Must be called at every
    decision step, calibration steps included; the activities come from visual_input.FlyVisEyes.step."""

    def __init__(self):
        self.value = 0.0

    def __call__(self, loom_L, loom_R):
        drive = -cfg.FLYVIS_T5_GAIN * (loom_L - loom_R)
        smoothed = cfg.FLYVIS_DECAY * self.value + (1.0 - cfg.FLYVIS_DECAY) * drive
        self.value = float(np.clip(smoothed, -cfg.FLYVIS_BIAS_MAX, cfg.FLYVIS_BIAS_MAX))
        return self.value


def platform_azimuth(pos, heading):
    """Horizontal bearing of the food platform relative to the heading (deg, + = left).
    Recorded only (orientation measurement); no controller reads it."""
    cx, cy = cfg.FOOD_PLATFORM[:2]
    a = np.arctan2(cy - pos[1], cx - pos[0]) - heading
    return float(np.degrees((a + np.pi) % (2 * np.pi) - np.pi))


# ── landing: retinal expansion of the platform (geometric) ──────────────────
def platform_angular_radius(pos):
    cx, cy, r, zt = cfg.FOOD_PLATFORM
    d = float(np.linalg.norm(np.asarray(pos) - np.array([cx, cy, zt])))
    return float(np.arctan2(r, max(d, 1e-6)))


class ExpansionRate:
    """(d theta/dt)/theta of the platform's angular radius between decisions."""

    def __init__(self, dt):
        self.dt = dt
        self.prev = None

    def __call__(self, pos):
        th = platform_angular_radius(pos)
        e = 0.0 if self.prev is None else (th - self.prev) / (self.dt * th)
        self.prev = th
        return e


# ── surface beneath (ventral reflex) ────────────────────────────────────────
def surface_below(x, y):
    """Height of the highest surface under (x, y): ground, tower tops, cylinder tops."""
    h = 0.0
    for (x0, x1), (y0, y1), (_, z1) in cfg.TOWERS:
        if x0 <= x <= x1 and y0 <= y <= y1:
            h = max(h, z1)
    for cx, cy, r, zt in (cfg.TAKEOFF_PEDESTAL, cfg.FOOD_PLATFORM):
        if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
            h = max(h, zt)
    return h
