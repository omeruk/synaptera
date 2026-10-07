# NOTICE

Synaptera builds on third-party data, models and software. This file lists their licences and attributions; the full audit (every component, where each licence was read, provenance of every `data/` file, UNVERIFIED items) is in [THIRD_PARTY.md](THIRD_PARTY.md). The licence information was read on 2026-10-05 from package metadata, from the LICENSE/DESCRIPTION files in the repositories and from the GitHub API; lines marked "to be verified" could not be verified.

## Upstream repository: NeuroFly
- **Synaptera builds on NeuroFly:** [github.com/seven-monarchs/NeuroFly](https://github.com/seven-monarchs/NeuroFly) (author name of the git commits: "Monarch"). Synaptera was developed as a continuation of NeuroFly: the history of its development repository starts with NeuroFly's commits (2026-03-25 – 2026-04-05).
- **This copy contains no NeuroFly file.** NeuroFly's walking simulation (`fly_brain_body_simulation.py`, `generate_plots.py`, `fruitfly/`, its `simulation_data/` files, the walking tests, `Dockerfile`, `run.bat`), its copy of `brain_model/` and its READMEs are not included. `README.md` has the same path as NeuroFly's README, but its content was written entirely in this work (no line of the upstream README remains; checked when the copy is built).
- Every file of this copy was written in this work (list with SHA-256: [docs/SNAPSHOT_MANIFEST.md](docs/SNAPSHOT_MANIFEST.md)). The flight code (`fly_flight_brain_body_simulation.py`, `flight/`, `simulation_data/odor_field_3d.py`, `scripts/`, `tests/flight/`, `render_flight_*.py`, `generate_flight_plots.py`) is new; parts of it are **adapted from the NeuroFly walking script** (same logic, formulas and constants, no verbatim lines). File and line ranges: [docs/ADAPTED_CODE.md](docs/ADAPTED_CODE.md).
- **Licence of NeuroFly: to be verified.** There is no licence file in the repository or in its git history; the GitHub API shows no licence either (`license: null`, 2026-10-05). Code without a licence file is by default "all rights reserved"; because parts of the flight code are adapted from it, redistribution and licensing of the adapted parts depend on the upstream author; the MIT licence of this work does not extend to any upstream file (none is in this copy).
- **Status of the adapted parts (2026-10-07).** The ideas and some constants of a few flight functions were adapted from NeuroFly and NeuroFly is credited for them. The upstream repository has no licence file. The licence question was put to the upstream author and no answer has been received up to this date. The affected flight code (annotation-based neuron groups, soma positions, the odour turn map, the FlyVis motion bias) was then re-implemented from a written specification ([docs/ADAPTED_CODE.md](docs/ADAPTED_CODE.md) §D), and the new functions give the same results as the old ones (§E). **This is not a clean-room re-implementation:** the same AI-assisted process had read the upstream code before and wrote the specification and the new code. A few constants (for example the two annotation patterns and the turn/motion-bias gains) are the same numbers as upstream and are listed as such. If the upstream author asks, the affected parts will be removed. This text states facts only and makes no claim about legal status. The code written in this work is MIT-licensed (decision of 2026-10-07, see *Code of this work* below); no upstream file is part of this licence.
- "NeuroFly" is the name of the upstream project; Synaptera does not use it as its own project name. Occurrences of "NeuroFly" in file, module and branch names are historical.

## Data
### FlyWire connectome (v783)
- **Licence: CC BY-NC 4.0 for the FlyWire public release.** The FlyWire citing-guidelines page states that the public release data (version 783, October 2023, including all data available in Codex for snapshot 783) is made available under CC BY-NC 4.0 ([flywire.ai/guidelines](https://flywire.ai/guidelines), opened 2026-10-07). The Zenodo connectivity record (doi:10.5281/zenodo.10676866) is CC BY 4.0; the stricter FlyWire licence is applied here. The `flywire_annotations` repository has no licence file. Details: [THIRD_PARTY.md](THIRD_PARTY.md) §2.1.
- **All FlyWire-derived files (derived data files, run records) are used and shared under CC BY-NC 4.0: no commercial use, attribution required.** Terms of use: [flywire.ai/tos](https://flywire.ai/tos), [codex.flywire.ai](https://codex.flywire.ai).
- Used by the code (**none of them is included in this copy**; `scripts/fetch_data.py` downloads and rebuilds them): `Completeness_783.csv`, `Connectivity_783.parquet`, `flywire_annotations.tsv`, Codex downloads (`classification`, `consolidated_cell_types`, `neurons`, `neuropil_synapse_table`, `synapse_coordinates`, `coordinates`, `column_assignment`) and the `data/*` files derived from them.
- Attribution: Dorkenwald, S. et al. (2024). *Nature* 634, 124–138. doi:10.1038/s41586-024-07558-y · Schlegel, P. et al. (2024). *Nature* 634, 139–152. doi:10.1038/s41586-024-07686-5 · Visual columns: Matsliah, A. et al. (2024). *Nature* 634, 166–180. doi:10.1038/s41586-024-07981-1.

### DoOR.data
- `data/orn_spontaneous_783.csv` (not included in this copy; `scripts/make_orn_spontaneous.py`, run by `scripts/fetch_data.py`, rebuilds it) is derived from the `SFR` rows of DoOR.data (Hallem & Carlson 2006 column).
- **Licence: CC BY-SA 4.0** (DoOR.data `DESCRIPTION`, [github.com/ropensci/DoOR.data](https://github.com/ropensci/DoOR.data)). ShareAlike: the derived data file must be shared under the same licence.
- The file also contains FlyWire-derived columns. If those are CC BY-NC 4.0, the combined file cannot meet both licences; therefore this copy does not distribute it and contains only the generating script (THIRD_PARTY.md §3).
- Attribution: Münch, D. & Galizia, C. G. (2016). DoOR 2.0. *Sci Rep* 6, 21841. doi:10.1038/srep21841 · Hallem, E. A. & Carlson, J. R. (2006). *Cell* 125, 143–160. doi:10.1016/j.cell.2006.01.050.

## Models and software
| component | use | licence | attribution |
|---|---|---|---|
| Shiu et al. LIF model ([philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model)) | `brain_model/model.py` (downloaded by `scripts/fetch_data.py`, not included), recurrent synapse set-up and LIF parameters | **MIT**, Copyright (c) 2023 Philip Shiu and Nico Spiller (`brain_model/LICENSE`) | Shiu, P. K. et al. (2024). *Nature* 634, 210–219. doi:10.1038/s41586-024-07763-9 |
| FlyGym / NeuroMechFly v2 | body, eyes, contacts, adhesion | **Apache-2.0** (flygym 1.2.1 metadata) | Wang-Chen, S. et al. (2024). *Nature Methods*. doi:10.1038/s41592-024-02497-y |
| FlyVis | visual network (FlyGym eyes → FlyVis → FlyWire boundary layer) | **MIT** (flyvis 1.2.0 metadata) | Lappalainen, J. K. et al. (2024). *Nature* 634, 1132–1140. doi:10.1038/s41586-024-07939-3 |
| Brian2 | LIF simulation | **CeCILL-2.1** (brian2 2.9.0 metadata) | Stimberg, M., Brette, R. & Goodman, D. F. M. (2019). *eLife* 8, e47314. doi:10.7554/eLife.47314 |
| MuJoCo | physics | **Apache-2.0** (mujoco 3.2.7 metadata) | Todorov, E., Erez, T. & Tassa, Y. (2012). *IROS 2012*. doi:10.1109/IROS.2012.6386109 |
| dm_control | FlyGym dependency | Apache-2.0 (dm_control 1.0.27 metadata) | — |
| flybody | NeuroFly dependency (commit d015e9b) | Apache-2.0 (flybody metadata) | — |

Other Python dependencies (`requirements.txt`) are used under their own licences; they are not included in this copy.

Bibliographic data of the references above were re-checked on Crossref on 2026-10-07; related projects and connectome data licences (MANC, BANC, male CNS) are listed with their sources in [REPORT.md](REPORT.md#related-work).

## Code of this work
The code written in this work is licensed under the **MIT licence** ([LICENSE](LICENSE), Copyright (c) 2026 omeruk). Facts about its scope:
- MIT does not cover third-party components: the Shiu et al. brain-model code (own MIT licence, reproduced below), FlyGym (Apache-2.0), FlyVis and the other dependencies keep their own licences; FlyWire data are CC BY-NC 4.0 and are not distributed here.
- Results derived from FlyWire (`figures/data/*.csv`, the result JSON files under `docs/`) and the separate data bundle are CC BY-NC 4.0; this work is non-commercial.
- NeuroFly: ideas adapted and credited; the upstream repository has no licence file, the licence question has had no answer up to 2026-10-07; the related code was re-implemented from a written specification (not clean-room); if the upstream author asks, the affected parts will be removed. Upstream files are not in this copy.

## Notice for the Shiu et al. brain-model code
This work uses the Shiu et al. LIF model (`brain_model/model.py`, imported by `flight/brain.py`; the recurrent synapse set-up and the LIF parameters are the ones of that code; the 20 sugar-GRN root IDs in `flight/groups.py` come from the same repository). The copyright notice and permission notice of that repository (`LICENSE` at [philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model), commit `91bdd1e`) are reproduced here:

```
MIT License

Copyright (c) 2023 Philip Shiu and Nico Spiller

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
