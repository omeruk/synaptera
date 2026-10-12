# 06 — New project setup: synaptera-banc-brain

Date: 2026-10-12. Decision: Synaptera v1.0.0 stays a **frozen archive**; the next study (`05_ARCHITECTURE_PLAN.md`) runs in
a new folder and a new repository (`omeruk/synaptera-banc-brain`). The v1 bugs (H1–H5, M1–M10, L1–L9;
`01_CODE_REVIEW.md`) are not patched into the old repository but built into the design of the new code.

Setup package: `new_project/setup.sh` (script), `new_project/migration.tsv` (migration list, single source),
`new_project/CLAUDE.md` (standing rules of the new repository). Language: everything in English.

## 1. Setup (on your computer, once)

```bash
cd ~/synaptera && git pull origin main
SYNAPTERA=~/synaptera DEV_REPO=~/Documents/NeuroFly bash synaptera-banc-brain/new_project/setup.sh
```

The script:
1. Creates `~/synaptera-banc-brain` with the planned layout (`connectome/ engine/ sense/ motor/ body/ coupling/ tasks/
   train/ prereg/ scripts/ configs/ tests/ docs/`). If the folder exists and is not empty, it **stops**.
2. Puts the documents of this folder in `docs/`, the analysis scripts in `scripts/analysis/`, `CLAUDE.md` at the root.
3. Copies the 52 files of `migration.tsv` **unchanged** into `vendor/synaptera_v1/`; `MANIFEST.md` records the source commit
   and the SHA-256 of every file; `MIGRATION_CHECKLIST.md` is the ordered checklist.
4. Copies `brain_model/` and `data/` from the development repository (`cp -n`, never overwrites). The Codex downloads stay
   in `~/Downloads`.
5. Writes `.gitignore`, runs `git init` and makes the first commit (with your git identity).

Then:
```bash
# On GitHub: empty repository omeruk/synaptera-banc-brain (WITHOUT README/licence)
cd ~/synaptera-banc-brain
git remote add origin https://github.com/omeruk/synaptera-banc-brain.git && git push -u origin main
conda activate neurofly && claude
```

Verified in this (cloud) environment in a scratch folder: 52 files, manifest, checklist, data copy, first commit; a second
run stopped with "folder not empty".

**Already set up with the earlier Turkish package?** Run `new_project/update_to_english.sh` once (section 5).

## 2. Migration rule

| decision | meaning | count |
|---|---|---|
| `take` | taken as is (import path only) | 3 |
| `adapt` | taken and adapted (BANC support, v1 bug fixes, legacy flags removed) | 35 |
| `pattern` | code not copied; the design/pattern is reused | 14 |
| `leave` | not carried over | the rest |

`vendor/synaptera_v1/` is **reference only** and is never imported. Each new file starts with a
`# Ported from synaptera@<commit>:<path>` note; when the migration is done `vendor/` can be deleted (MANIFEST stays).

**Not carried over, and why:**
- Parts adapted from NeuroFly (Synaptera `docs/ADAPTED_CODE.md`): the legacy group rule and `neuron_positions`
  (`groups.py`), the odour turn map `turn_hand` (`hybrid.py`), `LoomBias` (`sensors.py`) and related constants — unclear
  licence and not needed in the BANC project.
- Legacy flags and paths: `inputs="legacy"`, `--asc-legacy`, the all-DN turn readout, the post-hoc DNp15 choice.
- Specific to v1.0.0: `run_*.sh`, `scripts/diag/*`, report/figure/media scripts (`make_figures`, `make_media`,
  `make_public_snapshot`, `make_data_bundle`, `check_*`), `render_flight_video.py`, `render_flight_compare.py`,
  `generate_flight_plots.py`, `flight/controller.py` (as a pattern), `tests/flight/test_adapted_spec.py`,
  `test_controller.py`, `test_leg_grn.py`, `test_nt_*`.
- Reports, SPECs, figures, media: not copied; link to the v1 repository.

Full list, target paths and per-file notes: `new_project/migration.tsv`.

## 3. Migration order (dependency order)

1. **connectome/** — common schema, FlyWire 783 adapter, crosswalk, sign rules, QA (symmetry gate).
2. **engine/** — `NeuralEngine` interface, Shiu LIF (Brian2), Poisson input without delay; hashed `model.py` under `third_party/`.
3. **body/** — `ArenaSpec`, FlyGym body, wing model (amplitude limit), noise.
4. **sense/** — FlyVis vision + boundary layer (olfaction deferred).
5. **motor/** — readouts (pre-registered types), the hand-made bridge and reflexes as **control arms**.
6. **coupling/** — causal command queue, recording (overwrite protection), replay.
7. **tasks/**, **train/**, **scripts/**, **tests/**.

**First acceptance test (F0):** with the new code on FlyWire, with the hand-made bridge arm and command latency = 0,
reproduce the n1 flight of v1 (S1 ✓, S2 ✓; position trace compared with the v1 HDF5 record). Then run the same flight with
latency = 1 interval (causal) and report the difference. Do not move to BANC (F1) before this passes.

## 4. Prompts for Claude Code in the terminal

First prompt:
> Read CLAUDE.md, docs/05_ARCHITECTURE_PLAN.md and docs/06_NEW_PROJECT_SETUP.md. Apply MIGRATION_CHECKLIST.md in order: for
> each item, write the adapted code at the target location from the original file in vendor/synaptera_v1/, add its test,
> run the tests, tick the item and commit. Stop when connectome/ and engine/ are done and give me a summary. Do not carry
> over the parts adapted from NeuroFly; commit to the branch omeruk/migration-1, not directly to main.

Next prompts (each on its own branch + PR):
1. "Continue the migration: body/, sense/, motor/, coupling/; then run the first acceptance test of docs/06 §3."
2. "F1: use the Codex BANC export in banc/ (neurons-banc.csv.gz, connections_princeton-banc.csv.gz). Write
   connectome/adapters/banc.py on the common schema (sign from the neuron-level Predicted NT type; ask me to decide the rule
   for HIST and missing NT), record the file hashes, produce the QA report (left/right symmetry, sparseness, critical types).
   Then compare with docs/03_BANC_OPPORTUNITIES.md appendix A."
3. "F2 pre-registration: write the criteria of the 5 open-loop tests of docs/05_ARCHITECTURE_PLAN.md F2 into prereg/; show
   them to me before running anything."

## 5. Updating a project set up with the earlier Turkish package

If `~/synaptera-banc-brain` was created before the English version (it has `TASINMA_LISTESI.md` and Turkish file names
in `docs/`), run once, with no Claude Code session working in that folder:
```bash
cd ~/synaptera && git pull origin main
SYNAPTERA=~/synaptera bash ~/synaptera/synaptera-banc-brain/new_project/update_to_english.sh
```
It replaces the Turkish documents in `docs/` with the English ones, replaces `CLAUDE.md`, renames the checklist to
`MIGRATION_CHECKLIST.md` (ticked items stay ticked), rewrites the `vendor/synaptera_v1/MANIFEST.md` text, and commits.
