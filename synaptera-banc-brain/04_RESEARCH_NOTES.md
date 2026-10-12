# 04 — Research notes: how were "The Driving Fly" and similar connectome–body projects done?

Date: 2026-10-12. This document records **how** the work shown at `thedrivingfly.com/media` and at
`theuploadinglab.ai/fly` and `/fly/diary` was done, together with similar projects from the same period.

## 0. Note on source access (for honesty)

- `thedrivingfly.com` and `theuploadinglab.ai` were blocked by the network policy of this working environment (HTTP 403 /
  DNS); the pages **could not be opened directly**. Therefore:
  - For The Driving Fly, the project's **own GitHub repository** (`MarkUnthank/flyhard`: README, pilot report, CARLA video
    report, `src/flyhard/connectome.py`) was read. Search results show that the site and its press page (`/press`) belong
    to this repository (author: Mark Unthank, an independent experiment at "Really Nice").
  - For The Uploading Lab, the team's public repository `The-Uploading-Lab/fly-behavior-experiments` (README, `MODELS.md`,
    `THIRD_PARTY.md`) was read. The `/fly/diary` entries **could not be read**; the Uploading Lab information here comes from
    that repository and from the ledger/layers notes in the "Related work" section of Synaptera `REPORT.md` (opened 2026-10-07).
- Every repository README read was downloaded in this environment; the numbers below are the documents' **own statements**
  (not independently verified). Peer-reviewed papers are marked separately.
- To open the sites from a cloud session: add `thedrivingfly.com` and `theuploadinglab.ai` to "Allowed domains" in the
  environment settings (cloud environment menu in the session title bar → Edit → Network access).

---

## 1. The Driving Fly (flyhard) — Mark Unthank

**What:** a model built from the MaleCNS connectome (complete male *Drosophila* CNS: brain + optic lobes + neck + VNC) in
which a simulated fly **physically turns a steering wheel with its leg** and steers a car in the CARLA driving simulator
(currently a stock green Mini Cooper; the target "Flyat" is an old green Fiat Panda).

### 1.1 How it was done (method chain)

```
requested wheel angle + measured wheel angle + 7 joint angles
  → FIXED (untrained) random mapping → 6,365 "vnc_sensory" neurons
  → connectome rate model (165,122 neurons, 25,563,197 edges; 4 graph updates per decision)
  → 708 "vnc_motor" neurons → FIXED mapping → 7 foreleg joint targets
  → MuJoCo/NeuroMechFly joint servos → "point grip" constraint (foot ↔ wheel) → passive wheel
  → measured wheel angle → CARLA steering (25 Hz) → (future) camera → new input
```

- **Connectome:** MaleCNS v1.0, neurons with `status == "Traced"` and all connections between them, no extra threshold:
  165,122 neurons, 25,563,197 neuron-pair edges, 124,025,046 synapses in total.
- **Neuron model (`connectome.py`, read):** signed scalar **rate** state;
  `s ← (1−λ)s + λ·tanh(W s + drive)`, `W = (synapse count / postsynaptic total input) × (0.05 + 0.90·σ(g_edge))`,
  `λ = 0.05 + 0.90·σ(g_leak)`. The **topology is fixed**; what is learned is **one gain per edge + one leak per neuron**
  (25,728,319 parameters). The pilot does **not** use neurotransmitter signs (unsigned, input-normalised weights).
- **Training:** 1,200 demonstrations for 40 target angles with inverse kinematics + joint servos (teacher); then supervised
  learning (backpropagation), 600 optimiser steps, 186 s, one A6000 GPU, ~3 GB memory. Because PyTorch's sparse CSR
  backward asked for a 101.57 GiB dense intermediate, a custom `autograd.Function` computes the **per-edge derivative in
  chunks**.
- **Result (own statement):** on 100 held-out target angles 0/100 before training, **100/100** after (threshold 7.45°;
  worst 4.85°). Removing the grip constraint removes 99.98 % of the steering response (causal intervention).
- **Connection to CARLA:** neural decisions 20 Hz, joint commands 200 Hz, physics 20 kHz, CARLA 25 Hz; one clock; a
  24 s "instructed" drive (speed and turn requests **scripted**). Driving footage, cockpit footage and neuron activity come
  from the same recording; activity is labelled "computed rate states, not spikes".
- **Honest limits (their own words):** no visual driving, no wheel + pedals together, one training seed, no shuffled-graph
  control; "not a claim to recreate the original fly's mind".
- **Cost:** pilot session $0.67 (Runpod A6000, ~$0.56/hour).

### 1.2 "fly-self-driving" (suanmiao, Kylon agents), derived from it

Extends the flyhard recipe to visual driving:
- Same graph + same learned parameters (edge gain + leak); a **fixed random** pixel map (64×32 camera → 4,114 optic-lobe
  sensory neurons) and a fixed random motor readout (708 VNC motor neurons → steering).
- **Key finding 1:** **not resetting** the neural state between decisions (state carried) took the first task from 3/20 to 17/20.
- **Key finding 2:** behaviour cloning (BC) alone 12/20; with **DAgger ×3** 20·19·19/20 (street with traffic, 3 independent sets).
- **Controls:** linear map 12/20, MLP-40 18/20, **randomly rewired graph (presynaptic index permutation, in-degree kept)
  16/20**; on the speed + pedestrian task rewired 5/20 vs real 18·19·16/20.
- Caveats: one seed; on the first flat-road task the rewired graph was as good as or better than the real one; braking not learned.
- Cost: < $25 GPU, ~35 min on an H100.

### 1.3 "flydrive" (ORI-Muchim) — two approaches side by side

- **Hand-built visual pathway** (R1–R6 → L1/L2/L3 → Mi/Tm → T4/T5 Hassenstein–Reichardt → HS/VS → EPG ring attractor →
  PFL3 → DNa01/DNa02-like → steering/throttle), 83,182 parameters, weights learned with **PPO**.
- **The whole MaleCNS connectome as the policy:** 162,432 neurons, 24.4 M edges; signs from NT predictions (ACh +,
  GABA/Glu/His −); light enters at 5,708 neurons (photoreceptors + L1/L2/L3); **the rates of 1,311 DNs are read by a single
  linear layer**; learned: per-neuron time constant/gain/threshold, per-cell-type synaptic gain, input/output maps (674,129
  parameters).
- Practical lessons: raw synapse counts diverge (mean in-degree ~150) → **normalise each neuron's total input to 1**; store
  the transposed CSR for the backward pass; **centre** DN features per neuron (a linear probe on the frozen brain recovers
  lane position with R² 0.83).
- Result: frozen connectome + linear DN readout reaches crash-free lane keeping in 0.74 M steps (hand-built 1.11 M); but on
  the city task the ridge readout finishes 54 % and runs 1.25 red lights per episode.
- Injecting the turn command into **PFL3 (the goal-direction neurons of the central complex)** cut wrong turns from 70 % to 4 %.
- Visual-design lesson: photoreceptor adaptation + T4/T5 detecting only motion means **visual input fades to zero in a
  static scene**; the fix is the L3 pathway (sustained, luminance-coding lamina cell).

### 1.4 "flybrain-drive" (mingdianliu) — untrained, in the browser

A selected subgraph (8,000 neurons), simple LIF, engineered sensing/planning + population-rate readout; it has **not learned
to drive**; in its own words a demonstration that separates which behaviour is neural and which is programmed.

---

## 2. The Uploading Lab — a BANC-based "lo-fi whole-brain emulation"

Note in Synaptera `REPORT.md` (2026-10-07): the ledger page describes a "lo-fi whole-brain emulation" with 188,508 neurons
and 13.6 M synapses; shared physiological parameters (gain, time constants) are tuned, **synapses are never added, removed or
individually reweighted**, unmeasured values are "searched" and labelled as guesses.

The public repository `fly-behavior-experiments/MODELS.md` (read) describes the model as follows:
- Neuron identities and connections from **BANC v888**: **188,508 neurons, 13,620,865 directed edges, 42,316,236 retained synapses**.
- **Neuron model:** conductance-based integrate-and-fire + **adaptation** (`dw/dt = (a(V−V_rest) − w)/τ_w`, `+b` on a spike),
  synaptic delays, selected **graded-release** (non-spiking) cells and **explicit electrical connections (gap junctions)**.
  These parameters and the connection-strength mappings are marked as "model assumptions".
- **Body:** one neural network coupled to **two bodies**: an internal "walking body" provides the sensory feedback; the neural
  motor output drives the displayed winged body by joint-target transfer (FlyGym/FlyBody geometry, MuJoCo).
- **Native behaviours:** walking from neural motor output; **giant fibre (DNp01) / TTM events start the jump**. Wing power,
  wingbeat pattern (FlySuite `wing_pattern_fmech.npy`), attitude support, leg folding and landing are **programmed** → "a
  take-off does not establish an entirely neural flight controller".
- **Experiments (hackathon, team TimeFlies):** comparison of walking/escape with 25 wet-lab recordings; "ibuprofen"
  (adaptation parameters of all neurons), "calorie restriction" (LC4/LPLC2 → DNp01 input ×0.5) and "ageing" (all signed
  weights scaled by `2^(−d/45)`; the 45-day half-life is an **assumption**).
- **Honest limits:** all cases development seed 0; selected cases are not independent animals; no treatment kinetics.

---

## 3. Other important reference projects (short)

| project | connectome | how | what it showed / limit |
|---|---|---|---|
| **Eon Systems** "Virtual Embodied Fly" (March 2026) | FlyWire central brain, LIF (Shiu) | a few DNs read as high-level commands ("turn, walk, groom") → pretrained NeuroMechFly controllers | brain → body mapping chosen by hand; no VNC (own statement). A critique (Preserving Hope Substack): the "upload" claim is overstated because the ~15,000 VNC neurons are not simulated |
| **Fly.exe** (Ibtisam-Mohammad) | MaleCNS 165,122 neurons | GeNN/CUDA, 12 flies on one GPU; retinotopic lamina encoder; **2 DN population rates** read; walking from a published pattern generator | every parameter carries an origin class (M measured, P population prior, F fitted, E engineering, I irrecoverable); causal queue "body one interval behind" |
| **fly-cartpole** (Curt-Park) | the MaleCNS **flight-stabilisation circuit** (5,459 neurons: haltere, ocelli, HS → wing steering MNs b1/b2) | linear rate units, fixed topology, only 5 sensory gains tuned | untuned circuit 275.6 steps; tuned 499.9; shuffled wiring 165.9. **Strong hint that the flight attitude reflex can be obtained from the connectome** |
| **FlyGM** (Jin et al., arXiv 2602.17997) | FlyWire 139,246 neurons (19,262 afferent, 1,488 efferent) | the connectome as a directed message-passing graph; controls flybody with imitation + RL | better sample efficiency than rewired and Erdős–Rényi graphs and an MLP (own statement) |
| **flybody** (Vaxenburg et al., *Nature* 2025) | — (body) | whole MuJoCo body, fluid + adhesion models; in flight an MLP + a fixed **wingbeat pattern generator (WPG)**; imitates 216 real flight trajectories | the physically richest open flight body |
| **Pugliese et al. 2025** (bioRxiv) | MANC/BANC **VNC** | LIF simulation | a small rhythm-generating circuit (CPG) for walking |
| **BioReservoir** (IG Digital Lab) | MaleCNS + BANC | Shiu LIF, reservoir | **BANC (Dataverse snapshot 626) failed the lateral side check:** 114k neurons, ~3× lower mean degree, 45 % more proofread neurons on the right → "always right" in every trial; MaleCNS passed. Version 888 not tried yet |
| **flybrain-drive**, **Doodle Fly**, **Fly-NAF**, **FLYT3**, etc. | FlyWire/MaleCNS | mostly hand-made readouts + games | entertainment/demonstration; most report their own controls |

---

## 4. Common pattern: how did these projects get "driving/flying with a connectome" to work?

1. **Fixed topology, learned dynamic parameters.** None ran the raw connectome "as is" to solve a complex task. The
   successful ones (flyhard, fly-self-driving, FlyGM, flydrive) trained either the edge gains + leaks (rate model,
   backpropagation) or only the readout layer (ridge/linear).
2. **Rate model + input normalisation.** With raw synapse counts the network diverges; normalising each neuron's total input
   to 1 and using a saturating activation (tanh/sigmoid) gives stability. The spiking Shiu LIF model instead runs with fixed
   parameters **without resting activity** and leaves large regions silent (in Synaptera 986 of 1,299 DNs are constant in the
   training flights).
3. **Carrying the state over** is critical; resetting between decisions collapses performance.
4. **Imitation + DAgger** is much better than pure imitation (12/20 → 20/20). Synaptera's training ladder stopped exactly at
   this point (before the DAgger rounds).
5. **Fixed/random interfaces**: the principle "no engineered part can carry the signal on its own"; the readout and
   encoding layers are either fixed random or very small.
6. **Controls:** presynaptic-permutation (rewired) graph, linear/MLP, multiple seeds. On some tasks the rewired graph is as
   good as the real one — the topology advantage is **task-dependent**.
7. **The VNC matters:** the real motor outputs (leg/wing MNs) are in the VNC. Models with a VNC (MaleCNS/BANC) can build the
   DN → MN path without a hand-made bridge (flyhard: vnc_motor; Uploading Lab: walking; fly-cartpole: b1/b2).
8. **State of flight:** in no public project is flight entirely neural. In the Uploading Lab wing power/pattern is
   programmed; in flybody an MLP + WPG; fly-cartpole showed only the reflex.

## 5. Implications for Synaptera (short)

- Synaptera's methodological discipline (pre-registration, source labels, reporting negative results, a verification
  script) is stronger than most of these projects — keep it.
- Missing: (a) the VNC (solvable with BANC/MaleCNS), (b) trainable dynamic parameters or at least resting activity,
  (c) DAgger, (d) L/R symmetry checks (see `02_CONNECTOME_MODEL_PHYSICS_TESTS.md` §1.4), (e) information alignment (the
  teacher signal came from a sense the brain was not given).
- Detailed plan: `05_ARCHITECTURE_PLAN.md`.

## Sources

Primary repositories read (READMEs and documents downloaded in this environment):
- [MarkUnthank/flyhard](https://github.com/MarkUnthank/flyhard) — README, `docs/pilot-2026-09-09.md`, `docs/carla-video-2026-09-09.md`, `src/flyhard/connectome.py`
- [suanmiao/fly-self-driving](https://github.com/suanmiao/fly-self-driving) — README, `docs/method.md`, `docs/results.md`
- [ORI-Muchim/flydrive](https://github.com/ORI-Muchim/flydrive) — README
- [The-Uploading-Lab/fly-behavior-experiments](https://github.com/The-Uploading-Lab/fly-behavior-experiments) — README, `MODELS.md`, `THIRD_PARTY.md`
- [Ibtisam-Mohammad/Fly.exe](https://github.com/Ibtisam-Mohammad/Fly.exe) — README
- [Curt-Park/fly-cartpole](https://github.com/Curt-Park/fly-cartpole) — README
- [igdigitallab/bioreservoir](https://github.com/igdigitallab/bioreservoir) — README, `docs/MODEL.md`, `docs/DATA.md`
- [mingdianliu/flybrain-drive](https://github.com/mingdianliu/flybrain-drive), [eonsystemspbc/fly-brain](https://github.com/eonsystemspbc/fly-brain), [cobanov/awesome-fly](https://github.com/cobanov/awesome-fly) — README
- [htem/BANC-project](https://github.com/htem/BANC-project) — README

From search results (the pages themselves could not be opened in this environment):
- [The Driving Fly](https://thedrivingfly.com/), [Press kit](https://thedrivingfly.com/press)
- [The Uploading Lab](https://theuploadinglab.ai/)
- [Eon Systems — How the Eon Team Produced a Virtual Embodied Fly](https://eon.systems/updates/embodied-brain-emulation)
- [No, we haven't uploaded a fly yet (Preserving Hope)](https://preservinghope.substack.com/p/no-we-havent-uploaded-a-fly-yet)
- [Jin et al., arXiv:2602.17997 (FlyGM)](https://arxiv.org/abs/2602.17997)
- [Vaxenburg et al. 2025, *Nature* — Whole-body physics simulation of fruit fly locomotion](https://www.nature.com/articles/s41586-025-09029-4)
- [Bates et al. 2026, *Nature* — Distributed control circuits across a brain-and-cord connectome](https://www.nature.com/articles/s41586-026-10735-w)
- [Stürner et al. 2025, *Nature* — Comparative connectomics of Drosophila descending and ascending neurons](https://www.nature.com/articles/s41586-025-08925-z)
- [Pugliese et al. 2025 — Connectome simulations identify a central pattern generator circuit for fly walking](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/)
- [Cheong et al. — MANC premotor circuits (eLife reviewed preprint 96084)](https://elifesciences.org/reviewed-preprints/96084)
