"""Naturalness round report (SPEC_SENSORY_INPUTS §3.3d), read-only from the HDF5 files. Markdown to stdout.

n1 (hybrid) and n2 (brain only) with --no-brain-steer --head-reflex --postures, next to final_v2a, final_sB
and final_v2c. Behaviour / S1 / S2 / activity / DN windows / B-K1, B-K3, B-K4: scripts/diag/fv2_report.py
(same definitions). Here in addition: head reflex B-H1..B-H3, postures, visual input (boundary-layer
target rates) side by side.

Output language: the Turkish table text is compared verbatim with the Turkish lab notebook REPORT_FINAL_V2.md by
scripts/verify_report_final.py and is therefore kept as written.

    env -u PYTHONPATH python scripts/diag/nat_report.py
"""
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "diag"))
from flight import config as cfg  # noqa: E402
from flight import head_reflex as HR  # noqa: E402
import fv2_report  # noqa: E402

NAMES = ["n1", "final_v2a", "final_sB", "n2", "final_v2c"]


def badq_lines(name):
    done = ROOT / "logs" / "natural" / f"DONE_{name}"
    if not done.exists():
        return None
    m = re.search(r"^badqacc_warnings=(\d+)$", done.read_text(), re.M)
    return int(m.group(1)) if m else None


def pitch_deg(quat):
    """Thorax nose-down pitch (deg, +) from the recorded quaternions (w, x, y, z)."""
    w, x, y, z = quat.T
    r20 = 2 * (x * z - w * y)                     # R[2, 0]
    return np.degrees(np.arcsin(np.clip(-r20, -1, 1)))


def main():
    names = [n for n in NAMES if (ROOT / "logs/natural" / f"DONE_{n}").exists() or n.startswith("final")]
    paths, R = fv2_report.main(names)
    out = print

    out("\n## Baş refleksi (B-H1..B-H3, SPEC §3.3d)\n")
    for n in names:
        r = R[n]
        if not r.meta["flags"].get("head_reflex"):
            continue
        b = r.b
        on = b["wings_on"].astype(bool)
        bq = badq_lines(n)
        qmax = np.degrees(b["head_q_absmax"]).max(0)
        h2 = bool(np.all(b["head_q_absmax"] <= HR.THETA_MAX + 1e-9))
        ts, tl = int(b["head_turn_sub"][on].sum()), int(b["head_turn_sub_lt"][on].sum())
        h3 = "uygulanamaz" if ts == 0 else ("geçti" if tl / ts > 0.5 else "KALDI")
        q = np.degrees(b["head_q"][on]) if on.any() else np.zeros((0, 3))
        gz, bd = np.abs(b["gaze_yaw_rate"][on]), np.abs(b["body_yaw_rate"][on])
        out(f"- **{n}**: B-H1 {'geçti' if bq == 0 else ('KALDI' if bq else '?')} (BADQACC satırı {bq}); "
            f"B-H2 {'geçti' if h2 else 'KALDI'} (en büyük |θ| yaw/pitch/roll "
            f"{qmax[0]:.1f} / {qmax[1]:.1f} / {qmax[2]:.1f}°); "
            f"B-H3 {h3} ({tl:,} / {ts:,} dönüş alt adımı = %{100 * tl / max(ts, 1):.1f}).")
        if on.any():
            out(f"  - kanatlar açık {int(on.sum())} adım: baş yaw medyan |θ| {np.median(np.abs(q[:, 0])):.1f}°, "
                f"%95 {np.percentile(np.abs(q[:, 0]), 95):.1f}°; pitch ort. {q[:, 1].mean():+.1f}°, "
                f"roll ort. {q[:, 2].mean():+.1f}°; yaw reset sayısı {r.meta['head_reflex']['n_yaw_resets']}; "
                f"adım ort. |bakış yaw| {gz.mean():.3f} rad/s, |gövde yaw| {bd.mean():.3f} rad/s.")

    out("\n## Duruşlar (`leg_pose`, gövde pitch)\n")
    for n in names:
        r = R[n]
        if not r.meta["flags"].get("postures"):
            continue
        b = r.b
        lp = b["leg_pose"]
        pd = pitch_deg(b["quat"])
        landed = np.isin(b["phase"], [cfg.PHASE_CODE["touchdown"], cfg.PHASE_CODE["landed"]])
        feed = landed & (lp == cfg.LEG_POSE_CODE["feed"])
        stand = landed & (lp == cfg.LEG_POSE_CODE["stand"])
        sw = int(np.count_nonzero(np.diff(lp[landed].astype(int)))) if landed.any() else 0
        out(f"- **{n}**: adım sayısı stand / uçuş / feed = {int((lp == 0).sum())} / {int((lp == 1).sum())} / "
            f"{int((lp == 2).sum())}; platformda poz değişimi {sw}; gövde pitch (burun aşağı +) platformda feed "
            + (f"{pd[feed].mean():+.1f}°" if feed.any() else "–") + ", stand "
            + (f"{pd[stand].mean():+.1f}°" if stand.any() else "–") + ".")

    out("\n## Görsel girdi: sınır katmanı hedef hızı (FlyVis → Poisson, Hz; kanatlar açık adımlar)\n")
    out("| | " + " | ".join(names) + " |\n|---|" + "---|" * len(names))
    cells = {}
    for n in names:
        b = R[n].b
        on = b["wings_on"].astype(bool)
        v = b["vbnd_type_rate"][on]                    # (steps, 2, 32)
        cells[n] = (v[:, 0].mean(), v[:, 1].mean(), np.abs(v[:, 0] - v[:, 1]).mean(),
                    b["t45_rate_L"][on].mean(), b["t45_rate_R"][on].mean())
    for i, lab in enumerate(("ort. L", "ort. R", "ort. |L−R| (tip başına)", "T4/T5 L", "T4/T5 R")):
        out(f"| {lab} | " + " | ".join(f"{cells[n][i]:.2f}" for n in names) + " |")


if __name__ == "__main__":
    main()
