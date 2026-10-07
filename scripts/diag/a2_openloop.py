"""Step 2 (direction), open loop: visual stimulus -> full brain -> DNa02/DNp15 -> VNC bridge turn.

Every condition from the same fresh state (net.restore), 1 s, olfaction=False (Step 2
configuration). The readout counts are recorded per 25 ms step; the bridge
(flight/vnc_bridge.py, normalised with data/dn_lr_reference.json) is then applied to the
same counts three ways: normal, --swap-dn-lr steer, --ablate-dn steer (readout = perch
baseline, from the 'perch' condition). turn_bias > 0 = right turn; mean over 250-1000 ms.

Expected directions (fixed before the run, not used to set any constant):
  yaw_R (fly rotated clockwise -> world CCW) and syn_yaw_ccw: optomotor LEFT (turn < 0)
  yaw_L and syn_yaw_cw: optomotor RIGHT (turn > 0)
  loom_L (tower face approaching on the left): avoidance RIGHT (> 0) or none; loom_R: LEFT
  plat_*_{az}: orientation towards the platform = sign(turn) = -sign(az) (az + = left)
Visual sequences: a0_visual_rates.npz (a0_visual.py) and a2_visual_rates.npz (a2_visual.py).

    env -u PYTHONPATH python scripts/diag/a2_openloop.py --vis-dir DIR_A0 --vis2-dir DIR_A2 [--seeds 0 1 2]
    env -u PYTHONPATH python scripts/diag/a2_openloop.py --report a2_openloop_s0.npz a2_openloop_s1.npz ...
--vision-boundary (final-v2 input set sB, SPEC_SENSORY_INPUTS §3.3d): the sequences come from
a0_visual_rates_vb.npz / a2_visual_rates_vb.npz (FlyVis boundary layer, keys __vbnd_L/R), the brain
has vision_boundary=True, olfaction=False; output a2_openloop_vb_s{seed}.npz. --dn-reference sets the
steering reference used by --report (default data/dn_lr_reference.json).
"""
import argparse
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402

from flight import groups as G  # noqa: E402
from flight.readouts import READOUT_TYPES, Readouts  # noqa: E402
from flight.vnc_bridge import PATH_DN_REFERENCE, Bridge, load_reference  # noqa: E402

DT, N, SKIP = 0.025, 40, 10
A0 = ("perch", "air_static", "yaw_R", "yaw_L", "progressive", "loom_L", "loom_R", "sym_prog", "sym_static")
EXPECT = {"yaw_R": -1, "yaw_L": 1, "syn_yaw_ccw": -1, "syn_yaw_cw": 1, "loom_L": 1, "loom_R": -1}


def run(a):
    from flight.brain import FlightBrain, SpikeCounter
    vb = a.vision_boundary
    sfx, key = ("_vb", "vbnd") if vb else ("", "t45")
    v0 = dict(np.load(os.path.join(a.vis_dir, f"a0_visual_rates{sfx}.npz")))
    v2 = dict(np.load(os.path.join(a.vis2_dir, f"a2_visual_rates{sfx}.npz")))
    seqs = {c: (v0[f"{c}__{key}_L"], v0[f"{c}__{key}_R"]) for c in A0 if f"{c}__{key}_L" in v0}
    tail = f"__{key}_L"
    seqs.update({k[:-len(tail)]: (v2[k], v2[k[:-len(tail)] + f"__{key}_R"]) for k in v2 if k.endswith(tail)})
    rid = G.load_root_ids()
    ro = Readouts(rid)
    for seed in a.seeds:
        b = FlightBrain(seed=seed, olfaction=False, verbose=False, nt_silent=a.nt_silent, vision_boundary=vb)
        b.net.store("fresh")
        out = {}
        for name, (L, R) in seqs.items():
            t0 = time.time()
            b.net.restore("fresh")
            b.counter = SpikeCounter(b.spk_mon, b.n)
            b.silence_inputs()
            cnt = []
            for k in range(N):
                b.set_rates(**{f"{key}_L": L[k], f"{key}_R": R[k]}, sugar=0.0)
                _, c = b.step()
                cnt.append(ro.counts(c))
            out[name] = np.array(cnt, np.int32)
            b.counter.t_chunks, b.counter.i_chunks = [], []
            m = ro.rates(out[name][SKIP:].mean(0), DT)
            print(f"seed {seed} {name:18s} DNa02 {m[0, 0]:5.1f}/{m[0, 1]:5.1f} DNp15 {m[1, 0]:5.1f}/{m[1, 1]:5.1f} "
                  f"({time.time() - t0:.0f}s)", flush=True)
        for k in v2:
            if k.endswith("__az"):
                out[k] = v2[k]
        np.savez_compressed(f"a2_openloop{'_nts' + a.nt_silent[0].upper() if a.nt_silent else ''}{sfx}_s{seed}.npz",
                            **out, readout_n=ro.n)
        del b


def bridge_turns(counts, readout_n, perch_counts, reference=None):
    """Per-step turn_bias for normal / swap / ablate from the readout counts (n, types, 2)."""
    class _RO:
        n = readout_n

        @staticmethod
        def rates(c, dt):
            return c / (np.maximum(readout_n, 1) * dt)
    base = _RO.rates(perch_counts[SKIP:].mean(0), DT)
    res = {}
    for mode, kw in (("normal", {}), ("swap", dict(swap=("steer",))), ("ablate", dict(ablate=("steer",)))):
        br = Bridge(_RO, DT, reference=reference, **kw)
        br.set_baseline(np.zeros_like(base))     # open loop: filter starts from rest
        br.baseline = base
        tb, sn, raw = [], [], []
        for c in counts:
            _, used = br.update(c)
            s = br.steer(used)
            tb.append(s["turn_dn"])
            sn.append(s["steer_norm"])
            raw.append(s["steer_raw"])
        res[mode] = (np.array(tb), np.array(sn), np.array(raw))
    return res


def report(paths, ref_path=None):
    ref = load_reference(ref_path or PATH_DN_REFERENCE)
    print(f"steering reference: {ref_path or PATH_DN_REFERENCE}")
    R = [dict(np.load(p)) for p in paths]
    names = [k for k in R[0] if not k.endswith("__az") and k != "readout_n"]
    print(f"turn_bias (> 0 = right), mean 250-1000 ms, per seed; ŝ = normalised L-R; "
          f"raw = DNa02 and DNp15 L-R (Hz); {len(R)} seeds\n")
    print(f"{'condition':20s} {'expected':>8s} {'normal':>22s} {'swap':>22s} {'ablate':>16s}   ŝ       raw DNa02 / DNp15 L-R")
    summary = {}
    for nm in names:
        per = [bridge_turns(r[nm], r["readout_n"], r["perch"], ref) for r in R]
        row = {m: np.array([p[m][0][SKIP:].mean() for p in per]) for m in ("normal", "swap", "ablate")}
        sn = np.mean([p["normal"][1][SKIP:].mean() for p in per])
        raw = np.mean([p["normal"][2][SKIP:].mean(0) for p in per], axis=0)
        summary[nm] = row
        exp = EXPECT.get(nm)
        if nm.startswith("plat_"):
            az = float(nm.rsplit("_", 1)[1])
            exp = -int(np.sign(az)) if az else None
        ok = ""
        if exp:
            ok = " ✓" if np.all(np.sign(row["normal"]) == exp) else (" ✗" if np.all(np.sign(row["normal"]) == -exp)
                                                                      else " ~")
        fmt = lambda v: " ".join(f"{x:+.2f}" for x in v)  # noqa: E731
        print(f"{nm:20s} {('L' if exp == -1 else 'R' if exp == 1 else '-'):>8s} {fmt(row['normal']):>22s}{ok:2s}"
              f"{fmt(row['swap']):>22s} {fmt(row['ablate']):>16s}   {sn:+.2f}   {raw[0]:+6.1f} / {raw[1]:+6.1f}")
    # Step 2 decisions, pre-registered criteria (seeds 3-5): (a) optomotor sign 4 conditions x all seeds;
    # (c) static scenes |mean turn| < 0.3 x all seeds
    a_ok = [np.sign(summary[c]["normal"]) == EXPECT[c] for c in ("syn_yaw_ccw", "syn_yaw_cw", "yaw_R", "yaw_L")
            if c in summary]
    c_ok = [np.abs(summary[c]["normal"]) < 0.3 for c in ("perch", "air_static", "sym_static") if c in summary]
    print(f"\n(a) optomotor sign: {int(np.sum(a_ok))}/{np.size(a_ok)}   "
          f"(c) static |turn| < 0.3: {int(np.sum(c_ok))}/{np.size(c_ok)}")
    for style in ("dark", "neutral"):
        az = sorted({float(k.rsplit("_", 1)[1]) for k in names if k.startswith(f"plat_{style}_")})
        if not az:
            continue
        y = np.array([summary[f"plat_{style}_{int(a)}"]["normal"].mean() for a in az])
        r = np.corrcoef(az, y)[0, 1]
        print(f"\nplatform {style}: turn vs azimuth: " + " ".join(f"{a:+.0f}°:{v:+.2f}" for a, v in zip(az, y))
              + f"   r = {r:+.2f} (orientation towards the platform = negative r)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--vis-dir", default=".")
    ap.add_argument("--vis2-dir", default=".")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--nt-silent", default=None)
    ap.add_argument("--report", nargs="+", default=None)
    ap.add_argument("--vision-boundary", action="store_true")
    ap.add_argument("--dn-reference", default=None)
    a = ap.parse_args()
    report(a.report, a.dn_reference) if a.report else run(a)
