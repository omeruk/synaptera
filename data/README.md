# data/ — derived input data of the flight model

Every file in this directory is derived from third-party data (FlyWire v783 via the Shiu et al. model files,
the FlyWire annotations, FlyWire Codex downloads, DoOR.data) or from runs of this model. **The public snapshot
of this repository contains none of them**; `scripts/fetch_data.py` downloads the inputs from pinned commits
and rebuilds the files below, then prints a SHA-256 table against the files used by the reported runs.
Licence status of each file: [THIRD_PARTY.md](../THIRD_PARTY.md) §2.3 (FlyWire-derived files are treated as
CC BY-NC 4.0, non-commercial, until the FlyWire terms are verified).

| file | content | source / generating script |
|---|---|---|
| `column_assignment.csv.gz` | FlyWire v783 optic-lobe column assignment: 31 cell types, 45,528 neurons; `root_id, hemisphere, type, column_id, x, y, p, q` | FlyWire Codex download, unchanged (below) |
| `sugar_grn_783.csv` | sugar GRN input set: the 20 LB3 neurons of Shiu et al. (left) + 16 right LB3 homologs chosen by connectivity profile | `scripts/make_sugar_grn.py` (`flight.groups.select_sugar_homologs`) |
| `leg_sugar_grn_783.csv` | `--leg-grn`: the 74 leg GRNs (`sensory_ascending` / `gustatory` / `SA_VTV_pro_meso_meta`), `root_id, side, cell_type, knn_frac, selected`. 12 selected (all SA_VTV_2, 6 L + 6 R, `knn_frac` 1.0; all others ≤ 0.2) | `scripts/make_leg_sugar_grn.py` (`flight.groups.select_leg_sugar_grns`): the partner-type profile of `select_sugar_homologs` (input/output × ipsi/contra, L2-normalised, cosine), pool = labellar `sugar/water` 129 + `bitter` 65, k = 5 majority. Leave-one-out on the pool: 129/129 sugar/water correct, 0 false positives among 65 bitter. No behavioural data used (ASSUMPTION: leg and labellar GRN profiles are comparable) |
| `nt_modulatory_silent_783.csv` | `--nt-modulatory-silent` list: the 20,719 simulated neurons whose Codex v783 `neurons.csv` `nt_type` is DA/SER/OCT or missing (NaN, score 0); `root_id, nt_type, nt_type_score` (`none` = NaN). The narrow variant uses only the DA/SER/OCT rows; Poisson input neurons are exempted in `flight/brain.py` | `scripts/make_nt_silent.py` (Codex `neurons.csv.gz`) |
| `dn_lr_reference.json` | side reference for the yaw readout (ASSUMPTION): L/R rate (Hz per neuron) of every readout DN on the mirror-symmetric front-to-back grating (sym_prog), 3 seeds, 250–2000 ms, `olfaction=False`, T4/T5 input | `scripts/make_dn_reference.py` (full-brain runs) |
| `dn_lr_reference_sB.json` | the same through the FlyVis boundary layer (`--vision-boundary`, input set sB, SPEC_SENSORY_INPUTS §3.3c); used by the final runs | `scripts/make_dn_reference.py --vision-boundary` |
| `neuron_arbor_centroids.npz` | per-neuron synapse centroid (pre / post / all, nm, float32), `n_pre`, `n_post`; `xyz` = all-synapse centroid, for the 4,451 neurons without synapses the mean of `coordinates.csv` (`source` 1/2). Order = `Completeness_783.csv` rows. Codex `synapse_coordinates.csv` contains only pairs with ≥ 5 synapses (34.16 M synapses; per-neuron counts match the ≥ 5 thresholded Connectivity_783 for 99.6 %); an empty root_id cell repeats the previous row's value per column (block length = pair synapse count, verified). Used for the video brain panel and for the column of boundary-layer neurons without a column assignment | `scripts/prepare_neuron_geometry.py` |
| `neuron_neuropil.npz` | dominant neuropil (largest input + output synapse count; `_L/_R` split, `side` L/R/C) and its share | `scripts/prepare_neuron_geometry.py` (Codex `neuropil_synapse_table.csv`) |
| `neuron_class.npz` | display class: other / visual / olfactory / taste / DN / motor, `side` | `scripts/prepare_neuron_geometry.py` (Codex `classification.csv`) |
| `orn_spontaneous_783.csv` | Stage A (`--olfaction-full`): spontaneous rate of the ORNs of the 53 glomeruli. `spont_hz`; `source` = Hallem & Carlson 2006 (23 glomeruli, 24 receptors) or ASSUMPTION 5 Hz (30 glomeruli); `receptors_hc2006`, `receptors_door`, `n_L/n_R/n_na`, `food` (6 food glomeruli), `door_other_sfr` (SFR of the other DoOR datasets, information only, not used). Not distributed: CC BY-SA 4.0 (DoOR) combined with FlyWire columns (THIRD_PARTY.md §3) | `scripts/make_orn_spontaneous.py`: DoOR.data (Münch & Galizia 2016, *Sci Rep* 6:21841; github.com/ropensci/DoOR.data, commit `db323a4`), receptor csv files, row `SFR`, column `Hallem.2006.EN` (Hallem & Carlson 2006, *Cell* 125:143, doi 10.1016/j.cell.2006.01.050); receptor → glomerulus from DoOR `door_mappings.csv`. Two co-expressed H&C receptors (DM3 Or47a + Or33b, DM5 Or85a + Or33b): mean (ASSUMPTION) |
| `nt_literature_783.csv` | `--nt-literature` (SPEC_SENSORY_INPUTS §3.2c): literature transmitter of the 370 cell types that take part in the odour persistent state. `known_nt`, `fast_nt`, `sign_lit` (ACh +1, GABA/Glu −1; 0 = no fast transmitter / more than one / inconsistent within the type → not touched), `source`, `confidence` (high/medium, report only), `model_sign`, `n_change`, `codex_nt`, `loop_drive_pct_s/g`. 272 types get a sign; 24 neurons in 8 types change. Not rebuilt by `scripts/fetch_data.py` | `scripts/make_nt_literature.py --diag sa2_diag_neurons.parquet` (output of `scripts/diag/sa2_diag.py` on the Stage A smoke runs v17/v18). Source: `known_nt`/`known_nt_source` of `brain_model/flywire_annotations.tsv` (literature compilation of Schlegel et al. 2024, *Nature* 634:139); for lLN1_bc the discussion in Eckstein et al. 2024 (*Cell* 187:2574) (Huang et al. 2010 is named in the generating script; not verified, listed for completeness) |
| `nt_impute_783.csv` | `--nt-impute` (MODEL VARIANT N1, SPEC_SENSORY_INPUTS §3.4b, not the published model): one row per neuron without a Codex v783 `nt_type` (19,042): `cell_type`, `published_sign`, `imputed_sign` (0 = keeps its sign), `n_peers`, `peer_syn_pos/neg` (output synapses of the predicted peers of the same cell type by predicted sign). 3,599 neurons change sign. Not rebuilt by `scripts/fetch_data.py` | `scripts/make_nt_impute.py` (needs the Codex `neurons.csv.gz`, like `make_nt_silent.py`) |
| `t45_transduction.json` | FlyVis → T4/T5 transduction constants: `a0` (grey-screen steady-state activity of every FlyVis T4/T5 node), `a_ref` (response to the standard grating per subtype), `r_max`, `r_clip` | `scripts/make_t45_transduction.py` (`flight.visual_input.calibrate_transduction`; needs the FlyVis pretrained weights) |
| `visual_transduction.json` | the same for every FlyVis node and type (`--vision-boundary`) | `scripts/make_visual_transduction.py` (`flight.vision_boundary.calibrate`) |
| `vision_boundary_783.csv`, `vision_boundary_types.json` | FlyVis → FlyWire boundary layer: the 32 FlyWire types driven from FlyVis (34,121 neurons), their column (column assignment, else mean of columnar partners, else arbor centroid) and the selection rule | `scripts/make_vision_boundary.py` (rule and validation in `flight/vision_boundary.py`; Codex `consolidated_cell_types`, `column_assignment`, `Connectivity_783`) |

## column_assignment.csv.gz

- **Source:** FlyWire Codex "visual columns" download (FlyWire v783 materialization), copied unchanged
  (462,838 bytes).
- **Method papers:** Matsliah, A. et al. (2024). *Neuronal parts list and wiring diagram for a visual system.*
  Nature 634, 166–180. · Zhao, A. et al. *Eye structure shapes neuron function in Drosophila motion vision.*
  bioRxiv 2022.12.14.520178. · FlyWire connectome: Dorkenwald, S. et al. (2024), Nature 634, 124–138;
  Schlegel, P. et al. (2024), Nature 634, 139–152.
- **Licence:** subject to the FlyWire Codex terms of use; the licence text of the Codex downloads could not be
  read (UNVERIFIED, THIRD_PARTY.md §2.1). An earlier version of this file said the Codex lists it as CC BY 4.0;
  that was not verified.
- **Coordinates:** `p, q` hexagonal column coordinates; neighbours ±(1,0), ±(0,1), ±(1,1) (verified from the
  connectivity). `x = (q − p)/2`, `y = p + q`. Central column `column_id 628` (p = q = 0), the same in both
  hemispheres; `hemisphere` is the fly's own side (> 99 % agreement with the annotations' `side`, checked in a test).
- **Use:** only T4a–d and T5a–d (11,822 neurons) are mapped to FlyVis columns (`flight/visual_input.py`). The
  alignment (FlyWire → FlyVis: 60° rotation, no reflection) is computed from the Mi4/Mi9/Tm9 → T4/T5 column
  offsets of the two connectomes (`fit_alignment`, `tests/flight/test_visual_input.py`).

## sugar_grn_783.csv

- `source = shiu2023`: 20 of the 21 IDs of the list in Shiu et al.'s `figures.ipynb` (Shiu et al. 2023,
  *A leaky integrate-and-fire computational model based on the connectome of the entire adult Drosophila
  brain*, bioRxiv / Nature 2024) that exist in v783. All LB3, annotations `side = left`. The IDs are in
  `flight/groups.py` (`SHIU_SUGAR`).
- `source = homolog_knn5`: right LB3 neurons (58) whose 5 most similar left LB3 neurons (input + output partner
  cell-type profile, ipsi/contra split, L2-normalised) are mostly Shiu neurons. The method was chosen by its
  leave-one-out accuracy on the left side (19/20 sugar, 2 false positives among 44 other LB3); no behavioural
  data were used. `knn_frac` = share of Shiu neurons among the 5 neighbours.

## FlyWire Codex v783 downloads — inventory (not in the repository)

The scripts read these files from a directory given as an argument (`--codex-dir`, `--src`; default
`~/Downloads`). Download instructions: `python scripts/fetch_data.py --codex-help`.

- **Source:** FlyWire Codex (codex.flywire.ai) downloads, materialization v783. 139,255 neurons; all 138,639
  neurons of the simulation (Completeness_783) are in `neurons.csv` (verified, `scripts/diag/a0_codex.py`).
- **Citation:** Dorkenwald, S. et al. (2024), *Neuronal wiring diagram of an adult brain*, Nature 634, 124–138;
  Schlegel, P. et al. (2024), *Whole-brain annotation and multi-connectome cell typing of Drosophila*, Nature
  634, 139–152; visual types/columns: Matsliah et al. (2024), Nature 634, 166–180.
- **Licence:** Codex terms of use (attribution required). UNVERIFIED, see above.
- **Rule:** none of them is a model parameter. The LIF network, the synapse list and the transmitter signs come
  from `brain_model/Connectivity_783.parquet`. These files are used for cross-checks, analysis, input-set
  selection and visualisation.

| file | size | content | used in |
|---|---|---|---|
| `neurons.csv.gz` | 1.7 MB | root_id, neuropil group, nt_type + nt_type_score, transmitter probabilities (ach/gaba/glut/da/ser/oct) | brain-control Step 0 decisions: confidence of the APL/KC/lLN1_bc transmitters, agreement with the parquet signs, root_id coverage; `nt_modulatory_silent_783.csv` |
| `neuropil_synapse_table.csv.gz` | 4.7 MB | input/output synapse counts per neuron and neuropil | Step 0 decisions: neuropil distribution of the persistent state and of the DN asymmetry; `neuron_neuropil.npz` |
| `connections_princeton.csv.gz` | 68 MB | pre, post, neuropil, synapse count (≥ 5 per neuropil), nt_type | Step 0 decisions: T4/T5 → LPTC → DN path by hemisphere/neuropil |
| `visual_neuron_types.csv.gz` | 0.6 MB | optic-lobe types, family, subsystem, side | Step 0 decisions: T4/T5, HS, VS counts L/R |
| `classification.csv.gz` | 0.9 MB | flow, super_class, class, sub_class, hemilineage, side, nerve | Step 0 decisions: side, class of the 616 extra neurons; `neuron_class.npz` |
| `consolidated_cell_types.csv.gz` | 0.9 MB | primary_type, additional_type(s) | Step 0 decisions: T4/T5 count cross-check; boundary-layer types |
| `column_assignment.csv.gz` | 0.5 MB | column assignment (above) | FlyVis → T4/T5 and boundary layer |
| `synapse_coordinates.csv.gz` | 317 MB | pre, post, x, y, z per synapse | per-neuron synapse centroid (`neuron_arbor_centroids.npz`) |
| `coordinates.csv.gz` | 5.3 MB | neuron position (position, supervoxel) | centroid fallback |
| `names.csv.gz` | 1.2 MB | neuron name, group | not used (planned for panel labels) |
| `labels.csv.gz` | 4.8 MB | community labels (user, date) | not used (planned for panel labels) |
| `processed_labels.csv.gz` | 1.0 MB | processed label lists | not used (planned for panel labels) |
| `connections_princeton_no_threshold.csv.gz` | 276 MB | Princeton synapse prediction, no threshold | reserve: only if a finding were threshold-sensitive |
| `connections_buhmann_no_threshold.csv.gz` | 212 MB | Buhmann et al. synapse prediction, no threshold | reserve: comparison with an alternative prediction |
| `connectivity_tags.csv.gz` | 0.6 MB | rich_club, reciprocal, … tags | not used |
| `cell_stats.csv.gz` | 2.5 MB | length, area, volume | not used |
| `synapse_attachment_rates.csv.gz` | 3 KB | proofread share per neuropil | not used |

Note: the parquet and the Princeton ≥ 5 table are not identical. In 10.7 % of the shared pairs the synapse
counts are equal; the median difference is +2 in favour of Princeton. Findings agree in direction at the level of
synapse-count magnitudes; absolute synapse-count comparisons use the parquet.
