# Originality and citation check

Produced on 2026-10-07 with `scripts/check_originality.py` (code similarity), `scripts/check_text_overlap.py` (text overlap) and by opening each source named in section 3. The scripts compute counts only; nothing in this file interprets the content of the upstream files.

## 1. Code similarity with the upstream NeuroFly source files

Compared: every `.py` / `.sh` file of the public copy's allow-list (files of `docs/FILE_PROVENANCE.md` section B that are not upstream paths; archive, data, logs and plots excluded) against every `.py` / `.sh` file of the upstream commit `b59264a`, read with `git show` from the local repository. Lines are normalised (blank lines, comments and docstrings removed, white space collapsed). "Shared lines" counts lines (as a multiset) present in both files; trivial lines (imports, bare brackets, `pass`, `else:`, `try:`, `return` …) are counted separately and not in the ratio. "Longest block" is the longest run of consecutive identical lines; the threshold for a stop was 5 meaningful lines in one block.

**Result:** no file reaches the threshold. The longest identical block of meaningful lines in any file is 1 line. The table lists every file with at least one shared meaningful line (the five highest are the first five rows); files not listed share none.

Upstream: `b59264a` (29 .py/.sh files); public files compared: 127; files with at least one shared meaningful line: 48.

| public file | lines | meaningful lines | shared meaningful | shared trivial | longest block (lines) | meaningful lines in it | ratio | best upstream match |
|---|---|---|---|---|---|---|---|---|
| `generate_flight_plots.py` | 498 | 482 | 6 | 6 | 4 | 1 | 0.012 | `generate_plots.py` |
| `flight/recorder.py` | 241 | 235 | 4 | 4 | 1 | 0 | 0.017 | `fly_brain_body_simulation.py` |
| `scripts/figures/make_figures.py` | 701 | 666 | 4 | 13 | 4 | 1 | 0.006 | `generate_plots.py` |
| `render_flight_video_v2.py` | 1484 | 1438 | 3 | 18 | 3 | 1 | 0.002 | `generate_plots.py` |
| `tests/flight/test_brain.py` | 310 | 285 | 3 | 1 | 1 | 0 | 0.011 | `tests/test_poisson_rate_update.py` |
| `flight/groups.py` | 224 | 220 | 2 | 4 | 2 | 0 | 0.009 | `fly_brain_body_simulation.py` |
| `flight/visual_input.py` | 222 | 209 | 2 | 6 | 2 | 0 | 0.010 | `fly_brain_body_simulation.py` |
| `render_flight_video.py` | 214 | 196 | 2 | 10 | 3 | 1 | 0.010 | `fly_brain_body_simulation.py` |
| `tests/flight/test_body.py` | 303 | 291 | 2 | 1 | 1 | 0 | 0.007 | `tests/test_optic_flow_reflex.py` |
| `flight/body.py` | 347 | 333 | 1 | 3 | 1 | 0 | 0.003 | `tests/test_flyvis_reflex_integration.py` |
| `flight/config.py` | 88 | 87 | 1 | 1 | 1 | 0 | 0.011 | `tests/test_looming_integration.py` |
| `flight/hybrid.py` | 103 | 99 | 1 | 1 | 1 | 0 | 0.010 | `tests/test_optic_flow_reflex.py` |
| `flight/vision_boundary.py` | 363 | 352 | 1 | 7 | 2 | 0 | 0.003 | `fly_brain_body_simulation.py` |
| `fly_flight_brain_body_simulation.py` | 698 | 654 | 1 | 14 | 1 | 0 | 0.002 | `fly_brain_body_simulation.py` |
| `render_flight_compare.py` | 99 | 88 | 1 | 5 | 1 | 0 | 0.011 | `fly_brain_body_simulation.py` |
| `scripts/diag/a0_apl_gain.py` | 49 | 40 | 1 | 1 | 1 | 0 | 0.025 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/a0_criteria.py` | 172 | 157 | 1 | 3 | 1 | 0 | 0.006 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/a0_symmetry.py` | 123 | 113 | 1 | 1 | 1 | 0 | 0.009 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/a2_openloop.py` | 120 | 109 | 1 | 1 | 1 | 0 | 0.009 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/nf_report.py` | 110 | 100 | 1 | 2 | 1 | 0 | 0.010 | `tests/test_light_source.py` |
| `scripts/diag/o1_diag_report.py` | 190 | 182 | 1 | 1 | 1 | 0 | 0.005 | `tests/test_light_source.py` |
| `scripts/diag/o1_report.py` | 94 | 86 | 1 | 1 | 1 | 0 | 0.012 | `tests/test_light_source.py` |
| `scripts/diag/r0_sugar.py` | 44 | 37 | 1 | 1 | 1 | 1 | 0.027 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/r2_extra.py` | 48 | 44 | 1 | 0 | 1 | 1 | 0.023 | `tests/test_optic_flow_reflex.py` |
| `scripts/diag/r3_open.py` | 85 | 76 | 1 | 0 | 1 | 1 | 0.013 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/r3_open_v1_contaminated.py` | 71 | 63 | 1 | 0 | 1 | 1 | 0.016 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/sa_criteria.py` | 149 | 134 | 1 | 3 | 1 | 0 | 0.007 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/sa_leg_grn.py` | 53 | 42 | 1 | 1 | 1 | 0 | 0.024 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/so_nt_robust.py` | 71 | 58 | 1 | 1 | 1 | 0 | 0.017 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/so_o1.py` | 140 | 121 | 1 | 3 | 1 | 0 | 0.008 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/so_o1_diag.py` | 48 | 38 | 1 | 1 | 1 | 0 | 0.026 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/so_o1_nf.py` | 124 | 106 | 1 | 3 | 1 | 0 | 0.009 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/so_o2.py` | 155 | 138 | 1 | 2 | 1 | 0 | 0.007 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/vd_render.py` | 74 | 59 | 1 | 1 | 1 | 0 | 0.017 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/vd_run.py` | 58 | 46 | 1 | 1 | 1 | 0 | 0.022 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/vl_render.py` | 73 | 58 | 1 | 1 | 1 | 0 | 0.017 | `tests/test_poisson_rate_update.py` |
| `scripts/diag/vl_run.py` | 59 | 47 | 1 | 1 | 1 | 0 | 0.021 | `tests/test_poisson_rate_update.py` |
| `scripts/ladder_fit.py` | 65 | 55 | 1 | 2 | 1 | 0 | 0.018 | `tests/test_poisson_rate_update.py` |
| `scripts/ladder_replay.py` | 72 | 59 | 1 | 2 | 1 | 0 | 0.017 | `tests/test_poisson_rate_update.py` |
| `scripts/make_dn_reference.py` | 78 | 61 | 1 | 2 | 1 | 0 | 0.016 | `tests/test_poisson_rate_update.py` |
| `scripts/make_orn_spontaneous.py` | 76 | 62 | 1 | 1 | 1 | 0 | 0.016 | `brain_model/model.py` |
| `scripts/make_vision_boundary.py` | 49 | 41 | 1 | 3 | 1 | 0 | 0.024 | `generate_plots.py` |
| `scripts/prepare_neuron_geometry.py` | 165 | 149 | 1 | 3 | 1 | 0 | 0.007 | `tests/test_poisson_rate_update.py` |
| `scripts/verify_report_final.py` | 1015 | 951 | 1 | 3 | 1 | 0 | 0.001 | `tests/test_poisson_rate_update.py` |
| `tests/flight/test_nt_impute.py` | 95 | 88 | 1 | 2 | 2 | 0 | 0.011 | `fly_brain_body_simulation.py` |
| `tests/flight/test_nt_literature.py` | 90 | 82 | 1 | 2 | 2 | 0 | 0.012 | `fly_brain_body_simulation.py` |
| `tests/flight/test_vision_boundary.py` | 127 | 116 | 1 | 1 | 1 | 0 | 0.009 | `tests/test_shadow_pole.py` |
| `tests/flight/test_vnc_bridge.py` | 157 | 138 | 1 | 1 | 1 | 0 | 0.007 | `tests/test_optic_flow_reflex.py` |

Files with a longest block of at least 5 meaningful lines: none.

## 2. Upstream text in `nf_report.py` and `so_o1_nf.py`

The comparison check of REPORT §3.7 cites lines of the upstream walking script. The verbatim code strings that were stored for the check have been replaced by the line number and the SHA-256 of the stripped line (`CITED` in `scripts/diag/nf_report.py`); `scripts/verify_report_final.py` recomputes the hashes from `fly_brain_body_simulation.py` if that file is present and otherwise prints "upstream file not present, check skipped". The two keyword selections that reproduce the upstream selection of olfactory and gustatory neurons are now built from keyword lists (the resulting patterns are identical, checked). The row of REPORT §3.7 that described the upstream turn command in code-like notation is written in prose with the same line references. Counts and results are unchanged.

## 3. Citation table (REPORT.md and README.md)

Status: **opened and confirmed** = the source was opened (page, repository, or Crossref record for bibliographic data) on 2026-10-07 and the claim matches what the source states; **not confirmed** = not opened, or the opened source does not settle the claim; such claims are marked in the text as "expectation, source not verified" where they appear.

| claim | where | source | status |
|---|---|---|---|
| FlyWire v783 model: 138,639 neurons, 15,091,983 connections, 54,492,922 synapses | README, REPORT §1 | `brain_model/Completeness_783.csv` (138,639 rows) and `Connectivity_783.parquet` (15,091,983 rows, sum of `Connectivity` 54,492,922), recomputed | opened and confirmed (local files) |
| Dorkenwald et al. 2024, *Nature* 634, 124–138, 10.1038/s41586-024-07558-y | REPORT, README references | Crossref record | opened and confirmed |
| Schlegel et al. 2024, *Nature* 634, 139–152, 10.1038/s41586-024-07686-5 | same | Crossref record | opened and confirmed |
| Shiu et al. 2024, *Nature* 634, 210–219, 10.1038/s41586-024-07763-9 | same | Crossref record | opened and confirmed |
| LIF parameters (v0 = vrst = −52 mV, vth = −45 mV, τm = 20 ms, τ = 5 ms, refractory 2.2 ms, delay 1.8 ms, w_syn 0.275 mV) are those of Shiu et al. | REPORT §2.1 | `model.py` of github.com/philshiu/Drosophila_brain_model (parameter dictionary) and `brain_model/model.py` of this repository | opened and confirmed |
| Shiu repository: MIT licence; configured for FlyWire v630, v783 selectable | REPORT Related work | repository page | opened and confirmed |
| Wang-Chen et al. 2024, *Nature Methods* 21, 2353–2362, 10.1038/s41592-024-02497-y; Lobato-Rios et al. 2022, *Nature Methods* 19, 620–627, 10.1038/s41592-022-01466-7 | REPORT Related work, README | Crossref records | opened and confirmed |
| FlyGym: library for NeuroMechFly v2, MuJoCo, EPFL Neuroengineering Laboratory, Apache-2.0 | REPORT Related work | github.com/NeLy-EPFL/flygym, neuromechfly.org | opened and confirmed |
| Lappalainen et al. 2024, *Nature* 634, 1132–1140, 10.1038/s41586-024-07939-3 | REPORT, README references | Crossref record and abstract | opened and confirmed |
| FlyVis network built from the connectivity of 64 cell types of the optic-lobe motion pathways | REPORT §2.4 (wording "pretrained, not FlyWire") | abstract (Crossref) states the 64 cell types and the optic-lobe motion pathways; the full paper was not opened | partly confirmed; "pretrained" and "not FlyWire" are statements about our use (FlyVis weights downloaded with `flyvis download-pretrained`), not checked against the paper |
| Matsliah et al. 2024, *Nature* 634, 166–180, 10.1038/s41586-024-07981-1 | README references | Crossref record | opened and confirmed |
| Stimberg et al. 2019, *eLife* 8, e47314; Todorov et al. 2012, IROS, 5026–5033 | README references | Crossref records | opened and confirmed |
| Hallem & Carlson 2006, *Cell* 125, 143–160, 10.1016/j.cell.2006.01.050 | REPORT §3.7 / references | Crossref record (bibliographic data only; the ORN spontaneous rates are taken through DoOR.data, not read from the paper) | bibliographic data confirmed; rates not checked against the paper |
| Münch & Galizia 2016, *Sci Rep* 6, 21841, 10.1038/srep21841; DoOR.data licence CC BY-SA 4.0 | README, THIRD_PARTY §2.2 | Crossref record; `DESCRIPTION` of ropensci/DoOR.data ("License: CC BY-SA 4.0", version 2.0.1.9001) | opened and confirmed |
| Hengstenberg 1988, *J Comp Physiol A* 163, 151–165, 10.1007/BF00612425, as the source of the head-reflex gains and latency | REPORT §2.3, README, THIRD_PARTY §6 | Crossref record; the paper could not be opened (publisher page requires a sign-in; one attempt on 2026-10-07) | bibliographic data confirmed; **value claim removed**: the constants are described as hand-set and the paper as related literature, not the source |
| Davis & Mongeau 2023, *PLoS Comput Biol* 19, e1011746, 10.1371/journal.pcbi.1011746 | README (related literature, "not the source of these constants") | Crossref record | opened and confirmed (bibliographic) |
| Eckstein et al. 2024, *Cell* 187, 2574–2594.e23, 10.1016/j.cell.2024.03.016 (transmitter predictions) | THIRD_PARTY | Crossref record | opened and confirmed (bibliographic) |
| Huang et al. 2010, *Neuron* 67, 1021–1033, for the lLN1_bc transmitter | THIRD_PARTY §2.3, §6, `data/README.md` | Crossref record (10.1016/j.neuron.2010.08.025) matches the volume and pages cited in `scripts/make_nt_literature.py`; paper not opened | bibliographic data confirmed; **value attribution removed** (listed for completeness, content not verified) |
| Fishilevich & Vosshall 2005, *Curr Biol* 15, 1548–1553, and Couto et al. 2005, *Curr Biol* 15, 1535–1547, as the sources of DoOR's receptor → glomerulus mapping | `scripts/make_orn_spontaneous.py`, THIRD_PARTY §6 | Crossref records (10.1016/j.cub.2005.07.066, 10.1016/j.cub.2005.07.034); the DoOR repository does not state the origin of the mapping | bibliographic data confirmed; **claim about DoOR removed** (mapping used as provided) |
| Tammero & Dickinson 2002; van Breugel & Dickinson 2012; Lin et al. 2014; Fry et al. 2003; Hedrick et al. 2009 as sources of hand-made parameters | THIRD_PARTY §6 | Crossref records of the listed DOIs (Tammero 2002, van Breugel 2012, Lin 2014, Fry 2003, Hedrick 2009 confirmed); content not opened | bibliographic data confirmed; the parameters are hand-set and the table lists these papers as related literature (content claims not verified, none relied on) |
| Bates et al. 2026, *Nature* 656, 957–970, 10.1038/s41586-026-10735-w; BANC data CC BY 4.0 | REPORT Related work | Crossref record; github.com/htem/BANC-project README | opened and confirmed |
| MANC papers (Takemura, Marin, Cheong; eLife 10.7554/eLife.97769, .97766, .96084) and MANC "licensed under CC-BY" | REPORT Related work | Crossref records; janelia.org MANC page | opened and confirmed |
| Male CNS v1.0, 8 June 2026, "licensed under CC-BY" | REPORT Related work | janelia.org male-CNS page | opened and confirmed; the accompanying paper could not be opened (HTTP 403) and is not cited |
| FlyWire public release (v783) is CC BY-NC 4.0; all data available in Codex for snapshot 783 is publicly released | README, NOTICE, THIRD_PARTY §2.1 | flywire.ai/guidelines (page text, opened 2026-10-07) | opened and confirmed (the page names no paper to cite) |
| Codex lists FAFB v783, BANC v888, MANC v1.2.1, MCNS v1.0; no data licence stated, refers to the FlyWire Terms of Service | REPORT Related work | codex.flywire.ai/api/download | opened and confirmed |
| Eon Systems page (10 March 2026): connectome, MuJoCo, hand-chosen mappings, VNC as further direction | REPORT Related work, README | eon.systems/updates/embodied-brain-emulation (verbatim sentences checked) | opened and confirmed |
| "NeuroFly was inspired by this demonstration" (Eon Systems) | README (earlier version) | NeuroFly README, section on inspiration (written in French): "directly inspired by the work of EON Systems PBC" | opened and confirmed (the sentence was replaced by the neutral Related work paragraph and is no longer in the README) |
| NeuroFly: FlyWire v783, Brian2 LIF, NeuroMechFly v2 / MuJoCo, no learning | REPORT Related work | github.com/seven-monarchs/NeuroFly | opened and confirmed |
| Uploading Lab pages and repository; Lulzx/fly-brain; Jin et al. arXiv:2602.17997; Pugliese et al. 10.1101/2025.09.12.675944; Guan et al. arXiv:2609.38665; Brunton et al. "digital sphinx" repository | REPORT Related work | the pages themselves (details in the table of that section) | opened and confirmed for the statements made; Uploading Lab repository licence and Lulzx licence file not verified |
| Upstream walking script behaviour (odour term, 80 Hz drive, 150 Hz ascending drive, 2,279 neurons) | REPORT §3.7 | `fly_brain_body_simulation.py` of this repository (upstream file); line hashes recomputed by `verify_report_final.py` | opened and confirmed (local file) |

Every claim that could not be confirmed (Hengstenberg, Huang, Fishilevich & Vosshall / Couto, the hand-parameter papers of THIRD_PARTY §6) has been removed as a value attribution; the papers remain only as bibliographic entries "not verified, listed for completeness" or as related literature. No row of this table is left as "not confirmed" without a stated consequence.

## 4. Text overlap with sources

`scripts/check_text_overlap.py` compared REPORT.md, README.md, THIRD_PARTY.md and NOTICE.md with 28 saved source texts (the pages and README files of section 3 and the Crossref abstracts of the cited papers). Longest identical word runs of 15 or more words found: only bibliographic reference strings (the same paper title, journal and DOI written in the same way), one quoted span that is an artefact of the check (two quotation marks of different sentences), a licence expression and a sentence of NOTICE.md. Quoted spans of Related work were shortened or rewritten in own words where they reached 15 words; the remaining quotations are short phrases and licence wording.
