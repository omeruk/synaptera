"""Vision screen (SPEC_SENSORY_INPUTS §3.5): mechanical application of the pre-registered criteria to the raw run files.

    python scripts/diag/vis_dn_report.py --directions docs/vis_dn_directions.json   # discovery seeds only
    python scripts/diag/vis_dn_report.py --report --out logs/vis_dn/report.json [--md logs/vis_dn/report.md]

Raw records: logs/vis_dn/{main,null}/vd_c{cond}_s{seed}.npz (per-step spike counts of all 1,299 DNs), rendered input
check logs/vis_dn/vd_input_check.json. Window = steps 28-59 (200-1000 ms after onset, 0.8 s).
"""
import argparse
import glob
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

LOGS = os.path.join(_ROOT, "logs", "vis_dn")
DISC, VAL, NULL = [501, 502, 503], [601, 602, 603, 604, 605], [801, 802, 803, 804, 805]
WIN, T_WIN = (28, 60), 0.8
DN_CSV = os.path.join(_ROOT, "brain_model", "descending_neurons.csv")
COND_NAMES = {1: "yaw-CW", 2: "yaw-CCW", 3: "static", 4: "loom-L", 5: "loom-R", 6: "loom-front", 7: "recede-L",
              8: "recede-R", 9: "exp. flow", 10: "grey"}
MEASURES = ("D", "R", "S", "Dfront", "Dflow")
THR = {"D": 0.10, "S": 0.10, "R": 1.0, "Dfront": 1.0, "Dflow": 1.0}
UNIT = {"D": "", "S": "", "R": " Hz", "Dfront": " Hz", "Dflow": " Hz"}
# a-priori (cluster, measure) tests, SPEC §3.5
APRIORI = ([("DNg02", "D", "H1")] + [(c, "D", "H2") for c in ("DNa04", "DNa05", "DNp15", "DNb01")]
           + [(c, m, "H3") for c in ("DNp03", "DNp01", "DNp02", "DNp04", "DNp06", "DNp11") for m in ("R", "S")]
           + [(c, m, "H4") for c in ("DNp07", "DNp10") for m in ("Dfront", "Dflow")])
CLUSTERS = ["DNg02", "DNa04", "DNa05", "DNp15", "DNb01", "DNp03", "DNp01", "DNp02", "DNp04", "DNp06", "DNp11", "DNp07", "DNp10"]


def dn_table():
    from flight import groups as G
    r2i = G.root_to_index(G.load_root_ids())
    dn = pd.read_csv(DN_CSV)
    return dn[dn["root_id"].isin(r2i)].reset_index(drop=True)


def units(dn):
    """{unit name: (mask L, mask R, mask all, kind)}: the 13 a-priori clusters, then every DN type."""
    side = dn["side"].astype(str).to_numpy()
    ct = dn["cell_type"].astype(str).to_numpy()
    out = {}

    def add(name, m, kind):
        out[name] = (m & (side == "left"), m & (side == "right"), m, kind)
    add("DNg02", pd.Series(ct).str.fullmatch(r"DNg02_[a-h]").to_numpy(), "cluster")
    for c in CLUSTERS[1:]:
        add(c, ct == c, "cluster")
    for t in sorted(set(ct)):
        add("type:" + t, ct == t, "type")
    return out


def load(d, seeds, conds, win=WIN):
    """{seed: {cond: (n_dn,) window spike counts}}; missing files are skipped."""
    res = {}
    for s in seeds:
        for c in conds:
            f = f"{LOGS}/{d}/vd_c{c:02d}_s{s}.npz"
            if os.path.exists(f):
                res.setdefault(s, {})[c] = np.load(f)["dn_counts"][win[0]:win[1]].sum(0).astype(float)
    return res


def rates_of(win_counts, U, t_win=T_WIN):
    """Per unit and seed-cond: (all, L, R) per-neuron Hz."""
    r = {}
    for name, (mL, mR, mA, _) in U.items():
        r[name] = tuple(win_counts[m].sum() / (max(m.sum(), 1) * t_win) if m.any() else np.nan for m in (mA, mL, mR))
    return r


def asym(L, R):
    return (L - R) / (L + R + 1.0)


def effects(rc):
    """rc[cond] = (all, L, R) Hz of one unit in one seed -> {measure: value}, controls {name: value}."""
    A = lambda c: asym(rc[c][1], rc[c][2])  # noqa: E731
    r = lambda c: rc[c][0]  # noqa: E731
    eff = {"D": A(1) - A(2), "S": A(4) - A(5), "R": 0.5 * (r(4) + r(5)) - 0.5 * (r(7) + r(8)),
           "Dfront": r(6) - r(3), "Dflow": r(9) - r(3)}
    ctl = {"A3": A(3), "r3_minus_grey": (r(3) - r(10)) if 10 in rc else np.nan}
    return eff, ctl


def per_seed(d, seeds, U, conds):
    """{unit: {seed: (eff, ctl, rc)}} for the seeds with all needed conditions."""
    data = load(d, seeds, conds)
    out = {u: {} for u in U}
    for s, cc in data.items():
        if not all(c in cc for c in conds):
            continue
        rr = {c: rates_of(cc[c], U) for c in conds}
        for u in U:
            rc = {c: rr[c][u] for c in conds}
            out[u][s] = effects(rc) + (rc,)
    return out


def usable(U, name, measure):
    mL, mR = U[name][0], U[name][1]
    return (mL.any() and mR.any()) if measure in ("D", "S") else U[name][2].any()


def silent(disc, name):
    """SILENT iff the mean over the discovery seeds of the whole-cluster rate is < 1 Hz in every one of the 10 conditions."""
    seeds = list(disc[name])
    return all(np.nanmean([disc[name][s][2][c][0] for s in seeds]) < 1.0 for c in range(1, 11))


def key(name):
    return name if not name.startswith("type:") else name[5:]


def directions():
    dn = dn_table()
    U = units(dn)
    disc = per_seed("main", DISC, U, list(range(1, 11)))
    assert all(len(v) == 3 for v in disc.values()), "discovery incomplete"
    out = dict(window="steps 28-59", seeds=DISC, apriori={}, exploratory={}, screened=0)
    for cl, m, h in APRIORI:
        e = np.array([disc[cl][s][0][m] for s in DISC])
        mean = float(e.mean())
        out["apriori"][f"{cl}|{m}"] = dict(hypothesis=h, discovery_values=e.tolist(), discovery_mean=mean,
                                           direction=int(np.sign(mean)), silent=bool(silent(disc, cl)))
    excl = {(f"type:{c}", m) for c, m, _ in APRIORI if c != "DNg02"}
    cand = []
    screened = 0
    for name, (_, _, _, kind) in U.items():
        if kind != "type" or silent(disc, name):
            continue
        for m in MEASURES:
            if (name, m) in excl or not usable(U, name, m):
                continue
            e = np.array([disc[name][s][0][m] for s in DISC])
            screened += 1
            cand.append((-abs(float(e.mean())) / THR[m], key(name), m, e.tolist(), float(e.mean())))
    cand.sort(key=lambda x: (round(x[0], 12), x[1], x[2]))
    out["screened"] = screened
    out["n_types_nonsilent"] = int(sum(1 for n, u in U.items() if u[3] == "type" and not silent(disc, n)))
    for sc, t, m, e, mean in cand[:10]:
        out["exploratory"][f"{t}|{m}"] = dict(type=t, measure=m, score=-sc, discovery_values=e, discovery_mean=mean,
                                              direction=int(np.sign(mean)))
    return out


def judge(unit, m, direction, val, null, U, name):
    """Criteria 1-5 for one (unit, measure); direction fixed on the discovery seeds. Returns a dict."""
    v = np.array([val[name][s][0][m] for s in VAL if s in val[name]])
    ctl = np.array([val[name][s][1]["A3" if m in ("D", "S") else "r3_minus_grey"] for s in VAL if s in val[name]])
    res = dict(n_val=len(v), val_values=v.tolist(), val_mean=float(v.mean()) if len(v) else np.nan,
               n_same_sign=int((np.sign(v) == direction).sum()) if direction else 0)
    res["c2_sign_5of5"] = bool(direction != 0 and len(v) == 5 and res["n_same_sign"] == 5)
    res["c3_magnitude"] = bool(len(v) and abs(v.mean()) >= THR[m])
    res["control"] = float(abs(ctl.mean())) if len(ctl) else np.nan
    res["c4_control"] = bool(len(v) and abs(ctl.mean()) < abs(v.mean()))
    nv = np.array([null[name][s][0][m] for s in NULL if name in null and s in null[name]])
    res["null_values"] = nv.tolist()
    res["null_max_abs"] = float(np.abs(nv).max()) if len(nv) else np.nan
    res["c5_null"] = bool(len(nv) == 5 and abs(v.mean()) > np.abs(nv).max()) if len(v) else False
    res["null_pending"] = len(nv) < 5
    return res


def evaluate():
    """All a-priori tests and the exploratory candidates against validation and null. Returns a dict (JSON-able)."""
    dn = dn_table()
    U = units(dn)
    D = json.load(open(os.path.join(_ROOT, "docs", "vis_dn_directions.json")))
    val = per_seed("main", VAL, U, list(range(1, 11)))
    null = per_seed("null", NULL, U, list(range(1, 10)))
    n_null = max(len(v) for v in null.values())
    out = dict(window="steps 28-59 (200-1000 ms after onset)", n_val_seeds=max(len(v) for v in val.values()), n_null_seeds=n_null,
               apriori=[], exploratory=[], screened=D["screened"], n_candidates=len(D["exploratory"]))
    for cl, m, h in APRIORI:
        d = D["apriori"][f"{cl}|{m}"]
        row = dict(hypothesis=h, cluster=cl, measure=m, n_left=int(U[cl][0].sum()), n_right=int(U[cl][1].sum()),
                   discovery_mean=d["discovery_mean"], direction=d["direction"])
        if d["silent"]:
            row["result"] = "SILENT"
        else:
            row.update(judge(cl, m, d["direction"], val, null, U, cl))
            ok = row["c2_sign_5of5"] and row["c3_magnitude"] and row["c4_control"] and row["c5_null"]
            row["result"] = "PASS" if ok else "FAIL"
            row["failed"] = [n for n, k in (("sign 5/5", "c2_sign_5of5"), ("magnitude", "c3_magnitude"), ("control", "c4_control"),
                                            ("null", "c5_null")) if not row[k]]
        out["apriori"].append(row)
    for k, d in D["exploratory"].items():
        name = "type:" + d["type"]
        row = dict(cluster=d["type"], measure=d["measure"], n_left=int(U[name][0].sum()), n_right=int(U[name][1].sum()),
                   discovery_mean=d["discovery_mean"], direction=d["direction"], score=d["score"])
        row.update(judge(name, d["measure"], d["direction"], val, null, U, name))
        ok = row["c2_sign_5of5"] and row["c3_magnitude"] and row["c4_control"] and row["c5_null"]
        row["result"] = "PASS" if ok else "FAIL"
        row["failed"] = [n for n, kk in (("sign 5/5", "c2_sign_5of5"), ("magnitude", "c3_magnitude"), ("control", "c4_control"),
                                         ("null", "c5_null")) if not row[kk]]
        out["exploratory"].append(row)
    out["apriori_counts"] = {r: sum(x["result"] == r for x in out["apriori"]) for r in ("PASS", "FAIL", "SILENT")}
    out["exploratory_counts"] = {r: sum(x["result"] == r for x in out["exploratory"]) for r in ("PASS", "FAIL")}
    # per-condition cluster rates (Hz per neuron, mean over seeds), for the tables
    def cond_rates(data, conds):
        t = {}
        for cl in CLUSTERS:
            t[cl] = {c: [float(np.mean([data[cl][s][2][c][i] for s in data[cl]])) for i in range(3)] for c in conds
                     if all(c in data[cl][s][2] for s in data[cl])}
        return t
    out["rates_val"] = cond_rates(val, range(1, 11))
    out["rates_null"] = cond_rates(null, range(1, 10))
    return out


def fmt_md(r, chk):
    L = ["Input check (rendered boundary-layer rates, window 200-1000 ms): " + chk["verdict"], "",
         "| condition | A_in (T4a+T5a) | A_in (all boundary neurons) | mean rate L / R (Hz) |", "|---|---|---|---|"]
    for c in range(1, 11):
        x = chk["per_condition"][str(c)]
        L.append(f"| {c} {COND_NAMES[c]} | {x['A_in_T4aT5a']:+.3f} | {x['A_in_all']:+.3f} | {x['mean_L']:.2f} / {x['mean_R']:.2f} |")
    L += ["", f"A-priori tests ({len(r['apriori'])}): " + ", ".join(f"{k} {v}" for k, v in r["apriori_counts"].items()), "",
          "| H | cluster | L/R n | measure | direction (discovery) | discovery mean | validation mean | same sign | control | null max | result |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]

    def line(x, h=""):
        if x["result"] == "SILENT":
            return f"| {h} | {x['cluster']} | {x['n_left']}/{x['n_right']} | {x['measure']} | - | {x['discovery_mean']:+.3f} | - | - | - | - | SILENT |"
        u = UNIT[x["measure"]]
        why = f" ({', '.join(x['failed'])})" if x["result"] == "FAIL" and x["failed"] else ""
        nm = "pending" if x["null_pending"] else f"{x['null_max_abs']:.3f}"
        return (f"| {h} | {x['cluster']} | {x['n_left']}/{x['n_right']} | {x['measure']} | {'+' if x['direction'] > 0 else '-' if x['direction'] < 0 else '0'} "
                f"| {x['discovery_mean']:+.3f}{u} | {x['val_mean']:+.3f}{u} | {x['n_same_sign']}/{x['n_val']} | {x['control']:.3f} | {nm} | {x['result']}{why} |")
    L += [line(x, x["hypothesis"]) for x in r["apriori"]]
    L += ["", f"Exploratory screen: {r['screened']} (type, measure) pairs screened, {r['n_candidates']} candidates, "
          f"{r['exploratory_counts']['PASS']} pass.", "",
          "| type | L/R n | measure | direction | discovery mean | validation mean | same sign | control | null max | result |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in r["exploratory"]:
        s = line(x, "")
        L.append("|" + s[4:])
    return "\n".join(L)


def posthoc():
    """POST-HOC / EXPLORATORY looks added after the pre-registered result was known (not criteria, not passes)."""
    dn = dn_table()
    U = units(dn)
    rates = np.load(f"{LOGS}/vd_rates.npz")
    L = ["POST-HOC / EXPLORATORY (added after the results were known; not criteria, not passes)", "",
         "Rendered boundary-layer input, mean rate L / R (Hz) per window:", "",
         "| condition | 200-1000 ms | 800-1000 ms (steps 52-59) |", "|---|---|---|"]
    for c in range(1, 11):
        a, b = rates[f"c{c:02d}__vbnd_L"], rates[f"c{c:02d}__vbnd_R"]
        L.append(f"| {c} {COND_NAMES[c]} | {a[28:60].mean():.2f} / {b[28:60].mean():.2f} | {a[52:60].mean():.2f} / {b[52:60].mean():.2f} |")
    late = (52, 60)
    data = load("main", VAL, list(range(1, 11)), late)
    seeds = sorted(data)
    rr = {s: {c: rates_of(data[s][c], U, 0.2) for c in range(1, 11)} for s in seeds}
    L += ["", "Loom clusters, mean rate (Hz per neuron, both sides) in 800-1000 ms, mean over the validation seeds:", "",
          "| cluster | " + " | ".join(COND_NAMES[c] for c in (10, 3, 4, 5, 6, 7, 8)) + " |", "|---|" + "---|" * 7]
    for cl in ("DNp01", "DNp02", "DNp03", "DNp04", "DNp06", "DNp11", "DNp07", "DNp10"):
        L.append(f"| {cl} | " + " | ".join(f"{np.mean([rr[s][c][cl][0] for s in seeds]):.2f}" for c in (10, 3, 4, 5, 6, 7, 8)) + " |")
    full = load("main", VAL, list(range(1, 11)))
    types = [n for n, u in U.items() if u[3] == "type"]
    rf = {s: {c: rates_of(full[s][c], U) for c in range(1, 11)} for s in sorted(full)}
    L += ["", f"Number of the {len(types)} DN types with a mean rate >= 1 Hz (200-1000 ms, mean over validation seeds), per condition:", "",
          "| " + " | ".join(COND_NAMES[c] for c in range(1, 11)) + " |", "|" + "---|" * 10,
          "| " + " | ".join(str(sum(np.mean([rf[s][c][t][0] for s in rf]) >= 1.0 for t in types)) for c in range(1, 11)) + " |"]
    L += ["", "Per-condition rates of the two clusters that passed (Hz per neuron, left / right, mean over the validation seeds):", "",
          "| condition | DNp15 | DNbe001 |", "|---|---|---|"]
    for c in range(1, 11):
        cells = []
        for u in ("DNp15", "type:DNbe001"):
            cells.append(f"{np.mean([rf[s][c][u][1] for s in rf]):.2f} / {np.mean([rf[s][c][u][2] for s in rf]):.2f}")
        L.append(f"| {c} {COND_NAMES[c]} | {cells[0]} | {cells[1]} |")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--directions")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--posthoc", action="store_true")
    ap.add_argument("--loom-followup", action="store_true", help="SPEC §3.5b follow-up (scripts/diag/vl_report.py)")
    ap.add_argument("--out")
    ap.add_argument("--md")
    a = ap.parse_args(argv)
    if a.loom_followup:
        import vl_report
        return vl_report.main(a)
    if a.directions:
        d = directions()
        json.dump(d, open(a.directions, "w"), indent=1)
        print(f"wrote {a.directions}: {len(d['apriori'])} a-priori, {len(d['exploratory'])} candidates of {d['screened']} screened")
        return
    if a.posthoc:
        print(posthoc())
        return
    r = evaluate()
    chk = json.load(open(f"{LOGS}/vd_input_check.json"))
    if a.out:
        json.dump(r, open(a.out, "w"), indent=1, default=float)
    md = fmt_md(r, chk)
    if a.md:
        open(a.md, "w").write(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
