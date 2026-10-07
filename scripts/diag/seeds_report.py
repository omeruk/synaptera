"""Multi-seed repeat report (SPEC_SENSORY_INPUTS §3.3e), read-only from the HDF5 files. Markdown to stdout.

Output language: the default (Turkish) table text is compared verbatim with the Turkish lab notebook REPORT_FINAL_V2.md by
scripts/verify_report_final.py and is therefore kept as written; `--lang en` is the English version.

n1 (hybrid) and n2 (brain only), seeds 10-14 (logs/seeds/DONE_<arm>_s<seed>), next to seed 3 (logs/natural).
Per run: S1, S2, touchdown step, MN9 at the touchdown step and during feeding, feeding steps, tower contact
(scripts/verify_report_final.metrics definitions); B-K1 / B-K3 / B-K4 from scripts/diag/fv2_report.py (same
definitions). Determinism check: largest |difference| of pos / heading / turn_total / phase / is_feeding against
seed 3 of the same arm, over all steps.

    env -u PYTHONPATH python scripts/diag/seeds_report.py              # Turkish (REPORT_FINAL_V2 §6.7)
    env -u PYTHONPATH python scripts/diag/seeds_report.py --lang en    # English (README.md); the per-run B-K lines
                                                                       # are only in the Turkish output
"""
import argparse
import contextlib
import io
import re
import sys
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "diag"))
from verify_report_final import metrics  # noqa: E402

SEEDS = (10, 11, 12, 13, 14)
ARMS = ("n1", "n2")
MN9_THR = 10.0
DET_KEYS = ("pos", "heading", "turn_total", "phase", "is_feeding", "tower_contact", "leg_pose")


def name(arm, seed):
    return arm if seed == 3 else f"{arm}_s{seed}"


def h5_of(n):
    for d in ("seeds", "natural"):
        done = ROOT / "logs" / d / f"DONE_{n}"
        if done.exists():
            return ROOT / re.search(r"^h5=(.+)$", done.read_text(), re.M).group(1)
    (hit,) = sorted((ROOT / "simulations").glob(f"*_{n}_data.h5"))
    return hit


def badq(n):
    for d in ("seeds", "natural"):
        done = ROOT / "logs" / d / f"DONE_{n}"
        if done.exists():
            m = re.search(r"^badqacc_warnings=(\d+)$", done.read_text(), re.M)
            return int(m.group(1)) if m else None
    return None


def run_values(n):
    """Numbers of one run (strings as written in the report)."""
    p = h5_of(n)
    m = metrics(p)
    with h5py.File(p, "r") as f:
        b = {k: f["behavior"][k][:] for k in ("phase", "mn9_rate", "is_feeding")}
        seed = int(f["meta"].attrs["seed"])
    td = np.flatnonzero(b["phase"] == 4)
    k_td = int(td[0]) if len(td) else None
    feed = np.flatnonzero(b["is_feeding"] > 0)
    mn9 = b["mn9_rate"]
    return {
        "seed": seed, "S1": m["S1"], "S2": m["S2"],
        "touchdown": f"{k_td}" if k_td is not None else None,
        "mn9_td": f"{mn9[k_td]:.1f}" if k_td is not None else "—",
        "mn9_td_raw": float(mn9[k_td]) if k_td is not None else None,
        "feed_first": f"{int(feed[0])}" if len(feed) else "—",
        "feed_steps": f"{len(feed)}",
        "mn9_feed_mean": f"{mn9[feed].mean():.1f}" if len(feed) else "—",
        "mn9_feed_min": f"{mn9[feed].min():.1f}" if len(feed) else "—",
        "tower_contact": m["tower_contact_steps"], "pen_pre_td": m["pen_steps_pre_td"],
        "badq": badq(n),
    }


def determinism(arm):
    """Largest |difference| against seed 3 of the same arm, per behaviour array, over all steps of all seeds."""
    with h5py.File(h5_of(name(arm, 3)), "r") as f:
        ref = {k: f["behavior"][k][:].astype(float) for k in DET_KEYS}
    worst = dict.fromkeys(DET_KEYS, 0.0)
    for s in SEEDS:
        with h5py.File(h5_of(name(arm, s)), "r") as f:
            for k in DET_KEYS:
                worst[k] = max(worst[k], float(np.abs(f["behavior"][k][:].astype(float) - ref[k]).max()))
    return worst


def bk_lines(names):
    """B-K1 / B-K3 / B-K4 bullet of each run, from fv2_report.main (same definitions)."""
    import fv2_report
    fv2_report.h5_of = h5_of
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fv2_report.main(names)
    return {mm.group(1): mm.group(2) for mm in re.finditer(r"^- \*\*(\S+)\*\*: (B-K1 .*)$", buf.getvalue(), re.M)}


TEXT = {
    "tr": dict(
        header="| koşu | seed | S1 | S2 | touchdown adımı | MN9 temas adımında (Hz) | ilk beslenme adımı | beslenme adımı | "
               "beslenmede MN9 ort. / en düşük (Hz) | kule teması (adım sonu) | adım-içi kule (td öncesi) | BADQACC |",
        none="yok", seeds="seed 10–14",
        mn9="temas adımında MN9 > {thr} Hz: {c}/{m}, en düşük {lo:.1f} Hz, en yüksek {hi:.1f} Hz.",
        no_td="touchdown yok (MN9 temas ölçüsü uygulanamaz).",
        det="**Belirlenimcilik** (seed 10–14 vs seed 3, aynı kol, tüm adımlar; en büyük |fark|):",
        summary="Özet (rapora aynen):",
        bk="- **{a}**: B-K1 ∧ B-K3 ∧ B-K4 {k}/{n}; sürülmeyen {u} Hz, adım {s} s, temassız MN9 {m} Hz."),
    "en": dict(
        header="| run | seed | S1 | S2 | touchdown step | MN9 at the touchdown step (Hz) | first feeding step | "
               "feeding steps | MN9 during feeding, mean / lowest (Hz) | tower contact (end of step) | "
               "intra-step tower contact (before td) | BADQACC |",
        none="none", seeds="seeds 10–14",
        mn9="MN9 > {thr} Hz at the touchdown step: {c}/{m}, lowest {lo:.1f} Hz, highest {hi:.1f} Hz.",
        no_td="no touchdown (the MN9 contact measure does not apply).",
        det="**Determinism** (seeds 10–14 vs seed 3, same arm, all steps; largest |difference|):",
        summary="Summary:",
        bk="- **{a}**: B-K1 ∧ B-K3 ∧ B-K4 {k}/{n}; undriven {u} Hz, step {s} s, MN9 without contact {m} Hz."),
}


def main(lang="tr"):
    out = print
    T = TEXT[lang]
    allseeds = (3,) + SEEDS
    V = {(a, s): run_values(name(a, s)) for a in ARMS for s in allseeds}
    for (a, s), v in V.items():
        assert v["seed"] == s, (a, s, v["seed"])
        if v["touchdown"] is None:
            v["touchdown"] = T["none"]
    out(T["header"])
    out("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for a in ARMS:
        for s in allseeds:
            v = V[(a, s)]
            out(f"| {a} | {s}{' (§3.3d)' if s == 3 else ''} | {v['S1']} | {v['S2']} | {v['touchdown']} | {v['mn9_td']} | "
                f"{v['feed_first']} | {v['feed_steps']} | {v['mn9_feed_mean']} / {v['mn9_feed_min']} | "
                f"{v['tower_contact']} | {v['pen_pre_td']} | {v['badq']} |")
    out("")
    for a in ARMS:
        ok = [s for s in SEEDS if V[(a, s)]["S1"] == "✓" and V[(a, s)]["S2"] == "✓"]
        td = [V[(a, s)]["mn9_td_raw"] for s in SEEDS if V[(a, s)]["mn9_td_raw"] is not None]
        cross = sum(x > MN9_THR for x in td)
        out(f"- **{a}** ({T['seeds']}): S1 ∧ S2 {len(ok)}/{len(SEEDS)}; "
            + (T["mn9"].format(thr=f"{MN9_THR:g}", c=cross, m=len(td), lo=min(td), hi=max(td)) if td else T["no_td"]))
    out("")
    out(T["det"])
    for a in ARMS:
        w = determinism(a)
        out(f"- **{a}**: " + ", ".join(f"{k} {v:.3g}" for k, v in w.items()))
    out("")
    bk = bk_lines([name(a, s) for a in ARMS for s in SEEDS])
    if lang == "tr":
        out("**B-K1 / B-K3 / B-K4** (fv2_report tanımları):")
        for a in ARMS:
            for s in SEEDS:
                out(f"- **{name(a, s)}**: {bk[name(a, s)]}")
        out("")
    out(T["summary"])
    for a in ARMS:
        L = [bk[name(a, s)] for s in SEEDS]
        n_ok = sum(all(f"{c} geçti" in x for c in ("B-K1", "B-K3", "B-K4")) for x in L)

        def rng(pat, nd):
            v = [float(re.search(pat, x).group(1)) for x in L]
            return f"{min(v):.{nd}f}–{max(v):.{nd}f}"
        out(T["bk"].format(a=a, k=n_ok, n=len(SEEDS), u=rng(r'sürülmeyen ([0-9.]+) Hz', 3), s=rng(r'adım ([0-9.]+) s', 3),
                           m=rng(r'temassız MN9 ([0-9.]+) Hz', 2)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=sorted(TEXT), default="tr")
    main(ap.parse_args().lang)
