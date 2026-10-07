"""Step 0 (b) source: where does the DN L/R asymmetry come from with a mirror-symmetric T4/T5 grating?

Stimulus: sym_prog of a0_visual.py: the same forward (front-to-back) grating in the FlyVis frame of
both eyes. No odour (the KC state does not fire), ascending 0, 1 s, every condition from the same clean state.

  normal    FlyVis left eye -> FlyWire t45_L, right eye -> t45_R (run-time path)
  swap      the eyes are exchanged: the FlyVis activity of the right eye drives the T4/T5 of the left
            hemisphere (same column mapping), the left eye drives the right
  uniform   no mapping: every T4/T5 neuron gets the rate of the two-eye mean of its own sub-type
            (per step), no column / spatial information; identical input to L and R per sub-type
  swap_uniform does not exist (uniform is L/R identical already)

Reading: if the asymmetry moves with the input under swap, the source is the input / mapping;
if it stays, it is on the FlyWire side. If it also stays under uniform, it is the connectome and not the column mapping.
In addition the T4/T5 output synapses per hemisphere (to the LPTCs) are counted from the parquet.

    env -u PYTHONPATH python scripts/diag/a0_symmetry.py [--seed 0]
"""
import argparse
import os
import sys
import time

os.environ.setdefault("MUJOCO_GL", "egl")
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from flight import groups as G  # noqa: E402
from flight import visual_input as V  # noqa: E402

N_STEPS = 40
SKIP = 10
READ = ["DNa02", "DNp15", "DNb06", "DNp22", "DNp20", "DNa01", "DNa03", "DNp07", "DNp10", "DNp01", "DNg02"]
LPTC = {"HS": r"^HS[NES]$", "VS": r"^VS\d+$", "H2": r"^H2$", "LPLC2": r"^LPLC2$", "LPLC1": r"^LPLC1$",
        "LLPC1": r"^LLPC1$", "LPC2": r"^LPC2$"}


def visual_rates(groups):
    """Per-step per-neuron rates for normal / swap / uniform, plus FlyVis L/R activity difference."""
    eyes = V.FlyVisEyes({"L": groups["t45_L"], "R": groups["t45_R"]})
    sub = V.VIS_SUBFRAMES
    n = N_STEPS * sub
    gL = list(V.grating_frames((-1, 0), n, tf=V.GRATING_TF_HZ))
    gR = list(V.grating_frames((1, 0), n, tf=V.GRATING_TF_HZ))
    eyes.reset()
    out = {k: {"L": [], "R": []} for k in ("normal", "swap", "uniform")}
    dact = []
    for k in range(N_STEPS):
        acc = 0.0
        for i in range(k * sub, (k + 1) * sub):
            acc = acc + eyes._forward(eyes.to_flyvis(np.stack([gL[i][0], gR[i][1]])))
        act = acc / sub
        nL, nR = eyes.node["L"], eyes.node["R"]
        dact.append(np.abs(act[0, nL] - act[1, nL]).mean() / (np.abs(act[0, nL]).mean() + 1e-12))
        for name, a in (("normal", {"L": act[0, nL], "R": act[1, nR]}), ("swap", {"L": act[1, nL], "R": act[0, nR]})):
            r = eyes.rates(a)
            out[name]["L"].append(r["L"])
            out[name]["R"].append(r["R"])
        r = eyes.rates({"L": act[0, nL], "R": act[1, nR]})
        mu = [(r["L"][eyes.type_code["L"] == t].sum() + r["R"][eyes.type_code["R"] == t].sum())
              / ((eyes.type_code["L"] == t).sum() + (eyes.type_code["R"] == t).sum()) for t in range(8)]
        out["uniform"]["L"].append(np.asarray(mu)[eyes.type_code["L"]])
        out["uniform"]["R"].append(np.asarray(mu)[eyes.type_code["R"]])
    tc = eyes.type_code
    del eyes
    return {k: {s: np.array(v[s]) for s in v} for k, v in out.items()}, float(np.mean(dact[SKIP:])), tc


def parquet_t45_out(rid, ann):
    con = pd.read_parquet(G.PATH_CON, columns=["Presynaptic_Index", "Postsynaptic_Index", "Connectivity"])
    col = G.load_t45_columns()
    r2i = G.root_to_index(rid)
    hemi = np.zeros(len(rid), np.int8)
    hemi[[r2i[r] for r in col.root_id[col.hemisphere == "left"]]] = 1
    hemi[[r2i[r] for r in col.root_id[col.hemisphere == "right"]]] = 2
    ct = ann["cell_type"].reindex(rid).fillna("?").astype(str).to_numpy()
    pre = con.Presynaptic_Index.to_numpy()
    post = con.Postsynaptic_Index.to_numpy()
    w = con.Connectivity.to_numpy()
    m = hemi[pre] > 0
    print("\nparquet: T4/T5 output synapses (no threshold), hemisphere: "
          f"L {w[m & (hemi[pre] == 1)].sum():,} / R {w[m & (hemi[pre] == 2)].sum():,}")
    rows = []
    for lab, pat in LPTC.items():
        tm = pd.Series(ct).str.match(pat).to_numpy()
        a = [w[m & (hemi[pre] == h) & tm[post]].sum() for h in (1, 2)]
        rows.append((lab, a[0], a[1], (a[0] - a[1]) / max(a[0] + a[1], 1)))
    print(pd.DataFrame(rows, columns=["LPTC", "L", "R", "asym"]).to_string(index=False))


def main(seed):
    rid = G.load_root_ids()
    ann = pd.read_csv(G.PATH_ANN, sep="\t", low_memory=False).set_index("root_id")
    groups = G.build_groups(rid)
    rates, dact, tc = visual_rates(groups)
    print(f"FlyVis left/right eye activity difference (at left-eye nodes, relative mean): {dact:.4f}")
    for k, r in rates.items():
        mL, mR = r["L"][SKIP:].mean(), r["R"][SKIP:].mean()
        tL = [r["L"][SKIP:, tc["L"] == t].mean() for t in range(8)]
        tR = [r["R"][SKIP:, tc["R"] == t].mean() for t in range(8)]
        print(f"  input {k:8s}: mean Hz L {mL:.2f} / R {mR:.2f}; total (Hz·neuron) L {r['L'][SKIP:].sum(1).mean():.0f} / "
              f"R {r['R'][SKIP:].sum(1).mean():.0f} | " + " ".join(f"{G.T45_TYPES[t]} {tL[t]:.1f}/{tR[t]:.1f}" for t in range(8)))
    parquet_t45_out(rid, ann)

    from flight.brain import FlightBrain, SpikeCounter
    b = FlightBrain(seed=seed, olfaction=False)
    b.net.store("fresh")
    dn = pd.read_csv(G.PATH_DN)
    r2i = G.root_to_index(rid)
    dn = dn[dn.root_id.isin(r2i)]
    sets = {}
    for t in READ:
        m = dn.cell_type.astype(str).str.match(rf"^{t}(_|$)")
        sets[t] = {s: dn.root_id[m & (dn.side == sd)].map(r2i).to_numpy() for s, sd in (("L", "left"), ("R", "right"))}
    ctn = ann["cell_type"].reindex(rid).fillna("?").astype(str)
    sd = ann["side"].reindex(rid).astype(str).to_numpy()
    for lab, pat in LPTC.items():
        tm = ctn.str.match(pat).to_numpy()
        sets[lab] = {s: np.flatnonzero(tm & (sd == sdn)) for s, sdn in (("L", "left"), ("R", "right"))}
    res = {}
    for name in ("normal", "swap", "uniform"):
        t0 = time.time()
        b.net.restore("fresh")
        b.counter = SpikeCounter(b.spk_mon, b.n)
        b.silence_inputs()
        on = np.zeros(b.n, np.int64)
        for k in range(N_STEPS):
            b.set_rates(t45_L=rates[name]["L"][k], t45_R=rates[name]["R"][k])
            _, c = b.step()
            if k >= SKIP:
                on += c
        b.counter.t_chunks, b.counter.i_chunks = [], []
        T = (N_STEPS - SKIP) * 0.025
        res[name] = {t: (on[v["L"]].sum() / max(len(v["L"]), 1) / T, on[v["R"]].sum() / max(len(v["R"]), 1) / T)
                     for t, v in sets.items()}
        print(f"{name}: net {on.sum() / (b.n * T):.3f} Hz ({time.time() - t0:.0f}s)", flush=True)
    print("\nHz per neuron L/R and |L−R|/(L+R) (signed: (L−R)/(L+R))")
    rows = []
    for t in list(LPTC) + READ:
        row = {"okuma": t}
        for name in res:
            L, R = res[name][t]
            row[name] = f"{L:.0f}/{R:.0f} {((L - R) / (L + R)) if L + R > 0 else float('nan'):+.2f}"
        rows.append(row)
    print(pd.DataFrame(rows).to_string(index=False))
    np.savez_compressed(f"a0_symmetry_s{seed}.npz", **{f"{n}__{t}": np.array(v) for n, d in res.items() for t, v in d.items()})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    main(ap.parse_args().seed)
