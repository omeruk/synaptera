"""Smell part 2/4 report (SPEC_SENSORY_INPUTS §3.4b): audit tables, O1 under the NT variants next to the published model, O2 and
robustness records if they were run. Markdown to stdout. Everything is recomputed from the repository files and logs/smell/*.

    env -u PYTHONPATH .../python scripts/diag/nt_report.py [--logs logs/smell]
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "diag"))
import nt_audit  # noqa: E402
import o1_report  # noqa: E402
import so_o2  # noqa: E402

LABEL = {"published": "published model", "N1": "MODEL VARIANT N1, not the published model",
         "N2": "MODEL VARIANT N2, not the published model"}


def audit_md(brief=False):
    rid, con, ann = nt_audit.load()
    return nt_audit.md(nt_audit.audit_a(ann), nt_audit.audit_b(ann), nt_audit.audit_c(ann), nt_audit.audit_d(rid, con, ann), brief=brief)


def o1_tables(logs):
    L, summ = [], {}
    for v, d in (("published", "o1"), ("N1", "o1_N1"), ("N2", "o1_N2")):
        p = os.path.join(logs, d)
        rows = o1_report.o1_rows(p) if os.path.isdir(p) else {}
        if not rows:
            continue
        sm = o1_report.o1_summary(rows)
        summ[v] = sm
        L += [f"**O1, {LABEL[v]}** ({sm['n_runs']} runs, seeds {sm['n_seeds'][0]}–{sm['n_seeds'][-1]}):", "",
              "| drive rate (Hz) | seeds passing | AL after the cut, 100–200 ms (Hz, min–max) | not-driven after the cut, 100–200 ms (Hz, min–max) | AL, 400–500 ms (Hz, mean) | not-driven, 400–500 ms (Hz, mean) | ALPN during the drive (Hz, mean) |",
              "|---|---|---|---|---|---|---|"]
        for r in sorted(rows):
            x = rows[r]
            f = lambda k: [y[k] for y in x]  # noqa: E731
            L.append(f"| {r:.1f} | {sm['npass'][r]}/{len(x)} | {min(f('W1_AL')):.3f}–{max(f('W1_AL')):.3f} | "
                     f"{min(f('W1_not_driven')):.3f}–{max(f('W1_not_driven')):.3f} | {np.mean(f('W2_AL')):.3f} | "
                     f"{np.mean(f('W2_not_driven')):.3f} | {np.mean(f('drive_ALPN')):.1f} |")
        L += ["", f"- {LABEL[v]}: **{len(sm['passing'])} of {len(rows)} rates pass in 5/5 seeds**"
              + (f" ({', '.join(f'{r:g}' for r in sm['passing'])} Hz)" if sm["passing"] else "") + ".", ""]
    return L, summ


def o2_lines(logs):
    L = []
    for v in ("N1", "N2", "published"):
        d = os.path.join(logs, f"o2_{v}")
        if not os.path.isdir(d):
            continue
        r = so_o2.report(d)
        L += [f"**O2, {LABEL[v]}**, drive {r.get('rate')} Hz (complete: {r.get('complete')}):", ""]
        L += ["| DN type (validation seeds 301–305) | (i) L>R in L-only and R>L in R-only, 5/5 | (ii) symmetric |L−R|/(L+R) < 0.2, 5/5 | (iii) no input |L−R| < 0.1 Hz, 5/5 | supported |", "|---|---|---|---|---|"]
        for t, c in list(r["confirmatory"].items()) + [("DNa01 (FlyWire name, reported separately)", r["flywire_DNa01_reported_separately"])]:
            L.append(f"| {t} | {c['i']} | {c['ii']} | {c['iii']} | {c['supported']} |")
        L += ["", "Per-seed DNa02 rates (Hz, left / right):", "", "| seed | L-only | R-only | symmetric | no input |", "|---|---|---|---|---|"]
        for s, p in r["confirmatory"]["DNa02"]["per_seed"].items():
            L.append(f"| {s} | " + " | ".join(f"{p[c][0]:.1f} / {p[c][1]:.1f}" for c in so_o2.CONDS) + " |")
        e = r["exploratory"]
        L += ["", f"Exploratory sweep (discovery seeds 201–203; new hypotheses, not confirmed): {e['n_consistent']} of {e['n_types']} DN types have the "
              "right sign in both one-sided conditions in all 3 seeds; ranking by mean |L−R|/(L+R): "
              + ", ".join(f"{x['type']} {x['mean_effect']:.2f}" for x in e["ranking"][:15]) + ".", ""]
        if "null" in r:
            L += ["Null control (5 degree-preserving shuffled connectomes, seeds 401–405):"]
            for t, n in r["null"].items():
                L.append(f"- {t}: reproduced in {n['n_reproduce']} of {n['n_done']} shuffles.")
            L.append("")
    return L


def robust_lines(logs):
    p = os.path.join(logs, "robust", "robust.json")
    if not os.path.exists(p):
        return []
    r = json.load(open(p))
    L = ["| model | (i) no input: network rate, last 200 ms (Hz, seeds 501/502/503) | silent | (ii) sugar 100 Hz → MN9 mean (Hz, seeds 501/502/503) | MN9 > 10 Hz |", "|---|---|---|---|---|"]
    for v, x in r.items():
        i, ii = x["i_no_input"], x["ii_sugar_mn9"]
        last = " / ".join("%.3f" % q["last200ms_hz"] for q in i)
        mn9 = " / ".join("%.1f" % q["mean_hz"] for q in ii)
        L.append(f"| {LABEL[v]} | {last} | {all(q['silent'] for q in i)} | {mn9} | {all(q['above_threshold'] for q in ii)} |")
    return L


def main(logs=str(ROOT / "logs" / "smell"), part="all", brief=True):
    """brief: the audit prints 15 LN types and 10 inconsistent types (the form used in REPORT.md); --full prints all."""
    if part in ("all", "audit"):
        print(audit_md(brief))
        print()
    if part in ("all", "o1"):
        print("\n".join(o1_tables(logs)[0]))
    if part in ("all", "o2"):
        print("\n".join(o2_lines(logs)))
    if part in ("all", "robust"):
        print("\n".join(robust_lines(logs)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default=str(ROOT / "logs" / "smell"))
    ap.add_argument("--part", choices=["all", "audit", "o1", "o2", "robust"], default="all")
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    main(a.logs, a.part, not a.full)
