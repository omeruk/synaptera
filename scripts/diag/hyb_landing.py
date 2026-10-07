#!/usr/bin/env python
"""--hybrid HAND layer without a brain: take-off -> odor navigation -> approach -> landing.

Diagnosis/design check of flight/hybrid.py only (no FlyWire, no FlyVis; turn_brain and
turn_flyvis are 0 unless --replay-turn). Not a result.

  --replay-turn H5   add that run's recorded turn_dn series as a stand-in for turn_brain
                     (e.g. flight_v10 brain-only: DNp15 readout statistics in flight)
  --replay-offset K  start the replay at step K of the recorded series

    python scripts/diag/hyb_landing.py --n-steps 240 [--replay-turn simulations/flight_v10_..._data.h5]
"""
import argparse
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import h5py  # noqa: E402
import numpy as np  # noqa: E402

from flight import config as cfg  # noqa: E402
from flight import hybrid as H  # noqa: E402
from flight import quasi_steady as qs  # noqa: E402
from flight import sensors as S  # noqa: E402
from flight.body import FlightBody  # noqa: E402
from flight.odor_field_3d import build_arena_odor_field  # noqa: E402

DT = cfg.PHYSICS_STEPS_PER_DECISION * cfg.PHYSICS_DT


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-steps", type=int, default=240)
    ap.add_argument("--replay-turn", default=None)
    ap.add_argument("--replay-offset", type=int, default=0)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    replay = None
    if args.replay_turn:
        with h5py.File(args.replay_turn, "r") as f:
            replay = f["behavior/turn_dn"][:]
    field = build_arena_odor_field()
    body = FlightBody(legs="stand")
    head_id = __import__("mujoco").mj_name2id(body.m, __import__("mujoco").mjtObj.mjOBJ_BODY,
                                              f"{body.fly.name}/Head")
    for _ in range(cfg.CALIB_STEPS + cfg.PERSIST_CUT_STEPS):      # same perch time as the real run
        body.step(qs.WingCommand(0, 0, 0, on=False))
    body.set_legs("tuck")
    pm = H.HybridPhases()
    t0 = body.sim.curr_time
    log = dict(t_touch=None, tower_steps=0, max_pen=0.0, min_clear=np.inf, badqacc=0, v_touch=None)
    tw = time.time()
    for k in range(args.n_steps):
        st = body.state()
        con = body.contacts()
        phase = pm.update(st["pos"], st["vel"], int(con["platform_legs"].sum()))
        if pm.legs_extended and body.legs != "stand":
            body.set_legs("stand")
        if phase == "touchdown":
            body.set_legs("stand", adhesion=1.0)
            log["t_touch"] = st["time"] - t0
            log["v_touch"] = float(np.linalg.norm(st["vel"]))
        od = S.sample_odor(field, body.d.xpos[head_id].copy(), st["R"])
        tb = 0.0 if replay is None else float(replay[(args.replay_offset + k) % len(replay)])
        th = H.turn_hand(od["I_asym"], phase)
        turn = H.combine_turn(tb, th, 0.0)
        thrust = H.thrust_hand(phase, st["pos"][2], st["vel"][2], od["I_grad"])["total"]
        pd, rr, v_des = H.tilt_hand(phase, st["pos"], st["vel"], st["heading"])
        cmd, lift = H.wing_command(turn, thrust, pd, rr, body.params, wings_on=pm.wings_on)
        r = body.step(cmd, pitch_down=pd, roll_right=rr)
        c1 = body.contacts()
        log["tower_steps"] += int(c1["tower_contact"])
        log["max_pen"] = max(log["max_pen"], r["tower_penetration"])
        log["min_clear"] = min(log["min_clear"], c1["min_tower_clearance"])
        log["badqacc"] = r["badqacc"]
        s1 = body.state()
        d_xy = float(np.linalg.norm(H.platform_offset(s1["pos"])))
        treflex = qs.yaw_torque_to_turn(r["haltere_yaw"], body.params, cfg.TURN_DPHI_DEG)
        if not args.quiet and (k % 8 == 0 or phase in ("descend", "touchdown")):
            print(f"{k:03d} t={s1['time'] - t0:.3f} [{phase:8s}] pos=({s1['pos'][0]:6.1f},{s1['pos'][1]:6.1f},"
                  f"{s1['pos'][2]:6.1f}) |v|={np.linalg.norm(s1['vel']):5.0f} vz={s1['vel'][2]:+5.0f} d_xy={d_xy:6.1f} "
                  f"turn b{tb:+.2f} h{th:+.2f} refl{treflex:+.2f} thrust {thrust:+.2f} pd {np.degrees(pd):+5.1f} "
                  f"rr {np.degrees(rr):+5.1f} plat {int(c1['platform_legs'].sum())} tower {int(c1['tower_contact'])}")
    print(f"touchdown t={log['t_touch']} |v|={log['v_touch']} tower_steps={log['tower_steps']} "
          f"max_pen={log['max_pen']:.4f} min_clear={log['min_clear']:.1f} badqacc={log['badqacc']} "
          f"final phase={pm.phase} final pos={np.round(body.state()['pos'], 1)} wall {time.time() - tw:.0f}s")
    return log


if __name__ == "__main__":
    main()
