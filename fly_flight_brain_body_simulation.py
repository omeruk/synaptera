#!/usr/bin/env python
"""NeuroFly flight: FlyWire v783 brain (Brian2 LIF) + FlyGym body, closed loop in 3D.

Every 25 ms decision step:
    sensors (odor at the antennae, compound eyes -> FlyVis -> T4/T5 per neuron,
    tarsus contact with the food platform)
    -> Poisson input rates (brain-control Step 0 inputs: food-odour ORNs, sugar
       GRNs, T4/T5; ascending only with --asc-legacy)
    -> net.run(25 ms) -> incremental spike count
    -> readouts (flight/readouts.py) -> VNC bridge (flight/vnc_bridge.py):
       proboscis extension = MN9 > threshold (Step 1)
       yaw: turn_bias = -K * normalised DNp15 L-R only (Step 2 decisions, post-hoc readout;
       DNa02 recorded; no odor, b_loom or all-DN term)
    -> controller (turn / collective / body pitch, phases)
    -> 250 physics steps (stroke-averaged aero + HAND-MADE haltere reflex),
       both eyes rendered VIS_SUBFRAMES times for the next FlyVis step
    -> record.
Before take-off: perch calibration (CALIB_STEPS), then all brain inputs are cut
for PERSIST_CUT_STEPS (persistent-activity measurement, stored in /meta).
When the loop ends the HDF5 (behaviour + spikes) is written BEFORE any video
rendering. Spec: SPEC_FLIGHT.md. Run with `env -u PYTHONPATH` (see SPEC §0).

    python fly_flight_brain_body_simulation.py --n-steps 20 --dev-subnet --no-video   # smoke
"""
import argparse
import gc
import os
import re
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco  # noqa: E402
import numpy as np  # noqa: E402
import psutil  # noqa: E402

from flight import config as cfg  # noqa: E402
from flight import controller as ctl  # noqa: E402
from flight import groups as G  # noqa: E402
from flight import head_reflex as HR  # noqa: E402
from flight import hybrid as H  # noqa: E402
from flight import quasi_steady as qs  # noqa: E402
from flight import readout_model as RM  # noqa: E402
from flight import sensors as S  # noqa: E402
from flight.body import FlightBody  # noqa: E402
from flight.brain import BRAIN_DT, DEV_MIN_SYN, FlightBrain  # noqa: E402
from flight import visual_input as V  # noqa: E402
from flight import vision_boundary as VB  # noqa: E402
from flight.readouts import READOUT_TYPES, Readouts  # noqa: E402
from flight.readouts import STEER_DRIVE, STEER_TYPES  # noqa: E402
from flight.vnc_bridge import (ABLATION_SETS, K_STEER, MN9_THRESHOLD_HZ, PATH_DN_REFERENCE, READOUT_TAU,  # noqa: E402
                               Bridge, load_reference)
from flight.odor_field_3d import build_arena_odor_field  # noqa: E402
from flight.recorder import SIM_DIR, BehaviorRecorder, ReadoutRecorder, SparseSpikeCounts, h5_path, write_h5  # noqa: E402

REPO = Path(__file__).resolve().parent
DT = cfg.PHYSICS_STEPS_PER_DECISION * cfg.PHYSICS_DT   # 25 ms
PLAY_SPEED, FPS = 0.25, 30                            # video: 0.25x real time, 30 fps
FRAME_DT = PLAY_SPEED / FPS                           # sim seconds between video frames
RSS_WARN_GB = 12.0
YAW_PERTURB_S = 0.1   # s, duration of the --yaw-perturb torque pulse (SPEC Step 2 decisions (b))


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-steps", type=int, default=160, help="decision steps after the 0.25 s calibration")
    ap.add_argument("--dev-subnet", action="store_true",
                    help=f"DEV only: groups + partners with >= {DEV_MIN_SYN} synapses (never a result)")
    ap.add_argument("--dev-subnet-full", action="store_true", help="DEV only: groups + all 1-hop partners")
    ap.add_argument("--ablate-dn", action="append", nargs="?", const="steer", choices=sorted(ABLATION_SETS),
                    help="readout set replaced by its perch baseline (default set: steer; legacy: turn_dn = 0); "
                         "repeatable")
    ap.add_argument("--swap-dn-lr", action="append", nargs="?", const="steer", choices=["steer"],
                    help="exchange the normalised L/R steering channels (turn sign test)")
    ap.add_argument("--platform-neutral", action="store_true",
                    help="control: the food platform has the obstacle checker (default: uniformly dark, Step 2)")
    ap.add_argument("--spawn-air", type=float, nargs=4, metavar=("X", "Y", "Z", "YAW_DEG"), default=None,
                    help="EXPERIMENT DESIGN: start hovering in the air at X Y Z (mm), heading YAW_DEG; calibration "
                         "and input cut while hovering (wings on), then cruise")
    ap.add_argument("--hover", action="store_true",
                    help="EXPERIMENT DESIGN (with --spawn-air): stay hovering, body tilt 0 (no cruise pitch)")
    ap.add_argument("--yaw-perturb", type=float, nargs=2, metavar=("T_S", "DEG"), default=None,
                    help=f"EXPERIMENT DESIGN: external yaw torque pulse at closed-loop time T_S for "
                         f"{YAW_PERTURB_S} s, sized so that passive damping alone turns DEG (+ = left/CCW)")
    ap.add_argument("--ablate-mn9", action="store_true", help="= --ablate-dn mn9 (proboscis never extends)")
    ap.add_argument("--hybrid", action="store_true",
                    help="honest hybrid (flight/hybrid.py): HAND odor navigation, altitude, approach and "
                         "landing + BRAIN DNp15 yaw term + FLYVIS b_loom; feeding only by MN9; every term "
                         "recorded separately")
    ap.add_argument("--no-brain-steer", action="store_true",
                    help="POST-HOC control (SPEC_SENSORY_INPUTS §3.3d): the DNp15 yaw term is exactly 0 (no perch "
                         "baseline constant either); the readout is still computed and recorded")
    ap.add_argument("--head-reflex", action="store_true",
                    help="HAND reflex (SPEC_SENSORY_INPUTS §3.3d, flight/head_reflex.py): neck joints counter-rotate "
                         "the body angular velocity (gaze stabilisation); the eyes move with the head. Default off")
    ap.add_argument("--postures", action="store_true",
                    help="HAND postures (SPEC_SENSORY_INPUTS §3.3d): flight leg pose (forelegs forward folded, middle/"
                         "hind legs back) instead of the tuck pose; on the platform stand <-> feeding pose (forward "
                         "lean) following the MN9 feeding decision; PD ramps. Default off")
    ap.add_argument("--start-on-platform", action="store_true",
                    help="EXPERIMENT DESIGN: start standing on the food platform (sugar contact from the first "
                         "closed-loop step; perch calibration without sugar), wings off")
    ap.add_argument("--start-offset", type=float, nargs=2, metavar=("DX", "DY"), default=[0.0, 0.0],
                    help="EXPERIMENT DESIGN (SPEC_SENSORY_INPUTS §3.3f): move the take-off pedestal and the fly's "
                         "start by DX DY mm (default 0 0 = unchanged)")
    ap.add_argument("--start-yaw", type=float, default=0.0, metavar="DEG",
                    help="EXPERIMENT DESIGN (SPEC_SENSORY_INPUTS §3.3f): initial heading on the pedestal, deg "
                         "(+ = left/CCW; default 0 = facing +x, unchanged)")
    ap.add_argument("--ablate-odor", action="store_true", help="turn_odor = pitch_odor = 0")
    ap.add_argument("--antenna-real", action="store_true", help="steer with the real antenna l = 0.5 mm")
    ap.add_argument("--asc-legacy", action="store_true",
                    help="drive all 1736 ANs with |omega| (Stage 4 input, no anatomical basis); default 0")
    ap.add_argument("--untextured", action="store_true", help="uniform arena colours (replay comparison)")
    ap.add_argument("--apl-graded", action="store_true",
                    help="APL output as graded global KC inhibition (flight/brain.py; gain from KC sparseness)")
    ap.add_argument("--no-olfaction", action="store_true",
                    help="odour fully off: no food-ORN input to the brain (not even spontaneous) and "
                         "turn_odor = pitch_odor = 0 (implies --ablate-odor, except with --hybrid: there only "
                         "the brain input is off, the HAND odor navigation stays); for clean visual steering")
    ap.add_argument("--nt-modulatory-silent", nargs="?", const="broad", default=None, choices=G.NT_SILENT_VARIANTS,
                    help="flag-only exception to the NT rule: outgoing fast synapses of DA/SER/OCT (+ no-NT: broad) "
                         "neurons (Codex v783) -> weight 0; Poisson input neurons never silenced "
                         "(SPEC_BRAIN_CONTROL Step 0 decisions II)")
    ap.add_argument("--nt-literature", action="store_true",
                    help="flag-only exception to the NT rule (SPEC_SENSORY_INPUTS §3.2c): the cell types with a "
                         "literature fast transmitter in data/nt_literature_783.csv get w = |w| * sign_lit on all "
                         "outgoing synapses (ACh +, GABA/Glu -); other types unchanged. Default off")
    ap.add_argument("--vision-boundary", action="store_true",
                    help="Stage B (SPEC_SENSORY_INPUTS §2.1): drive the 32 FlyVis boundary types (34,121 neurons) "
                         "from FlyVis instead of T4/T5 only; the other FlyVis types are recorded as a display layer "
                         "(/flyvis, never an input). Default off")
    ap.add_argument("--olfaction-full", action="store_true",
                    help="Stage A (SPEC_SENSORY_INPUTS §2.2): all 2,275 typed ORNs (53 glomeruli) at their "
                         "spontaneous rate (data/orn_spontaneous_783.csv: Hallem & Carlson 2006, else 5 Hz); food "
                         "odour raises only the 6 food glomeruli. Replaces the food-ORN input. Default off")
    ap.add_argument("--leg-grn", action="store_true",
                    help="SPEC_SENSORY_INPUTS §2.4: the sugar-like leg GRNs (data/leg_sugar_grn_783.csv, chosen by "
                         "connectivity) at SUGAR_RATE_CONTACT while any tarsus touches the food platform. Default off")
    ap.add_argument("--dn-reference", default=None,
                    help="DNp15 steering reference JSON (default data/dn_lr_reference.json, T4/T5 input set; "
                         "data/dn_lr_reference_sB.json = --vision-boundary --no-olfaction, SPEC_SENSORY_INPUTS §3.3)")
    ap.add_argument("--persist-steps", type=int, default=cfg.PERSIST_CUT_STEPS,
                    help="decision steps with all inputs cut after the perch calibration")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--version", type=int, default=None, help="output version (default: next free)")
    ap.add_argument("--sim-dir", default=str(SIM_DIR))
    ap.add_argument("--record-readout", default=None, metavar="DIR",
                    help="RECORDING (SPEC_SENSORY_INPUTS §3.6): write DIR/<run>_readout.h5 with the spike counts of the "
                         "1,299 DNs, the boundary-layer rates as sensed, the teacher route commands and the body state "
                         "per 25 ms step (calibration and input-cut steps included). Changes nothing else")
    ap.add_argument("--readout-model", default=None, metavar="NPZ",
                    help="READOUT MODE (SPEC_SENSORY_INPUTS §3.6, training ladder): the four route commands turn_hand, "
                         "thrust_hand, pitch_hand, roll_hand (wings-on phases only) are the clipped output of the trained "
                         "linear readout in NPZ (flight/readout_model.py; arm real / shuffled / bypass is stored in the "
                         "file). The teacher command of the same state is computed and recorded too and never "
                         "influences the flight. Needs --hybrid --vision-boundary. Default off: the flight is unchanged")
    ap.add_argument("--shuffle-seed", type=int, default=None,
                    help="NULL CONTROL (arm T1-shuffled only): degree-preserving shuffled connectome with this "
                         "permutation seed (FlightBrain(shuffle_seed=...)); never a result of the published model")
    ap.add_argument("--no-video", action="store_true")
    args = ap.parse_args(argv)
    args.ablate_dn = sorted(set(args.ablate_dn or []) | ({"mn9"} if args.ablate_mn9 else set()))
    args.swap_dn_lr = sorted(set(args.swap_dn_lr or []))
    if args.spawn_air and args.start_on_platform:
        ap.error("--spawn-air and --start-on-platform exclude each other")
    if args.hover and not args.spawn_air:
        ap.error("--hover needs --spawn-air")
    if args.nt_literature and args.nt_modulatory_silent:
        ap.error("--nt-literature and --nt-modulatory-silent exclude each other")
    if args.olfaction_full and args.no_olfaction:
        ap.error("--olfaction-full and --no-olfaction exclude each other")
    if args.no_olfaction and not args.hybrid:
        args.ablate_odor = True       # --hybrid: the HAND odor navigation reads the odor field itself
    if args.hybrid and (args.spawn_air or args.start_on_platform):
        ap.error("--hybrid starts from the pedestal and excludes --spawn-air/--start-on-platform")
    args.start_offset = [float(v) for v in args.start_offset]
    if (any(args.start_offset) or args.start_yaw) and (args.spawn_air or args.start_on_platform):
        ap.error("--start-offset/--start-yaw move the pedestal start; they exclude --spawn-air/--start-on-platform")
    return args


def next_version(sim_dir):
    vs = [int(m.group(1)) for f in Path(sim_dir).glob("flight_v*")
          if (m := re.match(r"flight_v(\d+)", f.name))]
    return max(vs, default=0) + 1


def rss_gb():
    return psutil.Process().memory_info().rss / 1e9


def peak_rss_gb():
    try:
        for line in open("/proc/self/status"):
            if line.startswith("VmHWM:"):
                return int(line.split()[1]) / 1e6
    except OSError:
        pass
    return float("nan")


def git_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:
        return "unknown"


def brain_share(rec):
    """Pre-registered brain contribution: sum|turn_brain| / sum|turn_total| over the wings-on steps
    (SPEC_BRAIN_CONTROL "Honest hybrid final"); also each term's share of the summed magnitudes."""
    n = rec.n_done
    a = {k: rec.a[k][:n] for k in ("turn_brain", "turn_hand", "turn_flyvis", "turn_reflex", "turn_total")}
    on = rec.a["wings_on"][:n].astype(bool)
    if not on.any():
        return dict(n_wings_on=0)
    s = {k: float(np.abs(v[on]).sum()) for k, v in a.items()}
    parts = s["turn_brain"] + s["turn_hand"] + s["turn_flyvis"] + s["turn_reflex"]
    return dict(n_wings_on=int(on.sum()), brain_over_total=s["turn_brain"] / max(s["turn_total"], 1e-12),
                **{f"share_{k[5:]}": s[k] / max(parts, 1e-12) for k in
                   ("turn_brain", "turn_hand", "turn_flyvis", "turn_reflex")},
                sum_abs={k: s[k] for k in s})


def main(argv=None):
    args = parse_args(argv)
    dev = args.dev_subnet or args.dev_subnet_full
    sim_dir = Path(args.sim_dir)
    sim_dir.mkdir(parents=True, exist_ok=True)
    version = args.version if args.version is not None else next_version(sim_dir)
    out = h5_path(version, sim_dir=sim_dir, dev_subnet=dev, ablate_dn=args.ablate_dn,
                  ablate_odor=args.ablate_odor, antenna_real=args.antenna_real, tag=args.tag,
                  asc_legacy=args.asc_legacy, untextured=args.untextured, apl_graded=args.apl_graded,
                  no_olfaction=args.no_olfaction, nt_silent=args.nt_modulatory_silent,
                  start_on_platform=args.start_on_platform,
                  swap_dn=args.swap_dn_lr, platform_neutral=args.platform_neutral, spawn_air=args.spawn_air,
                  hover=args.hover, yaw_perturb=args.yaw_perturb, hybrid=args.hybrid,
                  vision_boundary=args.vision_boundary, olfaction_full=args.olfaction_full,
                  leg_grn=args.leg_grn, nt_literature=args.nt_literature, no_brain_steer=args.no_brain_steer,
                  head_reflex=args.head_reflex, postures=args.postures, start_offset=args.start_offset,
                  start_yaw=args.start_yaw)
    if any(args.start_offset):     # before the odor field and the body read the pedestal geometry
        cfg.move_takeoff_pedestal(*args.start_offset)
    print(f"NeuroFly flight -> {out.name}" + ("   [DEV subnet: NOT a result]" if dev else ""))
    t_setup = time.time()

    # ── setup ───────────────────────────────────────────────────────────────
    print("odor field (3D Dijkstra) ...")
    field = build_arena_odor_field()
    print("brain ...")
    brain = FlightBrain(dev_subnet=dev, dev_min_syn=1 if args.dev_subnet_full else DEV_MIN_SYN, seed=args.seed,
                        asc_legacy=args.asc_legacy, olfaction=not args.no_olfaction, apl_graded=args.apl_graded,
                        nt_silent=args.nt_modulatory_silent, vision_boundary=args.vision_boundary,
                        olfaction_full=args.olfaction_full, leg_grn=args.leg_grn,
                        nt_literature=args.nt_literature, shuffle_seed=args.shuffle_seed)
    print(f"  {brain.n:,} neurons, {len(brain.syn):,} synapses, RSS {rss_gb():.2f} GB")
    print("body (FlyGym, vision on) ...")
    spawn, spawn_yaw = None, np.radians(args.start_yaw)
    if args.start_on_platform:     # experiment design: standing on the food platform, facing +x
        cx, cy, _, zt = cfg.FOOD_PLATFORM
        spawn = (cx, cy, zt + 0.5)
    if args.spawn_air:             # experiment design: hovering in the air
        spawn, spawn_yaw = tuple(args.spawn_air[:3]), np.radians(args.spawn_air[3])
    body = FlightBody(spawn_pos=spawn, spawn_yaw=spawn_yaw, legs="tuck" if args.spawn_air else "stand",
                      enable_vision=True, textured=not args.untextured,
                      platform="neutral" if args.platform_neutral else "dark", head_reflex=args.head_reflex,
                      postures=args.postures)
    g2l = None
    if brain.l2g is not None:
        g2l = np.full(brain.n_global, -1, dtype=np.int64)
        g2l[brain.l2g] = np.arange(len(brain.l2g))
    readouts = Readouts(brain.root_ids, g2l)
    ref_path = Path(args.dn_reference) if args.dn_reference else PATH_DN_REFERENCE
    if not ref_path.exists():
        raise SystemExit(f"{ref_path} missing: run scripts/make_dn_reference.py")
    bridge = Bridge(readouts, DT, ablate=args.ablate_dn, swap=args.swap_dn_lr,
                    reference=load_reference(ref_path) if ref_path.exists() else None)
    head_id = mujoco.mj_name2id(body.m, mujoco.mjtObj.mjOBJ_BODY, f"{body.fly.name}/Head")
    vb = args.vision_boundary
    display = None
    if vb:
        print("FlyVis -> FlyWire boundary layer ...")
        eyes = VB.BoundaryEyes({"L": brain.groups["vbnd_L"], "R": brain.groups["vbnd_R"]})
        display = VB.DisplayWriter(out, eyes)     # /flyvis/activity streamed per step (display only)
        vb_sum = {s: np.zeros(len(eyes.node[s])) for s in ("L", "R")}   # closed-loop target rate sums (K6)
    else:
        print("FlyVis -> FlyWire T4/T5 ...")
        eyes = V.FlyVisEyes({"L": brain.groups["t45_L"], "R": brain.groups["t45_R"]})
    olf_full = None
    if args.olfaction_full:
        from flight.olfaction_full import OlfactionFull
        olf_full = OlfactionFull(brain.root_ids)
        for k_, v_ in olf_full.idx.items():
            assert np.array_equal(v_, brain.groups[k_])
        print(f"  olfaction full: {olf_full.summary()['n']} ORNs, spontaneous "
              f"{olf_full.summary()['spont_mean_hz']:.1f} Hz mean")
    loom_bias = S.LoomBias()
    expansion = S.ExpansionRate(DT)
    n_mn = max(len(brain.local["brain_mn"]), 1)
    render_at = tuple(int(round(cfg.PHYSICS_STEPS_PER_DECISION * (j + 1) / V.VIS_SUBFRAMES))
                      for j in range(V.VIS_SUBFRAMES))
    frames = [body.update_vision().copy()] * V.VIS_SUBFRAMES   # static scene before the first step
    print(f"setup {time.time() - t_setup:.1f} s, RSS {rss_gb():.2f} GB")

    def sense(st, frames, step):
        a, (loom_L, loom_R) = eyes.step(frames)
        r = eyes.rates(a)
        if vb:
            t45, t45_tm = eyes.t45_view(r)
            display.add(step, eyes.display)
        else:
            t45, t45_tm = r, eyes.type_means(r)
        head = body.d.xpos[head_id].copy()
        od = S.sample_odor(field, head, st["R"], antenna_real=args.antenna_real)
        return dict(t45=t45, t45_tm=t45_tm, vbnd=r if vb else None, loom_L=loom_L, loom_R=loom_R,
                    b_loom=loom_bias(loom_L, loom_R), od=od)

    def input_rates(st, sn, sugar_contact):
        od = sn["od"]
        r = dict(sugar=cfg.SUGAR_RATE_CONTACT if sugar_contact else 0.0)
        if args.leg_grn:
            r["leg_sugar"] = cfg.SUGAR_RATE_CONTACT if sugar_contact else 0.0
        if vb:
            r.update(vbnd_L=sn["vbnd"]["L"], vbnd_R=sn["vbnd"]["R"])
        else:
            r.update(t45_L=sn["t45"]["L"], t45_R=sn["t45"]["R"])
        if olf_full is not None:
            r.update(olf_full.rates(S.odor_norm(od["L"]), S.odor_norm(od["R"])))
        elif not args.no_olfaction:
            r["orn_food_L"] = S.rate(S.odor_norm(od["L"]), cfg.ORN_FOOD_RATE)
            r["orn_food_R"] = S.rate(S.odor_norm(od["R"]), cfg.ORN_FOOD_RATE)
        if args.asc_legacy:
            r["ascending"] = S.ascending_rate(st["omega"])
        return r

    def net_rate(counts):
        return float(counts.sum()) / (brain.n * DT)

    # ── perch: 0.25 s calibration (wings off, standing on the pedestal) ────
    # --spawn-air: hovering instead (wings on, symmetric, vertical-speed damping only)
    def off_cmd():
        if not args.spawn_air:
            return qs.WingCommand(0, 0, 0, on=False)
        st = body.state()
        return ctl.wing_command(0.0, -float(st["vel"][2]) / cfg.VZ_DAMP_REF, 0.0, body.params)[0]

    acc = {k: 0.0 for k in brain.local}
    acc_ro = np.zeros((len(READOUT_TYPES), 2))
    perch_rate = []
    spike_counts = SparseSpikeCounts(brain.l2g)          # every neuron, every 25 ms step (sparse)
    n_pre = cfg.CALIB_STEPS + args.persist_steps
    rro = None
    route_ro, label_arr = None, None
    if args.readout_model:
        if not (vb and args.hybrid):
            raise SystemExit("--readout-model needs --hybrid --vision-boundary")
        ro_model, ro_arm, ro_meta = RM.load_model(args.readout_model)
        if (ro_arm == "shuffled") != (args.shuffle_seed is not None):
            raise SystemExit("arm 'shuffled' needs --shuffle-seed and the other arms must not have it")
        route_ro = RM.RouteReadout(ro_model, ro_arm)
        label_arr = np.full((args.n_steps, 4), np.nan)          # teacher label of the visited state (never used by the flight)
        print(f"READOUT MODE: arm {ro_arm}, model {args.readout_model} (route commands from the trained readout)")
    if args.record_readout or route_ro is not None:
        if not vb:
            raise SystemExit("--record-readout needs --vision-boundary")
        import pandas as pd
        r2i = G.root_to_index(brain.root_ids)
        dn_tab = pd.read_csv(G.PATH_DN)
        dn_glob = dn_tab.loc[dn_tab["root_id"].isin(r2i), "root_id"].map(r2i).to_numpy(np.int64)
        dn_loc = dn_glob if g2l is None else g2l[dn_glob]
        assert (dn_loc >= 0).all()
    if args.record_readout:
        rro = ReadoutRecorder(n_pre, args.n_steps, dn_loc, dn_glob, len(eyes.node["L"]), len(eyes.node["R"]))
    for j in range(cfg.CALIB_STEPS):
        st = body.state()
        sn_c = sense(st, frames, j - n_pre)
        rates_c = input_rates(st, sn_c, sugar_contact=False)
        brain.set_rates(**rates_c)
        c, per = brain.step()
        if rro is not None:
            rro.put(j - n_pre, per, sn_c["vbnd"], rates_c["sugar"], True)
        if route_ro is not None:
            route_ro.update(per[dn_loc], sn_c["vbnd"]["L"], sn_c["vbnd"]["R"])
        spike_counts.add(j - n_pre, per)
        perch_rate.append(net_rate(per))
        acc_ro += readouts.counts(per)
        for k in acc:
            acc[k] += c[k]
        frames = body.step(off_cmd(), render_at=render_at)["frames"]
    base = {k: v / cfg.CALIB_STEPS for k, v in acc.items()}
    ro_base = readouts.rates(acc_ro / cfg.CALIB_STEPS, DT)     # Hz per neuron at perch (ablation value)

    # ── persistence: all brain inputs cut (FlyVis keeps integrating) ────────
    persist_rate, persist_dn = [], []
    for j in range(args.persist_steps):
        sn_p = sense(body.state(), frames, cfg.CALIB_STEPS + j - n_pre)
        brain.silence_inputs()
        c, per = brain.step()
        if rro is not None:
            rro.put(cfg.CALIB_STEPS + j - n_pre, per, sn_p["vbnd"], 0.0, False)
        if route_ro is not None:
            route_ro.update(per[dn_loc], sn_p["vbnd"]["L"], sn_p["vbnd"]["R"])
        spike_counts.add(cfg.CALIB_STEPS + j - n_pre, per)
        persist_rate.append(net_rate(per))
        persist_dn.append((c["dn_L"] + c["dn_R"] + c["dn_C"]) / DT)
        frames = body.step(off_cmd(), render_at=render_at)["frames"]
    if args.persist_steps:
        print(f"persistence: perch {np.mean(perch_rate):.3f} Hz -> inputs cut: "
              + " ".join(f"{x:.3f}" for x in persist_rate) + " Hz (per 25 ms); "
              f"DN {persist_dn[-1]:.0f} spikes/s in the last step")
    brain.baseline = base
    bridge.set_baseline(ro_base)
    print(f"calibration: all_dn L/R {base['dn_L']:.1f}/{base['dn_R']:.1f}; dng02 {base['dng02_L']:.2f}/{base['dng02_R']:.2f}; "
          f"steer {base['steer_L']:.2f}/{base['steer_R']:.2f}")

    # ── closed loop ─────────────────────────────────────────────────────────
    rec = BehaviorRecorder(args.n_steps)
    # --yaw-perturb: body-z torque pulse; passive damping alone would turn DEG (FlightBody.yaw_pulse_torque)
    pert_T = 0.0
    if args.yaw_perturb:
        pert_T = body.yaw_pulse_torque(args.yaw_perturb[1], YAW_PERTURB_S)
        print(f"yaw perturbation: t={args.yaw_perturb[0]:.3f}s, {YAW_PERTURB_S}s, {args.yaw_perturb[1]:+.0f} deg "
              f"(torque {pert_T:+.4g} uN*mm about body z)")
    if args.hybrid:
        pm = H.HybridPhases()
    else:
        pm = ctl.PhaseMachine(DT, start="landed" if args.start_on_platform else ("cruise" if args.spawn_air else "takeoff"))
    if args.start_on_platform:
        body.set_legs("stand", adhesion=1.0)
    tuck_reflex_done = body.legs == "tuck"
    t_run0 = body.sim.curr_time
    next_frame = t_run0
    touched = False
    t_loop = time.time()
    for k in range(args.n_steps):
        t_step = time.time()
        st = body.state()
        sn = sense(st, frames, k)
        od = sn["od"]
        if vb:
            for s_ in ("L", "R"):
                vb_sum[s_] += sn["vbnd"][s_]
        con = body.contacts()
        rates = input_rates(st, sn, sugar_contact=bool(con["platform_legs"].any()))
        brain.set_rates(**rates)
        t_b = time.time()
        c, per = brain.step()
        brain_time = time.time() - t_b
        spike_counts.add(k, per)
        if rro is not None:
            rro.put(k, per, sn["vbnd"], rates["sugar"], True)
        ro_out = None if route_ro is None else route_ro.update(per[dn_loc], sn["vbnd"]["L"], sn["vbnd"]["R"])
        ro_counts = readouts.counts(per)
        _, ro_used = bridge.update(ro_counts)
        feed = bridge.proboscis(ro_used)

        e = expansion(st["pos"])
        if args.hybrid:
            phase = pm.update(st["pos"], st["vel"], int(con["platform_legs"].sum()))
            if pm.legs_extended and not pm.landed:
                body.set_legs("stand")                # HAND: legs extended in approach/descend
        else:
            phase = pm.update(e, int(con["platform_legs"].sum()))
            if phase == "approach":
                body.set_legs("stand")                # legs extended for landing
        # REFLEX (VNC tarsal reflex, HAND): wings on + no tarsus contact -> tuck ramp, once per
        # flight; never after the landing extension started (SPEC_SENSORY_INPUTS.md §7.2)
        extending = pm.legs_extended if args.hybrid else phase == "approach"
        if (not tuck_reflex_done and pm.wings_on and not extending and not pm.landed
                and not (con["pedestal_legs"].any() or con["ground_legs"].any() or con["platform_legs"].any())):
            body.set_legs("tuck")
            tuck_reflex_done = True
            print(f"  LEG TUCK (tarsal contact loss) t={st['time'] - t_run0:.3f}s")
        if pm.landed and not touched and not args.start_on_platform:
            touched = True
            body.set_legs("stand", adhesion=1.0)
            print(f"  TOUCHDOWN t={st['time']:.3f}s speed={np.linalg.norm(st['vel']):.1f} mm/s")
        if args.postures and pm.landed:
            # HAND posture following the BRAIN feeding decision (MN9): forward lean while feeding
            body.set_legs("feed" if feed["proboscis_extended"] else "stand")

        v_fwd = float(st["vel"][0] * np.cos(st["heading"]) + st["vel"][1] * np.sin(st["heading"]))
        height = float(st["pos"][2] - S.surface_below(st["pos"][0], st["pos"][1]))
        sb = bridge.steer(ro_used) if bridge.ref is not None else None
        # --no-brain-steer (post-hoc control): DNp15 term exactly 0; the readout stays recorded
        turn_dn = 0.0 if args.no_brain_steer else (sb["turn_dn"] if sb else 0.0)
        roll_right, vz_des, v_des_h = 0.0, np.nan, np.nan
        if args.hybrid:
            # BRAIN (DNp15 bridge) + HAND (odor) + FLYVIS (b_loom); REFLEX acts inside body.step
            t_brain, t_hand, t_fv = turn_dn, H.turn_hand(od["I_asym"], phase, args.ablate_odor), sn["b_loom"]
            th = H.thrust_hand(phase, st["pos"][2], st["vel"][2], od["I_grad"], args.ablate_odor)
            pitch_down, roll_right, v_des_h = H.tilt_hand(phase, st["pos"], st["vel"], st["heading"])
            if route_ro is not None:      # READOUT MODE: teacher label of this state recorded, applied = readout output
                label_arr[k] = (t_hand, th["total"], pitch_down, roll_right)
                t_hand, thrust_total, pitch_down, roll_right = RM.apply_route(label_arr[k], ro_out, pm.wings_on)
                th = dict(th, total=thrust_total)
            t_tot = H.combine_turn(t_brain, t_hand, t_fv)
            tt = dict(turn_bias=t_tot, turn_odor=t_hand, turn_dn=t_brain, turn_loom=t_fv,
                      dn_lr_delta=sb["steer_norm"])
            pt = dict(pitch_bias=th["total"], pitch_odor=th["odor"], pitch_alt=th["alt"], pitch_ventral=0.0,
                      pitch_takeoff=th["boost"])
            vz_des = th["vz_des"]
            cmd, lift = H.wing_command(t_tot, th["total"], pitch_down, roll_right, body.params,
                                       wings_on=pm.wings_on)
        else:
            tt = ctl.turn_terms_brain(turn_dn, sb["steer_norm"])
        if not args.hybrid:
            pt = ctl.pitch_terms(od["I_grad"], st["vel"][2], height, phase, ablate_odor=args.ablate_odor)
            pitch_down = 0.0 if args.hover else ctl.body_pitch_target(phase, v_fwd)
            cmd, lift = ctl.wing_command(tt["turn_bias"], pt["pitch_bias"], pitch_down, body.params,
                                         wings_on=pm.wings_on)

        t0 = body.sim.curr_time
        snap = []
        for j in range(cfg.PHYSICS_STEPS_PER_DECISION):
            if t0 + j * cfg.PHYSICS_DT >= next_frame - 0.5 * cfg.PHYSICS_DT:
                snap.append(j)
                next_frame += FRAME_DT
        t_rel = k * DT
        pert = pert_T if (args.yaw_perturb and args.yaw_perturb[0] - 1e-9 <= t_rel
                          < args.yaw_perturb[0] + YAW_PERTURB_S - 1e-9) else 0.0
        r = body.step(cmd, pitch_down=pitch_down, roll_right=roll_right, snap_at=snap, render_at=render_at,
                      ext_torque=st["R"][:, 2] * pert if pert else None)
        frames = r["frames"]
        for j, q, qv in zip(snap, r["qpos"], r["qvel"]):
            rec.add_qpos(t0 + j * cfg.PHYSICS_DT - t_run0, q, qv)
        t_reflex = qs.yaw_torque_to_turn(r["haltere_yaw"], body.params, cfg.TURN_DPHI_DEG)

        s1 = body.state()
        c1 = body.contacts()
        rec.put(k, t=s1["time"] - t_run0, pos=s1["pos"], vel=s1["vel"], speed=np.linalg.norm(s1["vel"]),
                quat=s1["quat"], omega=s1["omega"], heading=s1["heading"],
                dist_to_food=np.linalg.norm(s1["pos"] - cfg.FOOD_POS), phase=cfg.PHASE_CODE[phase],
                odor_L=od["L"], odor_R=od["R"], odor_U=od["U"], odor_D=od["D"],
                I_asym=od["I_asym"], I_grad=od["I_grad"],
                I_asym_real=od["I_asym_real"], I_grad_real=od["I_grad_real"],
                ell_LR=od["ell_LR"], ell_UD=od["ell_UD"], v_fwd=v_fwd,
                **tt, **pt, lift_frac=lift, pitch_down=pitch_down,
                stroke_amp_L=cmd.amp_L, stroke_amp_R=cmd.amp_R, stroke_freq=cmd.freq,
                force=r["force"], torque=r["torque"],
                asc_rate=rates.get("ascending", 0.0),
                olf_rate_L=olf_full.food_mean(rates, "L") if olf_full else rates.get("orn_food_L", 0.0),
                olf_rate_R=olf_full.food_mean(rates, "R") if olf_full else rates.get("orn_food_R", 0.0),
                sugar_rate_in=rates["sugar"],
                t45_rate_L=float(sn["t45"]["L"].mean()), t45_rate_R=float(sn["t45"]["R"].mean()),
                t45_type_rate=sn["t45_tm"], net_rate=net_rate(per),
                vbnd_type_rate=eyes.type_means(sn["vbnd"]) if vb else 0.0,
                loom_L=sn["loom_L"], loom_R=sn["loom_R"], expansion_rate=e, height_above=height,
                dng02_L=c["dng02_L"], dng02_R=c["dng02_R"], steer_L=c["steer_L"], steer_R=c["steer_R"],
                all_dn_L=c["dn_L"], all_dn_R=c["dn_R"], dnp01=c["dnp01"], brain_mn=c["brain_mn"],
                sez_out_rate=c["brain_mn"] / (n_mn * DT),
                platform_contact=int(c1["platform_legs"].sum()), tower_contact=int(c1["tower_contact"]),
                tower_penetration=r["tower_penetration"], min_tower_clearance=c1["min_tower_clearance"],
                is_feeding=int(pm.landed and feed["proboscis_extended"]),
                dn_readout=ro_counts, dn_readout_rate=ro_used, **feed,
                steer_raw=sb["steer_raw"] if sb else np.nan, steer_norm_t=sb["steer_norm_t"] if sb else np.nan,
                steer_norm=sb["steer_norm"] if sb else np.nan, yaw_perturb_torque=pert,
                turn_total=tt["turn_bias"], turn_brain=tt["turn_dn"], turn_hand=tt["turn_odor"],
                turn_flyvis=tt["turn_loom"], turn_reflex=t_reflex, thrust_hand=pt["pitch_bias"],
                pitch_hand=pitch_down, roll_hand=roll_right, vz_des=vz_des, v_des_h=v_des_h,
                **({} if r["head"] is None else dict(
                    head_q=r["head"]["q"], head_target=r["head"]["target"], head_q_absmax=r["head"]["q_absmax"],
                    gaze_yaw_rate=r["head"]["gaze_yaw_rate"], body_yaw_rate=r["head"]["body_yaw_rate"],
                    head_turn_sub=r["head"]["turn_sub"], head_turn_sub_lt=r["head"]["turn_sub_lt"])),
                leg_pose=cfg.LEG_POSE_CODE[body.legs],
                wings_on=int(pm.wings_on), platform_azimuth=S.platform_azimuth(s1["pos"], s1["heading"]),
                step_time=time.time() - t_step, brain_time=brain_time, rss_gb=rss_gb())
        a = rec.a
        if k < 5 or k % 10 == 0 or k == args.n_steps - 1:
            print(f"  step {k:03d} t={a['t'][k]:.3f}s [{phase}] pos=({s1['pos'][0]:.1f},{s1['pos'][1]:.1f},"
                  f"{s1['pos'][2]:.1f}) v={a['speed'][k]:.0f} d_food={a['dist_to_food'][k]:.1f} | "
                  f"T4/T5 L{a['t45_rate_L'][k]:.1f}/R{a['t45_rate_R'][k]:.1f}Hz net {a['net_rate'][k]:.2f}Hz | "
                  f"turn={tt['turn_bias']:+.3f} (odor {tt['turn_odor']:+.3f} dn {tt['turn_dn']:+.3f} "
                  f"loom {tt['turn_loom']:+.3f}) pitch={pt['pitch_bias']:+.3f} | DN L{c['dn_L']}/R{c['dn_R']} "
                  f"g02 {c['dng02_L']}/{c['dng02_R']} | MN9 {feed['mn9_rate']:.1f}Hz s^ {sb['steer_norm'] if sb else float('nan'):+.2f}"
                  f"{' EXT' if feed['proboscis_extended'] else ''} | {a['step_time'][k]:.2f}s RSS {a['rss_gb'][k]:.2f}GB")
        if a["rss_gb"][k] > RSS_WARN_GB:
            print(f"  WARNING: RSS {a['rss_gb'][k]:.1f} GB > {RSS_WARN_GB} GB")
        if r["badqacc"]:
            print(f"  WARNING: MuJoCo BADQACC x{r['badqacc']}")

    loop_s = time.time() - t_loop

    # ── HDF5 first (before any video) ───────────────────────────────────────
    import brian2
    meta = dict(
        n_steps=args.n_steps, decision_interval=DT, brain_dt=float(BRAIN_DT / brian2.second),
        physics_dt=cfg.PHYSICS_DT, scale=cfg.SCALE, play_speed=PLAY_SPEED, fps=FPS,
        flags=dict(dev_subnet=dev, dev_subnet_full=args.dev_subnet_full, ablate_dn=args.ablate_dn,
                   ablate_odor=args.ablate_odor, antenna_real=args.antenna_real, tag=args.tag,
                   asc_legacy=args.asc_legacy, untextured=args.untextured, apl_graded=args.apl_graded,
                   no_olfaction=args.no_olfaction, nt_modulatory_silent=args.nt_modulatory_silent,
                    start_on_platform=args.start_on_platform,
                   hover=args.hover, yaw_perturb=args.yaw_perturb, hybrid=args.hybrid,
                   vision_boundary=args.vision_boundary, olfaction_full=args.olfaction_full,
                   leg_grn=args.leg_grn, nt_literature=args.nt_literature,
                   no_brain_steer=args.no_brain_steer, head_reflex=args.head_reflex,
                   postures=args.postures, start_offset=args.start_offset, start_yaw=args.start_yaw,
                   **({"readout_model": args.readout_model, "readout_arm": ro_arm, "shuffle_seed": args.shuffle_seed}
                      if route_ro is not None else {})),
        experiment_design=(["start standing on the food platform (--start-on-platform)"]
                           if args.start_on_platform else [])
                          + ([f"start hovering in the air at {args.spawn_air} (--spawn-air)"] if args.spawn_air else [])
                          + ([f"take-off pedestal and start moved by {args.start_offset} mm (--start-offset)"]
                             if any(args.start_offset) else [])
                          + ([f"initial heading {args.start_yaw:+g} deg (--start-yaw)"] if args.start_yaw else [])
                          + (["stay hovering, body tilt 0 (--hover)"] if args.hover else [])
                          + ([f"yaw torque pulse {args.yaw_perturb[1]:+g} deg passive at t={args.yaw_perturb[0]:g} s "
                              f"for {YAW_PERTURB_S} s (--yaw-perturb)"] if args.yaw_perturb else [])
                          + (["dark food platform (arena design, user decision 5)"] if not args.platform_neutral else []),
        readout_types=list(READOUT_TYPES), readout_n=readouts.n.tolist(), readout_perch_hz=ro_base.tolist(),
        bridge=dict(readout_tau=READOUT_TAU, mn9_threshold_hz=MN9_THRESHOLD_HZ, ablate=args.ablate_dn,
                    swap=args.swap_dn_lr, k_steer=K_STEER, steer_types=list(STEER_TYPES),
                    steer_drive=list(STEER_DRIVE), steer_drive_label="POST-HOC (chosen after Step 2 seeds 0-2)",
                    steer_reference_hz=bridge.ref.tolist() if bridge.ref is not None else None,
                    steer_reference_path=str(ref_path.resolve().relative_to(REPO)
                                             if ref_path.resolve().is_relative_to(REPO) else ref_path),
                    turn="0 (--no-brain-steer, post-hoc control; DNp15 readout recorded only)" if args.no_brain_steer else
                    "-K_STEER * [(r_L-ref_L)-(r_R-ref_R)]/mean(ref) of DNp15 (post-hoc)",
                    feeding="MN9 > threshold"),
        nt_silent=brain.nt_info or {},
        nt_literature=brain.nt_lit_info or {},
        input_set="v2" + ("+asc_legacy" if args.asc_legacy else "") + ("-olfaction" if args.no_olfaction else "")
                  + ("+vision_boundary(-t45)" if vb else "")
                  + ("+olfaction_full(-orn_food)" if args.olfaction_full else "")
                  + ("+leg_grn" if args.leg_grn else ""),
        olfaction_full=olf_full.summary() if olf_full else {},
        apl=(dict(brain.apl_info, mechanism="graded global feedback inhibition, a = KC->APL-weighted mean KC rate "
                                             "(t_mbr low-pass); I_apl = gain * w_APL->j * a")
             if args.apl_graded else dict(mechanism="spiking (LIF, as all neurons)")),
        food_glomeruli=list(G.FOOD_GLOMERULI), orn_food_rate=list(cfg.ORN_FOOD_RATE),
        sugar_rate_contact=cfg.SUGAR_RATE_CONTACT,
        visual=dict(model=V.FLYVIS_MODEL, subframes=V.VIS_SUBFRAMES, flyvis_dt=V.FLYVIS_DT, r_max=V.R_MAX,
                    r_clip=V.R_CLIP, align_rot=V.ALIGN_ROT, align_reflect=V.ALIGN_REFLECT,
                    r_eye_flip=V.R_EYE_FLIP, n_outside_extent=eyes.n_outside,
                    **(dict(boundary_types=list(eyes.fw_types), boundary_rule=VB.BOUNDARY_FRAC,
                            transduction="data/visual_transduction.json", r_central=VB.R_CENTRAL,
                            a_ref_min=VB.A_REF_MIN, unresponsive=list(eyes.unresponsive),
                            n_boundary={s: len(eyes.node[s]) for s in ("L", "R")},
                            display_types=list(eyes.display_types),
                            display="/flyvis: FlyVis a - a0 of the not-driven types, display only, not an input")
                       if vb else dict(transduction="data/t45_transduction.json"))),
        perch_net_rate_hz=perch_rate, persist_steps=args.persist_steps,
        persist_net_rate_hz=persist_rate, persist_dn_rate=persist_dn,
        dev_subnet=dev, seed=args.seed, git_hash=git_hash(), timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        geometry=dict(tower1=cfg.TOWER1, tower2=cfg.TOWER2, pedestal=cfg.TAKEOFF_PEDESTAL,
                      food_platform=cfg.FOOD_PLATFORM, food=cfg.FOOD_POS.tolist()),
        lif_params={k: str(v) for k, v in brain.params.items()},
        group_counts=G.group_counts(brain.groups), n_neurons=brain.n, n_synapses=len(brain.syn),
        dn_baseline={k: float(v) for k, v in base.items()}, calib_steps=cfg.CALIB_STEPS,
        phase_codes=cfg.PHASE_CODE, brian2_version=brian2.__version__,
        peak_rss_gb=peak_rss_gb(), step_time_mean=float(rec.a["step_time"][:rec.n_done].mean()),
        loop_seconds=loop_s, max_tower_penetration=body.max_tower_penetration,
        hand_made=(["HAND odor->turn map (take-off/cruise)", "HAND l_eff = 10 mm",
                      "HAND odor->collective map (take-off/cruise)", "HAND climb-only floor / approach altitude "
                      "target platform top + %g mm" % H.APPROACH_CLEAR, "HAND approach radius, world-frame "
                      "position controller (reads platform geometry)", "HAND descent at %g mm/s" % H.LAND_VZ,
                      "HAND take-off timer + lift boost", "HAND leg extension / touchdown", "cruise pitch",
                      "FLYVIS b_loom turn term (FlyVis network, walking constants)", "REFLEX haltere PD"]
                     if args.hybrid else
                     ["haltere reflex", "landing trigger", "cruise pitch", "odor->collective map",
                      "vertical-speed damping", "ventral reflex", "take-off lift boost"])
                  + (["REFLEX head stabilisation (--head-reflex)"] if args.head_reflex else [])
                  + (["HAND flight / feeding leg postures (--postures)"] if args.postures else [])
                  + (["ascending |omega| input (--asc-legacy)"] if args.asc_legacy else []),
        hybrid=(dict(module="flight/hybrid.py", phases=list(H.HYBRID_PHASES),
                     turn="turn_total = clip(turn_brain + turn_hand + turn_flyvis, +-%g); turn_reflex recorded, "
                          "not commanded" % cfg.TURN_BIAS_MAX,
                     brain=("turn_brain = 0 (--no-brain-steer)" if args.no_brain_steer else
                            "turn_brain = -K_STEER*s_hat(DNp15) (POST-HOC readout)")
                           + "; feeding = MN9 > %g Hz only" % MN9_THRESHOLD_HZ,
                     altitude="HAND only: VNC flight program has no altitude target, DNg02 silent",
                     constants=dict(approach_clear=H.APPROACH_CLEAR, z_gain=H.Z_GAIN, vz_max=H.VZ_MAX,
                                    land_vz=H.LAND_VZ, r_approach=H.R_APPROACH, v_gain=H.V_GAIN,
                                    r_descend=H.R_DESCEND, v_descend=H.V_DESCEND, tilt_max_deg=H.TILT_MAX_DEG),
                     brain_share=brain_share(rec)) if args.hybrid else {}),
        turn_share=brain_share(rec),
        postures=(dict(label="HAND postures (VARSAYIM)", flight_pose_offsets_deg=cfg.FLIGHT_POSE_OFFSETS,
                       feed_pose_offsets_deg=cfg.FEED_POSE_OFFSETS, feed_ramp_s=cfg.LEG_FEED_RAMP_S,
                       tuck_ramp_s=cfg.LEG_TUCK_RAMP_S, extend_ramp_s=cfg.LEG_EXTEND_RAMP_S,
                       feed_trigger="landed and MN9 proboscis decision (BRAIN); pose itself HAND")
                  if args.postures else {}),
        head_reflex=(dict(module="flight/head_reflex.py", label="HAND reflex (VARSAYIM, literature constants)",
                          joints=HR.JOINTS, gain=HR.G.tolist(), theta_max_deg=float(np.degrees(HR.THETA_MAX)),
                          yaw_reset_deg=float(np.degrees(HR.YAW_RESET)), tau_rc=HR.TAU_RC, kp=HR.KP,
                          turn_rate=HR.TURN_RATE, n_yaw_resets=body.head.n_resets)
                     if args.head_reflex else {}),
        assumptions=["readout low-pass tau 50 ms", "MN9 threshold 10 Hz from the R0 curve",
                     "yaw: per-side symmetric-grating reference subtracted, common scale mean(ref_L, ref_R)",
                     "yaw readout DNp15 only: POST-HOC choice",
                     "yaw: ipsilateral DN -> turn sign, K_STEER = 1",
                     "T4/T5 transduction R_MAX/R_CLIP"]
                    + (["vision boundary layer: rule >= 50 % outgoing synapses to non-FlyVis neurons; columns of "
                        "non-columnar neurons by partner-mean column; per-type a_ref from a fixed standard stimulus "
                        "set; graded -> Poisson rate for non-spiking types; a_ref < 1e-3 -> 0 Hz"] if vb else [])
                    + ["sugar GRN drive on tarsus-platform contact", "right sugar GRN homologs by connectivity kNN"]
                    + (["leg GRNs: sugar-like subset by connectivity kNN vs labellar sugar/water + bitter; driven "
                        "on any tarsus-platform contact (no tarsus -> GRN map)"] if args.leg_grn else [])
                    + (["ORN spontaneous rate per glomerulus: Hallem & Carlson 2006 (DoOR SFR) for 23 glomeruli, "
                        "5 Hz for the other 30; co-expressed receptors averaged; food odour raises only the 6 food "
                        "glomeruli (odor_norm, ipsilateral)"] if args.olfaction_full else ["food ORN spontaneous 8 Hz"])
                    + (["graded APL gain from KC sparseness 5-10 % (non-spiking APL)"] if args.apl_graded else [])
                    + (["DA/SER/OCT/no-NT outgoing synapses silent on the fast path (--nt-modulatory-silent)"]
                       if args.nt_modulatory_silent else [])
                    + (["literature NT sign for the persistent-state cell types with a known fast transmitter "
                        "(Schlegel et al. 2024 known_nt; --nt-literature)"] if args.nt_literature else []),
    )
    body_max_pen = body.max_tower_penetration
    spikes = brain.spikes()
    positions = G.neuron_positions(brain.root_ids)
    extra = {"nt_silent/idx": brain.nt_silent_global.astype(np.int32)} if args.nt_modulatory_silent else {}
    if args.nt_literature:
        extra["nt_literature/idx"] = brain.nt_lit_global.astype(np.int32)
    if vb:
        n_cl = max(rec.n_done, 1)
        for s_ in ("L", "R"):
            extra[f"vision_boundary/idx_{s_}"] = np.asarray(brain.groups[f"vbnd_{s_}"], np.int32)
            extra[f"vision_boundary/type_code_{s_}"] = eyes.tcode[s_].astype(np.int16)
            extra[f"vision_boundary/target_rate_mean_{s_}"] = (vb_sum[s_] / n_cl).astype(np.float32)
        extra["vision_boundary/types"] = np.array(eyes.fw_types, dtype="S16")
    if olf_full is not None:
        for k_ in olf_full.idx:
            s_ = k_[-1]
            extra[f"olfaction_full/idx_{s_}"] = olf_full.idx[k_].astype(np.int32)
            extra[f"olfaction_full/spont_hz_{s_}"] = olf_full.spont[k_].astype(np.float32)
            extra[f"olfaction_full/food_{s_}"] = olf_full.food[k_].astype(np.int8)
            extra[f"olfaction_full/glomerulus_{s_}"] = olf_full.glom[k_].astype("S8")
    if display is not None:     # writes /flyvis/step_idx and closes before write_h5(mode="a")
        display.close()
    write_h5(out, rec, meta, spikes, brain.groups, positions, field, extra=extra, spike_counts=spike_counts,
             mode="a" if vb else "w")
    if rro is not None:
        ro_dir = Path(args.record_readout)
        ro_dir.mkdir(parents=True, exist_ok=True)
        ro_path = ro_dir / (out.name[:-len("_data.h5")] + "_readout.h5")
        rro.write(ro_path, rec, dict(seed=args.seed, start_offset=list(args.start_offset), start_yaw=args.start_yaw,
                                     git_hash=meta["git_hash"], n_steps=args.n_steps, flags=meta["flags"],
                                     readout_model=args.readout_model, shuffle_seed=args.shuffle_seed),
                  labels=label_arr)
        print(f"readout record written: {ro_path} ({ro_path.stat().st_size / 1e6:.1f} MB)")
    print(f"HDF5 written: {out} ({out.stat().st_size / 1e6:.1f} MB), {len(spikes[0]):,} spikes, "
          f"peak RSS {meta['peak_rss_gb']:.2f} GB, loop {loop_s:.1f} s")
    bs = brain_share(rec)
    if bs.get("n_wings_on"):
        print(f"turn terms (wings on, {bs['n_wings_on']} steps): sum|brain|/sum|total| = {bs['brain_over_total']:.3f}; "
              f"shares brain {bs['share_brain']:.3f} hand {bs['share_hand']:.3f} flyvis {bs['share_flyvis']:.3f} "
              f"reflex {bs['share_reflex']:.3f}")
    ph = rec.a["phase"][:rec.n_done]
    td = np.flatnonzero(ph == cfg.PHASE_CODE["touchdown"])
    fd = np.flatnonzero(rec.a["is_feeding"][:rec.n_done] > 0)
    print(f"touchdown step {td[0] if len(td) else None}, feeding steps {len(fd)} (first {fd[0] if len(fd) else None}), "
          f"tower-contact steps {int(rec.a['tower_contact'][:rec.n_done].sum())}, "
          f"max tower penetration {body_max_pen:.4f} mm")

    del brain, body, eyes, spikes, rec
    gc.collect()

    # ── video (Stage 5) ─────────────────────────────────────────────────────
    if not args.no_video:
        renderer = REPO / "render_flight_video.py"
        if renderer.exists():
            subprocess.run([sys.executable, str(renderer), str(out)], check=False)
        else:
            print("render_flight_video.py not present yet (Stage 5); video skipped")
    return out


if __name__ == "__main__":
    main()
