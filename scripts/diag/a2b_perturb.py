"""Step 2 decisions (b): closed-loop yaw stabilisation after a sudden 30 deg yaw perturbation.

Runs: fly_flight_brain_body_simulation.py --no-olfaction --spawn-air 440 -170 160 90 --hover
--yaw-perturb 0.5 +-30 --n-steps 60, seeds 3/4/5, normal and --ablate-dn steer.
Criteria (fixed in SPEC before the runs; t_on = 0.5 s, omega = d heading / dt, + = left):
  b1  normal: mean |omega| in [t_on+0.4, t_on+0.5] < 0.5 * omega_p (omega_p = 30 deg / 0.1 s)
  b2  normal: mean turn [t_on, t_on+0.5] - mean turn [t_on-0.25, t_on] opposite in sign to the perturbation
  b3  |dpsi_normal| < |dpsi_ablate| (same seed, direction); dpsi = psi(t_on+0.5) - psi(t_on) - omega_pre*0.5
  (c, record only) mean turn in [0.25, 0.5] s of the normal runs.

    env -u PYTHONPATH python scripts/diag/a2b_perturb.py RUN_data.h5 [...]
"""
import json
import sys

import h5py
import numpy as np

T_ON, DUR, W_P = 0.5, 0.1, np.radians(30.0) / 0.1


def load(p):
    with h5py.File(p) as f:
        b = {k: f["behavior"][k][:] for k in ("t", "heading", "turn_bias", "steer_norm", "steer_raw", "speed")}
        fl = json.loads(f["meta"].attrs["flags"])
        seed = int(f["meta"].attrs["seed"])
    return b, fl, seed


def mean_in(b, key, t0, t1):
    m = (b["t"] > t0 + 1e-9) & (b["t"] <= t1 + 1e-9)       # t = end of the step
    return float(np.mean(b[key][m]))


def analyse(b):
    t = np.concatenate([[0.0], b["t"]])
    psi = np.unwrap(np.concatenate([[b["heading"][0]], b["heading"]]))
    b["omega_z"] = np.diff(psi) / np.diff(t)                  # per step, rad/s
    psi_at = lambda x: float(np.interp(x, t, psi))            # noqa: E731
    w_pre = mean_in(b, "omega_z", T_ON - 0.25, T_ON)
    return dict(
        w_late=abs(mean_in(b, "omega_z", T_ON + 0.4, T_ON + 0.5)),
        w_peak=float(np.max(np.abs(b["omega_z"][(b["t"] > T_ON) & (b["t"] <= T_ON + DUR + 0.05)]))),
        d_turn=mean_in(b, "turn_bias", T_ON, T_ON + 0.5) - mean_in(b, "turn_bias", T_ON - 0.25, T_ON),
        turn_pre=mean_in(b, "turn_bias", 0.25, T_ON),
        dpsi=np.degrees(psi_at(T_ON + 0.5) - psi_at(T_ON) - w_pre * 0.5),
        w_pre=w_pre, dpsi_total=np.degrees(psi_at(t[-1]) - psi_at(0.0)),
        speed=float(b["speed"].max()))


def main(paths):
    R = {}
    for p in paths:
        b, fl, seed = load(p)
        deg = fl["yaw_perturb"][1]
        R[(seed, deg, "ablate" if fl["ablate_dn"] else "normal")] = analyse(b)
    print(f"{'seed':>4s} {'dir':>4s} {'cond':>7s} | {'|w| peak':>8s} {'|w| late':>8s} {'b1':>3s} | {'turn_pre':>8s} "
          f"{'dturn':>6s} {'b2':>3s} | {'dpsi':>6s} {'b3':>3s} | w_pre  total  vmax")
    n = dict(b1=0, b2=0, b3=0, N=0)
    for (seed, deg, cond), r in sorted(R.items()):
        sgn = np.sign(deg)
        b1 = r["w_late"] < 0.5 * W_P
        b2 = np.sign(r["d_turn"]) == sgn             # left perturbation (+) -> right counter-turn (turn > 0)
        ab = R.get((seed, deg, "ablate"))
        b3 = ab is not None and abs(r["dpsi"]) < abs(ab["dpsi"])
        if cond == "normal":
            n["N"] += 1
            n["b1"] += b1
            n["b2"] += b2
            n["b3"] += b3
        mark = (lambda x: " ok" if x else "  x") if cond == "normal" else (lambda x: "  -")
        print(f"{seed:4d} {deg:+4.0f} {cond:>7s} | {r['w_peak']:8.2f} {r['w_late']:8.2f} {mark(b1)} | "
              f"{r['turn_pre']:+8.2f} {r['d_turn']:+6.2f} {mark(b2)} | {r['dpsi']:+6.1f} {mark(b3)} | "
              f"{r['w_pre']:+5.2f} {r['dpsi_total']:+6.0f} {r['speed']:5.0f}")
    print(f"\nnormal runs: b1 {n['b1']}/{n['N']}, b2 {n['b2']}/{n['N']}, b3 {n['b3']}/{n['N']}  "
          f"(threshold |w| late < {0.5 * W_P:.2f} rad/s; ablate b1: "
          f"{sum(r['w_late'] < 0.5 * W_P for k, r in R.items() if k[2] == 'ablate')}/"
          f"{sum(k[2] == 'ablate' for k in R)})")


if __name__ == "__main__":
    main(sys.argv[1:])
