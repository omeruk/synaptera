"""Summary table "What the brain controls in this model" (REPORT.md section of that name; short form in README.md).

Every number is recomputed from the run files and the existing report scripts (no simulation, read-only); the fixed wording is
in this file. Markdown to stdout. `scripts/verify_report_final.py` checks every line of the output verbatim against REPORT.md
(full) and README.md (--short).

    env -u PYTHONPATH python scripts/diag/summary_report.py            # full table + reading (REPORT.md)
    env -u PYTHONPATH python scripts/diag/summary_report.py --short    # function | source | status (README.md)

Source labels: BRAIN, HAND-MADE, REFLEX, FLYVIS, TRAINED. Status: shown / not shown / not testable / not completed.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "diag"))
import verify_report_final as V  # noqa: E402

SEEDS = (10, 11, 12, 13, 14)
START_RUNS = ("st_xp40", "st_xm40", "st_yp40", "st_ym40", "st_yawp30", "st_yawm30", "st_yawp60", "st_yawm60")


def ladder_s1():
    """Trial-1 validation S1 count per arm (S1 of every flight recomputed by ladder_trial1_report.flights())."""
    import ladder_trial1_report as T
    R = T.flights()
    return {arm: (sum(r["S1"] == "✓" for r in R if r["arm"] == arm), sum(r["arm"] == arm for r in R)) for arm in ("real", "shuffled", "bypass")}


def verdict():
    """The one verdict sentence of the training ladder, step 1 (identical wherever it is quoted)."""
    s = ladder_s1()
    assert len({v for v in s.values()}) == 1 and all(n < 3 for n, _ in s.values()), s   # no champion; same count in all arms
    n, m = s["real"]
    assert not list((ROOT / "logs" / "ladder").glob("trial[2-9]*")) and not list((ROOT / "logs" / "ladder").glob("exam*")), "later trial or exam present"
    return f"T1 not completed: no champion in trial 1 (S1 {n}/{m} in all three arms); trials 2–4 and the exam were not run."


def values():
    import seeds_report as SE
    import starts_report as ST
    import ladder_report as LR
    import vis_dn_report as VD
    import vl_report as VL
    import o1_report as O
    v = {}
    # feeding decision, route, landing: n1 seeds (seed 3 + 10-14), the 8 start conditions, the 16 teacher flights
    n1 = [SE.run_values(SE.name("n1", s)) for s in (3, *SEEDS)]
    v["n1_n"] = len(n1)
    v["n1_s12"] = sum(r["S1"] == "✓" and r["S2"] == "✓" for r in n1)
    v["n1_td"] = sum(r["touchdown"] is not None for r in n1)
    mn9 = [r["mn9_td_raw"] for r in n1]
    v["n1_mn9_ok"], v["n1_mn9_min"] = sum(x > 10 for x in mn9), min(mn9)
    st = [ST.run_values(n) for n in START_RUNS]
    v["st_n"] = len(st)
    v["st_s12"] = sum(r["S1"] == "✓" and r["S2"] == "✓" for r in st)
    v["st_mn9_ok"] = sum(r["mn9_td_raw"] > 10 for r in st)
    t = LR.rows()
    v["t_n"], v["t_s1"], v["t_s2"] = len(t), sum(r["S1"] == "✓" for r in t), sum(r["S2"] == "✓" for r in t)
    # brain-only arm
    n2 = [SE.run_values(SE.name("n2", s)) for s in (3, *SEEDS)]
    v["n2_n"], v["n2_s12"] = len(n2), sum(r["S1"] == "✓" and r["S2"] == "✓" for r in n2)
    v["n2_td"] = sum(r["touchdown"] is not None for r in n2)
    v["n2_tc"] = sorted({int(r["tower_contact"]) for r in n2})
    assert all(V.metrics(V.h5_any(n))["touchdown_step"] == "yok" for n in ("final_c", "final_v2c"))   # no touchdown ("yok" = Turkish "none", the token of metrics())
    # DNp15 closed-loop validation (§3.2) and DNg02
    val = ROOT / "logs" / "v2" / "val"
    ol = "\n".join(V.script_lines([ROOT / "scripts/diag/a2_openloop.py", "--report", *[f"a2_openloop_vb_s{s}.npz" for s in (6, 7, 8)],
                                   "--dn-reference", ROOT / "data" / "dn_lr_reference_sB.json"], cwd=val))
    v["val_a"] = re.search(r"\(a\) optomotor sign: (\d+/\d+)", ol).group(1)
    v["val_c"] = re.search(r"\(c\) static \|turn\| < 0\.3: (\d+/\d+)", ol).group(1)
    runs_b = sorted((ROOT / "simulations").glob("flight_v*_v2val_data.h5"))
    assert len(runs_b) == 12
    bb = "\n".join(V.script_lines([ROOT / "scripts/diag/a2b_perturb.py", *runs_b]))
    v["val_b"] = re.search(r"normal runs: b1 (\d+/\d+), b2 (\d+/\d+), b3 (\d+/\d+)", bb).groups()
    v["v2a_S1"], v["v2a_S2"] = (V.metrics(V.h5_any("final_v2a"))[k] for k in ("S1", "S2"))
    tot = 0
    for n in ("final_a", "final_b", "final_c", "final_v2a", "final_v2c", "n1", "n2"):
        with h5py.File(V.h5_any(n), "r") as f:
            tot += int(f["behavior/dng02_L"][:].sum() + f["behavior/dng02_R"][:].sum())
    v["dng02"] = tot
    # olfaction
    o1 = V.o1_values()
    v["o1_pass"] = o1["O1 rates"].split(" drive rates")[0]
    nt = V.nt_values()
    v["nt_pass"] = nt["NT variants rates"]
    nf = V.nf_values()
    v["nf"] = nf["NF result"]
    # vision -> DN, open loop
    r = VD.evaluate()
    v["vd_n"], v["vd_pass"] = len(r["apriori"]), r["apriori_counts"]["PASS"]
    v["vd_pass_names"] = [x["cluster"] for x in r["apriori"] if x["result"] == "PASS"]
    v["vd_ex_pass"], v["vd_ex_n"] = r["exploratory_counts"]["PASS"], r["n_candidates"]
    v["vd_ex_names"] = [x["cluster"] for x in r["exploratory"] if x["result"] == "PASS"]
    r = VL.evaluate()
    v["vl_n"], v["vl_pass"] = len(r["apriori"]), r["apriori_counts"]["PASS"]
    # trained readout
    v["t1"] = ladder_s1()
    v["verdict"] = verdict()
    # visual input
    with h5py.File(V.h5_any("n1"), "r") as f:
        v["vb_types"] = len(f["vision_boundary/types"])
        v["vb_n"] = len(f["vision_boundary/idx_L"]) + len(f["vision_boundary/idx_R"])
    from flight import head_reflex as HR  # noqa: E402
    v["hr"] = (HR.G[0], HR.G[1], float(np.degrees(HR.THETA_MAX)))
    return v


def rows(v):
    pas = "; ".join(v["vd_pass_names"])
    ex = "; ".join(v["vd_ex_names"])
    yaw, roll, pitch = v["hr"][0], v["hr"][1], v["hr"][2]
    return [
        ("Feeding decision after touchdown (MN9 above 10 Hz)", "BRAIN",
         f"§3.4, §3.5: MN9 above 10 Hz at the touchdown step in {v['n1_mn9_ok']}/{v['n1_n']} n1 seeds (lowest {v['n1_mn9_min']:.1f} Hz) and in "
         f"{v['st_mn9_ok']}/{v['st_n']} start conditions (the others one step later); the trigger below is hand-made", "shown (given the hand-made trigger)"),
        ("Trigger of the feeding decision (leg contact drives labellar sugar GRNs)", "HAND-MADE",
         "§2.4: tarsus–platform contact is mapped by hand onto 36 labellar sugar GRNs at 100 Hz; there is no proboscis contact in the model", "shown (hand-made shortcut)"),
        ("Leg GRN → MN9 path (the natural trigger)", "BRAIN",
         "§4: driving the 12 leg sugar GRNs selected by connectivity left MN9 at 0.0 Hz in 3/3 seeds (lab-notebook number, no stored run)", "not shown"),
        ("Route to the target", "HAND-MADE",
         f"§3.4, §3.5, §3.9: turn from the odour field of the simulator, thrust and tilt from the platform position; n1 S1 ∧ S2 {v['n1_s12']}/{v['n1_n']} seeds "
         f"(bit-identical route) and {v['st_s12']}/{v['st_n']} start conditions; teacher S1 {v['t_s1']}/{v['t_n']} and S2 {v['t_s2']}/{v['t_n']} in the 16 joint start draws",
         "shown (hand-made; no brain contribution)"),
        ("Landing sequence (phase machine: take-off, cruise, approach, descend, touchdown)", "HAND-MADE",
         f"§2.3: timers and distance rules read the simulator position and contact; touchdown in {v['n1_td']}/{v['n1_n']} n1 seeds", "shown (hand-made)"),
        ("Attitude stabilisation (haltere PD) and head reflex", "REFLEX",
         f"§2.3: hand-set constants (head yaw gain {yaw:g}, roll/pitch gain {roll:g}, angle limit ±{v['hr'][2]:g}°); the brain is not connected to the neck", "shown (hand-set)"),
        ("Brain-only flight (hand-made flight programme only)", "BRAIN",
         f"§3.3, §3.4: n2 S1 ∧ S2 {v['n2_s12']}/{v['n2_n']} seeds, touchdown {v['n2_td']}/{v['n2_n']}; final_c and final_v2c: no touchdown", "not shown"),
        ("Steering from brain DNs (DNp15, closed loop)", "BRAIN",
         f"§3.2: pre-registered validation failed (optomotor sign {v['val_a']}, yaw stabilisation b1 {v['val_b'][0]}, b2 {v['val_b'][1]}, b3 {v['val_b'][2]}, "
         f"static-scene turn command below 0.3 in {v['val_c']}); final_v2a S1 {v['v2a_S1']}", "not shown"),
        ("Altitude and thrust from DNg02", "BRAIN",
         f"§4: DNg02 fired {v['dng02']} spikes in all seven reported runs", "not shown"),
        ("Olfaction (brain's olfactory circuit)", "BRAIN",
         f"§3.7: stage O1 {v['o1_pass']} returned to rest; the N1/N2 sign variants {v['nt_pass']}; upstream-style drive {v['nf']} (the circuit locks into a persistent state)",
         "not shown"),
        ("Vision → descending neurons (open loop)", "BRAIN",
         f"§3.8: {v['vd_pass']} of {v['vd_n']} a-priori tests passed ({pas}, lateralised even for a static grating); exploratory {v['vd_ex_pass']} of "
         f"{v['vd_ex_n']} candidates ({ex}, general motion)", "not shown"),
        ("Loom tracking by DNs (open loop)", "BRAIN",
         f"§3.8b: {v['vl_pass']} of {v['vl_n']} a-priori tests passed; the frontal-disc 'appearance' response is a post-hoc observation", "not shown"),
        ("Trained readout of the DNs for the route commands (T1)", "TRAINED",
         "§3.9b: trial 1 fitted from 12 teacher flights; " + v["verdict"], "not completed"),
        ("Visual input to the brain", "FLYVIS",
         f"§2.4: FlyVis (pretrained, not FlyWire) → {v['vb_types']} boundary-layer types ({v['vb_n']:,} neurons) → Poisson drive into FlyWire", "shown (input only)"),
    ]


READING = ("**Reading.** In this model, with these inputs, the only behaviour controlled by the connectome model is the feeding decision, and it is "
           "triggered by a hand-made contact-to-taste mapping. Usable sensory information about the position of the target could not be shown "
           "in the model: the olfactory circuit locks into a persistent state, the steering and altitude readouts failed or stayed silent, and the "
           "open-loop visual screens gave one lateralised pass. Known reasons that limit these tests: there is no ventral nerve cord (the DN → wing "
           "path is a hand-made bridge), the model has no resting activity, and several transmitter signs are predictions. "
           "The route, the landing sequence and the reflexes are hand-made, and the trained readout was not completed, so the model gives "
           "no evidence about whether a connectome-based route readout is possible.")

NOTE = ("A `noOlf` / `--no-olfaction` label means that the BRAIN's olfactory input is off. The hand-made route still reads the odour field of the "
        "simulator directly.")


def main(short=False):
    v = values()
    R = rows(v)
    if short:
        out = ["| function | source | status |", "|---|---|---|"]
        out += [f"| {f} | **{s}** | {st} |" for f, s, _, st in R]
    else:
        out = ["| function | source | evidence | status |", "|---|---|---|---|"]
        out += [f"| {f} | **{s}** | {e} | {st} |" for f, s, e, st in R]
        out += ["", READING]
    out += ["", NOTE] if not short else []
    print("\n".join(out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--short", action="store_true")
    main(short=ap.parse_args().short)
