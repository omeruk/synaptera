"""--record-readout (SPEC_SENSORY_INPUTS §3.6): shapes, dtypes, step indexing and consistency with the sparse spike counts.
Synthetic recorder input; no brain, no body."""
import h5py
import numpy as np

from flight.recorder import BehaviorRecorder, ReadoutRecorder, SparseSpikeCounts


def _fill(n_pre=18, n_steps=5, n_neurons=40, n_L=7, n_R=6):
    rng = np.random.default_rng(0)
    dn_glob = np.array([3, 9, 10, 25, 39])
    rro = ReadoutRecorder(n_pre, n_steps, dn_glob, dn_glob, n_L, n_R)       # full brain: local = global
    sp = SparseSpikeCounts(None)
    rec = BehaviorRecorder(n_steps)
    steps = list(range(-n_pre, n_steps))
    for s in steps:
        per = rng.poisson(0.7, n_neurons)
        vb = {"L": rng.random(n_L) * 10, "R": rng.random(n_R) * 10}
        rro.put(s, per, vb, 100.0 if s == 2 else 0.0, applied=(s >= 0 or s < -8))
        sp.add(s, per)
    for k in range(n_steps):
        rec.put(k, turn_hand=0.1 * k, thrust_hand=-0.2 * k, pitch_hand=0.01 * k, roll_hand=-0.001 * k,
                phase=2, wings_on=1, pos=np.array([k, 0, 1.0]), vel=np.zeros(3), quat=np.array([1, 0, 0, 0.0]),
                omega=np.zeros(3), heading=0.0, platform_contact=0, tower_contact=0, tower_penetration=0.0,
                is_feeding=0, mn9_rate=0.0, turn_flyvis=0.0)
    return rro, sp, rec, dn_glob


def test_shapes_indexing_and_counts(tmp_path):
    rro, sp, rec, dn = _fill()
    p = tmp_path / "x_readout.h5"
    rro.write(p, rec, dict(seed=1))
    with h5py.File(p, "r") as f:
        assert f["step_idx"][0] == -18 and f["step_idx"][-1] == 4 and len(f["step_idx"]) == 23
        assert f["dn_counts"].shape == (23, 5) and f["dn_counts"].dtype == np.int16
        assert f["vbnd_L"].shape == (23, 7) and f["vbnd_L"].dtype == np.float32 and f["vbnd_R"].shape == (23, 6)
        assert f["teacher_cmd"].shape == (23, 4) and np.all(f["teacher_cmd"][:18] == 0)
        assert np.allclose(f["teacher_cmd"][18 + 3], [0.3, -0.6, 0.03, -0.003])
        assert f["pos"].shape == (23, 3) and f["phase"].shape == (23,)
        assert f["applied_inputs"][10] == 0 and f["applied_inputs"][0] == 1 and f["applied_inputs"][18] == 1
        assert f["sugar_rate_in"][18 + 2] == 100.0
        s_idx, n_idx, cnt = sp.arrays()
        for r, step in enumerate(f["step_idx"][:]):
            for j, g in enumerate(f["dn_neuron_idx"][:]):
                m = (s_idx == step) & (n_idx == g)
                assert f["dn_counts"][r, j] == (int(cnt[m][0]) if m.any() else 0)


def test_labels_replace_teacher_cmd_and_applied_is_kept(tmp_path):
    """Readout mode: teacher_cmd = label of the visited state, applied_cmd = what the flight used; default: no applied_cmd."""
    rro, sp, rec, dn = _fill()
    lab = np.arange(20, dtype=float).reshape(5, 4)
    p = tmp_path / "y_readout.h5"
    rro.write(p, rec, dict(seed=1), labels=lab)
    with h5py.File(p, "r") as f:
        assert np.allclose(f["teacher_cmd"][18:], lab) and np.all(f["teacher_cmd"][:18] == 0)
        assert np.allclose(f["applied_cmd"][18 + 3], [0.3, -0.6, 0.03, -0.003])
    q = tmp_path / "z_readout.h5"
    rro.write(q, rec, dict(seed=1))
    with h5py.File(q, "r") as f:
        assert "applied_cmd" not in f
