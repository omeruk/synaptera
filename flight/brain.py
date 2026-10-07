"""Brian2 brain for flight: FlyWire v783 LIF network + Poisson sensory inputs.

The recurrent network is built by brain_model/model.py:create_model (unchanged;
LIF parameters, w_syn, delay and 0.1 ms dt as in default_params). Sensory inputs
are PoissonGroups -> Synapses 'v += w_syn*f_poi' (68.75 mV) with the model delay,
and their targets get rfc = 0 as in model.py:poi(). Rates are changed with
`.rates = ...` (no recompilation); a rate may be a scalar or a per-neuron array
(T4/T5 from FlyVis).

Input sets (inputs=...):
  "v2" (default, brain-control Step 0): food-odour ORNs L/R/C, sugar GRNs,
       T4/T5 L/R (per neuron). Ascending only with asc_legacy=True.
       vision_boundary=True (--vision-boundary): vbnd_L/R (34,121 neurons, 32 FlyVis-matched
       types, SPEC_SENSORY_INPUTS §2.1) replace t45_L/R.
  "legacy": the Stage 2-4 inputs (all ANs, all ORNs, LA>ME, all GRNs), kept to
       reproduce R0-R3 (scripts/diag).
       olfaction_full=True (--olfaction-full, Stage A, SPEC_SENSORY_INPUTS §2.2): orn_all_L/R/C (all
       2,275 typed ORNs, 53 glomeruli, per-neuron spontaneous rate; flight/olfaction_full.py)
       replace orn_food_L/R/C.
       leg_grn=True (--leg-grn, SPEC_SENSORY_INPUTS §2.4): leg_sugar (sugar-like leg GRNs by
       connectivity, data/leg_sugar_grn_783.csv), driven on tarsus-food contact.
Only groups that are driven get a PoissonGroup (and rfc = 0).
olfaction=False (--no-olfaction): the food-ORN groups get no PoissonGroup at all
(odour input fully off, also no spontaneous rate), to measure visual steering cleanly.

apl_graded=True (--apl-graded): APL output mechanism only. APL is a non-spiking
neuron with graded, global feedback inhibition of the KCs (Papadopoulou et al.
2011; Lin et al. 2014). Its outgoing synapses (same list, same counts, same
negative NT sign from Connectivity_783.parquet) stop acting on APL spikes and act
instead as a continuous current I_apl on each target:
    I_apl_j = APL_GAIN * sum_APL w_APL->j * a_APL / Hz        (w = signed count * w_syn)
    da_APL/dt = -a_APL / t_mbr,   a_APL += n_KC->APL / (N_KC->APL * t_mbr) per KC spike
i.e. a_APL is the KC->APL-synapse-weighted mean KC rate (Hz), low-pass filtered with
the model's membrane constant t_mbr (input from KCs only, from the same parquet;
delay t_dly). The only new term in the neuron equation is "+ I_apl" (0 for all
non-APL targets); LIF parameters, the synapse list and NT signs are unchanged.
APL_GAIN is fixed once from the KC sparseness target alone (scripts/diag/a0_apl_gain.py).

nt_silent="broad"|"narrow" (--nt-modulatory-silent, default off; SPEC_BRAIN_CONTROL
Step 0 decisions II): a deliberate, flag-only exception to "NT signs unchanged".
Shiu's model treats every NT other than GABA/Glu as fast excitation; DA/SER/OCT are
slow modulators. All outgoing synapses of the neurons whose Codex v783 nt_type is
DA/SER/OCT or missing (broad) / DA/SER/OCT only (narrow)
(data/nt_modulatory_silent_783.csv) get weight 0 on the fast path. Poisson-driven
input neurons (orn_food_L/R/C, sugar, t45_L/R, and ascending with asc_legacy) are
never silenced, in either variant and also with olfaction=False. They stay in the synapse list; the neurons stay in the network (they receive
input and spike). Nothing else changes. Applied after the graded-APL move (APL is
GABA and not in the list). Counts in self.nt_info.

nt_literature=True (--nt-literature, default off; SPEC_SENSORY_INPUTS §3.2c): a second deliberate,
flag-only exception to "NT signs unchanged". The neurons of the cell types with a literature fast
transmitter in data/nt_literature_783.csv (sign_lit != 0; Schlegel et al. 2024 known_nt, scripts/
make_nt_literature.py) get w = |w| * sign_lit on all their outgoing synapses: same synapse list and
counts, only the sign. Other types are untouched. Applied after the graded-APL move (APL is GABA in
the table, so unchanged; its graded-path spike weights stay 0). Excludes nt_silent. Counts in
self.nt_lit_info.

nt_impute=True (--nt-impute, default off; SPEC_SENSORY_INPUTS §3.4b): MODEL VARIANT N1, not the published model.
Only neurons with no Codex nt_type prediction can change; they take the synapse-weighted majority sign of the
non-empty cells of their cell_type (data/nt_impute_783.csv, scripts/make_nt_impute.py). Applied before
nt_literature; nt_impute + nt_literature = variant N2. Counts in self.nt_imp_info. Excludes nt_silent.

Spikes are counted incrementally: after each 25 ms run only the new part of the
SpikeMonitor is read (spk_mon.i[n0:]), never the full history.

--dev-subnet (development only, never reported): all annotated groups plus
their 1-hop pre/post partners connected by >= DEV_MIN_SYN synapses (default 10;
--dev-subnet-full uses every partner, min 1). The parquet is filtered and
re-indexed and the same create_model() builds it. Spikes are always stored
with GLOBAL indices.
"""
import gc
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from flight import groups as G

sys.path.insert(0, str(G.BRAIN_DIR))
from model import create_model, default_params  # noqa: E402  (brain_model/model.py)

from brian2 import Hz, ms, Network, NeuronGroup, PoissonGroup, Synapses, defaultclock  # noqa: E402
from brian2 import seed as brian_seed  # noqa: E402

BRAIN_DT = 0.1 * ms          # must equal the brian2 default used by model.py
DECISION_INTERVAL = 25 * ms  # fixed decision step
DEV_MIN_SYN = 10             # --dev-subnet partner threshold (synapses); --dev-subnet-full: 1
APL_GAIN = 2.0               # --apl-graded: fixed once by scripts/diag/a0_apl_gain.py (food odour 150 Hz ->
                             # 8.5 % of KCs active; target 5-10 %, grid 2**(k/2)); never tuned on behaviour

# Default input rates (Hz) before the controller sets them
LEGACY_RATES = {"ascending": 22.5, "olf_L": 20.0, "olf_R": 20.0, "olf_C": 20.0,
                "vis_L": 20.0, "vis_R": 20.0, "sez": 10.0}
DEFAULT_RATES = LEGACY_RATES   # backwards-compatible name
V2_RATES = {"ascending": 0.0, "orn_food_L": 0.0, "orn_food_R": 0.0, "orn_food_C": 0.0,
            "sugar": 0.0, "t45_L": 0.0, "t45_R": 0.0, "vbnd_L": 0.0, "vbnd_R": 0.0,
            "orn_all_L": 0.0, "orn_all_R": 0.0, "orn_all_C": 0.0, "leg_sugar": 0.0}


def input_names(inputs="v2", asc_legacy=False, olfaction=True, vision_boundary=False, olfaction_full=False,
                leg_grn=False):
    """vision_boundary (--vision-boundary): vbnd_L/R (32 boundary types, flight/vision_boundary.py)
    replace t45_L/R (T4/T5 are part of the boundary layer).
    olfaction_full (--olfaction-full): orn_all_L/R/C (all typed ORNs) replace orn_food_L/R/C.
    leg_grn (--leg-grn): + leg_sugar."""
    if inputs == "legacy":
        return G.LEGACY_INPUT_GROUPS
    if inputs != "v2":
        raise ValueError(inputs)
    names = tuple(n for n in G.INPUT_GROUPS
                  if (asc_legacy or n != "ascending") and (olfaction or not n.startswith("orn_food")))
    if vision_boundary:
        names = tuple(n for n in names if not n.startswith("t45_")) + ("vbnd_L", "vbnd_R")
    if olfaction_full:
        if not olfaction:
            raise ValueError("olfaction_full needs olfaction=True")
        names = tuple(n for n in names if not n.startswith("orn_food")) + ("orn_all_L", "orn_all_R", "orn_all_C")
    if leg_grn:
        names = names + ("leg_sugar",)
    return names


def apl_graded_eqs(eqs):
    """Neuron equations with the graded APL current I_apl added to dv/dt (nothing else changes)."""
    old = "dv/dt = (v_0 - v + g) / t_mbr"
    if old not in eqs:
        raise ValueError("unexpected neuron equations; cannot add I_apl")
    return eqs.replace(old, "dv/dt = (v_0 - v + g + I_apl) / t_mbr") + "I_apl : volt\n"


class SpikeCounter:
    """Incremental spike counting on a brian2 SpikeMonitor.

    update() reads only spikes recorded since the previous call, returns their
    per-neuron counts (length n) and keeps the new (t, global i) as chunks.
    """

    def __init__(self, spk_mon, n, local_to_global=None):
        self.mon = spk_mon
        self.n = n
        self.l2g = local_to_global
        self.n_seen = int(spk_mon.num_spikes)
        self.t_chunks, self.i_chunks = [], []
        self.total = np.zeros(n, dtype=np.int64)

    def update(self):
        n1 = int(self.mon.num_spikes)
        i_new = np.asarray(self.mon.i[self.n_seen:n1], dtype=np.int64)
        t_new = np.asarray(self.mon.t_[self.n_seen:n1], dtype=np.float64)
        self.n_seen = n1
        counts = np.bincount(i_new, minlength=self.n)
        self.total += counts
        gi = i_new if self.l2g is None else self.l2g[i_new]
        self.i_chunks.append(gi.astype(np.int32))
        self.t_chunks.append(t_new.astype(np.float32))
        return counts

    def spikes(self):
        """All counted spikes as (t float32 [s], i int32 global)."""
        if not self.t_chunks:
            return np.zeros(0, np.float32), np.zeros(0, np.int32)
        return np.concatenate(self.t_chunks), np.concatenate(self.i_chunks)


def dev_subnet_keep(groups, n, min_syn=DEV_MIN_SYN, path_con=G.PATH_CON):
    """Boolean mask over global indices: all groups + 1-hop pre/post partners
    connected to a group neuron by >= min_syn synapses."""
    core = np.zeros(n, dtype=bool)
    for idx in groups.values():
        core[idx] = True
    con = pd.read_parquet(path_con, columns=["Presynaptic_Index", "Postsynaptic_Index", "Connectivity"])
    pre = con["Presynaptic_Index"].to_numpy()
    post = con["Postsynaptic_Index"].to_numpy()
    strong = con["Connectivity"].to_numpy() >= min_syn
    del con
    keep = core.copy()
    keep[post[core[pre] & strong]] = True
    keep[pre[core[post] & strong]] = True
    return keep


def write_dev_files(keep, out_dir, path_comp=G.PATH_COMP, path_con=G.PATH_CON):
    """Write a re-indexed Completeness csv + Connectivity parquet for the subnet."""
    out_dir = Path(out_dir)
    comp = pd.read_csv(path_comp, index_col=0)
    comp[keep].to_csv(out_dir / "Completeness_DEV.csv")
    g2l = np.full(len(keep), -1, dtype=np.int64)
    g2l[np.flatnonzero(keep)] = np.arange(int(keep.sum()))
    con = pd.read_parquet(path_con)
    pre = con["Presynaptic_Index"].to_numpy()
    post = con["Postsynaptic_Index"].to_numpy()
    con = con[keep[pre] & keep[post]].copy()
    con["Presynaptic_Index"] = g2l[con["Presynaptic_Index"].to_numpy()]
    con["Postsynaptic_Index"] = g2l[con["Postsynaptic_Index"].to_numpy()]
    con.to_parquet(out_dir / "Connectivity_DEV.parquet")
    return out_dir / "Completeness_DEV.csv", out_dir / "Connectivity_DEV.parquet"


def shuffled_connectome(out_dir, seed, path_con=G.PATH_CON):
    """NULL CONTROL (SPEC_SENSORY_INPUTS §3.4b): write a copy of the connectome in which the Postsynaptic_Index (and _ID) column is
    randomly permuted over all edges. Every edge keeps its presynaptic neuron, weight and sign, so out-degree, out-synapse count and the
    in-degree distribution are preserved; only which neuron is contacted is destroyed. Returns the parquet path."""
    con = pd.read_parquet(path_con)
    perm = np.random.default_rng(seed).permutation(len(con))
    for c in ("Postsynaptic_Index", "Postsynaptic_ID"):
        con[c] = con[c].to_numpy()[perm]
    out = Path(out_dir) / "Connectivity_shuffled.parquet"
    con.to_parquet(out)
    return str(out)


class FlightBrain:
    def __init__(self, dev_subnet=False, dev_min_syn=DEV_MIN_SYN, seed=None, verbose=True,
                 inputs="v2", asc_legacy=False, olfaction=True, apl_graded=False, apl_gain=None,
                 nt_silent=None, vision_boundary=False, olfaction_full=False, leg_grn=False, nt_literature=False,
                 nt_impute=False, shuffle_seed=None):
        log = print if verbose else (lambda *a, **k: None)
        if seed is not None:
            brian_seed(seed)
        defaultclock.dt = BRAIN_DT
        self.params = dict(default_params)
        self.apl_graded = bool(apl_graded)
        if self.apl_graded:
            self.params["eqs"] = apl_graded_eqs(self.params["eqs"])
        self.dev_subnet = bool(dev_subnet)
        self.dev_min_syn = int(dev_min_syn) if self.dev_subnet else None

        self.root_ids = G.load_root_ids()
        self.n_global = len(self.root_ids)
        self.groups = G.build_groups(self.root_ids)          # global indices
        self.vision_boundary = bool(vision_boundary)
        if self.vision_boundary:
            from flight.vision_boundary import boundary_groups
            self.groups.update(boundary_groups(self.root_ids))
        self.olfaction_full = bool(olfaction_full)
        if self.olfaction_full:
            from flight.olfaction_full import orn_groups
            self.groups.update(orn_groups(self.root_ids))
        self.leg_grn = bool(leg_grn)
        if self.leg_grn:
            self.groups.update(G.leg_sugar_group(self.root_ids))
        log(f"  groups: {G.group_counts(self.groups)}")

        if self.dev_subnet:
            keep = dev_subnet_keep(self.groups, self.n_global, min_syn=self.dev_min_syn)
            self.l2g = np.flatnonzero(keep)
            g2l = np.full(self.n_global, -1, dtype=np.int64)
            g2l[self.l2g] = np.arange(len(self.l2g))
            tmp = tempfile.mkdtemp(prefix="neurofly_DEV_")
            try:
                path_comp, path_con = write_dev_files(keep, tmp)
                neu, syn, spk_mon = create_model(str(path_comp), str(path_con), self.params)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            self.local = {k: g2l[v] for k, v in self.groups.items()}
            log(f"  DEV subnet (partners >= {self.dev_min_syn} syn): {len(self.l2g):,} neurons, "
                f"{len(syn):,} synapses (NOT a result)")
        else:
            self.l2g = None
            path_con = str(G.PATH_CON)
            tmp_shuf = None
            if shuffle_seed is not None:   # NULL CONTROL (SPEC §3.4b), never a result: degree-preserving shuffled connectome
                tmp_shuf = tempfile.mkdtemp(prefix="neurofly_SHUFFLE_")
                path_con = shuffled_connectome(tmp_shuf, int(shuffle_seed))
            try:
                neu, syn, spk_mon = create_model(str(G.PATH_COMP), path_con, self.params)
            finally:
                if tmp_shuf:
                    shutil.rmtree(tmp_shuf, ignore_errors=True)
            self.local = self.groups
        gc.collect()  # drop create_model's dataframes
        assert defaultclock.dt == BRAIN_DT

        self.neu, self.syn, self.spk_mon = neu, syn, spk_mon
        self.n = len(neu)
        apl_objs = self._build_apl_graded(apl_gain, log) if self.apl_graded else []
        self.nt_literature = bool(nt_literature)
        if self.nt_literature and nt_silent:
            raise ValueError("nt_literature and nt_silent exclude each other")
        self.nt_impute = bool(nt_impute)
        if self.nt_impute and nt_silent:
            raise ValueError("nt_impute and nt_silent exclude each other")
        self.nt_imp_info = None
        if self.nt_impute:                       # N1 first; with nt_literature (N2) the literature rule is applied after it
            self._apply_nt_impute(log)
        self.nt_lit_info = None
        self.nt_lit_global = np.zeros(0, np.int64)
        if self.nt_literature:
            self._apply_nt_literature(log)
        self.nt_silent = nt_silent or None
        self.nt_info = None
        self.nt_silent_idx = self.nt_silent_global = np.zeros(0, np.int64)
        if self.nt_silent:
            self._silence_modulatory(self.nt_silent, asc_legacy, log)

        # ── Poisson inputs ──────────────────────────────────────────────────
        w_in = self.params["w_syn"] * self.params["f_poi"]
        self.input_set = inputs
        self.asc_legacy = bool(asc_legacy)
        self.olfaction = bool(olfaction)
        defaults = LEGACY_RATES if inputs == "legacy" else V2_RATES
        self.inputs, objs = {}, []
        self.rates = {}
        for name in input_names(inputs, asc_legacy, olfaction, self.vision_boundary, self.olfaction_full,
                                self.leg_grn):
            tgt = self.local[name]
            if len(tgt) == 0:
                continue
            self.rates[name] = defaults[name]
            pg = PoissonGroup(len(tgt), rates=defaults[name] * Hz, name=f"poi_{name}")
            s = Synapses(pg, neu, "w : volt", on_pre="v += w", delay=self.params["t_dly"],
                         name=f"poi_syn_{name}")
            s.connect(i=np.arange(len(tgt)), j=tgt)
            s.w = w_in
            neu.rfc[tgt] = 0 * ms  # no refractory period for Poisson targets (model.py:poi)
            self.inputs[name] = pg
            objs += [pg, s]

        self.net = Network(neu, syn, spk_mon, *apl_objs, *objs)
        self.counter = SpikeCounter(spk_mon, self.n, self.l2g)
        self.baseline = None

    # ── graded APL (--apl-graded) ───────────────────────────────────────────
    def _build_apl_graded(self, gain, log):
        """Move the APL output synapses from the spike path to the graded path (see module doc)."""
        apl, kc = G.apl_kc_indices(self.root_ids)
        if self.l2g is not None:
            g2l = np.full(self.n_global, -1, dtype=np.int64)
            g2l[self.l2g] = np.arange(len(self.l2g))
            apl, kc = g2l[apl], g2l[kc]
            apl, kc = apl[apl >= 0], kc[kc >= 0]
        if len(apl) == 0:
            raise ValueError("no APL neuron in the network")
        gain = APL_GAIN if gain is None else gain
        if gain is None:
            raise ValueError("APL_GAIN not calibrated yet; pass apl_gain=")
        w_syn = float(self.params["w_syn"])
        si, sj = np.asarray(self.syn.i[:]), np.asarray(self.syn.j[:])
        sw = np.array(self.syn.w_[:])                          # copy (w_[:] is a view)
        pos = np.full(self.n, -1, dtype=np.int64)
        pos[apl] = np.arange(len(apl))
        is_apl, is_kc = pos >= 0, np.zeros(self.n, bool)
        is_kc[kc] = True
        out = np.flatnonzero(is_apl[si])                       # APL -> any target
        kin = np.flatnonzero(is_apl[sj] & is_kc[si])           # KC -> APL
        n_in = sw[kin] / w_syn                                 # positive synapse counts (ACh)
        if np.any(n_in <= 0):
            raise ValueError("non-excitatory KC->APL synapse")
        tot = np.bincount(pos[sj[kin]], weights=n_in, minlength=len(apl))
        t_mbr = self.params["t_mbr"]

        grp = NeuronGroup(len(apl), "da/dt = -a / t_mbr : Hz\napl_gain : 1", method="exact",
                          namespace={"t_mbr": t_mbr}, name="apl_graded")
        s_in = Synapses(self.neu, grp, "w_ka : Hz", on_pre="a_post += w_ka", delay=self.params["t_dly"],
                        name="apl_graded_in")
        s_in.connect(i=si[kin], j=pos[sj[kin]])
        s_in.w_ka_ = n_in / (tot[pos[sj[kin]]] * float(t_mbr))
        s_out = Synapses(grp, self.neu, "w_ao : volt\nI_apl_post = apl_gain_pre * w_ao * a_pre / Hz : volt (summed)",
                         name="apl_graded_out")
        s_out.connect(i=pos[si[out]], j=sj[out])
        s_out.w_ao_ = sw[out]
        self.syn.w_[out] = 0.0                                  # APL spikes no longer act on targets
        grp.apl_gain = gain
        self.apl_group, self.apl_idx, self.kc_idx = grp, apl, kc
        self.apl_info = dict(n_apl=len(apl), n_out_edges=len(out), n_out_to_kc=int(is_kc[sj[out]].sum()),
                             n_in_kc_edges=len(kin), out_syn=float(sw[out].sum() / w_syn),
                             in_kc_syn=tot.tolist(), gain=float(gain))
        log(f"  APL graded: {len(apl)} APL, {len(out)} output edges ({self.apl_info['n_out_to_kc']} to KCs, "
            f"{self.apl_info['out_syn']:.0f} signed syn), KC->APL {len(kin)} edges; gain {gain:g}")
        del si, sj, sw
        return [grp, s_in, s_out]

    # ── --nt-modulatory-silent ──────────────────────────────────────────────
    def _silence_modulatory(self, variant, asc_legacy, log):
        """Outgoing fast-path weights of DA/SER/OCT(/no-NT) neurons -> 0 (see module doc)."""
        idx, nts = G.nt_silent_indices(self.root_ids, variant)
        inp = np.zeros(self.n_global, bool)
        for name in input_names("v2", asc_legacy, olfaction=True, vision_boundary=self.vision_boundary,
                                olfaction_full=self.olfaction_full, leg_grn=self.leg_grn):
            inp[self.groups[name]] = True
        n_input_kept = int(inp[idx].sum())
        idx, nts = idx[~inp[idx]], nts[~inp[idx]]
        self.nt_silent_global = idx
        if self.l2g is not None:
            g2l = np.full(self.n_global, -1, dtype=np.int64)
            g2l[self.l2g] = np.arange(len(self.l2g))
            keep = g2l[idx] >= 0
            idx, nts = g2l[idx][keep], nts[keep]
        is_sil = np.zeros(self.n, bool)
        is_sil[idx] = True
        w_syn = float(self.params["w_syn"])
        si = np.asarray(self.syn.i[:])
        sel = np.flatnonzero(is_sil[si])
        del si
        w = np.array(self.syn.w_[:])[sel]
        self.syn.w_[sel] = 0.0
        by_nt = {t: int((nts == t).sum()) for t in ("DA", "SER", "OCT", "none")}
        self.nt_silent_idx = idx
        self.nt_info = dict(variant=variant, n_neurons=len(idx), by_nt=by_nt, n_input_neurons_kept=n_input_kept,
                            n_edges=len(sel),
                            n_edges_exc=int((w > 0).sum()), n_edges_inh=int((w < 0).sum()),
                            n_edges_zero=int((w == 0).sum()),
                            syn_exc=float(w[w > 0].sum() / w_syn), syn_inh=float(-w[w < 0].sum() / w_syn),
                            source="Codex v783 neurons.csv nt_type in DA/SER/OCT"
                                   + (" or NaN (score 0)" if variant == "broad" else "")
                                   + "; Poisson input neurons excluded")
        log(f"  NT modulatory silent ({variant}): {len(idx):,} neurons {by_nt} (+{n_input_kept} input neurons "
            f"kept); {len(sel):,} outgoing edges -> 0 "
            f"({self.nt_info['syn_exc']:.0f} exc + {self.nt_info['syn_inh']:.0f} inh synapses)")

    # ── --nt-impute (MODEL VARIANT N1) ──────────────────────────────────────
    def _apply_nt_impute(self, log):
        """MODEL VARIANT, not the published model: outgoing weights of the neurons without a Codex NT prediction
        -> |w| * imputed_sign (see module doc and scripts/make_nt_impute.py)."""
        idx, sgn, typ = G.nt_impute_indices(self.root_ids)
        if self.l2g is not None:
            g2l = np.full(self.n_global, -1, dtype=np.int64)
            g2l[self.l2g] = np.arange(len(self.l2g))
            keep = g2l[idx] >= 0
            loc, sgn_l = g2l[idx][keep], sgn[keep]
        else:
            loc, sgn_l = idx, sgn
        sign_of = np.zeros(self.n, np.int64)
        sign_of[loc] = sgn_l
        si = np.asarray(self.syn.i[:])
        sel = np.flatnonzero(sign_of[si] != 0)
        w = np.array(self.syn.w_[:])[sel]
        w_new = np.abs(w) * sign_of[si[sel]]
        self.syn.w_[sel] = w_new
        flip = (np.sign(w) != np.sign(w_new)) & (w != 0)
        pre_flip = np.unique(si[sel[flip]])
        del si
        w_syn = float(self.params["w_syn"])
        self.nt_imp_info = dict(
            n_neurons_imputable=int(len(idx)), n_neurons_changed=int(len(pre_flip)), n_edges=int(len(sel)),
            n_edges_changed=int(flip.sum()),
            syn_exc_to_inh=float(w[flip & (w > 0)].sum() / w_syn),
            syn_inh_to_exc=float(-w[flip & (w < 0)].sum() / w_syn),
            rule="MODEL VARIANT N1: neurons without a Codex nt_type take the synapse-weighted majority sign of the "
                 "non-empty cells of the same cell_type; w = |w| * imputed_sign on all their outgoing synapses")
        log(f"  NT impute (MODEL VARIANT N1, not the published model): {len(idx):,} imputable neurons; "
            f"{len(pre_flip)} neurons / {int(flip.sum()):,} edges change sign "
            f"({self.nt_imp_info['syn_exc_to_inh']:.0f} exc->inh, {self.nt_imp_info['syn_inh_to_exc']:.0f} inh->exc synapses)")

    # ── --nt-literature ─────────────────────────────────────────────────────
    def _apply_nt_literature(self, log):
        """Outgoing weights of the literature-typed neurons -> |w| * sign_lit (see module doc)."""
        idx, sgn, typ = G.nt_literature_indices(self.root_ids)
        if self.l2g is not None:
            g2l = np.full(self.n_global, -1, dtype=np.int64)
            g2l[self.l2g] = np.arange(len(self.l2g))
            keep = g2l[idx] >= 0
            loc, sgn_l = g2l[idx][keep], sgn[keep]
        else:
            loc, sgn_l = idx, sgn
        sign_of = np.zeros(self.n, np.int64)
        sign_of[loc] = sgn_l
        si = np.asarray(self.syn.i[:])
        sel = np.flatnonzero(sign_of[si] != 0)
        w = np.array(self.syn.w_[:])[sel]
        w_new = np.abs(w) * sign_of[si[sel]]
        self.syn.w_[sel] = w_new
        flip = (np.sign(w) != np.sign(w_new)) & (w != 0)
        pre_flip = np.unique(si[sel[flip]])
        del si
        pre_flip = pre_flip if self.l2g is None else self.l2g[pre_flip]
        w_syn = float(self.params["w_syn"])
        self.nt_lit_global = idx
        self.nt_lit_info = dict(
            table=str(G.PATH_NT_LIT.relative_to(G.PATH_NT_LIT.parents[1])), n_types=int(len(set(typ))),
            n_neurons=int(len(idx)), n_neurons_changed=int(len(pre_flip)),
            types_changed=sorted(set(typ[np.isin(idx, pre_flip)])), n_edges=int(len(sel)),
            n_edges_changed=int(flip.sum()),
            syn_exc_to_inh=float(w[flip & (w > 0)].sum() / w_syn),
            syn_inh_to_exc=float(-w[flip & (w < 0)].sum() / w_syn),
            rule="w = |w| * sign_lit for every outgoing synapse of the neurons of types with sign_lit != 0 "
                 "(ACh +1, GABA -1, Glu -1; Schlegel et al. 2024 known_nt)")
        log(f"  NT literature: {self.nt_lit_info['n_types']} types, {len(idx):,} neurons; "
            f"{len(pre_flip)} neurons / {int(flip.sum()):,} edges change sign "
            f"({self.nt_lit_info['syn_exc_to_inh']:.0f} exc->inh, {self.nt_lit_info['syn_inh_to_exc']:.0f} "
            f"inh->exc synapses): {self.nt_lit_info['types_changed']}")

    def set_apl_gain(self, gain):
        self.apl_group.apl_gain = gain
        self.apl_info["gain"] = float(gain)

    # ── inputs ──────────────────────────────────────────────────────────────
    def set_rates(self, **rates):
        """Set input rates in Hz: a scalar, or an array with one rate per neuron of
        the group (in group order), e.g. set_rates(orn_food_L=40, t45_L=array).
        Unknown names raise KeyError (e.g. ascending without asc_legacy).
        olf_C / orn_food_C (side unknown) follow the L/R mean unless given."""
        for k, v in rates.items():
            if k not in self.rates:
                raise KeyError(k)
            if np.ndim(v) == 0:
                self.rates[k] = float(v)
            else:
                v = np.asarray(v, dtype=float)
                if v.shape != (len(self.inputs[k]),):
                    raise ValueError(f"{k}: {v.shape} rates for {len(self.inputs[k])} neurons")
                self.rates[k] = v
        for c, l, r in (("olf_C", "olf_L", "olf_R"), ("orn_food_C", "orn_food_L", "orn_food_R")):
            if c in self.rates and c not in rates and (l in rates or r in rates):
                self.rates[c] = 0.5 * (self.rates[l] + self.rates[r])
        for k in rates.keys() | {"olf_C", "orn_food_C"}:
            if k in self.inputs:
                self.inputs[k].rates = self.rates[k] * Hz

    def silence_inputs(self):
        """All input rates 0 (persistence test)."""
        self.set_rates(**{k: 0.0 for k in self.inputs})

    # ── run ─────────────────────────────────────────────────────────────────
    def step(self):
        """Run one 25 ms decision step. Returns ({group: spike count}, per-neuron counts)."""
        self.net.run(DECISION_INTERVAL)
        counts = self.counter.update()
        return {k: int(counts[v].sum()) for k, v in self.local.items()}, counts

    def calibrate(self, n_steps):
        """Mean group counts over n_steps at the current rates (pre-takeoff).
        HAND-MADE normalisation: the controller subtracts this baseline, which
        also removes the connectome's own L/R bias."""
        acc = {k: 0.0 for k in self.local}
        for _ in range(n_steps):
            c, _ = self.step()
            for k in acc:
                acc[k] += c[k]
        self.baseline = {k: v / n_steps for k, v in acc.items()}
        return self.baseline

    def spikes(self):
        return self.counter.spikes()
