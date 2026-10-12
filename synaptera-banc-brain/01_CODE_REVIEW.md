# 01 — Code review: bugs, gaps and high-severity findings

Date: 2026-10-12. Scope: `fly_flight_brain_body_simulation.py`, `flight/` (19 modules), `simulation_data/odor_field_3d.py`,
`scripts/` (data, analysis, report and figure scripts), `tests/` (19 test files), the run scripts (`run_*.sh`), and the
Shiu et al. `brain_model/model.py` (downloaded, SHA-256 verified).

Method: all core code read line by line; `ruff` static analysis (pyflakes + bugbear); the test suite run with Python 3.10
and the pinned package versions (x86_64, 4 cores); the data-derivation scripts re-run and their SHA-256 compared with the
development copy; an independent structural analysis of FlyWire v783 and an open-loop Shiu-LIF simulation
(`02_CONNECTOME_MODEL_PHYSICS_TESTS.md`).

**Overall:** the code base is unusually disciplined for research software: every motor term is recorded and labelled
separately, the origin of each constant is in the comments, the HDF5 schema is documented, report numbers are checked by a
script and data files are pinned by hash. Most findings below are at the **design/method** level; no code bug was found
that invalidates the reported results. Severity: **H** (high), **M** (medium), **L** (low).

---

## A. High-severity findings (H)

### H1 — Within-step causality violation in the brain–body co-simulation (lockstep)
`fly_flight_brain_body_simulation.py:451` → `:526`: in every decision step `brain.step()` first runs the brain over
[t, t+25 ms]; the command derived from the spikes of that interval is then applied to the **same** [t, t+25 ms] physics
interval. The body is driven by spikes that have not yet happened in physical time (up to 25 ms "in the future"), while the
visual input comes from frames rendered in the previous step. Result: a sensorimotor latency between 0 and 25 ms that is
acausal within the step; the real fly's visuomotor latency is tens of milliseconds and cannot be zero.
- **Impact:** the reported n1/n2 flights are unaffected (the brain steering term is 0), but the DNp15 closed-loop
  validation (b1–b3) and every future brain-controlled flight get a wrong loop gain/stability estimate.
- **Fix:** a queue that delays the command by one step (the brain output of step k is applied in step k+1; the "body one
  interval behind" design of Fly.exe), or finer coupling (e.g. 5 ms brain / 5 ms body sub-steps). The latency should be an
  explicit, recorded parameter.

### H2 — Left/right reconstruction asymmetry is not checked when choosing readouts
Independent analysis in this session (`scripts/dn_lr_asymmetry.py`): among the 383 DN types with exactly one neuron per side
in FlyWire v783, the median right/left ratio of input synapses is 1.17×; 24.8 % differ by >1.41× and 11.5 % by >2×.
**DNp15 right/left = 1.66× (65th most asymmetric of 383)**, excitatory input 1,126 / 636 (1.77×). **DNp10 = 0.24× (8th).**
This explains two reported negative findings **structurally** (DNp15's "right-dominant baseline", perch L 0 / R 52 Hz;
DNp10 being "one-sided"). The pre-registered primary readout DNa02 is symmetric (1.07×).
- **Fix:** a pre-registered **symmetry gate** for every lateral readout (e.g. |log2(R/L)| < 0.5 for both total and
  excitatory input) and/or a mirror-symmetrised connectome control arm.

### H3 — Information mismatch in the training ladder
`flight/readout_model.py` + `--readout-model`: the teacher's turn command (`turn_hand`) comes from the simulator's **odour
field**, while in the T1 arms the brain's olfactory input is off (`--no-olfaction`) and it receives vision only. The
readout is asked to extract from DN activity information the brain never receives (the report's own interpretation points
the same way; turn R² < 0 in every arm). In addition **986** of the 1,299 DN features are constant (silent) over the
training flights.
- **Fix:** the teacher signal and the brain's sensory input must carry the same information (e.g. a visually defined
  route, or a working olfactory input); DAgger rounds; the λ grid was saturated at its edge (1000,
  `readout_model.py:20`) → extend the grid.

### H4 — Visual sampling is too slow for the flight speed (motion aliasing)
`flight/visual_input.py`: 2 renders per decision (80 Hz, `VIS_SUBFRAMES = 2`, FlyVis dt 12.5 ms). At 300 mm/s cruise and
4.4 mm from a tower the angular velocity is ~3,900°/s → ~49° shift per frame; at 10 mm ~21°/frame; at 50 mm ~4.3°/frame.
With ~5° ommatidial spacing the T4/T5 motion signal near obstacles is aliased/unreliable.
- **Impact:** brain input for visual obstacle avoidance or optic-flow landing can be physically corrupted; the open-loop
  screens (slow stimuli) are fine.
- **Fix:** more sub-frames in near-obstacle phases (e.g. 8–10 per step), or run FlyVis with a smaller dt; measure the
  rendering cost.

### H5 — Wing stroke amplitude has no physical limit
`flight/quasi_steady.py:68` (`wing_lift ∝ Φ²`), `controller.py:64`, `hybrid.py:180`: no upper bound on the amplitude.
With the upper end of `LIFT_FRAC_RANGE` (1.8) and a 20° tilt the collective amplitude reaches 193.8°, and with the turn
difference 206.3° (the geometric limit is ~180°; Drosophila approaches it in manoeuvres). The quasi-steady `Φ²` scaling is
an extrapolation there.
- **Fix:** clip Φ at ≤ ~180° (or a lower value chosen from the literature) and record clip events; cover the missing
  thrust with frequency when saturated.

---

## B. Medium-severity findings (M)

| code | finding | where | fix |
|---|---|---|---|
| M1 | **Silent overwrite:** with an explicit `--version` and the same flags, `DisplayWriter` (`"w"`) and `write_h5` (`mode="w"`) delete an existing result HDF5 without warning | `flight/vision_boundary.py:470`, `flight/recorder.py:280` | stop if the file exists (or an `--overwrite` flag) |
| M2 | **Hard dependency on Codex data:** `build_groups` always reads `column_assignment.csv.gz` (Codex, sign-in required); even experiments without vision cannot build the brain | `flight/groups.py:151` | build the T4/T5 groups only when vision is on |
| M3 | **Shuffled null control is not activity-matched:** the postsynaptic permutation can duplicate (pre, post) pairs; the shuffled brain produces 2.5× the DN spikes on the same inputs (REPORT §3.9b) → "wiring" and "activity level" effects are confounded | `flight/brain.py:203` | activity-matched normalisation, shuffling within cell class/neuropil, a second null (Erdős–Rényi with the same degrees) |
| M4 | **Poisson input path deviates from the model:** Synaptera uses `PoissonGroup → Synapses(delay=1.8 ms)`; Shiu's `PoissonInput` has no delay. The 68.75 mV kick (threshold gap 7 mV) turns every input spike into a forced output spike; with refractoriness off, the 34,121 boundary neurons become pure spike generators and their recurrent input becomes irrelevant | `flight/brain.py:315` | footnote to the "unmodified model" statement; a current-injection variant for graded cells |
| M5 | **Seeds are not independent:** `--seed` seeds only Brian2; physics is deterministic → with steering 0 the route is bit-identical (the report states this correctly) | main script | a variant seeded with physical noise (gusts, sensor noise) |
| M6 | **Private FlyGym API:** `_update_vision`, `_last_vision_update_time`, `_curr_visual_input`, `_floor_contacts`; `sim.step()` bypassed with direct `physics.step()` | `flight/body.py:145-150, 387, 433-435` | keep versions pinned; regression test on any FlyGym upgrade |
| M7 | **Reproducibility hashes are platform-sensitive:** in this session `data/t45_transduction.json` was rebuilt and its SHA-256 differed (x86_64 + torch 2.14.1 vs aarch64 + 2.14.0); floating-point differences in JSON break a bit-level comparison | `scripts/fetch_data.py` (EXPECTED) | add a numeric-tolerance comparison (e.g. rtol 1e-6) |
| M8 | **Yaw validation baseline:** the DNp15 normalisation subtracts a per-side reference and divides by a common scale; the reference comes from one stimulus (sym_prog) — because of H2, `s_hat` is large even for a static scene | `flight/vnc_bridge.py` | the gate of H2 |
| M9 | **Quasi-steady model details:** lift along body z (no stroke-plane angle); isotropic counter-force; the turn command increases total lift by `d²` (~0.8 %); fixed roll–yaw coupling | `flight/quasi_steady.py` | flybody wing model, or stroke-plane angle + anisotropic damping |
| M10 | **Ridge grid at its edge:** λ = 1000 (grid maximum) chosen for every command/arm; 1,412 samples / 1,299 features | `flight/readout_model.py:20` | extend the grid; handle silent features up front |

---

## C. Low-severity findings (L)

- **L1** `FlyVisEyes.step` / `BoundaryEyes.step`: the loom term uses the activity of the **last sub-frame** instead of the
  sub-frame mean (`visual_input.py:257`, `vision_boundary.py:446`); an empty `frames` list causes a division by zero /
  undefined variable.
- **L2** `Bridge.update`: with ablation on, using it before `set_baseline` raises a `None` indexing error
  (`vnc_bridge.py:90`); the order in the main loop is correct, scripts are at risk.
- **L3** `del brain, body, eyes, ...` at the end of the main script (`:759`) deletes closure variables; static analysis
  reports 9 "undefined name" (F821). No runtime problem, but fragile.
- **L4** Hard-coded paths: `PATH_CODEX_TYPES = ~/Downloads/...` (`vision_boundary.py:52`); run scripts use
  `PY=$HOME/miniforge3/envs/neurofly/bin/python` (overridable by an environment variable).
- **L5** `tests/conftest.py:23`: 25 walking scripts absent from the snapshot are listed in `collect_ignore` (harmless, stale).
- **L6** `FlightBrain(dev_subnet=True, shuffle_seed=...)`: the shuffled control is silently ignored on the DEV subnet.
- **L7** After a crash, a half-written HDF5 holding `/flyvis` but no `meta` can remain under a result-like name.
- **L8** `ruff` (F + B rules): 117 findings, mostly unused imports/variables and `zip(strict=)` style. All `B023`
  (loop-variable closure) warnings were checked: the lambdas are called within the same iteration → **not real bugs**.
- **L9** `SpikeMonitor` keeps every spike of the run in memory (~3.5 GB for 7.5 s); longer flights need streaming.

---

## D. Gaps (features/scope)

1. **No VNC:** the DN → wing path is a hand-made bridge; the ascending neurons (1,736) are never driven (REPORT §5).
2. **No resting activity:** the network is silent without input; most DNs stay silent (986/1,299 constant features).
3. **Neuron model:** uniform LIF; no gap junctions, adaptation, graded (non-spiking) neurons or neuromodulation.
4. **The olfactory circuit locks up** (structural cause: `02_CONNECTOME_MODEL_PHYSICS_TESTS.md` §1.6).
5. **No proboscis joint**; the MN9 decision is a visual marker only.
6. **Route, altitude, landing and reflexes are hand-made**; the brain only makes the feeding decision.
7. **No external pre-registration** (OSF etc.); commit timestamps are not independent evidence (the repository says so).
8. **Test coverage:** full-brain tests are marked `slow` and do not run without Codex data; an independent user of the
   public snapshot can run only the pure-function and physics tests.
9. **The data bundle and videos are not published yet** (DOI "to be added"); `verify_report_final.py` does not run without the bundle.

---

## E. Checks run in this session

| check | result |
|---|---|
| Shiu model files + FlyWire annotations (5 files) | SHA-256 **identical** to the constants in fetch_data.py |
| Derived `descending_neurons.csv`, `sugar_grn_783.csv`, `leg_sugar_grn_783.csv`, `orn_spontaneous_783.csv` | 4/4 **identical** to the development copy |
| `t45_transduction.json` (FlyVis weights downloaded) | rebuilt; SHA-256 **differs** (platform/torch difference; see M7) |
| 8 files that need Codex | could not be built (sign-in required) |
| `pytest tests/` | see `02_CONNECTOME_MODEL_PHYSICS_TESTS.md` §5 |
| Static analysis (ruff F, B) | 117 findings; no real bug (L8) |
| Independent Shiu-LIF open loop (GRN → MN9) | see `02_CONNECTOME_MODEL_PHYSICS_TESTS.md` §5 |

## F. Priority fix list (for the existing repository)

1. (H1) Causal coupling with a command queue + latency parameter.
2. (H2) L/R symmetry report and readout gate (`scripts/dn_lr_asymmetry.py` can be the basis).
3. (M1) Prevent overwriting result files.
4. (M2) Require the T4/T5 column file only when vision is on.
5. (H5) Stroke-amplitude clipping + recording.
6. (M7) Numeric tolerance in the hash comparison.
7. (H4) More visual sub-frames in near-obstacle phases.
8. (L1–L3) Small clean-ups.

Decision taken later (see `06_NEW_PROJECT_SETUP.md`): these fixes are not patched into Synaptera v1.0.0 but built into the
design of the new project.
