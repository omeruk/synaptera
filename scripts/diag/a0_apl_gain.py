"""Step 0 / --apl-graded: fix the graded-APL gain once from KC sparseness alone.

Pre-registered rule (written before the scan; no DN or behaviour output is looked at):
  stimulus  food odour: all food-glomerulus ORNs (both antennae) at the model's odour
            maximum cfg.ORN_FOOD_RATE[1] = 150 Hz, no other input, 1 s from the fresh state
  measure   fraction of the 5177 KCs with >= 1 spike in 250-1000 ms
  target    literature: ~5-10 % of KCs respond to an odour (Turner et al. 2008;
            Honegger et al. 2011; Lin et al. 2014) -> midpoint 7.5 %
  grid      gain = 2**(k/2), k = -6..10 (0.125 .. 32)
  choice    the grid gain whose fraction is closest to 7.5 %
Output: a0_apl_gain.json (scan + chosen gain) in the current directory. The chosen value
is then written by hand into flight/brain.py APL_GAIN.

    env -u PYTHONPATH python scripts/diag/a0_apl_gain.py [--seed 0]
"""
import argparse
import json
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402

from flight import config as cfg  # noqa: E402

TARGET = 0.075
GRID = [2 ** (k / 2) for k in range(-6, 11)]


def main(seed):
    from flight.brain import FlightBrain, SpikeCounter
    b = FlightBrain(seed=seed, apl_graded=True, apl_gain=GRID[0])
    b.net.store("fresh")
    odor = cfg.ORN_FOOD_RATE[1]
    scan = []
    for gain in [0.0] + GRID:
        t0 = time.time()
        b.net.restore("fresh")
        b.counter = SpikeCounter(b.spk_mon, b.n)
        b.set_apl_gain(gain)
        b.silence_inputs()
        b.set_rates(orn_food_L=odor, orn_food_R=odor)
        on = np.zeros(b.n, np.int64)
        for k in range(40):
            _, c = b.step()
            if k >= 10:
                on += c
        kc = on[b.kc_idx]
        r = dict(gain=gain, kc_frac_ge1=float((kc >= 1).mean()), kc_frac_ge2=float((kc >= 2).mean()),
                 kc_rate_active=float(kc[kc > 0].sum() / max((kc > 0).sum(), 1) / 0.75),
                 net_hz=float(on.sum() / (b.n * 0.75)), a_apl=np.asarray(b.apl_group.a_[:]).tolist(),
                 i_apl_kc_mv=float(np.asarray(b.neu.I_apl_[:])[b.kc_idx].mean() * 1e3))
        scan.append(r)
        b.counter.t_chunks, b.counter.i_chunks = [], []
        print(f"gain {gain:7.3f}: KC >=1 spike {100 * r['kc_frac_ge1']:5.1f}%  >=2 {100 * r['kc_frac_ge2']:5.1f}%  "
              f"active KC {r['kc_rate_active']:5.1f} Hz  net {r['net_hz']:.3f} Hz  I_apl(KC) {r['i_apl_kc_mv']:.1f} mV "
              f"({time.time() - t0:.0f}s)", flush=True)
    grid = [r for r in scan if r["gain"] > 0]
    best = min(grid, key=lambda r: abs(r["kc_frac_ge1"] - TARGET))
    print(f"chosen gain {best['gain']:.4f} (KC {100 * best['kc_frac_ge1']:.1f}%)")
    with open("a0_apl_gain.json", "w") as f:
        json.dump(dict(rule=__doc__, seed=seed, odor_hz=odor, target=TARGET, scan=scan, chosen=best["gain"]), f,
                  indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    main(ap.parse_args().seed)
