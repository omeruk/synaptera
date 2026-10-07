"""Training ladder, round 1 (SPEC_SENSORY_INPUTS §3.6): the 16 teacher (n1) flights from the training and validation starts.
Read-only from logs/ladder/teacher (DONE markers, flight HDF5, readout records). Markdown to stdout.

    env -u PYTHONPATH python scripts/diag/ladder_report.py

S1 / S2 / touchdown / tower contact: scripts/verify_report_final.metrics (§3.3c definitions). Every flight's meta (seed,
steps, flags, start) is checked against the pre-registered table.
"""
import json
import re
import sys
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from verify_report_final import metrics  # noqa: E402

LOG = ROOT / "logs" / "ladder" / "teacher"
# SPEC §3.6 table (id: role, DX, DY, YAW), ids 1-16 (the exam starts 17-22 are not in this report)
STARTS = {1: (24.9, -14.2, 59.3), 2: (-22.1, 3.9, -34.7), 3: (7.2, -18.3, 46.6), 4: (32.8, -26.8, -23.4),
          5: (31.7, 25.7, 7.8), 6: (39.6, -37.8, 47.6), 7: (7.7, -14.0, 5.8), 8: (-15.5, -21.5, 12.3),
          9: (9.7, 22.9, 40.0), 10: (28.9, 28.6, 42.8), 11: (-17.6, -0.1, -11.6), 12: (-8.2, -38.3, -56.4),
          13: (-8.1, -23.1, 43.1), 14: (-29.7, -35.9, 10.7), 15: (39.9, -4.7, -58.2), 16: (-35.9, 28.2, 46.2)}


def role(i):
    return "train" if i <= 12 else "validation"


def rows():
    out = []
    for i, (dx, dy, yaw) in STARTS.items():
        name = f"lt{i:02d}"
        done = (LOG / f"DONE_{name}").read_text()
        g = lambda k: re.search(rf"^{k}=(.*)$", done, re.M).group(1)  # noqa: E731
        h5 = Path(g("h5"))
        m = metrics(h5)
        with h5py.File(h5, "r") as f:
            seed, n_steps = int(f["meta"].attrs["seed"]), int(f["meta"].attrs["n_steps"])
            flags = json.loads(f["meta"].attrs["flags"])
            ped = json.loads(f["meta"].attrs["geometry"])["pedestal"]
            b = f["behavior"]
            on = int((b["wings_on"][:] > 0).sum())
            ph = b["phase"][:]
            k_td = int(np.flatnonzero(ph == 4)[0]) if (ph == 4).any() else None
            mn9_td = float(b["mn9_rate"][k_td]) if k_td is not None else None
        assert seed == 100 + i and n_steps == 300 and list(flags["start_offset"]) == [dx, dy] and flags["start_yaw"] == yaw, name
        assert all(flags[k] for k in ("hybrid", "vision_boundary", "no_olfaction", "no_brain_steer", "head_reflex", "postures"))
        assert abs(ped[0] - dx) < 1e-9 and abs(ped[1] - dy) < 1e-9
        rec = next((LOG / "records").glob(f"*_{name}_readout.h5"))
        with h5py.File(rec, "r") as f:
            shape = f["dn_counts"].shape
            assert f["vbnd_L"].shape[0] == shape[0] == 18 + 300 and shape[1] == 1299
        out.append(dict(id=i, role=role(i), dx=dx, dy=dy, yaw=yaw, seed=seed, exit=int(g("exit")), S1=m["S1"], S2=m["S2"],
                        td=m["touchdown_step"], tc=m["tower_contact_steps"], pen=m["pen_steps_pre_td"], dmin=m["d_min"],
                        mn9=f"{mn9_td:.1f}" if mn9_td is not None else "—", wings_on=on, badq=int(g("badqacc_warnings")),
                        rec_mb=rec.stat().st_size / 1e6, h5_mb=h5.stat().st_size / 1e6, rec=rec.name))
    return out


def main():
    R = rows()
    L = ["| id | role | DX (mm) | DY (mm) | YAW (deg) | brain seed | S1 | S2 | touchdown step | tower-contact steps | pre-touchdown penetration steps | closest to food | MN9 at touchdown (Hz) | wings-on steps |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in R:
        L.append(f"| {r['id']} | {r['role']} | {r['dx']:+.1f} | {r['dy']:+.1f} | {r['yaw']:+.1f} | {r['seed']} | {r['S1']} | {r['S2']} | "
                 f"{r['td']} | {r['tc']} | {r['pen']} | {r['dmin']} | {r['mn9']} | {r['wings_on']} |")
    n = len(R)
    s1, s2 = sum(r["S1"] == "✓" for r in R), sum(r["S2"] == "✓" for r in R)
    both = sum(r["S1"] == "✓" and r["S2"] == "✓" for r in R)
    L += ["", f"Teacher flights: {n}; all exit codes 0: {all(r['exit'] == 0 for r in R)}; BADQACC lines: {sum(r['badq'] for r in R)}.",
          f"- S1 {s1}/{n} (train {sum(r['S1'] == '✓' for r in R if r['role'] == 'train')}/12, validation "
          f"{sum(r['S1'] == '✓' for r in R if r['role'] == 'validation')}/4); S2 {s2}/{n}; S1 and S2 {both}/{n}.",
          f"- Wings-on steps (training samples of the readout): train {sum(r['wings_on'] for r in R if r['role'] == 'train')}, "
          f"validation {sum(r['wings_on'] for r in R if r['role'] == 'validation')}.",
          f"- Readout records: {n} files, {sum(r['rec_mb'] for r in R):.0f} MB in total ({min(r['rec_mb'] for r in R):.0f}-"
          f"{max(r['rec_mb'] for r in R):.0f} MB each; 318 rows = 18 pre-take-off + 300 closed-loop steps); flight HDF5 "
          f"{sum(r['h5_mb'] for r in R):.0f} MB in total."]
    print("\n".join(L))


if __name__ == "__main__":
    main()
