# Code adapted from NeuroFly

Audit date: 2026-10-05 (branch `sensory-inputs`, HEAD `1d133f8`). Upstream = NeuroFly at `b59264a`
([seven-monarchs/NeuroFly](https://github.com/seven-monarchs/NeuroFly), no licence file, see
[THIRD_PARTY.md](../THIRD_PARTY.md) §1).

**Answer: no line was copied verbatim, but parts of the flight code were adapted from the NeuroFly walking
script** `fly_brain_body_simulation.py` (same logic, same formulas, same constants, same pandas idioms,
rewritten as functions). An earlier statement in THIRD_PARTY.md §4.1 ("No verbatim code lines … were found")
is true for verbatim lines only; it did not cover adaptation. This file lists the adaptations.

Method: (1) normalised line comparison (whitespace collapsed, lines ≥ 25 characters, imports and comments
excluded) of every `.py`/`.sh` file of this work outside `archive/` against the upstream Python files
(`fly_brain_body_simulation.py`, `generate_plots.py`, `brain_model/utils.py`, the 25 walking tests) and
against `archive/flight_attempts/`; (2) `git log -C --find-copies-harder` over `b59264a..HEAD` (no code file
was created as a copy); (3) manual reading of every place where the flight code says "walking" or "legacy".
Line numbers refer to HEAD `1d133f8`; upstream line numbers to `b59264a:fly_brain_body_simulation.py`.

## A. Adapted code, current state (2026-10-07, after the re-implementation of section E)

Line numbers refer to the working tree of branch `sensory-inputs` after commit `524d81a`; upstream line numbers as in A0.

| # | file:lines (this work) | what | upstream lines | status now |
|---|---|---|---|---|
| 1 | `flight/groups.py:38-39` | keyword patterns `OLFACTORY_PATTERN`, `SEZ_PATTERN` (identical strings; they define which neurons count as olfactory / gustatory) | 302, 327 | unchanged; recorded groups, not driven in n1 |
| 2 | `flight/groups.py:93-161` (`_text_hits`, `_by_side`, `_annotation_groups`, `build_groups`) | same grouping rule as before (keyword match over `cell_class` / `cell_type` / `super_class`, ascending by `super_class`, split by `side`, DN list by `side`); code and names written from the specification (section D.1) | 281-297, 306-320, 327-336 | **re-implemented** (`056df11`); outputs identical to the recorded groups (section E) |
| 3 | `flight/groups.py:352-366` (`neuron_positions`) | soma position, else mean synapse position; written from section D.2 | 337-355 | **re-implemented** (`056df11`); identical to the recorded positions |
| 4 | formerly `flight/controller.py:31-43` (`dn_lr`, `turn_terms`) | all-DN turn term of the walking code | 719-721, 824-827 | **moved** to `archive/adapted_originals/controller_before_reimpl.py` (`--legacy-control` only; not in the public copy) |
| 5 | formerly `flight/controller.py:89-137` (timed feeding phases of `PhaseMachine`) | `feed_extend → feed_eat → feed_retract` timers | 788-806 | **moved** to the same archive file; `PhaseMachine` (`flight/controller.py:73-112`) has no feeding timers |
| 6 | `flight/hybrid.py:94-101` (`turn_hand`) | odour turn map `ODOR_TURN_K·tanh(ODOR_TURN_GAIN·I_asym)`: the form and `ODOR_TURN_GAIN` are the idea of the walking code, `ODOR_TURN_K` differs (2.0 here, 2.5 upstream) | 824 | **re-implemented** (`056df11`); **used in n1** (hand-made navigation term) |
| 7 | `flight/sensors.py:56-68` (`LoomBias`) | FlyVis T5 loom bias: gain, persistence and clamp as in the walking code (idea and numbers), code written from section D.4 | 702-708 | **re-implemented** (`056df11`); **used in n1** (FLYVIS term) |
| 8 | `flight/config.py:57-58, 158-164` | constants: antenna half-separations, `ODOR_TURN_GAIN`, `ODOR_TURN_K`, `TURN_BIAS_MAX`, `FLYVIS_T5_GAIN/DECAY/BIAS_MAX` (`K_DN_TURN`, `VIS_RATE` and the feeding times were moved out) | 125, 158-159, 164-166, 193, 824-826 | partly used (`ODOR_TURN_*`, `FLYVIS_*` in n1) |
| 9 | `scripts/diag/nf_report.py`, `scripts/diag/so_o1_nf.py` | comparison check of REPORT §3.7: the quoted upstream code strings are replaced by line numbers and SHA-256 hashes of the stripped lines; the two keyword selections are built from keyword lists (same patterns) | cited lines listed in `nf_report.CITED` | **changed 2026-10-07**; counts and results unchanged |

Similarity measured by script after the change: `scripts/check_originality.py` and `docs/ORIGINALITY_CHECK.md` (longest identical block of meaningful lines between any file of the public copy and any upstream `.py`/`.sh` file: 1 line).

## A0. Adapted code before the re-implementation (audit of 2026-10-05, kept as the record of that state)

| # | file:lines (this work) | what | upstream lines | used in the final configuration (n1)? |
|---|---|---|---|---|
| 1 | `flight/groups.py:38-39` | regex `OLFACTORY_PATTERN`, `SEZ_PATTERN` (identical strings) | 302, 327 | groups are built and recorded; not driven in n1 |
| 2 | `flight/groups.py:88-125` (`build_groups`, legacy part) | `find()` = `_find_ids` (regex over `cell_class`/`cell_type`/`super_class`); ascending = `super_class == "ascending"`; LA>ME split by `side`; DN split by `side` from `descending_neurons.csv` | 281-297, 306-320, 327-336 | yes (DN and recorded groups) |
| 3 | `flight/groups.py:333-346` (`neuron_positions`) | soma position, else `pos_x/pos_y`, same `.where(.notna())` idiom | 337-355 | rendering only |
| 4 | `flight/controller.py:31-43` (`dn_lr`, `turn_terms`) | DN asymmetry `(L−R)/(L+R+1e-6)`; turn = `K·tanh(20·I_asym) + 0.15·ΔDN + b_loom` (here ΔDN is baseline-subtracted) | 719-721, 824-827 | no (`--legacy-control` only) |
| 5 | `flight/controller.py:89-137` (`PhaseMachine`, timed feeding) | phase names and timers `feed_extend → feed_eat → feed_retract` | 788-806 | no (`--legacy-control` only) |
| 6 | `flight/hybrid.py:94-100` (`turn_hand`) | odour turn map `ODOR_TURN_K·tanh(ODOR_TURN_GAIN·I_asym)` of the walking code | 824 | **yes** (hand-made navigation term) |
| 7 | `flight/sensors.py:55-68` (`LoomBias`) | FlyVis T5 loom bias: `−GAIN·(L−R)`, exponential persistence, clip | 702-708 | **yes** (FLYVIS term `b_loom` of the turn command) |
| 8 | `flight/config.py:58, 147, 160-165` | constants: antenna half-separation 0.5 mm, `VIS_RATE` 20–150 Hz, `ODOR_TURN_GAIN` 20, `K_DN_TURN` 0.15, `FLYVIS_T5_GAIN/DECAY/BIAS_MAX` 0.5/0.5/0.15 (`ODOR_TURN_K` differs: 2.0 here, 2.5 upstream) | 125, 158-159, 164-166, 193, 824-826 | partly (`ODOR_TURN_*`, `FLYVIS_*` in n1) |

## B. Weaker similarities (structure, names, standard API use)

| file:lines | what | upstream |
|---|---|---|
| `flight/recorder.py:215-238` | HDF5 group names `meta`, `behavior`, `spikes`, `positions` (schema otherwise different) | 1249-1313 |
| `render_flight_video.py:44`, `render_flight_video_v2.py:80` | spike glow time constant 80 ms; frontal soma projection of every neuron | 148, 337-355 |
| `generate_flight_plots.py` | plot list and file names `01_circuit_timeline`, `02_raster_circuits`, `05_population_heatmap`, `06_firing_rate_distribution`, `07_odor_olfactory_response`, `08_visual_lamina_*` (code written anew) | `generate_plots.py` |
| `flight/visual_input.py:152-245` | FlyVis loop: `NetworkView(flow/0000/000)`, best checkpoint, grey steady state, `vision.max(axis=2)` → `RetinaMapper.flygym_to_flyvis` (standard FlyVis/FlyGym API use) | 579-597, 688-700 |
| `simulation_data/odor_field_3d.py` | idea only: odour as Dijkstra path distance around obstacles (re-implemented in 3D with `scipy.sparse.csgraph`; different concentration law, trilinear lookup) | 202-262 |

## C. Not from NeuroFly

`flight/brain.py:266-285` (Poisson input groups → `Synapses` with `w_syn·f_poi`, model delay, `rfc = 0`)
follows `poi()` in Shiu et al.'s `brain_model/model.py` (MIT, Copyright (c) 2023 Philip Shiu and Nico
Spiller), which the walking code also follows.

## D. Specification used for the re-implementation

Written 2026-10-07, before any code was changed. The re-implementation of the parts that are **active in the
reported runs** (n1, n2, final_a/b/c, final_v2a/c, final_sA/sB, the 16 teacher flights, the T1 replays/flights; flight
code paths `--hybrid`, brain-only, `--readout-model`) is written from this text only. It was derived from this
work's own SPEC/REPORT texts and from the recorded behaviour (HDF5 fields), not from the old lines. Constants are
listed with their source: **hand-set** = chosen in this work (SPEC_FLIGHT / SPEC_BRAIN_CONTROL decision),
**upstream idea** = the value or the form was taken over from the NeuroFly walking script (the idea and the number,
not code); these are the items the upstream author could be asked about.

Parts that are **not active** in any reported run (`--legacy-control` only: the all-DN turn term and the timed
feeding phases, rows 4 and 5 of table A) are not specified; they are moved to `archive/` (status in the section
"Status of the re-implementation").

### D.1 Neuron groups from the annotation table (`flight/groups.py`, legacy part of `build_groups`)

*Inputs.* `root_ids`: the root ids in the row order of `Completeness_783.csv` (index of a neuron = its row).
`ann`: the FlyWire annotation table (`flywire_annotations.tsv`; columns `root_id`, `cell_class`, `cell_type`,
`super_class`, `side`). `dn`: `descending_neurons.csv` (columns `root_id`, `cell_type`, `side`).
*Output.* A dict name → strictly increasing `int64` array of Completeness row indices.

1. Only annotation rows whose `root_id` is in `root_ids` are considered. A root id that is selected but missing from
   `root_ids` is ignored (cannot happen after the first filter; also applied to the `dn` table).
2. `side(x)` = `str(x).strip().lower()`. "left" and "right" are the two sides; **every other value** (including
   missing, which becomes the text "nan", "center", "") is "no side" (C).
3. `match(pattern)` selects a row if, for **at least one** of the columns `cell_class`, `cell_type`, `super_class`,
   `re.search(pattern, str(value).lower())` finds a match (missing values are the text "nan").
4. Groups:
   - `ascending`: rows with `super_class == "ascending"` (exact, case-sensitive).
   - `olf_L`, `olf_R`, `olf_C`: `match(OLFACTORY_PATTERN)` split by side into left / right / no side.
   - `sez`: `match(SEZ_PATTERN)`, not split.
   - `vis_L`, `vis_R`: rows with `cell_class == "LA>ME"` (exact), split into left / right. A row without side is an
     error (`ValueError`), checked before any other group is used.
   - `brain_mn`: rows with `cell_class == "brain_motor_neuron"` (exact).
   - From `dn` (rows by `side`): `dn_L`, `dn_R`, `dn_C` (all descending neurons by side);
     `dng02_L`/`dng02_R`: `cell_type` equal to `DNg02` or starting with `DNg02_`, by side;
     `steer_L`/`steer_R`: `cell_type` in {`DNa01`, `DNa02`}, by side; `dnp01`: `cell_type == "DNp01"` (no side split).
5. Constants. `OLFACTORY_PATTERN = "olfactory|olfactori|\\born\\b|projection.neuron"` and
   `SEZ_PATTERN = "sez|fdg|feeding|subesophageal|pharyngeal|gustatory"`: **upstream idea**, the strings are identical
   to the walking script's (they define which neurons the walking script calls olfactory / feeding; REPORT §3.7 reports
   that the olfactory pattern selects 2,279 neurons, 2,275 ORNs and no projection neurons). They are kept character for
   character because the recorded groups depend on them. The column list, the "LA>ME" and "brain_motor_neuron"
   classes, the DNg02/DNa01/DNa02/DNp01 types and the `dn` table are **hand-set** (this work).
6. Expected sizes (group_counts of the recorded runs): ascending 1,736; olfactory 2,279; sez 408; dn 1,299; LA>ME
   8,025; DNg02 25; steer 4; DNp01 2; brain_mn 105.

### D.2 Frontal soma positions for the brain panel and the HDF5 `positions` group (`neuron_positions`)

*Inputs.* `root_ids`; the annotation columns `root_id`, `soma_x`, `soma_y`, `pos_x`, `pos_y` (FlyWire 4 nm voxels).
*Output.* `x` (float32), `z` (float32), `idx` (int32), equal length, sorted by `idx` (the Completeness row index).
For each annotation row whose `root_id` is in `root_ids`: `x0 = soma_x` if it is present, else `pos_x`; `y0 = soma_y`
if present, else `pos_y` (each coordinate is replaced independently). The row is kept only if both `x0` and `y0`
are present. `x = x0`, `z = -y0` (dorsal up in the panel), cast to float32. Rows are ordered by increasing
`idx` with `numpy.argsort` (default kind; root ids are unique, so the order is unambiguous). Rendering and the
`positions` record only; no command depends on it. Source of the choice "soma, else centroid": **hand-set**
(the walking script's brain panel does the same: **upstream idea**).

### D.3 Odour turn term `turn_hand` (`flight/hybrid.py`)

*Inputs.* `I_asym` (float): normalised left-right odour contrast at the antennae, `(R - L)/(R + L + 1e-12)` computed by
`sensors.sample_odor` (positive = stronger on the right); `phase` (string); `ablate_odor` (bool).
*Output.* Turn command (dimensionless wing-amplitude asymmetry, positive = turn right), float.
`turn_hand = 0` if `ablate_odor` or `phase` is not `takeoff` or `cruise`; otherwise
`turn_hand = K * tanh(G * I_asym)` with `K = 2.0` and `G = 20`.
Edge cases: `I_asym = 0` → 0; saturates at ±K; NaN propagates; no clipping here (the sum with the other terms is
clipped to ±2.5 in `combine_turn`). Off in `approach`/`descend`/`touchdown`/`landed` because the odour loop is
unstable over the platform (SPEC_BRAIN_CONTROL, hand-made decision).
Constants. `G = 20` (`ODOR_TURN_GAIN`): **upstream idea** (same number as the walking script's odour-to-turn gain).
`K = 2.0` (`ODOR_TURN_K`): **hand-set** (walking uses 2.5; 2.0 was chosen for flight in SPEC_FLIGHT).
The functional form `K·tanh(G·I)` is **upstream idea** (a saturating odour-asymmetry steering map).

### D.4 Visual motion bias `b_loom` (`flight/sensors.py`, class `LoomBias`)

*Inputs per decision step (25 ms).* `loom_L`, `loom_R` (floats): mean absolute T5a+T5b activity of the left and right
FlyVis eye (computed in `flight/visual_input.py`). State: `p` (float), initial value 0.
*Output.* `p` after the update (positive = turn right), float; it is the term `turn_flyvis` of the turn command.
Update, once per call: `n = -g * (loom_L - loom_R)`; `p ← clip(d * p + (1 - d) * n, -m, m)`; return `p`.
The call is made at **every** decision step, including the perch calibration and the input-cut steps before take-off
(the state at the first recorded step is therefore not 0 in general). Steps are not skipped when the phase changes.
Edge cases: `loom_L == loom_R` → `n = 0` and `p` decays by the factor `d` each step; NaN input makes `p` NaN
(the clip does not repair it); the order of the floating-point operations is as written above (multiplications and one
addition), so the result is reproducible bit for bit.
Constants (all three **upstream idea**, same numbers as the walking script): `g = 0.5` (`FLYVIS_T5_GAIN`, turn per unit
of T5 asymmetry), `d = 0.5` (`FLYVIS_DECAY`, persistence per step), `m = 0.15` (`FLYVIS_BIAS_MAX`, clamp). The
sign (turn away from the side with more motion) is the walking convention, **upstream idea**.

### D.5 Other constants of the active path (`flight/config.py`)

| constant | value | role | source |
|---|---|---|---|
| `ANTENNA_HALF_SEP_REAL` | 0.5 mm | real antenna half-separation; `I_asym_real`/`I_grad_real` are always recorded with it | **upstream idea** (same number as the walking script); only recorded in n1/n2 |
| `ANTENNA_HALF_SEP_EFF` | 10 mm | separation used for steering | **hand-set** (SPEC_FLIGHT, "ℓ_eff decision") |
| `ODOR_TURN_GAIN`, `ODOR_TURN_K` | 20, 2.0 | see D.3 | upstream idea / hand-set |
| `FLYVIS_T5_GAIN`, `FLYVIS_DECAY`, `FLYVIS_BIAS_MAX` | 0.5, 0.5, 0.15 | see D.4 | upstream idea |
| `TURN_BIAS_MAX` | 2.5 | clip of the summed turn command | **hand-set** |

Constants that exist only for `--legacy-control` (`K_DN_TURN`, `FEED_EXTEND_S`, `FEED_EAT_S`, `FEED_RETRACT_S`) and the
unused `VIS_RATE` move out of `flight/config.py` with the code that used them.

## E. Status of the re-implementation (2026-10-07)

**Re-implemented from the written specification (section D)**, in a new structure with new names, in commit `056df11`
(the specification itself: `4c7494b`):

| part | where now | spec |
|---|---|---|
| groups from the annotation tables | `flight/groups.py` (`_text_hits`, `_by_side`, `_annotation_groups`, `build_groups`) | D.1 |
| soma positions | `flight/groups.py` (`neuron_positions`) | D.2 |
| odour turn term | `flight/hybrid.py` (`turn_hand`) | D.3 |
| FlyVis motion bias | `flight/sensors.py` (`LoomBias`) | D.4 |
| constants | `flight/config.py` (values unchanged; the unused ones removed) | D.5 |

**Moved out** (not active in any reported run; verbatim copies in `archive/adapted_originals/`, not in the public
snapshot): `dn_lr`, `turn_terms` and the timed feeding phases of `PhaseMachine` (all `--legacy-control` only),
the constants `K_DN_TURN`, `FEED_EXTEND_S`, `FEED_EAT_S`, `FEED_RETRACT_S`, `VIS_RATE`, and the `--legacy-control`
option of `fly_flight_brain_body_simulation.py` with its branches. `PhaseMachine` was rewritten without the feeding timers.
The old tests of `turn_terms` moved to `archive/adapted_originals/test_controller_before_reimpl.py`.
Consequence: the `meta` of a new run no longer contains the `legacy_control` flag; no number of any run changes.

**Equivalence** (no tuning; `docs/reimpl_equivalence/`):
- 4a, run-free, 82 stored run records (all n1/n2/final_*/teacher/T1 flights with the current layout, plus the early
  brain-only runs): groups (22) and positions (138,617 neurons) identical to the recorded ones in all 82 files; `turn_hand`
  vs the recorded value or the teacher label, `LoomBias` (from the recorded step-0 state) and the brain-only phase sequence:
  new = old = recorded, **largest difference 0**. 5 old-format records have no turn-term decomposition (skipped).
  Limit: the `LoomBias` state before step 0 (calibration steps) is not in the records, so step 0 itself is not tested
  against the record; it is covered by 4b.
- 4b, one run: n1, seed 3, 300 steps, full brain, same flags as `run_natural.sh`: all 92 behaviour fields, the spike
  list, positions and the touchdown step (120) bit-identical to the recorded n1 (`flight_v44`); only wall-clock and memory
  diagnostics differ (not compared).

**Resolved on 2026-10-07 (row 9 of table A):** `scripts/diag/nf_report.py` and `scripts/diag/so_o1_nf.py` no longer contain verbatim upstream strings (line numbers and hashes instead); the check still parses the upstream file when it is present and skips with a message when it is not (public copy).

## Consequence

No `LICENSE` file is added for the code of this work while the adapted parts above are in it and the
upstream author has not answered (decision of the author, 2026-10-05). The public snapshot
(`scripts/make_public_snapshot.sh`) contains these files and this list. After the re-implementation (section E) the
adapted parts of table A are re-written from the specification; table A0 describes the state before 2026-10-07 and table A the state after it.

**Update 2026-10-07: licence decision.** The author decided on 2026-10-07 to publish this work under the pseudonym "omeruk" and to license the code written in this work under MIT (`LICENSE`, Copyright (c) 2026 omeruk). The paragraph above is the state of 2026-10-05 and is kept. The upstream repository still has no licence file and the question to its author is still unanswered; the MIT licence covers only what was written in this work, not any upstream file (none is in the public copy). This note states facts only and makes no claim about legal status. If the upstream author asks, the adapted parts will be removed.
