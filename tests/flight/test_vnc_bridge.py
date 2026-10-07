"""brain-control: VNC bridge (flight/vnc_bridge.py): Step 1 feeding decision, Step 2 yaw readout."""
import numpy as np
import pytest

from flight import config as cfg
from flight import controller as ctl
from flight.readouts import READOUT_TYPES, Readouts
from flight.vnc_bridge import K_STEER, MN9_THRESHOLD_HZ, READOUT_TAU, Bridge, load_reference

DT = 0.025


class _RO:
    n = np.ones((len(READOUT_TYPES), 2), int)

    @staticmethod
    def rates(c, dt):
        return c / dt


def _counts(mn9_hz):
    c = np.zeros((len(READOUT_TYPES), 2))
    c[Readouts.row("MN9")] = mn9_hz * DT
    return c


def test_constants_fixed():
    assert MN9_THRESHOLD_HZ == 10.0 and READOUT_TAU == 0.05   # R0 curve / VARSAYIM (SPEC Step 1)
    assert K_STEER == 1.0                                       # VARSAYIM (SPEC Step 2)


def test_filter_is_first_order():
    br = Bridge(_RO, DT)
    br.set_baseline(np.zeros((len(READOUT_TYPES), 2)))
    _, used = br.update(_counts(40.0))
    np.testing.assert_allclose(br.mn9_rate(used), 40.0 * (1 - np.exp(-DT / READOUT_TAU)))


def test_proboscis_threshold_and_ablation():
    br = Bridge(_RO, DT)
    br.set_baseline(np.zeros((len(READOUT_TYPES), 2)))
    for _ in range(10):
        _, used = br.update(_counts(60.0))
    assert br.proboscis(used)["proboscis_extended"] == 1
    for _ in range(20):
        _, used = br.update(_counts(0.0))
    assert br.proboscis(used)["proboscis_extended"] == 0
    abl = Bridge(_RO, DT, ablate=("mn9",))
    abl.set_baseline(np.zeros((len(READOUT_TYPES), 2)))       # perch MN9 = 0
    for _ in range(10):
        raw, used = abl.update(_counts(60.0))
    assert abl.proboscis(used)["proboscis_extended"] == 0 and raw[Readouts.row("MN9")].mean() == 60.0


def test_phase_machine_landed_mode():
    pm = ctl.PhaseMachine(DT)
    for _ in range(12):
        pm.update(0.0, 0)
    assert pm.phase == "cruise"
    for _ in range(3):
        pm.update(0.0, 4)
    for _ in range(40):
        pm.update(0.0, 4)
    assert pm.phase == "landed" and pm.landed and not pm.wings_on
    assert ctl.PhaseMachine(DT, start="landed").landed


def test_cli_ablation_sets():
    from fly_flight_brain_body_simulation import parse_args
    from flight.recorder import output_stem
    assert parse_args([]).ablate_dn == []
    assert parse_args(["--ablate-dn"]).ablate_dn == ["steer"]
    assert parse_args(["--ablate-mn9"]).ablate_dn == ["mn9"]
    assert parse_args(["--ablate-dn", "--ablate-mn9"]).ablate_dn == ["mn9", "steer"]
    assert output_stem(2, ablate_dn=["mn9"], start_on_platform=True) == "flight_v2_ablDN-mn9_onPlat"
    assert output_stem(2, ablate_dn=True) == "flight_v2_ablDN"


# ── Step 2: yaw readout ──────────────────────────────────────────────────────
def _ref():
    ref = np.ones((len(READOUT_TYPES), 2))
    ref[Readouts.row("DNa02")] = (30.0, 10.0)
    ref[Readouts.row("DNp15")] = (15.0, 60.0)
    return ref


def _steer_counts(a02, p15):
    c = np.zeros((len(READOUT_TYPES), 2))
    c[Readouts.row("DNa02")] = np.asarray(a02) * DT
    c[Readouts.row("DNp15")] = np.asarray(p15) * DT
    return c


def _settle(br, c, n=40):
    br.set_baseline(np.zeros((len(READOUT_TYPES), 2)))
    for _ in range(n):
        _, used = br.update(c)
    return br.steer(used)


def test_steer_normalised_left_dn_turns_left():
    """n_t = [(r_L - ref_L) - (r_R - ref_R)] / mean(ref); s_hat = n_DNp15 only (DNa02 recorded);
    DNp15 L > R beyond the reference -> left turn (< 0)."""
    s = _settle(Bridge(_RO, DT, reference=_ref()), _steer_counts((60, 10), (45, 60)))
    np.testing.assert_allclose(s["steer_norm_t"], [(60 - 30 - 0) / 20.0, (45 - 15 - 0) / 37.5], rtol=1e-6)
    np.testing.assert_allclose(s["steer_norm"], 0.8, rtol=1e-6)
    np.testing.assert_allclose(s["turn_dn"], -K_STEER * 0.8, rtol=1e-6)
    np.testing.assert_allclose(s["steer_raw"], [50.0, -15.0], rtol=1e-6)
    # DNa02 does not drive the turn (post-hoc DNp15-only readout)
    s1 = _settle(Bridge(_RO, DT, reference=_ref()), _steer_counts((0, 90), (45, 60)))
    assert s1["turn_dn"] == pytest.approx(s["turn_dn"])
    # the reference response itself gives s_hat = 0; a near-silent side is not amplified
    s0 = _settle(Bridge(_RO, DT, reference=_ref()), _steer_counts((30, 10), (15, 60)))
    assert abs(s0["steer_norm"]) < 1e-6
    s2 = _settle(Bridge(_RO, DT, reference=_ref()), _steer_counts((30, 10), (15, 70)))
    np.testing.assert_allclose(s2["steer_norm"], -10 / 37.5, rtol=1e-6)


def test_swap_flips_and_ablation_holds_baseline():
    c = _steer_counts((60, 10), (45, 60))
    s = _settle(Bridge(_RO, DT, reference=_ref()), c)
    sw = _settle(Bridge(_RO, DT, reference=_ref(), swap=("steer",)), c)
    assert sw["turn_dn"] == pytest.approx(-s["turn_dn"])
    ab = Bridge(_RO, DT, reference=_ref(), ablate=("steer",))
    base = np.zeros((len(READOUT_TYPES), 2))
    base[Readouts.row("DNa02")] = (30.0, 10.0)
    base[Readouts.row("DNp15")] = (15.0, 60.0)
    ab.set_baseline(base)
    for _ in range(20):
        _, used = ab.update(c)
    assert ab.steer(used)["turn_dn"] == pytest.approx(0.0)


def test_turn_clipped_and_zero_reference_rejected(tmp_path):
    import json
    s = _settle(Bridge(_RO, DT, reference=_ref()), _steer_counts((0, 0), (3000, 0)))
    assert s["turn_dn"] == -cfg.TURN_BIAS_MAX
    ref = {t: dict(L=1.0, R=1.0) for t in READOUT_TYPES}
    ref["DNp15"] = dict(L=0.0, R=0.0)
    p = tmp_path / "ref.json"
    p.write_text(json.dumps(dict(rates_hz=ref)))
    with pytest.raises(ValueError):
        load_reference(p)


def test_reference_file():
    """data/dn_lr_reference.json: sym_prog, 3 seeds, Step 2 brain configuration, steering refs > 0."""
    import json
    from flight.vnc_bridge import PATH_DN_REFERENCE
    d = json.load(open(PATH_DN_REFERENCE))
    assert d["seeds"] == [0, 1, 2] and d["brain"]["olfaction"] is False and d["stimulus"].startswith("sym_prog")
    ref = load_reference()
    assert np.all(ref[[Readouts.row(t) for t in ("DNa02", "DNp15")]] > 0)


def test_reference_file_sB():
    """data/dn_lr_reference_sB.json: same sym_prog protocol and seeds, sB input set (boundary layer, no
    olfaction); the T4/T5 reference is kept as a separate file."""
    import json
    from flight.vnc_bridge import PATH_DN_REFERENCE, PATH_DN_REFERENCE_SB
    assert PATH_DN_REFERENCE_SB != PATH_DN_REFERENCE   # a missing file -> FileNotFoundError below -> skipped
    d = json.load(open(PATH_DN_REFERENCE_SB))
    old = json.load(open(PATH_DN_REFERENCE))
    assert d["seeds"] == old["seeds"] == [0, 1, 2] and d["window_s"] == old["window_s"]
    assert d["grating"] == old["grating"] and d["stimulus"].startswith("sym_prog")
    assert d["brain"]["olfaction"] is False and d["brain"]["vision_boundary"] is True
    assert "vision_boundary" not in old["brain"]
    ref = load_reference(PATH_DN_REFERENCE_SB)
    assert np.all(ref[[Readouts.row(t) for t in ("DNa02", "DNp15")]].sum(1) > 0)


def test_cli_dn_reference():
    from fly_flight_brain_body_simulation import parse_args
    assert parse_args([]).dn_reference is None
    assert parse_args(["--dn-reference", "data/dn_lr_reference_sB.json"]).dn_reference == \
        "data/dn_lr_reference_sB.json"


def test_brain_turn_terms_have_no_hand_made_parts():
    tt = ctl.turn_terms_brain(-0.4, 0.4)
    assert tt == dict(turn_bias=-0.4, turn_odor=0.0, turn_dn=-0.4, turn_loom=0.0, dn_lr_delta=0.4)


def test_cli_step2_flags():
    from fly_flight_brain_body_simulation import parse_args
    from flight.recorder import output_stem
    a = parse_args(["--swap-dn-lr", "--platform-neutral", "--spawn-air", "440", "-170", "160", "60"])
    assert a.swap_dn_lr == ["steer"] and a.platform_neutral and a.spawn_air == [440, -170, 160, 60]
    assert output_stem(1, swap_dn=["steer"], platform_neutral=True, spawn_air=[440, -170, 160, 60]) == \
        "flight_v1_swapDN-steer_platNeutral_air440_-170_160_60"


def test_cli_hover_yaw_perturb():
    from fly_flight_brain_body_simulation import parse_args
    from flight.recorder import output_stem
    a = parse_args(["--spawn-air", "440", "-170", "160", "90", "--hover", "--yaw-perturb", "0.5", "-30"])
    assert a.hover and a.yaw_perturb == [0.5, -30.0]
    with pytest.raises(SystemExit):
        parse_args(["--hover"])
    assert output_stem(1, spawn_air=[440, -170, 160, 90], hover=True, yaw_perturb=[0.5, -30]) == \
        "flight_v1_air440_-170_160_90_hover_yawP-30"


def test_platform_azimuth():
    from flight.sensors import platform_azimuth
    cx, cy = cfg.FOOD_PLATFORM[:2]
    assert platform_azimuth((cx, cy - 100, 0), np.pi / 2) == pytest.approx(0.0)
    assert platform_azimuth((cx, cy - 100, 0), 0.0) == pytest.approx(90.0)      # platform on the left
    assert platform_azimuth((cx - 100, cy, 0), np.pi / 2) == pytest.approx(-90.0)
