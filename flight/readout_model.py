"""Trained linear route readout (SPEC_SENSORY_INPUTS §3.6, training ladder step 1).

One ridge regression (imitation of the hand-made teacher; no RL, no policy gradient, no backpropagation) maps the
causally filtered, standardised activity of the 1,299 descending neurons (arms T1-real and T1-shuffled) or a fixed random
projection of the boundary-layer rates (arm T1-bypass) to the four route commands turn_hand, thrust_hand, pitch_hand and
roll_hand. Everything here is shared by the fitting script, the replay audit and the closed-loop flight, so all three
see the same numbers.
"""
import hashlib
import json

import numpy as np

from flight import config as cfg
from flight import hybrid as H

DT = 0.025                       # decision step (s)
TAU_FILTER = 0.100               # s, causal exponential filter on the DN rate
FILTER_A = float(np.exp(-DT / TAU_FILTER))
LAMBDAS = (0.1, 1.0, 10.0, 100.0, 1000.0)
STD_MIN = 1e-9                   # a feature with a standard deviation below this is set to 0
COMMANDS = ("turn_hand", "thrust_hand", "pitch_hand", "roll_hand")
N_DN = 1299
N_BND = 17185 + 16936            # boundary-layer neurons L + R
BYPASS_SEED = 902
SHUFFLE_SEED = 901
ARMS = ("real", "shuffled", "bypass")
_TILT = float(np.radians(H.TILT_MAX_DEG))
CLIP_LO = np.array([-cfg.TURN_BIAS_MAX, cfg.LIFT_FRAC_RANGE[0] - 1.0, -_TILT, -_TILT])
CLIP_HI = np.array([cfg.TURN_BIAS_MAX, cfg.LIFT_FRAC_RANGE[1] - 1.0, _TILT, _TILT])


def bypass_matrix():
    """Fixed random projection of the boundary-layer rates (L then R, Hz): entries N(0, 1/34,121), seed 902, float64."""
    rng = np.random.default_rng(BYPASS_SEED)
    return rng.normal(0.0, 1.0 / np.sqrt(N_BND), size=(N_DN, N_BND))


def raw_features(arm, counts=None, vbnd_L=None, vbnd_R=None, P=None):
    """Unfiltered feature vector of one step. real/shuffled: DN spike counts -> Hz. bypass: P @ [L, R] float32 rates."""
    if arm == "bypass":
        v = np.concatenate([np.asarray(vbnd_L, np.float32), np.asarray(vbnd_R, np.float32)]).astype(np.float64)
        return P @ v
    return np.asarray(counts, np.float64) / DT


class Filter:
    """f_k = a f_{k-1} + (1-a) r_k, f = 0 before the first step; one object per flight."""

    def __init__(self, n=N_DN):
        self.f = np.zeros(n)

    def update(self, r):
        self.f = FILTER_A * self.f + (1.0 - FILTER_A) * np.asarray(r, np.float64)
        return self.f


def filter_series(R):
    """Whole-flight filter of a (steps x features) raw-feature array (every recorded step, including calibration and cut)."""
    out = np.zeros_like(R, dtype=np.float64)
    flt = Filter(R.shape[1])
    for i in range(R.shape[0]):
        out[i] = flt.update(R[i])
    return out


def standardise_stats(F):
    mean = F.mean(0)
    std = F.std(0)
    inv = np.where(std < STD_MIN, 0.0, 1.0 / np.maximum(std, STD_MIN))
    return mean, inv


def ridge(X, Y, lam):
    """argmin sum (y - ybar - x w)^2 + lam |w|^2 on already standardised X (intercept ybar, unpenalised), float64."""
    ybar = Y.mean(0)
    w = np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ (Y - ybar))
    return w, ybar


def fit_arm(F_list, Y_list, lambdas=LAMBDAS):
    """F_list / Y_list: per training flight (samples x 1299 filtered features, samples x 4 teacher commands).
    Per output: leave-one-flight-out λ (smallest summed squared held-out error of the UNCLIPPED prediction; ties -> larger λ),
    standardisation recomputed on each fold's training flights; then refit on all flights.
    Returns model dict and the CV table (per command: λ, held-out SSE per λ, CV R2 at the chosen λ)."""
    n_f = len(F_list)
    sse = np.zeros((len(lambdas), 4))
    held = [np.zeros((len(lambdas), len(Y), 4)) for Y in Y_list]
    for h in range(n_f):
        tr = [i for i in range(n_f) if i != h]
        Ftr, Ytr = np.concatenate([F_list[i] for i in tr]), np.concatenate([Y_list[i] for i in tr])
        mean, inv = standardise_stats(Ftr)
        Xtr, Xte = (Ftr - mean) * inv, (F_list[h] - mean) * inv
        for li, lam in enumerate(lambdas):
            w, yb = ridge(Xtr, Ytr, lam)
            held[h][li] = Xte @ w + yb
    for li in range(len(lambdas)):
        sse[li] = sum(((held[h][li] - Y_list[h]) ** 2).sum(0) for h in range(n_f))
    lam_idx = np.zeros(4, int)
    for j in range(4):
        best = sse[:, j].min()
        lam_idx[j] = max(li for li in range(len(lambdas)) if sse[li, j] <= best)   # ties -> the larger λ
    Yall = np.concatenate(Y_list)
    sst = ((Yall - Yall.mean(0)) ** 2).sum(0)
    r2 = np.array([1.0 - sse[lam_idx[j], j] / sst[j] for j in range(4)])
    Fall = np.concatenate(F_list)
    mean, inv = standardise_stats(Fall)
    Xall = (Fall - mean) * inv
    W, B, lam_sel = np.zeros((Xall.shape[1], 4)), np.zeros(4), np.zeros(4)
    for j in range(4):
        lam_sel[j] = lambdas[lam_idx[j]]
        w, yb = ridge(Xall, Yall[:, [j]], lam_sel[j])
        W[:, j], B[j] = w[:, 0], yb[0]
    model = dict(W=W, b=B, mean=mean, inv_std=inv, lam=lam_sel)
    return model, dict(lam=lam_sel, sse=sse, r2=r2, sst=sst, n_samples=len(Yall), n_flights=n_f,
                       n_const_features=int((inv == 0).sum()))


class RouteReadout:
    """Closed-loop readout: update(raw features) -> four clipped route commands. The filter runs on every brain step from the
    first perch step; the command at step k uses the DN counts (or projected rates) of step k."""

    def __init__(self, model, arm):
        self.m, self.arm = model, arm
        self.flt = Filter()
        self.P = bypass_matrix() if arm == "bypass" else None

    def update(self, counts=None, vbnd_L=None, vbnd_R=None):
        f = self.flt.update(raw_features(self.arm, counts, vbnd_L, vbnd_R, self.P))
        return predict(self.m, f[None, :])[0]


def predict(model, F):
    """Clipped route commands (steps x 4) of filtered features F (steps x 1299)."""
    out = ((F - model["mean"]) * model["inv_std"]) @ model["W"] + model["b"]
    return np.clip(out, CLIP_LO, CLIP_HI)


def apply_route(teacher, readout_out, wings_on):
    """Applied commands (turn_hand, thrust_hand, pitch_hand, roll_hand). The teacher label is never altered: with the readout
    off, or outside the wings-on phases, the applied commands ARE the teacher's; otherwise they are the readout output."""
    teacher = tuple(float(x) for x in teacher)
    if readout_out is None or not wings_on:
        return teacher
    return tuple(float(x) for x in np.clip(readout_out, CLIP_LO, CLIP_HI))


def save_model(path, model, arm, meta):
    np.savez(path, W=model["W"], b=model["b"], mean=model["mean"], inv_std=model["inv_std"], lam=model["lam"],
             arm=np.array(arm), meta=np.array(json.dumps(meta)))


def load_model(path):
    z = np.load(path, allow_pickle=False)
    return dict(W=z["W"], b=z["b"], mean=z["mean"], inv_std=z["inv_std"], lam=z["lam"]), str(z["arm"]), json.loads(str(z["meta"]))


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()
