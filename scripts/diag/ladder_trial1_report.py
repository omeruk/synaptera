"""Training ladder, round 2, trial 1 (SPEC_SENSORY_INPUTS §3.6 + round-2 clarifications): replay audit, readout table (descriptive),
the 12 validation flights and the champion status. Read-only from logs/ladder and docs/ladder. Markdown to stdout.

    env -u PYTHONPATH python scripts/diag/ladder_trial1_report.py

S1 / S2 / touchdown / tower contact: scripts/verify_report_final.metrics (§3.3c definitions).
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
from flight import readout_model as RM  # noqa: E402
from verify_report_final import metrics  # noqa: E402

L = ROOT / "logs" / "ladder"
T = L / "trial1"
VAL = {13: (-8.1, -23.1, 43.1), 14: (-29.7, -35.9, 10.7), 15: (39.9, -4.7, -58.2), 16: (-35.9, 28.2, 46.2)}
ARM_LABEL = {"real": "T1-real", "shuffled": "T1-shuffled", "bypass": "T1-bypass"}
CMD_LABEL = {"turn_hand": "turn", "thrust_hand": "thrust", "pitch_hand": "pitch", "roll_hand": "roll"}


def audit_lines():
    a = json.loads((L / "replay_audit" / "lt02_real_replay.json").read_text())
    out = [f"- Audit (teacher flight 2, published brain, Brian seed {a['seed']}): {a['rows']} rows; DN counts identical to the recording: "
           f"{a['dn_identical']} (rows differing {a['dn_rows_differing']}, summed absolute difference {a['dn_total_abs_diff']}, "
           f"{a['dn_total_spikes_recorded']:,} DN spikes); counts of all neurons identical: {a['all_neuron_counts_identical']} "
           f"({a['all_neuron_spikes_recorded']:,} recorded, {a['all_neuron_spikes_replay']:,} replayed spikes)."]
    rows, tot_real, tot_shuf, ok = 0, 0, 0, True
    for i in range(1, 17):
        s = json.loads((L / "replay_shuffled" / f"lt{i:02d}_shuffled_replay.json").read_text())
        z = np.load(L / "replay_shuffled" / f"lt{i:02d}_shuffled_dn.npz")
        rec = next((L / "teacher" / "records").glob(f"*_lt{i:02d}_readout.h5"))
        with h5py.File(rec, "r") as f:
            tot_real += int(f["dn_counts"][:].sum())
            ok &= bool(np.array_equal(z["step_idx"], f["step_idx"][:]))
        tot_shuf += int(z["dn_counts"].sum())
        rows += s["rows"]
        ok &= s["shuffle_seed"] == RM.SHUFFLE_SEED and s["seed"] == 100 + i
    out.append(f"- Shuffled-connectome replay (permutation seed {RM.SHUFFLE_SEED}, Brian seed 100 + id): 16 flights, {rows} rows; DN spikes over all "
               f"16 flights {tot_shuf:,} (published brain, recorded live: {tot_real:,}); rows and seeds as recorded: {ok}.")
    return out


def r2_table():
    S = json.loads((ROOT / "docs" / "ladder" / "trial1_readouts.json").read_text())
    n = S["arms"]["real"]["data"]
    out = [f"Fitted on the {n['n_flights']} training flights (starts 1-12), {n['n_samples']} wings-on samples; leave-one-flight-out "
           "cross-validation over the training flights. **Descriptive, not a criterion.** λ (selected) / cross-validated R²:", "",
           "| arm | " + " | ".join(f"{CMD_LABEL[c]} λ | {CMD_LABEL[c]} R²" for c in RM.COMMANDS) + " | constant features | readout file SHA-256 |",
           "|---|" + "---|" * (2 * len(RM.COMMANDS) + 2)]
    for arm in RM.ARMS:
        a = S["arms"][arm]
        cells = " | ".join(f"{a['lam'][c]:g} | {a['cv_r2'][c]:+.3f}" for c in RM.COMMANDS)
        out.append(f"| {ARM_LABEL[arm]} | {cells} | {a['data']['n_const_features']} | `{a['sha256'][:16]}…` |")
    return out


def flights():
    rows = []
    for arm in RM.ARMS:
        for i, (dx, dy, yaw) in VAL.items():
            name = f"t1{arm}_v{i:02d}"
            done = (T / f"DONE_{name}").read_text()
            g = lambda k: re.search(rf"^{k}=(.*)$", done, re.M).group(1)  # noqa: E731
            h5 = Path(g("h5"))
            m = metrics(h5)
            rec = next((T / "records").glob(f"*_{name}_readout.h5"))
            with h5py.File(h5, "r") as f:
                meta = f["meta"].attrs
                flags = json.loads(meta["flags"])
                assert int(meta["seed"]) == 100 + i and int(meta["n_steps"]) == 300 and list(flags["start_offset"]) == [dx, dy]
                assert flags["start_yaw"] == yaw and flags["readout_arm"] == arm
                assert flags["shuffle_seed"] == (RM.SHUFFLE_SEED if arm == "shuffled" else None)
                assert Path(flags["readout_model"]).name == f"trial1_{arm}.npz"
                b = f["behavior"]
                ph = b["phase"][:]
                k_td = int(np.flatnonzero(ph == 4)[0]) if (ph == 4).any() else None
                mn9 = float(b["mn9_rate"][k_td]) if k_td is not None else None
            with h5py.File(rec, "r") as f:
                n_pre = int(f.attrs["n_pre"])
                on = f["wings_on"][:] > 0
                on[:n_pre] = False
                dev = np.abs(f["applied_cmd"][:][on] - f["teacher_cmd"][:][on]).mean(0)
                n_on = int(on.sum())
            rows.append(dict(arm=arm, id=i, exit=int(g("exit")), badq=int(g("badqacc_warnings")), S1=m["S1"], S2=m["S2"], td=m["touchdown_step"].replace("yok", "none"),
                             tc=m["tower_contact_steps"], pen=m["pen_steps_pre_td"], dmin=m["d_min"], dev=dev, n_on=n_on,
                             mn9=f"{mn9:.1f}" if mn9 is not None else "—"))
    return rows


def main():
    out = ["**Replay (step A).**", *audit_lines(), "", "**Readouts (step B).**", *r2_table(), ""]
    R = flights()
    out += ["**Trial 1 validation flights (step D; starts 13-16, brain seed 100 + id).** Mean deviation = mean over the wings-on steps of "
            "|readout command − teacher command of the same state| (turn: wing-yaw command units; thrust: lift fraction; pitch and roll: rad).", "",
            "| arm | start | S1 | S2 | touchdown step | tower-contact steps | pre-touchdown penetration steps | closest to food | wings-on steps | "
            "mean deviation turn | thrust | pitch | roll |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in R:
        out.append(f"| {ARM_LABEL[r['arm']]} | {r['id']} | {r['S1']} | {r['S2']} | {r['td']} | {r['tc']} | {r['pen']} | {r['dmin']} | {r['n_on']} | "
                   f"{r['dev'][0]:.3f} | {r['dev'][1]:.3f} | {r['dev'][2]:.3f} | {r['dev'][3]:.3f} |")
    out += ["", f"Validation flights: {len(R)}; all exit codes 0: {all(r['exit'] == 0 for r in R)}; BADQACC lines: {sum(r['badq'] for r in R)}.", ""]
    for arm in RM.ARMS:
        n = sum(r["S1"] == "✓" for r in R if r["arm"] == arm)
        champ = "champion of trial 1" if n >= 3 else "no champion at trial 1"
        out.append(f"- {ARM_LABEL[arm]}: S1 {n}/4 → {champ}"
                   + (f"; S2 {sum(r['S2'] == '✓' for r in R if r['arm'] == arm)}/4" if arm == "real" else "") + ".")
    print("\n".join(out))


if __name__ == "__main__":
    main()
