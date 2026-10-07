#!/usr/bin/env python
"""Recompute every number of REPORT_FINAL.md from the final_a/b/c HDF5 files and check the report; then the same
for REPORT_FINAL_V2.md (check_v2: behaviour / activity tables of §3 and §6.1 cell by cell, §6.2–6.3 against
scripts/diag/nat_report.py, video list §6.6 against ffprobe, §6.7 seeds against scripts/diag/seeds_report.py,
§6.8 against scripts/diag/starts_report.py); the O1 anatomy and table of REPORT.md §3.7 against scripts/diag/o1_report.py and its exploratory diagnostic against scripts/diag/o1_diag_report.py; the NT audit, the O1 tables under the sign variants and the robustness records against scripts/diag/nt_report.py; then README.md (English; check_readme); then REPORT.md (English,
consolidated report; check_report_en).

Language note: the Turkish strings in this file (table labels, section headings, units such as "adım", "yok", "temas hızı") are the labels of the
Turkish lab notebooks REPORT_FINAL.md and REPORT_FINAL_V2.md, which are matched verbatim; they are data, not messages. The English
reports (README.md, REPORT.md) are checked against the English output of the report scripts.

Numbers are recomputed from the behaviour arrays (not copied from meta); the meta turn_share is only
compared against the recomputation. Each value is formatted exactly as written in the report and must
appear there verbatim (key = what it is, value = the string).

    env -u PYTHONPATH python scripts/verify_report_final.py            # check, exit 1 on a mismatch
    env -u PYTHONPATH python scripts/verify_report_final.py --print    # only print the values
"""
import argparse
import json
import re
import sys
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
def _doc(name):
    """Turkish lab-notebook report: repository root, or docs/tr/ in the public snapshot."""
    p = ROOT / name
    return p if p.exists() else ROOT / "docs" / "tr" / name


REPORT = _doc("REPORT_FINAL.md")
TERMS = ("brain", "hand", "flyvis", "reflex")


def h5_of(name):
    """HDF5 of a final run: logs/final/DONE_<name> marker, else simulations/*_<name>_data.h5 (clean checkout)."""
    done = ROOT / "logs" / "final" / f"DONE_{name}"
    if done.exists():
        return ROOT / re.search(r"^h5=(.+)$", done.read_text(), re.M).group(1)
    (hit,) = sorted((ROOT / "simulations").glob(f"*_{name}_data.h5"))
    return hit


def metrics(path):
    f = h5py.File(path, "r")
    b = {k: f["behavior"][k][:] for k in f["behavior"]}
    meta = {k: f["meta"].attrs[k] for k in f["meta"].attrs}
    dt = float(meta["decision_interval"])
    t = b["t"]
    td = np.flatnonzero(b["phase"] == 4)
    k_td = int(td[0]) if len(td) else None
    pre = slice(0, k_td if k_td is not None else len(t))
    pen = np.flatnonzero(b["tower_penetration"][pre] > 0)
    feed = np.flatnonzero(b["is_feeding"] > 0)
    mn9 = np.flatnonzero(b["mn9_rate"] > 10.0)
    on = b["wings_on"] > 0
    s = {k: np.abs(b[f"turn_{k}"][on]).sum() for k in TERMS}
    tot = sum(s.values())
    ratio = np.abs(b["turn_brain"][on]).sum() / max(np.abs(b["turn_total"][on]).sum(), 1e-12)   # as brain_share()
    share_meta = json.loads(meta["turn_share"])
    for k in TERMS:     # recomputation must agree with what the simulation stored
        assert abs(s[k] / tot - share_meta[f"share_{k}"]) < 1e-9, (path.name, k)
    assert abs(ratio - share_meta["brain_over_total"]) < 1e-9
    s1 = k_td is not None and b["tower_contact"][pre].sum() == 0 and len(pen) == 0
    s2 = k_td is not None and len(feed) > 0 and feed[0] >= k_td
    out = {
        "n_steps": f"{len(t)}",
        "wings_on_steps": f"{int(on.sum())}",
        "touchdown_t": f"{t[k_td]:.2f} s" if k_td is not None else "yok",
        "touchdown_step": f"{k_td}" if k_td is not None else "yok",
        "touchdown_speed": f"{b['speed'][k_td]:.1f} mm/s" if k_td is not None else "—",
        "tower_contact_steps": f"{int(b['tower_contact'].sum())}",
        "pen_steps_pre_td": f"{len(pen)}",
        "pen_first": f"{int(pen[0])}" if len(pen) else "—",
        "pen_max_um": f"{b['tower_penetration'][pre].max(initial=0) * 1e3:.1f} µm",
        "S1": "✓" if s1 else "✗",
        "S2": "✓" if s2 else "✗",
        "mn9_first_t": f"{t[mn9[0]]:.2f} s" if len(mn9) else "—",
        "feed_steps": f"{len(feed)}",
        "feed_s": f"{len(feed) * dt:.2f} s",
        "mn9_mean_feed": f"{b['mn9_rate'][feed].mean():.1f} Hz" if len(feed) else "—",
        "d_min": f"{b['dist_to_food'].min():.1f} mm",
        "d_end": f"{b['dist_to_food'][-1]:.1f} mm",
        "ratio_brain_total": f"{ratio:.2f}",
        **{f"share_{k}": f"{s[k] / tot:.2f}" for k in TERMS},
        "turn_brain_unique": f"{len(np.unique(np.round(b['turn_brain'], 6)))}",
        "turn_brain_const": f"{b['turn_brain'][0]:+.3f}",
        "n_neurons": f"{int(meta['n_neurons']):,}".replace(",", "."),
        "seed": f"{int(meta['seed'])}",
        "peak_rss": f"{float(meta['peak_rss_gb']):.2f} GB",
    }
    f.close()
    return out


# ── REPORT_FINAL_V2.md ───────────────────────────────────────────────────────
REPORT_V2 = _doc("REPORT_FINAL_V2.md")
NUM = re.compile(r"[−+-]?\d[\d,]*(?:\.\d+)?")


def h5_any(name):
    """HDF5 of any final / final-v2 / naturalness run: DONE marker in logs/{natural,final_v2,final}, else the
    single simulations/*_<name>_data.h5."""
    for d in ("natural", "final_v2", "final"):
        done = ROOT / "logs" / d / f"DONE_{name}"
        if done.exists():
            return ROOT / re.search(r"^h5=(.+)$", done.read_text(), re.M).group(1)
    (hit,) = sorted((ROOT / "simulations").glob(f"*_{name}_data.h5"))
    return hit


def tokens(cell):
    """Numbers written in a report cell: (value, decimals); thousands separator ',' and the minus '−' allowed."""
    out = []
    for t in NUM.findall(cell):
        t2 = t.replace("−", "-").replace(",", "")
        out.append((float(t2), len(t2.split(".")[1]) if "." in t2 else 0))
    return out


def cell_ok(cell, want):
    """want: list of numbers (each must match a number of the cell at the precision written there), a string
    (substring), or None (cell must say there is no value)."""
    if want is None:
        return any(x in cell for x in ("—", "–", "yok", "none"))
    if isinstance(want, str):
        return want in cell
    tk = tokens(cell)
    return all(any(abs(v - w) <= 0.5 * 10.0 ** -d + 1e-9 for v, d in tk) for w in want)


def tables(text):
    """Markdown tables -> list of (column names, {row label: cells}); ** and spaces stripped."""
    out, lines = [], text.replace("\\|", "\x00").splitlines()      # escaped pipes stay inside their cell
    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith("|") and re.match(r"^\|[-|\s]+\|$", lines[i + 1]):
            cols = [c.strip().strip("*").strip().replace("\x00", "|") for c in lines[i].split("|")[1:-1]]
            rows = {}
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                c = [x.strip().replace("\x00", "|") for x in lines[j].split("|")[1:-1]]
                rows[c[0].strip("*").strip()] = [x.replace("**", "") for x in c[1:]]
                j += 1
            out.append((cols, rows))
            i = j
        else:
            i += 1
    return out


def v2_values(name):
    """Every per-run number of the REPORT_FINAL_V2 behaviour / activity tables, recomputed from the HDF5."""
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    from sb_report import Run as SRun        # noqa: E402  (activity: same definitions as fv2_report)
    p = h5_any(name)
    m = metrics(p)
    r = SRun(p)
    b = r.b
    on = b["wings_on"] > 0
    t = b["t"]
    td = np.flatnonzero(b["phase"] == 4)
    k_td = int(td[0]) if len(td) else None
    pre = slice(0, k_td if k_td is not None else len(t))
    pen = np.flatnonzero(b["tower_penetration"][pre] > 0)
    feed = np.flatnonzero(b["is_feeding"] > 0)
    mn9 = np.flatnonzero(b["mn9_rate"] > 10.0)
    sh = {k: float(m[f"share_{k}"]) for k in TERMS}
    tb = np.unique(np.round(b["turn_brain"], 6))
    act = {}
    for lab, msk in (("Toplam", np.ones(r.N, bool)), ("Sürülen girdi", r.driven), ("Sürülmeyen", ~r.driven)):
        a = int((r.count_cl[msk] > 0).sum())
        act[lab] = [a, int(msk.sum()), 100 * a / msk.sum()]
    und = ~r.driven
    v = {
        "touchdown": [t[k_td], k_td] if k_td is not None else None,
        "temas hızı": [b["speed"][k_td]] if k_td is not None else None,
        "kule teması (adım sonu)": [int(b["tower_contact"].sum())],
        "adım-içi kule (touchdown öncesi)": [len(pen)] + ([int(pen[0])] if len(pen) else []),
        "en büyük penetrasyon": [b["tower_penetration"][pre].max(initial=0) * 1e3],
        "S1": m["S1"], "S2": m["S2"],
        "MN9 ilk > 10 Hz": [t[mn9[0]]] if len(mn9) else None,
        "beslenme adımı": [len(feed)],
        "beslenmede ort. MN9": [b["mn9_rate"][feed].mean()] if len(feed) else None,
        "besine en yakın / son": [b["dist_to_food"].min(), b["dist_to_food"][-1]],
        "besine en yakın": [b["dist_to_food"].min()],
        "kanatlar açık": [int(on.sum())],
        **{f"pay {k.upper()}": [sh[k]] for k in TERMS},
        "pay HAND / REFLEX / FLYVIS / BRAIN": [sh["hand"], sh["reflex"], sh["flyvis"], sh["brain"]],
        "oran BRAIN/toplam": [float(m["ratio_brain_total"])],
        "turn_brain": [float(tb[0])] if len(tb) == 1 else "değişken",
        "yön terimi (BRAIN)": [float(tb[0])] if len(tb) == 1 else "değişken",
        "toplam yön değişimi (kanatlar açık)": [np.degrees(np.diff(np.unwrap(b["heading"]))[on[1:]].sum())],
        "ort. adım / beyin s": [b["step_time"].mean(), b["brain_time"].mean()],
        "tepe RSS": [float(r.meta["peak_rss_gb"])],
        "aktif nöron (toplam)": [act["Toplam"][2]],
        "sürülmeyen aktif / ort. Hz": [act["Sürülmeyen"][2], r.rate[und].mean()],
        "ağ ort. Hz": [r.rate.mean()],
        # §3 activity table
        "Toplam": act["Toplam"][::2], "Sürülen girdi": act["Sürülen girdi"], "Sürülmeyen": act["Sürülmeyen"],
        "Ağ ort. Hz": [r.rate.mean()], "Sürülmeyen ort. Hz": [r.rate[und].mean()],
    }
    return v


def nat_output():
    """stdout of scripts/diag/nat_report.py (regenerates §6 tables from the HDF5 files)."""
    import contextlib
    import io
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import nat_report                        # noqa: E402
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        nat_report.main()
    return buf.getvalue()


def video_probe(path):
    """(duration s, frames, fps, width x height, max key-frame interval in frames) via ffprobe."""
    import subprocess
    q = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                        "stream=width,height,r_frame_rate,nb_read_frames,pix_fmt:format=duration", "-of", "json",
                        str(path)], capture_output=True, text=True, check=True)
    j = json.loads(q.stdout)
    st = j["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    pk = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=flags",
                         "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout.split()
    keys = [i for i, f_ in enumerate(pk) if "K" in f_]
    gap = int(np.max(np.diff(keys + [len(pk)]))) if keys else 0
    return dict(duration=float(j["format"]["duration"]), frames=int(st["nb_read_frames"]),
                fps=float(num) / float(den), size=f"{st['width']}×{st['height']}", pix_fmt=st["pix_fmt"],
                key_gap=gap, n_keys=len(keys))


def check_v2(show=print):
    rep = REPORT_V2.read_text()
    bad = 0
    tabs = tables(rep)
    cache = {}

    def vals(n):
        if n not in cache:
            cache[n] = v2_values(n)
        return cache[n]

    # behaviour tables (§3 and §6.1) and the §3 activity table: every cell of every known row
    names = {"final_v2a", "final_v2c", "final_a", "final_b", "final_c", "final_sB", "n1", "n2"}
    n_cells = 0
    for cols, rows in tabs:
        runs = [c for c in cols[1:] if c in names]
        if len(runs) < 3 or len(runs) != len(cols) - 1:
            continue
        for lab, cells in rows.items():
            for n, cell in zip(runs, cells):
                want = vals(n).get(lab, "__skip__")
                if isinstance(want, str) and want == "__skip__":
                    continue
                if lab.startswith("adım-içi") and "adım" not in cell:
                    want = want[:1]                  # first in-step touch only where the cell names it
                ok = cell_ok(cell, want)
                n_cells += 1
                bad += not ok
                if not ok:
                    show(f"BAD v2 table [{lab}] {n}: report {cell!r}, recomputed {want!r}")
    show(f"{'ok ' if not bad else 'BAD'} v2 tables: {n_cells} cells checked")

    # §6.2 / §6.3: every number of the n1 / n2 bullets and the side-by-side tables of nat_report.py must be in §6
    s6 = rep[rep.index("## 6. Doğallık"):rep.index("## Sınırlamalar")]
    nat = nat_output()
    lines = [ln for ln in nat.splitlines() if re.match(r"^\s*- \*\*n[12]\*\*", ln)]
    miss = []
    for ln in lines:
        body = ln.split("**", 2)[-1]
        for t_ in NUM.findall(body):
            t2 = t_.lstrip("+")
            if t2 not in s6 and t2.replace("-", "−") not in s6:
                miss.append((ln.split("**")[1], t_))
    bad += len(miss)
    for n, t_ in miss:
        show(f"BAD §6 {n}: {t_!r} from nat_report not in the report")
    show(f"{'ok ' if not miss else 'BAD'} §6 bullets: {len(lines)} nat_report lines (n1/n2), numbers checked")
    # visual-input table (§6.3) against nat_report's table
    # nat_report writes the |L−R| label with bare pipes: escape them before parsing its table
    vis = next(((c, r) for c, r in tables(nat.replace("|L−R|", "\\|L−R\\|")) if "ort. L" in r), None)
    rv = next(((c, r) for c, r in tabs if "ort. L / R" in r), None)
    nv = 0
    if vis and rv:
        for lab_r, labs in (("ort. L / R", ("ort. L", "ort. R")), ("tip başına ort. |L−R|", ("ort. |L−R| (tip başına)",)),
                            ("T4/T5 L / R", ("T4/T5 L", "T4/T5 R"))):
            for n, cell in zip(rv[0][1:], rv[1][lab_r]):
                j = vis[0][1:].index(n)
                want = [float(vis[1][x][j]) for x in labs]
                ok = cell_ok(cell, want)
                nv += 1
                bad += not ok
                if not ok:
                    show(f"BAD §6.3 visual [{lab_r}] {n}: report {cell!r}, nat_report {want}")
    show(f"{'ok ' if vis and rv else 'BAD'} §6.3 visual table: {nv} cells")
    # DN table (§6.3) against nat_report's per-run window tables
    dn = {}
    cur = None
    for ln in nat.splitlines():
        mm = re.match(r"^\*\*(\S+)\*\* \(touchdown", ln)
        if mm:
            cur = mm.group(1)
        elif cur and ln.startswith("| ") and not ln.startswith("| |"):
            dn.setdefault(cur, {})[ln.split("|")[1].strip()] = [c.strip() for c in ln.split("|")[2:-1]]
        elif cur and ln.startswith("| |"):
            dn.setdefault(cur + "#cols", [c.strip() for c in ln.split("|")[2:-1]])
    rd = next(((c, r) for c, r in tabs if c[1:2] == ["n1 seyir"]), None)
    nd = 0
    win = {"seyir": "cruise", "yaklaşma": "approach", "alçalma": "descend"}
    rowmap = {"boyun MN": "neck MN"}
    if rd:
        for lab, cells in rd[1].items():
            for col, cell in zip(rd[0][1:], cells):
                n, w = col.split(" ")
                j = dn[n + "#cols"].index(win[w])
                want = [float(x) for x in dn[n][rowmap.get(lab, lab)][j].split(" / ")]
                ok = cell_ok(cell, want)
                nd += 1
                bad += not ok
                if not ok:
                    show(f"BAD §6.3 DN [{lab}] {col}: report {cell!r}, nat_report {want}")
    show(f"{'ok ' if rd else 'BAD'} §6.3 DN table: {nd} cells")
    # videos (§6.6): ffprobe numbers of every listed file
    vt = next(((c, r) for c, r in tabs if c[:2] == ["video", "dosya"]), None)
    if "### 6.6 Videolar" in rep:
        if vt is None:
            bad += 1
            show("BAD §6.6: video table missing")
        else:
            for lab, cells in vt[1].items():
                d = dict(zip(vt[0][1:], cells))
                path = ROOT / d["dosya"].strip("`")
                if not path.exists():
                    bad += 1
                    show(f"BAD video {lab}: {path} missing")
                    continue
                pr = video_probe(path)
                checks = {"süre": [pr["duration"]], "kare": [pr["frames"]], "fps": [pr["fps"]],
                          "anahtar kare aralığı": [pr["key_gap"]], "çözünürlük": pr["size"],
                          "piksel": pr["pix_fmt"]}
                for k, want in checks.items():
                    ok = k in d and cell_ok(d[k], want)
                    bad += not ok
                    show(f"{'ok ' if ok else 'BAD'} video {lab:12s} {k:22s} report {d.get(k)!r} ffprobe {want!r}")
        bad += check_video_prose(rep, show)
    if "### 6.7 Çok seed" in rep:
        bad += check_seeds(rep, show)
    if "### 6.8 Kalkış" in rep:
        bad += check_starts(rep, show)
    return bad


def check_seeds(rep, show):
    """§6.7: every table row, the S1/S2 + MN9 summary, the determinism lines and the B-K summary printed by
    scripts/diag/seeds_report.py (recomputed from the seed 10-14 HDF5 files) must appear verbatim in §6.7."""
    import contextlib
    import io
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import seeds_report                      # noqa: E402
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        seeds_report.main()
    end = rep.index("### 6.8 Kalkış") if "### 6.8 Kalkış" in rep else rep.index("## Sınırlamalar")
    s67 = rep[rep.index("### 6.7 Çok seed"):end]
    want = [ln for ln in buf.getvalue().splitlines()
            if re.match(r"^\| n[12] \|", ln) or re.match(r"^- \*\*n[12]\*\* ", ln) or re.match(r"^- \*\*n[12]\*\*: ", ln)]
    bad = 0
    for ln in want:
        ok = ln in s67
        bad += not ok
        if not ok:
            show(f"BAD §6.7 line not in the report: {ln!r}")
    show(f"{'ok ' if not bad else 'BAD'} §6.7 seeds: {len(want)} lines from seeds_report.py checked verbatim")
    return bad


def check_starts(rep, show):
    """§6.8 (SPEC §3.3f): every line printed by scripts/diag/starts_report.py (recomputed from the eight start
    runs and n1) must appear verbatim in REPORT_FINAL_V2 §6.8; the table rows and the S1/S2 summary lines must
    also appear verbatim in README.md."""
    import contextlib
    import io
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import starts_report                     # noqa: E402
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        starts_report.main()
    s68 = rep[rep.index("### 6.8 Kalkış"):rep.index("## Sınırlamalar")]
    lines = [ln for ln in buf.getvalue().splitlines() if ln.strip() and not ln.startswith("|---")]
    bad = 0
    for ln in lines:
        if ln not in s68:
            bad += 1
            show(f"BAD §6.8 line not found: {ln!r}")
    show(f"{'ok ' if not bad else 'BAD'} §6.8 starts: {len(lines)} lines from starts_report.py checked verbatim")
    return bad


def report_output(module, **kw):
    """stdout of scripts/diag/<module>.main(**kw)."""
    import contextlib
    import importlib
    import io
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        importlib.import_module(module).main(**kw)
    return buf.getvalue()


def negative_numbers():
    """Numbers of the negative findings shared by README.md and REPORT.md, recomputed: DN window rates of final_v2a
    (nat_report.py; windows of sb_report.Run.windows), the antennal-lobe persistent state of the smoke runs
    v17/v18/v20/v21 (network rate 100-200 ms after the input cut-off, meta persist_net_rate_hz[4:8]), the
    --nt-literature neuron count (meta nt_literature of v20/v21), the ORN glomerulus count, DNg02 spikes. {what: string as written}."""
    out = {}
    nat = nat_output()
    blk = nat[nat.index("**final_v2a** (touchdown"):]
    cols = [c.strip() for c in re.search(r"^\| \|(.+)\|$", blk, re.M).group(1).split("|")]
    row = lambda t: [float(x) for c in re.search(rf"^\| {t} \|(.+)\|$", blk, re.M).group(1).split("|")  # noqa: E731
                     for x in c.split(" / ")]
    d7, d10, d15 = row("DNp07"), row("DNp10"), row("DNp15")
    out["DNp07 range"] = f"({min(d7):.1f}–{max(d7):.1f} Hz per side)"
    l10, r10 = d10[0::2], d10[1::2]
    zero_l = [c for c, v in zip(cols, l10) if v == 0]
    assert max(r10) == 0 and zero_l == ["takeoff"], (r10, zero_l)
    n_to = int(re.search(r"takeoff (\d+)", blk).group(1))       # steps in the take-off window
    out["DNp10 sides"] = (f"(left {min(l10):.1f}–{max(l10):.1f} Hz, 0.0 only in the {n_to}-step take-off window; "
                          "right side 0.0 Hz in every window)")
    out["DNp15 perch"] = f"perch L {d15[0]:g} / R {d15[1]:g} Hz"
    pers, nt_changed = {}, set()
    for tag in ("v17", "v18", "v20", "v21"):
        (h,) = sorted((ROOT / "simulations").glob(f"flight_{tag}_*_data.h5"))
        with h5py.File(h, "r") as f:
            pr = f["meta"].attrs["persist_net_rate_hz"]
            pr = json.loads(pr) if isinstance(pr, str) else pr
            pers[tag] = float(np.mean(np.asarray(pr)[4:8]))           # 100-200 ms after the cut-off
            if tag in ("v20", "v21"):                                 # --nt-literature runs: neurons whose sign changed
                nt_changed.add(json.loads(f["meta"].attrs["nt_literature"])["n_neurons_changed"])
    out["AL persistent (spiking / graded)"] = (f"{pers['v17']:.2f} Hz (spiking APL, smoke run v17) and "
                                               f"{pers['v18']:.2f} Hz (graded APL, v18)")
    out["AL persistent (nt-literature)"] = f"{pers['v20']:.2f} Hz (v20) and {pers['v21']:.2f} Hz (v21)"
    import pandas as pd
    (n_nt,) = nt_changed
    out["nt-literature neurons"] = f"(`--nt-literature`, {n_nt} neurons)"
    out["ORN glomeruli"] = f"Spontaneous ORN input to the {len(pd.read_csv(ROOT / 'data' / 'orn_spontaneous_783.csv'))} glomeruli"
    tot = 0
    for n in ("final_a", "final_b", "final_c", "final_v2a", "final_v2c", "n1", "n2"):
        with h5py.File(h5_any(n), "r") as f:
            tot += int(f["behavior/dng02_L"][:].sum() + f["behavior/dng02_R"][:].sum())
    out["DNg02 total"] = tot
    return out


def o1_values():
    """Stage O1 (SPEC §3.4a) numbers shared by README.md and REPORT.md, recomputed from logs/smell/o1: {what: string}."""
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import o1_report as O                          # noqa: E402
    rows = O.o1_rows(str(ROOT / "logs" / "smell" / "o1"))
    sm = O.o1_summary(rows)
    al = [x["W1_AL"] for v in rows.values() for x in v]
    n, rs = len(rows), sorted(rows)
    return {"O1 rates": f"{len(sm['passing'])} of {n} drive rates ({rs[0]:g}–{rs[-1]:g} Hz)",
            "O1 AL range": f"AL {min(al):.1f}–{max(al):.1f} Hz 100–200 ms after the cut-off",
            "O1 neurons": f"driving only the {rows[rs[0]][0]['n_food']} food-glomerulus ORNs"}


def nt_values():
    """Smell part 2/4 (SPEC §3.4b) numbers shared by README.md and REPORT.md, recomputed from logs/smell/o1*, nt_report.py: {what: string}."""
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import o1_report as O                          # noqa: E402
    out, m = {}, {}
    for v, d in (("published", "o1"), ("N1", "o1_N1"), ("N2", "o1_N2")):
        rows = O.o1_rows(str(ROOT / "logs" / "smell" / d))
        sm = O.o1_summary(rows)
        assert sm["n_runs"] == 40 and not sm["passing"], (v, sm["n_runs"], sm["passing"])
        m[v] = np.mean([x["W1_AL"] for r in rows.values() for x in r])
    out["NT variants AL"] = f"about {m['published']:.0f} Hz published, {m['N1']:.0f} Hz N1, {m['N2']:.0f} Hz N2"
    out["NT variants rates"] = "0 of 8 drive rates"
    return out


def nf_values():
    """Comparison check (SPEC §3.4c) numbers shared by README.md and REPORT.md, recomputed from logs/smell/o1_nf and the upstream script: {what: string}."""
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import nf_report as N                          # noqa: E402
    import o1_report as O                          # noqa: E402
    r = N.nf_rows(None)
    runs, sm = r["runs"], r["summary"]
    c = N.counts()
    assert sm["n"] == 5 and sm["n_pass"] == 0 and not sm["level_passes"], sm
    o1 = O.o1_rows(str(ROOT / "logs" / "smell" / "o1"))
    m = lambda k: np.mean([x[k] for x in runs])    # noqa: E731
    f85 = [x for x in o1[85.0]]
    fr = [x["frac_driven_spiking_W1"] for x in runs] + [x["frac_driven_spiking_W2"] for x in runs]
    return {"NF result": f"{sm['n_pass']} of {sm['n']} seeds",
            "NF set": f"{c['model']:,} olfactory-class neurons at a constant {sm['rate_hz']:g} Hz",
            "NF PN": f"the ALPN mean is {m('drive_ALPN'):.1f} Hz and the uniglomerular PN mean {m('drive_PN_uni'):.1f} Hz (seed means), against "
                     f"{np.mean([x['drive_ALPN'] for x in f85]):.1f} / {np.mean([x['drive_PN_uni'] for x in f85]):.1f} Hz at 85 Hz",
            "NF spiking": f"({100 * min(fr):.0f}–{100 * max(fr):.0f} % per seed)",
            "NF driven mean": f"driven-neuron mean about {np.mean([x['W1_driven'] for x in runs]):.1f} Hz"}


def vd_values():
    """Visual DN screen (SPEC §3.5) numbers shared by README.md and REPORT.md, recomputed from logs/vis_dn and docs/vis_dn_directions.json
    (scripts/diag/vis_dn_report.py): ({README phrase: string}, {REPORT phrase: string})."""
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import vis_dn_report as VD                     # noqa: E402
    r = VD.evaluate()
    c, ec = r["apriori_counts"], r["exploratory_counts"]
    n_ap = len(r["apriori"])
    assert n_ap == 21 and r["n_val_seeds"] == 5 and r["n_null_seeds"] == 5, (n_ap, r["n_val_seeds"], r["n_null_seeds"])
    ap = [x["cluster"] for x in r["apriori"] if x["result"] == "PASS"]
    ex = [x["cluster"] for x in r["exploratory"] if x["result"] == "PASS"]
    assert ap == ["DNp15"] and ex == ["DNbe001"], (ap, ex)
    n_c, n_s = r["n_candidates"], r["screened"]
    readme = {"VD a-priori": f"{n_ap} a-priori tests: {c['PASS']} passed ({ap[0]}",
              "VD fail/silent": f"{c['FAIL']} failed, {c['SILENT']} silent",
              "VD exploratory": f"{ec['PASS']} pass ({ex[0]}, flow versus static) among {n_c} candidates of {n_s} pairs"}
    report = {"VD summary": f"of {n_ap} a-priori tests (yaw, loom, landing clusters) {c['PASS']} passed ({ap[0]}, yaw; with a right-dominant static baseline), "
                            f"{c['FAIL']} failed and {c['SILENT']} were silent; the exploratory screen gave {ec['PASS']} pass ({ex[0]}, expanding flow versus a static grating) "
                            f"among {n_c} candidates of {n_s} pairs",
              "VD result": f"of {n_ap} a-priori tests, {c['PASS']} passed ({ap[0]}, yaw), {c['FAIL']} failed and {c['SILENT']} were silent; "
                           f"the exploratory screen of {n_s} (type, measure) pairs gave {n_c} candidates, of which {ec['PASS']} passed ({ex[0]}",
              "VD runs": "125 runs in about 40 minutes"}
    return readme, report


def vl_values():
    """Loom follow-up (SPEC §3.5b) numbers shared by README.md and REPORT.md, recomputed from logs/vis_loom and docs/vl_directions.json
    (scripts/diag/vl_report.py): ({README phrase: string}, {REPORT phrase: string})."""
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import vl_report as VL                         # noqa: E402
    r = VL.evaluate()
    c, ec = r["apriori_counts"], r["exploratory_counts"]
    n = len(r["apriori"])
    assert n == 20 and r["n_val_seeds"] == 5 and r["n_null_seeds"] == 5, (n, r["n_val_seeds"], r["n_null_seeds"])
    readme = {"VL result": f"{c['PASS']} of {n} a-priori tests passed, {c['FAIL']} failed, {c['SILENT']} silent; exploratory {ec['PASS']} pass "
                           f"among {r['n_candidates']} candidates of {r['screened']} pairs"}
    report = {"VL result": f"of {n} a-priori tests {c['PASS']} passed, {c['FAIL']} failed and {c['SILENT']} were silent; the exploratory screen of "
                           f"{r['screened']} (type, measure) pairs gave {r['n_candidates']} candidates, of which {ec['PASS']} passed",
              "VL runs": "86 runs, about 25 minutes", "VL §3.8 note": f"(0 of {n} passed, {c['SILENT']} silent)"}
    return readme, report


def check_ladder_stop(show=print):
    """Training ladder step 1 stopped after trial 1: the one verdict sentence (recomputed from the 12 validation flights by
    summary_report.verdict) appears in the SPEC note, the ledger, the pre-registration log, REPORT.md and README.md, and the
    deviation is named as such."""
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import summary_report as SM                    # noqa: E402
    vd = SM.verdict()
    bad = 0
    for f in ("SPEC_SENSORY_INPUTS.md", "docs/ladder_trials.md", "docs/PREREGISTRATION_LOG.md", "REPORT.md", "README.md"):
        t = " ".join((_doc(f) if f.startswith("SPEC_") else ROOT / f).read_text().split())
        for k, w in (("verdict", vd), ("deviation", "deviation from the pre-registration" if f != "README.md" else "a deviation from the pre-registration")):
            ok = w in t
            bad += not ok
            show(f"{'ok ' if ok else 'BAD'} {f} {k}: {w!r}")
    t = " ".join(_doc("SPEC_SENSORY_INPUTS.md").read_text().split())
    w = "stopping for futility was not a pre-registered rule"
    bad += w not in t
    show(f"{'ok ' if w in t else 'BAD'} SPEC note: {w!r}")
    return bad


def check_cited_lines(show=print):
    """The upstream line numbers cited in REPORT.md §3.7 (comparison check) still hold the quoted code."""
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import nf_report as N                          # noqa: E402
    bad = 0
    res = N.cited_ok()
    if not res:
        show("ok  upstream file not present, check skipped")
    for n, h, ok in res:
        bad += not ok
        show(f"{'ok ' if ok else 'BAD'} fly_brain_body_simulation.py L{n} has SHA-256 {h[:12]}…")
    return bad


def check_readme(show=print):
    """README.md (English). (1) Start-position test (SPEC §3.3f): table header, rows and summary lines of
    `starts_report.py --lang en`, verbatim. (2) Seed summary lines of `seeds_report.py --lang en`, verbatim.
    (3) Final-v1 and n1/n2 tables: every S1 / S2 / touchdown / feeding cell and the numbers in the note cells,
    recomputed from the HDF5 files (v2_values). (4) Numbers of the final-v2 bullets."""
    readme = (ROOT / "README.md").read_text()
    bad = 0
    st = report_output("starts_report", lang="en").splitlines()
    want = [ln for ln in st if re.match(r"^\| (condition|n1|st_\w+) \|", ln) or ln.startswith("- **S1 ∧ S2")
            or ln.startswith("- S1 ") or ln.startswith("- touchdown →") or ln.startswith("- route convergence")
            or re.match(r"^  - st_\w+: ", ln)]
    se = report_output("seeds_report", lang="en").splitlines()
    want_se = [ln for ln in se if re.match(r"^- \*\*n[12]\*\* \(seeds", ln)]
    for where, lines in (("starts_report --lang en", want), ("seeds_report --lang en", want_se)):
        n_bad = 0
        for ln in lines:
            if ln not in readme:
                n_bad += 1
                show(f"BAD README line from {where} not found: {ln!r}")
        show(f"{'ok ' if not n_bad else 'BAD'} README: {len(lines)} lines from {where} checked verbatim")
        bad += n_bad
    sm = [ln for ln in report_output("summary_report", short=True).splitlines() if ln.strip()]
    n_bad = sum(ln not in readme for ln in sm)
    for ln in sm:
        if ln not in readme:
            show(f"BAD README line from summary_report --short not found: {ln!r}")
    show(f"{'ok ' if not n_bad else 'BAD'} README: {len(sm)} lines from summary_report --short checked verbatim")
    bad += n_bad
    tabs = tables(readme)
    n_cells = 0

    def check(lab, n, cell, w):
        nonlocal bad, n_cells
        ok = cell_ok(cell, w)
        n_cells += 1
        bad += not ok
        if not ok:
            show(f"BAD README table [{lab}] {n}: README {cell!r}, recomputed {w!r}")

    # note-cell numbers per run (README wording, numbers recomputed)
    notes = {"final_a": lambda v: v["adım-içi kule (touchdown öncesi)"][1:] + v["en büyük penetrasyon"],
             "final_c": lambda v: v["adım-içi kule (touchdown öncesi)"][:1],
             "n1": lambda v: v["besine en yakın"] + v["toplam yön değişimi (kanatlar açık)"],
             "n2": lambda v: v["adım-içi kule (touchdown öncesi)"][1:] + v["kule teması (adım sonu)"]}
    seen = set()
    for cols, rows in tabs:
        if cols[0] == "run" and "S1" in cols and "S2" in cols:
            for lab, cells in rows.items():
                n = lab.split(" ")[0]                # "n1 (hybrid)" -> n1
                v = v2_values(n)
                d = dict(zip(cols[1:], cells))
                seen.add(n)
                check("S1", n, d["S1"], v["S1"])
                check("S2", n, d["S2"], v["S2"])
                if "touchdown" in d:
                    check("touchdown", n, d["touchdown"], v["touchdown"][:1] if v["touchdown"] else None)
                if "feeding steps" in d:
                    check("feeding steps", n, d["feeding steps"], v["beslenme adımı"])
                if n in notes:
                    check("note", n, d["note"], notes[n](v))
    miss = {"final_a", "final_b", "final_c", "n1", "n2"} - seen
    bad += len(miss)
    show(f"{'ok ' if not miss else 'BAD'} README tables: {n_cells} cells checked" + (f"; missing rows {miss}" if miss else ""))
    # final-v2 bullets
    va, vc = v2_values("final_v2a"), v2_values("final_v2c")
    prose = {"final_v2a touchdown": f"{va['touchdown'][0]:.2f} s", "final_v2a feeding": f"{va['beslenme adımı'][0]} feeding steps",
             "final_v2a first in-step": f"step {va['adım-içi kule (touchdown öncesi)'][1]}",
             "final_v2a penetration": f"{va['en büyük penetrasyon'][0]:.1f} µm",
             "final_v2c heading": f"{vc['toplam yön değişimi (kanatlar açık)'][0]:.1f}°".replace("-", "−"),
             "final_v2c S1 / S2": f"final_v2c (brain only): failed, S1 {vc['S1']}, S2 {vc['S2']}.",
             "final_v2a S1 / S2": f"final_v2a (hybrid): failed, S1 {va['S1']}, S2 {va['S2']}."}
    if vc["touchdown"] is None and vc["kule teması (adım sonu)"] == [0] and vc["adım-içi kule (touchdown öncesi)"] == [0]:
        prose["final_v2c no-touchdown note"] = "It touched no tower, but without touchdown S1 fails by definition."
    for k, w in prose.items():
        ok = w in readme
        bad += not ok
        show(f"{'ok ' if ok else 'BAD'} README {k:24s} {w!r}")
    # "Negative findings": every number, recomputed (same values as REPORT.md §4)
    neg = negative_numbers()
    nf = readme[readme.index("## Negative findings"):readme.index("## Limitations")]
    lg = __import__("pandas").read_csv(ROOT / "data" / "leg_sugar_grn_783.csv")
    sel = lg[lg["selected"]]
    want = {k: neg[k] for k in ("DNp07 range", "DNp10 sides", "DNp15 perch", "AL persistent (spiking / graded)",
                                "AL persistent (nt-literature)", "nt-literature neurons", "ORN glomeruli")}
    want["DNg02 silent"] = "(0 spikes)" if neg["DNg02 total"] == 0 else f"DNg02 total {neg['DNg02 total']} spikes"
    want["leg GRN count"] = f"when the {len(sel)} {'/'.join(sorted(sel['cell_type'].unique()))} neurons"
    o1 = o1_values()
    want["O1 rates"], want["O1 neurons"] = o1["O1 rates"], o1["O1 neurons"]
    want.update(nt_values())
    nfv = nf_values()
    want["NF result"], want["NF set"] = nfv["NF result"], nfv["NF set"]
    want.update(vd_values()[0])
    want.update(vl_values()[0])
    for k, w in want.items():
        ok = w in nf
        bad += not ok
        show(f"{'ok ' if ok else 'BAD'} README negative findings {k:34s} {w!r}")
    return bad


# ── REPORT.md (English) ──────────────────────────────────────────────────────
REPORT_EN = ROOT / "REPORT.md"
# English row label -> v2_values key (the Turkish labels of REPORT_FINAL_V2)
EN_ROWS = {
    "touchdown": "touchdown", "touchdown speed": "temas hızı",
    "tower contact, end of step (steps)": "kule teması (adım sonu)",
    "intra-step tower contact before touchdown (steps)": "adım-içi kule (touchdown öncesi)",
    "max. penetration": "en büyük penetrasyon", "S1": "S1", "S2": "S2", "MN9 first > 10 Hz": "MN9 ilk > 10 Hz",
    "feeding steps": "beslenme adımı", "mean MN9 while feeding": "beslenmede ort. MN9",
    "closest to food / final": "besine en yakın / son", "closest to food": "besine en yakın",
    "wings-on steps": "kanatlar açık", "turn shares HAND-MADE / REFLEX / FLYVIS / BRAIN": "pay HAND / REFLEX / FLYVIS / BRAIN",
    "ratio Σ|BRAIN| / Σ|total|": "oran BRAIN/toplam", "BRAIN steering term": "yön terimi (BRAIN)",
    "total heading change (wings on)": "toplam yön değişimi (kanatlar açık)",
    "active neurons (total)": "aktif nöron (toplam)", "undriven neurons: active / mean rate": "sürülmeyen aktif / ort. Hz",
    "network mean rate": "ağ ort. Hz",
}
RUNS_EN = ("final_a", "final_b", "final_c", "final_v2a", "final_v2c", "final_sB", "n1", "n2")
VIDEOS_EN = {"n1": "simulations/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change_en_vis.mp4",
             "n2": "simulations/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change_en_vis.mp4",
             "n1 | n2": "simulations/flight_n1_vs_n2_v2_compare_en_vis.mp4"}


def script_lines(argv, cwd=ROOT):
    """stdout lines of a report script run as a subprocess (same interpreter)."""
    import subprocess
    r = subprocess.run([sys.executable, *map(str, argv)], cwd=cwd, capture_output=True, text=True, check=True)
    return r.stdout.splitlines()


def report_en_prose():
    """Values written in the REPORT.md text, recomputed from the run files, the DN reference files, the report
    scripts and the code constants: {what: string that must appear verbatim}."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "brain_model"))
    from flight import config as cfg              # noqa: E402
    from flight import head_reflex as HR          # noqa: E402
    from flight import vnc_bridge as VB           # noqa: E402
    from model import default_params as P         # noqa: E402  (brain_model/model.py, Shiu et al.)
    from brian2 import Hz, mV, ms                 # noqa: E402
    from flight.brain import BRAIN_DT, DECISION_INTERVAL  # noqa: E402
    want = {}
    n1 = h5_any("n1")
    with h5py.File(n1, "r") as f:
        meta = f["meta"].attrs
        want["neurons"] = f"{int(meta['n_neurons']):,} neurons"
        want["connections"] = f"{int(meta['n_synapses']):,}"
        want["boundary layer"] = (f"{len(f['vision_boundary/types'])} boundary-layer types "
                                  f"({len(f['vision_boundary/idx_L']) + len(f['vision_boundary/idx_R']):,} neurons)")
        want["sugar contact"] = f"→ {float(meta['sugar_rate_contact']):g} Hz Poisson drive"
        n_syn = int(meta["n_synapses"])
    import pandas as pd                           # noqa: E402
    con = pd.read_parquet(ROOT / "brain_model" / "Connectivity_783.parquet", columns=["Connectivity"])
    assert len(con) == n_syn                      # one model synapse object per parquet row (neuron pair)
    want["connections / synapses"] = (f"{len(con):,}\n  connections (pre–post neuron pairs; weight = synapse count), "
                                      f"{int(con['Connectivity'].sum()):,} synapses in total")
    p = {k: float(P[k] / u) for k, u in (("v_0", mV), ("v_rst", mV), ("v_th", mV), ("t_mbr", ms), ("tau", ms),
                                          ("t_rfc", ms), ("t_dly", ms), ("w_syn", mV))}
    assert p["v_0"] == p["v_rst"]
    m = lambda x: f"{x:g}".replace("-", "−")    # noqa: E731
    want["LIF"] = (f"v0 = vrst = {m(p['v_0'])} mV, vth = {m(p['v_th'])} mV, τm = {p['t_mbr']:g} ms,\n"
                   f"  τsyn = {p['tau']:g} ms, refractory period {p['t_rfc']:g} ms, synaptic delay {p['t_dly']:g} ms, "
                   f"w_syn = {p['w_syn']:g} mV")
    want["dt / decision step"] = (f"dt = {float(BRAIN_DT / ms):g} ms; the brain and the body exchange data every "
                                  f"{float(DECISION_INTERVAL / ms):g} ms decision step")
    want["readout τ"] = f"low-pass filtered (τ = {VB.READOUT_TAU * 1e3:g} ms)"
    want["MN9 threshold"] = f"MN9 readout (2 CB0701 neurons) > {VB.MN9_THRESHOLD_HZ:g} Hz"
    dt_ms = float(DECISION_INTERVAL / ms)
    want["calibration / cut"] = (f"the first {cfg.CALIB_STEPS} decision steps (perch) calibrate the DN baselines; then "
                                 f"all brain inputs are cut\n  for {cfg.PERSIST_CUT_STEPS} steps "
                                 f"({cfg.PERSIST_CUT_STEPS * dt_ms:g} ms)")
    want["head reflex"] = (f"yaw gain {HR.G[0]:g}, roll/pitch gain {HR.G[1]:g}, angle limit "
                           f"±{np.degrees(HR.THETA_MAX):g}°, yaw reset saccade at {np.degrees(HR.YAW_RESET):g}°")
    assert HR.G[1] == HR.G[2]
    # DN reference rates (per-side normalisation of the steering readout)
    rsb = json.loads((ROOT / "data" / "dn_lr_reference_sB.json").read_text())["rates_hz"]["DNp15"]
    r45 = json.loads((ROOT / "data" / "dn_lr_reference.json").read_text())["rates_hz"]["DNp15"]
    want["DNp15 reference"] = (f"DNp15 L / R {rsb['L']:.1f} / {rsb['R']:.1f} Hz; T4/T5 reference "
                               f"{r45['L']:.1f} / {r45['R']:.1f} Hz")
    # final runs (prose)
    va, vc, vb = v2_values("final_v2a"), v2_values("final_v2c"), v2_values("final_b")
    want["v2a ablation constant"] = f"the constant became {va['yön terimi (BRAIN)'][0]:+.3f}"
    want["v1 ablation constant"] = f"instead of {vb['yön terimi (BRAIN)'][0]:+.3f}"
    pen_a = f"(step {va['adım-içi kule (touchdown öncesi)'][1]}, {va['en büyük penetrasyon'][0]:.1f} µm)"
    want["v2a penetration"] = pen_a
    want["v2a landing / feeding"] = (f"It landed at {va['touchdown'][0]:.2f} s and fed for "
                                     f"{va['beslenme adımı'][0]} steps")
    want["v2c circles"] = f"flew in circles ({vc['toplam yön değişimi (kanatlar açık)'][0]:.1f}°)".replace("-", "−")
    n2 = v2_values("n2")
    want["n2 tower"] = (f"step {n2['adım-içi kule (touchdown öncesi)'][1]} and stayed against it for the rest of the run "
                        f"({n2['kule teması (adım sonu)'][0]} contact steps)")
    v1 = v2_values("n1")
    want["n1 route"] = f"Its route was almost straight ({v1['toplam yön değişimi (kanatlar açık)'][0]:+.1f}°)"
    want["n1 feeding"] = (f"the fly fed for {v1['beslenme adımı'][0]} steps, {v1['besine en yakın'][0]:.1f} mm from "
                          "the food")
    # DNp15 validation: (a)/(c) from the open-loop report, (b) from the 12 closed-loop runs
    val = ROOT / "logs" / "v2" / "val"
    ol = "\n".join(script_lines([ROOT / "scripts/diag/a2_openloop.py", "--report",
                                 *[f"a2_openloop_vb_s{s}.npz" for s in (6, 7, 8)],
                                 "--dn-reference", ROOT / "data" / "dn_lr_reference_sB.json"], cwd=val))
    a_ = re.search(r"\(a\) optomotor sign: (\d+/\d+)", ol).group(1)
    c_ = re.search(r"\(c\) static \|turn\| < 0\.3: (\d+/\d+)", ol).group(1)
    runs_b = sorted((ROOT / "simulations").glob("flight_v*_v2val_data.h5"))
    assert len(runs_b) == 12, runs_b
    bb = "\n".join(script_lines([ROOT / "scripts/diag/a2b_perturb.py", *runs_b]))
    b_ = re.search(r"normal runs: b1 (\d+/\d+), b2 (\d+/\d+), b3 (\d+/\d+)", bb).groups()
    want["validation (a)"] = f"optomotor sign correct in {a_}"
    want["validation (b)"] = f"b1 {b_[0]}, b2 {b_[1]}, b3 {b_[2]}"
    want["validation (c)"] = f"|turn| < 0.3 in {c_}"
    # negative findings
    neg = negative_numbers()
    tot = neg["DNg02 total"]
    want["DNg02 silent"] = ("0 spikes in final_a, final_b, final_c, final_v2a, final_v2c, n1 and\n  n2"
                            if tot == 0 else f"DNg02 total {tot} spikes")
    want["DNp07 range"] = neg["DNp07 range"]
    want["DNp10 sides"] = neg["DNp10 sides"].replace("take-off window;", "take-off\n  window;")
    want["AL persistent (spiking / graded)"] = neg["AL persistent (spiking / graded)"]
    want["AL persistent (nt-literature)"] = neg["AL persistent (nt-literature)"]
    import pandas as pd
    lg = pd.read_csv(ROOT / "data" / "leg_sugar_grn_783.csv")
    sel = lg[lg["selected"]]
    want["leg GRN count"] = (f"the {len(sel)} leg sugar GRNs selected by connectivity (all "
                             f"{'/'.join(sorted(sel['cell_type'].unique()))})")
    sg = pd.read_csv(ROOT / "data" / "sugar_grn_783.csv")      # GRN set driven on tarsus-platform contact
    ann = pd.read_csv(ROOT / "brain_model" / "flywire_annotations.tsv", sep="\t", low_memory=False,
                      usecols=["root_id", "super_class", "cell_class", "cell_sub_class", "cell_type", "nerve"])
    a = ann[ann["root_id"].isin(sg["root_id"])]
    assert len(a) == len(sg)
    assert {tuple(r) for r in a.iloc[:, 1:].to_numpy()} == {("sensory", "gustatory", "sugar/water", "LB3", "MxLbN")}
    n_shiu = int((sg["source"] == "shiu2023").sum())
    want["labellar GRN set"] = (f"{len(sg)} labellar sugar gustatory receptor neurons (FlyWire annotations: sensory / "
                                f"gustatory /\n  `sugar/water`, cell type LB3, maxillary–labial nerve): the {n_shiu} left "
                                f"neurons of Shiu et al. (2024) plus {len(sg) - n_shiu} right")
    return want


def check_report_en(show=print):
    """REPORT.md (English, the single consolidated report). (1) Every cell of the run tables (§3.1, §3.3), recomputed
    from the HDF5 files (v2_values; English row labels). (2) The table rows and summary lines of
    `seeds_report.py --lang en` and `starts_report.py --lang en`, verbatim. (3) Every number of the prose
    (report_en_prose: run files, DN reference files, DNp15 validation scripts, code constants). (4) The video table
    against ffprobe."""
    rep = REPORT_EN.read_text()
    bad = 0
    n_cells = 0
    seen = set()
    for cols, rows in tables(rep):
        runs = [c for c in cols[1:] if c in RUNS_EN]
        if len(runs) < 2 or len(runs) != len(cols) - 1:
            continue
        for lab, cells in rows.items():
            key = EN_ROWS.get(lab)
            if key is None:
                bad += 1
                show(f"BAD REPORT.md table row without a check: {lab!r}")
                continue
            for n, cell in zip(runs, cells):
                want = v2_values(n)[key]
                if want == "değişken":
                    want = "variable"
                if key.startswith("adım-içi") and "step" not in cell:
                    want = want[:1]
                ok = cell_ok(cell, want)
                n_cells += 1
                seen.add(n)
                bad += not ok
                if not ok:
                    show(f"BAD REPORT.md table [{lab}] {n}: report {cell!r}, recomputed {want!r}")
    miss = set(RUNS_EN) - seen
    bad += len(miss)
    show(f"{'ok ' if not miss and not bad else 'BAD'} REPORT.md run tables: {n_cells} cells checked"
         + (f"; runs missing {miss}" if miss else ""))
    # S1 footnote ¹ (SPEC: no touchdown -> S1 ✗): exactly the S1 ✗ cells of runs without touchdown and without any
    # tower contact carry it, and the footnote under that table names the run
    nf = nfb = 0
    blocks = re.split(r"\n(?=### )", rep)
    for cols, rows in tables(rep):
        runs = [c for c in cols[1:] if c in RUNS_EN]
        if "S1" not in rows or len(runs) != len(cols) - 1:
            continue
        blk = next(b for b in blocks if "| " + " | ".join(cols) + " |" in b.replace("**", ""))
        for n, cell in zip(runs, rows["S1"]):
            v = v2_values(n)
            need = (v["S1"] == "✗" and v["touchdown"] is None and v["kule teması (adım sonu)"] == [0]
                    and v["adım-içi kule (touchdown öncesi)"] == [0])
            ok = ("¹" in cell) == need and (not need or re.search(rf"^¹ {n}[ :]", blk, re.M) is not None)
            nf += 1
            nfb += not ok
            if not ok:
                show(f"BAD REPORT.md S1 footnote {n}: cell {cell!r}, no-touchdown-without-contact {need}")
    bad += nfb
    show(f"{'ok ' if not nfb else 'BAD'} REPORT.md S1 footnotes: {nf} S1 cells checked")
    # turn-share note under every table with a turn-share row: runs whose turn_brain is one constant != 0, one
    # constant == 0, or variable (unique values over all steps, from the HDF5), named in column order
    def runs_txt(ns):
        return ns[0] if len(ns) == 1 else ", ".join(ns[:-1]) + " and " + ns[-1]
    nts = 0
    for cols, rows in tables(rep):
        runs = [c for c in cols[1:] if c in RUNS_EN]
        lab = "turn shares HAND-MADE / REFLEX / FLYVIS / BRAIN"
        if lab not in rows or len(runs) != len(cols) - 1:
            continue
        blk = next(b for b in blocks if "| " + " | ".join(cols) + " |" in b.replace("**", ""))
        note = " ".join(blk[blk.index("| " + lab):].split())     # text after the table, line breaks removed
        kind = {}
        for n in runs:
            with h5py.File(h5_any(n), "r") as f:
                tb = np.unique(np.round(f["behavior/turn_brain"][:], 6))
            kind[n] = "zero" if len(tb) == 1 and tb[0] == 0 else "const" if len(tb) == 1 else "var"
        want = []
        for k, phrase in (("const", "constant offset in {}"), ("zero", "exactly 0 in {}"),
                          ("var", "varies with brain activity only in {}")):
            ns = [n for n in runs if kind[n] == k]
            if ns:
                want.append(phrase.format(runs_txt(ns)))
        for w in want:
            ok = w in note
            nts += not ok
            show(f"{'ok ' if ok else 'BAD'} REPORT.md turn-share note [{', '.join(runs)}]: {w!r}")
    bad += nts
    se = report_output("seeds_report", lang="en").splitlines()
    st = report_output("starts_report", lang="en").splitlines()
    want_se = [ln for ln in se if re.match(r"^\| n[12] \|", ln) or re.match(r"^- \*\*n[12]\*\* \(seeds", ln)
               or re.match(r"^- \*\*n[12]\*\*: pos ", ln)]
    want_st = [ln for ln in st if re.match(r"^\| (condition|n1|st_\w+) \|", ln) or ln.startswith("- **S1 ∧ S2")
               or ln.startswith("- S1 ") or ln.startswith("- touchdown →") or ln.startswith("- route convergence")]
    o1l = [ln for ln in report_output("o1_report").splitlines() if ln.strip()]
    o1d = [ln for ln in report_output("o1_diag_report").splitlines() if ln.strip()]
    ntl = [ln for ln in report_output("nt_report").splitlines() if ln.strip()]
    nfl = [ln for ln in report_output("nf_report").splitlines() if ln.strip()]
    if not (ROOT / "fly_brain_body_simulation.py").exists():
        show("ok  upstream file not present: the odour-field line of the comparison check (nf_report step 0) is not recomputed")
    vdl = [ln for ln in report_output("vis_dn_report", argv=["--report"]).splitlines() if ln.strip()]
    vdp = [ln for ln in report_output("vis_dn_report", argv=["--posthoc"]).splitlines() if ln.strip()]
    vll = [ln for ln in report_output("vis_dn_report", argv=["--loom-followup", "--report"]).splitlines() if ln.strip()]
    ldl = [ln for ln in report_output("ladder_report").splitlines() if ln.strip()]
    lt1 = [ln for ln in report_output("ladder_trial1_report").splitlines() if ln.strip() and not ln.startswith("**")]
    smr = [ln for ln in report_output("summary_report").splitlines() if ln.strip()]
    for where, lines in (("seeds_report --lang en", want_se), ("starts_report --lang en", want_st),
                         ("o1_report (step-0 anatomy, O1 table)", o1l),
                         ("o1_diag_report (exploratory diagnostic)", o1d),
                         ("nt_report (NT audit, O1 under the sign variants, robustness)", ntl),
                         ("nf_report (comparison check: upstream drive, step-0 counts and result)", nfl),
                         ("vis_dn_report --report (visual DN screen: input check, a-priori and exploratory tables)", vdl),
                         ("vis_dn_report --posthoc (post-hoc looks)", vdp),
                         ("vis_dn_report --loom-followup --report (loom follow-up §3.8b)", vll),
                         ("ladder_report (training ladder round 1, §3.9: teacher flights)", ldl),
                         ("ladder_trial1_report (training ladder round 2, §3.9b: replay, readouts, validation flights)", lt1),
                         ("summary_report (§1.1: what the brain controls, table, reading, note)", smr)):
        nb = 0
        for ln in lines:
            if ln not in rep:
                nb += 1
                show(f"BAD REPORT.md line from {where} not found: {ln!r}")
        show(f"{'ok ' if not nb else 'BAD'} REPORT.md: {len(lines)} lines from {where} checked verbatim")
        bad += nb
    for k, w in {**report_en_prose(), **o1_values(), **nt_values(), **nf_values(), **vd_values()[1], **vl_values()[1]}.items():
        ok = w in rep
        bad += not ok
        show(f"{'ok ' if ok else 'BAD'} REPORT.md {k:32s} {w!r}")
    bad += check_brain_panel_en(rep, show)
    bad += check_cited_lines(show)
    bad += check_ladder_stop(show)
    vt = next(((c, r) for c, r in tables(rep) if c[:2] == ["video", "file"]), None)
    if vt is None or set(vt[1]) != set(VIDEOS_EN):
        bad += 1
        show("BAD REPORT.md: video table missing or incomplete")
    else:
        for lab, cells in vt[1].items():
            d = dict(zip(vt[0][1:], cells))
            path = ROOT / d["file"].strip("`")
            if d["file"].strip("`") != VIDEOS_EN[lab] or not path.exists():
                bad += 1
                show(f"BAD REPORT.md video {lab}: {path} missing or not the English render")
                continue
            pr = video_probe(path)
            checks = {"duration": [pr["duration"]], "frames": [pr["frames"]], "fps": [pr["fps"]],
                      "key-frame interval": [pr["key_gap"]], "resolution": pr["size"], "pixels": pr["pix_fmt"]}
            for k, want in checks.items():
                ok = k in d and cell_ok(d[k], want)
                bad += not ok
                show(f"{'ok ' if ok else 'BAD'} REPORT.md video {lab:8s} {k:20s} report {d.get(k)!r} ffprobe {want!r}")
    return bad


def check_brain_panel_en(rep, show):
    """REPORT.md §3.6 brain-panel text against the display constants of render_flight_video_v2.py."""
    sys.path.insert(0, str(ROOT))
    import render_flight_video_v2 as RV      # noqa: E402
    s36 = " ".join(rep[rep.index("### 3.6 Videos"):rep.index("## 4. Negative findings")].split())
    want = {"percentile": f"{RV.GAIN_PCT:g}th percentile", "frames": f"over {RV.GAIN_SAMPLES} frames",
            "class levels": "(" + ", ".join(f"{c} {100 * v:.0f} %" for c, v in RV.BIG_LEVEL.items()) + ")",
            "small-class gain": f"gain is {RV.SMALL_X:g} / (median intensity of their active neurons)",
            "tone map": f"(1 − e^−x)^γ, γ {RV.GLOW_GAMMA:g}", "dot sigma": f"σ {RV.DOT_SIGMA:g} px",
            "bloom": f"blur σ {RV.BLOOM_SIGMA:g} px, weight {RV.BLOOM_W:g}", "resolution": f"{RV.BR_SS}× resolution",
            "panel label": f'"{RV.GAIN_NOTE}"'}
    bad = 0
    for k, w in want.items():
        ok = w in s36
        bad += not ok
        show(f"{'ok ' if ok else 'BAD'} REPORT.md §3.6 {k:20s} {w!r}")
    return bad


def check_video_prose(rep, show):
    """§6.6 prose numbers, recomputed: FlyVis display layer and boundary layer sizes, /flyvis row offset,
    neck yaw in the qpos replay vs the recorded head_q, brain-panel display constants of render_flight_video_v2.py
    (dot size, tone map, bloom, per-class gain formula, panel label)."""
    import mujoco
    sys.path.insert(0, str(ROOT))
    import render_flight_video_v2 as RV      # noqa: E402
    from flight import head_reflex as HR     # noqa: E402
    from flight.body import FlightBody       # noqa: E402
    s66 = rep[rep.index("### 6.6 Videolar"):rep.index("## Sınırlamalar")]
    with h5py.File(h5_any("n1"), "r") as f:
        rows, n_st = f["flyvis/activity"].shape[0], len(f["behavior/t"])
        mapped = len(f["flyvis/flywire_map/idx"])
        n_types = len(np.unique(f["flyvis/node_type"][:]))
        vb_types = len(f["vision_boundary/types"])
        vb_n = len(f["vision_boundary/idx_L"]) + len(f["vision_boundary/idx_R"])
        pre = -int(f["spikes/step_idx"][:].min())
        hq = np.degrees(np.abs(f["behavior/head_q"][:, 0]).max())
        qpos = f["render/qpos"][:]
        on = f["behavior/wings_on"][:] > 0
        yaw95 = np.percentile(np.degrees(np.abs(f["behavior/head_q"][:, 0][on])), 95)
    body = FlightBody(legs="stand")
    jid = mujoco.mj_name2id(body.m, mujoco.mjtObj.mjOBJ_JOINT, f"{body.fly.name}/{HR.JOINTS['yaw']}")
    rq = np.degrees(np.abs(qpos[:, body.m.jnt_qposadr[jid]]).max())
    dot = lambda x: f"{x:,}".replace(",", ".")      # noqa: E731
    want = {
        "FlyVis tipleri": f"{n_types} sürülmeyen FlyVis tipi", "FlyVis nöronları": f"{dot(mapped)} FlyWire nöronu",
        "sınır katmanı": f"{vb_types} tip, {dot(vb_n)} nöron",
        "satır kayması": f"satır = adım + {pre}", "satır sayısı": f"{rows} = {n_st} + {pre}",
        "spike step_idx min": f"en küçüğü −{pre}",
        "replay yaw = head_q": f"{rq:.2f}°" if f"{rq:.2f}" == f"{hq:.2f}" else "replay≠head_q",
        "yaw %95": f"%95'lik {yaw95:.1f}°",
        "parlaklık yüzdeliği": f"%{RV.GAIN_PCT:g}'lik", "parlaklık kare sayısı": f"{RV.GAIN_SAMPLES} karedeki",
        "sınıf düzeyleri": "(" + ", ".join(f"{c} %{100 * v:.0f}" for c, v in RV.BIG_LEVEL.items()) + ")",
        "küçük sınıf kazancı": f"kazanç {RV.SMALL_X:g} / (aktif nöronlarının medyan yoğunluğu)",
        "ton eşleme γ": f"(1 − e^−x)^γ, γ {RV.GLOW_GAMMA:g}", "nokta σ": f"σ {RV.DOT_SIGMA:g} px",
        "ışıma": f"σ {RV.BLOOM_SIGMA:g} px, ağırlık {RV.BLOOM_W:g}", "panel etiketi": f'"{RV.GAIN_NOTE}"',
        "beslenme hızlandırma": f"her {RV.FEED_SKIP}. kare", "kartlar": f"başlık {RV.TITLE_S:g} s, bitiş {RV.END_S:g} s",
    }
    bad = 0
    for k, w in want.items():
        ok = w in s66
        bad += not ok
        show(f"{'ok ' if ok else 'BAD'} §6.6 {k:22s} {w!r}")
    return bad


def check_figures(show=print):
    """figures/data/fig*_summary.csv (written by scripts/figures/make_figures.py) against the report scripts, and the plotted data
    against its own summary; every PNG / PDF must exist."""
    import csv
    sys.path.insert(0, str(ROOT / "scripts" / "diag"))
    import summary_report as SR                       # noqa: E402
    import vis_dn_report as VD                        # noqa: E402
    import vl_report as VL                            # noqa: E402
    D = ROOT / "figures" / "data"
    stems = ["fig1_system_labels", "fig2_flight_paths", "fig3_feeding_decision", "fig4_olfactory_lockup", "fig5_vision_dn_screen",
             "fig6_trained_readout", "fig7_what_the_brain_controls", "fig8_brain_snapshots"]
    bad = 0

    def ok(cond, what):
        nonlocal bad
        bad += not cond
        show(f"{'ok ' if cond else 'BAD'} figures: {what}")
    for st in stems:
        ok(all((ROOT / "figures" / f"{st}.{e}").exists() for e in ("png", "pdf")) and (D / f"{st}.csv").exists() and (D / f"{st}_summary.csv").exists(),
           f"{st}: png, pdf, data csv and summary csv exist")
    summ = {st: {r["key"]: r["value"] for r in csv.DictReader(open(D / f"{st}_summary.csv"))} for st in stems}
    v = SR.values()
    # fig 2: touchdown counts and seed spread
    f2 = summ[stems[1]]
    ok(int(f2["n1_touchdown"]) == v["n1_td"] and int(f2["n2_touchdown"]) == v["n2_td"] and int(f2["n1_n_seeds"]) == v["n1_n"] and int(f2["n2_n_seeds"]) == v["n2_n"],
       f"fig2: touchdown n1 {v['n1_td']}/{v['n1_n']}, n2 {v['n2_td']}/{v['n2_n']} as summary_report")
    ok(float(f2["n1_max_diff_mm"]) == 0.0 and float(f2["n2_max_diff_mm"]) == 0.0, "fig2: seed lines identical (max difference 0 mm), as stated in the caption")
    ok(int(f2["start_runs_touchdown"]) == v["st_n"], f"fig2: touchdown in {v['st_n']} start-condition runs")
    # fig 3: MN9 decision, recounted from the plotted data
    f3 = summ[stems[2]]
    rows = list(csv.DictReader(open(D / f"{stems[2]}.csv")))
    n1_td = [float(r["mn9_hz"]) for r in rows if r["group"] == "n1_seeds" and r["step_rel_touchdown"] == "0"]
    st_td = [float(r["mn9_hz"]) for r in rows if r["group"] == "n1_starts" and r["step_rel_touchdown"] == "0"]
    ok(len(n1_td) == v["n1_n"] and sum(x > 10 for x in n1_td) == v["n1_mn9_ok"] == int(f3["n1_mn9_ok"]) and abs(min(n1_td) - v["n1_mn9_min"]) < 1e-9,
       f"fig3: MN9 > 10 Hz at touchdown in {v['n1_mn9_ok']}/{v['n1_n']} n1 seeds, lowest {v['n1_mn9_min']:.1f} Hz")
    ok(len(st_td) == v["st_n"] and sum(x > 10 for x in st_td) == v["st_mn9_ok"] == int(f3["st_mn9_ok"]), f"fig3: MN9 > 10 Hz in {v['st_mn9_ok']}/{v['st_n']} start conditions")
    ok(float(f3["leg_grn_mn9_hz"]) == 0.0 and f3["leg_grn_seeds_k"] == f3["leg_grn_seeds_n"] == "3" and "left MN9\n  at 0.0 Hz in 3/3 seeds" in (ROOT / "REPORT.md").read_text(),
       "fig3: leg GRN -> MN9 0.0 Hz in 3/3 seeds as quoted in REPORT.md")
    ok(float(f3["sugar_hz_at_touchdown_all_runs"]) == 100.0, "fig3: sugar GRN drive 100 Hz at touchdown in all runs")
    # fig 4: pass counts and mean AL after the cut, in the words of the report
    f4 = summ[stems[3]]
    nt, o1, nf = nt_values(), o1_values(), nf_values()
    ok(nt["NT variants AL"] == f"about {float(f4['published_mean_al_after_cut_hz']):.0f} Hz published, {float(f4['N1_mean_al_after_cut_hz']):.0f} Hz N1, "
       f"{float(f4['N2_mean_al_after_cut_hz']):.0f} Hz N2", f"fig4: {nt['NT variants AL']}")
    ok(all(int(f4[f"{k}_rates_passing_5of5"]) == 0 and int(f4[f"{k}_seeds_passing_total"]) == 0 and int(f4[f"{k}_n_runs"]) == 40 for k in ("published", "N1", "N2"))
       and o1["O1 rates"].startswith(f"{f4['published_rates_passing_5of5']} of {f4['n_rates']} drive rates"), f"fig4: {o1['O1 rates']}; N1/N2 {nt['NT variants rates']}")
    ok(nf["NF result"] == f"{f4['nf_seeds_pass']} of {f4['nf_n']} seeds", f"fig4: upstream-style drive {nf['NF result']}")
    # fig 5: screen counts and the loom follow-up rates
    f5 = summ[stems[4]]
    r, rl = VD.evaluate(), VL.evaluate()
    ok((int(f5["apriori_n"]), int(f5["apriori_PASS"]), int(f5["apriori_FAIL"]), int(f5["apriori_SILENT"]))
       == (len(r["apriori"]), r["apriori_counts"]["PASS"], r["apriori_counts"]["FAIL"], r["apriori_counts"]["SILENT"]),
       f"fig5: a-priori {r['apriori_counts']} of {len(r['apriori'])} (vis_dn_report)")
    ok((int(f5["vl_apriori_n"]), int(f5["vl_apriori_PASS"]), int(f5["vl_apriori_FAIL"]), int(f5["vl_apriori_SILENT"]))
       == (len(rl["apriori"]), rl["apriori_counts"]["PASS"], rl["apriori_counts"]["FAIL"], rl["apriori_counts"]["SILENT"]),
       f"fig5: loom follow-up {rl['apriori_counts']} of {len(rl['apriori'])} (vl_report)")
    ok(all(abs(float(f5[f"{c}_{a}_mean_hz"]) - float(f5[f"vl_{c}_{a}_ref_hz"])) < 1e-9 for c in ("DNp04", "DNp01") for a in ("appear", "grow")),
       f"fig5: DNp04/DNp01 appearing {float(f5['DNp04_appear_mean_hz']):.1f}/{float(f5['DNp01_appear_mean_hz']):.1f} Hz, growing "
       f"{float(f5['DNp04_grow_mean_hz']):.1f}/{float(f5['DNp01_grow_mean_hz']):.1f} Hz as in the loom report")
    cond = {c: (r["rates_val"]["DNp15"][c][1], r["rates_val"]["DNp15"][c][2]) for c in (1, 2, 3)}
    ok(all(abs(float(f5[f"DNp15_{n}_{s}_mean_hz"]) - cond[c][i]) < 1e-9 for c, n in ((1, "yaw-CW"), (2, "yaw-CCW"), (3, "static")) for i, s in enumerate("LR")),
       "fig5: DNp15 left / right rates equal vis_dn_report rates_val")
    # fig 6: R^2 of the stored fit and S1 counts of the validation flights
    f6 = summ[stems[5]]
    S = json.loads((ROOT / "docs" / "ladder" / "trial1_readouts.json").read_text())
    ok(all(abs(float(f6[f"cv_r2_{a}_{c}"]) - S["arms"][a]["cv_r2"][c]) < 1e-12 for a in S["arms"] for c in S["arms"][a]["cv_r2"]), "fig6: cross-validated R^2 equal docs/ladder/trial1_readouts.json")
    ok(all((int(f6[f"{a}_S1_ok"]), int(f6[f"{a}_S1_n"])) == tuple(v["t1"][a]) and int(f6[f"{a}_touchdown"]) == 0 for a in ("real", "shuffled", "bypass")),
       f"fig6: S1 {v['t1']} (ladder_trial1_report), no touchdown")
    # fig 7: the table of summary_report
    f7 = summ[stems[6]]
    R = SR.rows(v)
    ok(int(f7["n_rows"]) == len(R) and all(f7[f"row{i + 1}"].startswith(f"{r_[0]}|{r_[1]}|") for i, r_ in enumerate(R)), "fig7: rows and source labels equal summary_report")
    t7 = list(csv.DictReader(open(D / f"{stems[6]}.csv")))
    ok(len(t7) == len(R) and all(a["status"] == r_[3] and a["function"] == r_[0] for a, r_ in zip(t7, R)), "fig7: status of every row equals summary_report")
    # fig 8: the four moments and their counts, recomputed from the n1 seed 3 run record
    import h5py                                         # noqa: E402
    sys.path.insert(0, str(ROOT / "scripts" / "figures"))
    import make_figures as MF                           # noqa: E402
    f8 = summ[stems[7]]
    mom, n_neu = MF.fig8_data()
    t8 = list(csv.DictReader(open(D / f"{stems[7]}.csv")))
    ok(len(mom) == 4 and [m["moment"] for m in mom] == ["perch", "cruise", "touchdown", "feeding"] and
       all(int(f8[f"{m['moment']}_step"]) == m["step"] and int(f8[f"{m['moment']}_n_fired"]) == m["n_fire"] and
           abs(float(f8[f"{m['moment']}_rate_hz"]) - m["rate_hz"]) < 1e-3 and abs(float(f8[f"{m['moment']}_mn9_hz"]) - m["mn9_hz"]) < 1e-3 for m in mom),
       "fig8: steps, firing-neuron counts, network mean rates and MN9 equal the recount from the n1 seed 3 record")
    ok(all(int(r["n_neurons_fired"]) == m["n_fire"] and int(r["step"]) == m["step"] for r, m in zip(t8, mom)) and
       sum(int(r["n_neurons_fired"]) for r in csv.DictReader(open(D / f"{stems[7]}_by_class.csv"))) == sum(m["n_fire"] for m in mom),
       "fig8: plotted data csv equals the recount; per-class counts add up")
    with h5py.File(MF.h5_run("n1", 3), "r") as f_:
        b_ = f_["behavior"]
        net = b_["net_rate"][:]
        cd = json.loads(b_["phase"].attrs["codes"])
        ph_ = b_["phase"][:]
    ok(all(abs(net[m["step"]] - m["rate_hz"]) < 1e-9 for m in mom if m["step"] >= 0) and mom[2]["step"] == int(np.flatnonzero(ph_ == cd["touchdown"])[0])
       and mom[0]["mn9_hz"] == 0.0 and mom[1]["mn9_hz"] == 0.0 and mom[2]["mn9_hz"] > 10 and mom[3]["mn9_hz"] > 50 and n_neu == 138639,
       f"fig8: recorded net_rate equals the spike recount; touchdown = first touchdown step; MN9 {mom[2]['mn9_hz']:.1f} Hz at touchdown, {mom[3]['mn9_hz']:.1f} Hz at feeding")
    return bad


NO_RECORDS = ("run records not present; download the data bundle (DOI: to be added) and place it as described in README_DATA.md "
              "(the files must lie at the same relative paths: logs/..., simulations/..., data/...)")


NO_INPUTS = ("input files not present: run `env -u PYTHONPATH python scripts/fetch_data.py` once (it downloads brain_model/ and rebuilds the "
             "derivable data/ files; see README.md, Reproducing the numbers)")


def inputs_present():
    return all((ROOT / p).exists() for p in ("brain_model/Completeness_783.csv", "brain_model/Connectivity_783.parquet",
                                             "brain_model/flywire_annotations.tsv", "brain_model/descending_neurons.csv"))


def records_present():
    return (ROOT / "logs" / "final" / "DONE_final_a").exists() and any((ROOT / "simulations").glob("*_data.h5"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--print", action="store_true")
    ap.add_argument("--v2-only", action="store_true", help="only REPORT_FINAL_V2.md, README.md and REPORT.md")
    args = ap.parse_args(argv)
    if not records_present():
        print(NO_RECORDS, file=sys.stderr)
        return 2
    if not inputs_present():
        print(NO_INPUTS, file=sys.stderr)
        return 2
    if args.v2_only:
        bad = check_v2() + check_readme() + check_report_en() + check_figures()
        print(f"{'ALL OK' if not bad else f'{bad} MISMATCH(ES)'}")
        return 1 if bad else 0
    runs = {r: metrics(h5_of(r)) for r in ("final_a", "final_b", "final_c")}
    if args.print:
        print(json.dumps(runs, indent=1, ensure_ascii=False))
        return 0
    rep = REPORT.read_text()
    # each check: (run, key, the report line tag the value must appear on)
    checks = [(r, k, tag) for r in runs for k, tag in (
        ("touchdown_t", "| touchdown"), ("touchdown_speed", "| temas hızı"), ("tower_contact_steps", "| kule teması"),
        ("pen_steps_pre_td", "| adım-içi kule"), ("pen_max_um", "| en büyük penetrasyon"), ("S1", "| S1"),
        ("S2", "| S2"), ("mn9_first_t", "| MN9 ilk"), ("feed_steps", "| beslenme adımı"),
        ("mn9_mean_feed", "| beslenmede ort. MN9"), ("d_min", "| besine en yakın"), ("d_end", "| son uzaklık"),
        ("ratio_brain_total", "| oran BRAIN/toplam"), ("share_brain", "| pay BRAIN"), ("share_hand", "| pay HAND"),
        ("share_reflex", "| pay REFLEX"), ("share_flyvis", "| pay FLYVIS"), ("wings_on_steps", "| kanatlar açık"),
        ("peak_rss", "| tepe RSS"))]
    col = {"final_a": 1, "final_b": 2, "final_c": 3}
    bad = 0
    rows = {line.split("|")[1].strip(): [c.strip() for c in line.split("|")[2:-1]]
            for line in rep.splitlines() if line.startswith("| ") and line.count("|") >= 5}
    for r, k, tag in checks:
        label = tag[2:]
        row = rows.get(label)
        want = runs[r][k]
        got = row[col[r] - 1] if row else None
        ok = got is not None and want in got
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {r:8s} {k:20s} want {want!r:14s} table {got!r}")
    # prose values (final_a) that must appear somewhere in the report
    a, b_ = runs["final_a"], runs["final_b"]
    prose = [a["pen_first"], a["pen_max_um"], a["mn9_first_t"], a["touchdown_t"], a["feed_s"],
             a["ratio_brain_total"], b_["turn_brain_const"], a["n_neurons"]]
    for v in prose:
        ok = v in rep
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} prose {v!r}")
    assert runs["final_b"]["turn_brain_unique"] == "1", "final_b turn_brain must be constant"
    # prose claims: MN9 silent before touchdown, crosses 1 step after it (final_a); DNg02 silent in all runs;
    # sugar GRN contact drive 100 Hz
    for r in runs:
        with h5py.File(h5_of(r), "r") as f:
            b = f["behavior"]
            ph, mn9 = b["phase"][:], b["mn9_rate"][:]
            td = np.flatnonzero(ph == 4)
            pre_max = mn9[:td[0]].max() if len(td) else mn9.max()
            dng = int(b["dng02_L"][:].sum() + b["dng02_R"][:].sum())
            rate = float(f["meta"].attrs["sugar_rate_contact"])
            claims = {"MN9 = 0 before touchdown": pre_max == 0.0, "DNg02 0 spikes": dng == 0,
                      "sugar contact 100 Hz": rate == 100.0}
            if r == "final_a":
                claims["MN9 > 10 Hz one step after touchdown"] = int(np.argmax(mn9 > 10)) - int(td[0]) == 1
            for c, ok in claims.items():
                bad += not ok
                print(f"{'ok ' if ok else 'BAD'} {r:8s} {c}")
    print("── REPORT_FINAL_V2.md ──")
    bad += check_v2()
    print("── README.md ──")
    bad += check_readme()
    print("── REPORT.md ──")
    bad += check_report_en()
    print("── figures ──")
    bad += check_figures()
    print(f"{'ALL OK' if not bad else f'{bad} MISMATCH(ES)'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
