"""Publication figures 1-8, drawn from the stored run files and the existing report scripts (no simulation, no render).

    env -u PYTHONPATH python scripts/figures/make_figures.py              # all figures
    env -u PYTHONPATH python scripts/figures/make_figures.py --only fig3  # one figure (fig1 ... fig8)

Output: figures/figN_<name>.png (300 dpi) and .pdf (vector); the plotted data as figures/data/figN_<name>.csv and the
summary numbers that `scripts/verify_report_final.py` re-checks against the report scripts as figures/data/figN_<name>_summary.csv.
Every number in a figure comes from the HDF5 / npz run records or from the report scripts (summary_report, vis_dn_report, vl_report,
o1_report, ladder_trial1_report); the only quoted number without a stored run (leg GRN -> MN9, 0.0 Hz) is read from REPORT.md.
Source labels have one colour and one marker in all figures: BRAIN, HAND-MADE, REFLEX, FLYVIS, TRAINED.
"""
import argparse
import csv
import json
import re
import sys
import textwrap
from pathlib import Path

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "diag"))
OUT = ROOT / "figures"
DATA = OUT / "data"

MM = 1 / 25.4
W1, W2 = 89 * MM, 183 * MM            # single / double column width (inches)

# Okabe-Ito colour and marker per source label (same in every figure)
SRC = {"BRAIN": ("#0072B2", "o"), "HAND-MADE": ("#E69F00", "s"), "REFLEX": ("#009E73", "^"),
       "FLYVIS": ("#CC79A7", "D"), "TRAINED": ("#D55E00", "P")}
GREY, DGREY, LGREY = "#7F7F7F", "#4D4D4D", "#DDDDDD"
C = {k: v[0] for k, v in SRC.items()}
MK = {k: v[1] for k, v in SRC.items()}

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": LGREY, "grid.linewidth": 0.5, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "lines.linewidth": 0.9, "pdf.fonttype": 42, "ps.fonttype": 42,
    "legend.frameon": False, "figure.dpi": 100, "axes.axisbelow": True,
})


# ── helpers ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def letter(ax, s, dx=-20, dy=3):
    ax.annotate(s, xy=(0, 1), xycoords="axes fraction", xytext=(dx, dy), textcoords="offset points", fontsize=9, fontweight="bold",
                ha="left", va="bottom")


def write_csv(name, header, rows):
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def write_summary(name, d):
    write_csv(name, ["key", "value"], [(k, v) for k, v in d.items()])


def save(fig, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png", dpi=300)
    fig.savefig(OUT / f"{stem}.pdf")
    plt.close(fig)
    print("wrote", OUT / f"{stem}.png")


def mean_band(ax, x, Y, color, ls="-", label=None, lw=1.6, alpha=0.18):
    """Mean line (bold) with min-max band over the rows of Y."""
    ax.fill_between(x, Y.min(0), Y.max(0), color=color, alpha=alpha, lw=0, zorder=1)
    ax.plot(x, Y.mean(0), color=color, ls=ls, lw=lw, label=label, zorder=3)


def tint(color, a=0.18):
    c = np.array(matplotlib.colors.to_rgb(color))
    return tuple(1 - a * (1 - c))


def h5_run(arm, seed):
    import seeds_report as SE
    return SE.h5_of(SE.name(arm, seed))


def load_beh(path, keys):
    with h5py.File(path, "r") as f:
        return {k: f["behavior"][k][:] for k in keys}


def td_step(phase):
    td = np.flatnonzero(phase == 4)
    return int(td[0]) if len(td) else None


SEEDS = (3, 10, 11, 12, 13, 14)
START_RUNS = ("st_xp40", "st_xm40", "st_yp40", "st_ym40", "st_yawp30", "st_yawm30", "st_yawp60", "st_yawm60")


def geometry():
    with h5py.File(h5_run("n1", 3), "r") as f:
        return json.loads(f["meta"].attrs["geometry"])


# ── Fig 1: system and labels (drawing only) ──────────────────────────────────────────────────────────────────────────
def fig1():
    fig = plt.figure(figsize=(W2, 126 * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 183)
    ax.set_ylim(0, 126)
    ax.axis("off")
    ax.grid(False)
    B = {}

    def box(key, x, y, w, h, src, title, text, dashed=False):
        """src: a source label or 'SIM' (simulator / body, grey)."""
        col = C.get(src, GREY)
        ls = (0, (3, 2)) if dashed else "-"
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=tint(col, 0.12), ec=col, lw=1.0, ls=ls, zorder=2))
        sh = 5.0
        ax.add_patch(Rectangle((x, y + h - sh), w, sh, fc=col, ec="none", alpha=0.85 if src != "SIM" else 0.5, zorder=3))
        lum = np.dot(matplotlib.colors.to_rgb(col), [0.2126, 0.7152, 0.0722])
        tc = "white" if lum < 0.45 and src != "SIM" else "black"
        tag = src if src != "SIM" else "SIMULATOR"
        if src in MK:
            ax.plot([x + 2.6], [y + h - sh / 2], marker=MK[src], ms=4.2, mfc="white", mec=tc, mew=0.7, zorder=4, ls="none")
        ax.text(x + 5.2 if src in MK else x + 2, y + h - sh / 2, tag, color=tc, fontsize=7, fontweight="bold", va="center", ha="left", zorder=4)
        ax.text(x + 2, y + h - sh - 1.6, title, fontsize=7, fontweight="bold", va="top", ha="left", zorder=4)
        ax.text(x + 2, y + h - sh - 5.4, text, fontsize=7, va="top", ha="left", zorder=4, linespacing=1.15)
        B[key] = (x, y, w, h)

    def pt(key, side, f=0.5):
        x, y, w, h = B[key]
        return {"l": (x, y + f * h), "r": (x + w, y + f * h), "t": (x + f * w, y + h), "b": (x + f * w, y)}[side]

    def arrow(a, sa, b, sb, fa=0.5, fb=0.5, label=None, dashed=False, lpos=(0, 0), color=DGREY):
        p, q = pt(a, sa, fa), pt(b, sb, fb)
        ax.annotate("", xy=q, xytext=p, zorder=5, arrowprops=dict(arrowstyle="-|>", lw=0.9, color=color, ls=(0, (3, 2)) if dashed else "-",
                                                                   shrinkA=0, shrinkB=0, mutation_scale=7))
        if label:
            ax.text((p[0] + q[0]) / 2 + lpos[0], (p[1] + q[1]) / 2 + lpos[1], label, fontsize=7, ha="center", va="center", color="black",
                    bbox=dict(fc="white", ec="none", pad=0.6), zorder=6)

    X = (2, 49.5, 97, 144.5)
    Wd = 36.5
    # row 0: legend + trigger
    box("trig", X[3], 103, Wd, 21, "HAND-MADE", "Feeding trigger", "tarsus–platform contact\ndrives labellar sugar GRNs\n(hand-made shortcut)")
    # row 1: sensing chain into the brain
    box("eyes", X[0], 70, Wd, 25, "SIM", "Compound eyes", "FlyGym renders the\narena and the platform\nfor both eyes")
    box("fv", X[1], 70, Wd, 25, "FLYVIS", "FlyVis network", "pretrained fly-vision\nmodel (not FlyWire);\nalso gives a loom term")
    box("bnd", X[2], 70, Wd, 25, "FLYVIS", "Boundary layer", "output cell types that\nproject to non-FlyVis\nneurons; rates → Poisson")
    box("brain", X[3], 70, Wd, 25, "BRAIN", "Brain model", "FlyWire v783 connectome,\nspiking LIF network,\nwhole brain, no pruning")
    # row 2
    box("sim", X[0], 37, Wd, 25, "SIM", "Simulator state", "position, odour field,\nplatform contact\n(read by hand-made parts)")
    box("body", X[1], 37, Wd, 25, "SIM", "Body", "NeuroMechFly in MuJoCo;\nquasi-steady wing forces;\nclosed loop with the brain")
    box("brdg", X[2], 37, Wd, 25, "HAND-MADE", "DN → wing bridge", "hand-made; the model has\nno ventral nerve cord")
    box("read", X[3], 37, Wd, 25, "BRAIN", "Read-outs", "descending neurons, MN9\n(feeding decision);\nDNp15 steering set to 0")
    # row 3
    xs, w3 = (2, 38.8, 75.6, 112.4, 149.2), 32.6
    box("route", xs[0], 3, w3, 28, "HAND-MADE", "Route", "odour map → turn;\nthrust and tilt from\nthe platform position")
    box("phase", xs[1], 3, w3, 28, "HAND-MADE", "Phase machine", "take-off, cruise,\napproach, descend,\ntouchdown (timers,\ndistance rules)")
    box("refl", xs[2], 3, w3, 28, "REFLEX", "Reflexes", "haltere attitude PD;\nhead stabilisation\n(neck not connected\nto the brain)")
    box("post", xs[3], 3, w3, 28, "HAND-MADE", "Postures", "flight and feeding\nposes; the feeding pose\nstarts on the MN9\ndecision")
    box("trn", xs[4], 3, w3, 28, "TRAINED", "Trained read-out", "ridge fit of DN counts\nto route commands;\nnot completed", dashed=True)
    # arrows
    arrow("eyes", "r", "fv", "l")
    arrow("fv", "r", "bnd", "l")
    arrow("bnd", "r", "brain", "l")
    arrow("trig", "b", "brain", "t")
    arrow("brain", "b", "read", "t")
    arrow("read", "l", "brdg", "r")
    arrow("brdg", "l", "body", "r")
    arrow("body", "l", "sim", "r")
    arrow("sim", "t", "eyes", "b", label="camera")
    arrow("fv", "b", "body", "t", label="loom term", lpos=(0, 0))
    arrow("sim", "b", "route", "t", fa=0.4, fb=0.5)
    arrow("route", "t", "body", "b", fa=0.8, fb=0.2)
    arrow("phase", "t", "body", "b", fa=0.5, fb=0.5)
    arrow("refl", "t", "body", "b", fa=0.35, fb=0.85)
    arrow("read", "b", "post", "t", fa=0.15, fb=0.7)
    ax.text(133, 34, "MN9 > threshold", fontsize=7, ha="right", va="center", zorder=6)
    arrow("read", "b", "trn", "t", fa=0.65, fb=0.6, dashed=True)
    # legend
    ax.text(2, 123, "Source labels (colour and marker are the same in every figure)", fontsize=7, fontweight="bold", va="top")
    items = [("BRAIN", "from the connectome model"), ("HAND-MADE", "hand-written control"), ("REFLEX", "hand-written reflex"),
             ("FLYVIS", "computed by FlyVis"), ("TRAINED", "fitted to teacher flights")]
    ys = [116.5, 110.5, 104.5, 98.5]
    for i, (k, d) in enumerate(items):
        x0, y0 = (2, ys[i]) if i < 3 else (74, ys[i - 3])
        ax.add_patch(Rectangle((x0, y0 - 2.6), 22, 5.2, fc=C[k], ec="none", alpha=0.85))
        lum = np.dot(matplotlib.colors.to_rgb(C[k]), [0.2126, 0.7152, 0.0722])
        tc = "white" if lum < 0.45 else "black"
        ax.plot([x0 + 2.2], [y0], marker=MK[k], ms=4, mfc="white", mec=tc, mew=0.7, ls="none")
        ax.text(x0 + 4.4, y0, k, color=tc, fontsize=7, fontweight="bold", va="center")
        ax.text(x0 + 24, y0, d, fontsize=7, va="center")
    x0, y0 = 74, ys[2]
    ax.add_patch(Rectangle((x0, y0 - 2.6), 22, 5.2, fc=GREY, ec="none", alpha=0.5))
    ax.text(x0 + 2, y0, "SIMULATOR", fontsize=7, fontweight="bold", va="center")
    ax.text(x0 + 24, y0, "simulator or body", fontsize=7, va="center")
    ax.add_patch(Rectangle((2, ys[3] - 2.6), 22, 5.2, fc="white", ec=DGREY, lw=1.0, ls=(0, (3, 2))))
    ax.text(26, ys[3], "dashed outline: not completed", fontsize=7, va="center")
    save(fig, "fig1_system_labels")
    write_csv("fig1_system_labels.csv", ["note"], [("drawing only; no data",)])
    write_summary("fig1_system_labels_summary.csv", {"data": "none (drawing only)"})


# ── Fig 2: flight paths ──────────────────────────────────────────────────────────────────────────────────────────────
def draw_arena(ax, g, view):
    for key in ("tower1", "tower2"):
        (x0, x1), (y0, y1), (z0, z1) = g[key]
        if view == "top":
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#BBBBBB", ec=DGREY, lw=0.6, hatch="////", zorder=1))
        else:
            ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fc="#BBBBBB", ec=DGREY, lw=0.6, hatch="////", zorder=1))
    px, py, pr, ph = g["pedestal"]
    fx, fy, fr, fh = g["food_platform"]
    if view == "top":
        ax.add_patch(Circle((px, py), pr, fc="white", ec=DGREY, lw=0.8, zorder=1))
        ax.add_patch(Circle((fx, fy), fr, fc="white", ec=DGREY, lw=0.8, zorder=1))
    else:
        ax.add_patch(Rectangle((px - pr, 0), 2 * pr, ph, fc="white", ec=DGREY, lw=0.8, zorder=1))
        ax.add_patch(Rectangle((fx - fr, 0), 2 * fr, fh, fc="white", ec=DGREY, lw=0.8, zorder=1))


def fig2():
    g = geometry()
    dashes = ["-", "--", "-.", ":", (0, (5, 1.5, 1, 1.5)), (0, (1, 1))]
    runs = {}
    for arm in ("n1", "n2"):
        for s in SEEDS:
            b = load_beh(h5_run(arm, s), ["pos", "phase", "tower_contact", "t"])
            runs[(arm, s)] = b
    import starts_report as ST
    starts = {n: load_beh(ST.h5_of(n), ["pos", "phase", "tower_contact", "t"]) for n in START_RUNS}
    spread = {arm: max(float(np.abs(runs[(arm, s)]["pos"] - runs[(arm, 3)]["pos"]).max()) for s in SEEDS[1:]) for arm in ("n1", "n2")}
    fig = plt.figure(figsize=(W2, 168 * MM))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.42], left=0.075, right=0.985, top=0.90, bottom=0.215, hspace=0.38, wspace=0.22)
    axs = {}
    rows = []
    for j, arm in enumerate(("n1", "n2")):
        col = C["HAND-MADE"] if arm == "n1" else C["BRAIN"]
        mk = MK["HAND-MADE"] if arm == "n1" else MK["BRAIN"]
        for i, view in enumerate(("top", "side")):
            ax = fig.add_subplot(gs[i, j])
            axs[(i, j)] = ax
            draw_arena(ax, g, view)
            yi = 1 if view == "top" else 2
            if arm == "n1":
                for n, b in starts.items():
                    ax.plot(b["pos"][:, 0], b["pos"][:, yi], color=col, lw=0.5, alpha=0.45, zorder=2)
                    k = td_step(b["phase"])
                    if k is not None:
                        ax.plot(b["pos"][k, 0], b["pos"][k, yi], marker="*", ms=4, color=col, mec="black", mew=0.3, ls="none", zorder=4, alpha=0.8)
            for si, s in enumerate(SEEDS):
                b = runs[(arm, s)]
                p = b["pos"]
                ax.plot(p[:, 0], p[:, yi], color=col, ls=dashes[si], lw=1.1, zorder=3)
                k = td_step(b["phase"])
                tc = np.flatnonzero(b["tower_contact"])
                for t, x, y in zip(("pos", ), (p[:, 0],), (p[:, yi],)):
                    pass
                rows += [(arm, s, view, int(i_), float(b["t"][i_]), *map(float, p[i_])) for i_ in range(len(p)) if view == "top"]
                ax.plot(p[0, 0], p[0, yi], marker="o", ms=3.5, mfc="white", mec="black", mew=0.7, ls="none", zorder=5)
                if k is not None:
                    ax.plot(p[k, 0], p[k, yi], marker="*", ms=9, color=col, mec="black", mew=0.6, ls="none", zorder=6)
                else:
                    ax.plot(p[-1, 0], p[-1, yi], marker="X", ms=6, color=col, mec="black", mew=0.6, ls="none", zorder=6)
                if len(tc):
                    ax.plot(p[tc[0], 0], p[tc[0], yi], marker="v", ms=5, color="white", mec="black", mew=0.8, ls="none", zorder=7)
            ax.set_xlim(-70, 480)
            ax.set_xlabel("x (mm)")
            if view == "top":
                ax.set_ylim(-125, 325)
                ax.set_aspect("equal")
                ax.set_ylabel("y (mm)")
            else:
                ax.set_ylim(0, 235)
                ax.set_aspect("equal")
                ax.set_ylabel("z (mm)")
    t1 = "n1: hand-made route + brain feeding decision\n(6 seeds, dash styles; thin lines: 8 start conditions)\ntop view"
    t2 = "n2: brain only, hand-made flight programme\n(6 seeds, dash styles)\ntop view"
    axs[(0, 0)].set_title(t1, fontsize=7, loc="left")
    axs[(0, 1)].set_title(t2, fontsize=7, loc="left")
    axs[(1, 0)].set_title("n1: side view", fontsize=7, loc="left")
    axs[(1, 1)].set_title("n2: side view", fontsize=7, loc="left")
    for (i, j), s in zip(((0, 0), (0, 1), (1, 0), (1, 1)), "abcd"):
        letter(axs[(i, j)], s, dx=-16)
    h = [Line2D([], [], color=C["HAND-MADE"], lw=1.1, label="n1 route (HAND-MADE; seeds 3, 10–14)"),
         Line2D([], [], color=C["BRAIN"], lw=1.1, label="n2 route (BRAIN only; seeds 3, 10–14)"),
         Line2D([], [], marker="o", mfc="white", mec="black", ls="none", label="start"),
         Line2D([], [], marker="*", ms=9, color=GREY, mec="black", mew=0.6, ls="none", label="touchdown (first contact with the platform)"),
         Line2D([], [], marker="X", ms=6, color=GREY, mec="black", mew=0.6, ls="none", label="end of run, no touchdown"),
         Line2D([], [], marker="v", ms=5, mfc="white", mec="black", ls="none", label="first tower contact"),
         Rectangle((0, 0), 1, 1, fc="#BBBBBB", ec=DGREY, hatch="////", label="towers"), Rectangle((0, 0), 1, 1, fc="white", ec=DGREY, label="start pedestal, food platform")]
    fig.legend(handles=h, loc="lower center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, 0.045), borderaxespad=0)
    fig.text(0.5, 0.012, f"Largest position difference between the 6 seeds over all steps: n1 {spread['n1']:.1f} mm, n2 {spread['n2']:.1f} mm (the seed lines coincide).", fontsize=7, ha="center", va="bottom", color=DGREY)
    save(fig, "fig2_flight_paths")
    # data: top-view positions per step
    write_csv("fig2_flight_paths.csv", ["arm", "seed", "view", "step", "t_s", "x_mm", "y_mm", "z_mm"], rows)
    summ = {"n1_n_seeds": len(SEEDS), "n2_n_seeds": len(SEEDS), "n1_max_diff_mm": spread["n1"], "n2_max_diff_mm": spread["n2"],
            "n1_touchdown": sum(td_step(runs[("n1", s)]["phase"]) is not None for s in SEEDS),
            "n2_touchdown": sum(td_step(runs[("n2", s)]["phase"]) is not None for s in SEEDS),
            "n1_tower_contact_steps": sum(int(runs[("n1", s)]["tower_contact"].sum()) for s in SEEDS),
            "n2_first_tower_contact_step": ";".join(sorted({str(int(np.flatnonzero(runs[("n2", s)]["tower_contact"])[0])) for s in SEEDS})),
            "start_runs_touchdown": sum(td_step(b["phase"]) is not None for b in starts.values()), "start_runs_n": len(starts)}
    write_summary("fig2_flight_paths_summary.csv", summ)


# ── Fig 3: feeding decision ──────────────────────────────────────────────────────────────────────────────────────────
def leg_grn_note():
    """Leg GRN -> MN9 open-loop result: quoted in REPORT.md section 4 (lab-notebook number; no stored run file)."""
    t = (ROOT / "REPORT.md").read_text()
    m = re.search(r"left MN9\s+at ([\d.]+) Hz in (\d+)/(\d+) seeds", t)
    return float(m.group(1)), int(m.group(2)), int(m.group(3))


def fig3():
    import starts_report as ST
    OFF = np.arange(-6, 9)

    def aligned(path):
        b = load_beh(path, ["phase", "mn9_rate", "sugar_rate_in", "is_feeding"])
        k = td_step(b["phase"])
        assert k is not None
        return k, b["mn9_rate"][k + OFF], b["sugar_rate_in"][k + OFF], b["is_feeding"][k + OFF]
    n1 = {f"seed {s}": aligned(h5_run("n1", s)) for s in SEEDS}
    st = {n: aligned(ST.h5_of(n)) for n in START_RUNS}
    thr = 10.0
    fig = plt.figure(figsize=(W2, 112 * MM), constrained_layout=True)
    gs = fig.add_gridspec(2, 2)
    t_ms = OFF * 25
    rows = []

    def mn9_panel(ax, runs, title, name):
        M = np.array([v[1] for v in runs.values()])
        ax.axhline(thr, color="black", lw=0.9, ls=(0, (4, 2)), zorder=2)
        ax.text(t_ms[0] + 3, thr + 1.5, "10 Hz threshold", fontsize=7, va="bottom")
        mean_band(ax, t_ms, M, C["BRAIN"])
        for i, (n, v) in enumerate(runs.items()):
            ax.plot(t_ms, v[1], ls="none", marker=MK["BRAIN"], ms=3.2, mfc=C["BRAIN"], mec="white", mew=0.3, alpha=0.8, zorder=4)
            rows.extend((name, n, int(o), int(tm), float(m), float(sg)) for o, tm, m, sg in zip(OFF, t_ms, v[1], v[2]))
        ax.axvline(0, color=GREY, lw=0.8, zorder=1)
        ax.set_xlim(t_ms[0] - 5, t_ms[-1] + 5)
        ax.set_ylim(0, 95)
        ax.set_ylabel("MN9 rate (Hz)")
        ax.set_xlabel("time relative to the touchdown step (ms)")
        ax.set_title(title, loc="left", fontsize=7)
    axa, axb = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1], sharey=None)
    mn9_panel(axa, n1, f"n1, {len(n1)} seeds: MN9 at touchdown\n(dots = seeds, line = mean, band = min–max)", "n1_seeds")
    mn9_panel(axb, st, f"n1, {len(st)} start conditions: MN9 at touchdown\n(dots = runs, line = mean, band = min–max)", "n1_starts")
    letter(axa, "a")
    letter(axb, "b")
    axc = fig.add_subplot(gs[1, 0])
    S = np.array([v[2] for v in list(n1.values()) + list(st.values())])
    mean_band(axc, t_ms, S, C["HAND-MADE"])
    for v in list(n1.values()) + list(st.values()):
        axc.plot(t_ms, v[2], ls="none", marker=MK["HAND-MADE"], ms=3.2, mfc=C["HAND-MADE"], mec="white", mew=0.3, alpha=0.7, zorder=4)
    axc.axvline(0, color=GREY, lw=0.8, zorder=1)
    axc.set_xlim(t_ms[0] - 5, t_ms[-1] + 5)
    axc.set_ylim(0, 115)
    axc.set_ylabel("labellar sugar GRN drive (Hz)")
    axc.set_xlabel("time relative to the touchdown step (ms)")
    axc.set_title(f"Trigger is HAND-MADE: leg contact drives 36 labellar\nsugar GRNs ({S.shape[0]} runs: 6 seeds + 8 start conditions)", loc="left", fontsize=7)
    letter(axc, "c")
    axd = fig.add_subplot(gs[1, 1])
    hz, k, n = leg_grn_note()
    axd.axhline(thr, color="black", lw=0.9, ls=(0, (4, 2)))
    axd.text(0.55, thr + 1.5, "10 Hz threshold", fontsize=7, va="bottom")
    axd.plot(np.arange(1, n + 1), [hz] * n, ls="none", marker=MK["BRAIN"], ms=6, mfc="white", mec=C["BRAIN"], mew=1.3, clip_on=False)
    axd.set_xlim(0.4, 3.6)
    axd.set_xticks(range(1, n + 1), [f"seed {i}" for i in range(1, n + 1)])
    axd.set_ylim(0, 85)
    axd.set_ylabel("MN9 rate (Hz)")
    axd.set_title("Natural path: 12 leg sugar GRNs → MN9\n(open loop, 3 seeds)", loc="left", fontsize=7)
    axd.text(2, 40, f"MN9 = {hz:.1f} Hz in {k}/{n} seeds\nquoted from the lab notebook;\nno stored run file", fontsize=7, ha="center", va="center", color=DGREY)
    letter(axd, "d")
    save(fig, "fig3_feeding_decision")
    write_csv("fig3_feeding_decision.csv", ["group", "run", "step_rel_touchdown", "t_ms", "mn9_hz", "sugar_grn_drive_hz"], rows)
    n1_mn9_td = [float(v[1][list(OFF).index(0)]) for v in n1.values()]
    st_mn9_td = [float(v[1][list(OFF).index(0)]) for v in st.values()]
    write_summary("fig3_feeding_decision_summary.csv", {
        "n1_n": len(n1), "n1_mn9_ok": sum(x > thr for x in n1_mn9_td), "n1_mn9_min": min(n1_mn9_td),
        "st_n": len(st), "st_mn9_ok": sum(x > thr for x in st_mn9_td),
        "sugar_hz_at_touchdown_all_runs": float(np.unique(S[:, list(OFF).index(0)])[0]) if len(np.unique(S[:, list(OFF).index(0)])) == 1 else -1,
        "leg_grn_mn9_hz": hz, "leg_grn_seeds_k": k, "leg_grn_seeds_n": n})


# ── Fig 4: olfactory lock-up ─────────────────────────────────────────────────────────────────────────────────────────
def fig4():
    import glob
    import o1_report as O
    import so_o1
    dt = so_o1.DT * 1000
    t = (np.arange(80) - 40 + 0.5) * dt                  # step centres, ms relative to the cut
    variants = (("published", "o1", "published model", "-", "o"), ("N1", "o1_N1", "N1 (sign variant)", "--", "s"),
                ("N2", "o1_N2", "N2 (sign variant)", ":", "^"))
    TS, rows, passes, mean_w1 = {}, [], {}, {}
    for key, d, _, _, _ in variants:
        fs = sorted(glob.glob(str(ROOT / "logs" / "smell" / d / "o1_r*_s*.npz")))
        TS[key] = np.array([np.load(f)["pop_AL"] for f in fs])
        for f, y in zip(fs, TS[key]):
            z = np.load(f)
            rows += [(key, float(z["rate"]), int(z["seed"]), int(i), float(t[i]), float(y[i])) for i in range(80)]
        r = O.o1_rows(str(ROOT / "logs" / "smell" / d))
        sm = O.o1_summary(r)
        passes[key] = {rate: sm["npass"][rate] for rate in sorted(r)}
        mean_w1[key] = float(np.mean([x["W1_AL"] for v in r.values() for x in v]))
        assert TS[key].shape[0] == 40
    nf = sorted(glob.glob(str(ROOT / "logs" / "smell" / "o1_nf" / "nf_s*.npz")))
    NF = np.array([np.load(f)["pop_AL"] for f in nf])
    nf_seeds = [int(np.load(f)["seed"]) for f in nf]
    rows += [("nf_upstream_style", 80.0, s, int(i), float(t[i]), float(y[i])) for s, Y in zip(nf_seeds, NF) for i in range(80)]
    import nf_report as N
    nfr = N.nf_rows(None)
    fig = plt.figure(figsize=(W2, 78 * MM), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.3, 1.05, 1.1])
    thr = so_o1.THR

    def yaxis(ax):
        ax.set_yscale("symlog", linthresh=thr, linscale=0.35)
        ax.set_ylim(0, 300)
        ax.set_yticks([0, 0.1, 1, 10, 100])
        ax.set_yticklabels(["0", "0.1", "1", "10", "100"])
        ax.set_ylabel("antennal-lobe rate (Hz)\n(symlog axis: linear below 0.1 Hz)")
        ax.axhline(thr, color="black", lw=0.9, ls=(0, (4, 2)), zorder=2)
        ax.axvline(0, color=GREY, lw=0.8, zorder=1)
        ax.set_xlabel("time relative to end of drive (ms)")
    a = fig.add_subplot(gs[0, 0])
    for key, d, lab, ls, mk in variants:
        mean_band(a, t, TS[key], C["BRAIN"], ls=ls, label=f"{lab}: ≈{mean_w1[key]:.0f} Hz after the cut", lw=1.4, alpha=0.12)
    yaxis(a)
    a.text(t[0], thr * 1.25, "criterion 0.1 Hz", ha="left", va="bottom", fontsize=7)
    a.text(-480, 190, "drive on", ha="center", fontsize=7, color=DGREY)
    a.text(480, 190, "all inputs off", ha="center", fontsize=7, color=DGREY)
    a.axvspan(100, 200, color=LGREY, alpha=0.6, lw=0, zorder=0)
    a.set_ylim(0, 450)
    a.legend(loc="lower left", fontsize=7, bbox_to_anchor=(0.0, 0.2))
    a.set_title("40 runs per variant: mean line, min–max band;\ngrey: 100–200 ms test window", loc="left", fontsize=7)
    letter(a, "a", dx=-22)
    b = fig.add_subplot(gs[0, 1])
    rates = sorted(passes["published"])
    xs = np.arange(len(rates))
    for i, (key, d, lab, ls, mk) in enumerate(variants):
        b.plot(xs + (i - 1) * 0.27, [passes[key][r] for r in rates], ls="none", marker=mk, ms=4, mfc=C["BRAIN"], mec="black", mew=0.4, label=lab, clip_on=False, zorder=5)
    b.axhline(5, color="black", lw=0.9, ls=(0, (4, 2)))
    b.text(len(rates) - 0.6, 5.15, "pass needs 5/5", ha="right", va="bottom", fontsize=7)
    b.set_xticks(xs, [f"{r:g}" for r in rates], rotation=45, ha="right")
    b.set_ylim(0, 5.8)
    b.set_yticks(range(0, 6))
    b.set_xlabel("drive rate of the food-glomerulus ORNs (Hz)")
    b.set_ylabel("seeds passing (of 5)")
    b.set_title("0 of 5 seeds pass at every one of\nthe 8 drive rates, in all three models", loc="left", fontsize=7)
    b.legend(loc="center left", fontsize=7, bbox_to_anchor=(0.0, 0.5))
    letter(b, "b", dx=-18)
    c = fig.add_subplot(gs[0, 2])
    for i, (s, y) in enumerate(zip(nf_seeds, NF)):
        c.plot(t, y, color=C["BRAIN"], lw=0.9, ls=["-", "--", "-.", ":", (0, (5, 1.5, 1, 1.5))][i % 5], label=f"seed {s}")
        c.plot(t[::4], y[::4], ls="none", marker=MK["BRAIN"], ms=2.5, color=C["BRAIN"])
    yaxis(c)
    c.set_ylim(0, 450)
    c.text(t[0], thr * 1.25, "criterion 0.1 Hz", ha="left", va="bottom", fontsize=7)
    c.legend(loc="lower left", fontsize=7, ncol=2, bbox_to_anchor=(0.0, 0.2), columnspacing=0.8, handlelength=1.8)
    c.set_title(f"upstream-style drive ({nfr['summary']['rate_hz']:g} Hz):\n{nfr['summary']['n_pass']}/{nfr['summary']['n']} seeds pass", loc="left", fontsize=7)
    letter(c, "c", dx=-22)
    save(fig, "fig4_olfactory_lockup")
    write_csv("fig4_olfactory_lockup.csv", ["variant", "drive_rate_hz", "seed", "step", "t_ms_rel_cut", "al_rate_hz"], rows)
    summ = {"n_rates": len(rates), "n_seeds": 5}
    for key in passes:
        summ[f"{key}_seeds_passing_total"] = sum(passes[key].values())
        summ[f"{key}_rates_passing_5of5"] = sum(v == 5 for v in passes[key].values())
        summ[f"{key}_mean_al_after_cut_hz"] = mean_w1[key]
        summ[f"{key}_n_runs"] = TS[key].shape[0]
    summ["nf_seeds_pass"] = nfr["summary"]["n_pass"]
    summ["nf_n"] = nfr["summary"]["n"]
    write_summary("fig4_olfactory_lockup_summary.csv", summ)


# ── Fig 5: vision -> DN screen ───────────────────────────────────────────────────────────────────────────────────────
def fig5():
    import vis_dn_report as VD
    import vl_report as VL
    chk = json.load(open(ROOT / "logs" / "vis_dn" / "vd_input_check.json"))
    r = VD.evaluate()
    U = VD.units(VD.dn_table())
    conds = list(range(1, 11))
    names = [VD.COND_NAMES[c] for c in conds]
    fig = plt.figure(figsize=(W2, 178 * MM), constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[0.62, 1.25, 0.9])
    # a: input check
    a = fig.add_subplot(gs[0, :])
    A = [chk["per_condition"][str(c)]["A_in_T4aT5a"] for c in conds]
    a.bar(range(10), A, color=tint(C["FLYVIS"], 0.8), ec=C["FLYVIS"], hatch="////", lw=0.6, width=0.65, zorder=3)
    a.axhline(0, color="black", lw=0.8)
    for i, v in enumerate(A):
        a.text(i, v + (0.03 if v >= 0 else -0.03), f"{v:+.2f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=7)
    a.set_xticks(range(10), names, rotation=30, ha="right")
    a.set_ylim(-0.55, 0.55)
    a.set_ylabel("input asymmetry A_in\n(T4a+T5a, (L−R)/(L+R), a.u.)")
    a.set_title("Rendered FlyVis input to the brain, 200–1000 ms window: " + chk["verdict"] + " (yaw and loom sign checks)", loc="left", fontsize=7)
    letter(a, "a", dx=-22)
    # b: heatmap
    b = fig.add_subplot(gs[1, :])
    cl = VD.CLUSTERS
    M = np.array([[r["rates_val"][k][c][0] for c in conds] for k in cl])
    im = b.imshow(M, aspect="auto", cmap="viridis", vmin=0, vmax=np.ceil(M.max() / 10) * 10, interpolation="nearest")
    b.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            b.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=7, color="white" if v < 0.55 * im.norm.vmax else "black")
    b.set_xticks(range(10), names, rotation=30, ha="right")
    b.set_yticks(range(len(cl)), cl)
    b.tick_params(length=0)
    for s in b.spines.values():
        s.set_visible(False)
    res = {}
    for x in r["apriori"]:
        res.setdefault(x["cluster"], []).append((x["measure"], x["result"]))
    sym = {"PASS": "✓", "FAIL": "✗", "SILENT": "○"}
    for i, k in enumerate(cl):
        txt = "   ".join(f"{m} {sym[v]} {v}" for m, v in res[k])
        bold = any(v == "PASS" for _, v in res[k])
        b.text(9.62, i, txt, ha="left", va="center", fontsize=7, fontweight="bold" if bold else "normal", clip_on=False)
    b.text(9.62, -0.95, "a-priori tests: ✓ PASS ✗ FAIL ○ SILENT", ha="left", va="center", fontsize=7, fontweight="bold", clip_on=False)
    cb = fig.colorbar(im, ax=b, pad=0.01, fraction=0.025, location="left")
    cb.set_label("cluster rate (Hz per neuron)")
    cb.outline.set_visible(False)
    b.set_title(f"A-priori DN clusters: mean of {r['n_val_seeds']} validation seeds, 200–1000 ms", loc="left", fontsize=7)
    letter(b, "b", dx=-46)
    # c: DNp15 left/right
    c = fig.add_subplot(gs[2, 0])
    per = VD.per_seed("main", VD.VAL, U, conds)
    cs = {1: "yaw-CW", 2: "yaw-CCW", 3: "static"}
    rows = []
    for j, (cc, nm) in enumerate(cs.items()):
        for side, si, mk, off in (("left", 1, "o", -0.17), ("right", 2, "s", 0.17)):
            vals = np.array([per["DNp15"][s][2][cc][si] for s in sorted(per["DNp15"])])
            c.plot(np.full(len(vals), j + off) + np.linspace(-0.05, 0.05, len(vals)), vals, ls="none", marker=mk, ms=3.8, mfc=C["BRAIN"] if side == "left" else "white",
                   mec=C["BRAIN"], mew=0.9, alpha=0.9, zorder=4)
            c.hlines(vals.mean(), j + off - 0.14, j + off + 0.14, color="black", lw=1.6, zorder=5)
            rows += [("DNp15", nm, side, s, float(v)) for s, v in zip(sorted(per["DNp15"]), vals)]
    c.set_xticks(range(3), [f"{v}" for v in cs.values()])
    c.set_xlim(-0.6, 2.6)
    c.set_ylim(0, None)
    c.set_ylabel("DNp15 rate (Hz per neuron)")
    c.legend(handles=[Line2D([], [], marker="o", ls="none", mfc=C["BRAIN"], mec=C["BRAIN"], label="left cell"),
                      Line2D([], [], marker="s", ls="none", mfc="white", mec=C["BRAIN"], mew=0.9, label="right cell"),
                      Line2D([], [], color="black", lw=1.6, label="mean of 5 seeds")], loc="upper right", fontsize=7)
    c.set_title("DNp15, left and right cell:\nright cell dominates, also when static", loc="left", fontsize=7)
    letter(c, "c", dx=-22)
    # d: loom (post-hoc)
    d = fig.add_subplot(gs[2, 1])
    Uv = VD.units(VD.dn_table())
    data = VL.load("val", VL.VAL, VL.CONDS)
    seeds = sorted(data)
    stim = (("appearing\nfrontal disc\n(0–200 ms)", 11, VL.WO), ("growing\nfrontal disc\n(700–900 ms)", 6, VL.WL))
    rows_d, dsum = [], {}
    for j, (lab, cond, win) in enumerate(stim):
        for k, (cluster, mk, off) in enumerate((("DNp04", "o", -0.17), ("DNp01", "s", 0.17))):
            m = Uv["type:" + cluster][2]
            vals = np.array([VL.wrate(data[s][cond], m, win) for s in seeds])
            d.plot(np.full(len(vals), j + off) + np.linspace(-0.05, 0.05, len(vals)), vals, ls="none", marker=mk, ms=3.8, mfc=C["BRAIN"] if k == 0 else "white",
                   mec=C["BRAIN"], mew=0.9, alpha=0.9, zorder=4)
            d.hlines(vals.mean(), j + off - 0.14, j + off + 0.14, color="black", lw=1.6, zorder=5)
            rows_d += [(cluster, lab.replace("\n", " "), s, float(v)) for s, v in zip(seeds, vals)]
            dsum[f"{cluster}_{'appear' if cond == 11 else 'grow'}_mean_hz"] = float(vals.mean())
    d.set_xticks(range(2), [s[0] for s in stim])
    d.set_xlim(-0.6, 1.6)
    d.set_ylim(0, None)
    d.set_ylabel("DN rate (Hz per neuron)")
    d.legend(handles=[Line2D([], [], marker="o", ls="none", mfc=C["BRAIN"], mec=C["BRAIN"], label="DNp04"),
                      Line2D([], [], marker="s", ls="none", mfc="white", mec=C["BRAIN"], mew=0.9, label="DNp01"),
                      Line2D([], [], color="black", lw=1.6, label="mean of 5 seeds")], loc="upper right", fontsize=7)
    d.set_title("Loom follow-up, POST-HOC reading (not a test):\nappearing disc drives DNs, growing disc hardly", loc="left", fontsize=7)
    letter(d, "d", dx=-22)
    save(fig, "fig5_vision_dn_screen")
    heat = [("heatmap", k, VD.COND_NAMES[c], float(r["rates_val"][k][c][0])) for k in cl for c in conds]
    write_csv("fig5_vision_dn_screen.csv", ["panel", "item", "condition_or_group", "value"],
              [("a_input_A_in_T4aT5a", names[i], "", float(v)) for i, v in enumerate(A)] + heat
              + [("c_DNp15_" + x[2], x[1], x[3], x[4]) for x in rows] + [("d_loom_posthoc_" + x[0], x[1], x[2], x[3]) for x in rows_d])
    vlr = VL.evaluate()
    summ = {"apriori_n": len(r["apriori"]), "apriori_PASS": r["apriori_counts"]["PASS"], "apriori_FAIL": r["apriori_counts"]["FAIL"],
            "apriori_SILENT": r["apriori_counts"]["SILENT"], "n_val_seeds": r["n_val_seeds"], "vl_apriori_n": len(vlr["apriori"]),
            "vl_apriori_PASS": vlr["apriori_counts"]["PASS"], "vl_apriori_FAIL": vlr["apriori_counts"]["FAIL"],
            "vl_apriori_SILENT": vlr["apriori_counts"]["SILENT"], "input_check_passed": chk["passed"], **dsum}
    for cc, nm in cs.items():
        for si, side in ((1, "L"), (2, "R")):
            summ[f"DNp15_{nm}_{side}_mean_hz"] = float(np.mean([per["DNp15"][s][2][cc][si] for s in per["DNp15"]]))
    # reference values recorded by the loom report (validation means), for the cross-check
    summ["vl_DNp04_appear_ref_hz"] = vlr["rates_val"]["DNp04"]["recede-front|W_on"]
    summ["vl_DNp01_appear_ref_hz"] = vlr["rates_val"]["DNp01"]["recede-front|W_on"]
    summ["vl_DNp04_grow_ref_hz"] = vlr["rates_val"]["DNp04"]["loom-front|W_loom"]
    summ["vl_DNp01_grow_ref_hz"] = vlr["rates_val"]["DNp01"]["loom-front|W_loom"]
    write_summary("fig5_vision_dn_screen_summary.csv", summ)


# ── Fig 6: trained readout, trial 1 ──────────────────────────────────────────────────────────────────────────────────
def fig6():
    import ladder_trial1_report as T
    import summary_report as SR
    S = json.loads((ROOT / "docs" / "ladder" / "trial1_readouts.json").read_text())
    arms = ("real", "shuffled", "bypass")
    arm_lab = {"real": "T1-real (DN counts)", "shuffled": "T1-shuffled (connectome shuffled)", "bypass": "T1-bypass (boundary rates, no brain)"}
    cmds = ("turn_hand", "thrust_hand", "pitch_hand", "roll_hand")
    cmd_lab = {"turn_hand": "turn", "thrust_hand": "thrust", "pitch_hand": "pitch", "roll_hand": "roll"}
    mk = {"real": "o", "shuffled": "s", "bypass": "^"}
    fig = plt.figure(figsize=(W2, 128 * MM), constrained_layout=True)
    gs = fig.add_gridspec(2, 3, height_ratios=[0.9, 1.0])
    fig.suptitle("T1 not completed: no champion in trial 1; trials 2–4 and the exam were not run", fontsize=8, fontweight="bold", x=0.02, ha="left")
    a = fig.add_subplot(gs[0, :])
    ylo = -2.0
    rows = []
    for i, arm in enumerate(arms):
        for j, c in enumerate(cmds):
            v = S["arms"][arm]["cv_r2"][c]
            x = j + (i - 1) * 0.27
            rows.append((arm, c, v))
            if v < ylo:
                a.annotate("", xy=(x, ylo), xytext=(x, ylo + 0.4), arrowprops=dict(arrowstyle="-|>", lw=0.9, color="black"))
                a.text(x + 0.04, ylo + 0.45, f"{v:.1f} (off scale)", ha="left", va="bottom", fontsize=7)
            else:
                a.plot([x], [v], ls="none", marker=mk[arm], ms=6, mfc=C["TRAINED"] if arm == "real" else "white", mec=C["TRAINED"], mew=1.2, zorder=4)
                a.text(x, v + (0.1 if v >= 0 else -0.1), f"{v:+.2f}", fontsize=7, va="bottom" if v >= 0 else "top", ha="center")
    a.axhline(0, color="black", lw=1.6, zorder=3)
    a.text(1.5, 0.06, "R² = 0: no better than the mean", fontsize=7, ha="center", va="bottom")
    a.set_xticks(range(4), [cmd_lab[c] for c in cmds])
    a.set_xlim(-0.5, 3.7)
    a.set_ylim(ylo, 1.3)
    a.set_ylabel("cross-validated R²\n(leave one flight out, 12 flights)")
    a.legend(handles=[Line2D([], [], marker=mk[x], ls="none", ms=6, mfc=C["TRAINED"] if x == "real" else "white", mec=C["TRAINED"], mew=1.2, label=arm_lab[x]) for x in arms],
             loc="lower right", fontsize=7, ncol=1)
    a.set_title("Fitted readouts: command × arm (axis cut at −2)", loc="left", fontsize=7)
    letter(a, "a", dx=-22)
    g = geometry()
    R = T.flights()
    s1 = SR.ladder_s1()
    teacher, trial = {}, {}
    for i in T.VAL:
        done = (ROOT / "logs" / "ladder" / "teacher" / f"DONE_lt{i:02d}").read_text()
        teacher[i] = load_beh(ROOT / re.search(r"^h5=(.+)$", done, re.M).group(1), ["pos", "phase"])
        for arm in arms:
            done = (ROOT / "logs" / "ladder" / "trial1" / f"DONE_t1{arm}_v{i}").read_text()
            trial[(arm, i)] = load_beh(ROOT / re.search(r"^h5=(.+)$", done, re.M).group(1), ["pos", "phase", "tower_contact", "dist_to_food"])
    path_rows = []
    styles = {13: "-", 14: "--", 15: "-.", 16: ":"}
    for j, arm in enumerate(arms):
        ax = fig.add_subplot(gs[1, j])
        draw_arena(ax, g, "top")
        for i in T.VAL:
            p = teacher[i]["pos"]
            ax.plot(p[:, 0], p[:, 1], color="#999999", lw=0.9, ls=styles[i], zorder=2)
        for i in T.VAL:
            p = trial[(arm, i)]["pos"]
            ax.plot(p[:, 0], p[:, 1], color=C["TRAINED"], lw=1.1, ls=styles[i], zorder=3)
            ax.plot(p[0, 0], p[0, 1], marker="o", ms=3, mfc="white", mec="black", mew=0.6, ls="none", zorder=5)
            k = td_step(trial[(arm, i)]["phase"])
            ax.plot(p[-1, 0], p[-1, 1], marker="X" if k is None else "*", ms=5.5 if k is None else 9, color=C["TRAINED"], mec="black", mew=0.5, ls="none", zorder=6)
            tc = np.flatnonzero(trial[(arm, i)]["tower_contact"])
            if len(tc):
                ax.plot(p[tc[0], 0], p[tc[0], 1], marker="v", ms=4.5, mfc="white", mec="black", mew=0.7, ls="none", zorder=7)
            path_rows += [(arm, i, int(s), *map(float, p[s])) for s in range(len(p))]
        for i in T.VAL:
            p = teacher[i]["pos"]
            path_rows += [("teacher", i, int(s), *map(float, p[s])) for s in range(len(p))]
        ax.set_xlim(-60, 470)
        ax.set_ylim(-130, 330)
        ax.set_aspect("equal")
        ax.set_xlabel("x (mm)")
        if j == 0:
            ax.set_ylabel("y (mm)")
        ax.set_title(f"{arm_lab[arm].split(' (')[0]}: S1 {s1[arm][0]}/{s1[arm][1]}, touchdown 0/4", loc="left", fontsize=7)
        letter(ax, "bcd"[j], dx=-18)
        assert all(td_step(trial[(arm, i)]["phase"]) is None for i in T.VAL)
    h = [Line2D([], [], color="#999999", lw=0.9, label="teacher flight, same start (grey)"),
         Line2D([], [], color=C["TRAINED"], lw=1.1, label="trained readout, closed loop (starts 13–16: dash styles)"),
         Line2D([], [], marker="o", mfc="white", mec="black", ls="none", label="start"),
         Line2D([], [], marker="X", ms=5.5, color=C["TRAINED"], mec="black", mew=0.5, ls="none", label="end of run, no touchdown"),
         Line2D([], [], marker="v", ms=4.5, mfc="white", mec="black", ls="none", label="first tower contact")]
    fig.legend(handles=h, loc="outside lower center", ncol=3, fontsize=7)
    save(fig, "fig6_trained_readout")
    write_csv("fig6_trained_readout.csv", ["panel", "arm", "item", "value"],
              [("a_cv_r2", a_, c_, v_) for a_, c_, v_ in rows]
              + [("bcd_path", f"{p[0]}", f"start{p[1]}_step{p[2]}", f"{p[3]:.3f};{p[4]:.3f};{p[5]:.3f}") for p in path_rows])
    summ = {f"cv_r2_{a_}_{c_}": v_ for a_, c_, v_ in rows}
    for arm in arms:
        summ[f"{arm}_S1_ok"], summ[f"{arm}_S1_n"] = s1[arm]
        summ[f"{arm}_touchdown"] = sum(td_step(trial[(arm, i)]["phase"]) is not None for i in T.VAL)
    summ["teacher_flights_shown"] = len(teacher)
    write_summary("fig6_trained_readout_summary.csv", summ)


# ── Fig 7: what the brain controls ───────────────────────────────────────────────────────────────────────────────────
def fig7():
    import summary_report as SR
    v = SR.values()
    R = SR.rows(v)
    key = {
        "Feeding decision after touchdown (MN9 above 10 Hz)": f"MN9 > 10 Hz at touchdown: {v['n1_mn9_ok']}/{v['n1_n']} seeds, {v['st_mn9_ok']}/{v['st_n']} starts",
        "Trigger of the feeding decision (leg contact drives labellar sugar GRNs)": "contact → 36 labellar GRNs (not leg GRNs)",
        "Leg GRN → MN9 path (the natural trigger)": f"MN9 {leg_grn_note()[0]:.1f} Hz in {leg_grn_note()[1]}/{leg_grn_note()[2]} seeds (notebook)",
        "Route to the target": f"n1 S1∧S2 {v['n1_s12']}/{v['n1_n']} seeds, {v['st_s12']}/{v['st_n']} starts; no brain share",
        "Landing sequence (phase machine: take-off, cruise, approach, descend, touchdown)": f"touchdown {v['n1_td']}/{v['n1_n']} n1 seeds",
        "Attitude stabilisation (haltere PD) and head reflex": "hand-set gains; neck not connected to the brain",
        "Brain-only flight (hand-made flight programme only)": f"n2 S1∧S2 {v['n2_s12']}/{v['n2_n']}, touchdown {v['n2_td']}/{v['n2_n']}",
        "Steering from brain DNs (DNp15, closed loop)": f"validation: optomotor sign {v['val_a']}, b1 {v['val_b'][0]}, b2 {v['val_b'][1]}, b3 {v['val_b'][2]}",
        "Altitude and thrust from DNg02": f"DNg02 spikes in 7 runs: {v['dng02']}",
        "Olfaction (brain's olfactory circuit)": f"{v['o1_pass'].split(' drive')[0]} rates return to rest (O1); N1/N2 and upstream-style drive: none",
        "Vision → descending neurons (open loop)": f"{v['vd_pass']}/{v['vd_n']} a-priori tests passed (DNp15)",
        "Loom tracking by DNs (open loop)": f"{v['vl_pass']}/{v['vl_n']} a-priori tests passed",
        "Trained readout of the DNs for the route commands (T1)": f"S1 {v['t1']['real'][0]}/{v['t1']['real'][1]} in all three arms; trials 2–4 not run",
        "Visual input to the brain": f"{v['vb_types']} boundary-layer types, {v['vb_n']:,} neurons",
    }
    assert [r[0] for r in R] == list(key), "summary rows changed"

    def status_kind(s):
        return "shown" if s.startswith("shown") else s
    n = len(R)
    fig = plt.figure(figsize=(W2, 150 * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 183)
    ax.set_ylim(0, 150)
    ax.axis("off")
    ax.grid(False)
    x_fn, x_src, x_st, x_ev = 3, 70, 97, 130
    top = 143
    rh = (top - 14) / n
    for x, t_ in ((x_fn, "Function"), (x_src, "Source"), (x_st, "Status"), (x_ev, "Key number (recomputed)")):
        ax.text(x, 148, t_, fontsize=7, fontweight="bold", va="center")
    ax.plot([0, 183], [top + 1.5, top + 1.5], color="black", lw=0.8)
    ic = {"shown": ("o", "black"), "not shown": ("X", "black"), "not completed": ("s", "black")}
    csv_rows = []
    for i, (fn, src, ev, st) in enumerate(R):
        y = top - (i + 0.5) * rh
        if i % 2 == 0:
            ax.add_patch(Rectangle((0, y - rh / 2), 183, rh, fc="#F5F5F5", ec="none", zorder=0))
        ax.add_patch(Rectangle((0, y - rh / 2 + 0.3), 1.6, rh - 0.6, fc=C[src], ec="none"))
        ax.text(x_fn, y, textwrap.fill(fn, 46), fontsize=7, va="center", linespacing=1.1)
        col = C[src]
        lum = np.dot(matplotlib.colors.to_rgb(col), [0.2126, 0.7152, 0.0722])
        ax.add_patch(FancyBboxPatch((x_src, y - 2.6), 24, 5.2, boxstyle="round,pad=0,rounding_size=1", fc=col, ec="none", alpha=0.9))
        tc = "white" if lum < 0.45 else "black"
        ax.plot([x_src + 2.6], [y], marker=MK[src], ms=4, mfc="white", mec=tc, mew=0.7, ls="none")
        ax.text(x_src + 5.2, y, src, fontsize=7, fontweight="bold", color=tc, va="center")
        kind = status_kind(st)
        m, c_ = ic[kind]
        if kind == "shown":
            ax.plot([x_st + 2], [y], marker="o", ms=5.5, mfc="black", mec="black", ls="none")
        elif kind == "not shown":
            ax.plot([x_st + 2], [y], marker="x", ms=6, mec="black", mew=1.6, ls="none")
        else:
            ax.plot([x_st + 2], [y], marker="s", ms=5.5, mfc="white", mec="black", mew=1.0, ls="none")
            ax.plot([x_st + 2], [y], marker="_", ms=4, color="black")
        short = {"shown (given the hand-made trigger)": "shown (given the\nhand-made trigger)", "shown (hand-made shortcut)": "shown (hand-made)",
                 "shown (hand-made; no brain contribution)": "shown (hand-made)", "shown (hand-made)": "shown (hand-made)", "shown (hand-set)": "shown (hand-set)",
                 "not shown": "not shown", "not completed": "not completed", "shown (input only)": "shown (input only)"}[st]
        ax.text(x_st + 4.5, y, textwrap.fill(short, 17), fontsize=7, va="center", linespacing=1.1)
        ax.text(x_ev, y, textwrap.fill(key[fn], 38), fontsize=7, va="center", linespacing=1.1)
        csv_rows.append((fn, src, st, key[fn]))
    ax.plot([0, 183], [top - n * rh - 0.5, top - n * rh - 0.5], color="black", lw=0.8)
    yl = 5
    ax.plot([x_fn], [yl], marker="o", ms=5.5, mfc="black", mec="black", ls="none")
    ax.text(x_fn + 3, yl, "shown", fontsize=7, va="center")
    ax.plot([x_fn + 22], [yl], marker="x", ms=6, mec="black", mew=1.6, ls="none")
    ax.text(x_fn + 25, yl, "not shown", fontsize=7, va="center")
    ax.plot([x_fn + 52], [yl], marker="s", ms=5.5, mfc="white", mec="black", mew=1.0, ls="none")
    ax.plot([x_fn + 52], [yl], marker="_", ms=4, color="black")
    ax.text(x_fn + 55, yl, "not completed", fontsize=7, va="center")
    ax.text(x_fn + 85, yl, "Words in parentheses give the limit of a shown\nresult (hand-made trigger, hand-set constants).", fontsize=7, va="center", color=DGREY)
    save(fig, "fig7_what_the_brain_controls")
    write_csv("fig7_what_the_brain_controls.csv", ["function", "source", "status", "key_number"], csv_rows)
    write_summary("fig7_what_the_brain_controls_summary.csv", {"n_rows": n, **{f"row{i + 1}": f"{r[0]}|{r[1]}|{r[3]}" for i, r in enumerate(R)}})


# ── Fig 8: brain activity snapshots ──────────────────────────────────────────────────────────────────────────────────
# class colours of the brain panels = those of the videos (render_flight_video_v2.CLASS_RGB); a display setting
CLASS_RGB8 = {"other": (255, 205, 140), "visual": (70, 150, 255), "olfactory": (0, 225, 175), "taste": (255, 105, 200),
              "DN": (255, 50, 30), "motor": (255, 150, 0)}
FIG8_PERCH_STEP = -9      # last perch step with the sensory drive on (steps -8..-1 are the input cut; step 0 = take-off)


def fig8_moments(h5path):
    """The four moments (run step, label, phase) from the run record: perch, cruise between the towers, touchdown, feeding."""
    with h5py.File(h5path, "r") as f:
        b = f["behavior"]
        phase, x, mn9, feed = b["phase"][:], b["pos"][:], b["mn9_rate"][:], b["is_feeding"][:]
        codes = json.loads(b["phase"].attrs["codes"])      # name -> code
    k_cr = int(np.flatnonzero((phase == codes["cruise"]) & (x[:, 0] >= 240))[0])          # first cruise step past x = 240 mm (towers: 160-200, 280-320)
    k_td = int(np.flatnonzero(phase == codes["touchdown"])[0])
    k_fd = int(np.flatnonzero((mn9 > 50) & (feed > 0))[0])                                 # first step with MN9 > 50 Hz
    return [("perch", FIG8_PERCH_STEP), ("cruise", k_cr), ("touchdown", k_td), ("feeding", k_fd)]


def fig8_data(h5path=None):
    """Per moment: firing neuron indices (count > 0 in that 25 ms step), their class, network mean rate, MN9 readout."""
    path = h5path or h5_run("n1", 3)
    mom = fig8_moments(path)
    out = []
    with h5py.File(path, "r") as f:
        si, ni, cn = f["spikes/step_idx"][:], f["spikes/neuron_idx"][:], f["spikes/count"][:]
        b = f["behavior"]
        n = int(f["meta"].attrs["n_neurons"])
        dt = float(f["meta"].attrs["decision_interval"])
        mn9, t = b["mn9_rate"][:], b["t"][:]
        perch_mn9 = float(np.mean(json.loads(f["meta"].attrs["readout_perch_hz"])[2]))     # recorded perch readout (no per-step record before step 0)
        for name, k in mom:
            m = si == k
            idx = ni[m]
            out.append(dict(moment=name, step=k, t_s=float(t[k]) if k >= 0 else float("nan"), idx=idx, n_fire=int(len(idx)),
                            n_spikes=int(cn[m].sum()), rate_hz=float(cn[m].sum()) / n / dt, mn9_hz=perch_mn9 if k < 0 else float(mn9[k])))
    return out, n


def fig8():
    path = h5_run("n1", 3)
    mom, n = fig8_data(path)
    cen = np.load(ROOT / "data" / "neuron_arbor_centroids.npz")
    cls = np.load(ROOT / "data" / "neuron_class.npz")
    xyz = cen["xyz"].astype(np.float64) / 1e3                                  # um
    labels = [str(s) for s in cls["labels"]]
    c = cls["cls"]
    lo, hi = xyz.min(0), xyz.max(0)
    u, v = (hi[0] - xyz[:, 0]), (xyz[:, 1] - lo[1])                            # frontal view; the fly's left on the right of the panel (as in the videos)
    asp = (hi[1] - lo[1]) / (hi[0] - lo[0])
    pw = 58.0
    ph = pw * asp
    fw, fh = 183.0, 130.0
    fig = plt.figure(figsize=(W2, fh * MM))
    rgb = {k: np.array(val) / 255 for k, val in CLASS_RGB8.items()}
    cloud = np.array((120, 150, 200)) / 255
    rows = []
    class_rows = []
    y1 = fh - 17 - ph
    y2 = y1 - ph - 15                                                          # room under each panel for its information line
    pos = [(8, y1), (70, y1), (8, y2), (70, y2)]                               # panel left/bottom in mm: 2 x 2
    ZO = {"visual": 2, "other": 3, "olfactory": 4, "DN": 5, "motor": 6, "taste": 7}   # sparse classes drawn above the crowded visual one
    ALPHA = {"visual": 0.13}                                                   # display setting; all other classes 0.85 (dot size equal for all classes)
    DOT_S = 0.6
    n_by = {m["moment"]: {lab: int(np.sum(c[m["idx"]] == ci)) for ci, lab in enumerate(labels)} for m in mom}
    for (name, x0, y0), M, lt in zip([(m["moment"], *p) for m, p in zip(mom, pos)], mom, "abcd"):
        ax = fig.add_axes([x0 / fw, y0 / fh, pw / fw, ph / fh])
        ax.set_facecolor("black")
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.scatter(u, v, s=0.12, color=cloud, alpha=0.16, lw=0, rasterized=True)
        fire = M["idx"]
        for ci, lab in enumerate(labels):
            sel = fire[c[fire] == ci]
            if len(sel):
                ax.scatter(u[sel], v[sel], s=DOT_S, color=rgb[lab], alpha=ALPHA.get(lab, 0.85), lw=0, zorder=ZO[lab], rasterized=True)
            class_rows.append((name, lab, int(len(sel))))
        ax.set_xlim(0, hi[0] - lo[0])
        ax.set_ylim(hi[1] - lo[1], 0)
        ax.set_aspect("equal")
        when = f"step {M['step']}, t = {M['t_s']:.3f} s" if M["step"] >= 0 else f"step {M['step']}".replace("-", "\u2212")
        ax.set_title({"perch": "Perch", "cruise": "Cruise, between towers", "touchdown": "Touchdown", "feeding": "Feeding"}[name] + f" ({when})",
                     loc="left", fontsize=7, pad=2)
        info_y = -0.035
        if name in ("touchdown", "feeding"):                                   # feeding circuit: thin ring, leader line to a label under the panel (nothing over the image)
            prev = mom[[m["moment"] for m in mom].index(name) - 1]["moment"]
            tc = np.flatnonzero(c == labels.index("taste"))
            cx, cy = float(np.median(u[tc])), float(np.median(v[tc]))
            Wd, Hd = hi[0] - lo[0], hi[1] - lo[1]
            ax.add_patch(matplotlib.patches.Ellipse((cx, cy), 0.20 * Wd, 0.26 * Hd, fc="none", ec="white", lw=0.6, zorder=9))
            ax.annotate(f"taste GRNs and motor neurons fire after\ntouchdown ({prev} \u2192 {name}):\ntaste {n_by[prev]['taste']} \u2192 {n_by[name]['taste']}, motor {n_by[prev]['motor']} \u2192 {n_by[name]['motor']} neurons per step",
                        xy=(cx, cy + 0.13 * Hd), xycoords="data", xytext=(0.0, -0.035), textcoords="axes fraction", fontsize=7, va="top", ha="left", linespacing=1.25,
                        annotation_clip=False, arrowprops=dict(arrowstyle="-", color="white", lw=0.6, shrinkA=0, shrinkB=0, relpos=(min(max(cx / Wd, 0.05), 0.95) * 0.0 + 0.5, 1.0)))
            info_y = -0.37
        ax.text(0.0, info_y, f"{M['n_fire']:,} neurons fired in this 25 ms step\nnetwork mean {M['rate_hz']:.1f} Hz", transform=ax.transAxes,
                fontsize=7, va="top", ha="left", linespacing=1.25)
        letter(ax, lt, dx=-7)
        rows.append((name, M["step"], "" if M["step"] < 0 else round(M["t_s"], 3), M["n_fire"], M["n_spikes"], round(M["rate_hz"], 4), round(M["mn9_hz"], 4)))
    # MN9 panel
    axm = fig.add_axes([145 / fw, y2 / fh, 33 / fw, (2 * ph + 15 - 12) / fh])
    names = [m["moment"] for m in mom]
    vals = [m["mn9_hz"] for m in mom]
    axm.bar(range(4), vals, color=C["BRAIN"], width=0.6, zorder=3)
    axm.axhline(10, color="black", ls=(0, (3, 2)), lw=0.8, zorder=4)
    axm.text(-0.45, 11.5, "threshold 10 Hz", fontsize=7, ha="left", va="bottom")
    for i, val in enumerate(vals):
        axm.text(i, val + 1.5, f"{val:.0f}", ha="center", va="bottom", fontsize=7)
    axm.set_xticks(range(4), names, rotation=35, ha="right")
    axm.set_ylabel("MN9 readout (Hz)")
    axm.set_ylim(0, max(vals) * 1.18)
    axm.set_title("MN9 readout (BRAIN)\nat the same moments", loc="left", fontsize=7)
    letter(axm, "e", dx=-30, dy=14)
    # legend (display setting)
    hs = [Line2D([], [], marker="o", ls="none", ms=3.2, mfc=rgb[k], mec="none", label=k) for k in labels]
    hs.append(Line2D([], [], marker="o", ls="none", ms=2, mfc=cloud, mec="none", alpha=0.5, label="all other neurons (not firing)"))
    fig.legend(handles=hs, loc="upper left", bbox_to_anchor=(8 / fw, 1 - 2.2 / fh), ncol=7, fontsize=7, handletextpad=0.1, columnspacing=1.0, frameon=False)
    cap = ("Display settings, not measurements: dot position (arbor centroid of each neuron, frontal view; the fly's left is on the right), class colour, dot size (equal for all classes), dot opacity (visual 13 %, other classes 85 %), drawing order and the dim background cloud. "
           "Measured in the model: which neurons fired in the 25 ms step, their number, the network mean rate, the MN9 readout (perch: recorded perch mean; step \u22129 = last perch step "
           "before the input cut). Run: n1, seed 3. Visual input comes from FlyVis (FLYVIS); the route is hand-made (HAND-MADE); the only behaviour the brain controls is the "
           "feeding decision (BRAIN: MN9 > 10 Hz).")
    cap = textwrap.fill(cap, 122)
    fig.text(8 / fw, 1.5 / fh, cap, fontsize=7, va="bottom", ha="left", color=DGREY, linespacing=1.25)
    save(fig, "fig8_brain_snapshots")
    write_csv("fig8_brain_snapshots.csv", ["moment", "step", "t_s", "n_neurons_fired", "n_spikes", "network_rate_hz", "mn9_hz"], rows)
    write_csv("fig8_brain_snapshots_by_class.csv", ["moment", "class", "n_neurons_fired"], class_rows)
    summ = {"seed": 3, "n_neurons": n, "perch_step": FIG8_PERCH_STEP}
    for r in rows:
        summ.update({f"{r[0]}_step": r[1], f"{r[0]}_n_fired": r[3], f"{r[0]}_rate_hz": r[5], f"{r[0]}_mn9_hz": r[6]})
    write_summary("fig8_brain_snapshots_summary.csv", summ)


FIGS = {"fig1": fig1, "fig2": fig2, "fig3": fig3, "fig4": fig4, "fig5": fig5, "fig6": fig6, "fig7": fig7, "fig8": fig8}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=sorted(FIGS), help="one figure")
    a = ap.parse_args()
    for k in ([a.only] if a.only else sorted(FIGS)):
        FIGS[k]()
