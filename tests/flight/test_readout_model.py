"""Trained route readout (SPEC_SENSORY_INPUTS §3.6): ridge fit, leave-one-flight-out λ, causal filter, clipping, and the
readout-mode rule (the four applied commands equal the clipped readout output; the teacher label is never altered).
Synthetic data; no brain, no body."""
import numpy as np

from flight import config as cfg
from flight import readout_model as RM


def _flights(n_f=5, n=40, d=30, seed=0):
    rng = np.random.default_rng(seed)
    w = rng.normal(size=(d, 4))
    F, Y = [], []
    for _ in range(n_f):
        x = rng.normal(size=(n, d))
        x[:, 3] = 7.0                                   # constant feature
        F.append(x)
        Y.append(x @ w * 0.05 + 0.01 * rng.normal(size=(n, 4)))
    return F, Y


def test_clip_ranges_are_the_command_ranges():
    assert RM.CLIP_LO[0] == -cfg.TURN_BIAS_MAX and RM.CLIP_HI[0] == cfg.TURN_BIAS_MAX
    assert np.allclose(RM.CLIP_LO[1] + 1, cfg.LIFT_FRAC_RANGE[0]) and np.allclose(RM.CLIP_HI[1] + 1, cfg.LIFT_FRAC_RANGE[1])
    assert np.allclose(RM.CLIP_HI[2:], np.radians(20.0)) and np.allclose(RM.CLIP_LO[2:], -np.radians(20.0))


def test_filter_is_causal_exponential():
    r = np.zeros((6, 2))
    r[2] = [4.0, 8.0]
    f = RM.filter_series(r)
    a = RM.FILTER_A
    assert np.allclose(f[:2], 0) and np.allclose(f[2], (1 - a) * r[2]) and np.allclose(f[3], a * f[2])
    assert abs(a - np.exp(-0.25)) < 1e-12


def test_ridge_matches_closed_form_with_unpenalised_intercept():
    F, Y = _flights()
    X, y = np.concatenate(F), np.concatenate(Y)
    mean, inv = RM.standardise_stats(X)
    assert inv[3] == 0.0                                 # constant feature -> 0
    Z = (X - mean) * inv
    w, yb = RM.ridge(Z, y, 10.0)
    assert np.allclose(yb, y.mean(0))
    assert np.allclose((Z.T @ Z + 10.0 * np.eye(Z.shape[1])) @ w, Z.T @ (y - yb))


def test_fit_arm_selects_lambda_and_predicts():
    F, Y = _flights()
    model, tab = RM.fit_arm(F, Y)
    assert set(tab["lam"]) <= set(RM.LAMBDAS) and tab["n_flights"] == 5 and tab["n_const_features"] == 1
    assert (tab["r2"] > 0.5).all()
    pred = RM.predict(model, np.concatenate(F))
    assert pred.shape == (200, 4) and (pred >= RM.CLIP_LO).all() and (pred <= RM.CLIP_HI).all()


def test_lambda_ties_go_to_the_larger_value():
    F = [np.zeros((10, 3)) for _ in range(3)]            # all features constant -> w = 0 for every λ -> identical errors
    Y = [np.arange(10.0)[:, None] * np.ones((1, 4)) * (i + 1) for i in range(3)]
    _, tab = RM.fit_arm(F, Y)
    assert (tab["lam"] == RM.LAMBDAS[-1]).all()


def test_streaming_readout_equals_offline_path():
    F, Y = _flights(3, 30, 20)
    model, _ = RM.fit_arm(F, Y)
    model = dict(model)
    rng = np.random.default_rng(1)
    d = model["W"].shape[0]
    counts = rng.poisson(2.0, size=(25, d))
    offline = RM.predict(model, RM.filter_series(counts / RM.DT))
    ro = RM.RouteReadout.__new__(RM.RouteReadout)
    ro.m, ro.arm, ro.flt, ro.P = model, "real", RM.Filter(d), None
    online = np.array([ro.update(counts=c) for c in counts])
    assert np.allclose(online, offline)


def test_apply_route_rules():
    teacher = (0.3, -0.2, 0.05, -0.01)
    big = np.array([9.0, 9.0, 9.0, -9.0])
    assert RM.apply_route(teacher, None, True) == teacher                       # mode off
    assert RM.apply_route(teacher, big, False) == teacher                       # wings off: teacher
    got = RM.apply_route(teacher, big, True)                                    # mode on: clipped readout output
    assert np.allclose(got, RM.CLIP_HI * np.array([1, 1, 1, 0]) + RM.CLIP_LO * np.array([0, 0, 0, 1]))
    inside = np.array([0.1, 0.2, 0.01, 0.02])
    assert np.allclose(RM.apply_route(teacher, inside, True), inside)
    assert teacher == (0.3, -0.2, 0.05, -0.01) and big[0] == 9.0               # label and readout output untouched


def test_model_roundtrip(tmp_path):
    F, Y = _flights(3, 20, 10)
    model, _ = RM.fit_arm(F, Y)
    p = tmp_path / "m.npz"
    RM.save_model(p, model, "real", dict(a=1))
    m2, arm, meta = RM.load_model(p)
    assert arm == "real" and meta == dict(a=1) and all(np.array_equal(model[k], m2[k]) for k in model)
    assert len(RM.file_sha256(p)) == 64


def test_bypass_matrix_is_fixed_by_seed():
    P = RM.bypass_matrix()
    assert P.shape == (1299, 34121) and abs(P.std() - 1 / np.sqrt(34121)) < 1e-4
    assert np.array_equal(P[:2], RM.bypass_matrix()[:2])
