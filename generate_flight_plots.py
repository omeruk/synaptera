#!/usr/bin/env python
"""HDF5 -> 13 flight plots (plots/flight/<run stem>/NN_name.png).

Reads only the HDF5 written by fly_flight_brain_body_simulation.py (file kept
open for the whole run). Time axis = run time from take-off; the 0.25 s
pre-take-off calibration is excluded from the spike plots.

    python generate_flight_plots.py simulations/flight_v9_smoke_data.h5 \
        [--ablation simulations/flight_v10_ablDN_data.h5 ...] [--extra]
"""
import argparse
import json
from pathlib import Path

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

from flight import config as cfg  # noqa: E402

REPO = Path(__file__).resolve().parent
# Categorical slots in fixed order (dataviz reference palette, light mode)
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
LR = {"L": C[0], "R": C[1]}
PHASE_SHADE = {"approach": "#fdf1d8", "touchdown": "#e3f4ea", "feed_extend": "#e3f4ea",
               "feed_eat": "#e3f4ea", "feed_retract": "#e3f4ea"}

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 130, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 1.6, "font.size": 10, "axes.titlesize": 11, "legend.frameon": False,
})


class Run:
    def __init__(self, path):
        self.path = Path(path)
        self.f = h5py.File(path, "r")
        self.meta = {k: self.f["meta"].attrs[k] for k in self.f["meta"].attrs}
        self.b = {k: self.f["behavior"][k][:] for k in self.f["behavior"]}
        self.codes = {v: k for k, v in json.loads(self.f["behavior/phase"].attrs["codes"]).items()}
        self.phase = np.array([self.codes[int(c)] for c in self.b["phase"]])
        self.dt = float(self.meta["decision_interval"])
        # spike clock starts at the first pre-take-off step (calibration + input-cut steps, negative
        # step_idx); older files without step_idx: calib_steps only
        if "spikes/step_idx" in self.f and len(self.f["spikes/step_idx"]):
            self.calib = -min(int(self.f["spikes/step_idx"][:].min()), 0) * self.dt
        else:
            self.calib = float(self.meta["calib_steps"]) * self.dt
        self.t = self.b["t"]
        self.n_steps = len(self.t)
        self.dev = bool(self.meta.get("dev_subnet", False))
        flags = json.loads(self.meta["flags"]) if isinstance(self.meta["flags"], str) else {}
        parts = (["DEV"] if self.dev else []) + [k for k in ("ablate_dn", "ablate_odor", "antenna_real")
                                                 if flags.get(k)]
        self.label = ", ".join(parts) or "full"
        self._spk = None

    @property
    def spikes(self):
        if self._spk is None:
            t = self.f["spikes/all/t"][:].astype(np.float64) - self.calib
            i = self.f["spikes/all/i"][:]
            keep = t >= 0
            self._spk = (t[keep], i[keep])
        return self._spk

    def group(self, name):
        return self.f["spikes/groups"][name][:]

    def bin_edges(self):
        return np.arange(self.n_steps + 1) * self.dt

    def group_rate(self, name):
        """Mean rate per neuron (Hz) per 25 ms decision step."""
        idx = self.group(name)
        t, i = self.spikes
        m = np.isin(i, idx)
        h, _ = np.histogram(t[m], self.bin_edges())
        return h / (len(idx) * self.dt)

    def title(self, s):
        tag = self.path.name.replace("_data.h5", "")
        return f"{s}   [{tag}{'  DEV subnet: NOT a result' if self.dev else ''}]"


def shade_phases(ax, run):
    """Background bands for approach (sand) and feeding (mint) phases."""
    t0 = run.t - run.dt
    for p, col in PHASE_SHADE.items():
        on = run.phase == p
        if not on.any():
            continue
        starts = np.flatnonzero(on & ~np.r_[False, on[:-1]])
        ends = np.flatnonzero(on & ~np.r_[on[1:], False])
        for a, b in zip(starts, ends):
            ax.axvspan(t0[a], run.t[b], color=col, lw=0, zorder=0)


def save(fig, out, name):
    fig.savefig(out / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def step_axes(run, rows, h=1.7, w=11):
    fig, axs = plt.subplots(rows, 1, figsize=(w, h * rows + 0.6), sharex=True, squeeze=False)
    axs = axs[:, 0]
    for ax in axs:
        shade_phases(ax, run)
    axs[-1].set_xlabel("time since take-off (s)")
    return fig, axs


# ── 1 ───────────────────────────────────────────────────────────────────────
def p01_circuit_timeline(run, out):
    rows = [("olfactory (ORN)", [("olf_L", "L"), ("olf_R", "R")]),
            ("LA>ME (vision)", [("vis_L", "L"), ("vis_R", "R")]),
            ("ascending", [("ascending", None)]),
            ("descending (all DN)", [("dn_L", "L"), ("dn_R", "R")]),
            ("SEZ out: brain motor neurons", [("brain_mn", None)])]
    fig, axs = step_axes(run, len(rows))
    tc = run.t - run.dt / 2
    for ax, (lab, gs) in zip(axs, rows):
        for g, side in gs:
            ax.plot(tc, run.group_rate(g), color=LR.get(side, C[2]), label=side or None)
        ax.set_ylabel("Hz / neuron")
        ax.set_title(lab, loc="left")
        if len(gs) > 1:
            ax.legend(loc="upper right", ncol=2)
    fig.suptitle(run.title("Circuit timeline: population rate per 25 ms step"), x=0.01, ha="left")
    fig.text(0.01, -0.01, "Shading: sand = approach, mint = touchdown/feeding.", color=INK2)
    save(fig, out, "01_circuit_timeline.png")


# ── 2 ───────────────────────────────────────────────────────────────────────
def p02_raster(run, out, per_group=150, seed=0):
    rng = np.random.default_rng(seed)
    t, i = run.spikes
    groups = [("olf_L", "olfactory L", C[0]), ("olf_R", "olfactory R", C[1]),
              ("vis_L", "LA>ME L", C[0]), ("vis_R", "LA>ME R", C[1]), ("ascending", "ascending", C[2]),
              ("dn_L", "DN L", C[0]), ("dn_R", "DN R", C[1]), ("brain_mn", "brain MN", C[2])]
    fig, ax = plt.subplots(figsize=(11, 7))
    shade_phases(ax, run)
    y0, ticks = 0, []
    for g, lab, col in groups:
        idx = run.group(g)
        sel = np.sort(rng.choice(idx, min(per_group, len(idx)), replace=False))
        m = np.isin(i, sel)
        row = np.searchsorted(sel, i[m])
        ax.scatter(t[m], y0 + row, s=1.5, color=col, lw=0, rasterized=True)
        ticks.append((y0 + len(sel) / 2, f"{lab} ({len(sel)}/{len(idx)})"))
        y0 += len(sel) + 15
        ax.axhline(y0 - 8, color=GRID, lw=0.8)
    ax.set_yticks([a for a, _ in ticks], [b for _, b in ticks])
    ax.invert_yaxis()
    ax.grid(False)
    ax.set_xlim(0, run.t[-1])
    ax.set_xlabel("time since take-off (s)")
    ax.set_title(run.title("Spike raster, random sample per group (seed 0)"), loc="left")
    save(fig, out, "02_raster_circuits.png")


# ── 3 ───────────────────────────────────────────────────────────────────────
def p03_dn_turn(run, out):
    b = run.b
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    ax = axs[0]
    shade_phases(ax, run)
    ax.plot(run.t, b["turn_odor"], color=C[0], label="odour (hand-made map)")
    ax.plot(run.t, b["turn_dn"], color=C[1], label="DN (connectome, 0.15·ΔDN)")
    ax.plot(run.t, b["turn_loom"], color=C[2], label="loom (FlyVis T5)")
    ax.set_xlabel("time since take-off (s)")
    ax.set_ylabel("turn_bias term")
    ax.legend(loc="lower left", fontsize=8)
    ax.set_title("turn terms", loc="left")
    ax = axs[1]
    yaw = np.degrees(b["omega"][:, 2])
    ax.scatter(b["dn_lr_delta"], yaw, s=10, color=C[1])
    r = np.corrcoef(b["dn_lr_delta"], yaw)[0, 1] if run.n_steps > 2 else np.nan
    ax.set_xlabel("ΔDN = (L−R)/(L+R) − baseline")
    ax.set_ylabel("yaw rate after the step (deg/s)")
    ax.set_title(f"DN asymmetry vs yaw rate, r = {r:+.2f}", loc="left")
    ax = axs[2]
    shade_phases(ax, run)
    ax.plot(run.t, b["steer_L"], color=LR["L"], label="L")
    ax.plot(run.t, b["steer_R"], color=LR["R"], label="R")
    ax.set_xlabel("time since take-off (s)")
    ax.set_ylabel("spikes / 25 ms")
    ax.set_title("DNa01+DNa02 ('steer', record only; ASSUMPTION)", loc="left")
    ax.legend()
    fig.suptitle(run.title("DN steering vs turning"), x=0.01, ha="left")
    fig.tight_layout()
    save(fig, out, "03_dn_steer_turn_coupling.png")


# ── 4 ───────────────────────────────────────────────────────────────────────
def p04_dng02(run, out):
    b = run.b
    fig, axs = step_axes(run, 2, h=2.2)
    axs[0].plot(run.t, b["dng02_L"], color=LR["L"], label="L (13)")
    axs[0].plot(run.t, b["dng02_R"], color=LR["R"], label="R (12)")
    tot = int(b["dng02_L"].sum() + b["dng02_R"].sum())
    axs[0].set_ylabel("spikes / 25 ms")
    axs[0].set_title(f"DNg02 (25 neurons; Namiki 2022, wing amplitude): total {tot} spikes", loc="left")
    axs[0].set_ylim(bottom=-0.5, top=max(3, axs[0].get_ylim()[1]))
    axs[0].legend(loc="upper right")
    axs[1].plot(run.t, b["lift_frac"], color=C[2])
    axs[1].axhline(1.0, color=INK2, lw=0.8, ls="--")
    axs[1].set_ylabel("lift fraction")
    axs[1].set_title("collective (lift / W) — 100% hand-made terms, no DNg02 input", loc="left")
    fig.suptitle(run.title("DNg02 vs collective: connectome contribution to the collective = 0"),
                 x=0.01, ha="left")
    save(fig, out, "04_dng02_collective_coupling.png")


# ── 5 ───────────────────────────────────────────────────────────────────────
def p05_population_heatmap(run, out, top=1500):
    t, i = run.spikes
    counts = np.bincount(i, minlength=int(i.max(initial=0)) + 1)
    act = np.argsort(counts)[::-1][:top]
    act = act[counts[act] > 0]
    pos = np.full(len(counts), -1)
    pos[act] = np.arange(len(act))
    m = pos[i] >= 0
    tb = np.minimum((t[m] / run.dt).astype(int), run.n_steps - 1)
    mat = np.zeros((len(act), run.n_steps), np.float32)
    np.add.at(mat, (pos[i[m]], tb), 1.0)
    mat /= run.dt
    order = np.argsort(np.argmax(mat, axis=1), kind="stable")   # sort by time of peak
    fig, ax = plt.subplots(figsize=(11, 6))
    im = ax.imshow(mat[order], aspect="auto", cmap="Blues", interpolation="nearest",
                   extent=(0, run.n_steps * run.dt, len(act), 0), vmax=np.percentile(mat, 99.5) or 1)
    ax.grid(False)
    ax.set_xlabel("time since take-off (s)")
    ax.set_ylabel(f"{len(act)} most active neurons (sorted by peak time)")
    fig.colorbar(im, ax=ax, label="rate (Hz, 25 ms bins)")
    ax.set_title(run.title("Population activity"), loc="left")
    save(fig, out, "05_population_heatmap.png")


# ── 6 ───────────────────────────────────────────────────────────────────────
def p06_rate_distribution(run, out):
    t, i = run.spikes
    n = int(run.meta.get("n_neurons", i.max(initial=0) + 1))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bins = np.logspace(-1, 3, 49)
    for j, (lab, phases) in enumerate((("cruise", ("takeoff", "cruise")), ("approach", ("approach",)),
                                       ("feeding", ("touchdown", "feed_extend", "feed_eat", "feed_retract")))):
        on = np.isin(run.phase, phases)
        if not on.any():
            continue
        steps = np.flatnonzero(on)
        m = np.isin(np.minimum((t / run.dt).astype(int), run.n_steps - 1), steps)
        rate = np.bincount(i[m], minlength=n) / (len(steps) * run.dt)
        silent = (rate == 0).mean()
        ax.hist(rate[rate > 0], bins=bins, histtype="step", lw=1.8, color=C[j],
                label=f"{lab}: mean {rate.mean():.1f} Hz, silent {100 * silent:.0f}%")
    ax.set_xscale("log")
    ax.set_xlabel("firing rate per neuron (Hz, active neurons)")
    ax.set_ylabel("neurons")
    ax.legend()
    ax.set_title(run.title(f"Firing-rate distribution ({n:,} neurons)"), loc="left")
    save(fig, out, "06_firing_rate_distribution.png")


# ── 7 ───────────────────────────────────────────────────────────────────────
def p07_odor(run, out):
    b = run.b
    fig, axs = step_axes(run, 3)
    axs[0].semilogy(run.t, b["odor_L"], color=LR["L"], label="L")
    axs[0].semilogy(run.t, b["odor_R"], color=LR["R"], label="R")
    axs[0].set_ylabel("C at antenna")
    axs[0].set_title("odour concentration (l_eff sample points)", loc="left")
    axs[0].legend(loc="upper left", ncol=2)
    axs[1].plot(run.t, b["olf_rate_L"], color=LR["L"])
    axs[1].plot(run.t, b["olf_rate_R"], color=LR["R"])
    axs[1].set_ylabel("Hz")
    axs[1].set_title("Poisson input rate to ORNs (hand-made log map, 20–150 Hz)", loc="left")
    tc = run.t - run.dt / 2
    axs[2].plot(tc, run.group_rate("olf_L"), color=LR["L"])
    axs[2].plot(tc, run.group_rate("olf_R"), color=LR["R"])
    axs[2].set_ylabel("Hz / neuron")
    axs[2].set_title("olfactory (ORN) spiking in the brain model", loc="left")
    fig.suptitle(run.title("Odour → olfactory response"), x=0.01, ha="left")
    save(fig, out, "07_odor_olfactory_response.png")


# ── 8 ───────────────────────────────────────────────────────────────────────
def p08_visual(run, out):
    b = run.b
    fig, axs = step_axes(run, 3)
    tc = run.t - run.dt / 2
    axs[0].plot(tc, run.group_rate("vis_L"), color=LR["L"], label="L")
    axs[0].plot(tc, run.group_rate("vis_R"), color=LR["R"], label="R")
    axs[0].set_ylabel("Hz / neuron")
    axs[0].set_title("LA>ME spiking (driven by mean eye luminance)", loc="left")
    axs[0].legend(loc="upper left", ncol=2)
    axs[1].plot(run.t, b["loom_L"], color=LR["L"])
    axs[1].plot(run.t, b["loom_R"], color=LR["R"])
    axs[1].set_ylabel("|T5a|+|T5b|")
    axs[1].set_title("FlyVis T5 motion activity per eye (FlyVis network, not FlyWire)", loc="left")
    axs[2].plot(run.t, b["expansion_rate"], color=C[2])
    axs[2].axhline(cfg.LAND_EXPANSION_TRIG, color=C[7], lw=1, ls="--")
    axs[2].text(run.t[0], cfg.LAND_EXPANSION_TRIG, " landing trigger (hand-made)", color=INK2,
                va="bottom", fontsize=8)
    axs[2].set_ylabel("1/s")
    axs[2].set_title("platform expansion rate (dθ/dt)/θ (geometric)", loc="left")
    fig.suptitle(run.title("Vision: lamina/medulla, T5 loom, landing expansion"), x=0.01, ha="left")
    save(fig, out, "08_visual_lamina_loom.png")


# ── 9 ───────────────────────────────────────────────────────────────────────
def box_faces(box):
    (x0, x1), (y0, y1), (z0, z1) = box
    v = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    f = [[0, 1, 3, 2], [4, 5, 7, 6], [0, 1, 5, 4], [2, 3, 7, 6], [0, 2, 6, 4], [1, 3, 7, 5]]
    return [v[q] for q in f]


def draw_cylinder(ax, cx, cy, r, zt, color):
    a = np.linspace(0, 2 * np.pi, 40)
    for z in (0, zt):
        ax.plot(cx + r * np.cos(a), cy + r * np.sin(a), z, color=color, lw=1)
    for k in range(0, 40, 10):
        ax.plot([cx + r * np.cos(a[k])] * 2, [cy + r * np.sin(a[k])] * 2, [0, zt], color=color, lw=0.8)


def p09_trajectory(run, out):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(projection="3d")
    for box in cfg.TOWERS:
        ax.add_collection3d(Poly3DCollection(box_faces(box), facecolor="#b9bcc6", edgecolor="#7d808a",
                                             alpha=0.35, lw=0.5))
    draw_cylinder(ax, *cfg.TAKEOFF_PEDESTAL, "#8a6d4b")
    draw_cylinder(ax, *cfg.FOOD_PLATFORM, C[5])
    ax.scatter(*cfg.FOOD_POS, color=C[3], s=40, label="food")
    p = run.b["pos"]
    for j, ph in enumerate(("takeoff", "cruise", "approach")):
        on = run.phase == ph
        if on.any():
            ax.plot(*np.where(on[:, None], p, np.nan).T, color=C[j], lw=2, label=ph)
    feed = np.isin(run.phase, list(PHASE_SHADE)[1:])
    if feed.any():
        ax.scatter(*p[feed][0], color=C[4], s=40, label="touchdown")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_zlabel("z (mm)")
    ax.set_xlim(-20, 470)
    ax.set_ylim(-120, 320)
    ax.set_zlim(0, 260)
    ax.set_box_aspect((490, 440, 260))
    ax.view_init(elev=28, azim=-70)
    ax.legend(loc="upper left")
    ax.set_title(run.title("3D trajectory"), loc="left")
    save(fig, out, "09_trajectory_3d.png")


# ── 10 ──────────────────────────────────────────────────────────────────────
def p10_altitude_speed(run, out):
    b = run.b
    fig, axs = step_axes(run, 3, h=2.1)
    axs[0].plot(run.t, b["pos"][:, 2], color=C[0])
    axs[0].axhline(cfg.FOOD_PLATFORM[3], color=C[5], lw=1, ls="--")
    axs[0].axhline(cfg.TOWER1[2][1], color=INK2, lw=0.8, ls=":")
    axs[0].text(run.t[0], cfg.FOOD_PLATFORM[3], " platform top", color=INK2, fontsize=8, va="top")
    axs[0].text(run.t[0], cfg.TOWER1[2][1], " tower top", color=INK2, fontsize=8, va="bottom")
    axs[0].set_ylabel("z (mm)")
    axs[0].set_title("altitude (thorax COM)", loc="left")
    axs[1].plot(run.t, b["speed"], color=C[1], label="|v|")
    if "v_fwd" in b:   # recorded since the v7 diagnosis
        axs[1].plot(run.t, b["v_fwd"], color=C[2], label="forward (along heading)")
    axs[1].axhline(cfg.LAND_SPEED, color=C[7], lw=1, ls="--")
    axs[1].text(run.t[0], cfg.LAND_SPEED, " landing speed target", color=INK2, fontsize=8, va="bottom")
    axs[1].set_ylabel("mm/s")
    axs[1].set_title("speed", loc="left")
    axs[1].legend(loc="upper right", ncol=2)
    axs[2].plot(run.t, np.degrees(b["pitch_down"]), color=C[6])
    axs[2].set_ylabel("deg")
    axs[2].set_title("body tilt target (+ nose-down; hand-made cruise/brake)", loc="left")
    fig.suptitle(run.title("Altitude & speed profile (landing deceleration)"), x=0.01, ha="left")
    save(fig, out, "10_altitude_speed_profile.png")


# ── 11 ──────────────────────────────────────────────────────────────────────
def shares(terms):
    a = {k: np.abs(v).mean() for k, v in terms.items()}
    s = sum(a.values()) or 1.0
    return {k: 100 * v / s for k, v in a.items()}


def p11_decomposition(run, out):
    b = run.b
    turn = {"odour (hand-made)": b["turn_odor"], "DN (connectome)": b["turn_dn"], "loom (FlyVis)": b["turn_loom"]}
    pitch = {"odour (hand-made)": b["pitch_odor"], "v_z damping (hand-made)": b["pitch_alt"],
             "ventral (hand-made)": b["pitch_ventral"], "take-off (hand-made)": b["pitch_takeoff"]}
    fig, axs = plt.subplots(2, 2, figsize=(14, 7), gridspec_kw=dict(width_ratios=(3, 1)))
    for row, (terms, lab) in enumerate(((turn, "turn_bias"), (pitch, "pitch_bias (collective)"))):
        ax = axs[row, 0]
        shade_phases(ax, run)
        for j, (k, v) in enumerate(terms.items()):
            ax.plot(run.t, v, color=C[j], label=k, lw=1.3)
        ax.set_ylabel(lab)
        ax.legend(loc="upper left", fontsize=8, ncol=len(terms))
        ax.set_xlabel("time since take-off (s)")
        ax = axs[row, 1]
        sh = shares(terms)
        names = list(sh)[::-1]
        ax.barh(names, [sh[k] for k in names], color=[C[list(terms).index(k)] for k in names], height=0.6)
        for y, k in enumerate(names):
            ax.text(sh[k] + 1, y, f"{sh[k]:.1f}%", va="center", color=INK)
        ax.set_xlim(0, 115)
        ax.set_xlabel("share of mean |term| (%)")
        ax.grid(axis="y", visible=False)
    hybrid = bool(json.loads(run.meta["flags"]).get("hybrid")) if isinstance(run.meta.get("flags"), str) else False
    title = ("Legacy turn terms (odour/DN/loom) + collective. Hybrid run: turn terms BRAIN/HAND-MADE/FLYVIS/REFLEX "
             "in plot 14" if hybrid else
             "Turn / collective decomposition. Connectome share: turn ≈ DN row (noise level), collective 0%")
    fig.suptitle(run.title(title), x=0.01, ha="left")
    fig.tight_layout()
    save(fig, out, "11_turn_pitch_decomposition.png")


# ── 12 ──────────────────────────────────────────────────────────────────────
def p12_odor_field(run, out):
    o = run.f["odor_field_3d"]
    conc = o["conc"][:]
    blocked = o["blocked"][:]
    org, res = o.attrs["origin"], float(o.attrs["res"])
    ax_ = [org[a] + res * np.arange(conc.shape[a]) for a in range(3)]
    p = run.b["pos"]
    z_s = float(np.clip(np.median(p[:, 2]), ax_[2][0], ax_[2][-1]))
    y_s = float(cfg.FOOD_POS[1])
    kz = int(round((z_s - org[2]) / res))
    ky = int(round((y_s - org[1]) / res))
    fig, axs = plt.subplots(1, 2, figsize=(15, 5.6), gridspec_kw=dict(width_ratios=(1.1, 1)))
    for ax, sl, bl, ext, xy, lab in (
            (axs[0], conc[:, :, kz].T, blocked[:, :, kz].T, (ax_[0][0], ax_[0][-1], ax_[1][0], ax_[1][-1]),
             (p[:, 0], p[:, 1]), f"horizontal slice z = {ax_[2][kz]:.0f} mm (median flight height)"),
            (axs[1], conc[:, ky, :].T, blocked[:, ky, :].T, (ax_[0][0], ax_[0][-1], ax_[2][0], ax_[2][-1]),
             (p[:, 0], p[:, 2]), f"vertical slice y = {ax_[1][ky]:.0f} mm (through the food)")):
        lc = np.log10(np.maximum(sl, 1e-4))
        im = ax.imshow(np.ma.masked_where(bl, lc), origin="lower", extent=ext, cmap="Blues", vmin=-3.5,
                       vmax=0, aspect="equal", interpolation="nearest")
        ax.imshow(np.ma.masked_where(~bl, np.ones_like(lc)), origin="lower", extent=ext, cmap="Greys",
                  vmin=0, vmax=2, aspect="equal", interpolation="nearest")
        ax.plot(*xy, color=C[1], lw=1.8, label="trajectory (projection)")
        ax.scatter(cfg.FOOD_POS[0], cfg.FOOD_POS[1] if ax is axs[0] else cfg.FOOD_POS[2], color=C[3],
                   s=40, zorder=5, label="food")
        ax.grid(False)
        ax.set_title(lab, loc="left")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)" if ax is axs[0] else "z (mm)")
    axs[0].legend(loc="upper left", fontsize=8)
    fig.colorbar(im, ax=axs, label="log10 C  (gray = solid)", shrink=0.85)
    fig.suptitle(run.title("3D odour field (Dijkstra around obstacles) + trajectory"), x=0.01, ha="left")
    save(fig, out, "12_odor_field_3d_slices.png")


# ── 13 ──────────────────────────────────────────────────────────────────────
def p13_distance(run, out, ablations):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    shade_phases(ax, run)
    ax.plot(run.t, run.b["dist_to_food"], color=C[0], lw=2, label=f"{run.path.name} ({run.label})")
    for j, a in enumerate(ablations):
        ax.plot(a.t, a.b["dist_to_food"], color=C[1 + j], label=f"{a.path.name} ({a.label})")
    ax.set_xlabel("time since take-off (s)")
    ax.set_ylabel("distance to food (mm)")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper right", fontsize=8)
    note = "" if ablations else "  (no ablation runs given: --ablation)"
    ax.set_title(run.title("Distance to food" + note), loc="left")
    save(fig, out, "13_distance_to_food.png")


# ── 14 ──────────────────────────────────────────────────────────────────────
TERMS = (("turn_brain", "BRAIN (DNp15)", C[7]), ("turn_hand", "HAND-MADE", "#8a8f96"),
         ("turn_flyvis", "FLYVIS (loom)", C[0]), ("turn_reflex", "REFLEX (haltere PD)", C[2]))


def p14_turn_stack(run, out):
    """Signed stacked turn components per step (hybrid schema); line = commanded turn_total."""
    b = run.b
    if "turn_brain" not in b:
        return
    fig, (ax, axb) = plt.subplots(1, 2, figsize=(14, 4.6), gridspec_kw=dict(width_ratios=(3, 1)))
    shade_phases(ax, run)
    x = run.t - run.dt
    pos = np.zeros(run.n_steps)
    neg = np.zeros(run.n_steps)
    for key, lab, col in TERMS:
        v = b[key]
        vp, vn = np.clip(v, 0, None), np.clip(v, None, 0)
        ax.bar(x, vp, bottom=pos, width=run.dt, align="edge", color=col, lw=0, label=lab)
        ax.bar(x, vn, bottom=neg, width=run.dt, align="edge", color=col, lw=0)
        pos += vp
        neg += vn
    ax.plot(run.t - run.dt / 2, b["turn_total"], color=INK, lw=1.0, label="turn_total (commanded)")
    ax.axhline(0, color=INK2, lw=0.6)
    ax.set_xlabel("time since take-off (s)")
    ax.set_ylabel("turn term")
    ax.legend(loc="upper right", fontsize=8, ncol=3)
    on = b["wings_on"] > 0
    tot = sum(np.abs(b[k][on]).sum() for k, _, _ in TERMS) or 1.0
    names = [lab for _, lab, _ in TERMS][::-1]
    vals = [np.abs(b[k][on]).sum() / tot for k, _, _ in TERMS][::-1]
    axb.barh(names, vals, color=[c for _, _, c in TERMS][::-1], height=0.6)
    for y, v in enumerate(vals):
        axb.text(v + 0.01, y, f"{v:.2f}", va="center", color=INK)
    axb.set_xlim(0, 1.0)
    axb.set_xlabel(f"share of Σ|term| (wings on, {int(on.sum())} steps)")
    axb.grid(axis="y", visible=False)
    ratio = np.abs(b["turn_brain"][on]).sum() / max(np.abs(b["turn_total"][on]).sum(), 1e-12)
    fig.suptitle(run.title(f"Turn components (stacked, signed). Pre-registered Σ|BRAIN|/Σ|total| = {ratio:.2f} "
                           "(terms partly cancel: not a share)"), x=0.01, ha="left")
    fig.tight_layout()
    save(fig, out, "14_turn_components_stack.png")


# ── 15 ──────────────────────────────────────────────────────────────────────
def p15_mn9_contact(run, out):
    b = run.b
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11, 5.2), sharex=True, gridspec_kw=dict(height_ratios=(3, 1)))
    for a in (ax, ax2):
        shade_phases(a, run)
    ax.plot(run.t, b["mn9_rate"], color=C[1], label="MN9 readout (Hz, 50 ms low-pass)")
    ax.axhline(10.0, color=C[7], ls="--", lw=1, label="threshold 10 Hz")
    td = np.flatnonzero(b["phase"] == 4)
    for a in (ax, ax2):
        if len(td):
            a.axvline(run.t[td[0]], color=INK, lw=1, ls=":")
    if len(td):
        ax.text(run.t[td[0]], ax.get_ylim()[1] * 0.95, f" touchdown {run.t[td[0]]:.2f} s", va="top", fontsize=8)
    cross = np.flatnonzero(b["mn9_rate"] > 10.0)
    if len(cross):
        ax.scatter(run.t[cross[0]], b["mn9_rate"][cross[0]], color=C[7], zorder=5,
                   label=f"first > 10 Hz: {run.t[cross[0]]:.2f} s")
    ax.set_ylabel("MN9 (Hz)")
    ax.legend(loc="upper left", fontsize=8)
    ax2.step(run.t, b["platform_contact"], where="post", color=C[2], label="tarsi on platform")
    ax2.step(run.t, b["is_feeding"] * 6.3, where="post", color=C[3], label="is_feeding (scaled)")
    ax2.set_ylabel("legs")
    ax2.set_ylim(-0.3, 6.6)
    ax2.set_xlabel("time since take-off (s)")
    ax2.legend(loc="upper left", fontsize=8, ncol=2)
    fig.suptitle(run.title("Feeding: MN9 readout and platform contact"), x=0.01, ha="left")
    fig.tight_layout()
    save(fig, out, "15_mn9_contact.png")


PLOTS = [p01_circuit_timeline, p02_raster, p03_dn_turn, p04_dng02, p05_population_heatmap,
         p06_rate_distribution, p07_odor, p08_visual, p09_trajectory, p10_altitude_speed,
         p11_decomposition, p12_odor_field]
EXTRA_PLOTS = [p14_turn_stack, p15_mn9_contact]     # --extra (hybrid final runs)


def plot_dir(h5):
    return REPO / "plots" / "flight" / Path(h5).name.replace("_data.h5", "")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("h5")
    ap.add_argument("--ablation", nargs="*", default=[], help="HDF5 runs overlaid on plot 13")
    ap.add_argument("--out", default=None)
    ap.add_argument("--extra", action="store_true", help="also plots 14 (turn components stack), 15 (MN9 + contact)")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else plot_dir(args.h5)
    out.mkdir(parents=True, exist_ok=True)
    run = Run(args.h5)
    for fn in PLOTS:
        fn(run, out)
        print(f"  {fn.__name__}")
    abl = [Run(p) for p in args.ablation]
    p13_distance(run, out, abl)
    for fn in EXTRA_PLOTS if args.extra else []:
        fn(run, out)
        print(f"  {fn.__name__}")
    for a in abl:
        a.f.close()
    run.f.close()
    files = sorted(out.glob("*.png"))
    print(f"{len(files)} plots -> {out}")
    return out


if __name__ == "__main__":
    main()
