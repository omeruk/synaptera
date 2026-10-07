"""HDF5 recording for flight runs (schema: SPEC_FLIGHT.md, HDF5 section)."""
import json
from pathlib import Path

import h5py
import numpy as np

from flight.readouts import READOUT_TYPES

SIM_DIR = Path(__file__).resolve().parent.parent / "simulations"


def _abl(sets):
    """ablate_dn: True (legacy flag) -> "ablDN"; a set list -> "ablDN-steer+mn9"."""
    if sets is True:
        return "ablDN"
    return "ablDN-" + "+".join(sorted(sets))


def output_stem(version, dev_subnet=False, ablate_dn=False, ablate_odor=False,
                antenna_real=False, tag=None, asc_legacy=False, untextured=False, apl_graded=False,
                no_olfaction=False, nt_silent=False, legacy_control=False, start_on_platform=False,
                swap_dn=(), platform_neutral=False, spawn_air=None, hover=False, yaw_perturb=None,
                hybrid=False, vision_boundary=False, olfaction_full=False, leg_grn=False, nt_literature=False,
                no_brain_steer=False, head_reflex=False, postures=False, start_offset=None, start_yaw=0.0):
    """flight_v{N}[_DEV][_hybrid][_sA][_sB][_legGRN][_noBrSteer][_head][_pose][_ablDN][_ablOdor][_antReal][_ascLeg][_noTex][_aplG][_noOlf][_ntS-<variant>][_ntLit][_legacy][_onPlat]
    [_swapDN-steer][_platNeutral][_airX_Y_Z_YAW][_hover][_yawP<deg>][_start<dx>_<dy>][_startYaw<deg>][_tag].
    DEV runs are never results."""
    parts = [f"flight_v{version}"]
    if dev_subnet:
        parts.append("DEV")
    if hybrid:
        parts.append("hybrid")
    if olfaction_full:
        parts.append("sA")
    if vision_boundary:
        parts.append("sB")
    if leg_grn:
        parts.append("legGRN")
    if no_brain_steer:
        parts.append("noBrSteer")
    if head_reflex:
        parts.append("head")
    if postures:
        parts.append("pose")
    if ablate_dn:
        parts.append(_abl(ablate_dn))
    if ablate_odor:
        parts.append("ablOdor")
    if antenna_real:
        parts.append("antReal")
    if asc_legacy:
        parts.append("ascLeg")
    if untextured:
        parts.append("noTex")
    if apl_graded:
        parts.append("aplG")
    if no_olfaction:
        parts.append("noOlf")
    if nt_silent:
        parts.append(f"ntS-{nt_silent}" if isinstance(nt_silent, str) else "ntS")
    if nt_literature:
        parts.append("ntLit")
    if legacy_control:
        parts.append("legacy")
    if start_on_platform:
        parts.append("onPlat")
    if swap_dn:
        parts.append("swapDN-" + "+".join(sorted(swap_dn)))
    if platform_neutral:
        parts.append("platNeutral")
    if spawn_air:
        parts.append("air" + "_".join(f"{v:g}" for v in spawn_air))
    if hover:
        parts.append("hover")
    if yaw_perturb:
        parts.append(f"yawP{yaw_perturb[1]:+g}")
    if start_offset is not None and any(start_offset):
        parts.append("start" + "_".join(f"{v:+g}" for v in start_offset))
    if start_yaw:
        parts.append(f"startYaw{start_yaw:+g}")
    if tag:
        parts.append(str(tag))
    return "_".join(parts)


def h5_path(version, sim_dir=SIM_DIR, **flags):
    return Path(sim_dir) / (output_stem(version, **flags) + "_data.h5")


# ── behaviour arrays ────────────────────────────────────────────────────────
# name -> (trailing shape, dtype); every array has a leading n_steps axis
BEHAVIOR_FIELDS = {
    # state
    "t": ((), np.float64), "pos": ((3,), np.float64), "vel": ((3,), np.float64),
    "speed": ((), np.float64), "quat": ((4,), np.float64), "omega": ((3,), np.float64),
    "heading": ((), np.float64), "dist_to_food": ((), np.float64), "phase": ((), np.int8),
    # odor
    "odor_L": ((), np.float64), "odor_R": ((), np.float64), "odor_U": ((), np.float64),
    "odor_D": ((), np.float64), "I_asym": ((), np.float64), "I_grad": ((), np.float64),
    "I_asym_real": ((), np.float64), "I_grad_real": ((), np.float64),
    "ell_LR": ((), np.float64), "ell_UD": ((), np.float64), "v_fwd": ((), np.float64),
    # turn terms
    "turn_bias": ((), np.float64), "turn_odor": ((), np.float64), "turn_dn": ((), np.float64),
    "turn_loom": ((), np.float64), "dn_lr_delta": ((), np.float64),
    # collective / pitch terms
    "pitch_bias": ((), np.float64), "pitch_odor": ((), np.float64), "pitch_alt": ((), np.float64),
    "pitch_ventral": ((), np.float64), "pitch_takeoff": ((), np.float64),
    "lift_frac": ((), np.float64), "pitch_down": ((), np.float64),
    # motor
    "stroke_amp_L": ((), np.float64), "stroke_amp_R": ((), np.float64),
    "stroke_freq": ((), np.float64), "force": ((3,), np.float64), "torque": ((3,), np.float64),
    # input rates (Hz): asc (0 unless --asc-legacy), food-ORN L/R, sugar GRN, T4/T5 mean per eye
    # and per eye x subtype (T4a..d, T5a..d)
    "asc_rate": ((), np.float64), "olf_rate_L": ((), np.float64), "olf_rate_R": ((), np.float64),
    "sugar_rate_in": ((), np.float64), "t45_rate_L": ((), np.float64), "t45_rate_R": ((), np.float64),
    "t45_type_rate": ((2, 8), np.float64), "net_rate": ((), np.float64),
    # --vision-boundary: target (FlyVis) rate per eye x boundary type (meta visual.boundary_types order;
    # 0 without the flag); t45_* then hold the T4/T5 members of the boundary layer
    "vbnd_type_rate": ((2, 32), np.float64),
    # vision
    "loom_L": ((), np.float64), "loom_R": ((), np.float64), "expansion_rate": ((), np.float64),
    "height_above": ((), np.float64),
    # DN counts per 25 ms
    "dng02_L": ((), np.int32), "dng02_R": ((), np.int32), "steer_L": ((), np.int32),
    "steer_R": ((), np.int32), "all_dn_L": ((), np.int32), "all_dn_R": ((), np.int32),
    "dnp01": ((), np.int32), "brain_mn": ((), np.int32),
    # brain readouts (flight/readouts.py READOUT_TYPES x L/R): spikes per 25 ms, and the
    # bridge's filtered rate (Hz per neuron; ablated rows hold the perch baseline)
    "dn_readout": ((len(READOUT_TYPES), 2), np.int32), "dn_readout_rate": ((len(READOUT_TYPES), 2), np.float64),
    # Step 1: proboscis = MN9 decision
    "mn9_rate": ((), np.float64), "proboscis_extended": ((), np.int8),
    # Step 2: yaw readout. steer_raw: L-R Hz of DNa02, DNp15 (filtered, unnormalised);
    # steer_norm_t: [(r_L-ref_L)-(r_R-ref_R)]/mean(ref) per type; steer_norm: s_hat = DNp15 (after swap);
    # platform_azimuth: bearing of the food platform (deg, + = left; recorded only)
    "steer_raw": ((2,), np.float64), "steer_norm_t": ((2,), np.float64), "steer_norm": ((), np.float64),
    "platform_azimuth": ((), np.float64),
    # --yaw-perturb: external torque about body z during the step (uN*mm; experiment design)
    "yaw_perturb_torque": ((), np.float64),
    # output / contact
    "sez_out_rate": ((), np.float64), "platform_contact": ((), np.int8),
    "tower_contact": ((), np.int8), "tower_penetration": ((), np.float64),
    "min_tower_clearance": ((), np.float64), "is_feeding": ((), np.int8),
    # term decomposition (all modes; SPEC_BRAIN_CONTROL "Honest hybrid final"):
    # turn_total = wing yaw command (= turn_bias); turn_brain = DNp15 bridge term; turn_hand =
    # odor map; turn_flyvis = FlyVis T5 b_loom; turn_reflex = haltere yaw damping expressed as the
    # equivalent turn_bias (physics, not part of turn_total). thrust_hand = collective (lift
    # fraction - 1, HAND); pitch_hand / roll_hand = body nose-down tilt / right bank targets (rad,
    # HAND); vz_des / v_des_h: HAND vertical / horizontal speed targets (mm/s; nan when unused)
    "turn_total": ((), np.float64), "turn_brain": ((), np.float64), "turn_hand": ((), np.float64),
    "turn_flyvis": ((), np.float64), "turn_reflex": ((), np.float64), "thrust_hand": ((), np.float64),
    "pitch_hand": ((), np.float64), "roll_hand": ((), np.float64), "vz_des": ((), np.float64),
    "v_des_h": ((), np.float64), "wings_on": ((), np.int8),
    # --head-reflex (flight/head_reflex.py; 0 without the flag): neck joint angles and targets (rad;
    # yaw, pitch, roll), max |angle| over the sub-steps, sub-step mean gaze (Head) and body (Thorax) yaw
    # rates about thorax z (rad/s), turning sub-steps (|body yaw rate| > 1 rad/s) and those with
    # |gaze| < |body| (B-H3)
    "head_q": ((3,), np.float64), "head_target": ((3,), np.float64), "head_q_absmax": ((3,), np.float64),
    "gaze_yaw_rate": ((), np.float64), "body_yaw_rate": ((), np.float64),
    "head_turn_sub": ((), np.int32), "head_turn_sub_lt": ((), np.int32),
    # leg pose being held / ramped to (cfg.LEG_POSE_CODE: 0 stand, 1 tuck or flight pose, 2 feed)
    "leg_pose": ((), np.int8),
    # timing
    "step_time": ((), np.float64), "brain_time": ((), np.float64), "rss_gb": ((), np.float64),
}


class BehaviorRecorder:
    def __init__(self, n_steps):
        self.n = n_steps
        self.a = {k: np.zeros((n_steps,) + shp, dtype=dt) for k, (shp, dt) in BEHAVIOR_FIELDS.items()}
        self.qpos, self.qvel, self.qpos_t = [], [], []
        self.n_done = 0

    def put(self, k, **vals):
        for name, v in vals.items():
            self.a[name][k] = v
        self.n_done = max(self.n_done, k + 1)

    def add_qpos(self, t, qpos, qvel=None):
        self.qpos_t.append(t)
        self.qpos.append(np.asarray(qpos, dtype=np.float64))
        if qvel is not None:
            self.qvel.append(np.asarray(qvel, dtype=np.float64))


class SparseSpikeCounts:
    """Per-decision-step spike counts of every neuron, stored sparsely (non-zero entries only).
    step_idx: closed-loop decision step (0 = first closed-loop step; the perch calibration and
    input-cut steps before it are negative, -n_pre .. -1). neuron_idx: global index (row of
    Completeness_783.csv). count: spikes in that 25 ms step."""

    def __init__(self, local_to_global=None):
        self.l2g = local_to_global
        self.s, self.i, self.c = [], [], []

    def add(self, step, per_neuron):
        nz = np.flatnonzero(per_neuron)
        gi = nz if self.l2g is None else self.l2g[nz]
        self.s.append(np.full(len(nz), step, dtype=np.int32))
        self.i.append(np.asarray(gi, dtype=np.int32))
        self.c.append(np.asarray(per_neuron[nz], dtype=np.uint8))

    def arrays(self):
        if not self.s:
            return np.zeros(0, np.int32), np.zeros(0, np.int32), np.zeros(0, np.uint8)
        return np.concatenate(self.s), np.concatenate(self.i), np.concatenate(self.c)


class ReadoutRecorder:
    """--record-readout (SPEC_SENSORY_INPUTS §3.6): everything a trained readout needs, one row per 25 ms step.
    Rows are the perch calibration and input-cut steps (step_idx -n_pre .. -1) followed by the closed-loop steps
    (0 .. n_steps-1). DN spike counts (int16), the boundary-layer rates as sensed (float32), the applied sugar
    rate and whether the brain inputs were applied (0 in the input-cut steps)."""

    def __init__(self, n_pre, n_steps, dn_local, dn_global, n_L, n_R):
        self.n_pre, self.n_steps = int(n_pre), int(n_steps)
        rows = self.n_pre + self.n_steps
        self.dn_local = np.asarray(dn_local, dtype=np.int64)
        self.dn_global = np.asarray(dn_global, dtype=np.int32)
        self.step_idx = np.arange(-self.n_pre, self.n_steps, dtype=np.int32)
        self.dn_counts = np.zeros((rows, len(self.dn_local)), np.int16)
        self.vbnd_L = np.zeros((rows, n_L), np.float32)
        self.vbnd_R = np.zeros((rows, n_R), np.float32)
        self.sugar_rate_in = np.zeros(rows)
        self.applied_inputs = np.zeros(rows, np.int8)
        self.done = np.zeros(rows, bool)

    def put(self, step, per_neuron, vbnd, sugar, applied):
        r = int(step) + self.n_pre
        self.dn_counts[r] = np.minimum(np.asarray(per_neuron)[self.dn_local], np.iinfo(np.int16).max)
        self.vbnd_L[r] = vbnd["L"]
        self.vbnd_R[r] = vbnd["R"]
        self.sugar_rate_in[r] = sugar
        self.applied_inputs[r] = int(applied)
        self.done[r] = True

    def write(self, path, rec, meta, labels=None):
        """rec: BehaviorRecorder of the run (teacher commands and body state of the closed-loop rows).
        labels (readout mode only): (n_steps x 4) teacher command of every visited state; then rec holds the APPLIED
        (readout) commands, written as `applied_cmd`, and `teacher_cmd` is the label."""
        n = rec.n_done
        rows = self.n_pre + n
        a = rec.a
        pre = self.n_pre
        cmd = np.zeros((rows, 4))
        cmd[pre:, 0], cmd[pre:, 1] = a["turn_hand"][:n], a["thrust_hand"][:n]
        cmd[pre:, 2], cmd[pre:, 3] = a["pitch_hand"][:n], a["roll_hand"][:n]
        applied = cmd.copy()
        if labels is not None:
            cmd[pre:] = np.asarray(labels)[:n]

        def pad(x):
            x = np.asarray(x[:n])
            return np.concatenate([np.zeros((pre,) + x.shape[1:], x.dtype), x])
        with h5py.File(path, "w") as f:
            f.create_dataset("step_idx", data=self.step_idx[:rows])
            f.create_dataset("dn_counts", data=self.dn_counts[:rows], compression="gzip")
            f.create_dataset("dn_neuron_idx", data=self.dn_global)
            f.create_dataset("vbnd_L", data=self.vbnd_L[:rows], compression="gzip")
            f.create_dataset("vbnd_R", data=self.vbnd_R[:rows], compression="gzip")
            f.create_dataset("sugar_rate_in", data=self.sugar_rate_in[:rows])
            f.create_dataset("applied_inputs", data=self.applied_inputs[:rows])
            f.create_dataset("teacher_cmd", data=cmd)
            f["teacher_cmd"].attrs["columns"] = "turn_hand, thrust_hand (total), pitch_hand, roll_hand; 0 before step 0"
            if labels is not None:
                f.create_dataset("applied_cmd", data=applied)
                f["applied_cmd"].attrs["columns"] = f["teacher_cmd"].attrs["columns"] + " (readout output actually applied)"
            for k in ("phase", "wings_on", "pos", "vel", "quat", "omega", "heading", "platform_contact", "tower_contact",
                      "tower_penetration", "is_feeding", "mn9_rate", "turn_flyvis"):
                f.create_dataset(k, data=pad(a[k]))
            f.attrs["n_pre"] = self.n_pre
            f.attrs["meta"] = json.dumps(meta)


def write_h5(path, rec, meta, spikes, groups, positions, field, extra=None, spike_counts=None, mode="w"):
    """Write the whole run (mode "a": into a file that already holds the streamed /flyvis display layer). spikes: (t float32 s, i int32 global). extra: {"group/name": array}.
    spike_counts: SparseSpikeCounts -> /spikes/step_idx, /spikes/neuron_idx, /spikes/count."""
    n = rec.n_done
    with h5py.File(path, mode) as f:
        m = f.create_group("meta")
        for k, v in meta.items():
            m.attrs[k] = json.dumps(v) if isinstance(v, (dict, list, tuple)) else v
        b = f.create_group("behavior")
        for k, arr in rec.a.items():
            b.create_dataset(k, data=arr[:n])
        b["phase"].attrs["codes"] = json.dumps(meta.get("phase_codes", {}))
        s = f.create_group("spikes")
        a = s.create_group("all")
        a.create_dataset("t", data=spikes[0].astype(np.float32), compression="gzip")
        a.create_dataset("i", data=spikes[1].astype(np.int32), compression="gzip")
        if spike_counts is not None:
            si, ni, cn = spike_counts.arrays()
            s.create_dataset("step_idx", data=si, compression="gzip")
            s.create_dataset("neuron_idx", data=ni, compression="gzip")
            s.create_dataset("count", data=cn, compression="gzip")
            s.attrs["step_idx"] = ("closed-loop decision step of 25 ms (0 = first); negative = perch "
                                   "calibration and input-cut steps before take-off")
            s.attrs["neuron_idx"] = "global neuron index = row of Completeness_783.csv (root_id order)"
            s.attrs["count"] = "spikes of that neuron in that step (non-zero entries only)"
        g = s.create_group("groups")
        for k, idx in groups.items():
            g.create_dataset(k, data=np.asarray(idx, dtype=np.int32))
        p = f.create_group("positions")
        for k, v in positions.items():
            p.create_dataset(k, data=v)
        o = f.create_group("odor_field_3d")
        o.create_dataset("conc", data=field.conc.astype(np.float32), compression="gzip")
        o.create_dataset("blocked", data=field.blocked, compression="gzip")
        o.attrs["origin"] = field.origin
        o.attrs["res"] = field.res
        o.attrs["food"] = field.food_pos
        r = f.create_group("render")
        r.create_dataset("t", data=np.asarray(rec.qpos_t, dtype=np.float64))
        q = np.stack(rec.qpos) if rec.qpos else np.zeros((0, 0))
        r.create_dataset("qpos", data=q, compression="gzip")
        if rec.qvel:
            r.create_dataset("qvel", data=np.stack(rec.qvel), compression="gzip")
        for k, v in (extra or {}).items():
            f.create_dataset(k, data=v, compression="gzip")
