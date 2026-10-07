"""Smell comparison check report (SPEC_SENSORY_INPUTS §3.4c): upstream olfactory drive, step-0 counts and the open-loop decay result.
Markdown to stdout. Everything is recomputed from the repository files (the upstream script is parsed, never run) and logs/smell/o1_nf.

    env -u PYTHONPATH .../python scripts/diag/nf_report.py
"""
import ast
import hashlib
import heapq
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
UP = ROOT / "fly_brain_body_simulation.py"
BM = ROOT / "brain_model"
# keyword selections that reproduce the ones read at upstream lines 303 and 307 (hashes in CITED); built from keyword lists here
REGEX_OLF = "|".join(["olfactory", "olfactori", r"\born\b", "projection.neuron"])
REGEX_SEZ = "|".join(["sez", "fdg", "feeding", "subesophageal", "pharyngeal", "gustatory"])
FOOD = ("DM1", "DM2", "DM4", "VA2", "VM2", "DP1m")
# (line, SHA-256 of the stripped line) of the upstream lines that the Step-0 reading of REPORT.md §3.7 cites; checked by scripts/verify_report_final.py.
# The upstream text itself is not copied here: the hash shows that line N still is the line that was read.
CITED = [(303, "a88e804efdf940fd0fbd597c9eda6ef98089217396af9b5c9e4f5f082eb37e61"),
         (307, "f9754616d68baea958837da748029fdaba1f9667f93c61fc4beb92ace07f8f63"),
         (383, "c05027c5493a51d1bcedf44d8fc0e6ec53a27da76b343c243af948a43e687050"),
         (387, "66daa46c0dd51567d7ba8d18a4d9dd7e616d69f227d4254bce807589ba995580"),
         (412, "5367612ec70f8f4abf3d24f5b6e9b61d6d45911d597adecf2981fab80e7d9dbc"),
         (829, "0e10386475e4fdfb34186a2c6446db4be364583f78c034665efd0ebd74c3f818"),
         (831, "7945d8345134b810cbff46092249dd87b7d5e9b192ccd7e253f96d4c686c0aa5"),
         (832, "ed13bcb48ba7aaa005cb21eef16904e8e98b417caab4ddfb2d32fb42b91ea8fc"),
         (125, "5729e1f98a8c6780889ad28aebed6e53cdb99c4f643958f9bdbd6bb52cf17acb"),
         (166, "97ffa3cdf04a88a37e20a15698f264f36199efc64a85f03d7aea35161f313ee4"),
         (852, "f01d4568d4f23fe225ed871ece61f30f46c2b900f5b7af68357fa53ad40c263d")]


def cited_ok():
    """[(line, hash, matches)]; empty list if the upstream file is not present (public copy)."""
    if not UP.exists():
        return []
    L = UP.read_text().splitlines()
    return [(n, h, n <= len(L) and hashlib.sha256(L[n - 1].strip().encode()).hexdigest() == h) for n, h in CITED]


def _select(ann, pat):
    m = pd.Series(False, index=ann.index)
    for c in ("cell_class", "cell_type", "super_class"):
        m |= ann[c].astype(str).str.lower().str.contains(pat, na=False, regex=True)
    return m


def counts():
    comp = pd.read_csv(BM / "Completeness_783.csv", index_col=0)
    ann = pd.read_csv(BM / "flywire_annotations.tsv", sep="\t", low_memory=False)
    ann["idx"] = ann["root_id"].map({f: i for i, f in enumerate(comp.index)})
    mo, ms = _select(ann, REGEX_OLF), _select(ann, REGEX_SEZ)
    o = ann[mo & ann["idx"].notna()]
    orn = o["cell_type"].astype(str).str.startswith("ORN_")
    side = o["side"].astype(str).str.strip().str.lower()
    by_col = {c: int(ann[c].astype(str).str.lower().str.contains(REGEX_OLF, na=False, regex=True).sum())
              for c in ("cell_class", "cell_type", "super_class")}
    food = o["cell_type"].astype(str).str.replace("ORN_", "", regex=False).isin(FOOD) & orn
    sez = ann[ms & ann["idx"].notna()]
    dn = pd.read_csv(BM / "descending_neurons.csv")
    dns = dn["side"].astype(str).str.strip().str.lower()
    return dict(rows=int(mo.sum()), model=len(o), by_col=by_col, orn=int(orn.sum()), untyped=int((~orn).sum()),
                glom=int(o.loc[orn, "cell_type"].nunique()), L=int((side == "left").sum()), R=int((side == "right").sum()),
                U=int((~side.isin(["left", "right"])).sum()), food=int(food.sum()), sez=len(sez),
                overlap=len(set(o["idx"]) & set(sez["idx"])), union=len(set(o["idx"]) | set(sez["idx"])),
                dnL=int((dns == "left").sum()), dnR=int((dns == "right").sum()), dnC=int((~dns.isin(["left", "right"])).sum()),
                alpn_in_set=int((o["cell_class"].astype(str) == "ALPN").sum()))


def odor_field():
    """Spawn / food / min non-zero / max of the upstream odour field, from the upstream functions (parsed from the file, not run)."""
    if not UP.exists():
        return None            # upstream file not present (public copy): the odour-field line is not recomputed
    ns = {"np": np, "heapq": heapq}
    want = {"GRID_RES", "X_MIN", "X_MAX", "Y_MIN", "Y_MAX", "_ODOR_WALL_RECTS", "FOOD_POS"}
    for n in ast.parse(UP.read_text()).body:
        ok = isinstance(n, ast.FunctionDef) and n.name in ("build_odor_field", "lookup_odor")
        if isinstance(n, ast.Assign):  # also tuple targets such as `X_MIN, X_MAX = -1.0, 22.0`
            ok |= any(isinstance(e, ast.Name) and e.id in want for t in n.targets for e in (t.elts if isinstance(t, ast.Tuple) else [t]))
        if ok:
            exec(compile(ast.Module([n], []), str(UP), "exec"), ns)
    f, xs, ys, _ = ns["build_odor_field"](ns["FOOD_POS"][:2], x_range=(ns["X_MIN"], ns["X_MAX"]), y_range=(ns["Y_MIN"], ns["Y_MAX"]))
    lk = ns["lookup_odor"]
    return dict(spawn=lk(0.0, 0.0, f, xs, ys), food=lk(ns["FOOD_POS"][0], ns["FOOD_POS"][1], f, xs, ys),
                lo=float(f[f > 0].min()), hi=float(f.max()))


def nf_rows(d):
    p = ROOT / "logs" / "smell" / "o1_nf" if d is None else Path(d)
    return json.loads((p / "nf_summary.json").read_text())


def step0_lines(c=None, o=None):
    c = c or counts()
    o = o or odor_field()
    odour = [] if o is None else [
        f"- Upstream odour field at the antennae (computed from its own functions): {o['spawn']:.3f} at the spawn point, {o['hi']:.1f} at the food position "
        f"(the maximum), {o['lo']:.3f} the smallest non-zero value; none of these values is turned into a neuron rate.",
    ]
    return [
        f"- Upstream selection of \"olfactory\" neurons (regex of L303 over `cell_class`, `cell_type`, `super_class`): {c['rows']:,} annotation rows "
        f"({c['by_col']['cell_class']:,} by `cell_class`, {c['by_col']['cell_type']} by `cell_type`, {c['by_col']['super_class']} by `super_class`), "
        f"{c['model']:,} of them in the model: **{c['orn']:,} ORNs of {c['glom']} glomerulus types and {c['untyped']} olfactory-class cells without a cell type**; "
        f"{c['alpn_in_set']} projection neurons (ALPN) are in the set. Side (annotation): {c['L']:,} L / {c['R']:,} R / {c['U']} unknown; "
        f"the {c['food']} food-glomerulus ORNs of §3.7 are inside it.",
        f"- Same drive list also holds the SEZ/gustatory set of L307 ({c['sez']} neurons; overlap with the olfactory set {c['overlap']}): "
        f"{c['union']:,} neurons driven at one constant rate.",
        f"- Descending neurons read by the upstream turn command (L721–726): {c['dnL']} L / {c['dnR']} R / {c['dnC']} centre.",
    ] + odour


def result_lines(r):
    runs, sm = r["runs"], r["summary"]
    L = ["| seed | AL after the cut, 100–200 ms (Hz) | not-driven after the cut, 100–200 ms (Hz) | AL, 400–500 ms (Hz) | not-driven, 400–500 ms (Hz) | "
         "driven neurons, 100–200 ms (Hz) | ALPN during the drive (Hz) | uniglomerular PN during the drive (Hz) | driven neurons spiking, 100–200 ms | "
         "driven neurons spiking, 400–500 ms | pass |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in runs:
        L.append(f"| {x['seed']} | {x['W1_AL']:.1f} | {x['W1_not_driven']:.2f} | {x['W2_AL']:.1f} | {x['W2_not_driven']:.2f} | {x['W1_driven']:.2f} | "
                 f"{x['drive_ALPN']:.1f} | {x['drive_PN_uni']:.1f} | {100 * x['frac_driven_spiking_W1']:.1f} % | {100 * x['frac_driven_spiking_W2']:.1f} % | "
                 f"{'yes' if x['pass'] else 'no'} |")
    return L, sm


def main(dir=None):
    print("\n".join(step0_lines()))
    print()
    r = nf_rows(dir)
    L, sm = result_lines(r)
    print("\n".join(L))
    print()
    runs = r["runs"]
    al = [x["W1_AL"] for x in runs]
    nd = [x["W1_not_driven"] for x in runs]
    print(f"- **NeuroFly-style drive ({sm['rate_hz']:g} Hz, {runs[0]['n_driven']:,} neurons): {sm['n_pass']} of {sm['n']} seeds pass** "
          f"(seeds {', '.join(str(x['seed']) for x in runs)}); AL {min(al):.1f}–{max(al):.1f} Hz and not-driven network {min(nd):.2f}–{max(nd):.2f} Hz "
          f"100–200 ms after the cut, criterion < 0.1 Hz.")


if __name__ == "__main__":
    main()
