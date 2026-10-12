# Synaptera: BANC Brain — independent review and plan for the next study (2026-10-12)

This folder ("Synaptera: BANC Brain") holds the code, model, physics and test review of the Synaptera v1.0.0 snapshot; new
analyses of the connectome; the options offered by BANC; research notes on similar work ("The Driving Fly", The Uploading
Lab, etc.); the architecture plan for the next study and the setup package of the new project. Language: English.
These files were added **after** the snapshot; they are not in `docs/SNAPSHOT_MANIFEST.md`.

| document | content |
|---|---|
| [01_CODE_REVIEW.md](01_CODE_REVIEW.md) | Bugs and gaps; high/medium/low severity; priority fix list |
| [02_CONNECTOME_MODEL_PHYSICS_TESTS.md](02_CONNECTOME_MODEL_PHYSICS_TESTS.md) | Connectome structure analysis, brain model, physics engine, evaluation of the brain tests and results; test/simulation results of this session |
| [03_BANC_OPPORTUNITIES.md](03_BANC_OPPORTUNITIES.md) | What can be done with the BANC brain + nerve cord and possible outcomes; appendix A: first look at the Codex BANC export |
| [04_RESEARCH_NOTES.md](04_RESEARCH_NOTES.md) | How The Driving Fly (flyhard), fly-self-driving, flydrive, The Uploading Lab, Eon, Fly.exe, fly-cartpole, … were done |
| [05_ARCHITECTURE_PLAN.md](05_ARCHITECTURE_PLAN.md) | Layered architecture, phased roadmap and risk register for Synaptera-2 |
| [06_NEW_PROJECT_SETUP.md](06_NEW_PROJECT_SETUP.md) | Setup of the new project (`omeruk/synaptera-banc-brain`): `new_project/setup.sh`, migration list, `CLAUDE.md`, first prompts |
| `results/` | Numerical outputs of this analysis (FlyWire-derived files → CC BY-NC 4.0, as the repository policy; BANC-derived → CC BY 4.0) |

Analysis scripts: `scripts/connectome_structure.py`, `scripts/dn_lr_asymmetry.py`, `scripts/grn_mn9_check.py`,
`scripts/banc_first_look.py` (data: downloaded with the root `scripts/fetch_data.py`; BANC: Codex export).

## Repository layout (to keep things separate)

| what | where | note |
|---|---|---|
| Published Synaptera v1.0.0 (code, reports, figures) | this repository, root | **Not changed.** The file list and SHA-256 of `docs/SNAPSHOT_MANIFEST.md` stay valid |
| This analysis ("Synaptera: BANC Brain") | this repository, `synaptera-banc-brain/` | Only this folder is written; root files are not touched |
| The BANC study (plan F0–F6: ported code with the v1 fixes built in, data pipeline, VNC, reflexes, training) | **new repository** `omeruk/synaptera-banc-brain` | Different architecture and data licence (BANC CC BY 4.0 / FlyWire CC BY-NC); set up with `06_NEW_PROJECT_SETUP.md` |

Branch names: `omeruk/<topic>`. `main` only through a PR.

## Executive summary

**Code:** no code bug was found that invalidates the reported results. Test suite: **123 passed, 51 skipped, 0 failed**
(most skips because of Codex data that need a sign-in). The 4 derivable data files are SHA-256 identical to the development
copy. High-severity findings:
1. **Within-step brain–body acausality:** the body is driven by spikes produced "in the future" within the same 25 ms interval (a command queue is needed).
2. **No left/right asymmetry check:** DNp15's right input is 1.66× its left (65th most asymmetric of 383 DNs), DNp10's 0.24×
   (8th) → both reported lateral-readout failures were predictable from the connectome.
3. **Information mismatch in the training ladder:** the teacher's turn command comes from the odour field, the brain receives only vision; stopped before the DAgger rounds.
4. **Visual sampling at 80 Hz:** ~49° shift per frame at 4.4 mm from a tower → aliased motion perception.
5. **Unbounded wing stroke amplitude:** can reach ~206°.

**Connectome (new findings):**
- The signed linear influence of the leg sugar GRNs on MN9 is **negative**, that of the labellar GRNs **positive** → the leg
  GRN → MN9 failure is structural; also independently confirmed in this session with the unmodified Shiu model (12 leg GRNs
  @100 Hz → MN9 0/0 Hz; 36 labellar GRNs → 54–55 / 48 Hz; two seeds).
- 54 % of DNg02's input is inhibitory and part of it comes from ascending neurons that are never driven → the silence comes not from reachability but from net inhibition + no tonic drive.
- 77 % of the internal LN+PN synapses of the antennal lobe are excitatory (the Shiu sign rule counts amines as excitatory); leading eigenvalue ~2,184 synapses → a self-sustaining lock-up is structurally expected.
- The model has no wing/haltere/leg motor neurons; the 1,736 ascending neurons are never driven.

**BANC:** brings the VNC and real wing/haltere/leg motor neurons; CC BY 4.0. Most valuable possible gains: handing the DN →
wing bridge to the connectome, the haltere reflex from the connectome, the natural leg-taste → MN9 trigger, take-off by the
GF. Risks: proofreading-related L/R asymmetry (optic lobe right/left 1.56× in the current Codex export), sparseness (~2.6×
fewer synapses per neuron than FlyWire), no resting activity. The current Codex BANC export contains MN9, 62 wing MNs, 25
haltere MNs and TTMn (`03_BANC_OPPORTUNITIES.md` appendix A).

**Similar work:** all "driving" projects keep the topology fixed and **train the dynamic parameters or the readout layer**
(rate model + input normalisation + carried state + imitation + DAgger); in none of them is flight entirely neural.

**Plan:** F0 port + v1 fixes → F1 BANC data pipeline + QA → F2 open-loop reproductions → F3 VNC motor interface and haltere
reflex → F4 take-off/landing/feeding trigger → F5 trainable connectome arm → F6 full task. Details: `05_ARCHITECTURE_PLAN.md`.

## Access note
`thedrivingfly.com` and `theuploadinglab.ai` (and Harvard Dataverse, arXiv, Nature) were blocked by the network policy of
this working environment; the research notes rely on documents in the projects' GitHub repositories and on search results
(`04_RESEARCH_NOTES.md` §0).
