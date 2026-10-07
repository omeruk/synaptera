"""Start position / heading test report (SPEC_SENSORY_INPUTS §3.3f), read-only from the HDF5 files. Markdown to stdout.

Output language: the default (Turkish) table text is compared verbatim with the Turkish lab notebook REPORT_FINAL_V2.md by
scripts/verify_report_final.py and is therefore kept as written; `--lang en` is the English version.

Eight n1 runs (seed 3, --hybrid, run_natural.sh flags) with --start-offset / --start-yaw (logs/starts/DONE_<tag>),
next to n1 itself (logs/natural). S1 / S2 / tower contact / touchdown / feeding: scripts/verify_report_final.metrics;
total heading change as in verify_report_final (wings on); B-K1 / B-K3 / B-K4 from scripts/diag/fv2_report.py and
B-H1..B-H3 as in scripts/diag/nat_report.py (same definitions). Every run's meta (seed, steps, flags, pedestal) is
checked against the pre-registered condition.

    env -u PYTHONPATH python scripts/diag/starts_report.py              # Turkish (REPORT_FINAL_V2 §6.8)
    env -u PYTHONPATH python scripts/diag/starts_report.py --lang en    # English (README.md); the B-K / B-H
                                                                        # per-run lines are only in the Turkish output
"""
import argparse
import contextlib
import io
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
from flight import config as cfg  # noqa: E402
from flight import head_reflex as HR  # noqa: E402
from flight.body import point_box_distance  # noqa: E402
from verify_report_final import metrics  # noqa: E402

# SPEC §3.3f, fixed order: tag -> (start offset mm, start yaw deg)
CONDITIONS = {
    "st_xp40": ((40.0, 0.0), 0.0), "st_xm40": ((-40.0, 0.0), 0.0),
    "st_yp40": ((0.0, 40.0), 0.0), "st_ym40": ((0.0, -40.0), 0.0),
    "st_yawp30": ((0.0, 0.0), 30.0), "st_yawm30": ((0.0, 0.0), -30.0),
    "st_yawp60": ((0.0, 0.0), 60.0), "st_yawm60": ((0.0, 0.0), -60.0),
}
REF = "n1"
MN9_THR = 10.0


def done_text(n):
    for d in ("starts", "natural"):
        p = ROOT / "logs" / d / f"DONE_{n}"
        if p.exists():
            return p.read_text()
    return None


def h5_of(n):
    t = done_text(n)
    if t is not None:
        return ROOT / re.search(r"^h5=(.+)$", t, re.M).group(1)
    (hit,) = sorted((ROOT / "simulations").glob(f"*_{n}_data.h5"))
    return hit


def badq(n):
    t = done_text(n)
    m = re.search(r"^badqacc_warnings=(\d+)$", t, re.M) if t else None
    return int(m.group(1)) if m else None


def flag_str(n):
    if n == REF:
        return "— (§3.3d n1)"
    (dx, dy), yaw = CONDITIONS[n]
    return f"`--start-offset {dx:g} {dy:g}`" if (dx or dy) else f"`--start-yaw {yaw:g}`"


def run_values(n):
    p = h5_of(n)
    m = metrics(p)
    with h5py.File(p, "r") as f:
        b = {k: f["behavior"][k][:] for k in ("phase", "mn9_rate", "heading", "wings_on", "pos", "t", "is_feeding",
                                              "head_q_absmax", "head_turn_sub", "head_turn_sub_lt")}
        flags = json.loads(f["meta"].attrs["flags"])
        geom = json.loads(f["meta"].attrs["geometry"])
        seed, n_steps = int(f["meta"].attrs["seed"]), int(f["meta"].attrs["n_steps"])
        dev = bool(f["meta"].attrs["dev_subnet"])
    # pre-registered configuration
    off, yaw = CONDITIONS.get(n, ((0.0, 0.0), 0.0))
    assert seed == 3 and n_steps == 300 and not dev, (n, seed, n_steps, dev)
    for k in ("hybrid", "vision_boundary", "no_olfaction", "no_brain_steer", "head_reflex", "postures"):
        assert flags[k], (n, k)
    assert list(flags.get("start_offset", [0.0, 0.0])) == list(off) and flags.get("start_yaw", 0.0) == yaw, (n, flags)
    assert tuple(geom["pedestal"][:2]) == off, (n, geom["pedestal"])
    td = np.flatnonzero(b["phase"] == 4)
    k_td = int(td[0]) if len(td) else None
    on = b["wings_on"] > 0
    turn = np.degrees(np.diff(np.unwrap(b["heading"]))[on[1:]].sum())
    ts, tl = int(b["head_turn_sub"][on].sum()), int(b["head_turn_sub_lt"][on].sum())
    bq = badq(n)
    feed = np.flatnonzero(b["is_feeding"] > 0)
    pre = b["pos"][:k_td if k_td is not None else len(b["pos"])]
    # thorax (subtree COM) to the nearest tower surface before touchdown; record, not a criterion
    d = np.array([[point_box_distance(p_, box) for box in cfg.TOWERS] for p_ in pre])
    k_c, j_c = np.unravel_index(d.argmin(), d.shape)
    clear = float(d[k_c, j_c])
    clear_at = (f"{{tower}} {j_c + 1}, t = {b['t'][k_c]:.2f} s, ({pre[k_c][0]:.1f}, {pre[k_c][1]:.1f}, "
                f"{pre[k_c][2]:.1f}) mm")
    return {
        "S1": m["S1"], "S2": m["S2"],
        "td": f"{k_td} / {b['t'][k_td]:.2f} s" if k_td is not None else None,
        "mn9_td": f"{b['mn9_rate'][k_td]:.1f}" if k_td is not None else "—",
        "mn9_td_raw": float(b["mn9_rate"][k_td]) if k_td is not None else None,
        "feed": m["feed_steps"], "feed_first": f"{int(feed[0])}" if len(feed) else "—",
        "clear": f"{clear:.1f} mm", "clear_raw": clear, "clear_at": clear_at, "d_min": m["d_min"], "turn": f"{turn:+.1f}°",
        "tc": m["tower_contact_steps"], "pen": m["pen_steps_pre_td"], "pen_max": m["pen_max_um"],
        "pen_first": m["pen_first"], "badq": bq,
        "start": f"({b['pos'][0][0]:.1f}, {b['pos'][0][1]:.1f}) mm, {np.degrees(b['heading'][0]):+.1f}°",
        "bh1": bq == 0, "bh2": bool(np.all(b["head_q_absmax"] <= HR.THETA_MAX + 1e-9)),
        "bh3": None if ts == 0 else tl / ts > 0.5, "bh3_txt": f"{tl:,} / {ts:,}",
    }


CONV_DEG, CONV_UNTIL, CONV_STEP = 5.0, 60, 52


def convergence(n):
    """First time from which the heading stays within CONV_DEG of n1's up to step CONV_UNTIL, and |y - y_n1| at
    step CONV_STEP (t ~ 1.3 s, before tower 2). Record only."""
    with h5py.File(h5_of(REF), "r") as f:
        rh, ry = np.unwrap(f["behavior"]["heading"][:]), f["behavior"]["pos"][:, 1]
    with h5py.File(h5_of(n), "r") as f:
        h, y, t = np.unwrap(f["behavior"]["heading"][:]), f["behavior"]["pos"][:, 1], f["behavior"]["t"][:]
    dh = np.degrees(np.abs((h[:CONV_UNTIL] - rh[:CONV_UNTIL] + np.pi) % (2 * np.pi) - np.pi))
    k = next(i for i in range(CONV_UNTIL) if dh[i:].max() < CONV_DEG)
    return float(t[k]), float(abs(y[CONV_STEP] - ry[CONV_STEP])), float(t[CONV_STEP])


def bk_lines(names):
    import fv2_report
    fv2_report.h5_of = h5_of
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fv2_report.main(names)
    return {mm.group(1): mm.group(2) for mm in re.finditer(r"^- \*\*(\S+)\*\*: (B-K1 .*)$", buf.getvalue(), re.M)}


TEXT = {
    "tr": dict(
        header="| koşul | bayrak | S1 | S2 | touchdown (adım / s) | MN9 temas adımında (Hz) | ilk beslenme adımı | "
               "beslenme adımı | besine en yakın | toplam yön değişimi | kuleye en yakın (td öncesi) | "
               "kule teması (adım sonu) | adım-içi kule (td öncesi) | en büyük penetrasyon | BADQACC |",
        none="yok", tower="kule",
        passed="- **S1 ∧ S2: {k}/{n} koşulda geçti**", rest="; kalan: {r}.",
        counts="- S1 {s1}/{n}, S2 {s2}/{n}; touchdown {td}/{n}",
        mn9="; temas adımında MN9 > {thr} Hz: {c}/{m} (en düşük {lo:.1f} Hz).",
        lag="- touchdown → ilk beslenme: {a}–{b} adım; kuleye en yakın (td öncesi): {c}–{d} mm (n1 {e}).",
        no_td="touchdown yok", why_tower="kule: adım-içi {p} adım (ilki adım {f}), adım sonu {tc}, en büyük {m}",
        no_feed="touchdown sonrası beslenme yok",
        conv="- rota yakınsaması (kayıt): yön, n1'in {deg}° içine t = {a}–{b} s'de giriyor ve adım {u}'a kadar "
             "kalıyor; t = {t} s'de n1 rotasından |Δy| {c}–{d} mm.",
        start="**Başlangıç** (adım 0, kayıt; girdi kesme adımlarından sonra):",
        closest="**Kuleye en yakın nokta** (touchdown öncesi, gövde merkezi; kayıt):",
        record="**Kayıt ölçütleri:** B-K1 ∧ B-K3 ∧ B-K4 {k}/{n}; B-H1 ∧ B-H2 ∧ B-H3 {h}/{n}."),
    "en": dict(
        header="| condition | flag | S1 | S2 | touchdown (step / s) | MN9 at the touchdown step (Hz) | first feeding step | "
               "feeding steps | closest to food | total heading change | closest to a tower (before td) | "
               "tower contact (end of step) | intra-step tower contact (before td) | max. penetration | BADQACC |",
        none="none", tower="tower",
        passed="- **S1 ∧ S2: passed in {k}/{n} conditions**", rest="; failed: {r}.",
        counts="- S1 {s1}/{n}, S2 {s2}/{n}; touchdown {td}/{n}",
        mn9="; MN9 > {thr} Hz at the touchdown step: {c}/{m} (lowest {lo:.1f} Hz).",
        lag="- touchdown → first feeding: {a}–{b} steps; closest to a tower (before td): {c}–{d} mm (n1 {e}).",
        no_td="no touchdown", why_tower="tower: intra-step contact in {p} steps (first at step {f}), end of step {tc}, "
                                        "max. {m}",
        no_feed="no feeding after touchdown",
        conv="- route convergence (record): the heading comes within {deg}° of n1 at t = {a}–{b} s and stays there "
             "up to step {u}; at t = {t} s the distance |Δy| from the n1 route is {c}–{d} mm.",
        start="**Start** (step 0, record; after the input cut-off steps):",
        closest="**Closest point to a tower** (before touchdown, body centre; record):",
        record="**Record criteria:** B-K1 ∧ B-K3 ∧ B-K4 {k}/{n}; B-H1 ∧ B-H2 ∧ B-H3 {h}/{n}."),
}


def main(lang="tr"):
    out = print
    T = TEXT[lang]
    names = list(CONDITIONS)
    V = {n: run_values(n) for n in [REF] + names}
    for v in V.values():
        v["clear_at"] = v["clear_at"].format(tower=T["tower"])
        if v["td"] is None:
            v["td"] = T["none"]
    out(T["header"])
    out("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for n in [REF] + names:
        v = V[n]
        out(f"| {n} | {flag_str(n)} | {v['S1']} | {v['S2']} | {v['td']} | {v['mn9_td']} | {v['feed_first']} | {v['feed']} | "
            f"{v['d_min']} | {v['turn']} | {v['clear']} | {v['tc']} | {v['pen']} | {v['pen_max']} | {v['badq']} |")
    out("")
    ok = [n for n in names if V[n]["S1"] == "✓" and V[n]["S2"] == "✓"]
    bad = [n for n in names if n not in ok]
    out(T["passed"].format(k=len(ok), n=len(names)) + (T["rest"].format(r=", ".join(bad)) if bad else "."))
    s1 = sum(V[n]["S1"] == "✓" for n in names)
    s2 = sum(V[n]["S2"] == "✓" for n in names)
    td = [V[n]["mn9_td_raw"] for n in names if V[n]["mn9_td_raw"] is not None]
    out(T["counts"].format(s1=s1, s2=s2, td=len(td), n=len(names))
        + (T["mn9"].format(thr=f"{MN9_THR:g}", c=sum(x > MN9_THR for x in td), m=len(td), lo=min(td)) if td else "."))
    lag = [int(V[n]["feed_first"]) - int(V[n]["td"].split(" /")[0]) for n in names if V[n]["feed_first"] != "—"]
    out(T["lag"].format(a=min(lag), b=max(lag), c=f"{min(V[n]['clear_raw'] for n in names):.1f}",
                        d=f"{max(V[n]['clear_raw'] for n in names):.1f}", e=V[REF]["clear"]))
    for n in bad:
        v = V[n]
        why = []
        if v["td"] == T["none"]:
            why.append(T["no_td"])
        if v["pen"] != "0" or v["tc"] != "0":
            why.append(T["why_tower"].format(p=v["pen"], f=v["pen_first"], tc=v["tc"], m=v["pen_max"]))
        if v["S2"] == "✗" and v["td"] != T["none"]:
            why.append(T["no_feed"])
        out(f"  - {n}: " + "; ".join(why) + ".")
    conv = {n: convergence(n) for n in names}
    out(T["conv"].format(deg=f"{CONV_DEG:g}", a=f"{min(c[0] for c in conv.values()):.2f}",
                         b=f"{max(c[0] for c in conv.values()):.2f}", u=CONV_UNTIL, t=f"{conv[names[0]][2]:.2f}",
                         c=f"{min(c[1] for c in conv.values()):.1f}", d=f"{max(c[1] for c in conv.values()):.1f}"))
    out("")
    out(T["start"])
    for n in [REF] + names:
        out(f"- {n}: {V[n]['start']}")
    out("")
    out(T["closest"])
    for n in [REF] + names:
        out(f"- {n}: {V[n]['clear']}, {V[n]['clear_at']}")
    out("")
    bk = bk_lines(names)
    k_ok = sum(all(f"{c} geçti" in bk[n] for c in ("B-K1", "B-K3", "B-K4")) for n in names)
    h_ok = sum(V[n]["bh1"] and V[n]["bh2"] and V[n]["bh3"] is True for n in names)
    out(T["record"].format(k=k_ok, h=h_ok, n=len(names)))
    if lang != "tr":
        return
    for n in names:
        v = V[n]
        bh3 = "uygulanamaz" if v["bh3"] is None else ("geçti" if v["bh3"] else "KALDI")
        out(f"- **{n}**: {bk[n].rstrip('.')}; B-H1 {'geçti' if v['bh1'] else 'KALDI'}, B-H2 {'geçti' if v['bh2'] else 'KALDI'}, "
            f"B-H3 {bh3} ({v['bh3_txt']}).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=sorted(TEXT), default="tr")
    main(ap.parse_args().lang)
