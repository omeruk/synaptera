# 02 — Connectome structure, brain model, physics engine and brain tests

Date: 2026-10-12. The **new** numbers in this document come from scripts run in this session on FlyWire v783 (the Shiu et
al. model files + the FlyWire annotations, SHA-256 verified):
`scripts/connectome_structure.py` → `results/connectome_stats.json`,
`scripts/dn_lr_asymmetry.py` → `results/dn_lr_asymmetry.txt`,
`scripts/grn_mn9_check.py` → `results/grn_mn9.json`.
Numbers taken from the repository reports are cited with their source (REPORT.md §…).

---

## 1. Connectome structure

### 1.1 Global statistics (the graph loaded by the Shiu model)

| measure | value |
|---|---|
| neurons | 138,639 |
| edges (pre→post pairs) | 15,091,983 (excitatory 9,059,302 / inhibitory 6,032,681) |
| synapses | 54,492,922 (excitatory 32,494,717 = 59.6 % / inhibitory 21,998,205) |
| neuron sign (output) | 96,672 excitatory, 41,333 inhibitory, 634 without output |
| neurons without input | 1,549 (never spike unless driven) |
| synapses per edge | median 2, max 2,405 |
| in-degree (edges) | mean 108.9, median 69, max 10,356 |
| input synapses per neuron | mean 393, median 198, 99th percentile 3,477 |
| reciprocal edge fraction | 26.6 % |
| self-loops | 0 |

Super classes: optic 77,521; central 32,380; sensory 16,353; visual projection 8,037; **ascending (AN) 1,736**;
**descending (DN) 1,299**; sensory-ascending 581; visual centrifugal 524; **motor 110**; endocrine 76.
Largest synapse flows: optic→optic 20.2 M; central→central 18.4 M; optic→VPN 4.3 M; VPN→central 2.0 M;
**central→DN 1.47 M**; AN→central 0.87 M.

**Important:** of the 110 motor neurons in the model, 105 are brain motor neurons (proboscis/pharynx/antenna) and 1 is a
neck MN; **there is no wing, haltere or leg MN** — those are in the VNC. The 1,736 ascending neurons are in the model but
**never driven** (no VNC).

### 1.2 LIF arithmetic (Shiu parameters) — why "many synapses are needed"
- Peak PSP of one synapse: **0.043 mV** (at 9.2 ms; τm 20 ms, τs 5 ms, w 0.275 mV).
- Reaching threshold (−52 → −45 mV, 7 mV) takes ~**162 coincident synapses**, or by mean depolarisation
  **~5,091 synapse·Hz** (e.g. 51 synapses × 100 Hz).
- A Poisson input synapse is **68.75 mV** (w × 250) → every input spike is a guaranteed output spike. Driven neurons
  (including the 34,121 boundary-layer neurons) become effectively **spike generators**; their own recurrent input has no effect.
- The network has **no resting/tonic activity**: without input it is completely silent (BioReservoir also measured 0
  spikes). Result: neurons with weak or net-inhibitory input (e.g. DNg02) never fire; in the training flights 986 of the
  1,299 DNs are constant (REPORT §3.9b).

### 1.3 Sugar GRN → MN9 (the only BRAIN decision) and why the leg GRNs fail

| source | n | direct synapses to MN9 | excitatory hops to MN9 | signed linear influence (steps 1→4) |
|---|---|---|---|---|
| labellar sugar GRNs (LB3, 20 Shiu + 16 right homologs) | 36 | 0 | **2** | 0 → +2.1e-5 → +8.2e-4 → **+1.4e-3** |
| leg sugar-like GRNs (SA_VTV_2, selected by connectivity) | 12 | 0 | 3 | 0 → −2.5e-6 → −1.6e-5 → **−5.7e-6** |
| all leg GRNs | 74 | 0 | 2 | 0 → −1.2e-5 → −2.0e-4 → **−2.0e-4** |

(Signed influence: powers of the signed connectivity matrix normalised by each neuron's total input synapses — a simple
linear analogue of the "influence" measure of the BANC paper.)

MN9's own input is 11,465 synapses, **54 % inhibitory** (6,218); the largest inputs are DNge062, CB0553, CB0806, …
**Reading:** the influence of the leg GRNs on MN9 is structurally **net negative** → that the connectivity-selected leg GRNs
do not drive MN9 (lab-notebook finding) is the expected outcome at the connectome level. FlyWire contains only the
ascending axon fragments of these neurons; the natural path (tarsus → VNC → AN → SEZ) is missing → to be tested in BANC.

### 1.4 Left/right asymmetry — a structural explanation of the DNp15 and DNp10 failures

Whole brain: the right hemisphere has fewer neurons (68,914) than the left (69,499) but **10.8 % more input synapses**
(right/left: optic 1.157; VPN 1.133; central 1.064; DN 1.065).

The **383 DN types** with one neuron per side:
- median |log2(right/left)| 0.22 (~1.17×); **24.8 % differ by > 1.41×, 11.5 % by > 2×**; the signed median is shifted to
  the right (+0.10).

| DN | left input | right input | right/left | asymmetry rank of 383 | reported behaviour |
|---|---|---|---|---|---|
| **DNp15** (steering readout, post-hoc) | 1,255 (excitatory 636) | 2,085 (excitatory 1,126) | **1.66** | **65th** | perch baseline L 0 / R 52 Hz; right-dominant even for a static scene; validation failed |
| **DNp10** (landing candidate) | 7,655 | 1,849 | **0.24** | **8th** | left 0–20 Hz, right 0 in every window |
| DNa02 (pre-registered primary) | 12,268 | 13,159 | 1.07 | 300th | recorded only |
| DNa01 | 5,857 | 6,638 | 1.13 | 222nd | — |
| DNp01 (giant fibre) | 4,327 | 5,147 | 1.19 | 176th | — |
| DNp07 (landing candidate) | 4,656 | 4,061 | 0.87 | 214th | fires in every phase, not selective |

**Conclusion:** both reported lateral-readout failures were **predictable** from the connectome before the readouts were
chosen. The cause may be incomplete reconstruction (proofreading/segmentation) or individual variation; for the model it
makes no difference — a lateral readout needs a symmetry gate (see `05_ARCHITECTURE_PLAN.md`).

### 1.5 Why is DNg02 (collective power) silent in every run?
- 25 neurons, 13,329 input synapses in total, **54 % inhibitory** (7,228 vs 6,101).
- Input sources: central 11,378 (IB008, PS008, IB010, PS005, IB025, PS181, …), **ascending 1,107** (AN_multi_28, AN_multi_6;
  not driven in the model), DN 600, VPN 196.
- Distance from vision is not the problem: DNg02 neurons are 1–2 hops from VPNs and 2–3 from T4/T5 (1,288 of all 1,299 DNs
  are ≤ 2 hops from VPNs).
- **Reading:** the silence comes not from reachability but from **net-inhibitory input + no tonic drive + missing AN/VNC
  feedback**. A wing-power readout should be re-tested in a model with a VNC and/or with resting activity.

### 1.6 The structural cause of the antennal-lobe (AL) persistent state
- 429 ALLNs: **166 excitatory / 263 inhibitory** in the model. Dominant NT in the annotations: glutamate 148, GABA 147,
  **ACh 80, serotonin 40, dopamine 12, octopamine 2** → the Shiu rule counts the amines as **fast excitatory** as well.
- 685 ALPNs: 474 excitatory / 211 inhibitory.
- Internal LN+PN synapses: **650,947 excitatory / 192,129 inhibitory (77 % excitatory)**.
- **913** of the 1,114 LNs+PNs receive enough recurrent excitatory synapses to cross threshold when the other LNs/PNs fire at
  100 Hz (691 after subtracting inhibition).
- The leading eigenvalue of the signed LN+PN submatrix is **≈ 2,184 synapses** → by a rough linear (mean-depolarisation)
  estimate the gain is ≈ 2,184 × 1.375 µV/(synapse·Hz) ≈ **3.0 mV/Hz**: once the mean activity of this mode exceeds
  **~2.3 Hz** it supplies the 7 mV threshold gap by itself → a self-sustaining state. The reported AL lock-up (~120 Hz, no
  decay after the cut; REPORT §3.7) is consistent with this positive feedback. Changing only 24 neurons with literature
  signs (N2) was not enough to break it.

---

## 2. Evaluation of the brain model

**Strengths:** the published model is used unmodified; the whole brain is simulated (no subnetwork); every model variant
is separated by a flag and a label (`--nt-impute`, `--nt-literature`, `--apl-graded`, `--nt-modulatory-silent`); the FlyVis →
FlyWire boundary-layer rule was fixed before any behaviour; a shuffled-connectome null control; the replay audit passes
"bit for bit" (8,025,285 spikes).

**Weaknesses and their effects:**

| problem | effect | evidence |
|---|---|---|
| No resting activity, uniform LIF | most DNs silent → no readout information | 986/1,299 DN features constant (§3.9b) |
| Amines and all "other" NTs fast excitatory | runaway positive feedback in the AL | §1.6 |
| Graded (non-spiking) cells driven by Poisson spikes; 68.75 mV kick | boundary layer is a pure generator; over-strong, unbalanced input | §1.2; vision_boundary docstring |
| L/R reconstruction asymmetry | lateral readouts biased | §1.4 |
| No VNC, ANs not driven | DN → muscle path hand-made; DNg02 silent | §1.1, §1.5 |
| Shuffled null not activity-matched | "wiring" and "activity level" effects confounded | shuffled brain 2.5× DN spikes (§3.9b) |
| Readouts at 25 ms + 50 ms filter | no control at reflex time scale (ms) | `vnc_bridge.READOUT_TAU` |
| Post-hoc readout choice | lowers the value of pre-registration (the report says so honestly) | REPORT §2.6 |

---

## 3. Evaluation of the physics engine

**Set-up:** MuJoCo 3.2.7 (FlyGym 1.2.1 / NeuroMechFly v2 body), physics dt 0.1 ms, 250 sub-steps per decision. Wings are
**not** simulated aerodynamically: a stroke-averaged (quasi-steady) force/torque is applied with `xfrc_applied` at the
whole-fly centre of mass (torque shift correct). Lift `F = (W/2)(Φ/Φ0)²(f/f0)²` along body z; linear flapping
counter-force/torque (Hedrick 2009); terminal speed calibrated to 300 mm/s at 12°; haltere reflex PD (ωn 200 rad/s, ζ 1;
~30 ms settling after Beatus 2015); hand-made head reflex; soft contacts on obstacles (solimp/solref), adhesion.

**Done well:** the bug of the dummy inertial in the FlyGym root body (1e-6 g mass at the spawn position, which inflated the
roll inertia ~60×) was found and fixed; BADQACC warnings monitored; intra-step tower penetration measured (S1 criterion);
cosine ramps for leg transitions; textured towers/platform (motion off the edges for T4/T5).

**Problems:**
1. **Unbounded amplitude** (up to 206° computed; `01_CODE_REVIEW.md` H5).
2. **Stroke plane = body horizontal plane**; forward thrust only through body tilt; no stroke-plane angle or wingbeat phase.
3. **Isotropic linear damping**: the real flapping counter-force depends on direction.
4. **Fixed roll–yaw coupling**: roll torque (F_L − F_R)·arm; no separate control.
5. **Visual sampling at 80 Hz** → motion aliasing near obstacles (H4).
6. **Within-step brain–body acausality** (H1).
7. **Deterministic physics** → seed repeats are not independent.
8. **No proboscis joint** → the MN9 decision has no physical effect.
9. Wings collide as static geometry (they flap in the video, not in the physics).

Comparison: flybody (Vaxenburg et al. 2025) offers a flight model with wing joints, a fluid model and imitation of real
flight trajectories; it should be considered as an option in the next stage (`05_ARCHITECTURE_PLAN.md` §3.4).

---

## 4. Evaluation of the brain tests and their results (from the repository reports)

| test | result (REPORT.md) | reading of this analysis |
|---|---|---|
| Final-v1 (final_a/b/c) | a: S1 ✗ (6.3 µm), b: ✓✓, c: ✗✗ | routes of a and b almost identical → route is hand-made |
| DNp15 validation (pre-registered) | (a) 12/12, (b) 6/6, 3/6, 3/6, (c) 0/9 → **failed** | §1.4: DNp15 input 1.66× on the right → right dominance on a static scene is structural; the H1 latency bug also affects the closed-loop test |
| final_v2a (pre-registered) | S1 ✗ (130.9 µm), S2 ✓ | the ablation constant is not "brainless" (+0.244 right turn) |
| n1 / n2 (post-hoc control) | n1 ✓✓, n2 ✗✗ | n1 route hand-made; n2 brain-only, no landing |
| Multi-seed (n1 5/5) | route bit-identical | not an independent repeat (deterministic physics, steering 0) |
| Start position/heading (8/8) | ✓ | robustness of the hand-made route; not brain control |
| Olfaction O1 (+N1/N2 variants, upstream drive) | 0/8 rates, lock-up in every variant | §1.6: positive feedback caused by the sign rule |
| Visual DN screen | 1 of 21 a-priori tests passed (DNp15), 8 failed, 12 silent | DNg02 silence §1.5; most DNs sub-threshold without tonic drive |
| Loom follow-up (collision-locked) | 0/20 | same |
| Training ladder T1 (3 arms) | 0/12 flights land; turn R² < 0 | H3: information mismatch; stopped before DAgger; 986/1,299 silent features |
| Leg GRN → MN9 | MN9 0.0 Hz (lab notebook, no stored run) | **independently confirmed in this session** (§5) and its structural cause found (§1.3) |

Overall reading (I agree with the report): in this model the brain only makes the feeding decision; route, landing and
reflexes are hand-made. This analysis adds that most failures have **structural causes that could have been checked in
advance** (L/R asymmetry, net-inhibitory input, positive feedback from the sign rule, missing VNC), and these directly
shape the design of the next study.

---

## 5. Tests and checks run in this session

### 5.1 `pytest tests/` (Python 3.10, pinned Brian2 2.9.0 / MuJoCo 3.2.7 / FlyGym 1.2.1 / numpy 2.0.2, FlyVis 1.2.0, torch 2.14.1; x86_64, 4 cores)
**123 passed, 51 skipped, 0 failed** (12 min 23 s). Skip reasons: 22 × Codex `column_assignment.csv.gz` missing (sign-in
required), 9 × `slow` (full brain), 7 × `vision_boundary_783.csv` missing (Codex), 6 × `nt_impute_783.csv`,
4 × `nt_literature_783.csv`, 2 × DN reference files (need full-brain runs), others.
Note: on the first attempt the MuJoCo rendering tests could not be collected because `libEGL`/`libOSMesa` were missing;
they passed after installing them (the README's `MUJOCO_GL=egl` note should mention the system library requirement).

### 5.2 Reproducibility of the derived data
4/4 derivable files **SHA-256 identical** to the development copy; `t45_transduction.json` differs (platform/torch).

### 5.3 Independent open-loop simulation (unmodified Shiu model, Brian2, 1 s, Shiu `PoissonInput` protocol)

Results in `results/grn_mn9.json` (two Brian2 seeds, 0 and 1; a fresh network for every condition):

| driven neurons | input | MN9 left / right (Hz), seed 0 | seed 1 | active neurons (0 / 1) |
|---|---|---|---|---|
| Shiu's 20 left sugar GRNs | 100 Hz | 68 / 50 | 63 / 49 | 351 / 354 |
| 36 labellar sugar GRNs (the set of the reported runs) | 100 Hz | 54 / 48 | 55 / 48 | 393 / 397 |
| 12 leg sugar GRNs (SA_VTV_2) | 100 Hz | **0 / 0** | **0 / 0** | 75 / 76 |
| 12 leg sugar GRNs (SA_VTV_2) | 200 Hz | 1 / 0 | 2 / 0 | 154 / 173 |
| all 74 leg taste neurons | 100 Hz | 0 / 0 | 0 / 0 | 896 / 967 |
| no input | — | 0 / 0 | 0 / 0 | 0 / 0 |

This independently confirms, in two seeds, the leg-GRN finding that had "no stored run" in the report (MN9 0.0 Hz, 3/3
seeds); even with all 74 leg taste neurons driven together MN9 stays silent. The labellar path agrees with the
repository's R0 curve (v783, Shiu protocol, 100 Hz → 59.6 / 46.8 Hz; `flight/vnc_bridge.py`). The network without input is
completely silent (0 active neurons) — a direct demonstration of the missing resting activity (§1.2).
