"""Smell circuit part 1/4 report (SPEC_SENSORY_INPUTS §3.4a): step-0 anatomy and the O1 table. Markdown to stdout.

Anatomy: recomputed from the FlyWire files by scripts/diag/so_anatomy.compute() (no simulation, ~3 s).
O1: read from logs/smell/o1/o1_r<rate>_s<seed>.npz (scripts/diag/so_o1.py), criteria as pre-registered:
PASS per seed iff AL and not-driven mean rate < 0.1 Hz in steps 44-47 (100-200 ms after the cut); a rate passes iff 5/5.

    env -u PYTHONPATH python scripts/diag/o1_report.py [--dir logs/smell/o1]
"""
import argparse
import glob
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "diag"))
import so_anatomy  # noqa: E402
import so_o1  # noqa: E402

DNS = [("DNa02", "DNa02"), ("DNae001", "DNae001 (hemibrain name DNa01, the literature steering DN; mapping UNVERIFIED)"),
       ("DNa01", "DNa01 (FlyWire name; hemibrain type VES006)"), ("DNa15", "DNa15"), ("DNb01", "DNb01"),
       ("DNp03", "DNp03"), ("DNae002", "DNae002 (hemibrain name DNa04)"), ("DNa04", "DNa04 (FlyWire name)"),
       ("DNae004", "DNae004 (hemibrain name DNa05)"), ("DNa05", "DNa05 (FlyWire name)")]


def o1_rows(d):
    """{rate: [per-seed dicts]} from the npz files."""
    rows = {}
    for f in sorted(glob.glob(f"{d}/o1_r*_s*.npz")):
        z = np.load(f)
        r, nd = float(z["rate"]), int(z["n_drive"])
        assert nd == so_o1.N_DRIVE
        rec = {"seed": int(z["seed"]), "n_food": int(z["n_food_driven"])}
        for p in ("AL", "not_driven"):
            rec[f"W1_{p}"] = float(z[f"pop_{p}"][slice(*so_o1.W1)].mean())
            rec[f"W2_{p}"] = float(z[f"pop_{p}"][slice(*so_o1.W2)].mean())
        rec["pass"] = rec["W1_AL"] < so_o1.THR and rec["W1_not_driven"] < so_o1.THR
        for p in ("ALPN", "PN_uni"):
            rec[f"drive_{p}"] = float(z[f"pop_{p}"][slice(*so_o1.PN_WIN)].mean())
        rows.setdefault(r, []).append(rec)
    return rows


def o1_summary(rows):
    pn = [np.mean([x["drive_ALPN"] for x in rows[r]]) for r in sorted(rows)]
    npass = {r: sum(x["pass"] for x in rows[r]) for r in rows}
    passing = [r for r in sorted(rows) if npass[r] == len(rows[r]) == 5]
    return dict(npass=npass, passing=passing, pn_inversions=int(sum(b < a for a, b in zip(pn, pn[1:]))),
                n_runs=sum(len(v) for v in rows.values()), n_seeds=sorted({x["seed"] for v in rows.values() for x in v}))


def anatomy_lines():
    a = so_anatomy.compute()
    o, s = a["a_orn"], a["a_orn"]["orn_to_pn_synapses"]
    t = o["total"]
    per = ", ".join("%s %d/%d" % (g, v["L"], v["R"]) for g, v in o["per_glomerulus"].items())
    L = [f"- Food-glomerulus ORNs: {t['L']} left / {t['R']} right = {t['L'] + t['R']} ({per})."]
    for key, lab in (("food_ORN->all_ALPN", "food ORNs → all ALPN"),
                     ("food_ORN->uniglomerular_ALPN", "food ORNs → uniglomerular ALPN"),
                     ("all_53_glomeruli_ORN->all_ALPN", "all 53 glomeruli → all ALPN")):
        x = s[key]
        L.append(f"- ORN → PN synapses, {lab}: ipsilateral {x['ipsi']:,} / contralateral {x['contra']:,} = "
                 f"{x['ipsi_over_contra']:.2f} (ipsilateral {x['ipsi_excess_pct']:+.1f} %), {x['n_pn_targets']} target PNs.")
    L.append("- Ipsilateral / contralateral ratio by glomerulus (ORN → all ALPN): " + ", ".join(
        f"{g} {v['ipsi_over_contra']:.2f}" for g, v in o["per_glomerulus_ipsi_over_contra"].items()) + ".")
    L += ["", "| descending-neuron type | model DN list: cells (L / R) | note |", "|---|---|---|"]
    b = a["b_dn"]
    for q, lab in DNS:
        ex = b[q]["model_DN_list_exact"]
        L.append(f"| {lab} | {ex.get('left', 0)} / {ex.get('right', 0)} | |")
    g = b["DNg02"]["model_DN_list_prefix_types"]
    L.append(f"| DNg02 (sub-types DNg02_a … DNg02_h) | {sum(v.get('left', 0) for v in g.values())} / "
             f"{sum(v.get('right', 0) for v in g.values())} | no cell is named plain DNg02 |")
    L.append(f"| DNae014 | {b['DNae014']['annotations_cell_type_or_hemibrain_type']['n']} / 0 | not in the annotations (UNVERIFIED) |")
    c = a["c_paths"]
    top = c["fraction_of_shortest_paths_through_type_at_any_intermediate_hop"]
    L += ["", f"- Shortest ORN → DNa02 path (food ORNs, edges ≥ {a['syn_min_graph']} synapses): {c['min_hops']} hops, "
          f"{c['n_shortest_paths_total']:.0f} shortest paths; most frequent intermediate types "
          + ", ".join(f"`{k}` {100 * v:.0f} %" for k, v in list(top.items())[:3]) + ".",
          f"- Fraction of the shortest paths through Kenyon cells: {100 * c['fraction_through_KC']:.0f} %; "
          f"through MBON32: {100 * c['fraction_through_MBON32']:.0f} %."]
    return L


def main(dir=str(ROOT / "logs" / "smell" / "o1")):
    d = dir
    rows = o1_rows(d)
    sm = o1_summary(rows)
    print("\n".join(anatomy_lines()))
    print()
    print("| drive rate (Hz) | seeds passing | AL after the cut, 100–200 ms (Hz, min–max) | "
          "not-driven after the cut, 100–200 ms (Hz, min–max) | AL, 400–500 ms (Hz, mean) | "
          "not-driven, 400–500 ms (Hz, mean) | ALPN during the drive (Hz, mean) | uniglomerular PN during the drive (Hz, mean) |")
    print("|---|---|---|---|---|---|---|---|")
    for r in sorted(rows):
        L = rows[r]
        f = lambda k: [x[k] for x in L]  # noqa: E731
        print(f"| {r:.1f} | {sm['npass'][r]}/{len(L)} | {min(f('W1_AL')):.1f}–{max(f('W1_AL')):.1f} | "
              f"{min(f('W1_not_driven')):.2f}–{max(f('W1_not_driven')):.2f} | {np.mean(f('W2_AL')):.1f} | "
              f"{np.mean(f('W2_not_driven')):.2f} | {np.mean(f('drive_ALPN')):.1f} | {np.mean(f('drive_PN_uni')):.1f} |")
    print()
    n = len(rows)
    print(f"- **O1 result: {len(sm['passing'])} of {n} drive rates pass in 5/5 seeds** ({sm['n_runs']} runs, seeds "
          f"{', '.join(map(str, sm['n_seeds']))}); the lowest rate ({min(rows):g} Hz) already fails in "
          f"{len(rows[min(rows)]) - sm['npass'][min(rows)]}/{len(rows[min(rows)])} seeds.")
    print(f"- ALPN response over the drive rates: {sm['pn_inversions']} inversions in the seed mean "
          f"({np.mean([x['drive_ALPN'] for x in rows[min(rows)]]):.1f} → "
          f"{np.mean([x['drive_ALPN'] for x in rows[max(rows)]]):.1f} Hz over a {max(rows) / min(rows):.0f}-fold range of drive).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "logs" / "smell" / "o1"))
    main(ap.parse_args().dir)
