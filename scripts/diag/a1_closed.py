"""Step 1 (beslenme), closed loop: summarise flight HDF5 runs (MN9 decision vs contact).

Per run: steps with tarsus-platform contact, MN9 (bridge-filtered, mean of 2, Hz) with and
without contact, fraction of contact steps with the proboscis extended, extensions without
contact, latency from the first contact to the first extension.

    env -u PYTHONPATH python scripts/diag/a1_closed.py RUN_data.h5 [...]
"""
import sys

import h5py
import numpy as np


def summary(path):
    with h5py.File(path) as f:
        b = f["behavior"]
        con = b["platform_contact"][:] > 0
        mn9 = b["mn9_rate"][:]
        ext = b["proboscis_extended"][:] > 0
        feed = b["is_feeding"][:] > 0
        t = b["t"][:]
    lat = np.nan
    if con.any() and ext[con].any():
        lat = t[np.flatnonzero(ext & con)[0]] - t[np.flatnonzero(con)[0]] + 0.025
    return dict(n=len(t), contact=int(con.sum()), mn9_con=mn9[con].mean() if con.any() else np.nan,
                mn9_nocon=mn9[~con].mean() if (~con).any() else np.nan,
                ext_con=ext[con].mean() if con.any() else np.nan, ext_nocon=int(ext[~con].sum()),
                feeding=int(feed.sum()), latency_s=lat)


if __name__ == "__main__":
    print(f"{'run':55s} {'steps':>5s} {'contact':>7s} {'MN9 con':>8s} {'MN9 no':>7s} {'ext|con':>7s} "
          f"{'ext no-con':>10s} {'feeding':>7s} {'latency':>7s}")
    for p in sys.argv[1:]:
        s = summary(p)
        print(f"{p.split('/')[-1]:55s} {s['n']:5d} {s['contact']:7d} {s['mn9_con']:8.1f} {s['mn9_nocon']:7.1f} "
              f"{s['ext_con']:7.2f} {s['ext_nocon']:10d} {s['feeding']:7d} {s['latency_s'] * 1000:6.0f}ms")
