# Pre-registration log

**What "pre-registered" means in this project:** the criteria and the decision rule were written into a
`SPEC_*.md` file and **committed to the git repository before the runs** they judge. They were **not**
registered on an external registry (e.g. OSF). Git commit timestamps are set by the author's machine and can
be rewritten; they are **not independent evidence** of timing. This log only makes the claimed order
checkable against the repository history and the run logs.

**Note on hashes:** the commit hashes below belong to the author's private development repository (which
also contains the upstream NeuroFly history). They are not present in the public snapshot and are available
on request.

Times are local time (UTC+03:00). Sources for run start times:
- **run log** = the `start` line written by the run script (`logs/<dir>/run_*.out`) or a file timestamp in
  `logs/`, as noted; `logs/` is not tracked in git;
- **session log** = timestamp of the tool call that launched the run, in the local Claude Code session
  transcripts (`~/.claude/projects/…/*.jsonl`), used where the run script wrote no start line (runs whose
  logs were written to a temporary directory). These transcripts are not part of the repository.

## Summary

| # | pre-registration (SPEC section) | criteria commit | commit time | first criterion run started | source | result commit(s) | order |
|---|---|---|---|---|---|---|---|
| 1 | SPEC_BRAIN_CONTROL "Step 2 decisions" (DNp15 readout validation, seeds 3/4/5) | `38a2590` | 2026-09-30 15:23:58 | open loop 2026-09-30 15:31:51; closed loop 15:32:37 | session log | `3f66504` (17:22:59), `253e6da` (17:26:28) | criteria → runs |
| 2 | SPEC_BRAIN_CONTROL "Honest hybrid final" (final-v1: final_a/b/c, success S1 ∧ S2, brain-share measure) | `8cc3975` | 2026-09-30 18:30:00 | smoke 18:30:07; final_a 18:51:40 | session log; run log `logs/final/run_final.out` | `bc6f113` (19:55:19, REPORT_FINAL.md) | criteria → runs |
| 3 | SPEC_SENSORY_INPUTS §3.3b (Stage B: B-K1..K4, K6) | `e997650` | 2026-10-01 18:25:09 | smoke_sB 18:24:37; final_sB 18:27:41 | session log | `7a9f78a` (smoke), `afcae4c` (18:35:03, REPORT_SENSORY_B.md) | **smoke started 32 s before the commit** (note #3); full run after |
| 4 | SPEC_SENSORY_INPUTS §3.2b (Stage A: (i)–(iii), K1, smoke B-K1..K4, main-line decision) | `773b8ae` | 2026-10-01 19:02:10 | open loop 19:02:16; smokes v17/v18 19:05:24; full run v19 19:19:34 | session log | `fe3a184` (19:19:29), `3b55cd5` (20:15:49, REPORT_SENSORY_A.md) | criteria → runs |
| 5 | SPEC_SENSORY_INPUTS §3.2c (Stage A2: `--nt-literature` rule, FS/FG/BS/BG matrix, decision) | `58c9c17` | 2026-10-01 20:33:07 | test matrix 20:41:38 | session log | `39e292e` (20:52:50), `5ed12ad` (20:53:23) | criteria → runs |
| 6 | SPEC_SENSORY_INPUTS §3.3c (final-v2: DNp15 validation, seeds 6/7/8, decision rule; final runs) | `5aefc83` | 2026-10-02 00:08:49 | closed loop (b) 00:09:00; open loop (a)/(c) 00:31:07; final_v2a 00:38:30 | run log (`logs/v2/val/run_b.pid` mtime; `logs/final_v2/run_final_v2.out`); session log | `79a6499` (00:38:26, validation), `8978d41` (00:52:16, runs), `7de93f2` (01:01:21, REPORT_FINAL_V2.md) | criteria → criterion runs; **stimulus preparation started before the commit** (note #6) |
| 7 | SPEC_SENSORY_INPUTS §3.3d (n1/n2: S1, S2, B-K1/K3/K4, head reflex B-H1..H3; head-reflex constants) | `65f05bd` (constants: `e38d96b`, 01:29:06; postures `68bbcfb`, 01:34:08) | 2026-10-02 01:34:32 | smoke 01:41:52; n1 01:44:05 | session log; run log `logs/natural/run_natural.out` | `16f4e45` (02:09:11) | criteria → runs. `--no-brain-steer` itself is a **post-hoc** control (added after final_v2a's result, `1bd0730`) |
| 8 | SPEC_SENSORY_INPUTS §3.3e (multi-seed repeat, seeds 10–14) | `1b48395` | 2026-10-02 16:50:58 | n1_s10 16:51:11 | run log `logs/seeds/run_seeds.out` | `ca32d52` (2026-10-04 23:28:18) | criteria → runs |
| 9 | SPEC_SENSORY_INPUTS §3.3f (start position / heading test, 8 conditions) | `256d072` | 2026-10-05 00:12:30 | st_xp40 00:12:30 | run log `logs/starts/run_starts.out`; session log (commit and launch in one command, commit first) | `eedf653` (01:16:17) | criteria → runs (same second; order from the command sequence) |
| 10 | SPEC_SENSORY_INPUTS §3.4a (smell circuit part 1/4: step-0 anatomy, O1 criteria and stopping rule, O2 criteria) | `5b82f84` | 2026-10-05 23:24:51 | smoke (8 steps) ended 23:25:31; O1 (40 runs) started between 23:25:31 and 23:26:00 (first run file 23:26:20) | file timestamps in `logs/smell/` (`DONE_O1` 23:39:23); session log | `9ebaf76` (23:39:38) | criteria → runs |
| 11 | SPEC_SENSORY_INPUTS §3.4b (smell circuit part 2/4: NT audit, MODEL VARIANTS N1/N2, O1 under the variants, decision rule, O2 + null control, robustness records) | `ef6c3ff` | 2026-10-06 09:01:32 | N1 O1 09:01:54; N2 O1 09:15:09; robustness 09:28:52 | run log (`START_O1`, `logs/smell/o1_nt.log`, `logs/smell/robust/START_ROBUST`; the run scripts wrote their start times) | `90febc3` | criteria → runs |
| 12 | SPEC_SENSORY_INPUTS §3.4c (smell circuit comparison check: upstream NeuroFly-style olfactory drive, 2,279 neurons at 80 Hz, published model, open loop, seeds 701–705) | `cde230e` (wording fix `4f70813`, before any run) | 2026-10-06 09:52:55 | smoke 09:53:31 (one run, seed 701, 8+8 steps, temporary directory); O1-style runs 2026-10-06 09:54:17 (`logs/smell/o1_nf/START_NF`, written by the run script; 5 runs, finished by 09:56) | run log (`START_NF`, `logs/smell/o1_nf.log`) | `6a66cd6` | criteria → runs |
| 13 | SPEC_SENSORY_INPUTS §3.5 (vision screen part 3/3: which DN clusters separate which visual stimulus; 10 open-loop conditions, a-priori H1–H4 = 21 tests, exploratory screen, shuffled-connectome null; published model, seeds 501–503 / 601–605 / 801–805) | `3619bc6` | 2026-10-06 10:30:24 | render 2026-10-06 10:40:22 (input check passed); discovery runs 10:42:37; validation 10:52:21; null 11:07:11 (125 runs, all finished 11:20:35) | run log (`START_*` markers and `logs/vis_dn/*.log`; the run scripts wrote their start times) | `32b667b` | criteria → code → runs |
| 14 | SPEC_SENSORY_INPUTS §3.5b (vision screen follow-up: loom response in a collision-locked window W_loom 700–900 ms vs receding W_rec 100–300 ms, onset control W_on 0–200 ms; 20 a-priori tests R/S/Rfront, exploratory R/Rfront; published model, seeds 511–513 / 611–615 / 811–815). **Follow-up designed after the §3.8 results were known; new window, new seeds.** | `f10b870` | 2026-10-06 16:27:19 | render 2026-10-06 16:38:03 (input check passed); discovery 16:39:47; validation 16:46:09; null 16:56:33 (86 runs, finished 17:05:31) | run log (`START_*` markers in `logs/vis_loom/`) | `372d159` | criteria → code → render/input check → runs (the render start line and the code commit `c37431d` carry the same second, 16:38:03; the commit was issued first in the same command) |
| 15 | SPEC_SENSORY_INPUTS §3.6 (training ladder step 1, all three rounds: TRAINED READOUT (brain unchanged) in place of the four hand-made route commands; arms T1-real / T1-shuffled (seed 901) / T1-bypass (seed 902); 22 starts drawn with seed 20261006 (12 train, 4 validation, 6 exam); ridge on filtered DN activity, leave-one-flight-out λ, ≤ 4 trials with DAgger correction, champion rule, one exam on 6 untouched starts; pass: T1-real ≥ 5/6 and ≥ 3 flights above the best control) | `bc94557` | 2026-10-06 17:49:24 | smoke (20 steps, default start) 2026-10-06 ~17:56; teacher flights lt01 18:00:49 … lt16 end 19:42:02 (16 flights, round 1); round 2: replay audit 2026-10-06 22:43:46, shuffled replays 22:45 … 23:14:10, fit 23:14:10, trial-1 validation flights 23:14:42 … 2026-10-07 00:25:09 (12 flights) | run log (`logs/ladder/teacher/run.out`, `DONE_*`) | `3d05799` (round 1: teacher flights); `17ff927` (round 2: readouts fitted), `3c1b0fa` (round 2: trial-1 validation flights; later rounds pending) | criteria → code → runs |

## Notes

- **#1 (Step 2 decisions).** The decision text and criteria were written in the SPEC at 15:23:47–15:23:57
  (session log) and committed at 15:23:58. The validation runs were written to a temporary directory; their
  start times come from the session log only.
- **#2 (final-v1).** The smoke runs (20 steps) checked the run script, not the criteria; the three final runs
  were started by `run_final.sh` (start lines in the run log).
- **#3 (Stage B).** The criteria were written into the SPEC in the working tree at 18:21:07 (session log), the
  20-step smoke `smoke_sB` was launched at 18:24:37 and the commit was made at 18:25:09, while the smoke was
  still running (it finished at 18:27:30, file time of `logs/sB/smoke_sB.log`). By commit time, the smoke
  started **before** the criteria were committed. The full run `final_sB` started at 18:27:41, after the commit.
- **#4, #5.** Run logs were written to temporary directories; start times from the session log.
- **#6 (final-v2 validation).** `a2_visual.py --vision-boundary` (launched 00:00:16) and
  `a0_visual.py --vision-boundary` (launched 00:08:44, 5 s before the commit) only compute the FlyVis
  boundary-layer input rates of the stimulus sequences; they do not run the brain and produce no DN readout
  (`logs/v2/val/a2_visual_vb.log`, `a0_visual_vb.log`). The runs that measure the criteria (the 12 closed-loop
  runs of `run_b.sh`, started 00:09:00; `a2_openloop.py --seeds 6 7 8`, started 00:31:07) started after the
  commit. The DNp15 re-calibration (`1a551b1`, 00:08:45) is the method step that the criteria refer to; it
  precedes them by design.
- **#7.** The head-reflex constants were committed at 01:29:06 (`e38d96b`) before the n1/n2 runs; see the
  correction note of 2026-10-05 in SPEC §3.3d about their source.
- **#9.** `976812a` (flags) and `256d072` (criteria) have the same timestamp as the first run start; the session
  log shows one shell command that committed both and then launched `run_starts.sh`.
- **#10 (smell circuit part 1/4).** Step 0 (anatomy) is not a simulation: it was run at 23:23:06, before the
  criteria commit, and its results are part of the pre-registration. The 8-step smoke (one run, 200 Hz, seed 101,
  written to a temporary directory) checked the script; the 40 O1 runs started after the commit. The O1 script
  `scripts/diag/so_o1.py` was written after the criteria commit (SPEC §3.4a says so) and committed with the results
  (`9ebaf76`). The stopping rule fired (0 of 8 rates pass), so the O2 runs, whose criteria are in the same section,
  were not made. The exact O1 start time was not logged (the run script writes no start line); only the bounds
  above are known. The O2 (iii) reading (both sides 0 Hz in the no-input condition = pass) and the exploratory-sweep
  wording are interpretations written into the SPEC before any data; the SPEC states both.
  After the result commit, one **post-hoc exploratory diagnostic run** (O1 at 10 Hz, seed 101, per-neuron spike counts,
  `scripts/diag/so_o1_diag.py`) was made at the user's request; it is not pre-registered, is labelled as such in
  REPORT.md §3.7, and no criterion or decision depends on it.
- **#11 (smell circuit part 2/4).** The step-0 audit and the table of changes (`scripts/diag/nt_audit.py`,
  `scripts/make_nt_impute.py`, `--nt-impute` and its tests) are not simulations and were committed together with the
  pre-registration (`ef6c3ff`). Two 8-step smokes (one run each, N1 and N2, 200 Hz, seed 101, temporary directory) ran
  after that commit and before the 80 O1 runs; the O1 runs (`scripts/diag/run_o1_nt.sh`; the script writes its start time) and the
  robustness records started after it. The O2, null-control and robustness scripts and the shuffled-connectome option were
  committed after the O1 runs (`795bf01`); the O2 criteria themselves are the ones of §3.4a and the null-control definition is in
  §3.4b, both committed before. Neither variant passed O1 (0 of 8 rates each), so the decision rule gave "O2 not run" and no O2 or null run
  exists. The robustness records ran on N1, N2 and the published model (rule: both variants when none is selected). One
  interpretation was fixed before the runs and is written in §3.4b: peers vote with their predicted transmitter, not with their model sign.

- **#12 (smell circuit comparison check).** Step 0 (reading the upstream script, plus counting its regex matches in the annotation table) is not a simulation and was committed with the pre-registration. The task asked for three drive levels from the upstream script; the script has one olfactory rate (80 Hz), so the pre-registration fixed one level and 5 runs (written in §3.4c before any run, with the reason). The run script `scripts/diag/so_o1_nf.py` was written after the criteria commit and committed before the runs (one 8+8-step smoke of one run was made first, in a temporary directory, and it was not used for any result). The result does not change the odour decision (written in §3.4c).
- **#14 (vision follow-up, loom in a collision-locked window).** Designed after the §3.8 results (including the post-hoc looks on the last 200 ms and the DNp04 frontal response) were known; this is stated in SPEC §3.5b Step 0(a) and is not an independent pre-registration of a hypothesis. What was fixed before any run: windows, measures, thresholds, seeds, input-check rule, pass rule. The §3.5 results are unchanged. Order: SPEC `f10b870` → generator change (condition 11), tests, scripts (`vl_render.py`, `vl_run.py`, `vl_report.py`) → render of receding-front and input check → runs. The test suite run at this stage (`tests/`: 142 passed, 10 skipped) used no neural data of this follow-up.
- **#15 (training ladder, step 1).** Round 1/3 covers Step 0–3 of §3.6: pre-registration, this row, the recording option and the 16 teacher flights (starts 1–16). Training, correction rounds, validation trials and the exam are later rounds. Exam starts 17–22 are not run before the exam day. Round 2 (trial 1): the clarifications (SPEC §3.6, `7933359`) and the code (`1dacbae`, run scripts `053d610`) were committed before the audit, the replays, the fit and the validation flights; result: 0 of 12 validation flights reach touchdown, no champion; correction rounds (trials 2–4) and the exam are later rounds. Interpretation fixed in the SPEC before any run: the phase machine (including the position-reading approach/descend/touchdown triggers) stays hand-made in all arms. **Stopped after trial 1; deviation from the pre-registration (2026-10-07):** the correction rounds (trials 2–4) and the exam were not run, by a decision taken after the trial-1 results were known; stopping for futility was not a pre-registered rule (SPEC §3.6, note of 2026-10-07). Verdict: T1 not completed: no champion in trial 1 (S1 0/4 in all three arms); trials 2–4 and the exam were not run. Exam starts 17–22 were never used.

## Rules written before measurement but committed together with results

These SPEC sections state that the rule was fixed before the measurement, but the rule and the result are in the
same commit, so the repository gives no ordering evidence for them:

| SPEC section | commit | time |
|---|---|---|
| SPEC_BRAIN_CONTROL R2 "pre-specified readout sets" | `da99529` | 2026-09-29 15:42:45 |
| SPEC_BRAIN_CONTROL "Step 0 decisions II" (NT sign test rules) | `54b8760` | 2026-09-30 14:00:10 |
