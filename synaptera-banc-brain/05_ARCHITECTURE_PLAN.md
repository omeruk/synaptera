# 05 — Architecture plan for the next study

**Working title:** *Synaptera-2 — BANC-based, with a nerve cord (VNC), causal and trainable flight*
Date: 2026-10-12. Basis: `01_CODE_REVIEW.md` (bugs), `02_CONNECTOME_MODEL_PHYSICS_TESTS.md` (structural analysis),
`03_BANC_OPPORTUNITIES.md`, `04_RESEARCH_NOTES.md`.

---

## 1. Research questions and definition of success

| RQ | question | output that counts as a "result" |
|---|---|---|
| RQ1 | Can BANC's VNC paths replace the hand-made DN → wing bridge? | in open loop, DN stimulation → correctly signed responses in the right wing MN groups; in closed loop, hover sustained without the bridge |
| RQ2 | Is the flight attitude reflex (haltere/ocelli/HS → wing steering MNs) stable in closed loop from the connectome? | pre-registered criteria for a ±30° yaw/roll perturbation against the hand-made PD (like Synaptera b1–b3) |
| RQ3 | Can the feeding trigger come by the natural path (tarsal GRN → VNC → AN → SEZ → MN9)? | removal of the "HAND-MADE trigger" label |
| RQ4 | Does a connectome with fixed topology and trained dynamic parameters learn flight tasks, and is the real topology better than control graphs? | task success in the TRAINED arm + a difference against rewired/random/MLP controls in ≥3 seeds |
| RQ5 | Can the take-off decision (looming → DNp01 → TTM) and landing come from the brain? | at least one of the take-off/landing phases moves from HAND to BRAIN/VNC |

Each RQ is pre-registered separately; if one fails the others continue (a negative result is also an output).

## 2. Principles kept and new

**Kept from Synaptera:** one source label per motor/sensory term and separate recording; pre-registration + verification
script; negative results reported with equal weight; data pinned by hash; DEV subnets are never results.

**New:**
1. **Extended label set:** `BRAIN` (brain), `VNC` (nerve-cord connectome), `HAND`, `REFLEX` (hand-made), `TRAINED`,
   `FLYVIS`. In addition a **parameter origin class** (from Fly.exe): `M` measured, `P` population prior, `F` fitted (what it
   was fitted to is written down), `E` engineering scaffold, `I` irrecoverable.
2. **Causal timing:** the body is always one coupling interval behind the neural engine (command queue); the latency is
   explicit in the configuration and in the HDF5.
3. **Quality gates (pre-registered):** L/R symmetry (|log2 R/L| < 0.5), proofreading status, in/out degree, path (hop)
   existence — no readout or path is used in an experiment before it passes the gate.
4. **External pre-registration:** OSF (or equivalent) + the in-repository record.
5. **Meaningful seeds:** physical noise (gusts, sensor noise, start pose) changes with the seed; ≥5 seeds.
6. **Controls in every experiment:** activity-matched shuffled graph, random graph with the same degrees, ablation; in
   training also linear + MLP.

## 3. Layered architecture

```
┌──────────────────────── 6. Experiment / task layer (tasks/, prereg/) ───────────────────────┐
│ task ladder T0..T6, criteria, seeds + physical noise, evaluation, report/verify               │
└───────────────▲───────────────────────────────────────────────────────────┬────────────────┘
                │ measurement/record                                         │ config (YAML + hash)
┌───────────────┴──────┐  state   ┌───────────────────────────┐            │
│ 1. Body / physics    │────────▶ │ 3. Sensory interfaces     │            │
│ MuJoCo: flybody or   │          │ vision: FlyVis + L3 lum.  │            │
│ NeuroMechFly;        │          │ haltere/wing CS, JO,      │            │
│ wing model           │          │ tarsal GRN, (olfaction)   │            │
└──────────▲───────────┘          └─────────────┬─────────────┘            │
           │ force/torque, joints             rate/current (labelled)      │
┌──────────┴───────────┐                        ▼                          │
│ 4. Motor interfaces  │ MN activity   ┌──────────────────────────────────┐ │
│ wing power/steering  │◀───────────── │ 2. Neural engine (engine/)       │◀┘
│ MN → stroke; haltere,│   (queue:     │  graph: BANC (+FlyWire783,       │
│ leg, neck, MN9       │   1 interval  │   MaleCNS adapters)              │
└──────────────────────┘   latency)    │  (a) Shiu LIF spiking —          │
                                        │      "unmodified model" arm      │
                                        │  (b) rate + trainable gain/leak  │
                                        │      (PyTorch, GPU)              │
                                        │  (c) conductance+adaptation+gap  │
                                        └──────────────▲───────────────────┘
                                                       │
                                        ┌──────────────┴───────────────────┐
                                        │ 0. Connectome data layer         │
                                        │ common schema, type crosswalk, QA│
                                        └──────────────────────────────────┘
```

### 3.0 Connectome data layer (`connectome/`)
- **Adapters:** `banc.py` (Codex export or Dataverse 7WTH1N: `banc_888_edgelist_simple_v3.feather`, `banc_888_meta.feather`,
  NT predictions), `flywire783.py` (the existing Shiu files), `malecns.py` (optional, for comparison).
- **Common schema:** `neurons(id, cell_type, cell_class, super_class, side, region∈{brain,SEZ,neck,VNC}, nt, nt_conf, soma_xyz, status)`,
  `edges(pre, post, n_syn, sign)`. The sign rule is in the configuration (Shiu rule by default; variants labelled).
- **Type crosswalk** (`crosswalk.csv`): FlyWire ↔ BANC (DNs, MN9, LB3 sugar GRNs, HS/VS/H2, LC4/LPLC2, T4/T5, haltere
  afferents, wing MNs); a source column (NBLAST, name, connectivity profile).
- **QA report** (automatic for every data version): L/R symmetry table (generalised `dn_lr_asymmetry.py` from this study),
  degree distributions, neurons without input, excitatory/inhibitory ratios, hop distances and signed influence of the
  critical paths (generalised `connectome_structure.py`).

### 3.1 Neural engine (`engine/`)
Common interface (proposal):
```python
class NeuralEngine(Protocol):
    def reset(self, seed: int) -> None: ...
    def set_inputs(self, drive: dict[str, np.ndarray]) -> None:     # group name -> rate (Hz) or current
    def advance(self, dt_ms: float) -> None:                        # one coupling interval
    def rates(self, groups: list[str], window_ms: float) -> dict[str, np.ndarray]
    def state_dict(self) -> dict: ...                               # replay / audit
```
- **(a) Spiking (reference arm):** Shiu parameters unchanged; Brian2 (CPU) or GeNN/Brian2CUDA (GPU). "Unmodified model"
  claims come only from this arm. Poisson input without delay, as Shiu's `PoissonInput`; a current-injection variant for
  graded cells, labelled.
- **(b) Rate + trainable (TRAINED arm):** the flyhard recipe — `s ← (1−λ)s + λ·tanh(Ŵs + u)`, `Ŵ` = signed, input-normalised
  synapse count × (edge gain); learned: edge gain + neuron leak (+ optionally a gain per cell type). **State carried** (no
  reset). Custom sparse backward (chunked per-edge derivative + stored transpose).
- **(c) Biophysical variant:** conductance-based IF + adaptation + gap junctions (the Uploading Lab approach); to test the
  resting-activity problem (76 % of DNs silent).
- **Equivalence test:** open-loop response correlation between (a) and (b) (e.g. sugar → MN9, looming → DNp01) is reported.

### 3.2 Sensory interfaces (`sense/`)
| sense | source | target neurons (BANC) | note |
|---|---|---|---|
| vision | FlyGym eyes → FlyVis | boundary layer (existing rule) + **L3 luminance pathway** | more sub-frames near obstacles (H4) |
| haltere | body angular velocity (Coriolis) | haltere campaniform afferents (VNC) | critical for the reflex arc; ms scale |
| wing mechanosensors | stroke parameters | wing CS afferents | muscle feedback |
| antenna (JO) | air flow, wind | JO-A/B/C/E | speed/wind sense |
| leg taste (tarsal GRN) | tarsus–food contact | tarsal sugar GRNs (VNC) | RQ3; replaces the HAND shortcut |
| leg proprioception | joint angles/contact | leg CS/chordotonal | landing and walking |
| olfaction | 3D odour field | ORNs (antennal lobe) | off until the AL lock-up is solved (see §6) |

Each mapping is a `Transduction` object: input quantity → rate; its parameters carry an origin class (`M/P/F/E/I`).

### 3.3 Motor interfaces (`motor/`)
- **Wing:** power-muscle MNs (DLM/DVM; wingbeat frequency/amplitude) + steering MNs (b1–b3, i1–i2, iii1–iii3, hg, tp;
  amplitude asymmetry, stroke deviation). `MuscleModel`: MN rate → activation (first-order filter) → change of stroke
  parameter; parameters **only from literature physiology** (open loop), never tuned on behaviour; physical limits
  (Φ ≤ ~180°).
- **Haltere MNs, neck MNs** (the head reflex can stop being hand-made), **leg MNs** (TTM take-off, landing extension),
  **MN9** (proboscis; a physical effect if a proboscis joint is added to MuJoCo).
- **Bridge arm:** the existing hand-made DN → stroke bridge stays as a **control arm** (for comparison).

### 3.4 Body/physics (`body/`)
- **Option A (recommended start):** the existing FlyGym/NeuroMechFly + an improved stroke-averaged model (amplitude limit,
  stroke-plane angle, anisotropic damping). Fast, compatible with the existing code.
- **Option B (later):** the flybody (Vaxenburg 2025) wing-jointed fluid model + pattern generator; MN → modulation of the
  pattern generator. More realistic but a small time step and expensive.
- Physics dt 0.05–0.1 ms; **coupling interval 5 ms** (25 ms is too coarse for reflexes); vision 100–200 Hz.
- A (seeded) physical-noise generator: gusts, sensor noise.

### 3.5 Coupling and timing
```
for every 5 ms interval k:
    sensory_k = sense(body_state_k)               # input to the neural engine
    engine.advance(5 ms)                          # neural state k → k+1
    mn_k      = engine.rates(motor_groups)        # MN output of this interval
    body.step(motor(mn_{k-1}), 5 ms)              # body ONE INTERVAL BEHIND (causal)
    record(k)
```
In Brian2 the overhead of a 5 ms `run()` call is high → couple inside one `run()` with a `network_operation`, or use
GeNN/PyTorch.

### 3.6 Recording, replay, verification
- The existing HDF5 schema extended: every term + label + origin class; MN rates; the latency parameter; hash of the QA report.
- **Replay audit** (Synaptera already has it, "replay exact"): with the recorded inputs the neural engine is bit-identical.
- `verify_report.py`: recomputes the report numbers from the records (existing approach).
- Numeric-tolerance comparison (across platforms).

## 4. Task ladder and phases (gated roadmap)

| phase | work | output | gate |
|---|---|---|---|
| **F0** | Fixes of the v1 design built into the new code: H1 (queue), H2 (symmetry gate), M1, M2, H5, M7 | the ported code + an n1 re-run (same result expected) | n1 criteria pass unchanged |
| **F1** | BANC data pipeline + crosswalk + QA report | QA tables; MN9/DN matches | critical types matched (DNp01, DNg02, DNa02, MN9, haltere afferents, wing MNs); symmetry report published |
| **F2** | Open-loop reproductions (spiking arm): sugar→MN9, tarsal GRN→MN9, looming→DNp01→TTM, haltere→steering MN, HS→DN | 5 pre-registered tests | ≥3/5 pass; failures reported as negative findings |
| **F3** | Wing motor interface + muscle model; haltere reflex in closed loop during hover (RQ1, RQ2) | REFLEX → VNC label change (or negative) | ±30° perturbation criteria (like b1–b3), ≥5 seeds |
| **F4** | Take-off (GF/TTM), landing, natural feeding trigger (RQ3, RQ5) | per-phase label table | separate criteria per phase |
| **F5** | TRAINED arm: rate engine, BC + DAgger, tasks: hover → optomotor → obstacle → landing (RQ4) | learning curves, control arms | ≥3 seeds; comparison with controls pre-registered |
| **F6** | Full task: take-off → towers → landing → feeding; video; paper | final report | — |

Task ladder (each with a pre-registered criterion):
T0 open-loop responses → T1 hover + perturbation → T2 optomotor yaw tracking → T3 GF take-off → T4 landing on the platform
→ T5 orienting to the target (visual target: the dark platform; olfaction only if the AL problem is solved) → T6 full task.

**Information-alignment rule (lesson from H3):** in the TRAINED arm the teacher signal must be derivable from the senses the
brain receives (e.g. a visually defined route). Pre-test: cross-validated R² > 0 in a brainless "bypass" arm (random projection).

## 5. Proposed directory layout

```
synaptera-banc-brain/
  connectome/   adapters (banc, flywire783, malecns), schema.py, crosswalk.csv, qa.py
  engine/       lif_brian2.py, lif_genn.py, rate_torch.py (+ sparse autograd), cond_adapt.py, protocol.py
  sense/        vision_flyvis.py, l3_luminance.py, haltere.py, wing_cs.py, jo.py, tarsal_grn.py, olfaction.py
  motor/        wing_muscle.py, haltere_mn.py, leg_mn.py, neck_mn.py, proboscis.py, legacy_bridge.py
  body/         flygym_body.py, flybody_body.py, quasi_steady.py, noise.py
  coupling/     scheduler.py (causal queue), recorder.py (HDF5/Zarr), replay.py
  tasks/        t0_openloop.py ... t6_full.py, criteria.py
  train/        bc.py, dagger.py, controls.py (rewired/random/linear/MLP)
  prereg/       OSF links, criteria files (immutable)
  scripts/      fetch_data.py, verify_report.py, figures/
  configs/      *.yaml (+ parameter origin register assumptions.json)
  tests/        unit + integration + "golden" open-loop tests
```

## 6. Separate sub-plan for olfaction (optional)

The structural analysis shows that the persistent state in the AL comes from the **sign rule** (77 % of the internal LN+PN
synapses excitatory; 54 aminergic LNs counted as excitatory; leading eigenvalue ~2,184 synapses → a self-sustaining mode
above ~2.3 Hz). Options (each labelled as a **model variant**): (i) remove aminergic neurons from the fast path (existing
`--nt-modulatory-silent narrow`), (ii) literature signs for the LNs (existing `--nt-literature`, 24 neurons were not enough),
(iii) a neuron model with adaptation (c), (iv) input normalisation in the rate model. Gate: the O1 criterion (< 0.1 Hz
100–200 ms after the cut).

## 7. Compute plan

| work | resource | estimated cost |
|---|---|---|
| Spiking arm, BANC ~160–190k neurons, CPU Brian2 | one process/core; 1 s simulated ≈ 20–40 s wall (scaled from BioReservoir measurements; to be verified) | 7.5 s flight ≈ 3–5 min; 5 seeds × 10 conditions ≈ a few hours |
| Spiking arm, GPU (GeNN/Brian2CUDA) | one GPU | close to real time (FastFly/Eon benchmarks) |
| Rate-arm training | A6000/A40-class GPU (~$0.5/hour) | flyhard pilot: 600 steps in 186 s, ~3 GB; hours per task |
| FlyVis + rendering | CPU/GPU | the cost of more sub-frames must be measured |

## 8. Risk register

| risk | likelihood | impact | mitigation |
|---|---|---|---|
| MN9 match in BANC uncertain | low (MN9 named in the Codex export, 03 appendix A) | RQ3, feeding | confirm by connectivity profile + NBLAST |
| BANC L/R proofreading asymmetry | medium–high | lateral readouts | symmetry gate; mirror-symmetric control; population-level readouts |
| VNC paths silent (no resting activity) | high | RQ1–RQ2 | variant (c); tonic drive (labelled); rate arm |
| Muscle-model parameters uncertain | high | RQ1 | open-loop literature only; sensitivity analysis; origin class `P/F` |
| Compute cost (5 ms coupling) | medium | schedule | GeNN/PyTorch; DEV subnet for development only |
| Training shows no "topology advantage" | medium | RQ4 | reported anyway; task choice pre-registered |
| Licence | low | publication | BANC CC BY 4.0; FlyWire CC BY-NC; derived files in a separate bundle |

## 9. First concrete steps

1. F0: port the Synaptera code into the new layout (see `06_NEW_PROJECT_SETUP.md`), with the command queue, overwrite
   protection, conditional loading of the T4/T5 column file and amplitude clipping built in; tests.
2. F0: turn `scripts/dn_lr_asymmetry.py` into the readout-gate tool; publish the report for DNa02/DNp15.
3. F1: BANC adapter on the common schema; hash the data; QA report.
4. F1: first crosswalk: DNp01, DNg02 (a–h), DNa01/02, DNp15, DNp07/10, MN9, LB3, haltere afferents, wing MNs.
5. F2 pre-registration: criteria of the 5 open-loop tests (OSF + repository).

## 10. Why this order (link to the Synaptera results)

- DNg02 silence: 54 % of its input is inhibitory, 8 % from ascending neurons that are never driven → a power readout does
  not seem possible without VNC + AN feedback and resting activity → **F1–F3 first**.
- DNp15/DNp10 failures: consistent with the structural L/R asymmetry → **symmetry gate in F0**.
- Leg GRN → MN9 failure: the signed influence is negative in FlyWire and the VNC data are missing → **F2 in BANC**.
- Training ladder: information mismatch + stopped before DAgger → **information-alignment rule and DAgger mandatory in F5**.
- Olfactory lock-up: positive feedback caused by the sign rule → **separate sub-plan (§6)**, not on the critical path of flight.
