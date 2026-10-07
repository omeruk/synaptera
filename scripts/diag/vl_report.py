"""Vision follow-up (SPEC_SENSORY_INPUTS §3.5b): mechanical application of the pre-registered criteria to the raw run files.
Follow-up designed after the §3.8 results were known; new window, new seeds.

    python scripts/diag/vis_dn_report.py --loom-followup --directions docs/vl_directions.json   # discovery seeds only
    python scripts/diag/vis_dn_report.py --loom-followup --report --out logs/vis_loom/report.json --md logs/vis_loom/report.md

Raw records: logs/vis_loom/{disc,val,null}/vl_c{cond}_s{seed}.npz (per-step spike counts of all 1,299 DNs); input check
logs/vis_loom/vl_input_check.json. Windows (steps of 25 ms, onset = step 20): W_loom 48-55, W_rec 24-31, W_on 20-27 (0.2 s each).
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

import vis_dn_report as V  # noqa: E402

LOGS = os.path.join(_ROOT, "logs", "vis_loom")
DISC, VAL, NULL = [511, 512, 513], [611, 612, 613, 614, 615], [811, 812, 813, 814, 815]
WL, WR, WO, T_WIN = (48, 56), (24, 32), (20, 28), 0.2
CONDS, NULL_CONDS = [4, 5, 6, 7, 8, 11, 10], [4, 5, 6, 7, 8, 11]
NAMES = {4: "loom-L", 5: "loom-R", 6: "loom-front", 7: "recede-L", 8: "recede-R", 11: "recede-front", 10: "grey"}
THR = {"R": 1.0, "Rfront": 1.0, "S": 0.10}
LOOM_CL = ("DNp01", "DNp02", "DNp03", "DNp04", "DNp06", "DNp11")
APRIORI = ([(c, "R") for c in LOOM_CL] + [(c, "S") for c in LOOM_CL] + [(c, "Rfront") for c in LOOM_CL + ("DNp07", "DNp10")])
LABEL = "follow-up designed after the §3.8 results were known; new window, new seeds"


def load(d, seeds, conds):
    """{seed: {cond: (60, n_dn) counts}}; only complete seeds."""
    res = {}
    for s in seeds:
        cc = {}
        for c in conds:
            f = f"{LOGS}/{d}/vl_c{c:02d}_s{s}.npz"
            if os.path.exists(f):
                cc[c] = np.load(f)["dn_counts"].astype(float)
        if len(cc) == len(conds):
            res[s] = cc
    return res


def wrate(cnt, m, w):
    return cnt[w[0]:w[1]][:, m].sum() / (max(m.sum(), 1) * T_WIN) if m.any() else np.nan


def measures(cc, U, name):
    """Measures, onset-control pair and the (cond, window) rates of one unit in one seed."""
    mL, mR, mA, _ = U[name]
    r = lambda c, w: wrate(cc[c], mA, w)  # noqa: E731
    A = lambda c, w: V.asym(wrate(cc[c], mL, w), wrate(cc[c], mR, w))  # noqa: E731
    loom_lat, rec_lat = 0.5 * (r(4, WL) + r(5, WL)), 0.5 * (r(7, WR) + r(8, WR))
    eff = {"R": loom_lat - rec_lat, "S": A(4, WL) - A(5, WL), "Rfront": r(6, WL) - r(11, WR)}
    onset = {"R": (loom_lat, 0.5 * (r(7, WO) + r(8, WO)) if 7 in cc else np.nan),
             "Rfront": (r(6, WL), r(11, WO))}
    used = {"R": [r(4, WL), r(5, WL), r(7, WR), r(8, WR)], "S": [r(4, WL), r(5, WL)], "Rfront": [r(6, WL), r(11, WR)]}
    return eff, onset, used


def per_seed(d, seeds, U, conds, names):
    data = load(d, seeds, conds)
    return {n: {s: measures(cc, U, n) for s, cc in data.items()} for n in names}


def usable(U, name, m):
    return (U[name][0].any() and U[name][1].any()) if m == "S" else U[name][2].any()


def silent(disc, name, m):
    """SILENT iff the discovery mean is < 1 Hz in every (condition, window) pair the measure uses."""
    seeds = list(disc[name])
    return all(np.mean([disc[name][s][2][m][i] for s in seeds]) < 1.0 for i in range(len(disc[name][seeds[0]][2][m])))


def directions():
    U = V.units(V.dn_table())
    names = [n for n in U if n.startswith("type:")]                       # all types (a-priori clusters are types here)
    disc = per_seed("disc", DISC, U, CONDS, names)
    assert all(len(v) == 3 for v in disc.values()), "discovery incomplete"
    out = dict(windows=dict(W_loom="steps 48-55", W_rec="steps 24-31", W_on="steps 20-27"), seeds=DISC, label=LABEL,
               apriori={}, exploratory={})
    for c, m in APRIORI:
        e = np.array([disc["type:" + c][s][0][m] for s in DISC])
        out["apriori"][f"{c}|{m}"] = dict(discovery_values=e.tolist(), discovery_mean=float(e.mean()),
                                          direction=int(np.sign(e.mean())), silent=bool(silent(disc, "type:" + c, m)))
    excl = {("type:" + c, m) for c, m in APRIORI}
    cand, screened = [], 0
    for n in names:
        for m in ("R", "Rfront"):
            if (n, m) in excl or not usable(U, n, m) or silent(disc, n, m):
                continue
            e = np.array([disc[n][s][0][m] for s in DISC])
            screened += 1
            cand.append((-abs(float(e.mean())) / THR[m], n[5:], 0 if m == "R" else 1, m, e.tolist(), float(e.mean())))
    cand.sort(key=lambda x: (round(x[0], 12), x[1], x[2]))
    out["screened"] = screened
    for sc, t, _, m, e, mean in cand[:10]:
        out["exploratory"][f"{t}|{m}"] = dict(type=t, measure=m, score=-sc, discovery_values=e, discovery_mean=mean,
                                              direction=int(np.sign(mean)))
    return out


def judge(name, m, direction, val, null):
    v = np.array([val[name][s][0][m] for s in VAL if s in val[name]])
    res = dict(n_val=len(v), val_values=v.tolist(), val_mean=float(v.mean()) if len(v) else np.nan,
               n_same_sign=int((np.sign(v) == direction).sum()) if direction else 0)
    res["c2_sign_5of5"] = bool(direction != 0 and len(v) == 5 and res["n_same_sign"] == 5)
    res["c3_magnitude"] = bool(len(v) and abs(v.mean()) >= THR[m])
    if m in ("R", "Rfront"):
        lo = np.array([val[name][s][1][m][0] for s in val[name]])
        on = np.array([val[name][s][1][m][1] for s in val[name]])
        res["loom_rate"], res["onset_rate"] = float(lo.mean()), float(on.mean())
        res["c4_onset"] = bool(lo.mean() > on.mean())
    else:
        res["loom_rate"] = res["onset_rate"] = None
        res["c4_onset"] = True                                            # not applicable to S
    nv = np.array([null[name][s][0][m] for s in NULL if name in null and s in null[name]])
    res["null_values"] = nv.tolist()
    res["null_max_abs"] = float(np.abs(nv).max()) if len(nv) else np.nan
    res["c5_null"] = bool(len(nv) == 5 and len(v) and abs(v.mean()) > np.abs(nv).max())
    res["null_pending"] = len(nv) < 5
    ok = res["c2_sign_5of5"] and res["c3_magnitude"] and res["c4_onset"] and res["c5_null"]
    res["result"] = "PASS" if ok else "FAIL"
    res["failed"] = [n for n, k in (("sign 5/5", "c2_sign_5of5"), ("magnitude", "c3_magnitude"), ("onset control", "c4_onset"),
                                    ("null", "c5_null")) if not res[k]]
    if ok:
        if m == "S":
            res["label"] = "lateral position of the disc (not a claim of loom specificity)"
        elif direction > 0:
            res["label"] = "loom response (loom > receding)"
        else:
            res["label"] = "receding-preferring, not a loom response"
    return res


def evaluate():
    U = V.units(V.dn_table())
    D = json.load(open(os.path.join(_ROOT, "docs", "vl_directions.json")))
    names = ["type:" + c for c in LOOM_CL + ("DNp07", "DNp10")] + ["type:" + d["type"] for d in D["exploratory"].values()]
    val = per_seed("val", VAL, U, CONDS, names)
    null = per_seed("null", NULL, U, NULL_CONDS, names)
    out = dict(label=LABEL, n_val_seeds=max(len(v) for v in val.values()), n_null_seeds=max(len(v) for v in null.values()),
               apriori=[], exploratory=[], screened=D["screened"], n_candidates=len(D["exploratory"]))
    for c, m in APRIORI:
        d = D["apriori"][f"{c}|{m}"]
        row = dict(cluster=c, measure=m, n_left=int(U["type:" + c][0].sum()), n_right=int(U["type:" + c][1].sum()),
                   discovery_mean=d["discovery_mean"], direction=d["direction"])
        if d["silent"]:
            row["result"] = "SILENT"
        else:
            row.update(judge("type:" + c, m, d["direction"], val, null))
        out["apriori"].append(row)
    for d in D["exploratory"].values():
        n = "type:" + d["type"]
        row = dict(cluster=d["type"], measure=d["measure"], n_left=int(U[n][0].sum()), n_right=int(U[n][1].sum()),
                   discovery_mean=d["discovery_mean"], direction=d["direction"], score=d["score"])
        row.update(judge(n, d["measure"], d["direction"], val, null))
        out["exploratory"].append(row)
    out["apriori_counts"] = {r: sum(x["result"] == r for x in out["apriori"]) for r in ("PASS", "FAIL", "SILENT")}
    out["exploratory_counts"] = {r: sum(x["result"] == r for x in out["exploratory"]) for r in ("PASS", "FAIL")}
    # recorded, not criteria: validation-mean cluster rates per (condition, window), Hz per neuron
    data = load("val", VAL, CONDS)
    rec = {}
    for c in LOOM_CL + ("DNp07", "DNp10"):
        m = U["type:" + c][2]
        rec[c] = {f"{NAMES[k]}|{wn}": float(np.mean([wrate(cc[k], m, w) for cc in data.values()]))
                  for k in CONDS for wn, w in (("W_loom", WL), ("W_rec", WR), ("W_on", WO))}
    out["rates_val"] = rec
    return out


def fmt_md(r, chk):
    L = [f"Label: {LABEL}.", "", "Input check (rendered boundary-layer rates, W_loom = 700-900 ms): " + chk["verdict"], "",
         "| quantity | value | requirement |", "|---|---|---|",
         f"| loom-left, left eye / grey | {chk['driven_eye_loom_left_L']:.2f} Hz / {chk['grey_L']:.2f} Hz = {chk['ratio_left']:.1f}x | >= 3x |",
         f"| loom-right, right eye / grey | {chk['driven_eye_loom_right_R']:.2f} Hz / {chk['grey_R']:.2f} Hz = {chk['ratio_right']:.1f}x | >= 3x |",
         f"| A_in loom-left | {chk['A_in_loom_left']:+.3f} | > 0 expected; opposite signs, each >= 0.05 |",
         f"| A_in loom-right | {chk['A_in_loom_right']:+.3f} | < 0 expected |", ""]
    L += [f"A-priori tests ({len(r['apriori'])}): " + ", ".join(f"{k} {v}" for k, v in r["apriori_counts"].items()), "",
          "| cluster | L/R n | measure | direction (discovery) | discovery mean | validation mean | same sign | loom / onset rate (Hz) | null max | result |",
          "|---|---|---|---|---|---|---|---|---|---|"]

    def line(x):
        if x["result"] == "SILENT":
            return f"| {x['cluster']} | {x['n_left']}/{x['n_right']} | {x['measure']} | - | {x['discovery_mean']:+.3f} | - | - | - | - | SILENT |"
        u = " Hz" if x["measure"] != "S" else ""
        why = f" ({', '.join(x['failed'])})" if x["result"] == "FAIL" and x["failed"] else (f" - {x['label']}" if x["result"] == "PASS" else "")
        nm = "pending" if x["null_pending"] else f"{x['null_max_abs']:.3f}"
        on = "n/a" if x["loom_rate"] is None else f"{x['loom_rate']:.2f} / {x['onset_rate']:.2f}"
        dr = "+" if x["direction"] > 0 else "-" if x["direction"] < 0 else "0"
        return (f"| {x['cluster']} | {x['n_left']}/{x['n_right']} | {x['measure']} | {dr} | {x['discovery_mean']:+.3f}{u} "
                f"| {x['val_mean']:+.3f}{u} | {x['n_same_sign']}/{x['n_val']} | {on} | {nm} | {x['result']}{why} |")
    L += [line(x) for x in r["apriori"]]
    L += ["", f"Exploratory screen (EXPLORATORY): {r['screened']} (type, measure) pairs screened, {r['n_candidates']} candidates, "
          f"{r['exploratory_counts']['PASS']} pass.", "",
          "| type | L/R n | measure | direction | discovery mean | validation mean | same sign | loom / onset rate (Hz) | null max | result |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    L += [line(x) for x in r["exploratory"]]
    cols = [f"{NAMES[k]}|{w}" for k, w in ((4, "W_loom"), (5, "W_loom"), (6, "W_loom"), (7, "W_rec"), (8, "W_rec"), (11, "W_rec"),
                                          (7, "W_on"), (8, "W_on"), (11, "W_on"), (10, "W_loom"))]
    L += ["", "Recorded, not criteria: cluster rates (Hz per neuron, validation-seed mean) per condition and window:", "",
          "| cluster | " + " | ".join(c.replace("|", " ") for c in cols) + " |", "|---|" + "---|" * len(cols)]
    for c, d in r["rates_val"].items():
        L.append(f"| {c} | " + " | ".join(f"{d[k]:.2f}" for k in cols) + " |")
    return "\n".join(L)


def main(a):
    if a.directions:
        d = directions()
        json.dump(d, open(a.directions, "w"), indent=1)
        print(f"wrote {a.directions}: {len(d['apriori'])} a-priori, {len(d['exploratory'])} candidates of {d['screened']} screened")
        return
    r = evaluate()
    chk = json.load(open(f"{LOGS}/vl_input_check.json"))
    if a.out:
        json.dump(r, open(a.out, "w"), indent=1, default=float)
    md = fmt_md(r, chk)
    if a.md:
        open(a.md, "w").write(md + "\n")
    print(md)
