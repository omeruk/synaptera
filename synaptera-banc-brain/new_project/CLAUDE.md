# CLAUDE.md — synaptera-banc-brain

Standing instructions for Claude Code sessions in this repository. Copied to the root of the new project.

## Project

Continuation of Synaptera v1.0.0 (FlyWire v783 whole-brain LIF model + FlyGym/MuJoCo body, closed-loop *Drosophila*
flight). Goal: hand the hand-made DN → wing bridge, the reflexes and the triggers over to the BANC (brain + nerve cord)
connectome, and show this with measurable, pre-registered, controlled experiments.
- Architecture and roadmap: `docs/05_ARCHITECTURE_PLAN.md` (phases F1–F6, gates, risk register).
- Review of the previous study: `docs/01_CODE_REVIEW.md` … `docs/04_RESEARCH_NOTES.md`.
- Origin of the carried code: `docs/06_NEW_PROJECT_SETUP.md` and `vendor/synaptera_v1/MANIFEST.md`.
- Synaptera v1.0.0 (github.com/omeruk/synaptera) is a **frozen archive**; no code is written there.

## Environment and commands

- Python environment: conda `neurofly` (Python 3.10; Brian2 2.9.0, MuJoCo 3.2.7, FlyGym 1.2.1, FlyVis 1.2.0, numpy 2.0.2).
- Run every command as `env -u PYTHONPATH ...` (a PYTHONPATH from the shell profile can shadow packages).
- Headless rendering: `export MUJOCO_GL=egl` (system package `libegl1`, if needed `libosmesa6`).
- Tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 env -u PYTHONPATH python -m pytest tests/` (full-brain tests with `--runslow`).
- Data: `env -u PYTHONPATH python scripts/fetch_data.py` (SHA-256 pinned downloads; Codex files need a sign-in:
  `--codex-dir ~/Downloads`). Data files (`brain_model/`, `data/`, `banc/`, `runs/`) are **never committed**.
- One full-brain run takes ~3.5 GB RAM (FlyWire); BANC (~160–190k neurons) needs more. Long runs with `nohup` under
  `runs/<name>/`; follow progress in the log.

## Rules that do not change

1. **Source label:** every motor and sensory term carries exactly one label — `BRAIN`, `VNC`, `HAND`, `REFLEX`, `TRAINED`,
   `FLYVIS` — and is recorded separately. A term with an unclear label is not added.
2. **Parameter origin:** every constant is registered in `configs/assumptions.json` with an origin class: `M` measured,
   `P` population prior, `F` fitted (state what it was fitted to), `E` engineering scaffold, `I` irrecoverable.
3. **No tuning on behaviour:** constants are never tuned by looking at behavioural success; only against open-loop
   physiology/anatomy criteria, and those criteria are written down in advance.
4. **Causal timing:** the body receives the neural engine's output **one coupling interval late** (command queue); the
   latency is explicit in the configuration and in the record. Driving the body in an interval with spikes produced in that
   same interval is forbidden (Synaptera v1 bug H1).
5. **Symmetry gate:** no left/right readout or path is used in an experiment before it passes the input-synapse gate
   |log2(R/L)| < 0.5 (generalisation of `scripts/analysis/dn_lr_asymmetry.py`). The gate result is reported.
6. **Pre-registration:** criteria and decision rules are committed **before** the runs (and registered on OSF where
   possible); they are never changed afterwards. Everything added later is labelled "post-hoc".
7. **Controls:** in every experiment an activity-matched shuffled graph, a random graph with the same degrees and an
   ablation; in training also linear + MLP. Seeds also change the physical noise; at least 5 seeds.
8. **The reference arm is not modified:** the spiking reference arm runs with the Shiu et al. parameters; every deviation
   (sign rule, neuron model, input path) is a named **model variant** switched on by a flag.
9. **Information alignment:** in training the teacher signal must be derivable from the senses the brain receives; show
   cross-validated R² > 0 in a brainless "bypass" arm first (Synaptera v1 bug H3).
10. **Negative results** are reported with equal weight. `DEV` subnet runs are never results.
11. **Numbers are never typed by hand:** every number in a report is recomputed from the records by a script and checked
    against the text by `scripts/verify_report.py`.
12. **Licence:** code adapted from NeuroFly (Synaptera `docs/ADAPTED_CODE.md`) is not carried over. BANC data are CC BY 4.0,
    FlyWire data CC BY-NC 4.0; derived files carry the licence of their source.
13. **Result files are protected:** an existing run output is never overwritten (new version or an explicit `--overwrite`).

## Git and language

- Branches: `omeruk/<topic>`; `main` only through a PR.
- **Everything is in English:** code, comments, commit messages, documents, reports, file names.
- Every PR: the relevant tests + (if any) the output of the verification script.
