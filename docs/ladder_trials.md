# Training ladder: trial ledger (SPEC_SENSORY_INPUTS §3.6)

Every trial of every arm is listed, in the order it was run, whatever its result (rule: "every trial that was run is counted and
reported"). Validation = starts 13-16, brain seed 100 + id. Champion = first trial of an arm with S1 in at least 3 of 4 validation
flights. Rows are appended by each later round; nothing is edited or removed. Raw readout files and flights are under `logs/ladder/`
(outside git); the hashes of the readout files are in `docs/ladder/trial<n>_readouts.json`.

| arm | trial | training data | λ per command (turn / thrust / pitch / roll) | validation S1 | champion | readout file SHA-256 (first 16) | commit of the result |
|---|---|---|---|---|---|---|---|
| T1-real | 1 | 12 teacher flights (starts 1-12), 1,412 wings-on samples | 1000 / 1000 / 1000 / 1000 | 0/4 | no | `7d896a7911e55df9` | `3c1b0fa` (REPORT.md §3.9b) |
| T1-shuffled | 1 | 12 teacher flights (starts 1-12), 1,412 wings-on samples; DN counts from the replay into the shuffled connectome (seed 901) | 1000 / 1000 / 1000 / 1000 | 0/4 | no | `b5392607296a9e2d` | `3c1b0fa` (REPORT.md §3.9b) |
| T1-bypass | 1 | 12 teacher flights (starts 1-12), 1,412 wings-on samples; fixed random projection of the boundary-layer rates (seed 902) | 1000 / 1000 / 1000 / 1000 | 0/4 | no | `d75df57183b29cee` | `3c1b0fa` (REPORT.md §3.9b) |

Status after trial 1: no arm has a champion. Trials 2-4 (correction rounds with the teacher label of the visited states) have not been run.
No exam start (17-22) has been used.

Closing line (2026-10-07): step 1 stopped after trial 1 by a decision taken after the trial-1 results were known; this is a deviation from the pre-registration (stopping for futility was not a pre-registered rule; SPEC_SENSORY_INPUTS §3.6, note of 2026-10-07). T1 not completed: no champion in trial 1 (S1 0/4 in all three arms); trials 2–4 and the exam were not run. No row is added for trials 2–4 because none was run.
