"""Write data/dn_lr_reference.json: per-side DN reference rates for the yaw readout
normalisation (SPEC_BRAIN_CONTROL Step 0 decisions II, decision 2; VARSAYIM).

Reference stimulus (fixed before any closed-loop run): the mirror-symmetric
front-to-back grating of scripts/diag/a0_visual.py (sym_prog: standard FlyVis
grating, left-eye image moving left, right-eye image moving right, i.e.
progressive in both eyes after the right-eye mirror), 2 s, through the real
FlyVis -> T4/T5 path. Brain: Step 2 configuration (olfaction=False, spiking APL,
no NT change), full brain, fresh state, seeds 0/1/2; rates counted 250-2000 ms.
Every READOUT_TYPES entry is stored (Hz per neuron, L and R); the bridge uses
STEER_TYPES. Run once.

--vision-boundary (SPEC_SENSORY_INPUTS §3.3, final-v2 input set "sB"): the same stimulus,
protocol and seeds through the FlyVis boundary layer (flight/vision_boundary.py, 32 types)
instead of T4/T5 only; brain olfaction=False (--no-olfaction), spiking APL, NT unchanged.
Written to data/dn_lr_reference_sB.json; data/dn_lr_reference.json is kept.

    env -u PYTHONPATH python scripts/make_dn_reference.py
    env -u PYTHONPATH python scripts/make_dn_reference.py --vision-boundary
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from flight import groups as G  # noqa: E402
from flight import visual_input as V  # noqa: E402
from flight.readouts import READOUT_TYPES, Readouts  # noqa: E402
from flight.vnc_bridge import PATH_DN_REFERENCE, PATH_DN_REFERENCE_SB  # noqa: E402

N_STEPS, SKIP, SEEDS, DT = 80, 10, (0, 1, 2), 0.025


def sym_prog_rates(groups, vision_boundary=False):
    if vision_boundary:
        from flight import vision_boundary as VB
        eyes = VB.BoundaryEyes({"L": groups["vbnd_L"], "R": groups["vbnd_R"]})
    else:
        eyes = V.FlyVisEyes({"L": groups["t45_L"], "R": groups["t45_R"]})
    n = N_STEPS * V.VIS_SUBFRAMES
    gL = list(V.grating_frames((-1, 0), n))
    gR = list(V.grating_frames((1, 0), n))
    out = []
    for k in range(N_STEPS):
        fr = [np.stack([gL[i][0], gR[i][1]]) for i in range(k * V.VIS_SUBFRAMES, (k + 1) * V.VIS_SUBFRAMES)]
        a, _ = eyes.step(fr)
        r = eyes.rates(a)
        out.append((r["L"].astype(np.float32), r["R"].astype(np.float32)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--vision-boundary", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    vb = a.vision_boundary
    out = Path(a.out) if a.out else (PATH_DN_REFERENCE_SB if vb else PATH_DN_REFERENCE)
    from flight.brain import FlightBrain
    rid = G.load_root_ids()
    groups = G.build_groups(rid)
    if vb:
        from flight.vision_boundary import boundary_groups
        groups.update(boundary_groups(rid))
    seq = sym_prog_rates(groups, vision_boundary=vb)
    key = ("vbnd_L", "vbnd_R") if vb else ("t45_L", "t45_R")
    ro = Readouts(rid)
    per_seed = []
    for seed in SEEDS:
        t0 = time.time()
        b = FlightBrain(seed=seed, olfaction=False, verbose=False, vision_boundary=vb)
        acc = np.zeros((len(READOUT_TYPES), 2))
        for k, (rl, rr) in enumerate(seq):
            b.set_rates(**{key[0]: rl, key[1]: rr}, sugar=0.0)
            _, c = b.step()
            if k >= SKIP:
                acc += ro.counts(c)
        hz = ro.rates(acc, (N_STEPS - SKIP) * DT)
        per_seed.append(hz)
        print(f"seed {seed}: " + " ".join(f"{t} {hz[i, 0]:.1f}/{hz[i, 1]:.1f}" for i, t in enumerate(READOUT_TYPES))
              + f" ({time.time() - t0:.0f} s)", flush=True)
        del b
    m = np.mean(per_seed, axis=0)
    ref = dict(
        rates_hz={t: dict(L=float(m[i, 0]), R=float(m[i, 1])) for i, t in enumerate(READOUT_TYPES)},
        per_seed_hz={t: [[float(p[i, 0]), float(p[i, 1])] for p in per_seed] for i, t in enumerate(READOUT_TYPES)},
        stimulus="sym_prog: mirror-symmetric front-to-back grating (FlyVis standard grating, both eyes)"
                 + (" -> FlyVis boundary layer (32 types, data/visual_transduction.json)" if vb else ""),
        grating=dict(period_px=V.GRATING_PERIOD_PX, tf_hz=V.GRATING_TF_HZ, contrast=V.GRATING_CONTRAST),
        window_s=[SKIP * DT, N_STEPS * DT], seeds=list(SEEDS),
        brain=dict(olfaction=False, apl="spiking", nt_silent=None, inputs="v2", asc_legacy=False,
                   **(dict(vision_boundary=True, input_set="sB: --vision-boundary --no-olfaction") if vb else {})),
        label="VARSAYIM: per-side normalisation of the yaw readout (SPEC Step 0 decisions II, decision 2)"
              + ("; recalibrated for the sB input set (SPEC_SENSORY_INPUTS §3.3)" if vb else ""))
    with open(out, "w") as f:
        json.dump(ref, f, indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
