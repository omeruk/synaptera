"""Final-v2 report tables (SPEC_SENSORY_INPUTS §3.3c), read-only from the HDF5 files. Markdown to stdout.

Runs: final_v2a / final_v2c (logs/final_v2/DONE_*, else simulations/*_<name>_data.h5), next to final-v1
(final_a, final_b, final_c) and final_sB (Stage B). Behaviour / S1 / S2 / turn shares with the same
definitions as scripts/verify_report_final.py (metrics()); neuron activity and DN windows with
scripts/diag/sb_report.py (Run, neuron_sets); B-K1 / B-K3 / B-K4 as in SPEC §3.3b.

Output language: the Turkish table text is compared verbatim with the Turkish lab notebooks (REPORT_FINAL_V2.md) by
scripts/verify_report_final.py and is therefore kept as written.

    env -u PYTHONPATH python scripts/diag/fv2_report.py
"""
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "diag"))
from flight import config as cfg  # noqa: E402
from flight import groups as G  # noqa: E402
from sb_report import DT, Run, neuron_sets  # noqa: E402
from verify_report_final import metrics  # noqa: E402

V2 = ("final_v2a", "final_v2c")
V1 = ("final_a", "final_b", "final_c")


def h5_of(name):
    for d in ("natural", "final_v2", "final"):
        done = ROOT / "logs" / d / f"DONE_{name}"
        if done.exists():
            return ROOT / re.search(r"^h5=(.+)$", done.read_text(), re.M).group(1)
    (hit,) = sorted((ROOT / "simulations").glob(f"*_{name}_data.h5"))
    return hit


def main(names=None):
    if names is None:
        names = [n for n in V2 if any((ROOT / "logs/final_v2").glob(f"DONE_{n}")) or
                 list((ROOT / "simulations").glob(f"*_{n}_data.h5"))] + list(V1) + ["final_sB"]
    paths = {n: h5_of(n) for n in names}
    out = print
    out("| koşu | HDF5 |\n|---|---|")
    for n, p in paths.items():
        out(f"| {n} | `{p.relative_to(ROOT) if p.is_relative_to(ROOT) else p}` |")
    out("")

    M = {n: metrics(p) for n, p in paths.items()}
    rows = [("touchdown", "touchdown_t"), ("touchdown adımı", "touchdown_step"), ("temas hızı", "touchdown_speed"),
            ("kule teması", "tower_contact_steps"), ("adım-içi kule", "pen_steps_pre_td"),
            ("en büyük penetrasyon", "pen_max_um"), ("S1", "S1"), ("S2", "S2"), ("MN9 ilk", "mn9_first_t"),
            ("beslenme adımı", "feed_steps"), ("beslenmede ort. MN9", "mn9_mean_feed"),
            ("besine en yakın", "d_min"), ("son uzaklık", "d_end"), ("kanatlar açık", "wings_on_steps"),
            ("pay BRAIN", "share_brain"), ("pay HAND", "share_hand"), ("pay REFLEX", "share_reflex"),
            ("pay FLYVIS", "share_flyvis"), ("oran BRAIN/toplam", "ratio_brain_total"),
            ("turn_brain farklı değer sayısı", "turn_brain_unique"), ("turn_brain (ilk adım)", "turn_brain_const"),
            ("tepe RSS", "peak_rss")]
    out("## Davranış ve ön-kayıtlı ölçütler\n")
    out("| ölçü | " + " | ".join(names) + " |\n|---|" + "---|" * len(names))
    for lab, k in rows:
        out(f"| {lab} | " + " | ".join(M[n][k] for n in names) + " |")
    out("")

    R = {n: Run(p) for n, p in paths.items()}
    out("## Aktif nöronlar (kapalı döngü, ≥1 spike)\n")
    out("| | " + " | ".join(names) + " |\n|---|" + "---|" * len(names))
    for lab, f in (("Toplam", lambda r: np.ones(r.N, bool)), ("Sürülen girdi", lambda r: r.driven),
                   ("Sürülmeyen", lambda r: ~r.driven)):
        cells = []
        for n in names:
            r = R[n]
            m = f(r)
            a = int((r.count_cl[m] > 0).sum())
            cells.append(f"{a:,} / {m.sum():,} (%{100 * a / m.sum():.2f})")
        out(f"| {lab} | " + " | ".join(cells) + " |")
    out("| Ağ ort. Hz | " + " | ".join(f"{R[n].rate.mean():.2f}" for n in names) + " |")
    out("| Sürülmeyen ort. Hz | " + " | ".join(f"{R[n].rate[~R[n].driven].mean():.3f}" for n in names) + " |")
    out("| ort. adım s / beyin s | " + " | ".join(f"{R[n].b['step_time'].mean():.3f} / "
                                                 f"{R[n].b['brain_time'].mean():.3f}" for n in names) + " |")
    out("")

    sets = neuron_sets(G.load_root_ids())
    sets["DNg02"] = {"L": R[names[0]].groups["dng02_L"], "R": R[names[0]].groups["dng02_R"]}
    out("## DN / MN hızları (Hz/nöron, L / R)\n")
    for n in names:
        r = R[n]
        w, td = r.windows()
        out(f"**{n}** (touchdown adım {td}; pencere adım sayıları: " + ", ".join(f"{k} {len(v)}" for k, v in w.items())
            + ")\n")
        out("| | " + " | ".join(w) + " |\n|---|" + "---|" * len(w))
        for t, d in sets.items():
            per = {s: r.set_counts(d[s]) for s in "LR"}
            cells = []
            for st in w.values():
                if len(st) == 0:
                    cells.append("–")
                    continue
                v = [per[s][st + r.n_pre].sum() / (len(d[s]) * len(st) * DT) for s in "LR"]
                cells.append(f"{v[0]:.1f} / {v[1]:.1f}")
            out(f"| {t} | " + " | ".join(cells) + " |")
        out("")

    out("## B-K1 / B-K3 / B-K4 (SPEC §3.3b tanımları, kayıt)\n")
    npz = np.load(G.DATA_DIR / "neuron_neuropil.npz")
    npl = np.where(npz["frac"] > 0, npz["neuropils"][npz["dominant"]], "(yok)")
    mn9 = sets["MN9"]
    for n in names:
        r = R[n]
        und = ~r.driven
        m = (r.step >= 0) & und[r.nidx]
        ps = np.bincount(r.step[m], weights=r.cnt[m], minlength=r.n_cl) / (und.sum() * DT)
        q = r.n_cl // 4
        first, last = ps[:q].mean(), ps[-q:].mean()
        mu = r.rate[und].mean()
        top = max(((k, r.rate[npl == k].mean()) for k in np.unique(npl)), key=lambda kv: kv[1])
        k1 = mu < 5 and last <= 1.5 * first and top[1] <= 50
        st, rss = r.b["step_time"].mean(), r.meta["peak_rss_gb"]
        c = (r.set_counts(mn9["L"]) + r.set_counts(mn9["R"])) / ((len(mn9["L"]) + len(mn9["R"])) * DT)
        cl = c[r.n_pre:]
        nc = r.b["platform_contact"] == 0
        v4 = cl[nc].mean() if nc.any() else float("nan")
        pr = r.meta["persist_net_rate_hz"]
        out(f"- **{n}**: B-K1 {'geçti' if k1 else 'KALDI'} (sürülmeyen {mu:.3f} Hz, son/ilk %25 "
            f"{last / max(first, 1e-12):.2f}, en yüksek nöropil {top[0]} {top[1]:.2f} Hz); "
            f"B-K3 {'geçti' if st <= 2.0 and rss <= 8 else 'KALDI'} (adım {st:.3f} s, RSS {rss:.2f} GB); "
            f"B-K4 {'geçti' if v4 < 10 else 'KALDI'} (temassız MN9 {v4:.2f} Hz, {int(nc.sum())} adım; perch "
            f"{c[:cfg.CALIB_STEPS].mean():.2f} Hz); kesme 100–200 ms {np.mean(pr[4:8]):.3f} Hz.")
    return paths, R


if __name__ == "__main__":
    main()
