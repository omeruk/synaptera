"""Training ladder, round 2 (SPEC_SENSORY_INPUTS §3.6): open-loop replay of one recorded teacher flight into a brain.

The recorded brain inputs of the flight (boundary-layer rates as sensed, float32; platform-contact sugar rate; the perch
calibration steps, the input-cut steps and the 300 closed-loop steps, in the recorded order) are applied to a freshly built
brain; the spike counts of the 1,299 descending neurons of every step are saved.

  --brain real      published connectome, Brian seed = the flight's seed (100 + id): the AUDIT; the DN counts (and, with
                    --audit, the spike counts of all neurons) are compared with the recording of the live flight.
  --brain shuffled  degree-preserving shuffled connectome (permutation seed 901), Brian seed = the flight's seed (100 + id).

    env -u PYTHONPATH python scripts/ladder_replay.py --id 2 --brain real --audit --out logs/ladder/replay_audit
"""
import argparse
import json
import sys
import time
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flight import readout_model as RM  # noqa: E402
from flight.brain import FlightBrain  # noqa: E402
from flight.recorder import SparseSpikeCounts  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", type=int, required=True)
    ap.add_argument("--brain", choices=("real", "shuffled"), required=True)
    ap.add_argument("--records", default=str(ROOT / "logs/ladder/teacher/records"))
    ap.add_argument("--sim", default=str(ROOT / "logs/ladder/teacher/sim"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--audit", action="store_true", help="compare with the live flight's recording (real brain only)")
    a = ap.parse_args()
    name = f"lt{a.id:02d}"
    rec_path = next(Path(a.records).glob(f"*_{name}_readout.h5"))
    seed = 100 + a.id
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with h5py.File(rec_path, "r") as f:
        step_idx, dn_idx = f["step_idx"][:], f["dn_neuron_idx"][:].astype(np.int64)
        applied, sugar = f["applied_inputs"][:], f["sugar_rate_in"][:]
        vL, vR = f["vbnd_L"][:], f["vbnd_R"][:]
        dn_rec = f["dn_counts"][:]
    # the brain exactly as the flight script builds it (n1 configuration), nothing else changed
    t0 = time.time()
    brain = FlightBrain(seed=seed, olfaction=False, vision_boundary=True,
                        shuffle_seed=RM.SHUFFLE_SEED if a.brain == "shuffled" else None)
    print(f"{name} {a.brain}: brain built in {time.time() - t0:.0f} s, brian seed {seed}")
    spk = SparseSpikeCounts(brain.l2g)
    dn = np.zeros((len(step_idx), len(dn_idx)), np.int16)
    t1 = time.time()
    for r, k in enumerate(step_idx):
        if applied[r]:
            brain.set_rates(sugar=float(sugar[r]), vbnd_L=vL[r].astype(np.float64), vbnd_R=vR[r].astype(np.float64))
        else:
            brain.silence_inputs()
        _, per = brain.step()
        spk.add(int(k), per)
        dn[r] = np.minimum(per[dn_idx], np.iinfo(np.int16).max)
        if r % 50 == 0:
            print(f"  row {r}/{len(step_idx)} step {k}  DN spikes {int(dn[r].sum())}  {time.time() - t1:.0f} s", flush=True)
    res = dict(id=a.id, brain=a.brain, seed=seed, shuffle_seed=RM.SHUFFLE_SEED if a.brain == "shuffled" else None,
               rows=len(step_idx), loop_s=time.time() - t1, record=rec_path.name)
    if a.brain == "real":
        res["dn_identical"] = bool(np.array_equal(dn, dn_rec))
        res["dn_rows_differing"] = int((dn != dn_rec).any(1).sum())
        res["dn_total_abs_diff"] = int(np.abs(dn.astype(int) - dn_rec.astype(int)).sum())
        res["dn_total_spikes_recorded"] = int(dn_rec.sum())
    if a.audit:
        h5 = next(Path(a.sim).glob(f"*_{name}_data.h5"))
        with h5py.File(h5, "r") as f:
            s_ref, n_ref, c_ref = f["spikes/step_idx"][:], f["spikes/neuron_idx"][:], f["spikes/count"][:]
        s_new, n_new, c_new = spk.arrays()
        key = lambda s, n: s.astype(np.int64) * 1_000_000 + n.astype(np.int64)  # noqa: E731
        o1, o2 = np.argsort(key(s_ref, n_ref)), np.argsort(key(s_new, n_new))
        res["all_neuron_counts_identical"] = bool(
            len(s_ref) == len(s_new) and np.array_equal(key(s_ref, n_ref)[o1], key(s_new, n_new)[o2])
            and np.array_equal(c_ref[o1], c_new[o2]))
        res["all_neuron_spikes_recorded"] = int(c_ref.sum())
        res["all_neuron_spikes_replay"] = int(c_new.sum())
    np.savez_compressed(out / f"{name}_{a.brain}_dn.npz", dn_counts=dn, step_idx=step_idx, dn_neuron_idx=dn_idx)
    (out / f"{name}_{a.brain}_replay.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
