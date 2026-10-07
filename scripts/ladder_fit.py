"""Training ladder (SPEC_SENSORY_INPUTS §3.6): fit the three readouts of trial 1 from the 12 TEACHER training flights only.

Features: real = recorded DN counts of the published brain; shuffled = DN counts of the replay into the shuffled connectome
(scripts/ladder_replay.py); bypass = fixed random projection of the recorded boundary-layer rates. Samples: every wings-on
closed-loop step of training starts 1-12 (validation starts 13-16 and exam starts never enter a fit). Writes the readout files
under logs/ladder/readouts (outside git) and a summary with hashes under docs/ladder (in git).

    env -u PYTHONPATH python scripts/ladder_fit.py
"""
import json
import sys
import time
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flight import readout_model as RM  # noqa: E402

REC = ROOT / "logs/ladder/teacher/records"
REPLAY = ROOT / "logs/ladder/replay_shuffled"
OUT = ROOT / "logs/ladder/readouts"
TRAIN_IDS = list(range(1, 13))          # SPEC §3.6: starts 1-12 train, 13-16 validation, 17-22 exam
TRIAL = 1


def load_flight(i, arm, P):
    name = f"lt{i:02d}"
    path = next(REC.glob(f"*_{name}_readout.h5"))
    with h5py.File(path, "r") as f:
        n_pre = int(f.attrs["n_pre"])
        on = f["wings_on"][:] > 0
        on[:n_pre] = False
        Y = f["teacher_cmd"][:]
        if arm == "real":
            raw = f["dn_counts"][:].astype(np.float64) / RM.DT
        elif arm == "shuffled":
            z = np.load(REPLAY / f"{name}_shuffled_dn.npz")
            assert np.array_equal(z["step_idx"], f["step_idx"][:])
            assert np.array_equal(z["dn_neuron_idx"], f["dn_neuron_idx"][:])
            raw = z["dn_counts"].astype(np.float64) / RM.DT
        else:
            v = np.concatenate([f["vbnd_L"][:], f["vbnd_R"][:]], axis=1).astype(np.float64)   # float32 values as recorded
            raw = v @ P.T
    F = RM.filter_series(raw)
    return F[on], Y[on], path


def main():
    assert max(TRAIN_IDS) <= 12
    OUT.mkdir(parents=True, exist_ok=True)
    P = RM.bypass_matrix()
    summary = dict(trial=TRIAL, train_ids=TRAIN_IDS, lambdas=list(RM.LAMBDAS), filter_tau_s=RM.TAU_FILTER, commands=list(RM.COMMANDS),
                   seeds=dict(shuffle=RM.SHUFFLE_SEED, bypass=RM.BYPASS_SEED), arms={})
    for arm in RM.ARMS:
        t0 = time.time()
        F_list, Y_list, files = [], [], []
        for i in TRAIN_IDS:
            F, Y, p = load_flight(i, arm, P)
            F_list.append(F)
            Y_list.append(Y)
            files.append(p.name)
        model, tab = RM.fit_arm(F_list, Y_list)
        Yall = np.concatenate(Y_list)
        data = dict(n_flights=len(TRAIN_IDS), n_samples=int(len(Yall)), samples_per_flight=[len(y) for y in Y_list],
                    label_mean=Yall.mean(0).tolist(), label_std=Yall.std(0).tolist(), n_const_features=tab["n_const_features"],
                    record_files=files)
        path = OUT / f"trial{TRIAL}_{arm}.npz"
        meta = dict(arm=arm, trial=TRIAL, train_ids=TRAIN_IDS, lam=model["lam"].tolist(), data=data,
                    cv_r2=dict(zip(RM.COMMANDS, tab["r2"].tolist())), commands=list(RM.COMMANDS), filter_a=RM.FILTER_A,
                    clip_lo=RM.CLIP_LO.tolist(), clip_hi=RM.CLIP_HI.tolist())
        RM.save_model(path, model, arm, meta)
        summary["arms"][arm] = dict(file=str(path.relative_to(ROOT)), sha256=RM.file_sha256(path), lam=dict(zip(RM.COMMANDS, model["lam"].tolist())),
                                    cv_r2=dict(zip(RM.COMMANDS, [round(x, 4) for x in tab["r2"].tolist()])),
                                    heldout_sse={str(l): s.tolist() for l, s in zip(RM.LAMBDAS, tab["sse"])}, sst=tab["sst"].tolist(), data=data)
        print(f"{arm}: lambda {model['lam']}, CV R2 {np.round(tab['r2'], 3)}, {len(Yall)} samples, {time.time() - t0:.0f} s", flush=True)
    (ROOT / f"docs/ladder/trial{TRIAL}_readouts.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
