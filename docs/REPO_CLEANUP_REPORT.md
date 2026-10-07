# Repository clean-up report (2026-10-05; report only, nothing was deleted)

Measured with `git ls-files` + `du -b`, `git count-objects -vH`, `git rev-list --objects --all | git cat-file --batch-check`. Branch `sensory-inputs`, HEAD 256d072. 1 MB = 10^6 bytes.

## Summary
| measure | value |
|---|---|
| `.git` directory | 658 MB (pack 583 MiB) |
| all blobs in the history (on disk, compressed) | 686.4 MB |
| tracked files (working tree) | 693 files, 746.6 MB |
| working directory in total (untracked included) | 3.1 GB (untracked `simulations/` outputs 2.2 GB, 104 files) |
| FlyWire data in the repository? | **Yes** (below) |

## Tracked files above 50 MB
| size | file | added by | note |
|---|---|---|---|
| 100.8 MB | `brain_model/Connectivity_783.parquet` | NeuroFly (1a376da) | FlyWire v783 (licence: THIRD_PARTY.md §2.1) |
| 100.8 MB | `simulation_data/flywire_connectome_v783/Connectivity_783.parquet` | NeuroFly (2a50708) | byte-identical to the file above (same blob); tracked although listed in `.gitignore` |
| 93.6 MB | `simulations/preview2.gif` | NeuroFly (2a50708) | an older 102.6 MB version is also in the history |
| 86.6 MB | `brain_model/2023_03_23_connectivity_630_final.parquet` | NeuroFly (1a376da) | FlyWire v630; not used by the flight code |

GitHub rejects single files above 100 MiB (104.9 MB) and warns above 50 MiB. These four files are below the limit but trigger the warning. Other blobs above 20 MB in the history: `preview.gif` 47.0 MB, `flywire_annotations.tsv` 32.6 MB.

## Breakdown by directory (tracked)
| directory | size |
|---|---|
| `simulations/` | 309.8 MB (HDF5 145.9 MB: walking v33–v42 and final_a/b/c of ~11.5 MB each; GIF 140.6 MB; demo.mp4 17.8 MB) |
| `brain_model/` | 229.8 MB |
| `simulation_data/flywire_connectome_v783/` | 136.8 MB |
| `plots/` | 50.3 MB |
| `data/` | 12.5 MB |

## FlyWire data in the repository
- **Raw FlyWire / Codex files:** `brain_model/Completeness_783.csv`, `Connectivity_783.parquet`, `flywire_annotations.tsv`, `2023_03_23_completeness_630_final.csv`, `2023_03_23_connectivity_630_final.parquet`, `descending_neurons.csv`, `sez_neurons.pickle`, `results/example/*.parquet` (outputs of the Shiu model); `simulation_data/flywire_connectome_v783/` (a copy of the same files); `data/column_assignment.csv.gz` (Codex download, copied unchanged).
- **Derived:** `data/neuron_*.npz`, `data/*_783.csv`, `data/vision_boundary_*` (derived from FlyWire; treated as CC BY-NC 4.0 until the FlyWire licence is verified, THIRD_PARTY.md §2). `data/orn_spontaneous_783.csv` is also derived from DoOR.data (CC BY-SA 4.0).
- Most raw files were added by the upstream repository (NeuroFly); only `data/column_assignment.csv.gz` and the derived files were added in this work.

## Recommendations (decision and execution are yours; none was carried out)
1. **Stop tracking the raw FlyWire files** (`git rm --cached`; local copies stay) and add `brain_model/*.parquet`, `brain_model/*.csv`, `brain_model/*.tsv` to `.gitignore`. Replace them with download instructions (README "Data") and an optional download/check script (file name + SHA-256).
2. **Removing them from the history:** step 1 only removes the files from future commits; they stay in old commits. If the repository is pushed to a new remote (e.g. Synaptera) and the data must never be published, the history must be rewritten (`git filter-repo --path ... --invert-paths`). This is destructive (commit hashes change, and the pre-registration commit references in the reports — 5aefc83, 65f05bd, 1b48395, 256d072, etc. — become invalid). Alternative: keep this history-preserving repository private, open a new publication repository from a clean snapshot, and refer to the old hashes in the reports as a "private archive".
3. **The v630 connectome** (`2023_03_23_*`, ~90 MB) is not used by the flight code; it is a copy from the Shiu repository. It can be untracked.
4. **`simulation_data/flywire_connectome_v783/`** is tracked although it is listed in `.gitignore`; same files as `brain_model/`. It can be untracked (check first which path the walking code reads).
5. **GIFs** (`preview.gif`, `preview2.gif`, 140.6 MB): README previews of the upstream repository. Use a reduced version or a release attachment.
6. **Tracked HDF5 files** (145.9 MB): final_a/b/c are the sources of the reports. For these and for the untracked final_v2a/c, n1/n2, seed and start-test HDF5 files (~60 MB each), a data archive with a DOI such as Zenodo is recommended, linked from the README. Note: the HDF5 files contain spike data derived from FlyWire identifiers; the same FlyWire terms apply (THIRD_PARTY.md §2).
7. **Large untracked files** (e.g. `flight_biological_40s_data.h5` 627.8 MB, `flight_40s_perfected_data.h5` 214.1 MB; trials from before the closed loop): to avoid adding them by mistake, `simulations/*.h5` (with `!` exceptions for the needed ones) can be added to `.gitignore`.
