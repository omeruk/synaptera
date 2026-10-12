# 03 — What can be done with the BANC (Brain And Nerve Cord) connectome, and possible outcomes

Date: 2026-10-12. Sources at the end. The numbers in sections 1–5 come from the BANC paper/README and from the
documentation of projects that use BANC. Appendix A is our own first analysis of the Codex BANC export. Calculations on
FlyWire v783 are in `02_CONNECTOME_MODEL_PHYSICS_TESTS.md`.

## 1. What BANC is and why it matters for Synaptera

| property | FlyWire v783 (used now) | BANC |
|---|---|---|
| coverage | brain only (+ optic lobes, SEZ) | brain + SEZ + cervical connective + **the whole VNC** |
| individual | adult female | adult female (same sex → easier cell-type matching) |
| neurons | 138,639 (Shiu model) | ~188,000 (188,508 in the Uploading Lab model; 158,262 in the Codex export, appendix A) |
| synapses | 54.5 M (Shiu model file; median 2 synapses per edge) | ~199 M predicted; 42.3 M retained synapses / 13.6 M edges in the Uploading Lab model; 23.6 M in the Codex "princeton" export (appendix A) |
| DN / AN / effector | 1,299 DNs; ANs as cut axons | **1,316 DNs, 1,849 ANs, 1,031 effector neurons** (MN + endocrine + visceral) |
| wing/haltere/leg MNs | **none** | **present** (in the VNC) |
| licence | CC BY-NC 4.0 (non-commercial) | **CC BY 4.0** (Dataverse statement; more permissive) |

Synaptera's biggest structural gap — **the DN → wing path is a hand-made bridge** (REPORT §5) — can be handed over to the
connectome itself with BANC. The natural path of the leg taste neurons (tarsal GRNs) into the VNC and up to the SEZ via
ascending neurons is also fully present in BANC; FlyWire has only their ascending axon fragments (`sensory_ascending`, 581
neurons).

Main findings of the BANC paper (Bates et al. 2026): effectors are influenced most by sensory neurons of the **same body
part** (local sensorimotor loops); DNs/ANs coordinate these loops in behaviour-centric clusters (flight, walking, head
orienting, grooming, feeding, reproduction, posture, internal state); the mushroom body and the central complex act on these
clusters as "supervisors" (distributed control). This also explains why Synaptera's assumption "brain = single central
controller" was strained: much of flight stabilisation lives in local loops in the VNC.

## 2. Data versions and pitfalls (experience of projects using BANC)

- **Snapshot 626** (Dataverse doi:10.7910/DVN/8TFGGB): 114,456 neurons, ~1.4–2.7 M edges, **~3× lower mean degree** than
  FlyWire/MaleCNS; sparse typing (69 %). BioReservoir **failed its lateral side check** with this version: a narrow sensory
  input (Johnston's organ) gave an "always right" DN response in every trial; a likely cause is **45 % more proofread
  neurons on the right**. A balanced subgraph did not fix it.
- **Materialization 888** (Dataverse doi:10.7910/DVN/7WTH1N, paper version v3.0): `banc_888_edgelist_simple_v3.feather`,
  `banc_888_meta.feather`, NT predictions, influence parquets, NBLAST cross-dataset matches, meshes/SWC. The Uploading Lab
  uses 888.
- ~~**No neuron named MN9 in BANC**~~ (BioReservoir's scan of the 626 snapshot: "MN9 0"). **Correction (appendix A):** the
  current Codex BANC export has 2 neurons named `MN9` (left + right); the match should still be confirmed by connectivity
  profile.
- **L/R asymmetry**: even in FlyWire (analysis §1.4) 25 % of DN pairs differ by >1.41× in input synapses. In BANC the
  proofreading asymmetry can be larger → a **symmetry gate for every lateral readout** must be mandatory.
- Live BANC (CAVE) needs a restricted key; the static Dataverse/Codex distribution is enough.
- Python client: `banc` (PyPI 0.6.1, `jasper-tms/the-BANC-fly-connectome`); R: `bancr`; influence computation:
  `ConnectomeInfluenceCalculator`.

## 3. Studies possible with BANC (in priority order)

Each item: **work → expected/possible outcome → what we learn if it fails.**

### B0. Data pipeline and bridge tables (prerequisite)
- BANC → the common Synaptera schema (neuron: id, type, class, side, region [brain/SEZ/VNC], NT + confidence; edge: pre,
  post, synapses, sign). A FlyWire v783 ↔ BANC type crosswalk (DNs, MN9, LB3 sugar GRNs, HS/VS, LC4/LPLC2, T4/T5, haltere
  afferents, wing MNs).
- Quality gates: L/R symmetry report (input-synapse ratio per type), proofreading status, degree distribution, number of
  neurons without input.
- **Possible outcome:** most DN types match (Stürner et al. 2025 matched DNs across FlyWire/MANC/BANC).

### B1. Open-loop reproductions (model validation in BANC)
1. Labellar sugar GRNs → MN9 (Shiu protocol, 100 Hz, 1 s).
2. Leg (tarsal) sugar GRNs → VNC → AN → SEZ → MN9 (the "natural" path that fails in FlyWire).
3. Looming (LC4/LPLC2) → DNp01 (giant fibre) → **TTM motor neuron** (jump/take-off).
4. Haltere afferents → wing steering MNs (b1, b2, i1, iii3, hg, …) — the flight reflex arc.
5. Horizontal visual motion (HS/H2) → DNa/DNb/DNp15 → wing steering MNs.
- **Possible outcomes:** (1) and (3) very likely work (consistent with Shiu and Uploading Lab). (2) medium likelihood; if it
  works, Synaptera's "HAND-MADE trigger" label becomes **BRAIN/VNC** — the most valuable single gain. (4) the MaleCNS
  flight-circuit result of fly-cartpole is a positive sign; (5) high risk of lateral asymmetry.

### B2. Replacing the DN → wing bridge with the connectome
- Wing MNs: **power muscles** (DLM/DVM; indirect flight muscles, wingbeat frequency/amplitude) and **steering muscles**
  (b1, b2, b3, i1, i2, iii1, iii3, hg1–4, tp, …; amplitude asymmetry, stroke deviation). A small, clearly labelled "muscle
  model" from MN rate to stroke amplitude/frequency/asymmetry (e.g. b1 rate ↔ amplitude), fitted to literature curves, not
  to behaviour.
- Structural analysis of the path DNg02 (collective power) → power/steering MNs, then simulation.
- **Possible outcomes:** the path very likely exists structurally (DNg02 enters the wing premotor circuits in MANC).
  Dynamically, DNg02 was silent in the FlyWire model because of **net-inhibitory input** and undriven ANs; with ANs and VNC
  feedback in BANC this may change — if it does not, "missing resting activity/tonic drive" is shown to be the main
  bottleneck.

### B3. Closed-loop attitude stabilisation from haltere/wing mechanosensors
- Body angular velocity (MuJoCo) → Poisson/rate coding onto the haltere campaniform afferents; wing steering MNs → roll /
  pitch / yaw torque. The hand-made haltere PD stays as a **control arm**.
- **Possible outcome:** attitude control labelled "REFLEX (hand-made)" comes from the connectome for the first time. Latency
  and gain may need tuning; tune only against open-loop physiology (e.g. haltere reflex latency ~5–10 ms, Beatus 2015
  correction time ~30 ms).

### B4. Take-off and landing
- Take-off: GF/DNp01 → TTM (leg push) + wing opening; the Uploading Lab showed a "native GF/TTM jump".
- Landing: DNp07/DNp10 + leg-extension MNs; in FlyWire DNp10's left/right input was 4.1× asymmetric (analysis §1.4) → to be
  re-evaluated in BANC with the symmetry gate.
- **Possible outcome:** moving the take-off trigger to the brain is likely; the landing decision medium–low.

### B5. Trainable connectome (labelled TRAINED)
- The flyhard/fly-self-driving recipe applied to BANC: fixed topology, learned edge gain + neuron leak, rate model, state
  carried, BC + DAgger, controls (presynaptic permutation, linear, MLP), ≥3 seeds.
- Task: hover + yaw perturbation → optomotor yaw → obstacle avoidance → landing.
- **Possible outcomes:** task success is likely (the driving projects showed so); the "topology advantage" is task-dependent
  and may be small (in fly-self-driving the rewired graph was equal or better on the first task). The scientific value is in
  reporting the controls honestly.

### B6. Walking (side project)
- The Pugliese et al. VNC CPG circuit + NeuroMechFly; the Uploading Lab reported walking from neural motor output with BANC.
- **Possible outcome:** behaviours such as walking to the food after landing on the platform can come from the brain/VNC.

## 4. Scenario table (expected outcomes)

| scenario | what happens | likelihood (my judgement) |
|---|---|---|
| Optimistic | B1 (1, 2, 3, 4) pass; the haltere reflex stabilises hover in closed loop; take-off from the GF; landing hand-made; route from a TRAINED readout | low–medium |
| Realistic | B1-1 and B1-3 pass; B1-2 partly; the reflex has the right sign in open loop but needs tuning in closed loop; flight power (DNg02) stays silent; TRAINED arms solve the task but the topology advantage is unclear | medium–high |
| Pessimistic | lateral asymmetry persists; the MN9 match is uncertain; VNC paths are silent (no resting activity); only structural findings are reported | medium |

Every scenario gives a **reportable** result; if Synaptera's discipline on negative results is kept, even the pessimistic
scenario yields a publishable map of "what does not work in BANC and why".

## 5. Recommended first steps (concrete)

1. Get the BANC data (Codex export or Dataverse 888); pin SHA-256.
2. Adapt `scripts/connectome_structure.py` to the BANC schema and produce the same tables: L/R symmetry,
   inputs of DNg02/DNp15/MN9, AL eigenvalue, sensor → MN hop distances.
3. Run B1-1 and B1-3 with the Shiu LIF (CPU, Brian2; BANC ~160–190k neurons → roughly 20–40 s wall time per simulated second).
4. Gate: if B1-1 fails, inspect the MN9 match/NT signs in BANC; do not move on to flight.

---

## Appendix A — First look at the Codex BANC export (2026-10-12)

The two files the user has were analysed in this environment: `neurons-banc.csv.gz` (SHA-256 `40a22015…`) and
`connections_princeton-banc.csv.gz` (`8772298e…`). Script: `scripts/banc_first_look.py`; full output:
`results/banc_first_look.txt`. The files do not state the materialization (Codex's "current" BANC version); the numbers are
larger than those of the 626 snapshot.

**Coverage**
- 158,262 neurons (left 75,760 / right 82,502); 74.9 % typed. Super classes: optic 72,582, central brain 31,782, sensory
  16,557, **VNC intrinsic 12,851**, VPN 7,321, **AN 1,849, DN 1,316, motor 805**, unassigned (NaN) 11,499.
- Connections: 3,990,039 rows (per neuropil) → 3,037,361 unique neuron pairs, **23,556,214 synapses** (median 4 per pair).
  Mean input: 25 edges / 149 synapses (109 / 393 in the FlyWire v783 model) → **~2.6× sparser** than FlyWire. The Uploading
  Lab's 888 edge list reported 42.3 M synapses; this "princeton" table is a sparser export.
- `nt_type` is empty in the connection table; the sign must come from the neuron-level `Predicted NT type` (ACh 85,006,
  Glu 24,382, GABA 20,604, DA 8,072, **HIST 7,694**, OCT 1,903, SER 1,612, TYR 209, empty 8,780). A sign-rule decision is
  needed for HIST and for missing NT.

**Critical types for flight and feeding — all present**
- **MN9: 2 neurons** (L 1,913 / R 2,437 input synapses) → Synaptera's feeding decision can be tested in BANC.
- **Wing motor neurons 62:** power (DLM1–5, DVM1–3; 24), steering (b1, b2, b3, i1, i2, iii1, iii3, iii4, hg1–4, tp1, tp2,
  tpn, ps1, ps2; 24), tension (12). **Haltere MNs 25** (hi1, hi2, hiii2, hDVM, …), **neck MNs 49** (yaw/roll/pitch),
  **TTMn 2** (jump/take-off), leg MNs 391, proboscis MNs 35.
- The DNg02 family has 38 neurons; DNp15, DNa01, DNa02, DNp01, DNp07, DNp03, DNp10 (3), H2, HSN/HSE/HSS, LC4 (114),
  LPLC2 (181), LB3 (134) are present.
- Sensory (`Body Part`): haltere 466, wing 228 + wing margin 594, legs 5,596 (front/middle/hind), labellum 527 neurons.

**Left/right balance — caution**
- Optic-lobe intrinsic neurons are clearly more numerous on the right: 40,990 / 31,592 neurons, input synapses right/left
  **1.56×**; VPN 1.29×, central brain 1.12×, DN 1.16×; VNC intrinsic 0.95×, AN 1.00× (the VNC is balanced).
- In the 262 DN types with one neuron per side the median |log2(right/left)| is 0.35; 36.6 % differ by > 1.41×, 10.7 % by
  > 2× (FlyWire: 24.8 % / 11.5 %).
- **DNp15 is 1.17× here** (1.66× in FlyWire) → much of DNp15's asymmetry in FlyWire is probably a reconstruction effect.
  **DNa01 1.55×**, DNa02 1.10×, DNp01 0.92×, DNp07 1.05×.
- Conclusion: lateral comparisons driven by vision (optic-lobe imbalance) and DNa01 carry the most risk; the symmetry gate
  is essential in BANC.

**Effect on the plan**
1. Data for F1 are available: the two files go to `~/synaptera-banc-brain/banc/` (not committed), SHA-256 recorded.
2. B1-1 (labellar sugar → MN9) and B1-3 (LC4/LPLC2 → DNp01 → TTMn) can be run directly; the structural analysis of B2/B3
   can start from the wing/haltere MN list.
3. The sparseness (~2.6×) can produce silent paths with the Shiu weight (w_syn); compensating for it is a **model variant**
   decision (e.g. input normalisation or w_syn scaling) and must be pre-registered.

## Sources
- [Bates et al. 2026, *Nature* 656:957–970](https://www.nature.com/articles/s41586-026-10735-w); [BANC-project repository](https://github.com/htem/BANC-project); Dataverse [10.7910/DVN/7WTH1N](https://doi.org/10.7910/DVN/7WTH1N)
- [Stürner et al. 2025, *Nature* 643:158–172](https://www.nature.com/articles/s41586-025-08925-z) (DN/AN cross-dataset matching)
- [BioReservoir MODEL.md / DATA.md](https://github.com/igdigitallab/bioreservoir) (BANC 626 failure, missing MN9, 888 note)
- [The-Uploading-Lab/fly-behavior-experiments MODELS.md](https://github.com/The-Uploading-Lab/fly-behavior-experiments) (BANC 888 model)
- [Curt-Park/fly-cartpole](https://github.com/Curt-Park/fly-cartpole) (MaleCNS flight-stabilisation circuit)
- [Pugliese et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/) (VNC CPG)
- [Cheong et al., eLife 96084](https://elifesciences.org/reviewed-preprints/96084) (MANC premotor circuits); Namiki et al. (DNg02, flight motor)
- [banc (PyPI)](https://pypi.org/project/banc/)
