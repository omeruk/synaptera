# scripts/diag — brain-control diagnosis (R0–R3)

Source of the numbers in the diagnosis section of `SPEC_BRAIN_CONTROL.md`. All runs use the full brain (v783), the set-up of `brain_model/model.py`; the LIF parameters are unchanged.
Outputs (log/npz/csv) are written to the current directory and are not put into the repository. To run, change to an output directory and:

```bash
PY="env -u PYTHONPATH $HOME/miniforge3/envs/neurofly/bin/python"
D=scripts/diag   # path to this directory, from the repository root
bash $D/r0_all.sh                        # R0: sugar GRN -> MN9 (v630 + v783, ~15 min, 2 in parallel)
$PY $D/r0_sugar.py 783 shiu 100 5        # one condition: <630|783> <shiu|flight|sezgroup> <Hz> <trials>
$PY $D/r1_persist.py                     # R1: persistent activity after the input is cut -> r1_persist_mask.npy
$PY $D/r2_anat.py                        # R2: source -> DN hops + signed propagation -> r2_src_dn.csv
$PY $D/r2_extra.py dng02|kc|excprop      # R2: DNg02 inputs / KC core / excitatory propagation
$PY $D/r3_open.py all 0                  # R3: open-loop stimulation, every condition net.restore('fresh') -> r3_counts_all_s0.npz
$PY $D/r3_analyze.py r3_counts_all_s0.npz
$PY $D/r3_dng02.py                       # R3b: can DNg02 be excited?
```

`r3_open_v1_contaminated.py` is kept as a record only: it reset only v/g between conditions, so a persistent state was carried over; its result is not used.
Memory: every full-brain process needs ~2–3 GB; run at most 2 at a time.

## Step 0 (input revision) criteria

```bash
$PY $D/a0_visual.py                        # textured arena + FlyVis -> per-neuron T4/T5 rate arrays -> a0_visual_rates.npz (~5 min)
$PY $D/a0_criteria.py                      # full brain: R3 matrix (new inputs) + input cut-off + symmetry -> a0_counts_s0.npz
$PY $D/a0_criteria.py --asc                # ascending (legacy AN group) conditions -> a0_counts_asc_s0.npz
$PY $D/a0_criteria.py --report a0_counts_s0.npz a0_counts_asc_s0.npz   # tables (a)(b)(c)
```
Input data generation (once; outputs in `data/`): `scripts/make_sugar_grn.py`, `scripts/make_t45_transduction.py`.
`r1_persist.py` now uses `FlightBrain(inputs='legacy')`, i.e. the Stage 4 inputs (the R1 numbers belong to those inputs).

## Step 0 decisions (APL, symmetry, Codex)

```bash
$PY $D/a0_apl_gain.py                      # graded APL gain: KC sparseness scan (food odour 150 Hz) -> a0_apl_gain.json (~4 min)
$PY $D/a0_criteria.py --apl-graded --vis-dir <directory of a0_visual_rates.npz>        # -> a0_counts_apl_s0.npz
$PY $D/a0_criteria.py --apl-graded --asc --vis-dir <...>                          # -> a0_counts_asc_apl_s0.npz
$PY $D/a0_criteria.py --report a0_counts_apl_s0.npz a0_counts_asc_apl_s0.npz
$PY $D/a0_symmetry.py                      # mirror-symmetric grating: normal / eye swap / unmapped -> DN and LPTC L/R (~2 min)
$PY $D/a0_codex.py --persist-npz a0_counts_s0.npz   # Codex v783 cross-check (~/Downloads; root_id, NT, neuropil, T4/T5->LPTC->DN, L/R counts)
```

## Step 0 decisions II (NT sign test, `--nt-modulatory-silent`)

```bash
$PY scripts/make_nt_silent.py      # data/nt_modulatory_silent_783.csv (from ~/Downloads/neurons.csv.gz, once)
$PY $D/a0_criteria.py --nt-silent broad  --vis-dir <...>          # -> a0_counts_ntsB_s0.npz
$PY $D/a0_criteria.py --nt-silent broad  --apl-graded --vis-dir <...>   # -> a0_counts_apl_ntsB_s0.npz
$PY $D/a0_criteria.py --nt-silent narrow --vis-dir <...>          # -> a0_counts_ntsN_s0.npz (+ --apl-graded)
$PY $D/a0_criteria.py --report a0_counts_ntsB_s0.npz               # (a)(b)(c)
```

## Step 1 (feeding)

```bash
$PY $D/a1_mn9.py --vis-dir <directory of a0_visual_rates.npz>      # open-loop MN9: sugar × visual baseline, 3 seeds (~6 min)
cd <repository root>; P="env -u PYTHONPATH MUJOCO_GL=egl $PY fly_flight_brain_body_simulation.py --no-olfaction --no-video --n-steps 40"
$P --start-on-platform --seed 0            # contact; + --ablate-mn9; take-off from the pedestal = no-contact control
$PY $D/a1_closed.py simulations/flight_v*_onPlat_data.h5 ...   # MN9 / extension / contact summary
```

## Step 2 (visual direction)

```bash
$PY scripts/make_dn_reference.py    # data/dn_lr_reference.json (sym_prog, 3 seeds; once)
$PY $D/a2_visual.py                         # synthetic yaw + platform azimuth (dark/neutral) T4/T5 arrays -> a2_visual_rates.npz (~5 min)
$PY $D/a2_openloop.py --vis-dir <directory of a0_visual_rates.npz> --vis2-dir <directory of a2_visual_rates.npz>   # 3 seeds (~12 min)
$PY $D/a2_openloop.py --report a2_openloop_s0.npz a2_openloop_s1.npz a2_openloop_s2.npz
P="env -u PYTHONPATH MUJOCO_GL=egl $PY fly_flight_brain_body_simulation.py --no-olfaction --no-video"
$P --n-steps 60 --seed 0 --tag tower [--ablate-dn | --swap-dn-lr]                          # (b) tower
$P --n-steps 40 --seed 0 --tag plat --spawn-air 440 -170 160 60 [--platform-neutral | --ablate-dn]   # (e) azimuth +30 (120: azimuth -30)
$PY $D/a2_closed.py simulations/flight_v*_tower_data.h5 simulations/flight_v*_plat_data.h5
```

## Step 2 decisions (DNp15 readout, post-hoc; validation seeds 3/4/5)

```bash
$PY $D/a2_openloop.py --vis-dir <directory of a0_visual_rates.npz> --vis2-dir <directory of a2_visual_rates.npz> --seeds 3 4 5
$PY $D/a2_openloop.py --report a2_openloop_s3.npz a2_openloop_s4.npz a2_openloop_s5.npz   # (a) and (c) summary line
P="env -u PYTHONPATH MUJOCO_GL=egl $PY fly_flight_brain_body_simulation.py --no-olfaction --no-video"
$P --n-steps 60 --seed 3 --tag pert --spawn-air 440 -170 160 90 --hover --yaw-perturb 0.5 30 [--ablate-dn]   # (b), ±30
$PY $D/a2b_perturb.py simulations/flight_v*_pert_data.h5                                   # b1/b2/b3
# (d): the tower / platform commands of Step 2, --seed 3|4|5, normal and --ablate-dn; summary a2_closed.py
```
