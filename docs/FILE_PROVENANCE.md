# File provenance

Generated from git on 2026-10-05 (branch `sensory-inputs`). Upstream = NeuroFly ([seven-monarchs/NeuroFly](https://github.com/seven-monarchs/NeuroFly), `origin/main` = `b59264a`, commits `1a376da`–`b59264a`, 2026-03-25 – 2026-04-05, author "Monarch"). Everything after `b59264a` was committed in this work. See [THIRD_PARTY.md](../THIRD_PARTY.md) for licences.

Commands: `git ls-tree -r --name-only b59264a` (upstream files), `git diff --name-status -M b59264a HEAD` (status in HEAD), `git ls-files` minus the upstream list (files of this work).

## A. Files inherited from the upstream repository (445)

Status = state in HEAD relative to `b59264a`. "added in" = upstream commit that added the file.

| file | added in | status in HEAD |
|---|---|---|
| `.dockerignore` | 67e58df | unchanged |
| `.gitignore` | 1a376da | modified (cffe0d7) |
| `Dockerfile` | 67e58df | unchanged |
| `README.en.md` | c101a20 | renamed → `docs/neurofly_upstream/README.en.md` (97% similar) |
| `README.md` | 1a376da | replaced by the Synaptera README (28ee205, eedf653, a5cb1c0); upstream text kept in `docs/neurofly_upstream/README.fr.md` |
| `brain_model/.gitignore` | 1a376da | unchanged |
| `brain_model/2023_03_23_completeness_630_final.csv` | 1a376da | unchanged |
| `brain_model/2023_03_23_connectivity_630_final.parquet` | 1a376da | unchanged |
| `brain_model/Completeness_783.csv` | 1a376da | unchanged |
| `brain_model/Connectivity_783.parquet` | 1a376da | unchanged |
| `brain_model/LICENSE` | 1a376da | unchanged |
| `brain_model/Readme.md` | 1a376da | unchanged |
| `brain_model/descending_neurons.csv` | 1a376da | unchanged |
| `brain_model/environment.yml` | 1a376da | unchanged |
| `brain_model/environment_full.yml` | 1a376da | unchanged |
| `brain_model/example.ipynb` | 1a376da | unchanged |
| `brain_model/figures.ipynb` | 1a376da | unchanged |
| `brain_model/flywire_annotations.tsv` | 1a376da | unchanged |
| `brain_model/model.py` | 1a376da | unchanged |
| `brain_model/results/example/sugarR-720575940617937543.parquet` | 1a376da | unchanged |
| `brain_model/results/example/sugarR-720575940621754367.parquet` | 1a376da | unchanged |
| `brain_model/results/example/sugarR-720575940622695448.parquet` | 1a376da | unchanged |
| `brain_model/results/example/sugarR.parquet` | 1a376da | unchanged |
| `brain_model/results/example/sugarR_100Hz.parquet` | 1a376da | unchanged |
| `brain_model/sez_neurons.pickle` | 1a376da | unchanged |
| `brain_model/utils.py` | 1a376da | unchanged |
| `fly_brain_body_simulation.py` | c101a20 | modified (86ea1fc) |
| `fruitfly/assets/drosophila.xml` | 1a376da | unchanged |
| `fruitfly/assets/drosophila_defaults.xml` | 1a376da | unchanged |
| `fruitfly/assets/drosophila_fused.xml` | 1a376da | unchanged |
| `fruitfly/assets/floor.xml` | 1a376da | unchanged |
| `fruitfly/assets/fruitfly.xml` | 1a376da | unchanged |
| `generate_plots.py` | 8a0d6e9 | unchanged |
| `plots/v33/EN/01_circuit_timeline.png` | 8a0d6e9 | unchanged |
| `plots/v33/EN/02_raster_circuits.png` | 8a0d6e9 | unchanged |
| `plots/v33/EN/03_dn_turning_coupling.png` | 8a0d6e9 | unchanged |
| `plots/v33/EN/04_brain_body_coupling.png` | 8a0d6e9 | unchanged |
| `plots/v33/EN/05_population_heatmap.png` | 8a0d6e9 | unchanged |
| `plots/v33/EN/06_firing_rate_distribution.png` | 8a0d6e9 | unchanged |
| `plots/v33/EN/07_odor_olfactory_response.png` | 8a0d6e9 | unchanged |
| `plots/v33/FR/01_circuit_timeline.png` | 8a0d6e9 | unchanged |
| `plots/v33/FR/02_raster_circuits.png` | 8a0d6e9 | unchanged |
| `plots/v33/FR/03_dn_turning_coupling.png` | 8a0d6e9 | unchanged |
| `plots/v33/FR/04_brain_body_coupling.png` | 8a0d6e9 | unchanged |
| `plots/v33/FR/05_population_heatmap.png` | 8a0d6e9 | unchanged |
| `plots/v33/FR/06_firing_rate_distribution.png` | 8a0d6e9 | unchanged |
| `plots/v33/FR/07_odor_olfactory_response.png` | 8a0d6e9 | unchanged |
| `plots/v42/EN/01_circuit_timeline.png` | 2a50708 | unchanged |
| `plots/v42/EN/02_raster_circuits.png` | 2a50708 | unchanged |
| `plots/v42/EN/03_dn_turning_coupling.png` | 2a50708 | unchanged |
| `plots/v42/EN/04_brain_body_coupling.png` | 2a50708 | unchanged |
| `plots/v42/EN/05_population_heatmap.png` | 2a50708 | unchanged |
| `plots/v42/EN/06_firing_rate_distribution.png` | 2a50708 | unchanged |
| `plots/v42/EN/07_odor_olfactory_response.png` | 2a50708 | unchanged |
| `plots/v42/EN/08_visual_lamina_response.png` | 2a50708 | unchanged |
| `plots/v42/EN/09_trajectory.png` | 2a50708 | unchanged |
| `plots/v42/EN/10_looming_reflex.png` | 2a50708 | unchanged |
| `plots/v42/EN/11_odor_asymmetry.png` | 2a50708 | unchanged |
| `plots/v42/EN/12_odor_field_trajectory.png` | 2a50708 | unchanged |
| `plots/v42/EN/13_odor_movement_correlation.png` | 2a50708 | unchanged |
| `plots/v42/FR/01_circuit_timeline.png` | 2a50708 | unchanged |
| `plots/v42/FR/02_raster_circuits.png` | 2a50708 | unchanged |
| `plots/v42/FR/03_dn_turning_coupling.png` | 2a50708 | unchanged |
| `plots/v42/FR/04_brain_body_coupling.png` | 2a50708 | unchanged |
| `plots/v42/FR/05_population_heatmap.png` | 2a50708 | unchanged |
| `plots/v42/FR/06_firing_rate_distribution.png` | 2a50708 | unchanged |
| `plots/v42/FR/07_odor_olfactory_response.png` | 2a50708 | unchanged |
| `plots/v42/FR/08_visual_lamina_response.png` | 2a50708 | unchanged |
| `plots/v42/FR/09_trajectory.png` | 2a50708 | unchanged |
| `plots/v42/FR/10_looming_reflex.png` | 2a50708 | unchanged |
| `plots/v42/FR/11_odor_asymmetry.png` | 2a50708 | unchanged |
| `plots/v42/FR/12_odor_field_trajectory.png` | 2a50708 | unchanged |
| `plots/v42/FR/13_odor_movement_correlation.png` | 2a50708 | unchanged |
| `requirements.txt` | c101a20 | unchanged |
| `run.bat` | c101a20 | unchanged |
| `simulation_data/README.en.md` | 2a50708 | unchanged |
| `simulation_data/README.fr.md` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/000/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/000/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/000/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/000/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/000/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/001/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/001/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/001/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/001/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/001/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/002/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/002/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/002/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/002/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/002/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/003/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/003/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/003/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/003/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/003/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/004/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/004/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/004/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/004/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/004/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/005/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/005/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/005/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/005/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/005/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/006/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/006/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/006/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/006/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/006/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/007/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/007/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/007/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/007/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/007/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/008/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/008/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/008/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/008/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/008/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/009/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/009/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/009/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/009/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/009/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/010/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/010/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/010/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/010/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/010/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/011/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/011/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/011/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/011/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/011/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/012/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/012/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/012/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/012/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/012/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/013/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/013/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/013/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/013/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/013/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/014/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/014/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/014/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/014/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/014/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/015/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/015/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/015/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/015/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/015/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/016/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/016/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/016/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/016/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/016/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/017/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/017/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/017/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/017/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/017/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/018/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/018/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/018/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/018/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/018/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/019/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/019/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/019/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/019/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/019/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/020/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/020/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/020/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/020/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/020/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/021/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/021/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/021/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/021/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/021/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/022/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/022/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/022/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/022/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/022/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/023/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/023/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/023/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/023/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/023/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/024/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/024/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/024/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/024/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/024/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/025/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/025/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/025/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/025/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/025/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/026/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/026/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/026/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/026/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/026/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/027/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/027/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/027/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/027/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/027/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/028/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/028/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/028/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/028/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/028/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/029/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/029/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/029/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/029/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/029/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/030/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/030/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/030/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/030/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/030/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/031/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/031/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/031/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/031/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/031/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/032/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/032/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/032/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/032/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/032/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/033/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/033/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/033/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/033/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/033/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/034/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/034/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/034/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/034/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/034/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/035/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/035/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/035/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/035/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/035/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/036/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/036/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/036/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/036/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/036/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/037/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/037/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/037/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/037/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/037/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/038/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/038/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/038/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/038/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/038/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/039/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/039/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/039/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/039/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/039/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/040/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/040/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/040/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/040/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/040/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/041/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/041/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/041/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/041/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/041/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/042/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/042/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/042/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/042/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/042/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/043/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/043/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/043/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/043/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/043/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/044/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/044/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/044/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/044/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/044/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/045/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/045/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/045/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/045/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/045/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/046/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/046/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/046/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/046/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/046/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/047/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/047/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/047/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/047/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/047/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/048/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/048/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/048/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/048/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/048/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/049/_meta.yaml` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/049/best_chkpt` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/049/chkpts/chkpt_00000` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/049/validation/loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/049/validation_loss.h5` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Am.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/C2.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/C3.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/CT1(Lo1).pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/CT1(M10).pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/L1.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/L2.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/L3.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/L4.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/L5.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Lawf1.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Lawf2.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi1.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi10.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi11.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi12.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi13.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi14.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi15.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi2.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi3.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi4.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Mi9.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/R1.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/R2.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/R3.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/R4.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/R5.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/R6.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/R7.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/R8.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T1.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T2.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T2a.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T3.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T4a.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T4b.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T4c.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T4d.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T5a.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T5b.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T5c.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/T5d.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm1.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm16.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm2.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm20.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm28.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm3.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm30.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm4.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm5Y.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm5a.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm5b.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm5c.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/Tm9.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/TmY10.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/TmY13.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/TmY14.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/TmY15.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/TmY18.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/TmY3.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/TmY4.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/TmY5a.pickle` | 2a50708 | unchanged |
| `simulation_data/flyvis_pretrained_weights/0000/umap_and_clustering/TmY9.pickle` | 2a50708 | unchanged |
| `simulation_data/flywire_connectome_v783/Completeness_783.csv` | 2a50708 | unchanged |
| `simulation_data/flywire_connectome_v783/Connectivity_783.parquet` | 2a50708 | unchanged |
| `simulation_data/flywire_connectome_v783/descending_neurons.csv` | 2a50708 | unchanged |
| `simulation_data/flywire_connectome_v783/flywire_annotations.tsv` | 2a50708 | unchanged |
| `simulations/demo.mp4` | 8a0d6e9 | unchanged |
| `simulations/preview.gif` | c101a20 | unchanged |
| `simulations/preview2.gif` | 2a50708 | unchanged |
| `simulations/v10_brain_body_flygym_odor.mp4` | 26e1970 | unchanged |
| `simulations/v11_brain_body_flygym_odor.mp4` | 26e1970 | unchanged |
| `simulations/v1_wing_animation.mp4` | 26e1970 | unchanged |
| `simulations/v2_walk_random_policy.mp4` | 26e1970 | unchanged |
| `simulations/v33_data.h5` | 8a0d6e9 | unchanged |
| `simulations/v34_data.h5` | 2a50708 | unchanged |
| `simulations/v35_data.h5` | 2a50708 | unchanged |
| `simulations/v36_data.h5` | 2a50708 | unchanged |
| `simulations/v37_data.h5` | 2a50708 | unchanged |
| `simulations/v38_data.h5` | 2a50708 | unchanged |
| `simulations/v39_data.h5` | 2a50708 | unchanged |
| `simulations/v3_brain_body_walk_on_ball.mp4` | 26e1970 | unchanged |
| `simulations/v40_data.h5` | 2a50708 | unchanged |
| `simulations/v41_data.h5` | 2a50708 | unchanged |
| `simulations/v42_data.h5` | 2a50708 | unchanged |
| `simulations/v4_brain_body_tripod_gait.mp4` | 26e1970 | unchanged |
| `simulations/v5_brain_body_tripod_gait.mp4` | 26e1970 | unchanged |
| `simulations/v6_brain_body_flygym_odor.mp4` | 26e1970 | unchanged |
| `simulations/v7_brain_body_flygym_odor.mp4` | 26e1970 | unchanged |
| `simulations/v8_brain_body_flygym_odor.mp4` | 26e1970 | unchanged |
| `simulations/v9_brain_body_flygym_odor.mp4` | 26e1970 | unchanged |
| `tests/test_back_camera.py` | 2a50708 | unchanged |
| `tests/test_fly_body_height.py` | 2a50708 | unchanged |
| `tests/test_flyvis_reflex_integration.py` | 2a50708 | unchanged |
| `tests/test_flyvis_stateful_timing.py` | 2a50708 | modified (86ea1fc) |
| `tests/test_light_source.py` | 2a50708 | unchanged |
| `tests/test_looming_integration.py` | 2a50708 | unchanged |
| `tests/test_optic_flow_reflex.py` | 2a50708 | unchanged |
| `tests/test_poisson_rate_update.py` | c101a20 | unchanged |
| `tests/test_pole_on_path.py` | 2a50708 | unchanged |
| `tests/test_shadow_pole.py` | 2a50708 | unchanged |
| `tests/test_shadow_pole_v2.py` | 2a50708 | unchanged |
| `tests/test_shadow_pole_v3.py` | 2a50708 | unchanged |
| `tests/test_solid_wall_navigation.py` | 2a50708 | unchanged |
| `tests/test_solid_wall_stability.py` | 2a50708 | unchanged |
| `tests/test_vision_sensor.py` | 2a50708 | unchanged |
| `tests/test_visual_looming_reflex.py` | 2a50708 | unchanged |
| `tests/test_wall_base_sweep.py` | 2a50708 | unchanged |
| `tests/test_wall_before_food.py` | 2a50708 | unchanged |
| `tests/test_wall_heading04.py` | 2a50708 | unchanged |
| `tests/test_wall_heading0588.py` | 2a50708 | unchanged |
| `tests/test_wall_spawn_south.py` | 2a50708 | unchanged |
| `tests/test_wall_v40_config.py` | 2a50708 | unchanged |
| `tests/test_wall_wider.py` | 2a50708 | unchanged |
| `tests/test_wall_zigzag.py` | 2a50708 | unchanged |
| `tests/test_wall_zigzag_channeled.py` | 2a50708 | unchanged |

## B. Files added in this work (343)

Written in this work unless noted. Parts of the flight code are adapted from the NeuroFly walking script (no verbatim lines); file and line ranges: [ADAPTED_CODE.md](ADAPTED_CODE.md). `archive/flight_attempts/` holds earlier flight attempts written by another AI tool before this work (moved there in cffe0d7; not used). `archive/uncommitted_model_utils.patch` is a backup of uncommitted, broken flight functions that had been added to `brain_model/model.py`/`utils.py` (deb3bff; not used).

| file | first commit | note |
|---|---|---|
| `CITATION.cff` | a5cb1c0 |  |
| `CLAUDE.md` | b628a60 |  |
| `NOTICE.md` | a5cb1c0 |  |
| `REPORT_FINAL.md` | bc6f113 |  |
| `REPORT_FINAL_V2.md` | 7de93f2 |  |
| `REPORT_SENSORY_A.md` | 3b55cd5 |  |
| `REPORT_SENSORY_A2.md` | 73ed22b |  |
| `REPORT_SENSORY_B.md` | afcae4c |  |
| `SPEC_BRAIN_CONTROL.md` | da99529 |  |
| `SPEC_FLIGHT.md` | cffe0d7 |  |
| `SPEC_SENSORY_INPUTS.md` | 42014e3 |  |
| `archive/flight_attempts/flight_controllers/aerodynamics.py` | cffe0d7 |  |
| `archive/flight_attempts/flight_dn_mapping.py` | cffe0d7 |  |
| `archive/flight_attempts/fly_flight_40s_perfected.py` | cffe0d7 |  |
| `archive/flight_attempts/fly_flight_biological_40s.py` | cffe0d7 |  |
| `archive/flight_attempts/fly_flight_brain_body_simulation.py` | cffe0d7 |  |
| `archive/flight_attempts/fly_flight_brain_body_simulation.py.bak` | deb3bff |  |
| `archive/flight_attempts/generate_flight_plots.py` | cffe0d7 |  |
| `archive/flight_attempts/odor_field_3d.py` | cffe0d7 |  |
| `archive/flight_attempts/render_biological_40s_video.py` | cffe0d7 |  |
| `archive/flight_attempts/render_flight_40s_perfected_video.py` | cffe0d7 |  |
| `archive/flight_attempts/render_flight_40s_video.py` | cffe0d7 |  |
| `archive/flight_attempts/run_detached.sh` | deb3bff |  |
| `archive/uncommitted_model_utils.patch` | deb3bff |  |
| `archive/adapted_originals/README.md` | 056df11 | pre-re-implementation copy / equivalence helper (not public) |
| `archive/adapted_originals/check_equivalence.py` | 186cecc | pre-re-implementation copy / equivalence helper (not public) |
| `archive/adapted_originals/compare_n1.py` | 186cecc | pre-re-implementation copy / equivalence helper (not public) |
| `archive/adapted_originals/controller_before_reimpl.py` | 056df11 | pre-re-implementation copy / equivalence helper (not public) |
| `archive/adapted_originals/groups_before_reimpl.py` | 056df11 | pre-re-implementation copy / equivalence helper (not public) |
| `archive/adapted_originals/hybrid_before_reimpl.py` | 056df11 | pre-re-implementation copy / equivalence helper (not public) |
| `archive/adapted_originals/run_n1_check.sh` | 186cecc | pre-re-implementation copy / equivalence helper (not public) |
| `archive/adapted_originals/sensors_before_reimpl.py` | 056df11 | pre-re-implementation copy / equivalence helper (not public) |
| `archive/adapted_originals/test_controller_before_reimpl.py` | 056df11 | pre-re-implementation copy / equivalence helper (not public) |
| `data/README.md` | 5714609 |  |
| `data/column_assignment.csv.gz` | 5714609 | unchanged copy of a FlyWire Codex download; third-party data |
| `data/dn_lr_reference.json` | d50ea21 |  |
| `data/dn_lr_reference_sB.json` | 1a551b1 |  |
| `data/leg_sugar_grn_783.csv` | 3ca8175 |  |
| `data/neuron_arbor_centroids.npz` | 96daf66 |  |
| `data/neuron_class.npz` | 96daf66 |  |
| `data/neuron_neuropil.npz` | 96daf66 |  |
| `data/nt_literature_783.csv` | 90bd5e2 |  |
| `data/nt_modulatory_silent_783.csv` | 54b8760 |  |
| `data/orn_spontaneous_783.csv` | f083853 |  |
| `data/sugar_grn_783.csv` | 5714609 |  |
| `data/t45_transduction.json` | 5714609 |  |
| `data/vision_boundary_783.csv` | 7f66b5e |  |
| `data/vision_boundary_types.json` | 7f66b5e |  |
| `data/visual_transduction.json` | 7f66b5e |  |
| `docs/NEUROFLY_FLIGHT_YENI_PROJE_MASTER_DONUSUM_REHBERI.md` | b628a60 | draft written by another AI tool; reference only |
| `docs/NEUROFLY_MASTER_DOKUMANTASYON_VE_SISTEM_PROMPTU.md` | b628a60 |  |
| `docs/REPO_CLEANUP_REPORT.md` | a5cb1c0 |  |
| `docs/vis_dn_directions.json` | 13ffc9f |  |
| `docs/ladder/trial1_readouts.json` | 17ff927 | training ladder round 2: trial-1 readout summary with SHA-256 (§3.6) |
| `docs/ladder_trials.md` | 3c1b0fa | training ladder trial ledger (§3.6); closing line (step 1 stopped after trial 1): 43fefb3 |
| `docs/vl_directions.json` | ed493af | loom follow-up (§3.5b), directions fixed before validation |
| `docs/UCUS_PROMPTU.md` | b628a60 |  |
| `docs/neurofly_upstream/README.fr.md` | a5cb1c0 | copy of the upstream root `README.md` (French), moved here in a5cb1c0; upstream content |
| `flight/__init__.py` | ed85728 |  |
| `flight/body.py` | 5be91ec |  |
| `flight/brain.py` | 27e6010 |  |
| `flight/config.py` | ed85728 |  |
| `flight/controller.py` | c425bf1 |  |
| `flight/groups.py` | 27e6010 |  |
| `flight/head_reflex.py` | e38d96b |  |
| `flight/hybrid.py` | 31d7b6a |  |
| `flight/odor_field_3d.py` | ed85728 |  |
| `flight/olfaction_full.py` | 9a70acc |  |
| `flight/quasi_steady.py` | 5be91ec |  |
| `flight/readouts.py` | f8fe898 |  |
| `flight/readout_model.py` | 1dacbae | trained linear route readout (§3.6) |
| `flight/recorder.py` | 27e6010 | later edits (`ReadoutRecorder`, §3.6): d4e1cd0; teacher labels / applied commands: 1dacbae |
| `flight/sensors.py` | c425bf1 |  |
| `flight/vis_stim.py` | b3479d5 | later edit (condition 11, receding-front, SPEC §3.5b): c37431d |
| `flight/vision_boundary.py` | 8975c17 |  |
| `flight/visual_input.py` | 5714609 |  |
| `flight/vnc_bridge.py` | f8fe898 |  |
| `fly_flight_brain_body_simulation.py` | c425bf1 | later edits (`--record-readout`, §3.6): d4e1cd0; `--readout-model`, `--shuffle-seed`: 1dacbae |
| `generate_flight_plots.py` | b3cd305 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/01_circuit_timeline.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/02_raster_circuits.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/03_dn_steer_turn_coupling.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/04_dng02_collective_coupling.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/05_population_heatmap.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/06_firing_rate_distribution.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/07_odor_olfactory_response.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/08_visual_lamina_loom.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/09_trajectory_3d.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/10_altitude_speed_profile.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/11_turn_pitch_decomposition.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/12_odor_field_3d_slices.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/13_distance_to_food.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/14_turn_components_stack.png` | bc6f113 |  |
| `plots/flight/flight_v11_hybrid_noOlf_final_a/15_mn9_contact.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/01_circuit_timeline.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/02_raster_circuits.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/03_dn_steer_turn_coupling.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/04_dng02_collective_coupling.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/05_population_heatmap.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/06_firing_rate_distribution.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/07_odor_olfactory_response.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/08_visual_lamina_loom.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/09_trajectory_3d.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/10_altitude_speed_profile.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/11_turn_pitch_decomposition.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/12_odor_field_3d_slices.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/13_distance_to_food.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/14_turn_components_stack.png` | bc6f113 |  |
| `plots/flight/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b/15_mn9_contact.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/01_circuit_timeline.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/02_raster_circuits.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/03_dn_steer_turn_coupling.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/04_dng02_collective_coupling.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/05_population_heatmap.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/06_firing_rate_distribution.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/07_odor_olfactory_response.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/08_visual_lamina_loom.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/09_trajectory_3d.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/10_altitude_speed_profile.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/11_turn_pitch_decomposition.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/12_odor_field_3d_slices.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/13_distance_to_food.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/14_turn_components_stack.png` | bc6f113 |  |
| `plots/flight/flight_v13_ablOdor_noOlf_final_c/15_mn9_contact.png` | bc6f113 |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/01_circuit_timeline.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/02_raster_circuits.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/03_dn_steer_turn_coupling.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/04_dng02_collective_coupling.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/05_population_heatmap.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/06_firing_rate_distribution.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/07_odor_olfactory_response.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/08_visual_lamina_loom.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/09_trajectory_3d.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/10_altitude_speed_profile.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/11_turn_pitch_decomposition.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/12_odor_field_3d_slices.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/13_distance_to_food.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/14_turn_components_stack.png` | 81a89cb |  |
| `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/15_mn9_contact.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/01_circuit_timeline.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/02_raster_circuits.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/03_dn_steer_turn_coupling.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/04_dng02_collective_coupling.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/05_population_heatmap.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/06_firing_rate_distribution.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/07_odor_olfactory_response.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/08_visual_lamina_loom.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/09_trajectory_3d.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/10_altitude_speed_profile.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/11_turn_pitch_decomposition.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/12_odor_field_3d_slices.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/13_distance_to_food.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/14_turn_components_stack.png` | 81a89cb |  |
| `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/15_mn9_contact.png` | 81a89cb |  |
| `plots/flight/naturalness_check/flight_v11_hybrid_noOlf_final_a_change_t1.00_t1.00.png` | b075aa9 |  |
| `plots/flight/naturalness_check/flight_v11_hybrid_noOlf_final_a_change_t2.78_t2.78.png` | b075aa9 |  |
| `plots/flight/v2_keyframes/flight_v11_hybrid_noOlf_final_a_change_beslenme_t3.40.png` | 96daf66 |  |
| `plots/flight/v2_keyframes/flight_v11_hybrid_noOlf_final_a_change_kalkis_t0.13.png` | 96daf66 |  |
| `plots/flight/v2_keyframes/flight_v11_hybrid_noOlf_final_a_change_kule_t1.32.png` | 96daf66 |  |
| `plots/flight/v2_keyframes/flight_v11_hybrid_noOlf_final_a_change_t1.00_t1.00.png` | da41417 |  |
| `plots/flight/v2_keyframes/flight_v11_hybrid_noOlf_final_a_change_t2.78_t2.78.png` | da41417 |  |
| `plots/flight/v2_keyframes/flight_v11_hybrid_noOlf_final_a_end_card.png` | 96daf66 |  |
| `plots/flight/v2_keyframes/flight_v11_hybrid_noOlf_final_a_title_card.png` | 96daf66 |  |
| `plots/flight/v2_keyframes/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_change_beslenme_t3.52.png` | 81a89cb |  |
| `plots/flight/v2_keyframes/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_change_inis_t3.02.png` | 81a89cb |  |
| `plots/flight/v2_keyframes/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_change_kalkis_t0.13.png` | 81a89cb |  |
| `plots/flight/v2_keyframes/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_change_kule_t1.45.png` | 81a89cb |  |
| `plots/flight/v2_keyframes/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_end_card.png` | 81a89cb |  |
| `plots/flight/v2_keyframes/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_title_card.png` | 81a89cb |  |
| `plots/flight/v2_keyframes/kontrol/compare_f0100.png` | 35b93a2 |  |
| `plots/flight/v2_keyframes/kontrol/compare_f0600.png` | 35b93a2 |  |
| `plots/flight/v2_keyframes/kontrol/flight_v11_hybrid_noOlf_final_a_change_t1.30_t1.30.png` | 35b93a2 |  |
| `plots/flight/v2_keyframes/kontrol/flight_v11_hybrid_noOlf_final_a_change_t3.20_t3.20.png` | 35b93a2 |  |
| `plots/flight/v2_keyframes/kontrol/flight_v11_hybrid_noOlf_final_a_change_t5.50_t5.50.png` | 35b93a2 |  |
| `plots/flight/v2_keyframes/kontrol/flight_v11_hybrid_noOlf_final_a_end_card.png` | 35b93a2 |  |
| `plots/flight/v2_keyframes/kontrol/flight_v11_hybrid_noOlf_final_a_title_card.png` | 35b93a2 |  |
| `plots/flight/v2_video_frames/compare_final_a_vs_final_c_at15.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/compare_final_a_vs_final_c_at2.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/compare_final_a_vs_final_c_at25.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/flight_n1_vs_n2_v2_compare_at15.5s.png` | 81a89cb |  |
| `plots/flight/v2_video_frames/flight_n1_vs_n2_v2_compare_at24s.png` | 81a89cb |  |
| `plots/flight/v2_video_frames/flight_n1_vs_n2_v2_compare_at8s.png` | 81a89cb |  |
| `plots/flight/v2_video_frames/flight_v11_hybrid_noOlf_final_a_v2_change_at15.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/flight_v11_hybrid_noOlf_final_a_v2_change_at2.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/flight_v11_hybrid_noOlf_final_a_v2_change_at25.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b_v2_change_at15.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b_v2_change_at2.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b_v2_change_at25.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/flight_v13_ablOdor_noOlf_final_c_v2_change_at15.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/flight_v13_ablOdor_noOlf_final_c_v2_change_at2.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/flight_v13_ablOdor_noOlf_final_c_v2_change_at25.0s.png` | bc6f113 |  |
| `plots/flight/v2_video_frames/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change_at15.5s.png` | 81a89cb |  |
| `plots/flight/v2_video_frames/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change_at24s.png` | 81a89cb |  |
| `plots/flight/v2_video_frames/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change_at8s.png` | 81a89cb |  |
| `plots/flight/v2_video_frames/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change_at20s.png` | 81a89cb |  |
| `plots/flight/v2_video_frames/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change_at35s.png` | 81a89cb |  |
| `plots/flight/v2_video_frames/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change_at8s.png` | 81a89cb |  |
| `render_flight_compare.py` | bc6f113 |  |
| `render_flight_video.py` | b3cd305 |  |
| `render_flight_video_v2.py` | 96daf66 |  |
| `run_final.sh` | ea2b4ec |  |
| `run_final_v2.sh` | 8978d41 |  |
| `run_natural.sh` | dc33fb3 |  |
| `run_seeds.sh` | ca32d52 |  |
| `run_starts.sh` | 976812a |  |
| `run_ladder_teacher.sh` | d4e1cd0 | training ladder round 1 (§3.6) |
| `run_ladder_trial1_prep.sh` | 053d610 | training ladder round 2: audit, shuffled replays, fit (§3.6) |
| `run_ladder_trial1_flights.sh` | 053d610 | training ladder round 2: 12 validation flights (§3.6) |
| `run_videos_natural.sh` | 81a89cb |  |
| `run_videos_v2.sh` | bc6f113 |  |
| `scripts/check_videos_v2.sh` | bc6f113 |  |
| `scripts/diag/README.md` | da99529 |  |
| `scripts/diag/a0_apl_gain.py` | f5bc4af |  |
| `scripts/diag/a0_codex.py` | f5bc4af |  |
| `scripts/diag/a0_criteria.py` | 5714609 |  |
| `scripts/diag/a0_symmetry.py` | f5bc4af |  |
| `scripts/diag/a0_visual.py` | 5714609 |  |
| `scripts/diag/a1_closed.py` | f8fe898 |  |
| `scripts/diag/a1_mn9.py` | f8fe898 |  |
| `scripts/diag/a2_closed.py` | d50ea21 |  |
| `scripts/diag/a2_openloop.py` | d50ea21 |  |
| `scripts/diag/a2_visual.py` | d50ea21 |  |
| `scripts/diag/a2b_perturb.py` | 3f66504 |  |
| `scripts/diag/fv2_report.py` | 7de93f2 |  |
| `scripts/diag/hyb_landing.py` | 31d7b6a |  |
| `scripts/diag/ladder_report.py` | 3d05799 | training ladder round 1 (§3.6) |
| `scripts/diag/ladder_trial1_report.py` | 3c1b0fa | training ladder round 2 (§3.9b) |
| `scripts/diag/nat_report.py` | dc33fb3 |  |
| `scripts/diag/r0_all.sh` | da99529 |  |
| `scripts/diag/r0_sugar.py` | da99529 |  |
| `scripts/diag/r1_persist.py` | da99529 |  |
| `scripts/diag/r2_anat.py` | da99529 |  |
| `scripts/diag/r2_extra.py` | da99529 |  |
| `scripts/diag/r3_analyze.py` | da99529 |  |
| `scripts/diag/r3_dng02.py` | da99529 |  |
| `scripts/diag/r3_open.py` | da99529 |  |
| `scripts/diag/r3_open_v1_contaminated.py` | da99529 |  |
| `scripts/diag/sa2_diag.py` | 73ed22b |  |
| `scripts/diag/sa2_report.py` | deb94c8 |  |
| `scripts/diag/o1_diag_report.py` | 21d97bd |  |
| `scripts/diag/o1_report.py` | 79d0d95 |  |
| `scripts/diag/nt_audit.py` | ef6c3ff |  |
| `scripts/diag/nt_report.py` | `90febc3` |  |
| `scripts/diag/run_o1_nt.sh` | 795bf01 |  |
| `scripts/diag/run_vd.sh` | b3479d5 |  |
| `scripts/diag/nf_report.py` | 6a66cd6 |  |
| `scripts/diag/run_o1_nf.sh` | c3bee8f |  |
| `scripts/diag/so_o1_nf.py` | c3bee8f |  |
| `scripts/diag/sa_criteria.py` | fe3a184 |  |
| `scripts/diag/sa_leg_grn.py` | 3ca8175 |  |
| `scripts/diag/sa_report.py` | fe3a184 |  |
| `scripts/diag/sb_report.py` | afcae4c |  |
| `scripts/diag/seeds_report.py` | ca32d52 |  |
| `scripts/diag/so_anatomy.py` | 5b82f84 |  |
| `scripts/diag/so_o1_diag.py` | 21d97bd |  |
| `scripts/diag/so_o1.py` | 9ebaf76 | later edit (--variant): ef6c3ff |
| `scripts/diag/so_nt_robust.py` | 795bf01 |  |
| `scripts/diag/so_o2.py` | 795bf01 |  |
| `scripts/diag/starts_report.py` | eedf653 |  |
| `scripts/diag/summary_report.py` | 0c8753a | summary table "What the brain controls in this model" (REPORT §1.1, README) |
| `scripts/diag/vd_render.py` | b3479d5 |  |
| `scripts/diag/vd_run.py` | b3479d5 |  |
| `scripts/diag/vl_render.py` | c37431d | loom follow-up (§3.5b) |
| `scripts/diag/vl_report.py` | c37431d | loom follow-up (§3.5b) |
| `scripts/diag/vl_run.py` | c37431d | loom follow-up (§3.5b) |
| `scripts/diag/vis_dn_report.py` | 13ffc9f | later edits (--report, --posthoc): 32b667b; (--loom-followup): c37431d |
| `scripts/make_dn_reference.py` | d50ea21 |  |
| `scripts/make_leg_sugar_grn.py` | 3ca8175 |  |
| `scripts/make_nt_literature.py` | 90bd5e2 |  |
| `scripts/make_nt_impute.py` | ef6c3ff |  |
| `scripts/make_nt_silent.py` | 54b8760 |  |
| `scripts/make_orn_spontaneous.py` | f083853 |  |
| `scripts/make_sugar_grn.py` | 5714609 |  |
| `scripts/make_t45_transduction.py` | 5714609 |  |
| `scripts/make_vision_boundary.py` | 7f66b5e |  |
| `scripts/ladder_fit.py` | 1dacbae | training ladder: ridge readout fit (§3.6) |
| `scripts/ladder_replay.py` | 1dacbae | training ladder: open-loop replay audit and shuffled replay (§3.6) |
| `scripts/make_visual_transduction.py` | 7f66b5e |  |
| `scripts/prepare_neuron_geometry.py` | 96daf66 |  |
| `scripts/verify_report_final.py` | bc6f113 | later edits: loom follow-up checks 372d159; summary table and ladder-stop checks 0c8753a |
| `simulation_data/odor_field_3d.py` | ed85728 |  |
| `simulations/flight_v11_hybrid_noOlf_final_a_data.h5` | bc6f113 |  |
| `simulations/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b_data.h5` | bc6f113 |  |
| `simulations/flight_v13_ablOdor_noOlf_final_c_data.h5` | bc6f113 |  |
| `tests/conftest.py` | cffe0d7 |  |
| `tests/flight/test_adapted_spec.py` | 056df11 | checks written from docs/ADAPTED_CODE.md §D |
| `tests/flight/test_body.py` | 5be91ec |  |
| `tests/flight/test_brain.py` | 27e6010 |  |
| `tests/flight/test_controller.py` | c425bf1 |  |
| `tests/flight/test_hybrid.py` | 31d7b6a |  |
| `tests/flight/test_leg_grn.py` | 3ca8175 |  |
| `tests/flight/test_nt_literature.py` | deb94c8 |  |
| `tests/flight/test_nt_impute.py` | ef6c3ff |  |
| `tests/flight/test_odor_field_3d.py` | ed85728 |  |
| `tests/flight/test_olfaction_full.py` | 9a70acc |  |
| `tests/flight/test_readouts.py` | f8fe898 |  |
| `tests/flight/test_readout_record.py` | d4e1cd0 | `--record-readout` (§3.6) |
| `tests/flight/test_readout_model.py` | 1dacbae | trained route readout, ridge, filter, readout mode rules (§3.6) |
| `tests/flight/test_smoke_hdf5.py` | c425bf1 |  |
| `tests/flight/test_start_pose.py` | 976812a |  |
| `tests/flight/test_vis_stim.py` | b3479d5 |  |
| `tests/flight/test_vis_stim_followup.py` | c37431d | condition 11 geometry (§3.5b) |
| `tests/flight/test_vision_boundary.py` | 7a9f78a |  |
| `tests/flight/test_visual_input.py` | 5714609 |  |
| `tests/flight/test_vnc_bridge.py` | f8fe898 |  |
| `docs/reimpl_equivalence/step4a.txt` | 186cecc | run-free equivalence of the re-implemented parts (ADAPTED_CODE.md §E) |
| `docs/reimpl_equivalence/step4b.txt` | 186cecc | n1 seed 3 re-run vs recorded n1 |
| `docs/reimpl_equivalence/step4b_run.log` | 186cecc |  |
| `docs/reimpl_equivalence/step4b_DONE` | 186cecc |  |
| `scripts/figures/make_figures.py` | 98980a9 | figures 1-7 from the stored run files and report scripts |
| `figures/data/fig1_system_labels.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig1_system_labels_summary.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig2_flight_paths.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig2_flight_paths_summary.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig3_feeding_decision.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig3_feeding_decision_summary.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig4_olfactory_lockup.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig4_olfactory_lockup_summary.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig5_vision_dn_screen.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig5_vision_dn_screen_summary.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig6_trained_readout.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig6_trained_readout_summary.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig7_what_the_brain_controls.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/data/fig7_what_the_brain_controls_summary.csv` | db56f79 | plotted data / summary numbers of the figure |
| `figures/fig1_system_labels.pdf` | db56f79 | figure, vector |
| `figures/fig1_system_labels.png` | db56f79 | figure, 300 dpi |
| `figures/fig2_flight_paths.pdf` | db56f79 | figure, vector |
| `figures/fig2_flight_paths.png` | db56f79 | figure, 300 dpi |
| `figures/fig3_feeding_decision.pdf` | db56f79 | figure, vector |
| `figures/fig3_feeding_decision.png` | db56f79 | figure, 300 dpi |
| `figures/fig4_olfactory_lockup.pdf` | db56f79 | figure, vector |
| `figures/fig4_olfactory_lockup.png` | db56f79 | figure, 300 dpi |
| `figures/fig5_vision_dn_screen.pdf` | db56f79 | figure, vector |
| `figures/fig5_vision_dn_screen.png` | db56f79 | figure, 300 dpi |
| `figures/fig6_trained_readout.pdf` | db56f79 | figure, vector |
| `figures/fig6_trained_readout.png` | db56f79 | figure, 300 dpi |
| `figures/fig7_what_the_brain_controls.pdf` | db56f79 | figure, vector |
| `figures/fig7_what_the_brain_controls.png` | db56f79 | figure, 300 dpi |
| `scripts/check_originality.py` | 524d81a | line-level similarity with the upstream NeuroFly files (docs/ORIGINALITY_CHECK.md) |
| `scripts/check_text_overlap.py` | 524d81a | longest common word run between the documents and saved source texts |
| `docs/ORIGINALITY_CHECK.md` | 524d81a | code similarity table, citation table, text-overlap check |
| `scripts/make_data_bundle.py` | bb52a21 | builds the data bundle from a strace of verify (sanitised copies, manifest) |
| `scripts/make_data_bundle.sh` | bb52a21 | wrapper of make_data_bundle.py |
| `scripts/diag/nt_report.py` | 795bf01 | NT audit and O1 under the sign variants (report script; read by verify) |
