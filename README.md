# Synaptera
From synapse to wing: a pre-registered test of what a whole-brain connectome model controls in closed-loop Drosophila flight

![Figure 1: system and source labels](figures/fig1_system_labels.png)

**Figure 1.** System and source labels (BRAIN, HAND-MADE, REFLEX, FLYVIS, TRAINED); dashed = not completed. Figures 2–6 and their captions: [REPORT.md, Figures](REPORT.md#figures).

![Figure 7: what the brain controls](figures/fig7_what_the_brain_controls.png)

**Figure 7.** What the brain controls in this model (table of [REPORT.md §1.1](REPORT.md)): only the feeding decision is a brain readout that was shown, and it depends on a hand-made trigger.


Synaptera couples a whole-brain leaky integrate-and-fire (LIF) model built from the FlyWire v783 *Drosophila* connectome (Brian2; 138,639 neurons, 15,091,983 connections (pre–post neuron pairs; weight = synapse count), 54,492,922 synapses in total) to the NeuroMechFly/FlyGym MuJoCo body in closed loop. Using pre-registered criteria and ablations, it tests **which components of flight behaviour come from the connectome model and which come from hand-made control**. Task: take-off from a pedestal, passing two towers, landing on a food platform and feeding.

**"Pre-registered" in this repository** means: the criteria and decision rules were committed to the repository before the runs they judge. They were not registered on an external registry (e.g. OSF), and git commit timestamps are not independent evidence of timing. Commit-by-commit record, including two cases where a smoke run or stimulus preparation started shortly before the commit: [docs/PREREGISTRATION_LOG.md](docs/PREREGISTRATION_LOG.md).

The work builds on the [NeuroFly](https://github.com/seven-monarchs/NeuroFly) walking simulation (details: [NOTICE.md](NOTICE.md), [THIRD_PARTY.md](THIRD_PARTY.md)). **This is a public snapshot that contains only the files written in this work** (list: [docs/SNAPSHOT_MANIFEST.md](docs/SNAPSHOT_MANIFEST.md)). NeuroFly's own files (walking code, `brain_model/` copy, assets, data) are not included; parts of the flight code are adapted from the NeuroFly walking script ([docs/ADAPTED_CODE.md](docs/ADAPTED_CODE.md)). No data files are included: `scripts/fetch_data.py` downloads and rebuilds them (see [Data](#data)).

**Short result:** in this model the only behavioural decision that comes from the connectome is **the feeding decision** (MN9 motor neuron > 10 Hz). Navigation, altitude, approach, landing, the head reflex and the postures are hand-made. The brain readout chosen for steering (DNp15) failed its pre-registered validation. The pre-registered final run (final_v2a) failed the tower criterion.

---

## Contents
1. [What controls what](#what-controls-what)
2. [Main results](#main-results)
3. [Negative findings](#negative-findings)
4. [Limitations](#limitations)
5. [Reproducing the numbers](#reproducing-the-numbers)
6. [Installation](#installation)
7. [Running](#running)
8. [Data](#data)
9. [Videos](#videos)
10. [Documents and repository layout](#documents-and-repository-layout)
11. [References](#references)
12. [Related work](#related-work)
13. [AI use](#ai-use)
14. [How to cite](#how-to-cite)
15. [Licence](#licence)

**Full report (English): [REPORT.md](REPORT.md)** — methods, all results, negative findings, limitations. The lab-notebook reports (`docs/tr/REPORT_FINAL*.md`, `docs/tr/REPORT_SENSORY_*.md`) and the pre-registration documents (`docs/tr/SPEC_*.md`) are a lab notebook, in Turkish. Every number in the tables below and in REPORT.md is checked against the HDF5 run files by `scripts/verify_report_final.py`.

---

## What controls what

Final configuration (n1: `--hybrid --vision-boundary --no-olfaction --no-brain-steer --head-reflex --postures`). Every motor term carries exactly one label and is stored separately in the HDF5 file.

| component | source | note |
|---|---|---|
| feeding decision (proboscis) | **BRAIN** (decision); its sensory input is a **HAND-MADE** shortcut | MN9 readout (2 CB0701 neurons) > 10 Hz, only while on the platform. Input: while any tarsus touches the platform, a hand-made rule drives 36 **labellar** sugar GRNs at 100 Hz (FlyWire annotations: sensory / gustatory / `sugar/water`, cell type LB3, maxillary–labial nerve; 20 left neurons from Shiu et al. + 16 right homologs chosen by connectivity, `data/sugar_grn_783.csv`). This contact → GRN mapping is HAND-MADE: the legs touch the platform, but proboscis taste neurons are driven (there is no proboscis contact in the model). Only the GRN → MN9 path comes from the connectome. The leg sugar GRNs selected by connectivity (12 SA_VTV_2) do not drive MN9 (see [Negative findings](#negative-findings)) and are not used in the reported runs |
| navigation | **HAND-MADE** | odour-gradient map (`turn_hand`); a hand-made sensor that reads the odour field of the simulator directly. The brain's olfactory input is off (`noOlf`). DNp15 steering term is 0 (`--no-brain-steer`; recorded, not used in the command) |
| altitude, collective thrust | **HAND-MADE** | climb floor, approach altitude target; DNg02 silent |
| forward speed, body pitch, approach, landing, leg extension | **HAND-MADE** | fixed cruise pitch, world-frame position controller, phase timers |
| head stabilisation reflex | **HAND-MADE** (reflex) | yaw and roll/pitch gains, angle limit, reset saccade and latency are all hand-set (related literature in References, not the source of the constants); the brain is not connected to the neck MNs |
| postures (flight, standing, feeding) | **HAND-MADE** | the feeding posture is triggered by the MN9 decision; the posture itself is hand-made |
| haltere reflex | REFLEX | every physics substep; recorded |
| visual input | FlyVis → FlyWire | FlyGym eyes → FlyVis network → 32 boundary-layer types (34,121 neurons) → Poisson drive |
| wing aerodynamics | model | stroke-averaged (quasi-steady) force and torque applied to the body; wing flapping is visual only |

In the brain-only arm (n2) there is no hand-made navigation and no altitude target; the steering command is 0.

**"noOlf" / `--no-olfaction`** (flags, run and video file names) means that the **brain's** olfactory input is off. The hand-made route is not affected: it reads the odour field of the simulator directly. The hand-made route takes the fly to the food; the brain decides to feed.

### What the brain controls in this model: summary

| function | source | status |
|---|---|---|
| Feeding decision after touchdown (MN9 above 10 Hz) | **BRAIN** | shown (given the hand-made trigger) |
| Trigger of the feeding decision (leg contact drives labellar sugar GRNs) | **HAND-MADE** | shown (hand-made shortcut) |
| Leg GRN → MN9 path (the natural trigger) | **BRAIN** | not shown |
| Route to the target | **HAND-MADE** | shown (hand-made; no brain contribution) |
| Landing sequence (phase machine: take-off, cruise, approach, descend, touchdown) | **HAND-MADE** | shown (hand-made) |
| Attitude stabilisation (haltere PD) and head reflex | **REFLEX** | shown (hand-set) |
| Brain-only flight (hand-made flight programme only) | **BRAIN** | not shown |
| Steering from brain DNs (DNp15, closed loop) | **BRAIN** | not shown |
| Altitude and thrust from DNg02 | **BRAIN** | not shown |
| Olfaction (brain's olfactory circuit) | **BRAIN** | not shown |
| Vision → descending neurons (open loop) | **BRAIN** | not shown |
| Loom tracking by DNs (open loop) | **BRAIN** | not shown |
| Trained readout of the DNs for the route commands (T1) | **TRAINED** | not completed |
| Visual input to the brain | **FLYVIS** | shown (input only) |

Full table with evidence and a reading: [REPORT.md §1.1](REPORT.md#11-what-the-brain-controls-in-this-model-summary).

## Main results

All runs use the full brain (no subnetwork), 300 decision steps (7.5 s), 25 ms decision step, dt 0.1 ms. The criteria were written in the `docs/tr/SPEC_*.md` files and committed before the runs; results were not changed afterwards.

- **S1:** no tower contact before touchdown (end-of-step flag and intra-step penetration both 0). A run without touchdown fails S1, also when it touched no tower (pre-registered definition: SPEC_BRAIN_CONTROL "Honest hybrid final", criterion S1; SPEC_SENSORY_INPUTS §3.3c, §3.3f).
- **S2:** feeding in at least one step after touchdown.
- **Success = S1 ∧ S2.**

### Final-v1 (T4/T5 visual input; [REPORT_FINAL.md](docs/tr/REPORT_FINAL.md))
| run | setting | S1 | S2 | note |
|---|---|---|---|---|
| final_a | hybrid, DNp15 steering term active | ✗ | ✓ | intra-step contact with tower 2 at step 52, 6.3 µm |
| final_b | hybrid, DNp15 ablation (constant +0.102) | ✓ | ✓ | |
| final_c | brain only | ✗ | ✗ | no landing; intra-step tower contact in 18 steps |

The routes of final_a and final_b are almost identical: the route in effect comes from the hand-made layer.

### Final-v2, pre-registered ([REPORT_FINAL_V2.md](docs/tr/REPORT_FINAL_V2.md) §1–4; SPEC_SENSORY_INPUTS §3.3c)
- **DNp15 validation failed:** (a) open-loop optomotor sign 12/12; (b) hover + ±30° yaw perturbation failed (b1 6/6, b2 3/6, b3 3/6); (c) on static scenes |turn| < 0.3 failed (0/9). As the rule required, the DNp15 term was held at its perch baseline by ablation in the final runs.
- **final_v2a (hybrid): failed, S1 ✗, S2 ✓.** It landed (3.47 s) and fed (162 feeding steps), but at step 51 it penetrated the top edge of tower 2 by 130.9 µm within a step. With the new reference, the ablation constant amounts to a +0.244 right turn; the ablation is not a "brainless" baseline.
- **final_v2c (brain only): failed, S1 ✗, S2 ✗.** No landing; with a constant steering term it flew in circles (−532.1°). It touched no tower, but without touchdown S1 fails by definition.

### Additional control, post-hoc ([REPORT_FINAL_V2.md](docs/tr/REPORT_FINAL_V2.md) §6; SPEC §3.3d)
DNp15 term exactly 0 (`--no-brain-steer`), head reflex and postures on. This control was added **after** the result of final_v2a was known; its criteria were written before the runs, but its result does not replace final_v2a.

| run | S1 | S2 | touchdown | feeding steps | note |
|---|---|---|---|---|---|
| n1 (hybrid) | ✓ | ✓ | 3.02 s | 180 | route almost straight (+1.7°); closest to food 0.5 mm |
| n2 (brain only) | ✗ | ✗ | none | 0 | hit the face of tower 1 at step 36; contact in 264 steps |

n1 and final_v2a differ in three things (steering term, head, postures); attributing the difference to the steering term alone is a hypothesis.

### Multi-seed repeat ([REPORT_FINAL_V2.md](docs/tr/REPORT_FINAL_V2.md) §6.7; SPEC §3.3e)
- **n1** (seeds 10–14): S1 ∧ S2 5/5; MN9 > 10 Hz at the touchdown step: 5/5, lowest 15.7 Hz, highest 47.2 Hz.
- **n2** (seeds 10–14): S1 ∧ S2 0/5; no touchdown (the MN9 contact measure does not apply).
- **Interpretation:** because the steering term is 0, the route does not depend on the seed. Position, touchdown step and tower values are bit-identical to seed 3 in all five seeds. "S1 5/5" is therefore not five independent confirmations but five repeats of the same hand-made route.
- The only seed-dependent result is the feeding decision. Five seeds are a small sample for the error rate of this decision.

### Start position / heading test (SPEC §3.3f)
A test that does change the route: the take-off pedestal is shifted by ±40 mm (x/y) or the initial heading is rotated by ±30°/±60°; 8 conditions, seed 3, n1 configuration. Because the steering term is 0, this test measures the robustness of the **hand-made route/landing chain** and of the MN9 decision, not the brain's control of the route.

| condition | flag | S1 | S2 | touchdown (step / s) | MN9 at the touchdown step (Hz) | first feeding step | feeding steps | closest to food | total heading change | closest to a tower (before td) | tower contact (end of step) | intra-step tower contact (before td) | max. penetration | BADQACC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n1 | — (§3.3d n1) | ✓ | ✓ | 120 / 3.02 s | 15.7 | 120 | 180 | 0.5 mm | +1.7° | 4.4 mm | 0 | 0 | 0.0 µm | 0 |
| st_xp40 | `--start-offset 40 0` | ✓ | ✓ | 115 / 2.90 s | 0.0 | 116 | 184 | 0.5 mm | +1.6° | 4.7 mm | 0 | 0 | 0.0 µm | 0 |
| st_xm40 | `--start-offset -40 0` | ✓ | ✓ | 125 / 3.15 s | 23.6 | 125 | 175 | 0.5 mm | +1.9° | 4.1 mm | 0 | 0 | 0.0 µm | 0 |
| st_yp40 | `--start-offset 0 40` | ✓ | ✓ | 119 / 3.00 s | 0.0 | 120 | 180 | 0.4 mm | +1.7° | 4.0 mm | 0 | 0 | 0.0 µm | 0 |
| st_ym40 | `--start-offset 0 -40` | ✓ | ✓ | 121 / 3.05 s | 15.7 | 121 | 179 | 0.5 mm | +1.6° | 4.6 mm | 0 | 0 | 0.0 µm | 0 |
| st_yawp30 | `--start-yaw 30` | ✓ | ✓ | 120 / 3.02 s | 31.5 | 120 | 180 | 0.5 mm | -25.8° | 5.4 mm | 0 | 0 | 0.0 µm | 0 |
| st_yawm30 | `--start-yaw -30` | ✓ | ✓ | 118 / 2.97 s | 15.7 | 118 | 182 | 0.5 mm | +30.8° | 5.5 mm | 0 | 0 | 0.0 µm | 0 |
| st_yawp60 | `--start-yaw 60` | ✓ | ✓ | 116 / 2.92 s | 23.6 | 116 | 184 | 0.5 mm | -57.0° | 3.3 mm | 0 | 0 | 0.0 µm | 0 |
| st_yawm60 | `--start-yaw -60` | ✓ | ✓ | 114 / 2.87 s | 0.0 | 115 | 185 | 0.3 mm | +62.2° | 2.8 mm | 0 | 0 | 0.0 µm | 0 |

- **S1 ∧ S2: passed in 8/8 conditions**.
- S1 8/8, S2 8/8; touchdown 8/8; MN9 > 10 Hz at the touchdown step: 5/8 (lowest 0.0 Hz).
- touchdown → first feeding: 0–1 steps; closest to a tower (before td): 2.8–5.5 mm (n1 4.4 mm).
- route convergence (record): the heading comes within 5° of n1 at t = 1.02–1.42 s and stays there up to step 60; at t = 1.32 s the distance |Δy| from the n1 route is 0.2–5.2 mm.

- **Pre-registered result: S1 ∧ S2 in 8/8 conditions.**
- **Interpretation:** from different starts, the hand-made odour map pulls the route onto the same line (the heading comes within 5° of n1 at t = 1.02–1.42 s), and all eight runs cross over tower 2 at the same place, with the body centre 2.8–5.5 mm from the nearest tower surface. The edge that the pre-registered final_v2a penetrated by 130.9 µm is the top edge of this tower. The result shows that the hand-made route is robust over this range of starts, with a margin of a few mm; it is not evidence of route control by the brain.
- The feeding decision started 0–1 steps after touchdown in all 8 runs (MN9 at the touchdown step was 0.0 Hz in 3 runs and above threshold one step later).

Details: [REPORT_FINAL_V2.md](docs/tr/REPORT_FINAL_V2.md) §6.8.

## Negative findings
- **The DNp15 steering readout failed validation** (in two validations: seeds 3/4/5 and 6/7/8). It carries the optomotor sign, but because of its right-dominant baseline (perch L 0 / R 52 Hz) it does not give symmetric steering control in closed loop: it corrects a perturbation to the left and amplifies a perturbation to the right. The readout was chosen post-hoc.
- **DNg02 is silent in every run** (0 spikes): collective thrust and altitude cannot be read out from the brain.
- **DNp07 / DNp10 are not selective:** with the sB input, DNp07 fired in every phase window of final_v2a, perch included (50.0–82.2 Hz per side); DNp10 was one-sided (left 0.0–20.0 Hz, 0.0 only in the 4-step take-off window; right side 0.0 Hz in every window). Neither shows approach/landing selectivity; there is no candidate for a landing decision.
- **Olfaction: persistent state in the antennal lobe (AL).** Spontaneous ORN input to the 53 glomeruli (Hallem & Carlson 2006) drives the LN/PN loop of the AL into a self-sustaining state; the network does not decay when all inputs are cut (network rate 100–200 ms after the cut-off: 3.45 Hz (spiking APL, smoke run v17) and 1.96 Hz (graded APL, v18); criterion < 0.1 Hz). Literature transmitter signs (`--nt-literature`, 24 neurons) reduced it to 2.48 Hz (v20) and 1.55 Hz (v21) but did not remove it. Olfaction is off in the final runs. Details: REPORT_SENSORY_A.md, REPORT_SENSORY_A2.md.
- **Olfaction, stage O1 (no resting input):** driving only the 298 food-glomerulus ORNs for 1 s also leaves the network in the persistent state: 0 of 8 drive rates (10–200 Hz) returned to rest in 5/5 seeds, so the left/right test was not run (REPORT.md §3.7; `scripts/diag/o1_report.py`).
- **Olfaction under sign variants (MODEL VARIANTS `--nt-impute` N1 and N1 + `--nt-literature` N2, not the published model):** filling missing Codex transmitter predictions from the same cell type lowered the locked-up antennal-lobe rate (about 120 Hz published, 103 Hz N1, 86 Hz N2 after the cut) but 0 of 8 drive rates passed in 5/5 seeds under either variant, so O2 was not run; the sugar → MN9 open-loop drive is intact under both (REPORT.md §3.7, `scripts/diag/nt_report.py`). Closed-loop results belong to the published model.
- **Olfaction, comparison with the upstream drive:** the olfactory drive of the upstream walking script (2,279 olfactory-class neurons at a constant 80 Hz, not dependent on the odour value and never cut) did not decay under our O1 criterion either: 0 of 5 seeds passed (open loop, published model). The upstream demonstration does not test decay; the check changes no decision (REPORT.md §3.7, `scripts/diag/nf_report.py`).
- **Visual DN screen (open loop, pre-registered, published model):** ten body-frame visual stimuli (yaw gratings, looms, receding looms, expanding flow, static and grey) through FlyVis and the boundary layer into the full brain; 21 a-priori tests: 1 passed (DNp15, yaw; right-dominant even for a static grating), 8 failed, 12 silent (DNg02 and most loom clusters); exploratory screen: 1 pass (DNbe001, flow versus static) among 10 candidates of 575 pairs. No loom or landing cluster confirmed; the flight controller is unchanged (REPORT.md §3.8, `scripts/diag/vis_dn_report.py`). Loom follow-up in a collision-locked window (follow-up designed after these results were known; new window, new seeds): 0 of 20 a-priori tests passed, 4 failed, 16 silent; exploratory 0 pass among 10 candidates of 74 pairs (REPORT.md §3.8b, `scripts/diag/vl_report.py`). Training ladder, step 1, round 1 (pre-registered, REPORT.md §3.9, `scripts/diag/ladder_report.py`): the recording option and the 16 teacher (n1) flights from the training and validation starts are done; the teacher gets S1 in 13 of 16 and S2 in 16 of 16; no readout has been trained and no exam start has been flown. Round 2, trial 1 (REPORT.md §3.9b, `scripts/diag/ladder_trial1_report.py`, ledger `docs/ladder_trials.md`): the replay audit is exact (all spikes of the audited teacher flight reproduced); three ridge readouts (T1-real, T1-shuffled, T1-bypass) were fitted from the 12 training flights and flown on the 4 validation starts: 0 of 12 flights reach touchdown (S1 0/4 in every arm), no arm has a champion, the cross-validated R² is negative for turn and roll; step 1 was then stopped after trial 1 (decision of 2026-10-07, taken after the results were known; a deviation from the pre-registration, REPORT.md §3.9b "Status: stopped"). T1 not completed: no champion in trial 1 (S1 0/4 in all three arms); trials 2–4 and the exam were not run. No exam start has been used.
- **The leg GRN → MN9 path does not work:** when the 12 SA_VTV_2 neurons selected by connectivity are driven at 100 Hz, MN9 stays at 0.0 Hz (3/3 seeds). This is why the reported runs drive the labellar (proboscis) sugar GRNs on leg contact instead, a hand-made shortcut (see [What controls what](#what-controls-what)).
- **No run of the brain-only arm** (final_c, final_v2c, n2) landed.

## Limitations
- **Uniform LIF:** all neurons share the same parameters (the Shiu et al. 2024 model: v0 = vrst = −52 mV, vth = −45 mV, τ_m 20 ms, τ_syn 5 ms, refractory period 2.2 ms, delay 1.8 ms, w_syn 0.275 mV). Modulatory transmitters are treated as fast excitatory/inhibitory; no gap junctions, no adaptation.
- **No VNC:** the ventral nerve cord is not modelled. The path from descending neurons to the wings is a hand-made bridge; ascending neurons are not driven.
- **Post-hoc labels:** the DNp15 readout, the `--no-brain-steer` control and the n1/n2 runs were chosen after the pre-registered final result; they are marked "post-hoc" in the reports.
- **Almost all of the behaviour is hand-made;** the only decision that comes from the brain is feeding.
- **The single BRAIN decision depends on a hand-made sensory mapping:** leg (tarsus) contact with the platform is mapped by hand onto labellar sugar GRNs; with the leg GRNs chosen by connectivity, MN9 stays silent.
- **Single seed** (3) in the final runs; in the multi-seed repeat only the MN9 decision changes.
- Aerodynamics are quasi-steady and stroke-averaged; there is no proboscis joint (the proboscis is a visual marker only).
- Sensory transductions (vision, sugar contact) and some constants of the head reflex are marked as ASSUMPTION (SPEC §3.3d).
- The arena is artificial (towers, pedestal, platform), not a natural environment.
- **Pre-registration is internal:** criteria were committed to this repository before the runs, not registered externally (e.g. OSF); commit timestamps are not independent evidence ([docs/PREREGISTRATION_LOG.md](docs/PREREGISTRATION_LOG.md)).

## Reproducing the numbers
The numbers of the reports, the tables and the figures are recomputed from the stored run records; no simulation is needed. Three steps:
1. **Get the code** (this repository), install the environment ([Installation](#installation)) and run `env -u PYTHONPATH python scripts/fetch_data.py` once: it downloads the connectivity and annotation files from pinned commits and rebuilds the derivable input files (the FlyVis weights are needed: `flyvis download-pretrained`).
2. **Get the data bundle** (run records, about 4 GB, CC BY-NC 4.0; DOI to be added) and unpack it into the root of the repository, so that its `logs/`, `simulations/` and `data/` folders merge with the existing ones (`README_DATA.md` in the bundle lists the content, `SHA256SUMS` the checksums). A small folder of the three videos is published separately.
3. **Run** `env -u PYTHONPATH python scripts/verify_report_final.py`. It recomputes every number of README.md and REPORT.md from the run records and prints `ALL OK` (or the mismatches); `scripts/figures/make_figures.py` redraws the figures. Without the bundle it stops with "run records not present" and a non-zero exit code.

A **full re-run** of the experiments (not needed for the check above) uses the run scripts listed in REPORT.md §6 (`run_final.sh`, `run_natural.sh`, `run_seeds.sh`, `run_starts.sh`, …) and needs the Codex downloads (`scripts/fetch_data.py --codex-dir … --model-runs`, sign-in required). One 300-step full-brain flight run takes a few minutes and about 3.5 GB of RAM (REPORT.md §6); the open-loop screens of §3.7–§3.9 are batches of 40 to 125 runs (e.g. 125 runs in about 40 minutes for the visual DN screen, §3.8). A re-run of n1 (seed 3, 300 steps) reproduced the stored record bit for bit (`docs/reimpl_equivalence/`); the other runs were not repeated.

## Installation
Tested environment: Linux aarch64, 8 cores, no GPU, 15 GB RAM. One full run (300 steps, no video) uses ~3.5 GB RAM and takes ~6–9 min including set-up.

```bash
conda create -n neurofly python=3.10
conda activate neurofly
pip install -r requirements-flight.txt   # flight code only: packages it imports, tested versions
flyvis download-pretrained               # FlyVis weights used by the visual input
env -u PYTHONPATH python scripts/fetch_data.py --codex-dir ~/Downloads --model-runs   # data, see Data
```

Notes:
- **`env -u PYTHONPATH`:** if the shell profile adds the `PYTHONPATH` of another Python installation (e.g. ROS), packages can be shadowed. All commands are run with `env -u PYTHONPATH ...`; the `run_*.sh` scripts do this themselves.
- **pytest and ROS:** the ROS `launch_testing` plugin crashes pytest with `PluginValidationError`. Disable plugin autoloading: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.
- **Headless rendering:** `export MUJOCO_GL=egl`.
- The first run compiles Brian2's Cython code, which takes long; later runs use the cache.

## Running

```bash
export MUJOCO_GL=egl
# tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 env -u PYTHONPATH python -m pytest tests/

# short smoke test (20 steps, no video)
env -u PYTHONPATH python fly_flight_brain_body_simulation.py --hybrid --vision-boundary --no-olfaction \
    --dn-reference data/dn_lr_reference_sB.json --no-brain-steer --head-reflex --postures \
    --seed 3 --n-steps 20 --no-video --tag smoke

# n1 / n2 (SPEC §3.3d), detached
nohup bash run_natural.sh > logs/natural/nohup.out 2>&1 &
# multi-seed repeat (§3.3e) and start position / heading test (§3.3f)
nohup bash run_seeds.sh  > logs/seeds/nohup.out  2>&1 &
nohup bash run_starts.sh > logs/starts/nohup.out 2>&1 &

# report tables (Turkish by default; --lang en for the README wording) and the check of the report and
# README / REPORT.md numbers against the HDF5 files
env -u PYTHONPATH python scripts/diag/nat_report.py
env -u PYTHONPATH python scripts/diag/seeds_report.py [--lang en]
env -u PYTHONPATH python scripts/diag/starts_report.py [--lang en]
env -u PYTHONPATH python scripts/verify_report_final.py
```

Outputs are `simulations/flight_v<N>_<flags>_<tag>_data.h5` (behaviour, spike counts, metadata). Videos are rendered from the HDF5 file in a separate step (`render_flight_video_v2.py`); the simulation is not re-run. `--dev-subnet` is for development only; the output name contains `DEV` and it is not a result.

## Data
FlyWire data are **not placed** in this repository (licence CC BY-NC 4.0, see *Data and licences* below and [THIRD_PARTY.md](THIRD_PARTY.md) §2; size). Required files:

| file | location | source |
|---|---|---|
| `Completeness_783.csv`, `Connectivity_783.parquet` | `brain_model/` | Shiu et al. model repository ([philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model)), FlyWire v783 |
| `flywire_annotations.tsv` | `brain_model/` | Schlegel et al. 2024 ([flyconnectome/flywire_annotations](https://github.com/flyconnectome/flywire_annotations)) |
| `classification.csv.gz`, `consolidated_cell_types.csv.gz`, `neurons.csv.gz`, `neuropil_synapse_table.csv`, `synapse_coordinates.csv`, `coordinates.csv`, `column_assignment.csv.gz` | `~/Downloads/` (script argument) | [FlyWire Codex](https://codex.flywire.ai) downloads, materialization v783 |

The sources and generating scripts of the derived files in `data/` are listed in `data/README.md`; their licence status is in [THIRD_PARTY.md](THIRD_PARTY.md) §2.3. This snapshot contains no FlyWire, Codex or other third-party data file. Rebuild them with
`env -u PYTHONPATH python scripts/fetch_data.py --codex-dir <Codex downloads> --model-runs`: it downloads the Shiu et al. files and the FlyWire annotations from pinned commits (SHA-256 checked), rebuilds `brain_model/descending_neurons.csv` and the `data/` files, and prints a hash table against the files used by the reported runs. The Codex downloads need a sign-in; `--codex-help` prints step-by-step instructions. The HDF5 run files are not included (available on request); tests that need a missing data file are skipped.

## Videos
**This copy contains no video file and no HDF5 run file** (`.gitignore`: `*.mp4`, `*.h5`). The videos are rendered from the HDF5 run files (`run_videos_vis.sh`, render only, no simulation); the HDF5 files are available on request. The paths in the table below are where the scripts write the files.

**Video links: to be added.**

In every video the hand-made route takes the fly to the food; the brain decides to feed (the on-screen "brain odour input OFF" refers to the brain only; the route reads the simulator's odour field).

1920×1080, 30 fps, playback ×0.25.

| video | run | content |
|---|---|---|
| `simulations/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change_en_vis.mp4` | n1 | hybrid, S1 ✓ S2 ✓; follow camera, brain panel, circuit strip (33.6 s) |
| `simulations/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change_en_vis.mp4` | n2 | brain only, hits a tower (44.0 s) |
| `simulations/flight_n1_vs_n2_v2_compare_en_vis.mp4` | n1 \| n2 | side-by-side comparison (33.6 s) |
| `simulations/flight_v11/v12/v13_*_v2_change.mp4` | final_a / b / c | final-v1 runs |

The n1 / n2 / comparison videos have English on-screen text (`run_videos_vis.sh`; brain panel: one soft dot of equal size per neuron, fixed display gain per class, REPORT.md §3.6; title card "Synaptera", labels BRAIN / HAND-MADE / REFLEX / FLYVIS as above, end card with the NeuroFly credit and references). Earlier renders with the previous brain panel (`*_en.mp4`, `run_videos_en.sh`) and with Turkish on-screen text (same names without `_en`, `run_videos_natural.sh`) are kept and described in REPORT_FINAL_V2.md §6.6. In every video a persistent label states what is hand-made and what is brain; the FlyVis layer is labelled "display only, not driven". Older videos under `simulations/` (`flight_40s*`, `flight_biological_40s`, `flight_v01`–`v05`, `test_*`) are trials from before the closed loop; they are not results.

## Documents and repository layout
- `docs/tr/SPEC_FLIGHT.md`, `docs/tr/SPEC_BRAIN_CONTROL.md`, `docs/tr/SPEC_SENSORY_INPUTS.md`: design, user decisions and **pre-registrations** (each criterion was committed before the runs). In Turkish.
- `REPORT.md`: the English consolidated report (summary, methods, results, negative findings, limitations, reproducibility).
- `docs/tr/REPORT_FINAL.md` (final-v1), `docs/tr/REPORT_FINAL_V2.md` (final-v2, additional control, multi-seed repeat, start test), `docs/tr/REPORT_SENSORY_A/A2/B.md` (sensory stages). In Turkish.
- `fly_flight_brain_body_simulation.py` main loop; `flight/` modules (brain, body, bridge, hybrid controller, vision, olfaction, head reflex); `scripts/` data preparation and report scripts; `tests/flight` (pytest).
- `docs/tr/`: lab notebook in Turkish (reports and pre-registrations); `docs/`: provenance, adapted code, pre-registration log, snapshot manifest.

## References
- Dorkenwald, S. et al. (2024). Neuronal wiring diagram of an adult brain. *Nature* 634, 124–138. doi:[10.1038/s41586-024-07558-y](https://doi.org/10.1038/s41586-024-07558-y)
- Schlegel, P. et al. (2024). Whole-brain annotation and multi-connectome cell typing of *Drosophila*. *Nature* 634, 139–152. doi:[10.1038/s41586-024-07686-5](https://doi.org/10.1038/s41586-024-07686-5)
- Shiu, P. K. et al. (2024). A *Drosophila* computational brain model reveals sensorimotor processing. *Nature* 634, 210–219. doi:[10.1038/s41586-024-07763-9](https://doi.org/10.1038/s41586-024-07763-9)
- Wang-Chen, S. et al. (2024). NeuroMechFly v2: simulating embodied sensorimotor control in adult *Drosophila*. *Nature Methods* 21, 2353–2362. doi:[10.1038/s41592-024-02497-y](https://doi.org/10.1038/s41592-024-02497-y)
- Lappalainen, J. K. et al. (2024). Connectome-constrained networks predict neural activity across the fly visual system. *Nature* 634, 1132–1140. doi:[10.1038/s41586-024-07939-3](https://doi.org/10.1038/s41586-024-07939-3)
- Matsliah, A. et al. (2024). Neuronal parts list and wiring diagram for a visual system. *Nature* 634, 166–180. doi:[10.1038/s41586-024-07981-1](https://doi.org/10.1038/s41586-024-07981-1)
- Stimberg, M., Brette, R. & Goodman, D. F. M. (2019). Brian 2, an intuitive and efficient neural simulator. *eLife* 8, e47314. doi:[10.7554/eLife.47314](https://doi.org/10.7554/eLife.47314)
- Todorov, E., Erez, T. & Tassa, Y. (2012). MuJoCo: A physics engine for model-based control. *IROS 2012*, 5026–5033. doi:[10.1109/IROS.2012.6386109](https://doi.org/10.1109/IROS.2012.6386109)
- Hallem, E. A. & Carlson, J. R. (2006). Coding of odors by a receptor repertoire. *Cell* 125, 143–160. doi:[10.1016/j.cell.2006.01.050](https://doi.org/10.1016/j.cell.2006.01.050)
- Münch, D. & Galizia, C. G. (2016). DoOR 2.0 — comprehensive mapping of *Drosophila melanogaster* odorant responses. *Sci Rep* 6, 21841. doi:[10.1038/srep21841](https://doi.org/10.1038/srep21841)
- Hengstenberg, R. (1988). Mechanosensory control of compensatory head roll during flight in the blowfly *Calliphora erythrocephala* Meig. *J Comp Physiol A* 163, 151–165. doi:[10.1007/BF00612425](https://doi.org/10.1007/BF00612425) (related literature on head-roll compensation in flies; not the source of the constants of the head reflex, which are hand-set; the paper could not be opened, only its bibliographic record was checked)
- Head reflex, yaw gain G_yaw 0.6, angle limit θ_max 15°, reset saccade 9°: hand-set; motivated by the fly gaze-stabilisation literature; not traced to a specific source. Related literature (not the source of these constants): Davis, B. A. & Mongeau, J.-M. (2023). The influence of saccades on yaw gaze stabilization in fly flight. *PLoS Comput Biol* 19, e1011746. doi:[10.1371/journal.pcbi.1011746](https://doi.org/10.1371/journal.pcbi.1011746) · Cellini, B., Salem, W. & Mongeau, J.-M. (2022). Complementary feedback control enables effective gaze stabilization in animals. *PNAS* 119, e2121660119. doi:[10.1073/pnas.2121660119](https://doi.org/10.1073/pnas.2121660119). Earlier versions cited the constants to "Cellini, Salem & Mongeau 2022, *PLoS Comput Biol* 18:e1011746", a citation that mixes these two papers; the pre-registration text (SPEC_SENSORY_INPUTS §3.3d) is kept unchanged with a dated correction note.
- Parameter sources of the hand-made layer and the data provenance: [THIRD_PARTY.md](THIRD_PARTY.md) §2 and §6.

## Related work
Full list with sources, access date and what each source states about itself: [REPORT.md, Related work](REPORT.md#related-work).
- **Brain–body fly projects** that couple a connectome to a simulated body include Eon Systems PBC (web page, March 2026), the Uploading Lab fly pages, Lulzx/fly-brain, Jin et al. (arXiv:[2602.17997](https://arxiv.org/abs/2602.17997), connectome as a controller trained with reinforcement learning) and NeuroFly, which this work builds on ([NOTICE.md](NOTICE.md), [THIRD_PARTY.md](THIRD_PARTY.md)).
- **Nerve-cord connectomes** (MANC, BANC, male CNS) are listed with the licence statements of their data pages; this work uses the brain-only FlyWire v783 model and has no ventral nerve cord.
- **How this work differs** is limited to method: unmodified published model, criteria written to the repository before the runs, a source label on every component, a shuffled-connectome control, reported negative results.

## AI use
The code, the documentation and the figures of this repository were written with AI assistance (Claude, Anthropic), under the direction of the author (omeruk). The research question, the experimental design, the pre-registration decisions and the interpretation of the results are the author's. The numbers in this README, in the reports and in the figures are reproduced by scripts from the raw run records (HDF5 and npz files) and checked against the text (`scripts/verify_report_final.py`, `scripts/diag/*_report.py`, `scripts/figures/make_figures.py`), not transcribed by hand. The related-work entries and bibliographic data were opened and checked on 2026-10-07 (`docs/ORIGINALITY_CHECK.md`). `docs/NEUROFLY_FLIGHT_YENI_PROJE_MASTER_DONUSUM_REHBERI.md` (a draft) and the earlier flight attempts in `archive/flight_attempts/` were written by another AI tool before this work; the draft was used as a reference only and the attempts are not used (neither is in the public snapshot).

## How to cite
Cite this work through [CITATION.cff](CITATION.cff) (author: omeruk, version 1.0.0, 2026-10-07; repository URL and DOI to be added), and cite the FlyWire, Shiu et al., NeuroMechFly/FlyGym and FlyVis papers listed in [NOTICE.md](NOTICE.md).

## Licence
- **Code written in this work: MIT** ([LICENSE](LICENSE), Copyright (c) 2026 omeruk).
- **MIT does not cover third-party components:** the Shiu et al. brain-model code (its own MIT licence and copyright line, reproduced in [NOTICE.md](NOTICE.md)), FlyGym / NeuroMechFly (Apache-2.0), FlyVis and the other dependencies keep their own licences; FlyWire data are CC BY-NC 4.0 and are not distributed in this repository.
- **Results derived from FlyWire** (`figures/data/*.csv`, the result JSON files under `docs/`) and the separate data bundle are **CC BY-NC 4.0**; this work is non-commercial.
- **NeuroFly (upstream):** ideas of a few flight functions were adapted from NeuroFly and are credited ([docs/ADAPTED_CODE.md](docs/ADAPTED_CODE.md)). The upstream repository has no licence file; the licence question was sent to its author and has not been answered up to 2026-10-07. The affected code was re-implemented from a written specification (not a clean-room process: the same AI-assisted process had read the upstream code earlier). If the upstream author asks, the affected parts will be removed. Upstream files are not included in this copy.
- **Data:** third-party data keep their own licences (FlyWire, FlyWire Codex, Shiu et al., DoOR.data; [THIRD_PARTY.md](THIRD_PARTY.md) §2); see *Data and licences* below.

## Data and licences
1. **FlyWire data are not distributed in this repository.** `scripts/fetch_data.py` downloads the connectivity, annotation and model files from their sources (pinned commits, SHA-256 checked) and rebuilds the derived files; the FlyWire Codex downloads need a sign-in (`--codex-help`).
2. **Run records derived from FlyWire** (HDF5 behaviour and spike records, `logs/` summaries) are shared in a separate data bundle (DOI to be added), under **CC BY-NC 4.0** with attribution to FlyWire. FlyWire states that its public release data, version 783, is made available under CC BY-NC 4.0 ([flywire.ai/guidelines](https://flywire.ai/guidelines), opened 2026-10-07); the same licence is applied to everything derived from it, including the figures.
3. **This work is non-commercial** research; the CC BY-NC 4.0 restriction is respected throughout.
4. **Attributions to give when using the data or the records:** Dorkenwald, S. et al. (2024), *Nature* 634, 124–138, doi:10.1038/s41586-024-07558-y; Schlegel, P. et al. (2024), *Nature* 634, 139–152, doi:10.1038/s41586-024-07686-5; Matsliah, A. et al. (2024), *Nature* 634, 166–180, doi:10.1038/s41586-024-07981-1 (visual columns); Shiu, P. K. et al. (2024), *Nature* 634, 210–219, doi:10.1038/s41586-024-07763-9 (the model); FlyWire Codex (codex.flywire.ai) for the downloads. The FlyWire citing-guidelines page names no specific paper to cite and points to its citation guide, so this list is our own reading of what was used; please check the guide for your use.

Third-party licences and attributions: [NOTICE.md](NOTICE.md); full audit: [THIRD_PARTY.md](THIRD_PARTY.md). Citation information: [CITATION.cff](CITATION.cff).
