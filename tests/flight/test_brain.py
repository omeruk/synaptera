"""Stage 2: brain construction, groups, incremental spike counting.

Full-brain tests are marked slow (run with --runslow; several minutes, a few GB RAM).
"""
import numpy as np
import pandas as pd
import pytest

from flight import groups as G
from flight.recorder import h5_path, output_stem

N_NEURONS = 138_639
N_SYN = 15_091_983
SUM_EXC_X_CONN = 10_496_512


@pytest.fixture(scope="module")
def root_ids():
    return G.load_root_ids()


@pytest.fixture(scope="module")
def groups(root_ids):
    return G.build_groups(root_ids)


def test_completeness_rows(root_ids):
    assert len(root_ids) == N_NEURONS
    assert len(np.unique(root_ids)) == N_NEURONS


def test_group_counts(groups):
    c = G.group_counts(groups)
    assert c["ascending"] == 1736
    assert c["sez"] == 408
    assert c["dn"] == 1299
    assert c["olfactory"] == 2279
    assert c["la_me"] == 8025
    assert (len(groups["dn_L"]), len(groups["dn_R"]), len(groups["dn_C"])) == (645, 646, 8)
    assert (len(groups["vis_L"]), len(groups["vis_R"])) == (4189, 3836)
    assert c["dng02"] == 25
    assert c["steer"] == 4 and all(len(groups[k]) == 2 for k in ("steer_L", "steer_R"))
    assert c["dnp01"] == 2
    # brain-control Step 0 inputs
    assert c["orn_food"] == 298 and len(groups["orn_food_C"]) == 0
    assert (len(groups["orn_food_L"]), len(groups["orn_food_R"])) == (153, 145)
    assert c["sugar"] == 36
    assert (len(groups["t45_L"]), len(groups["t45_R"])) == (5901, 5921)


def test_input_groups_v2(root_ids, groups):
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False).set_index("root_id")
    # food ORNs: exactly the FOOD_GLOMERULI types, side from annotations
    ct = ann["cell_type"].reindex(root_ids[groups["orn_food_L"]])
    assert set(ct) <= {f"ORN_{x}" for x in G.FOOD_GLOMERULI}
    assert (ann["side"].reindex(root_ids[groups["orn_food_R"]]) == "right").all()
    # sugar: all LB3; the 20 Shiu neurons (left) + right homologs
    sug = root_ids[groups["sugar"]]
    assert (ann["cell_type"].reindex(sug) == "LB3").all()
    shiu = [r for r in G.SHIU_SUGAR if r in set(root_ids)]
    assert len(shiu) == 20 and set(shiu) <= set(sug)
    side = ann["side"].reindex(sug)
    assert (side == "left").sum() == 20 and (side == "right").sum() == 16
    # T4/T5: types and hemispheres from the column assignment
    col = G.load_t45_columns().set_index("root_id")
    assert set(col.loc[root_ids[groups["t45_L"]], "hemisphere"]) == {"left"}
    assert set(col.loc[root_ids[groups["t45_R"]], "type"]) == set(G.T45_TYPES)
    # column hemisphere agrees with the annotation side (fly's own side)
    assert (ann["side"].reindex(root_ids[groups["t45_L"]]) == "left").mean() > 0.99
    assert (ann["side"].reindex(root_ids[groups["t45_R"]]) == "right").mean() > 0.99


def test_input_names():
    from flight.brain import input_names
    assert "ascending" not in input_names()
    assert "ascending" in input_names(asc_legacy=True)
    assert input_names("legacy") == G.LEGACY_INPUT_GROUPS
    assert not {"olf_L", "vis_L", "sez"} & set(input_names())


def test_dn_index_is_completeness_row(root_ids, groups):
    comp = pd.read_csv(G.PATH_COMP, index_col=0)
    dn = pd.read_csv(G.PATH_DN)
    rows = np.array([comp.index.get_loc(r) for r in dn["root_id"]])
    np.testing.assert_array_equal(root_ids[rows], dn["root_id"].to_numpy())
    all_dn = np.sort(np.concatenate([groups["dn_L"], groups["dn_R"], groups["dn_C"]]))
    np.testing.assert_array_equal(all_dn, np.sort(rows))
    # DNg02: exactly the 25 DNg02_a..h rows, looked up by root_id
    m = dn["cell_type"].astype(str).str.startswith("DNg02")
    exp = np.sort([comp.index.get_loc(r) for r in dn.loc[m, "root_id"]])
    np.testing.assert_array_equal(np.sort(np.concatenate([groups["dng02_L"], groups["dng02_R"]])), exp)
    assert len(exp) == 25
    # left/right labels agree with the csv
    side = dict(zip(dn["root_id"], dn["side"]))
    assert all(side[root_ids[i]] == "left" for i in groups["dng02_L"])
    assert all(side[root_ids[i]] == "right" for i in groups["steer_R"])


def test_groups_not_slices(groups):
    for name, idx in groups.items():
        if len(idx) < 2:
            continue
        # not neu[:N] and not any contiguous block neu[a:a+N]
        assert not np.array_equal(idx, np.arange(len(idx))), name
        assert not np.array_equal(idx, np.arange(idx[0], idx[0] + len(idx))), name


def test_parquet_indices_match_root_id_mapping(root_ids):
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_ID", "Postsynaptic_ID",
                                               "Presynaptic_Index", "Postsynaptic_Index"])
    assert len(con) == N_SYN
    np.testing.assert_array_equal(root_ids[con["Presynaptic_Index"].to_numpy()], con["Presynaptic_ID"].to_numpy())
    np.testing.assert_array_equal(root_ids[con["Postsynaptic_Index"].to_numpy()], con["Postsynaptic_ID"].to_numpy())


def test_incremental_count_equals_full_history():
    from brian2 import (Hz, ms, mV, Network, NeuronGroup, PoissonGroup, SpikeMonitor,
                        Synapses, prefs, seed)
    from flight.brain import SpikeCounter

    old = prefs.codegen.target
    prefs.codegen.target = "numpy"  # toy net: avoid compilation
    try:
        seed(1)
        n = 60
        neu = NeuronGroup(n, "dv/dt = (-52*mV - v) / (20*ms) : volt", threshold="v > -45*mV",
                          reset="v = -52*mV", method="linear")
        neu.v = -52 * mV
        pg = PoissonGroup(n, rates=np.linspace(5, 300, n) * Hz)
        s = Synapses(pg, neu, on_pre="v += 8*mV")
        s.connect(j="i")
        mon = SpikeMonitor(neu)
        net = Network(neu, pg, s, mon)
        l2g = np.arange(n) * 7 + 3  # pretend-global indices to check the mapping
        ctr = SpikeCounter(mon, n, l2g)
        per_step = []
        for k in range(12):
            if k == 6:
                pg.rates = 50 * Hz
            net.run(25 * ms)
            per_step.append(ctr.update())
        full_i = np.asarray(mon.i[:])
        full_t = np.asarray(mon.t_[:])
        assert len(full_i) > 100
        np.testing.assert_array_equal(ctr.total, np.bincount(full_i, minlength=n))
        np.testing.assert_array_equal(np.sum(per_step, axis=0), ctr.total)
        t, i = ctr.spikes()
        np.testing.assert_array_equal(i, l2g[full_i])
        np.testing.assert_allclose(t, full_t, rtol=1e-6)
        # step k's counts are exactly the spikes in [25k, 25(k+1)) ms
        for k, c in enumerate(per_step):
            m = (full_t >= 0.025 * k - 1e-9) & (full_t < 0.025 * (k + 1) - 1e-9)
            np.testing.assert_array_equal(c, np.bincount(full_i[m], minlength=n))
    finally:
        prefs.codegen.target = old


def test_dev_name_contains_DEV(tmp_path):
    assert "DEV" in output_stem(3, dev_subnet=True)
    assert "DEV" not in output_stem(3)
    p = h5_path(3, sim_dir=tmp_path, dev_subnet=True, ablate_dn=True)
    assert p.name == "flight_v3_DEV_ablDN_data.h5"
    assert h5_path(1, sim_dir=tmp_path, antenna_real=True).name == "flight_v1_antReal_data.h5"


def test_dev_subnet_contains_all_groups(groups):
    from flight.brain import DEV_MIN_SYN, dev_subnet_keep
    assert DEV_MIN_SYN == 10
    keep = dev_subnet_keep(groups, N_NEURONS)             # default: partners >= 10 synapses
    keep_full = dev_subnet_keep(groups, N_NEURONS, min_syn=1)
    for idx in groups.values():
        assert keep[idx].all() and keep_full[idx].all()
    assert keep.sum() == 66_663          # Step 0 (T4/T5, food ORN, sugar groups; Stage 4: 52,798)
    assert keep_full.sum() == 115_923    # Stage 4: 98,266
    assert np.all(keep_full[keep])      # threshold subnet is a subset


@pytest.mark.slow
def test_full_brain_synapses_and_run():
    from brian2 import defaultclock, ms
    from flight.brain import FlightBrain

    b = FlightBrain(dev_subnet=False, seed=0)
    assert b.n == N_NEURONS
    assert len(b.syn) == N_SYN
    w = np.asarray(b.syn.w_[:])
    np.testing.assert_allclose(w.sum(), SUM_EXC_X_CONN * float(b.params["w_syn"]), rtol=1e-9)
    assert float(defaultclock.dt / ms) == pytest.approx(0.1)
    # LIF parameters untouched
    p = b.params
    assert (float(p["v_0"] / 1e-3), float(p["v_th"] / 1e-3), float(p["v_rst"] / 1e-3)) == pytest.approx((-52, -45, -52))
    assert float(p["t_mbr"] / ms) == pytest.approx(20) and float(p["tau"] / ms) == pytest.approx(5)
    assert float(p["t_rfc"] / ms) == pytest.approx(2.2) and float(p["t_dly"] / ms) == pytest.approx(1.8)
    # Poisson targets have rfc = 0, others (incl. the undriven ANs) keep 2.2 ms
    rfc = np.asarray(b.neu.rfc_[:])
    assert np.all(rfc[b.groups["t45_L"]] == 0) and np.all(rfc[b.groups["sugar"]] == 0)
    assert np.isclose(rfc[b.groups["ascending"][0]], 2.2e-3)
    assert np.isclose(rfc[b.groups["dn_L"][0]], 2.2e-3)
    assert "ascending" not in b.inputs
    with pytest.raises(KeyError):
        b.set_rates(ascending=30)
    rates_L = np.zeros(len(b.groups["t45_L"]))
    rates_L[:500] = 100.0
    b.set_rates(orn_food_L=40, orn_food_R=80, t45_L=rates_L, sugar=0)
    c1, per = b.step()
    c2, _ = b.step()
    t, i = b.spikes()
    assert per.shape == (N_NEURONS,) and len(t) == len(i) == b.counter.total.sum()
    assert t.max() < 0.050 + 1e-9
    tot = b.counter.total
    assert tot[b.groups["t45_L"][:500]].sum() > 0 and tot[b.groups["t45_L"][500:]].sum() < tot[b.groups["t45_L"][:500]].sum()
    assert tot[b.groups["orn_food_R"]].sum() > tot[b.groups["orn_food_L"]].sum() > 0
    assert tot[b.groups["sugar"]].sum() == 0


@pytest.mark.slow
def test_dev_subnet_build():
    from flight.brain import FlightBrain

    b = FlightBrain(dev_subnet=True, seed=0)
    assert b.dev_subnet and b.n < N_NEURONS
    assert len(b.syn) < N_SYN
    c, _ = b.step()
    t, i = b.spikes()
    # stored indices are global and inside the kept set
    assert np.isin(i, b.l2g).all()
    assert b.dev_min_syn == 10 and b.n == 66_663


@pytest.mark.slow
def test_sugar_homologs_reproducible():
    """data/sugar_grn_783.csv = select_sugar_homologs() (connectivity kNN, left LOO)."""
    df, loo = G.select_sugar_homologs()
    ref = pd.read_csv(G.PATH_SUGAR)
    assert list(df["root_id"]) == list(ref["root_id"])
    assert loo == dict(tp=19, n_sugar=20, fp=2, n_other=44)


def _cut_rate(b, rates, on_steps=20, off_steps=8):
    """Drive `rates` for on_steps x 25 ms from a fresh net, cut all inputs, return
    the network mean rate (Hz) in the last 100 ms of the cut window (100-200 ms)."""
    from flight.brain import SpikeCounter
    b.net.restore("fresh")
    b.counter = SpikeCounter(b.spk_mon, b.n)
    b.silence_inputs()
    b.set_rates(**rates)
    for _ in range(on_steps):
        b.step()
    b.silence_inputs()
    counts = [b.step()[1] for _ in range(off_steps)]
    return float(np.sum(counts[off_steps // 2:])) / (b.n * 0.025 * (off_steps - off_steps // 2))


@pytest.fixture(scope="module")
def fresh_brain():
    from flight.brain import FlightBrain
    b = FlightBrain(seed=0, verbose=False)
    b.net.store("fresh")
    return b


@pytest.mark.slow
def test_adim0_activity_dies_after_cut_without_odor(fresh_brain):
    """Step 0 test: T4/T5 (60 Hz on a quarter of each eye) and sugar GRNs (100 Hz):
    after the cut the network is < 0.1 Hz within 200 ms."""
    b = fresh_brain
    rL = np.zeros(len(b.groups["t45_L"]))
    rR = np.zeros(len(b.groups["t45_R"]))
    rL[::4] = 60.0
    rR[::4] = 60.0
    assert _cut_rate(b, dict(t45_L=rL, t45_R=rR, sugar=100.0)) < 0.1


@pytest.mark.slow
@pytest.mark.xfail(strict=True, reason="SPEC_BRAIN_CONTROL Step 0 (a): food-odour ORNs at the spontaneous "
                                       "8 Hz ignite the self-sustaining KC state (~3.4 Hz, ~3350 KCs); "
                                       "reported, LIF untouched (user decision 3)")
def test_adim0_activity_dies_after_cut_with_spontaneous_orn(fresh_brain):
    assert _cut_rate(fresh_brain, dict(orn_food_L=8.0, orn_food_R=8.0)) < 0.1


# ── Step 0 decisions: --no-olfaction, --apl-graded ──────────────────────────
def test_no_olfaction_input_names_and_stem():
    from flight.brain import input_names
    assert not any(n.startswith("orn_food") for n in input_names(olfaction=False))
    assert {"t45_L", "t45_R", "sugar"} <= set(input_names(olfaction=False))
    assert output_stem(4, apl_graded=True, no_olfaction=True) == "flight_v4_aplG_noOlf"


def test_no_olfaction_implies_ablate_odor():
    from fly_flight_brain_body_simulation import parse_args
    a = parse_args(["--no-olfaction"])
    assert a.no_olfaction and a.ablate_odor
    assert not parse_args([]).ablate_odor


def test_apl_graded_eqs_only_adds_current():
    from flight.brain import APL_GAIN, apl_graded_eqs, default_params
    e0 = default_params["eqs"]
    e1 = apl_graded_eqs(e0)
    assert "(v_0 - v + g + I_apl) / t_mbr" in e1 and "I_apl : volt" in e1
    assert e1.replace(" + I_apl", "").replace("I_apl : volt\n", "") == e0
    assert APL_GAIN == 2.0          # fixed once from KC sparseness (scripts/diag/a0_apl_gain.py)


def test_apl_kc_indices(root_ids):
    apl, kc = G.apl_kc_indices(root_ids)
    assert len(apl) == 2 and len(kc) == 5177
    assert not np.isin(apl, kc).any()


@pytest.mark.slow
def test_apl_graded_moves_apl_output_only():
    """--apl-graded: APL spike weights -> 0, the same synapses (counts, negative sign) act
    through the graded path; every other weight and the LIF parameters are unchanged."""
    from flight.brain import FlightBrain
    b = FlightBrain(seed=0, verbose=False, apl_graded=True, olfaction=False)
    assert b.n == N_NEURONS and len(b.syn) == N_SYN
    w = np.asarray(b.syn.w_[:])
    si = np.asarray(b.syn.i[:])
    out = np.isin(si, b.apl_idx)
    assert np.all(w[out] == 0)
    w_syn = float(b.params["w_syn"])
    graded = np.asarray(b.net["apl_graded_out"].w_ao_[:])
    assert len(graded) == out.sum() == b.apl_info["n_out_edges"] == 6221
    assert np.all(graded < 0)
    # all weights together (spike + graded) = the parquet sum
    np.testing.assert_allclose((w.sum() + graded.sum()) / w_syn, SUM_EXC_X_CONN, rtol=1e-9)
    assert b.apl_info["n_out_to_kc"] == 5194 and b.apl_info["n_in_kc_edges"] == 5215
    assert not any(k.startswith("orn_food") for k in b.inputs)
    # KC drive -> a_APL > 0 -> I_apl < 0 on KCs; nothing on a non-target
    rates = np.zeros(len(b.groups["t45_L"]))
    b.set_rates(t45_L=rates, sugar=0)
    b.step()
    assert np.all(np.asarray(b.neu.I_apl_[:]) <= 0)


@pytest.fixture(scope="module")
def apl_brain():
    from flight.brain import FlightBrain
    b = FlightBrain(seed=0, verbose=False, apl_graded=True)
    b.net.store("fresh")
    return b


@pytest.mark.slow
def test_apl_graded_kc_sparse_but_state_persists(apl_brain):
    """--apl-graded (gain 2.0): spontaneous food-ORN input (8 Hz) keeps KCs sparse (5-10 %,
    literature odour response), but the self-sustaining state survives the cut; it now lives
    in the antennal lobe (excitatory-signed ALLNs), not in the KCs (SPEC Step 0 decisions)."""
    from flight.brain import SpikeCounter
    b = apl_brain
    b.net.restore("fresh")
    b.counter = SpikeCounter(b.spk_mon, b.n)
    b.silence_inputs()
    b.set_rates(orn_food_L=8.0, orn_food_R=8.0)
    steps = [b.step()[1] for _ in range(40)]
    on = np.sum(steps[10:], axis=0)                      # 250-1000 ms, as a0_apl_gain.py / a0_criteria.py
    assert 0.05 <= (on[b.kc_idx] > 0).mean() <= 0.10
    b.silence_inputs()
    off = [b.step()[1] for _ in range(8)]
    late = np.sum(off[4:], axis=0)
    assert late.sum() / (b.n * 0.1) > 0.1                # criterion (a) still fails
    assert (late[b.kc_idx] > 0).sum() < 1000             # spiking APL: ~3350 KCs


# ── Step 0 decisions II: --nt-modulatory-silent (broad / narrow) ─────────────
def test_nt_silent_lists(root_ids, groups):
    """broad = Codex nt_type DA/SER/OCT or NaN (20,719 simulated neurons), narrow = DA/SER/OCT
    (1,677); the Poisson-input exception is applied in FlightBrain (checked below and slow test)."""
    broad, nb = G.nt_silent_indices(root_ids, "broad")
    narrow, nn = G.nt_silent_indices(root_ids, "narrow")
    assert len(broad) == 20_719 and len(narrow) == 1_677
    assert set(nn) == {"DA", "SER", "OCT"} and "none" in set(nb)
    assert np.isin(narrow, broad).all() and np.all(np.diff(broad) > 0)
    inp = np.concatenate([groups[n] for n in ("orn_food_L", "orn_food_R", "orn_food_C", "sugar", "t45_L", "t45_R")])
    assert np.isin(inp, broad).sum() == 1_347 and np.isin(inp, narrow).sum() == 82
    with pytest.raises(ValueError):
        G.nt_silent_indices(root_ids, "all")


def test_nt_silent_flag_and_stem():
    from fly_flight_brain_body_simulation import parse_args
    assert parse_args([]).nt_modulatory_silent is None
    assert parse_args(["--nt-modulatory-silent"]).nt_modulatory_silent == "broad"
    assert parse_args(["--nt-modulatory-silent", "narrow"]).nt_modulatory_silent == "narrow"
    assert output_stem(3, no_olfaction=True, nt_silent="narrow") == "flight_v3_noOlf_ntS-narrow"


@pytest.mark.slow
@pytest.mark.parametrize("variant,n_neu,n_edges", [("narrow", 1_595, 296_022), ("broad", 19_372, 1_132_146)])
def test_nt_silent_zeroes_outgoing_only(variant, n_neu, n_edges):
    """Outgoing fast weights of the silenced neurons are 0, the synapse list is unchanged,
    Poisson input neurons keep their outgoing weights, everything else is untouched."""
    from flight.brain import FlightBrain
    b = FlightBrain(seed=0, verbose=False, olfaction=False, nt_silent=variant)
    assert len(b.syn) == N_SYN and b.nt_info["n_neurons"] == n_neu and b.nt_info["n_edges"] == n_edges
    si = np.asarray(b.syn.i[:])
    w = np.asarray(b.syn.w_[:])
    sil = np.isin(si, b.nt_silent_idx)
    assert np.all(w[sil] == 0) and sil.sum() == n_edges
    inp = np.concatenate([b.groups[n] for n in ("orn_food_L", "orn_food_R", "sugar", "t45_L", "t45_R")])
    assert not np.isin(b.nt_silent_idx, inp).any()
    assert np.any(w[np.isin(si, inp)] != 0)
    w_syn = float(b.params["w_syn"])
    np.testing.assert_allclose((w.sum() + (b.nt_info["syn_exc"] - b.nt_info["syn_inh"]) * w_syn) / w_syn,
                               SUM_EXC_X_CONN, rtol=1e-9)
