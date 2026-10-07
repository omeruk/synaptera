"""Fixed VNC bridge: brain readouts (flight/readouts.py) -> motor decisions.

SPEC_BRAIN_CONTROL R5. Constants are fixed once, before behaviour is seen, and
are never tuned on behavioural success. Every one is labelled:
  VARSAYIM  = assumption (literature order of magnitude, no direct measurement)
  HAND-MADE = hand-made

Readout filter (VARSAYIM): per-neuron rates are low-pass filtered across decision
steps with READOUT_TAU = 50 ms (first order, exact discretisation). One DN at
10 Hz gives 0.25 spikes per 25 ms step; without a filter the decision flickers
from single spikes. 50 ms ~ the duration of a flight saccade / proboscis
extension onset; not fitted.

Step 1 — feeding (proboscis extension):
  extended = MN9 rate (mean of the 2 CB0701 neurons, filtered) > MN9_THRESHOLD_HZ.
  Threshold from the R0 curve (v783, Shiu protocol, sugar GRN rate -> MN9 L/R):
  20 Hz -> 0/0, 50 Hz -> 11.2/8.2, 100 Hz -> 59.6/46.8. The GRN transition lies
  between 20 and 50 Hz; the threshold is the MN9 mean at its upper end (50 Hz GRN):
  (11.2 + 8.2)/2 = 9.7 -> 10 Hz. FlyGym has no proboscis joint: the extension is
  recorded (and shown in the video), it has no physical effect.

Step 2 — yaw (turn_bias > 0 = right turn, Phi_L - Phi_R = 2 * TURN_DPHI_DEG * turn_bias):
  n_t   = [(r_L - ref_L) - (r_R - ref_R)] / ((ref_L + ref_R) / 2)   for t in STEER_TYPES (DNa02, DNp15)
  s_hat = n_DNp15                              (STEER_DRIVE; DNa02 is recorded only)
  turn_dn = -K_STEER * s_hat                   (clipped to +-TURN_BIAS_MAX)
  - Readout DNp15 only: POST-HOC choice (user decision, SPEC "Step 2 decisions"): DNp15 was a
    secondary R2 readout; making it the sole readout was decided after the Step 2 data (seeds
    0-2) were seen. Validation uses seeds 3-5 only.
  - Normalisation (VARSAYIM, user decision): each side's reference rate is SUBTRACTED and the
    difference is divided by a common scale, the mean of both sides' references; ref = the
    mirror-symmetric front-to-back grating response (data/dn_lr_reference.json,
    scripts/make_dn_reference.py). The reference stimulus itself gives s_hat = 0. The Step 2
    version divided each side by its own reference (r_L/ref_L - r_R/ref_R), which blew up the
    near-silent right DNa02 (ref 2.5 Hz) into a constant right turn. The raw L-R is recorded.
  - Sign (VARSAYIM, fixed before any run): a DN more active on the left turns the fly
    to the LEFT (ipsilateral), as DNa02 in walking (Rayshubskiy et al.) and HS -> DNp15
    (HS is excited by the ipsilateral front-to-back motion of a rightward body turn, the
    optomotor response turns back = ipsilateral). Hence the minus sign.
  - K_STEER = 1 (VARSAYIM, unchanged): s_hat = 1 (one reference-mean in excess on the left)
    -> Delta Phi = 10 deg, steady yaw ~5 rad/s (config YAW_RATE_PER_TURN). Not fitted.
  - --swap-dn-lr steer: the two side channels are exchanged: s_hat -> -s_hat.
  - --ablate-dn steer: the readout is held at the perch (or hover) baseline (s_hat constant).

Ablation (--ablate-dn <set>): the readout is replaced by its perch-calibration
baseline rate (the brain keeps running; nothing is deleted).
"""
import json
from pathlib import Path

import numpy as np

from flight import config as cfg
from flight.readouts import READOUT_TYPES, STEER_DRIVE, STEER_TYPES, Readouts

PATH_DN_REFERENCE = Path(__file__).resolve().parent.parent / "data" / "dn_lr_reference.json"
# sB input set (--vision-boundary --no-olfaction), same sym_prog protocol (SPEC_SENSORY_INPUTS §3.3)
PATH_DN_REFERENCE_SB = PATH_DN_REFERENCE.with_name("dn_lr_reference_sB.json")
K_STEER = 1.0                # VARSAYIM (see module doc)

READOUT_TAU = 0.050          # s, VARSAYIM (see module doc)
MN9_THRESHOLD_HZ = 10.0      # Hz, from the R0 curve (see module doc)
ABLATION_SETS = {"steer": ("DNa02", "DNp15"), "mn9": ("MN9",), "DNp15": ("DNp15",)}
# "DNp15": the yaw drive only (DNa02 is recorded only, so for the yaw command it equals "steer")


class Bridge:
    def __init__(self, readouts: Readouts, dt, ablate=(), swap=(), reference=None):
        self.ro = readouts
        self.dt = dt
        self.alpha = 1.0 - np.exp(-dt / READOUT_TAU)
        self.filt = np.zeros((len(READOUT_TYPES), 2))
        self.baseline = None          # perch-calibration mean rate (Hz per neuron)
        self.ablate_rows = sorted({Readouts.row(t) for s in ablate for t in ABLATION_SETS[s]})
        self.swap_rows = sorted({Readouts.row(t) for s in swap for t in ABLATION_SETS[s]})
        self.swap_steer = "steer" in swap
        if reference is None:
            reference = load_reference() if PATH_DN_REFERENCE.exists() else None
        self.ref = None if reference is None else np.asarray(reference, float)

    def set_baseline(self, rates):
        self.baseline = np.asarray(rates, float)
        self.filt = self.baseline.copy()

    def update(self, counts):
        """counts: (n_types, 2) spikes in the last step. Returns (raw Hz, filtered Hz used by the bridge)."""
        raw = self.ro.rates(counts, self.dt)
        self.filt += self.alpha * (raw - self.filt)
        used = self.filt.copy()
        if self.ablate_rows:
            used[self.ablate_rows] = self.baseline[self.ablate_rows]
        return raw, used

    # ── Step 1 ──────────────────────────────────────────────────────────────
    @staticmethod
    def mn9_rate(used):
        return float(used[Readouts.row("MN9")].mean())

    def proboscis(self, used):
        r = self.mn9_rate(used)
        return dict(mn9_rate=r, proboscis_extended=int(r > MN9_THRESHOLD_HZ))

    # ── Step 2 ──────────────────────────────────────────────────────────────
    def steer(self, used):
        if self.ref is None:
            raise RuntimeError(f"{PATH_DN_REFERENCE} missing: run scripts/make_dn_reference.py")
        rows = [Readouts.row(t) for t in STEER_TYPES]
        u, ref = used[rows], self.ref[rows]
        norm = steer_norm(u, ref)
        s_hat = float(norm[[STEER_TYPES.index(t) for t in STEER_DRIVE]].mean()) * (-1.0 if self.swap_steer else 1.0)
        turn = float(np.clip(-K_STEER * s_hat, -cfg.TURN_BIAS_MAX, cfg.TURN_BIAS_MAX))
        return dict(steer_raw=u[:, 0] - u[:, 1], steer_norm_t=norm, steer_norm=s_hat, turn_dn=turn)


def steer_norm(u, ref):
    """(n, 2) rates and references (Hz, columns L, R) -> per-type normalised L-R:
    [(r_L - ref_L) - (r_R - ref_R)] / mean(ref_L, ref_R)."""
    return ((u[:, 0] - ref[:, 0]) - (u[:, 1] - ref[:, 1])) / (0.5 * (ref[:, 0] + ref[:, 1]))


def load_reference(path=PATH_DN_REFERENCE):
    """(n_types, 2) reference rates (Hz per neuron) for the steering normalisation."""
    with open(path) as f:
        r = json.load(f)["rates_hz"]
    ref = np.array([[r[t]["L"], r[t]["R"]] for t in READOUT_TYPES])
    rows = [Readouts.row(t) for t in STEER_TYPES]
    if np.any(ref[rows].sum(1) <= 0):
        raise ValueError("steering reference rates are 0 on both sides; normalisation undefined")
    return ref
