# Third-party components, licences and provenance

> Public snapshot: this audit was made on the development repository. The snapshot contains only the files in docs/SNAPSHOT_MANIFEST.md; "copy in repo: yes" refers to the development repository.

Audit date: 2026-10-05. Branch `sensory-inputs`. This file records what Synaptera uses from others, under which licence, and where that licence was read. No licence is inferred: where the licence text could not be read from the source, the entry says **UNVERIFIED**. This is a provenance record, not legal advice.

Legend for "copy in repo": **yes** = the file(s) are tracked in this git repository; **no** = installed or downloaded separately.

Sources read for this audit (2026-10-05):
- installed package metadata (`importlib.metadata`, conda env `neurofly`, Python 3.10);
- GitHub API `GET /repos/{owner}/{repo}/license` and raw files (`LICENSE`, `DESCRIPTION`, `README.md`) of the repositories named below;
- Zenodo API record metadata;
- the FlyWire Terms of Service page (`https://flywire.ai/tos`) and the FlyWire Codex pages (`https://codex.flywire.ai/about_flywire`, `/api/download`; the download page requires sign-in and shows no licence text without it);
- Crossref API for DOIs.

---

## 1. Code, models and software

| component | used for | code / data / idea | licence | where the licence was read | copy in repo | attribution (DOI) |
|---|---|---|---|---|---|---|
| NeuroFly ([seven-monarchs/NeuroFly](https://github.com/seven-monarchs/NeuroFly)) | upstream repository; walking simulation; starting point of this repository | code + data (+ idea: odour field on a Dijkstra distance map, DN L−R turning gain) | **UNVERIFIED — no licence.** No licence file in the repository or its history; GitHub API `license: null` | GitHub API; `git log` of this repository | **yes** (445 files, see §4 and [docs/FILE_PROVENANCE.md](docs/FILE_PROVENANCE.md)) | no DOI; repository URL, author "Monarch" |
| Shiu et al. LIF model ([philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model)) | `brain_model/model.py` (`create_model`, `default_params`): recurrent network set-up and LIF parameters | code | **MIT**, "Copyright (c) 2023 Philip Shiu and Nico Spiller" | `brain_model/LICENSE` (byte-identical to the repository's `LICENSE`); GitHub API `MIT` | **yes** (`brain_model/`, via NeuroFly). `model.py` has the same git blob SHA as `philshiu/Drosophila_brain_model@main` (91bdd1e, 2024-09-14) | Shiu, P. K. et al. (2024). *Nature* 634, 210–219. doi:[10.1038/s41586-024-07763-9](https://doi.org/10.1038/s41586-024-07763-9) |
| FlyGym / NeuroMechFly v2 ([NeLy-EPFL/flygym](https://github.com/NeLy-EPFL/flygym)) | body, eyes (retina), contacts, adhesion, preprogrammed leg poses | code (+ model assets inside the package) | **Apache-2.0** | flygym 1.2.1 metadata; GitHub API `Apache-2.0` | no | Wang-Chen, S. et al. (2024). *Nature Methods* 21, 2353–2362. doi:[10.1038/s41592-024-02497-y](https://doi.org/10.1038/s41592-024-02497-y) |
| MuJoCo ([google-deepmind/mujoco](https://github.com/google-deepmind/mujoco)) | physics | code | **Apache-2.0** | mujoco 3.2.7 metadata; GitHub API `Apache-2.0` | no | Todorov, E., Erez, T. & Tassa, Y. (2012). *IROS 2012*, 5026–5033. doi:[10.1109/IROS.2012.6386109](https://doi.org/10.1109/IROS.2012.6386109) |
| Brian2 ([brian-team/brian2](https://github.com/brian-team/brian2)) | LIF simulation | code | **CeCILL-2.1** | brian2 2.9.0 metadata (classifier "CeCILL-2.1"); repository `LICENSE` ("License for Brian2", copyright ENS, INRIA, CNRS, INSERM, Sorbonne Université; GitHub API reports `NOASSERTION`) | no | Stimberg, M., Brette, R. & Goodman, D. F. M. (2019). *eLife* 8, e47314. doi:[10.7554/eLife.47314](https://doi.org/10.7554/eLife.47314) |
| FlyVis ([TuragaLab/flyvis](https://github.com/TuragaLab/flyvis)) | visual network (FlyGym eyes → FlyVis → FlyWire boundary layer) | code | **MIT** | flyvis 1.2.0 metadata; GitHub API `MIT` (file `license`) | no | Lappalainen, J. K. et al. (2024). *Nature* 634, 1132–1140. doi:[10.1038/s41586-024-07939-3](https://doi.org/10.1038/s41586-024-07939-3) |
| FlyVis pretrained weights (`flow/0000/000`, from `flyvis.results_dir`) | the FlyVis network used in flight | data (model weights) | **UNVERIFIED** | downloaded by `flyvis download-pretrained` (`results_pretrained_models.zip`); the terms of the download were not read | flight: no (site-packages). The walking code's copy `simulation_data/flyvis_pretrained_weights/` (315 files, from NeuroFly) **is** in the repo | Lappalainen et al. 2024 (above) |
| flybody ([TuragaLab/flybody](https://github.com/TuragaLab/flybody)) | NeuroFly dependency (walking); `fruitfly/assets/fruitfly.xml` and `floor.xml` are byte-identical to the files in the installed flybody package | code + model assets | **Apache-2.0** | GitHub API `Apache-2.0` | **yes** (2 assets, via NeuroFly); package: no | no DOI read |
| `fruitfly/assets/drosophila.xml`, `drosophila_defaults.xml`, `drosophila_fused.xml` | walking code (NeuroFly) | model assets | **UNVERIFIED** (origin not identified; not in the installed flybody package) | — | **yes** (via NeuroFly) | — |
| dm_control | FlyGym dependency | code | Apache-2.0 | dm_control 1.0.27 metadata; GitHub API `Apache-2.0` | no | — |
| DoOR.functions | not used (only DoOR.data, below) | — | GPL-3 (`DESCRIPTION`) | — | no | — |

## 2. Data

### 2.1 FlyWire v783 — what the licence sources say

The licence of "FlyWire data" is not one statement. What could be read:

| source | licence | where read |
|---|---|---|
| FlyWire v783 connectivity release on Zenodo ("FlyWire Whole-brain Connectome Connectivity Data", version 783, doi:10.5281/zenodo.10676866; synapse table, proofread connections, root IDs) | **CC BY 4.0** | Zenodo API record metadata |
| Supplemental files of Schlegel et al. 2024 on Zenodo (doi:10.5281/zenodo.10877326; NBLAST scores, skeletons; not used here) | CC BY 4.0 | Zenodo API record metadata |
| FlyWire Terms of Service: community edits and annotations | "freely available under a **CC-BY-NC 4.0** license" | `https://flywire.ai/tos` |
| FlyWire public release (version 783, October 2023), including the data available in Codex for snapshot 783 (`neurons`, `classification`, `consolidated_cell_types`, `neuropil_synapse_table`, `synapse_coordinates`, `coordinates`, `column_assignment`, …) | **CC BY-NC 4.0** (the page states the licence of the public release data and that all data available in Codex for snapshot 783 is publicly released) | [flywire.ai/guidelines](https://flywire.ai/guidelines), opened 2026-10-07 |
| [flyconnectome/flywire_annotations](https://github.com/flyconnectome/flywire_annotations) (annotation table) | the repository has no licence file (GitHub API: none) and its README asks for citations only; the FlyWire public-release licence above is the licence we apply to its content | GitHub API; README; flywire.ai/guidelines |
| `Completeness_783.csv`, `Connectivity_783.parquet` in the Shiu repository | the repository's `LICENSE` (MIT) covers the code; the files are FlyWire v783 data, to which the FlyWire public-release licence applies | repository `LICENSE`, `Readme.md`; flywire.ai/guidelines |

Since 2026-10-07 the licence of the FlyWire public release is read at the source ([flywire.ai/guidelines](https://flywire.ai/guidelines): CC BY-NC 4.0; the page does not list papers to cite and points to a citation guide). The Zenodo connectivity record is CC BY 4.0, which is more permissive; this repository applies the stricter, FlyWire-stated licence to **all FlyWire-derived files: non-commercial use (CC BY-NC 4.0), with attribution**. The Terms of Service of FlyWire (flywire.ai/tos) were not re-read in this step.

FlyWire attribution (all DOIs checked on Crossref): Dorkenwald, S. et al. (2024). *Nature* 634, 124–138. doi:[10.1038/s41586-024-07558-y](https://doi.org/10.1038/s41586-024-07558-y) · Schlegel, P. et al. (2024). *Nature* 634, 139–152. doi:[10.1038/s41586-024-07686-5](https://doi.org/10.1038/s41586-024-07686-5) · Matsliah, A. et al. (2024). *Nature* 634, 166–180. doi:[10.1038/s41586-024-07981-1](https://doi.org/10.1038/s41586-024-07981-1) (visual columns, optic-lobe types) · Eckstein, N. et al. (2024). *Cell* 187, 2574–2594. doi:[10.1016/j.cell.2024.03.016](https://doi.org/10.1016/j.cell.2024.03.016) (transmitter predictions) · Buhmann, J. et al. (2021). *Nature Methods* 18, 771–774. doi:[10.1038/s41592-021-01183-7](https://doi.org/10.1038/s41592-021-01183-7) (synapse detection) · FlyWire Codex: doi:10.13140/RG.2.2.35928.67844 (as given on codex.flywire.ai; not checked on Crossref).

### 2.2 Raw data files used by the flight code

| file | used for | licence | where read | copy in repo | provenance check |
|---|---|---|---|---|---|
| `brain_model/Completeness_783.csv` | neuron list; row order = Brian2 index | CC BY-NC 4.0 (§2.1) | — | **yes** (NeuroFly, 1a376da) | same git blob SHA as `philshiu/Drosophila_brain_model@main` |
| `brain_model/Connectivity_783.parquet` | recurrent synapses and signs | CC BY-NC 4.0 (§2.1) | — | **yes** (NeuroFly, 1a376da; second copy in `simulation_data/flywire_connectome_v783/`) | same git blob SHA as `philshiu/Drosophila_brain_model@main` |
| `brain_model/flywire_annotations.tsv` | cell types, sides, literature transmitters | CC BY-NC 4.0 (§2.1) | — | **yes** (NeuroFly, 1a376da) | same git blob SHA as `flyconnectome/flywire_annotations@c03ad462aa` (2025-10-07), `supplemental_files/Supplemental_file1_neuron_annotations.tsv` |
| `brain_model/descending_neurons.csv` | DN readouts (`root_id`, `cell_type`, `side`) | CC BY-NC 4.0 (§2.1) | — | **yes** (NeuroFly, 1a376da) | **not** in the Shiu repository; made in NeuroFly. Its rows equal annotations `super_class == "descending"` ∩ `Completeness_783` in the same order; `cell_type` and `side` identical, `top_nt` differs in 10 of 1,299 rows (not used by the flight code) |
| Codex downloads (`~/Downloads`, §2.1) | inputs of the `data/` scripts, cross-checks | CC BY-NC 4.0 (§2.1) | — | no (except `data/column_assignment.csv.gz`) | — |
| DoOR.data ([ropensci/DoOR.data](https://github.com/ropensci/DoOR.data), commit `db323a4`) | spontaneous ORN rates (`SFR` row, `Hallem.2006.EN` column), receptor → glomerulus mapping | **CC BY-SA 4.0** | `DESCRIPTION` of the repository (`License: CC BY-SA 4.0`, version 2.0.1.9001) | no (downloaded by `scripts/make_orn_spontaneous.py`); derived file yes (below) | Münch, D. & Galizia, C. G. (2016). *Sci Rep* 6, 21841. doi:[10.1038/srep21841](https://doi.org/10.1038/srep21841) · Hallem, E. A. & Carlson, J. R. (2006). *Cell* 125, 143–160. doi:[10.1016/j.cell.2006.01.050](https://doi.org/10.1016/j.cell.2006.01.050) · Couto, A. et al. (2005). *Curr Biol* 15, 1535–1547. doi:[10.1016/j.cub.2005.07.034](https://doi.org/10.1016/j.cub.2005.07.034) · Fishilevich & Vosshall 2005 (*Curr Biol*): DOI UNVERIFIED |

### 2.3 Files in `data/` (all added in this work)

"Redistributable?" is the conclusion from the licences above, not legal advice. "FlyWire part" means content derived from the files of §2.1–2.2 (root IDs, cell types, connectivity, positions).

| file | derived from | FlyWire part | other source | redistributable? |
|---|---|---|---|---|
| `column_assignment.csv.gz` | Codex "visual columns" download, **unchanged copy** | the whole file | — | **CC BY-NC 4.0** (FlyWire public release, §2.1). Safer: do not ship; download instructions instead |
| `sugar_grn_783.csv` | Shiu sugar GRN list (`brain_model/figures.ipynb`, MIT repo) + kNN on `Connectivity_783` | root IDs, sides, partner profiles | Shiu list | conditional on the FlyWire terms (§2.1) |
| `leg_sugar_grn_783.csv` | annotations + `Connectivity_783` (kNN) | root IDs, cell types | — | conditional on the FlyWire terms |
| `nt_modulatory_silent_783.csv` | Codex `neurons.csv` (`nt_type`, `nt_type_score`) | the whole file (Eckstein et al. predictions via Codex) | — | **CC BY-NC 4.0** (FlyWire public release, §2.1) |
| `nt_literature_783.csv` | annotations `known_nt`/`known_nt_source`, Codex `nt_type`, model run statistics | cell types, transmitters | literature (Eckstein et al. 2024; Huang et al. 2010 — DOI UNVERIFIED) | conditional on the FlyWire terms; Codex column UNVERIFIED |
| `orn_spontaneous_783.csv` | DoOR.data + annotations | `cell_type` (ORN_⟨glomerulus⟩), `n_L/n_R/n_na` (neuron counts) | DoOR: `spont_hz`, `receptors_*`, `door_other_sfr`, mapping (CC BY-SA 4.0) | **see §3 — likely not, as long as the FlyWire part is CC BY-NC** |
| `neuron_arbor_centroids.npz` | Codex `synapse_coordinates`, `coordinates` | the whole file | — | **CC BY-NC 4.0** (FlyWire public release, §2.1) |
| `neuron_neuropil.npz` | Codex `neuropil_synapse_table` | the whole file | — | **CC BY-NC 4.0** (FlyWire public release, §2.1) |
| `neuron_class.npz` | Codex `classification` | the whole file | — | **CC BY-NC 4.0** (FlyWire public release, §2.1) |
| `vision_boundary_783.csv`, `vision_boundary_types.json` | `Connectivity_783`, annotations, `column_assignment` | root IDs, types, columns | FlyVis type names | conditional on the FlyWire/Codex terms |
| `t45_transduction.json`, `visual_transduction.json` | outputs of the FlyVis network (calibration) | none | FlyVis code (MIT) + pretrained weights (UNVERIFIED) | own results; depends on the FlyVis weights terms |
| `dn_lr_reference.json`, `dn_lr_reference_sB.json` | outputs of this model (DN rates on a reference stimulus) | DN type names; model built from FlyWire | — | own results; conditional on the FlyWire terms for the type names |
| `README.md` | written in this work | — | — | yes (own text; licence not chosen yet) |

The run outputs (`simulations/*.h5`) contain spike counts indexed by FlyWire root-ID order; the same FlyWire conditions apply.

### 2.4 FlyWire-derived content of the public copy (scan of 2026-10-07)

Scan of `../synaptera_v6` for FlyWire root IDs, neuron lists and derived tables. Nothing was deleted; the column "proposal" is a recommendation for the author.

| file(s) | FlyWire-derived content | proposal |
|---|---|---|
| `flight/groups.py` (`SHIU_SUGAR`, 21 root IDs), `scripts/diag/r0_sugar.py`, `r2_anat.py`, `r3_open.py`, `r3_open_v1_contaminated.py` (the same 20/21 sugar GRN root IDs, copied from the MIT-licensed Shiu repository) | root IDs of 21 neurons | keep (tiny list from an MIT repository; FlyWire attribution applies); alternatively read the list from the Shiu repository at run time |
| `tests/flight/test_readouts.py` | the two root IDs of the MN9 neurons | keep |
| `docs/vis_dn_directions.json`, `docs/vl_directions.json` | DN cluster and type names with activity statistics of the model | keep (derived results, CC BY-NC 4.0) |
| `docs/ladder/trial1_readouts.json` | R² and SHA-256 values of fitted read-outs | keep |
| `figures/` and `figures/data/*.csv` | activity of FlyWire DN clusters and olfactory neurons in the model, aggregated | keep (derived results, CC BY-NC 4.0) |
| `REPORT.md`, `README.md`, `docs/tr/*` | cell-type names, counts and rates | keep |
| files that the copy does **not** contain | `brain_model/*`, `data/*` (root-ID lists, `descending_neurons.csv`, `orn_spontaneous_783.csv`, `nt_*.csv`), HDF5 run files | rebuilt by `scripts/fetch_data.py`; run records go to the data bundle (CC BY-NC 4.0) |

All of the above falls under the FlyWire public-release licence (CC BY-NC 4.0, §2.1); the copy states this in the README.

## 3. `data/orn_spontaneous_783.csv`: CC BY-SA 4.0 together with FlyWire

Content: one row per glomerulus (53). The DoOR part (spontaneous rates, receptor names, receptor → glomerulus mapping) is an adaptation of DoOR.data, licensed **CC BY-SA 4.0**. The FlyWire part is the cell-type name and the left/right neuron counts from `flywire_annotations.tsv`.

- **If the FlyWire part is CC BY-NC 4.0** (the conservative reading, §2.1): CC BY-SA 4.0 requires an adaptation to be shared under CC BY-SA 4.0 (or a BY-SA-compatible licence) and forbids additional restrictions; CC BY-NC 4.0 requires the non-commercial restriction. One file cannot meet both, so the combined file **should not be distributed** under these assumptions. (CC BY-SA 4.0 legal code §3(b)(1) and §3(b)(3), read at creativecommons.org/licenses/by-sa/4.0/legalcode.en: the Adapter's License must be CC BY-SA 4.0 or a BY-SA Compatible License, and no additional terms may restrict the rights granted under it.)
- **If the FlyWire part is CC BY 4.0** (as the Zenodo v783 connectivity release) or not protected: the file can be distributed under CC BY-SA 4.0 with attribution to DoOR, Hallem & Carlson and FlyWire.
- The FlyWire public-release licence is CC BY-NC 4.0 (§2.1), so the first case applies.

**Recommendation (not carried out; nothing was deleted):** stop tracking `data/orn_spontaneous_783.csv` (`git rm --cached`; local copy stays) and keep `scripts/make_orn_spontaneous.py`, which rebuilds it from the pinned DoOR.data commit and the local `flywire_annotations.tsv`. The final configuration uses `--no-olfaction`, so the file is only needed for `--olfaction-full` and `tests/flight/test_olfaction_full.py` (that test would need a skip when the file is absent). Alternative: split it into a DoOR-only table (CC BY-SA 4.0: glomerulus, receptors, rates) and compute the FlyWire columns at run time from the annotations.

## 4. Upstream files vs. files of this work

Full lists: [docs/FILE_PROVENANCE.md](docs/FILE_PROVENANCE.md) (generated from git).

- **Upstream (NeuroFly):** 445 files at `b59264a` (= `origin/main`; commits `1a376da`–`b59264a`, 2026-03-25 – 2026-04-05, author "Monarch"): `brain_model/` (21, Shiu repository copy), `simulation_data/` (321: 315 FlyVis weight files, 4 FlyWire files, 2 READMEs), `simulations/` (24: walking videos, GIFs, HDF5 v33–v42), `plots/` (40), `tests/` (25 walking tests), `fruitfly/assets/` (5), `fly_brain_body_simulation.py`, `generate_plots.py`, `requirements.txt`, `Dockerfile`, `.dockerignore`, `run.bat`, `.gitignore`, `README.md`, `README.en.md`.
- Status in HEAD: 440 unchanged; modified: `fly_brain_body_simulation.py` and `tests/test_flyvis_stateful_timing.py` (86ea1fc), `.gitignore` (cffe0d7), `README.md` (replaced by the Synaptera README; the upstream text is kept in `docs/neurofly_upstream/README.fr.md`); renamed: `README.en.md` → `docs/neurofly_upstream/README.en.md`. (The working tree additionally has uncommitted changes to the upstream PNGs in `plots/v42/`; they are not part of any commit.)
- **This work:** 255 files added after `b59264a`. Exceptions inside them: `docs/neurofly_upstream/*` (upstream text), `data/column_assignment.csv.gz` (Codex copy), `archive/flight_attempts/` (earlier attempts written by another AI tool, not used), `docs/NEUROFLY_FLIGHT_YENI_PROJE_MASTER_DONUSUM_REHBERI.md` (draft by another AI tool, reference only).

### 4.1 What the flight code takes from upstream files

Checked with `grep` over `fly_flight_brain_body_simulation.py`, `flight/`, `scripts/`, `tests/flight/`, `render_flight_*.py`, `generate_flight_plots.py`, `simulation_data/odor_field_3d.py`:

| upstream file | how | original source |
|---|---|---|
| `brain_model/model.py` | imported: `from model import create_model, default_params` (`flight/brain.py`; `poi` in `scripts/diag/r0_sugar.py`) | Shiu repository (MIT), byte-identical |
| `brain_model/Completeness_783.csv`, `Connectivity_783.parquet` | read (`flight/groups.py`) | Shiu repository, byte-identical |
| `brain_model/flywire_annotations.tsv` | read | flywire_annotations@c03ad462aa, byte-identical |
| `brain_model/descending_neurons.csv` | read | NeuroFly; reproducible from the annotations (§2.2) |
| `requirements.txt` | installation | NeuroFly |

Not used by the flight code: `fly_brain_body_simulation.py`, `generate_plots.py`, `fruitfly/`, `simulation_data/flyvis_pretrained_weights/` (flight loads FlyVis weights from the installed package), `simulation_data/flywire_connectome_v783/`, walking tests. No verbatim code lines of the walking scripts were found in the flight code (line comparison, lines > 40 characters). **Correction (2026-10-05): parts of the flight code are adapted from the walking script** (same logic, formulas, constants and idioms, rewritten): group selectors and soma positions (`flight/groups.py`), the DN turn readout and timed feeding phases (`flight/controller.py`, legacy path), the odour turn map (`flight/hybrid.py: turn_hand`, used in n1), the FlyVis loom bias (`flight/sensors.py: LoomBias`, used in n1) and several constants (`flight/config.py`). File and line ranges: [docs/ADAPTED_CODE.md](docs/ADAPTED_CODE.md). Ideas taken from NeuroFly are listed in §6.

**Update 2026-10-07:** the adapted parts were re-written from a specification and table A of [docs/ADAPTED_CODE.md](docs/ADAPTED_CODE.md) lists the current state; a script comparison of every `.py`/`.sh` file of the public copy with the upstream files gives a longest identical block of 1 meaningful line ([docs/ORIGINALITY_CHECK.md](docs/ORIGINALITY_CHECK.md)). The bibliographic data of the references of this audit were re-checked on Crossref on 2026-10-07 (the Hengstenberg 1988 and Huang 2010 content claims remain unverified, see the check file).

### 4.2 Option: publish only the files of this work

Technically possible, and the flight code does not need NeuroFly itself: every upstream file it uses has an original source outside NeuroFly. Needed:
1. `brain_model/`: fetch `model.py`, `Completeness_783.csv`, `Connectivity_783.parquet` from `philshiu/Drosophila_brain_model` at commit `91bdd1e` (a fetch script with SHA-256 check). `model.py` and its `LICENSE` may also be shipped directly under MIT (with the copyright notice), independently of NeuroFly. `flight/brain.py` and `flight/groups.py` keep their paths.
2. `flywire_annotations.tsv`: download from `flyconnectome/flywire_annotations` at `c03ad462aa`.
3. `descending_neurons.csv`: a small script that writes it from the annotations (§2.2).
4. Dependencies: `requirements-flight.txt` (no walking-only packages).
5. Tests: `tests/conftest.py` and `tests/flight/` are from this work; the 25 walking tests are not shipped (or are skipped).
6. **Git history:** the current history contains the upstream commits and files. Publishing "only our files" means either a history rewrite (`git filter-repo`; changes every commit hash, including the pre-registration hashes cited in the SPEC/REPORT files) or a new repository from a clean snapshot, with the pre-registration commits referenced as a private archive (see docs/REPO_CLEANUP_REPORT.md, recommendation 2).
7. Cloning NeuroFly separately would only be needed to reproduce the walking results; NeuroFly would still have to be cited (§1).

## 5. Python packages imported directly by the flight code

Installed versions (conda env `neurofly`); licence from the installed package metadata (`License-Expression`, `License` or classifier). These packages are not copied into the repository.

| package (import) | version | used for | licence (metadata) |
|---|---|---|---|
| numpy | 2.0.2 | arrays | BSD-style (classifier "BSD License"; licence text in metadata) |
| pandas | 2.3.3 | tables | BSD-3-Clause |
| scipy | 1.15.3 | sparse graphs, rotations | BSD-style (classifier "BSD License"; licence text in metadata) |
| matplotlib (incl. `mpl_toolkits`) | 3.10.8 | plots, video panels | Matplotlib licence (classifier "Python Software Foundation License") |
| h5py | 3.14.0 | HDF5 output | BSD-3-Clause |
| Brian2 (`brian2`) | 2.9.0 | LIF simulation | CeCILL-2.1 |
| mujoco | 3.2.7 | physics | Apache-2.0 |
| flygym | 1.2.1 | body | Apache-2.0 |
| flyvis | 1.2.0 | visual network | MIT |
| torch | 2.14.0 | FlyVis back-end | "Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT" (as stated) |
| imageio | 2.37.3 | video writing | BSD-2-Clause |
| opencv-python (`cv2`) | 4.14.0.94 | video rendering | Apache-2.0 |
| pyarrow | 23.0.1 | parquet / CSV streaming | Apache-2.0 |
| psutil | 7.2.2 | memory logging | BSD-3-Clause |
| joblib | 1.5.3 | imported by `brain_model/model.py` | BSD-3-Clause |
| pytest | 9.1.1 | tests | MIT |

Used at run time without a direct import: imageio-ffmpeg 0.6.0 (BSD-2-Clause; ships an ffmpeg binary whose licence was not checked — UNVERIFIED), dm_control 1.0.27 (Apache-2.0, FlyGym dependency). Walking-only packages in `requirements.txt` (flybody, python-dotenv, Cython, pillow) are not used by the flight code.

## 6. Inspired by (methods or parameter values used, no code taken)

DOIs were checked on Crossref (author, year, title) on 2026-10-05; "UNVERIFIED" means no matching record was confirmed.

| work | what was used | DOI |
|---|---|---|
| NeuroFly (seven-monarchs) | (code adaptations: [docs/ADAPTED_CODE.md](docs/ADAPTED_CODE.md)) odour field as a Dijkstra distance map (`simulation_data/odor_field_3d.py`: "same idea as the walking field"); DN L−R turning gain of the walking code (`flight/config.py`, `K_DN_TURN`) | — (no licence, §1) |
| Shiu, P. K. et al. 2024 | sugar GRN → MN9 protocol (`scripts/diag/r0_sugar.py`), sugar GRN list | [10.1038/s41586-024-07763-9](https://doi.org/10.1038/s41586-024-07763-9) |
| Matsliah, A. et al. 2024; Zhao, A. et al. (bioRxiv 2022.12.14.520178) | hexagonal column coordinates, FlyWire → FlyVis column alignment | [10.1038/s41586-024-07981-1](https://doi.org/10.1038/s41586-024-07981-1); [10.1101/2022.12.14.520178](https://doi.org/10.1101/2022.12.14.520178) |
| Hedrick, Cheng & Deng 2009, *Science* 324, 252–255 | flapping counter-torque (passive rotational damping) | [10.1126/science.1168431](https://doi.org/10.1126/science.1168431) |
| Fry, Sayaman & Dickinson 2003, *Science* 300, 495–498 | order of the hover stroke amplitude | [10.1126/science.1081944](https://doi.org/10.1126/science.1081944) |
| Beatus, Guckenheimer & Cohen 2015, *J R Soc Interface* 12, 20150075 | roll-correction time scale (haltere reflex) | [10.1098/rsif.2015.0075](https://doi.org/10.1098/rsif.2015.0075) |
| Tammero & Dickinson 2002, *J Exp Biol* 205, 2785–2798 | landing-response timing | [10.1242/jeb.205.18.2785](https://doi.org/10.1242/jeb.205.18.2785) |
| van Breugel & Dickinson 2012, *J Exp Biol* 215, 1783–1798 | landing response (hand-made trigger), leg-extension timing | [10.1242/jeb.066498](https://doi.org/10.1242/jeb.066498) |
| de Bruyne, Foster & Carlson 2001, *Neuron* 30, 537–552 | spontaneous rate of food-glomerulus ORNs | [10.1016/S0896-6273(01)00289-6](https://doi.org/10.1016/S0896-6273(01)00289-6) |
| Semmelhack & Wang 2009, *Nature* 459, 218–223 | choice of food-odour glomeruli | [10.1038/nature07983](https://doi.org/10.1038/nature07983) |
| Namiki, S. et al. 2022, *Curr Biol* 32, 1189–1196 | DNg02 as collective stroke-amplitude readout | [10.1016/j.cub.2022.01.008](https://doi.org/10.1016/j.cub.2022.01.008) |
| von Reyn, C. R. et al. 2014, *Nat Neurosci* 17, 962–970 | giant fibre (DNp01) recorded | [10.1038/nn.3741](https://doi.org/10.1038/nn.3741) |
| Lin, A. C. et al. 2014, *Nat Neurosci* 17, 559–568 | APL feedback (graded APL option) | [10.1038/nn.3660](https://doi.org/10.1038/nn.3660) |
| Hengstenberg 1988, *J Comp Physiol A* 163, 151–165 | **related literature, not the source of the constants** (the head-reflex gains and latency are hand-set); not verified, listed for completeness: the paper could not be opened (publisher page asks for a sign-in), only the bibliographic record was checked on Crossref (2026-10-07) | [10.1007/BF00612425](https://doi.org/10.1007/BF00612425) |
| Head-yaw constants G_yaw 0.6, θ_max 15°, reset saccade 9° (SPEC_SENSORY_INPUTS §3.3d, `flight/head_reflex.py`) | — | **hand-set; motivated by the fly gaze-stabilisation literature; not traced to a specific source.** Related literature, not the source of the constants: Davis, B. A. & Mongeau, J.-M. (2023), *PLoS Comput Biol* 19, e1011746, doi:10.1371/journal.pcbi.1011746 (preprint doi:10.1101/2021.12.29.474433); Cellini, B., Salem, W. & Mongeau, J.-M. (2022), *PNAS* 119, e2121660119, doi:10.1073/pnas.2121660119. The pre-registration cited "Cellini, Salem & Mongeau 2022, *PLoS Comput Biol* 18:e1011746 / bioRxiv 2021.12.29.474433", which mixes the two papers (correction note of 2026-10-05 in SPEC §3.3d) |
| Huang, J. et al. 2010, *Neuron* 67, 1021–1033 | not verified, listed for completeness: no transmitter value is attributed to it here; the bibliographic record (doi:10.1016/j.neuron.2010.08.025, "Functional Connectivity and Selective Odor Responses of Excitatory Local Interneurons in Drosophila Antennal Lobe") matches the volume and pages cited in `scripts/make_nt_literature.py`, but the paper was not opened | [10.1016/j.neuron.2010.08.025](https://doi.org/10.1016/j.neuron.2010.08.025) |
| Fishilevich & Vosshall 2005, *Curr Biol* 15, 1548–1553 | not verified, listed for completeness: the bibliographic record is confirmed (doi:10.1016/j.cub.2005.07.066), but the statement that DoOR's receptor → glomerulus mapping is built from this paper (and Couto et al. 2005) could not be confirmed from the DoOR repository; the mapping is used as provided by DoOR.data | [10.1016/j.cub.2005.07.066](https://doi.org/10.1016/j.cub.2005.07.066) |

## 7. This work

No licence has been chosen for the code of this work. No `LICENSE` file is added until the upstream author of NeuroFly has answered (§1). The code of this work contains parts adapted from NeuroFly ([docs/ADAPTED_CODE.md](docs/ADAPTED_CODE.md)); this is a further reason not to add a licence before that answer.

**Update 2026-10-07: licence decision.** The paragraph above is the state of 2026-10-05 and is kept. By the author's decision of 2026-10-07 the code written in this work is licensed under MIT (`LICENSE`, Copyright (c) 2026 omeruk) and the work is published under the pseudonym "omeruk". MIT does not cover the third-party components of §1 (Shiu et al. code: MIT with its own copyright line, reproduced in NOTICE.md; FlyGym: Apache-2.0; FlyVis and other dependencies: own licences), FlyWire data (CC BY-NC 4.0, not distributed), results derived from FlyWire (`figures/data/*.csv`, result JSON files under `docs/`, data bundle: CC BY-NC 4.0) or any upstream NeuroFly file (no licence file upstream; question unanswered; none in the public copy).
