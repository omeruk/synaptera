#!/usr/bin/env python
"""HDF5 -> 1920x1080 / 30 fps flight video v2: live whole-brain activity + circuit + body (qpos replay).

Layout (pixels)
    y    0-380  brain: frontal (x-y, seen from the front: the fly's left is on the RIGHT) and dorsal
                (x-z, anterior up) projections of every neuron's arbor centroid (synapse centroid,
                data/neuron_arbor_centroids.npz). Every neuron one soft dot of the same size, drawn at
                2x and area-downscaled: a dim static base cloud (depth-dimmed) + additive activity dots
                (np.bincount + Gaussian), hue-preserving tone map, light bloom; fixed display gain per class.
                Colour = class (data/neuron_class.npz). Glow tau 80 ms.
                Default "change" mode: a neuron glows only when its last-250 ms rate is above its
                FIXED baseline = its mean rate over the first 0.5 s of the closed loop (run t in
                [0, 0.5) s) (dF/F-like: (r250 - r0) / (r0 + 5 Hz), and z > 1.5 against Poisson noise),
                so the constant Poisson floor (e.g. T4/T5 drive) does not fill the screen, while
                sustained activity (e.g. taste/GNG during feeding) keeps glowing.
                --mode absolute: every spike glows.
         right  neuropil bars, L | R (dominant neuropil per neuron, data/neuron_neuropil.npz),
                mean rate over the last 250 ms, tick = fixed baseline (first 0.5 s).
    y  380-600  circuit: eye (FlyVis) -> T4/T5 -> LOP -> DNp15 (+DNa02 recorded) -> VNC bridge ->
                wing turn command; ORN -> AL -> MB/LH (brain odour input OFF in these runs);
                sugar GRN -> SEZ -> MN9 -> feeding. Box brightness = rate / run p95, value in Hz,
                arrow width proportional to the source box's rate (not a measured flux).
    y  600-930  follow camera (wing motion blur from the recorded stroke amplitudes) | arena
                with 3D trail (colour = time), fly's eyes (FlyGym ommatidia) + T4/T5 type rates.
                Follow camera angle by phase (CAM_VIEWS): rear three-quarter in cruise, side view in
                approach / descent, front-side close-up on the head at touchdown and feeding; 0.5 s ramps.
                Camera views only: food drop yellow, dark food platform mid grey (the eyes / FlyVis see the
                simulated dark colours).
    y  930-1080 HUD + 2 s traces: turn terms BRAIN/HAND/FLYVIS/REFLEX (stacked), altitude,
                distance to food, MN9 + 10 Hz threshold, phase shading.
Title card 6 s, end card 8 s.
Playback: x0.25 (120 Hz sim frames at 30 fps); from 1.0 s after feeding onset every 4th frame (x1.0 real
time), labelled on screen. HUD time, traces and trail use the true run time of each shown frame.

Rates in boxes: readouts recorded by the simulation (DNp15, DNa02, MN9: 50 ms low-pass; FlyVis
T4/T5 input; sugar GRN drive) are shown as recorded; population boxes (T4/T5, LOP, ORN, AL, MB, LH,
SEZ) are 250 ms rate estimates from the stored spikes.

Wings: no joints/dynamics in the model (stroke-averaged forces). Follow camera: motion blur as a real
camera sees it: WING_BLUR_N copies of each wing geom (own colour, low opacity) at the stroke angles
Phi_s/2 cos(phi_k) of one exposure, phi_k stratified (one random offset per 1/N slot) over min(1, f * WING_EXPOSURE_S) cycles with the
recorded L/R amplitude Phi_s and stroke_freq f (218 Hz x 1/120 s > 1 cycle: a full cycle). Copies at
the same angle merge (alpha 1 - (1 - a)^count), so the opacity follows the sinusoid's dwell density:
darker at the stroke reversals. Wings closed: no blur. Arena camera: wings at mid-stroke.
Persistent label (follow camera): what is hand-made vs. brain in this run (from the HDF5 flags).

Memory: frames are streamed (writer.append_data), plt.close(fig) after each; no frame list.
    env -u PYTHONPATH MUJOCO_GL=egl python render_flight_video_v2.py <h5> --keyframes auto
    env -u PYTHONPATH MUJOCO_GL=egl python render_flight_video_v2.py <h5>            # full video
"""
import argparse
import json
import os
import re
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import cv2  # noqa: E402
import h5py  # noqa: E402
import imageio  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.offsetbox import AnnotationBbox, HPacker, TextArea  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
import mujoco  # noqa: E402
import numpy as np  # noqa: E402

from flight import config as cfg  # noqa: E402
from flight.body import FlightBody  # noqa: E402

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
W, H = 1920, 1080
BRAIN_H = 380
CIRC_Y0, CIRC_H = 380, 220
CAM_Y0, CAM_H, CAM_W = 600, 330, 960
HUD_Y0 = 930
GLOW_TAU, FAST_TAU = 0.08, 0.25                     # s (brain clock)
BASE_T = 0.5                                        # s, fixed baseline window: run t in [0, BASE_T)
FEED_SLOW_S, FEED_SKIP = 1.0, 4                     # feeding: first 1.0 s at x0.25, then every 4th frame
# food drop colour in the camera views only; semi-transparent so that the proboscis marker, which ends inside
# the drop (the haustellum is ~0.1 mm from its surface while feeding), stays visible
FOOD_RENDER_RGBA = (1.0, 0.9, 0.1, 0.45)
DFF_R0, Z_MIN = 5.0, 1.5
EYE_X0, EYE_Y0 = CAM_W + 8, CAM_Y0 + CAM_H - 126      # eye insets (bottom-left of the arena panel)
TRACE_WIN = 2.0
MN9_THR = 10.0                                      # Hz, feeding readout threshold (display of the marker)                                     # s
WING_BLUR_N = 64                                    # wing copies per exposure (one stroke cycle)
# opacity of one copy, scaled so that N copies give the same total visibility as the former 16 copies
# at alpha 0.10: 1 - (1 - a)^(N/16) = 0.10 (overlapping copies composite as 1 - (1 - a)^count)
WING_BLUR_ALPHA = 1.0 - (1.0 - 0.10) ** (16 / WING_BLUR_N)
WING_EXPOSURE_S = 1.0 / 120                         # exposure = one 120 Hz sim frame
TITLE_S, END_S = 6.0, 8.0
# follow camera per phase class: (azimuth offset from the heading (deg; 0 = from behind, 90 = side, 180 = front),
# elevation (deg), distance (mm), lookat weight thorax -> haustellum); negative offsets: from the fly's left
# side (all classes on the same side, no swing across). Class changes ramp over CAM_RAMP_S (smoothstep of
# the view parameters, restarted from the current view if a ramp is still running): no cut.
CAM_VIEWS = {"cruise": (-40.0, -22.0, 7.5, 0.0),     # rear three-quarter: head and wings visible
             "side": (-90.0, -12.0, 7.0, 0.0),       # approach / descent: side view
             "close": (-120.0, -8.0, 3.4, 0.5)}      # touchdown / feeding: front-side close-up on the head
CAM_CLASS = {"perch": "cruise", "takeoff": "cruise", "cruise": "cruise", "approach": "side", "descend": "side"}
CAM_RAMP_S = 0.5
# food platform in the camera views only: mid grey instead of the simulated near-black (the eyes / FlyVis keep the
# simulated colour, as for the food drop)
PLATFORM_RENDER_RGBA = (0.5, 0.5, 0.5, 1.0)
# FlyVis display layer (/flyvis: |a - a0| of the NOT driven FlyVis types at their mapped FlyWire neurons)
FV_RGB = (210, 255, 60)                             # lime: not used by any neuron class colour
FV_ALPHA, FV_SAT = 0.6, 1.5                         # max opacity; summed weight per blurred pixel at ~63 %
# brain panels (display settings, not measurements). Every neuron is ONE soft dot of the same size for all classes
# (Gaussian, sigma DOT_SIGMA px at panel resolution, peak 1), drawn at BR_SS x resolution and area-downscaled. Dots
# add up in a float buffer (exposure, per channel); tone mapping per pixel on the brightest channel M:
# level = (1 - exp(-M))^GLOW_GAMMA, the other channels scaled with it (hue kept), cores with M > WHITE_M0 shift up to
# WHITE_MIX towards white; then a light bloom (blur sigma BLOOM_SIGMA px of the part above BLOOM_FROM, weight BLOOM_W).
# Activity weight of a neuron = BrainState.intensity (graded, tau 80 ms) x a FIXED display gain of its class
# (Renderer.calibrate_gain): for the crowded classes (keys of BIG_LEVEL) the GAIN_PCT percentile of the class-only
# exposure over GAIN_SAMPLES frames maps to the class's level in BIG_LEVEL; a small class gets
# SMALL_X / (median intensity of its active neurons), i.e. a typical firing neuron reaches ~full brightness.
BR_SS, DOT_SIGMA = 2, 0.7
GAIN_PCT, GAIN_SAMPLES, GLOW_GAMMA = 99.5, 40, 0.6
BIG_LEVEL, SMALL_X = {"visual": 0.80, "other": 0.70}, 3.0
WHITE_M0, WHITE_MIX = 3.0, 0.25
BLOOM_SIGMA, BLOOM_FROM, BLOOM_W = 5.0, 0.35, 0.22
PANEL_BG = (0, 0, 0)                               # brain panels: black background
FEED_CIRCUIT_COL = {"sugar GRN": "#ff69c8", "SEZ": "#ff69c8", "MN9": "#ffa000"}   # = circuit strip boxes
# base layer: every neuron as a very dim cold grey-blue dot (same dot); dense parts reach CLOUD_LEVEL of CLOUD_RGB;
# depth cue: the neuron farthest from the camera gets (1 - CLOUD_DEPTH) of the weight of the nearest
CLOUD_RGB, CLOUD_LEVEL, CLOUD_DEPTH = (120, 150, 200), 0.35, 0.55
GAIN_NOTE = "display gain per class (fixed); dot size equal for all neurons"
BG = (11, 13, 18)
BGf = tuple(c / 255 for c in BG)

# class colours: saturated, distinct also under deutan/protan/tritan simulation (Machado 2009; min CIELAB dE
# between classes incl. the FlyVis lime >= 17; blue/yellow and lightness carry the contrast, not red-green alone)
CLASS_RGB = {"other": (255, 205, 140), "visual": (70, 150, 255), "olfactory": (0, 225, 175),
             "taste": (255, 105, 200), "DN": (255, 50, 30), "motor": (255, 150, 0)}
CLASS_LABEL = {"other": "other", "visual": "visual", "olfactory": "olfactory", "taste": "taste", "DN": "DN",
               "motor": "motor"}
TERM_COL = {"brain": "#ff5a3c", "hand": "#c8cfd8", "flyvis": "#3d9bff", "reflex": "#ffd23f"}
# text colours on the dark background (WCAG contrast vs BG): TXT2 12.4:1, TXT3 10.6:1
TXT2, TXT3 = "#c8cfd8", "#b8c0ca"
MIN_PT = 9.0                                        # smallest text in the frames (pt at 100 dpi = 12.5 px)
TERM_LABEL = {"brain": "BRAIN", "hand": "HAND-MADE", "flyvis": "FLYVIS", "reflex": "REFLEX"}   # README terms
TITLE = "Synaptera"
SUBTITLE = ("From synapse to wing: what a whole-brain connectome model controls in closed-loop "
            "Drosophila flight")
PHASE_COL = {"perch": "#8a8f98", "takeoff": "#ffe14d", "cruise": "#4d94ff", "approach": "#d98cff",
             "descend": "#ff8a1f", "touchdown": "#ff2e5a", "landed": "#00c8a0", "feed_extend": "#00c8a0",
             "feed_eat": "#00c8a0", "feed_retract": "#00c8a0"}
PHASE_LABEL = {"perch": "perch", "takeoff": "take-off", "cruise": "cruise", "approach": "approach",
               "descend": "descent", "touchdown": "touchdown", "landed": "landed", "feed_extend": "feeding",
               "feed_eat": "feeding", "feed_retract": "feeding"}
# neuropil bar rows: label -> base neuropil names (dominant neuropil of each neuron)
NP_ROWS = (("AL", ("AL",)), ("MB", ("MB_CA", "MB_PED", "MB_VL", "MB_ML")), ("LH", ("LH",)),
           ("LA", ("LA",)), ("ME", ("ME", "AME")), ("LO", ("LO",)), ("LOP", ("LOP",)),
           ("AOTU", ("AOTU",)), ("PVLP/AVLP", ("PVLP", "AVLP")), ("PLP", ("PLP",)),
           ("SPS/IPS", ("SPS", "IPS")), ("LAL", ("LAL",)), ("VES/WED", ("VES", "WED")),
           ("SMP/SLP/SIP", ("SMP", "SLP", "SIP")), ("GNG/SEZ", ("GNG", "PRW", "SAD")),
           ("central complex", ("EB", "FB", "PB", "NO")))


# ── data ─────────────────────────────────────────────────────────────────────
def ema_coef(dt, tau):
    return float(np.exp(-dt / tau))


class Run:
    """Everything read from one HDF5 file."""

    def __init__(self, path):
        self.path = Path(path)
        f = h5py.File(path, "r")
        self.meta = {k: f["meta"].attrs[k] for k in f["meta"].attrs}
        self.flags = json.loads(self.meta["flags"])
        self.fps = int(self.meta.get("fps", 30))
        self.dt_dec = float(self.meta["decision_interval"])
        self.b = {k: f["behavior"][k][:] for k in f["behavior"]}
        self.codes = {v: k for k, v in json.loads(f["behavior/phase"].attrs["codes"]).items()}
        self.rt = f["render/t"][:]
        self.rt_len = len(self.rt)
        self.qpos = f["render/qpos"]               # read per frame
        self.spk_t = f["spikes/all/t"][:]
        self.spk_i = f["spikes/all/i"][:]
        self.groups = {k: f["spikes/groups"][k][:] for k in f["spikes/groups"]}
        self.step_idx = f["spikes/step_idx"][:]
        self.step_neu = f["spikes/neuron_idx"][:]
        self.step_cnt = f["spikes/count"][:]
        self.n = int(self.meta["n_neurons"])
        # brain clock: spikes of step s lie in [(s - s_min) dt, (s - s_min + 1) dt); run step 0 = [0, dt)
        self.s_min = int(self.step_idx.min())
        self.offset = -self.s_min * self.dt_dec
        self.readout_types = json.loads(self.meta["readout_types"])
        self.f = f
        # --vision-boundary: FlyVis display layer (/flyvis, NOT driven types; display only, never an input)
        self.fv = None
        if "flyvis" in f:
            g = f["flyvis"]
            act = g["activity"]
            # row of each decision step: /flyvis/step_idx when written; else rows are consecutive from the first
            # sensed step (perch calibration + input cut), the same first step as the spikes (s_min)
            if "step_idx" in g:
                rows = {int(s): j for j, s in enumerate(g["step_idx"][:])}
                row_of = np.array([rows.get(s, -1) for s in range(len(self.b["t"]))])
            else:
                assert act.shape[0] == len(self.b["t"]) - self.s_min, "flyvis rows != pre-steps + steps"
                row_of = np.arange(len(self.b["t"])) - self.s_min
            mp = g["flywire_map"]
            idx, eye, pos = mp["idx"][:], mp["eye"][:].astype(np.int64), mp["pos"][:].astype(np.int64)
            a = np.abs(act[:].astype(np.float32))[:, eye, pos]           # (rows, mapped neurons) |a - a0|
            self.fv = dict(idx=idx, absact=a, row_of=row_of, p99=float(np.percentile(a, 99)),
                           n_types=len(np.unique(g["node_type"][:])))
        self.vbnd = None
        if "vision_boundary" in f:
            vb = f["vision_boundary"]
            self.vbnd = dict(n_types=len(vb["types"]),
                             count={s: np.bincount(vb[f"type_code_{s}"][:], minlength=len(vb["types"]))
                                    for s in "LR"})

    def step_at(self, t):
        """Index of the decision step in progress at run time t."""
        return int(np.clip(np.searchsorted(self.b["t"], t + 1e-9), 0, len(self.b["t"]) - 1))

    def phase(self, k):
        return self.codes.get(int(self.b["phase"][k]), "?")

    def follow_cam(self):
        return FollowCam(self)

    def readout(self, name, k):
        j = self.readout_types.index(name)
        return self.b["dn_readout_rate"][k, j]           # (L, R) Hz

    def eye_drive(self, k, side):
        """FlyVis target rate (Hz) averaged over the boundary-layer neurons of one side (types weighted by size)."""
        j = 0 if side == "L" else 1
        if self.vbnd is None:
            return float(self.b[f"t45_rate_{side}"][k])
        c = self.vbnd["count"][side]
        return float((self.b["vbnd_type_rate"][k, j] * c).sum() / c.sum())

    def group_step_rates(self, idx):
        """Mean rate (Hz) of a neuron set per run step, from the sparse per-step counts."""
        m = np.isin(self.step_neu, idx) & (self.step_idx >= 0)
        c = np.bincount(self.step_idx[m], weights=self.step_cnt[m], minlength=len(self.b["t"]))
        return c / max(len(idx), 1) / self.dt_dec

    def summary(self):
        b = self.b
        td = np.nonzero(b["phase"] == 4)[0]
        k_td = int(td[0]) if len(td) else None
        feed = np.nonzero(b["is_feeding"] > 0)[0]
        mn9 = np.nonzero(b["mn9_rate"] > 10.0)[0]
        pre = slice(0, k_td if k_td is not None else len(b["t"]))
        pen_steps = np.nonzero(b["tower_penetration"][pre] > 0)[0]
        s1 = k_td is not None and b["tower_contact"][pre].sum() == 0 and len(pen_steps) == 0
        s2 = k_td is not None and len(feed) > 0 and feed[0] >= k_td
        share = json.loads(self.meta["turn_share"]) if "turn_share" in self.meta else None
        return dict(k_td=k_td, t_td=float(b["t"][k_td]) if k_td is not None else None,
                    v_td=float(b["speed"][k_td]) if k_td is not None else None,
                    k_feed=int(feed[0]) if len(feed) else None, n_feed=int(len(feed)),
                    k_mn9=int(mn9[0]) if len(mn9) else None,
                    t_mn9=float(b["t"][mn9[0]]) if len(mn9) else None,
                    mn9_mean_feed=float(b["mn9_rate"][feed].mean()) if len(feed) else None,
                    pen_steps=pen_steps.tolist(), pen_max=float(b["tower_penetration"][pre].max(initial=0)),
                    tower_contact=int(b["tower_contact"].sum()), s1=bool(s1), s2=bool(s2), share=share,
                    d_min=float(b["dist_to_food"].min()), d_end=float(b["dist_to_food"][-1]))


class FollowCam:
    """Follow-camera view (CAM_VIEWS) as a pure function of run time: the class of the step in progress, ramped
    over CAM_RAMP_S from the view at the class change (key frames and the video get the same view)."""

    def __init__(self, run):
        t = run.b["t"]
        cls = [CAM_CLASS.get(run.phase(k), "close") for k in range(len(t))]
        self.c0 = cls[0]
        # step k is shown for run time in (t[k-1], t[k]] (Run.step_at)
        self.changes = [(float(t[k - 1]), cls[k]) for k in range(1, len(cls)) if cls[k] != cls[k - 1]]

    @staticmethod
    def _blend(a, b, x):
        w = float(np.clip(x, 0.0, 1.0))
        w = w * w * (3 - 2 * w)
        return a + (b - a) * w

    def view(self, t):
        v0, t0, tgt = np.array(CAM_VIEWS[self.c0]), -np.inf, np.array(CAM_VIEWS[self.c0])
        for tc, c in self.changes:
            if tc > t:
                break
            v0, t0, tgt = self._blend(v0, tgt, (tc - t0) / CAM_RAMP_S), tc, np.array(CAM_VIEWS[c])
        return self._blend(v0, tgt, (t - t0) / CAM_RAMP_S)


class BrainState:
    """Per-neuron glow (tau 80 ms) and 250 ms rate EMA, updated incrementally per frame; fixed per-neuron
    baseline = mean rate over run t in [0, BASE_T) (first 0.5 s of the closed loop)."""

    def __init__(self, run):
        self.run = run
        n = run.n
        self.glow = np.zeros(n, np.float32)
        warm = run.offset                           # perch calibration + input cut before run t = 0
        c0 = np.bincount(run.spk_i[run.spk_t < warm], minlength=n).astype(np.float32) / max(warm, 1e-3)
        self.fast = c0.copy()
        m = (run.spk_t >= warm) & (run.spk_t < warm + BASE_T)
        self.base = np.bincount(run.spk_i[m], minlength=n).astype(np.float32) / np.float32(BASE_T)
        self.s0 = int(np.searchsorted(run.spk_t, warm, side="right"))
        self.t_prev = 0.0

    def advance(self, t):
        run = self.run
        dt = max(t - self.t_prev, 1e-6)
        s1 = int(np.searchsorted(run.spk_t, t + run.offset, side="right"))
        cnt = np.bincount(run.spk_i[self.s0:s1], minlength=run.n).astype(np.float32) if s1 > self.s0 \
            else None
        for arr, tau, scale in ((self.glow, GLOW_TAU, None), (self.fast, FAST_TAU, dt)):
            a = np.float32(ema_coef(dt, tau))
            arr *= a
            if cnt is not None:
                arr += cnt if scale is None else cnt * np.float32((1 - a) / scale)
        self.s0, self.t_prev = s1, t

    def intensity(self, mode):
        g = 1.0 - np.exp(-self.glow)
        if mode == "absolute":
            return g
        d = self.fast - self.base
        dff = d / (self.base + DFF_R0)
        z = d / np.sqrt((self.base + 1.0) / (2 * FAST_TAU))
        return g * np.clip(dff, 0, 1) * (z > Z_MIN)


# ── brain images ─────────────────────────────────────────────────────────────
class BrainView:
    """One projection, drawn at BR_SS x resolution: static base cloud once, then per frame the additive soft dots of
    the active neurons (see BR_SS ... BLOOM_W), tone-mapped, bloomed and area-downscaled."""

    def __init__(self, u, v, depth, w, h, scale, u0, v0, cls_rgb, cls):
        self.w, self.h = w, h
        self.W2, self.H2 = w * BR_SS, h * BR_SS
        fx, fy = u0 + scale * u, v0 + scale * v
        self.px = np.clip(np.round(fx).astype(np.int64), 0, w - 1)          # panel px (labels, region masks)
        self.py = np.clip(np.round(fy).astype(np.int64), 0, h - 1)
        px2 = np.clip(np.floor(fx * BR_SS).astype(np.int64), 0, self.W2 - 1)
        py2 = np.clip(np.floor(fy * BR_SS).astype(np.int64), 0, self.H2 - 1)
        self.lin = py2 * self.W2 + px2
        self.rgb = cls_rgb / cls_rgb.max(1, keepdims=True)                 # brightest channel 1
        self.cls = cls
        self.sig = DOT_SIGMA * BR_SS
        self.peak = np.float32(2 * np.pi * self.sig ** 2)                    # Gaussian with peak 1
        d = (depth - depth.min()) / max(np.ptp(depth), 1e-9)
        dens = self.splat(self.lin, 1.0 - CLOUD_DEPTH * d)
        ref = np.percentile(dens[dens > 1e-3], 99)
        lvl = CLOUD_LEVEL * (1.0 - np.exp(-2.0 * dens / ref)) / (1.0 - np.exp(-2.0))
        self.bg = PANEL_BG + lvl[..., None] * np.array(CLOUD_RGB, np.float32)

    def splat(self, lin, wgt):
        acc = np.bincount(lin, weights=wgt, minlength=self.W2 * self.H2).reshape(self.H2, self.W2)
        return self.peak * cv2.GaussianBlur(acc.astype(np.float32), (0, 0), self.sig)

    def exposure(self, a, gains=None, only=None):
        """Activity exposure (H2, W2, 3), class colour x intensity x class gain, summed over soft dots; None when
        nothing is on. `only`: restrict to one class index (gain calibration)."""
        on = a > 0.01
        if only is not None:
            on &= self.cls == only
        if not on.any():
            return None
        wgt = a[on].astype(np.float64) * (1.0 if gains is None else gains[self.cls[on]])
        lin = self.lin[on]
        return np.stack([self.splat(lin, wgt * self.rgb[on, c]) for c in range(3)], axis=-1)

    @staticmethod
    def tone(e):
        """Hue-preserving tone map of an exposure: (rgb 0..255 float, level 0..1 of the brightest channel)."""
        m = e.max(-1, keepdims=True)
        lvl = np.power(1.0 - np.exp(-m), GLOW_GAMMA)
        col = e * (lvl / np.maximum(m, 1e-6))
        wm = WHITE_MIX * np.clip((m - WHITE_M0) / WHITE_M0, 0, 1)
        return 255.0 * (col + (lvl - col) * wm), lvl

    def image(self, a, gains, fv=None, size=None):
        """Base cloud + tone-mapped activity + bloom, then the FlyVis display layer fv = (pixel index at BR_SS res,
        weight 0..1) alpha-blended on top in its own colour (never added to the spikes); area-downscaled to `size`
        (w, h; default the panel)."""
        img = self.bg.copy()
        e = self.exposure(a, gains)
        if e is not None:
            col, lvl = self.tone(e)
            bright = col * np.clip((lvl - BLOOM_FROM) / (1 - BLOOM_FROM), 0, 1)
            img = img * (1.0 - lvl) + col + BLOOM_W * cv2.GaussianBlur(bright, (0, 0), BLOOM_SIGMA * BR_SS)
        if fv is not None:
            lin, w = fv
            acc = np.bincount(lin, weights=w, minlength=self.W2 * self.H2).reshape(self.H2, self.W2)
            acc = cv2.GaussianBlur(acc.astype(np.float32), (0, 0), 1.2 * BR_SS) * BR_SS ** 2
            al = (FV_ALPHA * (1.0 - np.exp(-acc / FV_SAT)))[..., None]
            img = img * (1.0 - al) + np.array(FV_RGB, np.float32) * al
        size = size or (self.w, self.h)
        img = cv2.resize(np.clip(img, 0, 255), size, interpolation=cv2.INTER_AREA)
        return np.clip(np.round(img), 0, 255).astype(np.uint8)


class BrainPanels:
    def __init__(self):
        cen = np.load(DATA / "neuron_arbor_centroids.npz")
        cls = np.load(DATA / "neuron_class.npz")
        npl = np.load(DATA / "neuron_neuropil.npz")
        xyz = cen["xyz"].astype(np.float64) / 1e3                                  # um
        labels = [str(s) for s in cls["labels"]]
        self.cls = cls["cls"]
        self.labels = labels
        rgb = np.array([CLASS_RGB[lab] for lab in labels], np.float32)[self.cls]
        lo, hi = xyz.min(0), xyz.max(0)
        self.pw, self.ph = 690, BRAIN_H - 34                                       # one projection
        s = min((self.pw - 20) / (hi[0] - lo[0]), (self.ph - 10) / (hi[1] - lo[1]))
        self.scale = s
        ox = (self.pw - s * (hi[0] - lo[0])) / 2
        # frontal: seen from the front, fly's left (small x) on the right -> u = hi_x - x; far = posterior (z)
        oyf = (self.ph - s * (hi[1] - lo[1])) / 2
        self.front = BrainView(hi[0] - xyz[:, 0], xyz[:, 1] - lo[1], xyz[:, 2], self.pw, self.ph, s, ox, oyf, rgb,
                               self.cls)
        # dorsal: seen from above, anterior up, fly's left on the left -> u = x - lo_x, v = z (posterior down);
        # far = ventral (y)
        oyt = (self.ph - s * (hi[2] - lo[2])) / 2
        self.top = BrainView(xyz[:, 0] - lo[0], xyz[:, 2] - lo[2], xyz[:, 1], self.pw, self.ph, s, ox, oyt, rgb,
                             self.cls)
        # feeding circuit pointer target (frontal panel px): median position of the taste class (SEZ incl. sugar GRNs)
        tst = self.cls == labels.index("taste")
        self.feed_xy = (float(np.median(self.front.px[tst])), float(np.median(self.front.py[tst])))
        # midline: halfway between the median x of left and right neurons (classification side)
        side = cls["side"]
        xm = 0.5 * (np.median(xyz[side == "L", 0]) + np.median(xyz[side == "R", 0]))
        self.mid_front = ox + s * (hi[0] - xm)
        self.mid_top = ox + s * (xm - lo[0])
        # neuropil rows (per side), for the bars
        names = [str(s_) for s_ in npl["neuropils"]]
        dom, nside = npl["dominant"], npl["side"]
        self.np_idx = []
        for lab, bases in NP_ROWS:
            ids = [names.index(b_) for b_ in bases if b_ in names]
            m = np.isin(dom, ids)
            central = all(not np.any(m & (nside == sd)) for sd in "LR")
            if central:
                self.np_idx.append((lab, True, np.nonzero(m)[0], None))
            else:
                self.np_idx.append((lab, False, np.nonzero(m & (nside == "L"))[0],
                                    np.nonzero(m & (nside == "R"))[0]))
        self.dominant, self.names, self.nside = dom, names, nside


# ── MuJoCo ───────────────────────────────────────────────────────────────────
def add_geom(scn, gtype, size, pos, mat, rgba):
    if scn.ngeom >= scn.maxgeom:
        return
    mujoco.mjv_initGeom(scn.geoms[scn.ngeom], gtype, np.asarray(size, float), np.asarray(pos, float),
                        np.asarray(mat, float).ravel(), np.asarray(rgba, np.float32))
    scn.ngeom += 1


def add_sphere(scn, pos, r, rgba):
    add_geom(scn, mujoco.mjtGeom.mjGEOM_SPHERE, (r, 0, 0), pos, np.eye(3), rgba)


def add_segment(scn, a, b, width, rgba):
    if scn.ngeom >= scn.maxgeom or np.linalg.norm(np.subtract(b, a)) < 1e-6:
        return
    g = scn.geoms[scn.ngeom]
    mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_CAPSULE, np.zeros(3), np.zeros(3), np.eye(3).ravel(),
                        np.asarray(rgba, np.float32))
    mujoco.mjv_connector(g, mujoco.mjtGeom.mjGEOM_CAPSULE, width, np.asarray(a, float), np.asarray(b, float))
    scn.ngeom += 1


def quat_z(deg):
    h = np.radians(deg) / 2
    return np.array([np.cos(h), 0.0, 0.0, np.sin(h)])


def rot_z(deg):
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


class Scene:
    def __init__(self, platform="dark", cam_h=CAM_H, cam_w=CAM_W, arena_hw=None):
        # same food-platform look as the simulation (flight default "dark": uniform dark pillar + top;
        # the eyes inset then shows what FlyVis saw)
        self.body = FlightBody(legs="stand", enable_vision=True, platform=platform)
        m, d = self.body.m, self.body.d
        self.m, self.d = m, d
        name = self.body.fly.name
        self.wing = {s: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{name}/{s}Wing") for s in "LR"}
        self.wing_rest = {s: m.body_quat[self.wing[s]].copy() for s in "LR"}
        self.wing_parent = {s: int(m.body_parentid[self.wing[s]]) for s in "LR"}
        self.wing_geoms = {s: {g for g in range(m.ngeom) if m.geom_bodyid[g] == self.wing[s]} for s in "LR"}
        self.haustellum = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{name}/Haustellum")
        self.haustellum_geom = next(g for g in range(m.ngeom) if m.geom_bodyid[g] == self.haustellum)
        # food drop: bright yellow in the camera views only; the eyes (FlyVis input) keep the simulated colour
        self.food = next(g for g in range(m.ngeom)
                         if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").endswith("viz_food_drop"))
        self.food_rgba = m.geom_rgba[self.food].copy()
        # dark food platform (visible geoms only): mid grey in the camera views
        self.platform = [g for g in range(m.ngeom)
                         if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "").endswith("food_platform")
                         and m.geom_rgba[g, 3] > 0 and np.allclose(m.geom_rgba[g], cfg.PLATFORM_DARK_RGBA)]
        self.platform_rgba = m.geom_rgba[self.platform].copy()
        self.renderer = mujoco.Renderer(m, cam_h, cam_w, max_geom=4000)
        self.renderer_w = mujoco.Renderer(m, *arena_hw, max_geom=4000) if arena_hw else self.renderer
        self.blur_rng = np.random.default_rng(0)        # wing-blur phase jitter (render only, reproducible)
        self.cam_f = mujoco.MjvCamera()
        self.cam_f.type = mujoco.mjtCamera.mjCAMERA_FREE
        self.cam_f.distance, self.cam_f.elevation = 7.0, -32.0
        self.cam_w = mujoco.MjvCamera()
        self.cam_w.type = mujoco.mjtCamera.mjCAMERA_FREE
        self.cam_w.lookat[:] = (215.0, 70.0, 105.0)
        self.cam_w.distance, self.cam_w.azimuth, self.cam_w.elevation = 470.0, 90.0, -30.0
        self.az = None

    def pose(self, qpos, wings_on):
        """Body from qpos; spread wings at mid-stroke (angle 0) when on, folded (rest) when off."""
        m, d = self.m, self.d
        d.qpos[:] = qpos
        d.qvel[:] = 0.0
        for s in "LR":
            m.body_quat[self.wing[s]] = quat_z(0.0) if wings_on else self.wing_rest[s]
        mujoco.mj_forward(m, d)
        th = d.xpos[self.body.thorax].copy()
        R = d.xmat[self.body.thorax].reshape(3, 3)
        head = np.degrees(np.arctan2(R[1, 0], R[0, 0]))
        self.az = head if self.az is None else self.az + 0.2 * (((head - self.az) + 180) % 360 - 180)
        return th

    def wing_blur(self, scn, amp_l, amp_r, freq):
        """Motion blur: every wing geom in the scene (posed at mid-stroke by pose()) is replaced by its
        copies at the stroke angles of one exposure (see module docstring), rotated about the hinge."""
        d = self.d
        # stratified phases: one random offset per copy inside its 1/N slot (the evenly spaced, cos-symmetric
        # phases put pairs of copies on the same angle and leave visible discrete copies at large amplitude)
        u = self.blur_rng.random(WING_BLUR_N)
        phases = 2 * np.pi * min(1.0, freq * WING_EXPOSURE_S) * (np.arange(WING_BLUR_N) + u) / WING_BLUR_N
        n0 = scn.ngeom
        for s, sign, amp in (("L", 1.0, amp_l), ("R", -1.0, amp_r)):
            angs, cnt = np.unique(np.round(0.5 * amp * np.cos(phases), 6), return_counts=True)
            hinge = d.xpos[self.wing[s]].copy()
            Rp = d.xmat[self.wing_parent[s]].reshape(3, 3)
            for i in range(n0):
                g = scn.geoms[i]
                if g.objtype != mujoco.mjtObj.mjOBJ_GEOM or g.objid not in self.wing_geoms[s]:
                    continue
                pos, mat, rgba = g.pos.copy(), g.mat.copy(), g.rgba.copy()
                for j, (a, c) in enumerate(zip(angs, cnt)):
                    if j == 0:
                        h = g                                   # the original becomes the first copy
                    elif scn.ngeom < scn.maxgeom:
                        h = scn.geoms[scn.ngeom]
                        mujoco.mjv_initGeom(h, g.type, g.size, pos, mat.ravel(), rgba)
                        for f in ("dataid", "matid", "category", "objtype", "objid", "segid",
                                  "emission", "specular", "shininess", "reflectance"):
                            setattr(h, f, getattr(g, f))
                        scn.ngeom += 1
                    else:
                        break
                    Rr = Rp @ rot_z(sign * a) @ Rp.T
                    h.pos[:] = hinge + Rr @ (pos - hinge)
                    h.mat[:] = Rr @ mat
                    h.rgba[:] = (*rgba[:3], 1.0 - (1.0 - WING_BLUR_ALPHA) ** c)
                    h.transparent = 1

    def proboscis_marker(self, scn):
        """The FlyGym model has Rostrum/Haustellum bodies but no proboscis joints: while MN9 > 10 Hz a
        render-only orange marker is drawn from the haustellum mesh centre (the body origin lies inside the
        head) towards the food drop, ending 0.1 mm inside its surface (0.15-1.5 mm long)."""
        p0 = self.d.geom_xpos[self.haustellum_geom].copy()
        v = cfg.FOOD_POS - p0
        L = np.linalg.norm(v)
        if L < 1e-6:
            return
        p1 = p0 + v / L * float(np.clip(L - cfg.FOOD_DROP_RADIUS + 0.1, 0.15, min(L, 1.5)))
        add_segment(scn, p0, p1, 0.08, (1.0, 0.55, 0.1, 1.0))
        add_sphere(scn, p1, 0.11, (1.0, 0.55, 0.1, 1.0))

    def update_scene(self, cam, renderer=None):
        m = self.m
        m.geom_rgba[self.food] = FOOD_RENDER_RGBA
        m.geom_rgba[self.platform] = PLATFORM_RENDER_RGBA
        (renderer or self.renderer).update_scene(self.d, camera=cam)
        m.geom_rgba[self.food] = self.food_rgba
        m.geom_rgba[self.platform] = self.platform_rgba

    def fit_arena(self, lo, hi, margin=0.92):
        """Arena camera (azimuth/elevation kept) centred on the box [lo, hi]; distance = smallest that keeps
        all 8 corners inside `margin` of the view frustum."""
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        c = 0.5 * (lo + hi)
        az, el = np.radians(self.cam_w.azimuth), np.radians(self.cam_w.elevation)
        fwd = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
        right = np.cross(fwd, (0, 0, 1.0))
        right /= np.linalg.norm(right)
        up = np.cross(right, fwd)
        ty = np.tan(np.radians(self.m.vis.global_.fovy) / 2) * margin
        tx = ty * self.renderer_w.width / self.renderer_w.height
        corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) - c
        # corner q is visible when |q.right| <= tx (D + q.fwd) and |q.up| <= ty (D + q.fwd)
        dist = max(np.max(np.abs(corners @ right) / tx - corners @ fwd),
                   np.max(np.abs(corners @ up) / ty - corners @ fwd))
        self.cam_w.lookat[:] = c
        self.cam_w.distance = float(dist)

    def render_follow(self, th, wings_on, amp_l, amp_r, freq, proboscis=False, view=None):
        """view = (azimuth offset from the heading, elevation, distance, lookat weight thorax -> haustellum), see
        CAM_VIEWS / FollowCam; None: the former fixed view from behind."""
        az_off, el, dist, hw = view if view is not None else (0.0, -32.0, 7.0, 0.0)
        self.cam_f.lookat[:] = (1.0 - hw) * th + hw * self.d.xpos[self.haustellum]
        self.cam_f.azimuth = self.az + az_off
        self.cam_f.elevation, self.cam_f.distance = el, dist
        self.update_scene(self.cam_f)
        if wings_on:
            self.wing_blur(self.renderer.scene, amp_l, amp_r, freq)
        if proboscis:
            self.proboscis_marker(self.renderer.scene)
        return self.renderer.render().copy()

    def render_arena(self, th, trail, trail_t, t_end):
        self.update_scene(self.cam_w, self.renderer_w)
        scn = self.renderer_w.scene
        cmap = plt.get_cmap("plasma")
        pts = list(trail) + [th]
        tt = list(trail_t) + [trail_t[-1] if len(trail_t) else 0.0]
        for i, (p0, p1, tc) in enumerate(zip(pts[:-1], pts[1:], tt[:-1])):
            c = cmap(0.15 + 0.85 * tc / t_end)
            add_segment(scn, p0, p1, 2.0, (c[0], c[1], c[2], 1.0))
            if i % 8 == 0 and p0[2] > 3.0:          # drop lines: altitude cue
                add_segment(scn, p0, (p0[0], p0[1], 0.2), 0.5, (0.2, 0.2, 0.25, 0.45))
        add_sphere(scn, th, 5.0, (1.0, 0.15, 0.15, 1.0))
        add_sphere(scn, cfg.FOOD_POS + np.array([0, 0, 3.0]), 3.0, (1.0, 0.8, 0.1, 1.0))
        return self.renderer_w.render().copy()

    def eyes(self):
        v = self.body.update_vision()
        ret = self.body.fly.retina
        return [ret.hex_pxls_to_human_readable(v[i].max(-1), color_8bit=True) for i in range(2)]


def frame_schedule(run):
    """Shown frame indices: all frames up to FEED_SLOW_S after feeding onset (x0.25), then every FEED_SKIP-th
    (x1.0 real time). Returns (indices, run time from which playback is fast, or None without feeding)."""
    b = run.b
    n = len(run.rt)
    feed = np.nonzero(b["is_feeding"] > 0)[0]
    if not len(feed):
        return np.arange(n), None
    t_fast = float(b["t"][feed[0]]) + FEED_SLOW_S
    i0 = int(np.searchsorted(run.rt, t_fast - 1e-9))
    return np.r_[np.arange(i0), np.arange(i0, n, FEED_SKIP)], t_fast


def play_label(run, t_fast):
    slow = float(run.meta.get("play_speed", 0.25))
    return f"▶▶ feeding ×{slow * FEED_SKIP:.1f} real time, sped up (before ×{slow:g})"


# ── drawing helpers ──────────────────────────────────────────────────────────
def control_label(run):
    """Persistent on-screen label: hand-made vs. brain in this run (from the HDF5 flags)."""
    fl = run.flags
    extra = [n for n, f_ in (("head", "head_reflex"), ("postures", "postures")) if fl.get(f_)]
    if fl.get("no_brain_steer"):
        if fl.get("hybrid"):
            return ("Navigation, altitude, landing" + "".join(", " + n for n in extra)
                    + ": HAND-MADE · BRAIN: feeding decision (MN9)")
        return ("Navigation: NONE (steering term 0) · Flight programme (no altitude target)"
                + "".join(", " + n for n in extra) + ": HAND-MADE · BRAIN: feeding decision (MN9)")
    if not fl.get("hybrid"):
        return ("Navigation: brain only (DNp15) · HAND-MADE: "
                + ", ".join(json.loads(run.meta.get("hand_made", "[]"))) + " · BRAIN: feeding decision (MN9)")
    hand = "Navigation, altitude, landing: HAND-MADE (odour map)"
    if "DNp15" in (fl.get("ablate_dn") or []):
        return hand + " · BRAIN: feeding decision (MN9); DNp15 ABLATED (steering term constant)"
    return hand + " · BRAIN: feeding decision (MN9) + additional steering term (DNp15)"


def hud_footer(run):
    fl = run.flags
    hand = ("HAND-MADE: navigation, altitude, approach, landing" if fl.get("hybrid") else
            "no HAND-MADE navigation; flight programme hand-made")
    if fl.get("head_reflex"):
        hand += ", head reflex"
    if fl.get("postures"):
        hand += ", leg postures"
    brain = ("BRAIN: MN9 feeding decision only (steering term 0)" if fl.get("no_brain_steer") else
             "BRAIN: DNp15 steering term + MN9 feeding decision")
    return (f"{hand} · {brain} · FLYVIS: looming avoidance term (FlyVis network) · REFLEX: haltere PD "
            "(recorded, not added to the command)" if fl.get("hybrid") else
            f"{hand} · {brain} · REFLEX: haltere PD")


def render_colour_note(run):
    """Card note: colours changed in the camera views only."""
    if run.flags.get("platform_neutral"):
        return "translucent yellow drop = food (render colour only)"
    return ("translucent yellow drop = food · food platform mid grey (both camera render colours only; "
            "the eyes / FlyVis see the dark simulated colour)")


def lerp_rgb(c, level, dim=False):
    c = np.array(matplotlib.colors.to_rgb(c))
    base = np.array([0.13, 0.14, 0.17])
    lv = np.clip(level, 0, 1) * (0.35 if dim else 1.0)
    return tuple(base + (c - base) * (0.28 + 0.72 * lv))


def rel_lum(rgb):
    """WCAG relative luminance of an RGB triple in 0..1."""
    c = np.asarray(rgb, float)
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(c @ (0.2126, 0.7152, 0.0722))


def text_on(fc):
    """White or near-black text, whichever has the higher contrast on the fill fc (>= 4.5:1 either way)."""
    lum = rel_lum(fc)
    return "white" if 1.05 / (lum + 0.05) >= (lum + 0.05) / (rel_lum(BGf) + 0.05) else BGf


def box(ax, x, y, w, h, title, value, level, color, dim=False, dashed=False):
    fc = lerp_rgb(color, level, dim)
    ec = color if not dim else "#555a62"
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=6",
                                fc=fc, ec=ec, lw=2.4 if not dim else 1.2, ls="--" if dashed else "-",
                                alpha=0.55 if dim else 1.0))
    tc = text_on(fc) if not dim else TXT3
    ax.text(x, y + h * 0.17, title, ha="center", va="center", fontsize=MIN_PT, color=tc, weight="bold")
    ax.text(x, y - h * 0.24, value, ha="center", va="center", fontsize=9.6, color=tc, family="monospace")


def arrow(ax, p0, p1, level, color="#d8dde5", dim=False, rad=0.0):
    lw = 1.2 + 5.5 * float(np.clip(level, 0, 1))
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=10 + 2 * lw, lw=lw,
                                 color=color if not dim else "#5a606a", alpha=0.95 if not dim else 0.6,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))


def fmt_hz(v):
    return f"{v:5.1f} Hz" if v < 100 else f"{v:5.0f} Hz"


# ── renderer ─────────────────────────────────────────────────────────────────
class Renderer:
    def __init__(self, run, mode="change", brain_only=None, scene_size=None):
        self.run, self.mode = run, mode
        self.bp = BrainPanels()
        self.state = BrainState(run)
        self.scene = Scene(platform="neutral" if run.flags.get("platform_neutral") else "dark", **(scene_size or {}))
        self.fcam = run.follow_cam()
        self.brain_only = brain_only
        b = run.b
        g = run.groups
        # population rates per step (for box normalisation p95) and per-frame from the fast EMA
        lop = self.bp.names.index("LOP")
        t45 = np.concatenate([g["t45_L"], g["t45_R"]])
        dom, ns = self.bp.dominant, self.bp.nside

        def np_set(base, side=None):
            ids = [self.bp.names.index(x) for x in base]
            m = np.isin(dom, ids)
            if side:
                m &= ns == side
            return np.setdiff1d(np.nonzero(m)[0], t45) if base == ("LOP",) else np.nonzero(m)[0]

        self.vb = run.vbnd is not None and "vbnd_L" in g
        self.pop = {"t45_L": g["t45_L"], "t45_R": g["t45_R"],
                    "LOP_L": np_set(("LOP",), "L"), "LOP_R": np_set(("LOP",), "R"),
                    "orn_L": g["orn_food_L"], "orn_R": g["orn_food_R"],
                    "AL": np_set(("AL",)), "MB": np_set(("MB_CA", "MB_PED", "MB_VL", "MB_ML")),
                    "LH": np_set(("LH",)), "sugar": g["sugar"], "sez": g["sez"]}
        if self.vb:   # boundary layer (driven) -> optic-lobe neuropils without the driven neurons
            vb_all = np.concatenate([g["vbnd_L"], g["vbnd_R"]])
            for s_ in "LR":
                self.pop[f"vbnd_{s_}"] = g[f"vbnd_{s_}"]
                m_ = np.isin(dom, [self.bp.names.index(x) for x in ("LO", "LOP", "ME", "AME")]) & (ns == s_)
                self.pop[f"OL_{s_}"] = np.setdiff1d(np.nonzero(m_)[0], vb_all)
        del lop
        self.pop_ref = {k: max(np.percentile(run.group_step_rates(v), 95), 1.0) if len(v) else 1.0
                        for k, v in self.pop.items()}
        eye_all = [run.eye_drive(k_, s_) for k_ in range(len(b["t"])) for s_ in "LR"]
        self.rec_ref = {"flyvis": max(np.percentile(eye_all, 95), 1.0),
                        "DNp15": max(np.percentile(run.b["dn_readout_rate"][:, run.readout_types.index("DNp15")], 95), 1),
                        "DNa02": max(np.percentile(run.b["dn_readout_rate"][:, run.readout_types.index("DNa02")], 95), 1),
                        "MN9": max(np.percentile(b["mn9_rate"], 95), 10.0),
                        "sugar_in": max(b["sugar_rate_in"].max(), 1.0)}
        self.t_end = float(run.rt[-1])
        self.summary = run.summary()
        self.frames, self.t_fast = frame_schedule(run)
        self.fv_lin = None if run.fv is None else (self.bp.front.lin[run.fv["idx"]], self.bp.top.lin[run.fv["idx"]])
        self.gain = self.calibrate_gain()
        # olfactory class over the closed loop (run t >= 0): how many neurons spiked at all (panel note)
        olf = self.bp.cls == self.bp.labels.index("olfactory")
        m_ = run.spk_t >= run.offset
        self.olf_n, self.olf_active = int(olf.sum()), int(len(np.unique(run.spk_i[m_][olf[run.spk_i[m_]]])))

    def calibrate_gain(self):
        """Fixed display gain per class for the whole run (see BIG_LEVEL): replay the brain state over every
        frame; crowded classes: GAIN_PCT percentile of the class-only exposure (brightest channel, both projections,
        GAIN_SAMPLES evenly spaced frames) -> its level in BIG_LEVEL; small classes: SMALL_X / median intensity of
        their active neurons (a > 0.01, every frame). The state is reset afterwards. Returns gains per class index."""
        st, bp = self.state, self.bp
        nc = len(bp.labels)
        big = [bp.labels.index(c) for c in BIG_LEVEL if c in bp.labels]
        pick = set(np.linspace(0, self.run.rt_len - 1, GAIN_SAMPLES).astype(int).tolist())
        vals = {c: [] for c in big}
        act = {c: [] for c in range(nc) if c not in big}
        for fi in range(self.run.rt_len):
            st.advance(float(self.run.rt[fi]))
            a = st.intensity(self.mode)
            for c in act:
                v = a[bp.cls == c]
                act[c].append(v[v > 0.01])
            if fi in pick:
                for c in big:
                    for view in (bp.front, bp.top):
                        e = view.exposure(a, only=c)
                        if e is not None:
                            v = e.max(-1)
                            vals[c].append(v[v > 1e-3][::5])
        self.state = BrainState(self.run)
        gains = np.ones(nc)
        self.gain_ref = {}
        for c in big:
            ref = float(np.percentile(np.concatenate(vals[c]), GAIN_PCT)) if vals[c] else None
            x_big = -np.log(1.0 - BIG_LEVEL[bp.labels[c]] ** (1.0 / GLOW_GAMMA))   # exposure -> that level
            gains[c] = x_big / ref if ref else 1.0
            self.gain_ref[bp.labels[c]] = ref
        for c, v in act.items():
            v = np.concatenate(v)
            ref = float(np.median(v)) if len(v) else None
            gains[c] = SMALL_X / ref if ref else SMALL_X
            self.gain_ref[bp.labels[c]] = ref
        return gains

    def fv_layer(self, k):
        """FlyVis display weights (0..1) at step k: |a - a0| / run p99, clipped; None without /flyvis."""
        fv = self.run.fv
        if fv is None:
            return None, None
        row = int(fv["row_of"][k])
        if row < 0:
            return None, None
        w = np.clip(fv["absact"][row] / max(fv["p99"], 1e-6), 0, 1).astype(np.float64)
        return (self.fv_lin[0], w), (self.fv_lin[1], w)

    # per-frame quantities ------------------------------------------------------
    def pop_rate(self, key):
        idx = self.pop[key]
        return float(self.state.fast[idx].mean()) if len(idx) else 0.0

    def frame(self, fi):
        run, b = self.run, self.run.b
        t = float(run.rt[fi])
        k = run.step_at(t)
        phase = run.phase(k)
        wings = bool(b["wings_on"][k])
        amp_l, amp_r = float(b["stroke_amp_L"][k]), float(b["stroke_amp_R"][k])
        sc = self.scene
        th = sc.pose(run.qpos[fi], wings)
        img_f = sc.render_follow(th, wings, amp_l, amp_r, float(b["stroke_freq"][k]),
                                 proboscis=bool(b["mn9_rate"][k] > MN9_THR), view=self.fcam.view(t))
        kk = max(k, 1)
        trail = b["pos"][:kk:2]
        img_w = sc.render_arena(th, trail, b["t"][:kk:2], self.t_end)
        eyes = sc.eyes()

        a = self.state.intensity(self.mode)
        canvas = np.empty((H, W, 3), np.uint8)
        canvas[:] = BG
        bp = self.bp
        fv_f, fv_t = self.fv_layer(k)
        canvas[30:30 + bp.ph, 0:bp.pw] = bp.front.image(a, self.gain, fv_f)
        canvas[30:30 + bp.ph, bp.pw:2 * bp.pw] = bp.top.image(a, self.gain, fv_t)
        canvas[CAM_Y0:CAM_Y0 + CAM_H, 0:CAM_W] = img_f
        canvas[CAM_Y0:CAM_Y0 + CAM_H, CAM_W:2 * CAM_W] = img_w
        # eyes inset (bottom-left of arena panel)
        ew, eh = 96, 108
        for j, e in enumerate(eyes):
            small = cv2.resize(e, (ew, eh), interpolation=cv2.INTER_AREA)
            x0 = EYE_X0 + j * (ew + 6)
            y0 = EYE_Y0
            canvas[y0:y0 + eh, x0:x0 + ew] = small[..., None]

        fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
        fig.patch.set_facecolor(BGf)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(canvas, interpolation="nearest")
        ax.set_xlim(0, W)
        ax.set_ylim(H, 0)
        ax.set_axis_off()
        self.draw_brain_labels(ax, t, phase, bool(b["is_feeding"][k]))
        self.draw_neuropils(fig)
        self.draw_circuit(fig, k, t)
        self.draw_cam_labels(ax, k, amp_l, amp_r, ew, eh)
        self.draw_t45(fig, k, ew)
        self.draw_hud(fig, ax, k, t, phase)
        self.draw_speed(ax, t)
        fig.canvas.draw()
        out = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
        plt.close(fig)
        return out

    # panels ------------------------------------------------------------------
    def draw_brain_labels(self, ax, t, phase, feeding=False):
        bp = self.bp
        run = self.run
        title = (f"FlyWire v783 · {run.n:,} LIF neurons · whole brain"
                 + ("   [DEV subnetwork: NOT A RESULT]" if run.meta.get("dev_subnet") else ""))
        ax.text(8, 6, title, color="white", fontsize=12.5, va="top", weight="bold")
        mode = ("change mode: glows if 250 ms rate > baseline (ΔF/F-like; baseline = first 0.5 s, fixed)"
                if self.mode == "change" else "absolute mode: every spike glows")
        ax.text(498, 9, mode + " · τ = 80 ms · dot = synapse centroid",
                color=TXT2, fontsize=9, va="top")
        y0 = 30
        for x0, lab, mid, lr in ((0, "frontal (the fly's left is on the right of the screen)", bp.mid_front, ("R", "L")),
                                 (bp.pw, "dorsal (anterior up)", bp.mid_top, ("L", "R"))):
            ax.plot([x0 + mid, x0 + mid], [y0 + 4, y0 + bp.ph - 4], color="#6a7280", lw=0.8, ls=(0, (4, 4)))
            ax.text(x0 + 8, y0 + 6, lab, color="#e2e6eb", fontsize=9.5, va="top")
            ax.text(x0 + 14, y0 + bp.ph / 2, lr[0], color="#e8e8e8", fontsize=15, weight="bold", va="center")
            ax.text(x0 + bp.pw - 26, y0 + bp.ph / 2, lr[1], color="#e8e8e8", fontsize=15, weight="bold",
                    va="center")
        # class legend
        x = 10
        for lab in self.bp.labels:
            c = np.array(CLASS_RGB[lab]) / 255
            ax.text(x, y0 + bp.ph - 6, "● " + CLASS_LABEL[lab], color=c, fontsize=9.5, va="bottom")
            x += 22 + 8.5 * len(CLASS_LABEL[lab])
        ax.text(x - 4, y0 + bp.ph - 6, "(spikes, simulated)", color=TXT3, fontsize=9.5, va="bottom")
        if run.fv is not None:
            ax.text(x + 128, y0 + bp.ph - 6, f"■ FlyVis (display only, not driven): {run.fv['n_types']} types, "
                    "|a−a0| / p99", color=np.array(FV_RGB) / 255, fontsize=9.5, va="bottom")
        ax.text(bp.pw + bp.pw - 78, y0 + bp.ph - 30, GAIN_NOTE, color=TXT3, fontsize=9.5, va="bottom", ha="right")
        # olfactory input off: the antenna/AL region is marked
        if self.run.flags.get("no_olfaction"):
            ax.text(2 * bp.pw - 40, y0 + 26, f"olfactory: input OFF (--no-olfaction) · near-silent: "
                    f"{self.olf_active} of {self.olf_n:,} neurons spiked in the run", color="#e0a040",
                    fontsize=9.5, ha="right", va="top",
                    bbox=dict(fc=BGf, ec="#e0a040", lw=0.8, alpha=0.85, boxstyle="round,pad=0.25"))
        # feeding circuit pointer (frontal panel), while feeding
        if feeding:
            fx, fy = bp.feed_xy
            parts = [("feeding circuit: ", "white"), ("sugar GRN", FEED_CIRCUIT_COL["sugar GRN"]), (" → ", "white"),
                     ("SEZ", FEED_CIRCUIT_COL["SEZ"]), (" → ", "white"), ("MN9", FEED_CIRCUIT_COL["MN9"])]
            box_ = HPacker(children=[TextArea(tx, textprops=dict(color=c, fontsize=MIN_PT)) for tx, c in parts],
                           pad=0, sep=0)
            ax.add_artist(AnnotationBbox(box_, (fx, y0 + fy + 6), xybox=(12, y0 + bp.ph - 34),
                                         xycoords="data", boxcoords="data", box_alignment=(0, 0.5),
                                         bboxprops=dict(fc="black", ec="none", alpha=0.6, boxstyle="round,pad=0.2"),
                                         arrowprops=dict(arrowstyle="-", color="#c8cfd8", lw=0.6,
                                                         shrinkA=0, shrinkB=6)))

    def draw_neuropils(self, fig):
        x0, x1 = 1392, 1912
        axn = fig.add_axes([x0 / W, 1 - (BRAIN_H - 6) / H, (x1 - x0) / W, (BRAIN_H - 44) / H])
        axn.set_facecolor(BGf)
        rows = self.bp.np_idx
        n = len(rows)
        vmax = 20.0

        def sq(v):
            return np.sqrt(np.clip(v, 0, vmax) / vmax)

        for i, (lab, central, iL, iR) in enumerate(rows):
            y = n - 1 - i
            if central:
                v, v0 = self.state.fast[iL].mean(), self.state.base[iL].mean()
                axn.barh(y, sq(v), left=-sq(v) / 2, height=0.7, color="#f0d060")
                axn.plot([-sq(v0) / 2, sq(v0) / 2], [y, y], color="white", lw=1.6)
                axn.text(1.02, y, f"{v:4.1f}", color="#f0d060", fontsize=MIN_PT, ha="left", va="center",
                         family="monospace")
            else:
                for side, idx, sg, col in (("L", iL, -1, "#3d9bff"), ("R", iR, 1, "#ff9a2e")):
                    v = self.state.fast[idx].mean() if len(idx) else 0.0
                    v0 = self.state.base[idx].mean() if len(idx) else 0.0
                    axn.barh(y, sg * sq(v), height=0.7, color=col, alpha=0.9)
                    axn.plot([sg * sq(v0)] * 2, [y - 0.36, y + 0.36], color="white", lw=1.6)
                    axn.text(sg * 1.02, y, f"{v:4.1f}", color="#d8dde5", fontsize=MIN_PT,
                             ha="left" if sg > 0 else "right", va="center", family="monospace")
            axn.text(-1.28, y, lab + (" (C)" if central else ""), color="#e8e8e8", fontsize=9.5, ha="right", va="center")
        axn.axvline(0, color="#8a8f98", lw=1.1)
        axn.set_ylim(-0.7, n - 0.3)
        axn.set_axis_off()
        axn.set_xlim(-1.62, 1.2)
        fig.text(x0 / W, 1 - 8 / H, "neuropil (dominant; mean Hz, 250 ms; white = baseline, first 0.5 s)",
                 color="white", fontsize=9.5, va="top")
        fig.text(x0 / W + 0.12, 1 - 26 / H, "◀ L        R ▶   (√ scale, 0–20 Hz)", color=TXT2, fontsize=9.5,
                 va="top")

    def draw_circuit(self, fig, k, t):
        run, b = self.run, self.run.b
        axc = fig.add_axes([0, 1 - (CIRC_Y0 + CIRC_H) / H, 1, CIRC_H / H])
        axc.set_xlim(0, W)
        axc.set_ylim(0, CIRC_H)
        axc.set_facecolor((0.07, 0.08, 0.10))
        axc.set_xticks([])
        axc.set_yticks([])
        for s_ in axc.spines.values():
            s_.set_color("#333")
        bw, bh = 140, 44
        yL, yR = 160, 104
        ref = self.pop_ref
        rr = self.rec_ref
        fl = run.flags
        no_steer = bool(fl.get("no_brain_steer"))
        abl = "DNp15" in (fl.get("ablate_dn") or [])
        head = ("NO brain contribution to turning: steering term 0 (--no-brain-steer)" if no_steer else
                "brain contribution to turning: DNp15 ABLATED, constant baseline" if abl else
                "brain contribution to turning: DNp15, BRAIN")
        axc.text(10, 214, f"VISION → STEERING   ({head})", color="white", fontsize=10, weight="bold", va="top")
        if self.vb:
            n_vb = sum(int(run.vbnd["count"][s_].sum()) for s_ in "LR")
            axc.text(250, 196, f"{run.vbnd['n_types']} types, " + f"{n_vb:,} neurons", color="#a9cdf5",
                     fontsize=MIN_PT, ha="center", va="top")
            axc.text(80, 196, "target rate (mean)", color="#a9cdf5", fontsize=MIN_PT, ha="center", va="top")
            axc.text(420, 196, "undriven, simulated", color="#a9cdf5", fontsize=MIN_PT, ha="center", va="top")
        dnp15 = run.readout("DNp15", k)
        dna02 = run.readout("DNa02", k)
        for j, (side, y) in enumerate((("L", yL), ("R", yR))):
            fv = run.eye_drive(k, side)
            if self.vb:
                p1, n1_, p2, n2_ = f"vbnd_{side}", f"boundary {side}", f"OL_{side}", f"LO/LOP/ME {side}"
            else:
                p1, n1_, p2, n2_ = f"t45_{side}", f"T4/T5 {side}", f"LOP_{side}", f"LOP {side}"
            r1, r2 = self.pop_rate(p1), self.pop_rate(p2)
            box(axc, 80, y, bw, bh, f"eye {side} (FlyVis)", fmt_hz(fv), fv / rr["flyvis"], "#3d9bff")
            box(axc, 250, y, bw, bh, n1_, fmt_hz(r1), r1 / ref[p1], "#3d9bff")
            box(axc, 420, y, bw, bh, n2_, fmt_hz(r2), r2 / ref[p2], "#6f6cff")
            box(axc, 600, y, bw, bh, f"DNp15 {side}" + (" (logged)" if no_steer else ""), fmt_hz(dnp15[j]),
                dnp15[j] / rr["DNp15"], "#ff5a3c" if not no_steer else "#d0705f", dashed=no_steer)
            box(axc, 1140, y, 172, bh - 6, f"DNa02 {side} (recorded)", fmt_hz(dna02[j]), dna02[j] / rr["DNa02"],
                "#d0705f", dashed=True)
            arrow(axc, (80 + bw / 2, y), (250 - bw / 2, y), fv / rr["flyvis"])
            arrow(axc, (250 + bw / 2, y), (420 - bw / 2, y), r1 / ref[p1])
            arrow(axc, (420 + bw / 2, y), (600 - bw / 2, y), r2 / ref[p2])
            arrow(axc, (600 + bw / 2, y), (790 - 70, (yL + yR) / 2 + (8 if side == "L" else -8)),
                  dnp15[j] / rr["DNp15"], rad=-0.15 if side == "L" else 0.15, dim=no_steer)
        ym = (yL + yR) / 2
        tb = float(b["turn_brain"][k])
        if no_steer:
            box(axc, 790, ym, 140, 60, "VNC bridge", "steering term 0", 0.0, "#ff5a3c", dim=True)
            axc.text(585, yR - 28, "DNp15: recorded, not in the command", color="#e8b0aa", fontsize=MIN_PT, ha="center",
                     va="top")
        else:
            box(axc, 790, ym, 140, 60, "VNC bridge", f"BRAIN {tb:+.2f}", abs(tb) / 1.0, "#ff5a3c")
        tt = float(b["turn_total"][k])
        amp_l, amp_r = b["stroke_amp_L"][k], b["stroke_amp_R"][k]
        box(axc, 960, ym, 172, 60, "wing turn command",
            f"sum {tt:+.2f}  ΔA {amp_l - amp_r:+.0f}°", abs(tt) / 1.5, "#f0f0f0")
        arrow(axc, (790 + 70, ym), (960 - 86, ym), abs(tb), dim=no_steer)
        axc.text(938, ym - 34, f"HAND-MADE {b['turn_hand'][k]:+.2f}  FLYVIS {b['turn_flyvis'][k]:+.2f}"
                 + ("" if no_steer else f"  BRAIN {tb:+.2f}"), color=TXT2, fontsize=MIN_PT, ha="center", va="top")
        axc.text(1140, yR - 26, "not in the command", color="#e8b0aa", fontsize=MIN_PT, ha="center", va="top")
        # HAND boxes: head reflex (neck joints, eyes turn with the head) and leg posture
        if fl.get("head_reflex"):
            hy = np.degrees(float(b["head_q"][k, 0]))
            box(axc, 790, 47, 172, 34, "head (HAND-MADE)", f"yaw {hy:+5.1f}°", min(abs(hy) / 7.5, 1), TXT2)
        if fl.get("postures"):
            pn = {0: "stand", 1: "flight", 2: "feeding"}.get(int(b["leg_pose"][k]), "?")
            box(axc, 966, 47, 172, 34, "posture (HAND-MADE)", pn, 0.6, TXT2)
        # olfaction (brain input off)
        dim = bool(run.flags.get("no_olfaction"))
        xo = [1300, 1455, 1610, 1765]
        yo = 150
        axc.text(1238, 214, "OLFACTION  ORN → AL → MB / LH", color="white" if not dim else TXT3,
                 fontsize=10, weight="bold", va="top")
        if dim:
            axc.text(1540, 214, "brain odour input OFF (--no-olfaction)", color="#e0a040",
                     fontsize=9.5, va="top", weight="bold")
        orn = 0.5 * (self.pop_rate("orn_L") + self.pop_rate("orn_R"))
        al, mb, lh = self.pop_rate("AL"), self.pop_rate("MB"), self.pop_rate("LH")
        box(axc, xo[0], yo, 140, bh, "ORN (food, L+R)", fmt_hz(orn),
            orn / max(ref["orn_L"], ref["orn_R"]), "#00e1af", dim)
        box(axc, xo[1], yo, 128, bh, "AL", fmt_hz(al), al / ref["AL"], "#00e1af", dim)
        box(axc, xo[2], yo + 12, 118, bh - 8, "MB", fmt_hz(mb), mb / ref["MB"], "#00e1af", dim)
        box(axc, xo[3], yo - 12, 118, bh - 8, "LH", fmt_hz(lh), lh / ref["LH"], "#00e1af", dim)
        arrow(axc, (xo[0] + 70, yo), (xo[1] - 64, yo), orn / max(ref["orn_L"], 1), dim=dim)
        arrow(axc, (xo[1] + 64, yo + 6), (xo[2] - 59, yo + 12), al / ref["AL"], dim=dim)
        arrow(axc, (xo[1] + 64, yo - 6), (xo[3] - 59, yo - 12), al / ref["AL"], dim=dim, rad=0.12)
        # taste -> feeding
        yt = 72
        axc.text(1238, 112, "TASTE → FEEDING   (feeding decision: MN9 > 10 Hz, BRAIN)", color="white",
                 fontsize=10, weight="bold", va="top")
        sug_in = float(b["sugar_rate_in"][k])
        sug = self.pop_rate("sugar")
        sez = self.pop_rate("sez")
        mn9 = float(b["mn9_rate"][k])
        feed = bool(b["is_feeding"][k])
        box(axc, xo[0], yt, 128, bh, "sugar GRN", fmt_hz(sug), sug / ref["sugar"], "#ff69c8")
        box(axc, xo[1], yt, 128, bh, "SEZ", fmt_hz(sez), sez / ref["sez"], "#ff69c8")
        box(axc, xo[2], yt, 118, bh, "MN9", fmt_hz(mn9), mn9 / rr["MN9"], "#ffa000")
        box(axc, xo[3], yt, 118, bh, "feeding", "YES" if feed else "no", 1.0 if feed else 0.0, "#00c8a0")
        arrow(axc, (xo[0] + 64, yt), (xo[1] - 64, yt), sug / ref["sugar"])
        arrow(axc, (xo[1] + 64, yt), (xo[2] - 59, yt), sez / ref["sez"])
        arrow(axc, (xo[2] + 59, yt), (xo[3] - 59, yt), mn9 / rr["MN9"])
        axc.text(xo[0], yt - 30, f"contact input {sug_in:.0f} Hz", color=TXT2, fontsize=MIN_PT, ha="center",
                 va="top")
        axc.text(10, 14, "box brightness = rate / run p95 · arrow width ∝ rate of the source box "
                 "(not a measured flux) · DNp15/DNa02/MN9: the simulation's 50 ms readout · dashed = recorded, "
                 "not in the command", color=TXT3, fontsize=MIN_PT, va="bottom")

    def draw_cam_labels(self, ax, k, amp_l, amp_r, ew, eh):
        b = self.run.b
        ax.text(10, CAM_Y0 + CAM_H - 8, control_label(self.run), color="white", fontsize=10.5, weight="bold",
                va="bottom", bbox=dict(fc="#3a2a10", ec="#ffa000", alpha=0.9, lw=1.0, boxstyle="round,pad=0.35"))
        if b["mn9_rate"][k] > MN9_THR:
            ax.text(10, CAM_Y0 + CAM_H - 40, "orange: proboscis — VISUAL marker (MN9 > 10 Hz; the model has no proboscis joint, "
                    "no physics)", color="#ffa040", fontsize=9, va="bottom", bbox=dict(fc="black", alpha=0.55, lw=0))
        ax.text(10, CAM_Y0 + 8, "follow camera · wings: motion blur (one stroke cycle, recorded amplitude)",
                color="white", fontsize=10, va="top", bbox=dict(fc="black", alpha=0.45, lw=0))
        if b["wings_on"][k]:
            ax.text(10, CAM_Y0 + 32, f"amplitude L {amp_l:5.1f}°  R {amp_r:5.1f}°  f {b['stroke_freq'][k]:4.0f} Hz"
                    "  (blur is visual; forces are stroke-averaged)", color="#dde", fontsize=9, va="top",
                    family="monospace", bbox=dict(fc="black", alpha=0.45, lw=0))
        ax.text(CAM_W + 10, CAM_Y0 + 8, "arena · 3D trail, colour = time (plasma: purple → yellow), vertical lines = altitude · fly = red marker (render)",
                color="white", fontsize=10, va="top", bbox=dict(fc="black", alpha=0.45, lw=0))
        ax.text(EYE_X0, EYE_Y0 - 4, "eyes (FlyGym → FlyVis) left | right", color="white",
                fontsize=MIN_PT, va="bottom", bbox=dict(fc="black", alpha=0.5, lw=0))

    def draw_t45(self, fig, k, ew):
        r = self.run.b["t45_type_rate"][k]                          # (2 sides, 8 types)
        x0 = EYE_X0 + 26
        axt = fig.add_axes([x0 / W, 1 - (EYE_Y0 - 44) / H, 216 / W, 96 / H])
        axt.set_facecolor((0, 0, 0, 0.7))
        xs = np.arange(8)
        axt.bar(xs - 0.2, r[0], width=0.4, color="#3d9bff", label="L")
        axt.bar(xs + 0.2, r[1], width=0.4, color="#ff9a2e", label="R")
        axt.set_xticks(xs)
        axt.set_xticklabels(list("abcdabcd"), fontsize=MIN_PT, color="#d6dbe2")
        axt.axvline(3.5, color="#8a8f98", lw=0.9)
        axt.tick_params(axis="y", labelsize=MIN_PT, colors="#d6dbe2")
        axt.set_ylim(0, max(20.0, float(r.max()) * 1.25))
        axt.set_title("T4 a–d | T5 a–d rate (Hz)", fontsize=MIN_PT, color="white", pad=2,
                      bbox=dict(fc="black", alpha=0.6, lw=0, pad=1.5))
        axt.legend(fontsize=MIN_PT, loc="upper left", frameon=False, labelcolor="white", ncol=2, bbox_to_anchor=(0, 1.0))
        for s_ in axt.spines.values():
            s_.set_color("#6a707a")
        yt = [v for v in axt.get_yticks() if v <= axt.get_ylim()[1]]
        axt.set_yticks(yt)                                            # fixed ticks: the label boxes below persist
        for lab in axt.get_xticklabels() + axt.get_yticklabels():      # readable on the bright arena floor
            lab.set_bbox(dict(fc="black", alpha=0.7, lw=0, pad=0.6))

    def draw_speed(self, ax, t):
        slow = float(self.run.meta.get("play_speed", 0.25))
        if self.t_fast is not None and t >= self.t_fast - 1e-9:
            ax.text(CAM_W - 10, CAM_Y0 + 58, play_label(self.run, self.t_fast), color="black", fontsize=11,
                    weight="bold", ha="right", va="top", bbox=dict(fc="#ffd84a", ec="none", alpha=0.95,
                                                                   boxstyle="round,pad=0.3"))
        else:
            ax.text(CAM_W - 10, CAM_Y0 + 58, f"playback ×{slow:g}", color="white", fontsize=10, ha="right",
                    va="top", bbox=dict(fc="black", alpha=0.45, lw=0))

    def draw_hud(self, fig, ax, k, t, phase):
        run, b = self.run, self.run.b
        p = b["pos"][k]
        txt = (f"t = {t:5.2f} s   phase: {PHASE_LABEL.get(phase, phase)}\n"
               f"speed {b['speed'][k]:5.0f} mm/s   altitude z {p[2]:5.1f} mm\n"
               f"distance to food {b['dist_to_food'][k]:6.1f} mm\n"
               f"turn:  BRAIN {b['turn_brain'][k]:+.2f} HAND-MADE {b['turn_hand'][k]:+.2f}\n"
               f"       FLYVIS {b['turn_flyvis'][k]:+.2f} REFLEX {b['turn_reflex'][k]:+.2f}\n"
               f"MN9 {b['mn9_rate'][k]:5.1f} Hz  feeding {'YES' if b['is_feeding'][k] else 'no'}")
        ax.text(10, HUD_Y0 + 8, txt, color="white", fontsize=9.3, va="top", family="monospace", linespacing=1.3)
        ax.text(10, H - 3, hud_footer(run), color=TXT3, fontsize=MIN_PT, va="bottom")
        tt = b["t"]
        lo = max(t - TRACE_WIN, 0.0)
        m = (tt > lo - 1e-9) & (tt <= t + self.run.dt_dec)
        m[k + 1:] = False
        ts = tt[m]
        specs = [(400, 500, "turn terms (stacked)"), (940, 300, "altitude z (mm)"), (1260, 300, "distance to food (mm)"),
                 (1580, 330, "MN9 (Hz)")]
        axs = []
        for x0, w, title in specs:
            a_ = fig.add_axes([x0 / W, 40 / H, w / W, (H - HUD_Y0 - 62) / H])
            a_.set_facecolor((0.07, 0.08, 0.10))
            a_.set_title(title, fontsize=9.5, color="white", pad=2, loc="left")
            a_.tick_params(labelsize=MIN_PT, colors="#d6dbe2")
            for s_ in a_.spines.values():
                s_.set_color("#6a707a")
            a_.set_xlim(t - TRACE_WIN, t + 0.02)
            # ticks every 0.5 s, none within 0.2 s of either edge (neighbouring panels' labels collided)
            tk = np.arange(np.ceil((t - TRACE_WIN + 0.2) * 2) / 2, t - 0.2 + 1e-9, 0.5)
            a_.set_xticks(tk)
            a_.set_xticklabels([f"{round(v, 1) + 0.0:.1f}" for v in tk])
            axs.append(a_)
        # phase shading
        ph = b["phase"][m]
        for a_ in axs:
            if len(ts):
                edges = np.r_[0, np.nonzero(np.diff(ph))[0] + 1, len(ph)]
                for i0, i1 in zip(edges[:-1], edges[1:]):
                    nm = run.codes.get(int(ph[i0]), "?")
                    a_.axvspan(ts[i0] - self.run.dt_dec, ts[i1 - 1], color=PHASE_COL.get(nm, "#6a707a"), alpha=0.16, lw=0)
        a0 = axs[0]
        if len(ts):
            pos_b = np.zeros(len(ts))
            neg_b = np.zeros(len(ts))
            for term in ("brain", "hand", "flyvis", "reflex"):
                v = b[f"turn_{term}"][m]
                vp, vn = np.clip(v, 0, None), np.clip(v, None, 0)
                a0.bar(ts, vp, bottom=pos_b, width=self.run.dt_dec, color=TERM_COL[term], align="edge", lw=0,
                       label=TERM_LABEL[term])
                a0.bar(ts, vn, bottom=neg_b, width=self.run.dt_dec, color=TERM_COL[term], align="edge", lw=0)
                pos_b += vp
                neg_b += vn
            a0.plot(ts + self.run.dt_dec / 2, b["turn_total"][m], color="white", lw=1.6, label="total")
            axs[1].plot(ts, b["pos"][m, 2], color="#5cc8ff", lw=2.2)
            axs[2].plot(ts, b["dist_to_food"][m], color="#ffd04a", lw=2.2)
            axs[3].plot(ts, b["mn9_rate"][m], color="#ffa000", lw=2.2)
        a0.axhline(0, color="#8a8f98", lw=0.9)
        a0.set_ylim(-2.2, 2.2)
        a0.legend(fontsize=MIN_PT, loc="upper left", ncol=5, frameon=False, labelcolor="white",
                  handlelength=1.0, columnspacing=0.8)
        axs[1].set_ylim(0, 240)
        axs[2].set_ylim(0, max(50.0, float(b["dist_to_food"][m].max()) * 1.1) if len(ts) else 500)
        axs[3].axhline(10.0, color="#ff4d6a", lw=1.4, ls="--")
        axs[3].text(t - TRACE_WIN + 0.03, 11, "threshold 10 Hz", color="#ff9aa8", fontsize=MIN_PT)
        axs[3].set_ylim(0, max(70.0, float(b["mn9_rate"][m].max()) * 1.1) if len(ts) else 70)
        ax.text(1580 + 330 - 4, HUD_Y0 + 4, PHASE_LABEL.get(phase, phase), color=PHASE_COL.get(phase, "#d6dbe2"),
                fontsize=11, weight="bold", ha="right", va="top")

    # cards -------------------------------------------------------------------
    def card(self, lines, title, subtitle=None):
        fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
        fig.patch.set_facecolor(BGf)
        fig.text(0.06, 0.93, title, color="white", fontsize=28, weight="bold", va="top")
        y = 0.84
        if subtitle:
            fig.text(0.06, 0.875, subtitle, color="#e8e8e8", fontsize=17, va="top")
            y = 0.815
        for txt, col, size in lines:
            for part in wrap_card(txt, size):
                fig.text(0.06, y, part, color=col, fontsize=size, va="top")
                y -= 0.0026 * size + 0.013
        fig.canvas.draw()
        out = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
        plt.close(fig)
        return out

    def title_card(self):
        if self.run.flags.get("no_brain_steer"):
            return self.title_card_nat()
        return self.title_card_v1()

    def title_card_nat(self):
        """Naturalness runs (n1/n2): configuration from the HDF5 flags/meta."""
        run = self.run
        fl = run.flags
        hyb = bool(fl.get("hybrid"))
        n_vb = sum(int(run.vbnd["count"][s_].sum()) for s_ in "LR") if run.vbnd else 0
        lines = [
            (f"FlyWire v783 connectome · {run.n:,} LIF neurons (Brian2) · whole brain · "
             f"{int(run.meta['n_synapses']):,} connections (pre–post neuron pairs)", "white", 17),
            ("NeuroMechFly / FlyGym MuJoCo body · closed loop, 25 ms decision step", "#e2e6eb", 15),
            (f"run: {run_label(run.path)} · seed {int(run.meta['seed'])} · {len(run.b['t'])} steps "
             f"({len(run.b['t']) * run.dt_dec:.1f} s)", "#e2e6eb", 13),
            ("", "white", 8),
            ("Configuration", "white", 17),
            (f"  vision: ON — FlyVis → boundary layer ({run.vbnd['n_types'] if run.vbnd else '?'} types, "
             + f"{n_vb:,}" + " neurons) → FlyWire (FLYVIS)", "#3d9bff", 15),
            ("  brain odour input: OFF (--no-olfaction; persistent antennal-lobe state, REPORT.md)", "#e0a040", 15),
            ("  steering term (DNp15 → turn): 0 (--no-brain-steer; DNp15 is only recorded)", TERM_COL["brain"], 15),
            ("  feeding decision: MN9 > 10 Hz (BRAIN); input: leg–platform contact → labellar sugar GRNs (HAND-MADE shortcut)", "#ffa000", 15),
            (("  navigation, altitude, approach, landing: HAND-MADE (odour map + position controller)" if hyb else
              "  navigation: NONE · flight programme hand-made, no altitude target"), TXT2, 15),
            ("  head reflex (neck against body angular velocity; the eyes turn with the head): HAND-MADE "
             "(all constants hand-set)"
             if fl.get("head_reflex") else "  head reflex: off", TXT2, 14),
            ("  leg postures (flight / leaning forward to feed, triggered by the MN9 decision): HAND-MADE"
             if fl.get("postures") else "  postures: off", TXT2, 14),
            ("", "white", 8),
            (control_label(run), "white", 14),
            ("Post-hoc additional control (SPEC §3.3d): the pre-registered final result is final_v2a (S1 ✗).",
             TXT3, 12),
            (f"playback ×{float(run.meta.get('play_speed', 0.25)):g}"
             + (f"; from {FEED_SLOW_S:g} s after feeding onset ×"
                f"{float(run.meta.get('play_speed', 0.25)) * FEED_SKIP:.1f} (real time, sped up)"
                if self.t_fast is not None else "")
             + " · wing blur is visual · " + render_colour_note(run), TXT3, 12),
        ]
        return self.card(lines, TITLE, SUBTITLE)

    def end_card_nat(self):
        s = self.summary
        sh = s["share"] or {}
        lines = []
        td = (f"touchdown t = {s['t_td']:.2f} s (step {s['k_td']}), speed {s['v_td']:.1f} mm/s" if s["k_td"] is not None
              else f"NO touchdown · closest to food {s['d_min']:.1f} mm · tower contact {s['tower_contact']} steps")
        lines.append((td, "white", 15))
        if s["t_mn9"] is not None:
            lines.append((f"MN9 first > 10 Hz: t = {s['t_mn9']:.2f} s · feeding {s['n_feed']} steps "
                          f"({s['n_feed'] * self.run.dt_dec:.2f} s), mean MN9 {s['mn9_mean_feed']:.1f} Hz · "
                          f"closest to food {s['d_min']:.1f} mm", "#ffa000", 15))
        else:
            lines.append(("MN9 never crossed the threshold (no feeding)", "#ffa000", 15))
        lines.append((f"S1 {'✓' if s['s1'] else '✗'} ({pen_text(s)}) · S2 {'✓' if s['s2'] else '✗'} (feeding) "
                      "· criteria written before the runs (SPEC §3.3d)", "white", 14))
        if sh and sh.get("n_wings_on"):
            lines.append((f"turn command, Σ|·| shares (wings on, {sh['n_wings_on']} steps): "
                          f"BRAIN {sh['share_brain']:.2f} · HAND-MADE {sh['share_hand']:.2f} · "
                          f"REFLEX {sh['share_reflex']:.2f} · FLYVIS {sh['share_flyvis']:.2f}", "#e2e6eb", 13))
        lines.append(("", "white", 4))
        lines.append(("comparison (seed 3, same measures):", "white", 13))
        for p in comparison_runs(self.run):
            lines.append((run_line(run_label(p), p), "#e2e6eb", 12))
        lines.append(("", "white", 4))
        lines.append(("DNp15 steering readout failed validation (a 12/12, b ✗, c ✗): ablated in the final runs, "
                      "steering term 0 in this run", TERM_COL["brain"], 13))
        lines.append(("olfaction: persistent antennal-lobe state (the network does not decay when inputs are cut), "
                      "off in the final runs", "#e0a040", 13))
        lines.append(("The only behavioural decision that comes from the brain is feeding (MN9); single seed, "
                      "post-hoc, no claim of generality.", TXT3, 12))
        lines.append(("", "white", 4))
        lines += credit_lines()
        return self.card(lines, f"Result — {run_label(self.run.path)}")

    def title_card_v1(self):
        run = self.run
        fl = run.flags
        mode = "hybrid (HAND-MADE + BRAIN + FLYVIS + REFLEX)" if fl.get("hybrid") else "brain only"
        abl = f" · ablation: {', '.join(fl['ablate_dn'])}" if fl.get("ablate_dn") else ""
        lines = [
            (f"FlyWire v783 connectome · {run.n:,} LIF neurons (Brian2) · {int(run.meta['n_synapses']):,} "
             "connections (pre–post neuron pairs)", "white", 17),
            ("NeuroMechFly / FlyGym MuJoCo body · closed loop, 25 ms decision step", "#e2e6eb", 15),
            (f"run: {run.path.stem.replace('_data', '')} · seed {int(run.meta['seed'])} · {mode}{abl}", "#e2e6eb", 13),
            ("", "white", 8),
            (("Navigation, altitude, approach and landing: HAND-MADE" if fl.get("hybrid") else
              "no HAND-MADE navigation; other hand-made parts: " + ", ".join(json.loads(run.meta.get("hand_made", "[]")))),
             TXT2, 16 if fl.get("hybrid") else 13),
            ("Brain contribution to turning: DNp15 L/R difference → yaw term (BRAIN; readout chosen post-hoc)"
             + (" — ABLATED in this run: constant perch baseline" if "DNp15" in (fl.get("ablate_dn") or []) else ""),
             TERM_COL["brain"], 16),
            ("Feeding decision: MN9 > 10 Hz (BRAIN)", "#ffa000", 16),
            (control_label(run), "white", 14),
            ("Brain odour input OFF (--no-olfaction): ORN/AL boxes dimmed", "#e0a040", 16),
            ("", "white", 8),
            (f"playback speed ×{float(run.meta.get('play_speed', 0.25)):g}"
             + (f"; from {FEED_SLOW_S:g} s after feeding onset ×"
                f"{float(run.meta.get('play_speed', 0.25)) * FEED_SKIP:.1f} (real time, sped up)"
                if self.t_fast is not None else "")
             + " · wing blur is visual (forces are stroke-averaged) · " + render_colour_note(run),
             TXT3, 12),
        ]
        return self.card(lines, TITLE, SUBTITLE)

    def end_card(self):
        if self.run.flags.get("no_brain_steer"):
            return self.end_card_nat()
        s = self.summary
        sh = s["share"] or {}
        fl = self.run.flags
        lines = []
        td = (f"touchdown t = {s['t_td']:.2f} s, speed {s['v_td']:.1f} mm/s" if s["k_td"] is not None
              else "NO touchdown")
        lines.append((td, "white", 15))
        if s["t_mn9"] is not None:
            lines.append((f"MN9 first > 10 Hz: t = {s['t_mn9']:.2f} s · feeding {s['n_feed']} steps "
                          f"({s['n_feed'] * self.run.dt_dec:.2f} s), mean MN9 {s['mn9_mean_feed']:.1f} Hz", "#ffa000", 15))
        else:
            lines.append(("MN9 never crossed the threshold (no feeding)", "#ffa000", 15))
        lines.append((f"pre-registered success: S1 {'✓' if s['s1'] else '✗'} (touchdown without touching a tower; "
                      f"{pen_text(s)}) · S2 {'✓' if s['s2'] else '✗'} (feeding)", "white", 13))
        if sh:
            lines.append(("", "white", 4))
            lines.append((f"turn command, Σ|·| shares of the four terms (wings on, {sh['n_wings_on']} steps): "
                          f"BRAIN {sh['share_brain']:.2f} · HAND-MADE {sh['share_hand']:.2f} · "
                          f"REFLEX {sh['share_reflex']:.2f} · FLYVIS {sh['share_flyvis']:.2f}", TERM_COL["brain"], 16))
            lines.append((f"pre-registered ratio Σ|BRAIN| / Σ|total| = {sh['brain_over_total']:.2f}; the terms partly "
                          "cancel, so this is not a share", TXT3, 12))
            if fl.get("ablate_dn"):
                lines.append(("in this run the BRAIN term is the constant perch baseline (DNp15 ablation), not 0",
                              TXT3, 12))
            if fl.get("hybrid"):
                lines.append(("collective, altitude, body pitch and landing: brain share 0 by definition (HAND-MADE)",
                              TXT2, 12))
        others = [(lab, p) for lab, p in final_runs().items() if Path(p).resolve() != self.run.path.resolve()]
        if others:
            lines.append(("", "white", 4))
            lines.append(("comparison (same seed, same measures):", "white", 13))
            for lab, p in others:
                lines.append((run_line(lab, p), "#e2e6eb", 12.5))
        elif self.brain_only:
            lines.append(("", "white", 4))
            lines.append((self.brain_only, "#e2e6eb", 13))
        lines.append(("", "white", 4))
        lines.append(("Single seed; no claim of generality.", TXT3, 12))
        lines.append(("", "white", 4))
        lines += credit_lines()
        return self.card(lines, f"Result — {FINAL_LABEL.get(final_key(self.run.path), self.run.path.stem)}")


FINAL_LABEL = {"final_a": "final_a (hybrid)", "final_b": "final_b (hybrid + DNp15 ablation)",
               "final_c": "final_c (brain only)"}
CREDIT = "Synaptera is built on NeuroFly (seven-monarchs), github.com/seven-monarchs/NeuroFly"
CITATIONS = (
    "FlyWire: Dorkenwald et al. 2024, Nature 634:124–138, doi:10.1038/s41586-024-07558-y · "
    "Schlegel et al. 2024, Nature 634:139–152, doi:10.1038/s41586-024-07686-5",
    "LIF model: Shiu et al. 2024, Nature 634:210–219, doi:10.1038/s41586-024-07763-9 · "
    "NeuroMechFly v2 / FlyGym: Wang-Chen et al. 2024, Nature Methods 21:2353–2362, doi:10.1038/s41592-024-02497-y",
    "FlyVis: Lappalainen et al. 2024, Nature 634:1132–1140, doi:10.1038/s41586-024-07939-3 · "
    "FlyWire data: CC BY-NC 4.0 (flywire.ai/guidelines)",
    "Head reflex (n1/n2 only): all constants hand-set (SPEC §3.3d correction note); "
    "related literature: Hengstenberg 1988, J Comp Physiol A 163:151–165",
)


def credit_lines():
    """End-card credits: the upstream project, then the references."""
    return [(CREDIT, TXT2, 12), ("", "white", 3)] + [(c, TXT3, 12) for c in CITATIONS]


RUN_LABEL = {"n1": "n1 (hybrid; steering term 0, head reflex, postures)",
             "n2": "n2 (brain only; steering term 0, head reflex, postures)",
             "final_v2a": "final_v2a (pre-registered final; hybrid, DNp15 ablation)",
             "final_v2c": "final_v2c (pre-registered; brain only, DNp15 ablation)"}


def run_tag(path):
    m = re.search(r"_(n\d|final_v2[abc]|final_[abc]|final_sB)_data\.h5$", Path(path).name)
    return m.group(1) if m else None


def run_label(path):
    tag = run_tag(path)
    return RUN_LABEL.get(tag) or FINAL_LABEL.get(tag) or Path(path).stem.replace("_data", "")


def done_h5(log_dir, name):
    done = ROOT / "logs" / log_dir / f"DONE_{name}"
    if done.exists():
        m = re.search(r"^h5=(.+)$", done.read_text(), re.M)
        if m and Path(m.group(1)).exists():
            return m.group(1)
    return None


def comparison_runs(run):
    """End-card comparison rows for a naturalness run: the pre-registered final_v2a, then the other n runs."""
    me = run.path.resolve()
    cand = [done_h5("final_v2", "final_v2a"), done_h5("natural", "n1"), done_h5("natural", "n2")]
    return [p for p in cand if p and Path(p).resolve() != me]


def final_key(path):
    m = re.search(r"final_[abc]", Path(path).name)
    return m.group(0) if m else None


def final_runs():
    """final_a/b/c HDF5 paths from logs/final/DONE_* markers (existing files only)."""
    out = {}
    for lab in ("final_a", "final_b", "final_c"):
        done = ROOT / "logs" / "final" / f"DONE_{lab}"
        if done.exists():
            m = re.search(r"^h5=(.+)$", done.read_text(), re.M)
            if m and Path(m.group(1)).exists():
                out[lab] = m.group(1)
    return out


def wrap_card(txt, size, width=0.88 * W):
    """Split a card line at ' · ' so that it fits `width` px (DejaVu Sans: mean glyph ~0.53 em, measured)."""
    max_c = int(width / (0.53 * size * 100 / 72))
    if len(txt) <= max_c:
        return [txt]
    out, cur = [], ""
    for seg in txt.split(" · "):
        cand = seg if not cur else cur + " · " + seg
        if len(cand) > max_c and cur:
            out.append(cur)
            cur = "    " + seg
        else:
            cur = cand
    return out + [cur]


def pen_text(s):
    return (f"intra-step tower touch: {len(s['pen_steps'])} steps, first {s['pen_steps'][0]} "
            f"(max. {s['pen_max'] * 1e3:.1f} µm)" if s["pen_steps"] else "no tower contact")


def run_line(lab, path):
    r = Run(path)
    s = r.summary()
    r.f.close()
    land = f"touchdown t = {s['t_td']:.2f} s" if s["k_td"] is not None else \
        f"NO touchdown (closest to food {s['d_min']:.0f} mm)"
    feed = f"feeding {s['n_feed']} steps (MN9 > 10 Hz t = {s['t_mn9']:.2f} s)" if s["n_feed"] else "no feeding"
    if s["pen_steps"] or s["tower_contact"]:
        tower = (f"tower: intra-step {len(s['pen_steps'])}" + (f" (first step {s['pen_steps'][0]}, max. "
                                                              f"{s['pen_max'] * 1e3:.1f} µm)" if s["pen_steps"] else "")
                 + (f", end of step {s['tower_contact']}" if s["tower_contact"] else ""))
    else:
        tower = "no tower contact"
    return (f"{FINAL_LABEL.get(lab, lab)}: {land} · {tower} · {feed} · "
            f"S1 {'✓' if s['s1'] else '✗'} S2 {'✓' if s['s2'] else '✗'}")


def brain_only_text(path):
    if not path or not Path(path).exists():
        return None
    r = Run(path)
    s = r.summary()
    reached = s["k_td"] is not None
    n = len(r.b["t"])
    txt = (f"brain-only run ({r.path.stem.replace('_data', '')}, {n} steps, no HAND-MADE navigation): "
           + (f"platform contact t = {s['t_td']:.2f} s" if reached else
              f"did not reach the food (closest {s['d_min']:.0f} mm, final {s['d_end']:.0f} mm)"))
    r.f.close()
    return txt


def default_brain_only():
    done = ROOT / "logs" / "final" / "DONE_final_c"
    if done.exists():
        m = re.search(r"^h5=(.+)$", done.read_text(), re.M)
        if m and Path(m.group(1)).exists():
            return m.group(1)
    old = ROOT / "simulations" / "flight_v10_ablOdor_noOlf_brainonly160_data.h5"
    return str(old) if old.exists() else None


def auto_keyframes(run):
    b = run.b
    s = run.summary()
    k_end = s["k_td"] if s["k_td"] is not None else len(b["t"])
    t_take = float(b["t"][min(4, len(b["t"]) - 1)])
    fly = np.nonzero(b["wings_on"][:k_end] > 0)[0]
    # tower pass: smallest tower clearance while flying before touchdown (in-step touch if any)
    if s["pen_steps"]:
        k_tw = s["pen_steps"][0]
    else:
        k_tw = int(fly[np.argmin(b["min_tower_clearance"][fly])]) if len(fly) else k_end // 2
    kf = [("takeoff", t_take), ("tower", float(b["t"][k_tw]))]
    if s["k_td"] is not None:
        kf.append(("landing", float(b["t"][s["k_td"]]) - 0.5 * run.dt_dec))     # inside the touchdown step
    if s["k_feed"] is not None:
        kf.append(("feeding", float(b["t"][min(s["k_feed"] + 20, len(b["t"]) - 1)])))
    else:
        kf.append(("end", float(run.rt[-1])))
    return kf


def video_writer(out, fps):
    """H.264, yuv420p (plays everywhere), a key frame every second (-g fps, no scene-cut key frames), moov atom
    at the front (+faststart): seeking and streaming without stalls."""
    return imageio.get_writer(str(out), fps=fps, codec="libx264", quality=8, macro_block_size=8,
                              pixelformat="yuv420p",
                              output_params=["-g", str(fps), "-keyint_min", str(fps), "-sc_threshold", "0",
                                             "-movflags", "+faststart"])


# ── side-by-side comparison ──────────────────────────────────────────────────
# per half (960 px): header | follow camera | arena + 3D trail | 3 large status lines + small frontal brain panel
CMP_HEAD, CMP_FOL_H, CMP_AR_H = 52, 520, 270
CMP_BOT = CMP_HEAD + CMP_FOL_H + CMP_AR_H              # 842; bottom strip 238 px
CMP_BR_W, CMP_BR_H = 360, 180
CMP_SCENE = dict(cam_h=CMP_FOL_H, cam_w=W // 2, arena_hw=(CMP_AR_H, W // 2))


def compare_frame(ra, rb, fi, t_fast):
    """1920x1080, one half per run: header (run, time), follow camera (960x520, phase-dependent angle), arena with
    3D trail (960x270, both arena cameras fitted to the joint trajectory box), then phase / distance to food /
    MN9 + feeding in large type and the frontal brain projection (same glow as the full video, 380x190).
    Smallest text 10.5 pt = 14.6 px."""
    t = float(ra.run.rt[fi])
    cw = W // 2
    canvas = np.empty((H, W, 3), np.uint8)
    canvas[:] = BG
    ks = []
    for j, r in enumerate((ra, rb)):
        x0 = j * cw
        run, b, sc = r.run, r.run.b, r.scene
        k = run.step_at(t)
        ks.append(k)
        wings = bool(b["wings_on"][k])
        th = sc.pose(run.qpos[fi], wings)
        canvas[CMP_HEAD:CMP_HEAD + CMP_FOL_H, x0:x0 + cw] = sc.render_follow(
            th, wings, float(b["stroke_amp_L"][k]), float(b["stroke_amp_R"][k]), float(b["stroke_freq"][k]),
            proboscis=bool(b["mn9_rate"][k] > MN9_THR), view=r.fcam.view(t))
        kk = max(k, 1)
        canvas[CMP_HEAD + CMP_FOL_H:CMP_BOT, x0:x0 + cw] = sc.render_arena(th, b["pos"][:kk:2], b["t"][:kk:2],
                                                                           r.t_end)
        fv_f, _ = r.fv_layer(k)
        br = r.bp.front.image(r.state.intensity(r.mode), r.gain, fv_f, size=(CMP_BR_W, CMP_BR_H))
        bx, by = x0 + cw - CMP_BR_W - 12, CMP_BOT + 52
        canvas[by:by + CMP_BR_H, bx:bx + CMP_BR_W] = br
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(BGf)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(canvas, interpolation="nearest")
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.set_axis_off()
    ax.plot([W / 2, W / 2], [0, H], color="#777", lw=2.0)
    slow = float(ra.run.meta.get("play_speed", 0.25))
    fast = t_fast is not None and t >= t_fast - 1e-9
    small = dict(fontsize=10.5, va="top", bbox=dict(fc="black", alpha=0.5, lw=0, boxstyle="round,pad=0.25"))
    for j, (r, k) in enumerate(zip((ra, rb), ks)):
        x0 = j * cw
        run, b = r.run, r.run.b
        ax.text(x0 + 12, CMP_HEAD / 2, run_label(run.path), color="white", fontsize=14, weight="bold",
                va="center")
        ax.text(x0 + cw - 12, CMP_HEAD / 2, f"t = {t:4.2f} s · " + (f"×{slow * FEED_SKIP:.1f} (n1 feeding)" if fast
                                                                     else f"×{slow:g}"),
                color="black" if fast else "white", fontsize=13, ha="right", va="center", weight="bold",
                bbox=dict(fc="#ffd84a" if fast else "#2a2e36", ec="none", alpha=0.95, boxstyle="round,pad=0.3"))
        ax.text(x0 + 10, CMP_HEAD + 8, "follow camera · angle by phase (cruise: rear-side · approach/descent: side · "
                "touchdown/feeding: front-side close-up)", color="white", **small)
        if b["mn9_rate"][k] > MN9_THR:
            ax.text(x0 + 10, CMP_HEAD + 36, "orange: proboscis — VISUAL marker (MN9 > 10 Hz; the model has no proboscis joint)",
                    color="#ffa040", **small)
        ax.text(x0 + 10, CMP_HEAD + CMP_FOL_H - 8, control_label(run).replace(" · BRAIN", "\nBRAIN"), color="white",
                fontsize=11, weight="bold", va="bottom", linespacing=1.4,
                bbox=dict(fc="#3a2a10", ec="#ffa000", alpha=0.9, lw=1.0, boxstyle="round,pad=0.3"))
        ax.text(x0 + cw - 10, CMP_BOT - 8, "arena · 3D trail (colour = time, purple → yellow) · vertical line = altitude · "
                "red = fly", color="white", ha="right", **dict(small, va="bottom"))
        ph = run.phase(k)
        feed = bool(b["is_feeding"][k])
        y = CMP_BOT + 22
        ax.text(x0 + 16, y, f"phase: {PHASE_LABEL.get(ph, ph)}", color=PHASE_COL.get(ph, "#d6dbe2"), fontsize=20,
                weight="bold", va="top")
        ax.text(x0 + 16, y + 70, f"distance to food: {b['dist_to_food'][k]:.1f} mm", color="#ffd04a", fontsize=20,
                va="top")
        ax.text(x0 + 16, y + 140, f"MN9: {b['mn9_rate'][k]:.1f} Hz · feeding: " + ("YES" if feed else "no"),
                color="#00c8a0" if feed else "#ffa000", fontsize=20, weight="bold" if feed else "normal", va="top")
        ax.text(x0 + cw - 12, CMP_BOT + 48, "brain, frontal · glow: 250 ms rate > baseline · τ = 80 ms\n"
                + GAIN_NOTE, color="#e2e6eb", fontsize=10.5,
                va="bottom", ha="right", multialignment="right", linespacing=1.25)
    fig.canvas.draw()
    out = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    plt.close(fig)
    return out


def compare_cards(ra, rb):
    rows = []
    for r in (ra, rb):
        rows.append((run_line(run_label(r.run.path), str(r.run.path)), "#e2e6eb", 13))
    v2a = done_h5("final_v2", "final_v2a")
    title = ra.card([
        ("Comparison: hybrid | brain only", "white", 17),
        ("Same seed (3), same arena, same brain model; the two arms side by side, at the same run time.", "white", 16),
        ("", "white", 8),
        (f"LEFT: {run_label(ra.run.path)}", "white", 16), ("   " + control_label(ra.run), TXT2, 13),
        (f"RIGHT: {run_label(rb.run.path)}", "white", 16), ("   " + control_label(rb.run), TXT2, 13),
        ("", "white", 8),
        ("Shared: vision boundary layer ON (FLYVIS) · brain odour input OFF · steering term 0 (--no-brain-steer)",
         "#3d9bff", 14),
        ("Post-hoc additional control; the pre-registered final result is final_v2a (S1 ✗).", TXT3, 12),
        ("Camera render: " + render_colour_note(ra.run) + " · wing blur is visual · the orange proboscis "
         "marker is visual only (MN9 > 10 Hz; the model has no proboscis joint)", TXT3, 12),
    ], TITLE, SUBTITLE)
    end = ra.card(rows + ([("", "white", 4), (run_line(run_label(v2a), v2a), TXT3, 12)] if v2a else []) + [
        ("", "white", 6),
        ("In the hybrid arm route, altitude and landing are HAND-MADE; the brain-only arm has no steering or "
         "altitude control.", TXT2, 13),
        ("DNp15 steering readout failed validation (a 12/12, b ✗, c ✗): ablated in the final runs, steering term 0 "
         "in these runs", TERM_COL["brain"], 13),
        ("olfaction: persistent antennal-lobe state (the network does not decay when inputs are cut), off in the "
         "final runs", "#e0a040", 13),
        ("The only behavioural decision that comes from the brain is feeding (MN9). Single seed; no claim of "
         "generality.", TXT3, 12),
        ("", "white", 4)] + credit_lines(), "Result — n1 | n2")
    return title, end


def main_compare(args):
    ra = Renderer(Run(args.h5), mode=args.mode, scene_size=CMP_SCENE)
    rb = Renderer(Run(args.compare), mode=args.mode, scene_size=CMP_SCENE)
    assert np.array_equal(ra.run.rt, rb.run.rt), "render clocks differ"
    pos = np.concatenate([ra.run.b["pos"], rb.run.b["pos"]])
    lo, hi = pos.min(0), pos.max(0)
    lo[2] = 0.0                                              # drop lines reach the ground
    for r in (ra, rb):                                       # same arena view on both sides
        r.scene.fit_arena(lo, hi, margin=0.78)             # room for the label above the trail
    frames = ra.frames if args.max_frames is None else ra.frames[:args.max_frames]
    if args.keyframes:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        targets = sorted(int(np.searchsorted(ra.run.rt, float(x) - 1e-9)) for x in args.keyframes.split(","))
        fi = 0
        for ft in targets:
            while fi <= ft:
                ra.state.advance(float(ra.run.rt[fi]))
                rb.state.advance(float(rb.run.rt[fi]))
                fi += 1
            p = out_dir / f"compare_n1_n2_t{ra.run.rt[ft]:.2f}.png"
            imageio.imwrite(p, compare_frame(ra, rb, ft, ra.t_fast))
            print(f"  {p}")
        return
    out = Path(args.out)
    writer = video_writer(out, ra.run.fps)
    title, end = compare_cards(ra, rb)
    for _ in range(int(TITLE_S * ra.run.fps)):
        writer.append_data(title)
    ts = time.time()
    for j, fi in enumerate(frames):
        ra.state.advance(float(ra.run.rt[fi]))
        rb.state.advance(float(rb.run.rt[fi]))
        writer.append_data(compare_frame(ra, rb, fi, ra.t_fast))
        if j % 50 == 0:
            print(f"  frame {j}/{len(frames)} (sim frame {fi})  {(time.time() - ts) / (j + 1):.2f} s/frame", flush=True)
    for _ in range(int(END_S * ra.run.fps)):
        writer.append_data(end)
    writer.close()
    print(f"video written: {out}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("h5")
    ap.add_argument("--out", default=None)
    ap.add_argument("--mode", choices=("change", "absolute"), default="change")
    ap.add_argument("--keyframes", default=None,
                    help="'auto' or comma list of run times (s): write PNGs only, no video")
    ap.add_argument("--cards", action="store_true", help="with --keyframes: also write title/end card PNGs")
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--brain-only-h5", default=None, help="for the end card (default: final_c, else v10)")
    ap.add_argument("--compare", default=None, help="second HDF5: side-by-side video (left = h5, right = this); "
                    "requires --out; with --keyframes: comma list of run times")
    args = ap.parse_args(argv)
    if args.compare:
        return main_compare(args)

    run = Run(args.h5)
    bo = brain_only_text(args.brain_only_h5 or default_brain_only())
    t0 = time.time()
    r = Renderer(run, mode=args.mode, brain_only=bo)
    print(f"setup {time.time() - t0:.1f} s")
    stem = run.path.name.replace("_data.h5", "")

    if args.keyframes:
        kf = auto_keyframes(run) if args.keyframes == "auto" else \
            [(f"t{float(x):.2f}", float(x)) for x in args.keyframes.split(",")]
        out_dir = Path(args.out) if args.out else ROOT / "plots" / "flight" / "v2_keyframes"
        out_dir.mkdir(parents=True, exist_ok=True)
        targets = sorted((int(np.clip(np.searchsorted(run.rt, t - 1e-9), 0, len(run.rt) - 1)), lab) for lab, t in kf)
        t_adv = 0.0
        times = []
        fi = 0
        for f_target, lab in targets:
            ta = time.time()
            while fi <= f_target:
                r.state.advance(float(run.rt[fi]))
                fi += 1
            t_adv += time.time() - ta
            tr = time.time()
            img = r.frame(f_target)
            times.append(time.time() - tr)
            p = out_dir / f"{stem}_{args.mode}_{lab}_t{run.rt[f_target]:.2f}.png"
            imageio.imwrite(p, img)
            print(f"  {p}  render {times[-1]:.2f} s")
        per_adv = t_adv / max(fi, 1)
        if args.cards:
            for nm, img in (("title", r.title_card()), ("end", r.end_card())):
                p = out_dir / f"{stem}_{nm}_card.png"
                imageio.imwrite(p, img)
                print(f"  {p}")
        n_video = len(r.frames)
        est = n_video * (np.mean(times) + per_adv) + 2 * 1.0
        print(f"per frame: render {np.mean(times):.2f} s (+ state update {per_adv * 1e3:.1f} ms); "
              f"full video {n_video} sim frames + {int((TITLE_S + END_S) * run.fps)} card frames "
              f"≈ {est / 60:.1f} min")
        print("summary " + json.dumps(r.summary))
        return

    out = Path(args.out) if args.out else run.path.with_name(stem + f"_v2_{args.mode}.mp4")
    frames = r.frames if args.max_frames is None else r.frames[:args.max_frames]
    nfr = len(frames)
    writer = video_writer(out, run.fps)
    card = r.title_card()
    for _ in range(int(TITLE_S * run.fps)):
        writer.append_data(card)
    del card
    ts = time.time()
    for j, fi in enumerate(frames):
        r.state.advance(float(run.rt[fi]))
        writer.append_data(r.frame(fi))
        if j % 50 == 0:
            el = time.time() - ts
            print(f"  frame {j}/{nfr} (sim frame {fi})  {el / (j + 1):.2f} s/frame", flush=True)
    card = r.end_card()
    for _ in range(int(END_S * run.fps)):
        writer.append_data(card)
    writer.close()
    print(f"video written: {out}")


if __name__ == "__main__":
    main()
