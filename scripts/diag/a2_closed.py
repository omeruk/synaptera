"""Step 2 (direction), closed loop: summarise flight HDF5 runs.

tower runs (take-off from the pedestal towards tower 1): tower contact (collision) and its
time, minimum clearance, total heading change (+ = left), mean turn_bias and s_hat.
plat runs (--spawn-air, platform north at +-30 deg): platform azimuth at 0 / 0.25 / 0.5 / 1 s
(deg, + = left), change of |azimuth| (negative = turned towards the platform), closest
distance to the food, heading change.

    env -u PYTHONPATH python scripts/diag/a2_closed.py RUN_data.h5 [...]
"""
import sys

import h5py
import numpy as np


def load(p):
    with h5py.File(p) as f:
        return {k: f["behavior"][k][:] for k in ("t", "pos", "heading", "turn_bias", "steer_norm", "tower_contact",
                                                  "min_tower_clearance", "platform_azimuth", "dist_to_food",
                                                  "omega", "steer_raw")}


def at(b, key, t):
    return float(b[key][min(np.searchsorted(b["t"], t - 1e-9), len(b["t"]) - 1)])


def main(paths):
    print(f"{'run':62s} {'turn':>6s} {'s^':>6s} {'dhead':>7s} | tower: {'hit@':>6s} {'minclr':>6s} | "
          f"plat: az0 az.25 az.5 az1  d|az|  dmin")
    for p in paths:
        b = load(p)
        dh = np.degrees(np.unwrap(b["heading"])[-1] - np.unwrap(b["heading"])[0])
        hit = np.flatnonzero(b["tower_contact"] > 0)
        s = (f"{p.split('/')[-1][:62]:62s} {b['turn_bias'].mean():+6.2f} {b['steer_norm'].mean():+6.2f} "
             f"{dh:+7.0f} | {('%5.2fs' % b['t'][hit[0]]) if len(hit) else '    no':>6s} "
             f"{b['min_tower_clearance'].min():6.1f} | ")
        az = [at(b, "platform_azimuth", t) for t in (0.025, 0.25, 0.5, 1.0)]
        s += " ".join(f"{a:+4.0f}" for a in az) + f" {abs(az[-1]) - abs(az[0]):+5.0f} {b['dist_to_food'].min():5.0f}"
        print(s)


if __name__ == "__main__":
    main(sys.argv[1:])
