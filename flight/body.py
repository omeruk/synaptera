"""FlyGym body + arena for flight, stroke-averaged forces via xfrc_applied.

- Arena: FlatTerrain + two towers (boxes), take-off pedestal and food platform
  (cylinders). Obstacle geoms carry the CLAUDE.md solimp/solref; the fly-arena
  contact pairs created by FlyGym keep FlyGym's defaults (pair values override).
  Arena geoms have contype = conaffinity = 0: only the explicit pairs collide.
- Obstacles and ground carry high-contrast checker textures (config TEXTURE_*);
  textured=False restores the uniform colours.
- platform="dark" (Step 2 arena design; the flight script default): the food platform pillar and the
  droplet are uniformly dark (PLATFORM_DARK_RGBA); "neutral" (class default): the platform has the
  same checker as the other obstacles (control). Visual only; contacts unchanged.
- Visual-only geoms are named "viz_*"; their FlyGym contact pairs are removed.
- The fly collides with the arena with its body, head, wings and legs
  (antennae, aristae and halteres are excluded to keep the pair count down).
- Every physics step: aero wrench (flight/quasi_steady.py) + haltere reflex
  (HAND-MADE), force applied at the whole-fly COM through the Thorax xfrc.
"""
import mujoco
import numpy as np
from flygym import Fly, SingleFlySimulation
from flygym.arena import FlatTerrain
from flygym.examples.locomotion import PreprogrammedSteps
from flygym.state import KinematicPose

from flight import config as cfg
from flight import head_reflex as HR
from flight import quasi_steady as qs

OBSTACLES = ("tower1", "tower2", "pedestal", "food_platform")
TOWERS = ("tower1", "tower2")
EXCLUDED_COLLISION_PARTS = ("Pedicel", "Funiculus", "Arista", "Haltere")
LEGS = ("LF", "LM", "LH", "RF", "RM", "RH")


def _box_mesh(size, period):
    """Box (half-extents `size`) as 6 separate quads with texcoords in units of
    `period` (mm), so a 2D checker has the same period on every face. MuJoCo does
    not tile 2D textures on the sides of box/cylinder primitives."""
    hx, hy, hz = size
    verts, uvs, faces = [], [], []
    # (normal axis, sign, in-plane axes u, v) with u x v = outward normal
    for ax, sg, a, b in ((0, 1, 1, 2), (0, -1, 2, 1), (1, 1, 2, 0), (1, -1, 0, 2), (2, 1, 0, 1), (2, -1, 1, 0)):
        h = np.array([hx, hy, hz])
        n0 = len(verts)
        for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            p = np.zeros(3)
            p[ax] = sg * h[ax]
            p[a] = du * h[a]
            p[b] = dv * h[b]
            verts.append(p)
            uvs.append((p[a] / period, p[b] / period))
        faces += [(n0, n0 + 1, n0 + 2), (n0, n0 + 2, n0 + 3)]
    return np.array(verts), np.array(uvs), np.array(faces)


def _cylinder_mesh(r, hz, period, n=48):
    """Closed cylinder (radius r, half-height hz): side texcoords = (arc length, z)
    / period, caps = (x, y) / period."""
    verts, uvs, faces = [], [], []
    ang = np.linspace(0, 2 * np.pi, n + 1)          # seam vertex duplicated for the texcoords
    for z in (-hz, hz):
        for a in ang:
            verts.append((r * np.cos(a), r * np.sin(a), z))
            uvs.append((r * a / period, z / period))
    for i in range(n):
        b0, t0 = i, n + 1 + i
        faces += [(b0, b0 + 1, t0 + 1), (b0, t0 + 1, t0)]
    for z, sg in ((-hz, -1), (hz, 1)):
        c = len(verts)
        verts.append((0.0, 0.0, z))
        uvs.append((0.0, 0.0))
        ring = []
        for a in ang[:-1]:
            ring.append(len(verts))
            verts.append((r * np.cos(a), r * np.sin(a), z))
            uvs.append((r * np.cos(a) / period, r * np.sin(a) / period))
        for i in range(n):
            j, k = ring[i], ring[(i + 1) % n]
            faces.append((c, j, k) if sg > 0 else (c, k, j))
    return np.array(verts), np.array(uvs), np.array(faces)


class FlightArena(FlatTerrain):
    """textured=True: obstacles are drawn by visual-only checker meshes ("viz_tex_*",
    contype 0, no contact pairs) over the collision primitives, which are made
    invisible (alpha 0) but keep their names, solimp/solref and contacts."""

    def __init__(self, textured=True, platform="neutral"):
        if platform not in ("dark", "neutral"):
            raise ValueError(platform)
        super().__init__(size=cfg.ARENA_HALF_SIZE)
        dark = platform == "dark"
        wb = self.root_element.worldbody
        asset = self.root_element.asset
        soft = dict(solimp=cfg.OBSTACLE_SOLIMP, solref=cfg.OBSTACLE_SOLREF, contype=0, conaffinity=0)
        hidden = dict(rgba=(1, 1, 1, 0))
        if textured:
            rgb1, rgb2 = cfg.TEXTURE_RGB
            ground = asset.find("material", "grid")
            ground.texture.rgb1, ground.texture.rgb2 = rgb1, rgb2
            ground.texrepeat = tuple(2 * h / cfg.GROUND_TEX_PERIOD for h in cfg.ARENA_HALF_SIZE)
            tex = asset.add("texture", name="obstacle_checker", type="2d", builtin="checker",
                            width=64, height=64, rgb1=rgb1, rgb2=rgb2)
            mat = asset.add("material", name="obstacle_mat", texture=tex)

            def viz_mesh(name, pos, mesh, rgba=None):
                v, uv, f = mesh
                asset.add("mesh", name=f"mesh_{name}", vertex=v.ravel(), texcoord=uv.ravel(), face=f.ravel())
                look = dict(rgba=rgba) if rgba is not None else dict(material=mat, rgba=(1, 1, 1, 1))
                wb.add("geom", type="mesh", name=f"viz_tex_{name}", mesh=f"mesh_{name}", pos=pos,
                       **look, contype=0, conaffinity=0, mass=0)
        for name, box in (("tower1", cfg.TOWER1), ("tower2", cfg.TOWER2)):
            (x0, x1), (y0, y1), (z0, z1) = box
            pos = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
            size = ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2)
            wb.add("geom", type="box", name=name, pos=pos, size=size,
                   **(hidden if textured else dict(rgba=(0.55, 0.55, 0.6, 1.0))), **soft)
            if textured:
                viz_mesh(name, pos, _box_mesh(size, cfg.OBSTACLE_TEX_PERIOD))
        for name, (cx, cy, r, zt), rgba in (("pedestal", cfg.TAKEOFF_PEDESTAL, (0.4, 0.3, 0.2, 1)),
                                            ("food_platform", cfg.FOOD_PLATFORM, (0.3, 0.5, 0.3, 1))):
            is_dark = dark and name == "food_platform"
            if is_dark:
                rgba = cfg.PLATFORM_DARK_RGBA
            wb.add("geom", type="cylinder", name=name, pos=(cx, cy, zt / 2), size=(r, zt / 2),
                   **(hidden if textured else dict(rgba=rgba)), **soft)
            if textured:
                viz_mesh(name, (cx, cy, zt / 2), _cylinder_mesh(r, zt / 2, cfg.OBSTACLE_TEX_PERIOD),
                         rgba=cfg.PLATFORM_DARK_RGBA if is_dark else None)
        wb.add("geom", type="sphere", name="viz_food_drop", pos=tuple(cfg.FOOD_POS),
               size=(cfg.FOOD_DROP_RADIUS,), rgba=cfg.PLATFORM_DARK_RGBA if dark else (0.9, 0.7, 0.1, 1),
               contype=0, conaffinity=0)


class FlightFly(Fly):
    """Fly whose arena collision set is body + legs, without pairs to viz_* geoms."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.floor_collisions = [
            g.name for g in self.model.find_all("geom")
            if g.name and not any(p in g.name for p in EXCLUDED_COLLISION_PARTS)
        ]

    def init_floor_contacts(self, arena):
        super().init_floor_contacts(arena)
        for key, pair in list(self._floor_contacts.items()):
            if key.startswith("viz_"):
                pair.remove()
                del self._floor_contacts[key]


def pose_from_offsets(joint_names, stand, offsets):
    """stand + offsets (deg, per leg part; R-side roll/yaw mirrored), actuated-joint order."""
    pose = stand.copy()
    for part, dv in offsets.items():
        for side in "LR":
            j = joint_names.index(f"joint_{side}{part}")
            mirror = -1 if (side == "R" and ("roll" in part or "yaw" in part)) else 1
            pose[j] += np.radians(dv) * mirror
    return pose


def leg_poses(joint_names):
    """(stand, tuck) joint angle arrays in actuated-joint order."""
    stand = np.array(PreprogrammedSteps().default_pose, dtype=float)
    return stand, pose_from_offsets(joint_names, stand, cfg.TUCK_POSE_OFFSETS)


def point_box_distance(p, box):
    lo = np.array([b[0] for b in box])
    hi = np.array([b[1] for b in box])
    return float(np.linalg.norm(np.maximum(0, np.maximum(lo - p, p - hi))))


class FlightBody:
    def __init__(self, spawn_pos=None, spawn_yaw=0.0, legs="stand", enable_adhesion=True,
                 enable_vision=False, vision_refresh_rate=40, textured=True, platform="neutral",
                 head_reflex=False, postures=False):
        if spawn_pos is None:  # standing on the take-off pedestal
            spawn_pos = (cfg.TAKEOFF_PEDESTAL[0], cfg.TAKEOFF_PEDESTAL[1], cfg.TAKEOFF_PEDESTAL[3] + 0.5)
        joint_names = list(Fly().actuated_joints)
        self.stand_pose, self.tuck_pose = leg_poses(joint_names)
        self.feed_pose = None
        if postures:          # --postures: flight pose replaces the tuck pose, plus a feeding pose (HAND)
            self.tuck_pose = pose_from_offsets(joint_names, self.stand_pose, cfg.FLIGHT_POSE_OFFSETS)
            self.feed_pose = pose_from_offsets(joint_names, self.stand_pose, cfg.FEED_POSE_OFFSETS)
        init = self.stand_pose if legs == "stand" else self.tuck_pose
        self.fly = FlightFly(
            spawn_pos=tuple(spawn_pos), spawn_orientation=(0.0, 0.0, spawn_yaw),
            init_pose=KinematicPose(dict(zip(joint_names, init))),
            enable_adhesion=enable_adhesion, enable_vision=enable_vision,
            vision_refresh_rate=vision_refresh_rate,
        )
        neck_acts = None
        if head_reflex:       # --head-reflex (flight/head_reflex.py): position actuators on the 3 neck joints
            neck_acts = [self.fly.model.actuator.add("position", name=f"actuator_neck_{a}",
                                                     joint=self.fly.model.find("joint", HR.JOINTS[a]),
                                                     kp=HR.KP, ctrllimited=False, forcelimited=False)
                         for a in HR.AXES]
        self.sim = SingleFlySimulation(fly=self.fly, arena=FlightArena(textured=textured, platform=platform), cameras=[],
                                       timestep=cfg.PHYSICS_DT)
        self.sim.reset()
        self.enable_adhesion = enable_adhesion
        self.physics = self.sim.physics
        self.m = self.physics.model.ptr
        self.d = self.physics.data.ptr
        m = self.m
        name = self.fly.name
        self.root = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{name}/")
        self.thorax = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{name}/Thorax")
        # The free root body "<name>/" carries a 1e-6 g dummy inertial whose ipos equals the
        # spawn position, i.e. |spawn| mm away from the fly (xipos = 2*spawn). Left there it
        # adds 1e-6*|spawn|^2 g*mm^2 to the real dynamics (x60 roll inertia at 175 mm) and
        # shifts subtree_com by ~0.1% of |spawn|. Put it at the body origin (inside the fly).
        m.body_ipos[self.root] = 0.0
        mujoco.mj_forward(m, self.d)
        self.obstacle_geom = {g: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, g) for g in OBSTACLES}
        self.ground_geom = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "ground")
        self.tower_ids = np.array([self.obstacle_geom[t] for t in TOWERS])
        # fly geom id -> leg index (tarsus segments only), -1 otherwise
        self.tarsus_leg = np.full(m.ngeom, -1, dtype=int)
        self.fly_geom = np.zeros(m.ngeom, dtype=bool)
        for gid in range(m.ngeom):
            gname = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, gid) or ""
            if gname.startswith(f"{name}/"):
                self.fly_geom[gid] = True
                part = gname[len(name) + 1:]
                if "Tarsus" in part:
                    self.tarsus_leg[gid] = LEGS.index(part[:2])
        self.mass = float(m.body_subtreemass[self.root])
        self.params = qs.make_params(self.mass, float(-m.opt.gravity[2]), self.inertia_body(), cfg)
        self.legs = legs
        self.leg_target = init.copy()          # PD joint target applied at the last physics step
        self._ramp = None                      # (start, end, n_done, n_total) physics steps
        self._act_ids = np.asarray(self.physics.bind(self.fly.actuators).element_id)
        self.adhesion = np.zeros(6)
        self.badqacc0 = self.badqacc_count()
        self.max_tower_penetration = 0.0
        self.head = None
        if head_reflex:
            self.head = HR.HeadReflex()
            self._neck_ids = np.asarray(self.physics.bind(neck_acts).element_id)
            jids = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{name}/{HR.JOINTS[a]}") for a in HR.AXES]
            self._neck_qadr = np.array([m.jnt_qposadr[j] for j in jids])
        self.head_body = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{name}/Head")

    # ── model quantities ────────────────────────────────────────────────────
    def inertia_body(self):
        """Composite inertia of the whole fly about its COM, in thorax axes."""
        m, d = self.m, self.d
        mujoco.mj_forward(m, d)
        com = d.subtree_com[self.root].copy()
        I = np.zeros((3, 3))
        for b in range(m.nbody):
            if m.body_rootid[b] != self.root or m.body_mass[b] == 0:
                continue
            Rb = d.ximat[b].reshape(3, 3)
            r = d.xipos[b] - com
            I += Rb @ np.diag(m.body_inertia[b]) @ Rb.T + m.body_mass[b] * (r @ r * np.eye(3) - np.outer(r, r))
        Rt = d.xmat[self.thorax].reshape(3, 3)
        return Rt.T @ I @ Rt

    def yaw_pulse_torque(self, deg, duration):
        """Body-z torque (uN*mm) that, against the total yaw damping I_zz/HALTERE_YAW_TAU alone
        (turn command 0), holds the yaw rate deg/duration: a first-order system then turns by
        `deg` in total (--yaw-perturb, experiment design; + = left/CCW)."""
        izz = float(self.inertia_body()[2, 2])
        return izz / cfg.HALTERE_YAW_TAU * np.radians(deg) / duration

    def badqacc_count(self):
        return int(self.d.warning[mujoco.mjtWarning.mjWARN_BADQACC].number)

    # ── state ───────────────────────────────────────────────────────────────
    def state(self):
        m, d = self.m, self.d
        mujoco.mj_subtreeVel(m, d)
        R = d.xmat[self.thorax].reshape(3, 3).copy()
        return dict(pos=d.subtree_com[self.root].copy(), vel=d.subtree_linvel[self.root].copy(),
                    R=R, quat=d.xquat[self.thorax].copy(), omega=d.cvel[self.thorax][:3].copy(),
                    heading=qs.heading_of(R), time=self.sim.curr_time)

    def contacts(self):
        """Current contacts: tarsus-platform legs, tower contact, max tower penetration."""
        d = self.d
        n = d.ncon
        legs_on = {g: np.zeros(6, dtype=bool) for g in ("food_platform", "pedestal", "ground")}
        tower, pen = False, 0.0
        if n:
            g1 = d.contact.geom1[:n]
            g2 = d.contact.geom2[:n]
            dist = d.contact.dist[:n]
            for a, b, dd in zip(g1, g2, dist):
                other, flyg = (b, a) if self.fly_geom[a] else (a, b)
                if not self.fly_geom[flyg]:
                    continue
                if other in self.tower_ids:
                    tower = True
                    pen = max(pen, -dd)
                for gname in legs_on:
                    gid = self.ground_geom if gname == "ground" else self.obstacle_geom[gname]
                    if other == gid and self.tarsus_leg[flyg] >= 0:
                        legs_on[gname][self.tarsus_leg[flyg]] = True
        pos = self.d.subtree_com[self.root]
        clearance = min(point_box_distance(pos, b) for b in cfg.TOWERS)
        return dict(platform_legs=legs_on["food_platform"], pedestal_legs=legs_on["pedestal"],
                    ground_legs=legs_on["ground"], tower_contact=tower, tower_penetration=pen,
                    min_tower_clearance=clearance)

    # ── stepping ────────────────────────────────────────────────────────────
    def set_legs(self, legs, adhesion=None, ramp_s=None):
        """Leg pose "stand"/"tuck"/"feed" (feed only with postures=True). A pose change starts a cosine
        ramp of the PD joint target from the current target (HAND-MADE, HAND; durations
        cfg.LEG_TUCK_RAMP_S / LEG_EXTEND_RAMP_S, to or from "feed" cfg.LEG_FEED_RAMP_S, unless ramp_s).
        Repeating the current pose does not restart a running ramp."""
        if legs not in ("stand", "tuck", "feed") or (legs == "feed" and self.feed_pose is None):
            raise ValueError(legs)
        if legs != self.legs:
            if ramp_s is None:
                ramp_s = (cfg.LEG_FEED_RAMP_S if "feed" in (legs, self.legs) else
                          cfg.LEG_TUCK_RAMP_S if legs == "tuck" else cfg.LEG_EXTEND_RAMP_S)
            end = {"stand": self.stand_pose, "tuck": self.tuck_pose, "feed": self.feed_pose}[legs]
            n = max(1, int(round(ramp_s / cfg.PHYSICS_DT)))
            self._ramp = (self.leg_target.copy(), end, 0, n)
        self.legs = legs
        if adhesion is not None:
            self.adhesion = np.full(6, float(adhesion)) if np.isscalar(adhesion) else np.asarray(adhesion, float)

    def step(self, cmd, pitch_down=0.0, roll_right=0.0, n_steps=cfg.PHYSICS_STEPS_PER_DECISION,
             haltere=None, ext_torque=None, snap_at=(), render_at=()):
        """Advance n_steps physics steps with a constant wing command.

        pitch_down/roll_right (rad): attitude targets of the haltere reflex
        (active whenever the wings are on unless haltere=False).
        ext_torque: extra world-frame torque (uN*mm) on the thorax, e.g. a gust (tests).
        snap_at: physics sub-step indices before which qpos is copied (video replay).
        render_at: sub-step counts after which both eyes are rendered (e.g. (125, 250)).
        Returns mean applied force/torque (world), the max tower penetration, the
        qpos/qvel snapshots, the rendered vision frames and the mean haltere yaw torque
        about body z (uN*mm; --hybrid records it as turn_reflex)."""
        m, d = self.m, self.d
        haltere = cmd.on if haltere is None else haltere
        action = {"joints": self.leg_target}
        if self.enable_adhesion:
            action["adhesion"] = self.adhesion
        self.fly.pre_step(action, self.sim)
        F_acc, T_acc, pen_max = np.zeros(3), np.zeros(3), 0.0
        hal_yaw = 0.0             # haltere yaw torque about body z (uN*mm), summed
        p = self.params
        snap_at = set(snap_at)
        render_at = set(render_at)
        snaps, vsnaps, frames = [], [], []
        hd = self.head is not None
        h_gaze = h_body = 0.0                 # sub-step sums of the gaze / body yaw rate about thorax z
        h_turn = h_turn_lt = 0                # turning sub-steps, and those with |gaze| < |body| (B-H3)
        h_qmax = np.zeros(3)
        for k in range(n_steps):
            if k in snap_at:
                snaps.append(d.qpos.copy())
                vsnaps.append(d.qvel.copy())
            if cmd.on or haltere:
                mujoco.mj_subtreeVel(m, d)
                R = d.xmat[self.thorax].reshape(3, 3)
                com = d.subtree_com[self.root]
                v = d.subtree_linvel[self.root]
                w = d.cvel[self.thorax][:3]
                F, T, _ = qs.aero_wrench(R, v, w, cmd, p)
                if haltere:
                    z_des = qs.desired_up(qs.heading_of(R), pitch_down, roll_right)
                    T_h = qs.haltere_torque(R, w, z_des, p)
                    hal_yaw += float(R[:, 2] @ T_h)
                    T = T + T_h
                # xfrc acts at the thorax COM: shift the force to the whole-fly COM
                d.xfrc_applied[self.thorax, :3] = F
                d.xfrc_applied[self.thorax, 3:] = T + np.cross(com - d.xipos[self.thorax], F)
                F_acc += F
                T_acc += T
            else:
                d.xfrc_applied[self.thorax] = 0.0
            if ext_torque is not None:
                d.xfrc_applied[self.thorax, 3:] += ext_torque
            d.ctrl[self._act_ids] = self._advance_leg_target()
            if hd:                            # HAND reflex, every sub-step (flight/head_reflex.py)
                Rh = d.xmat[self.thorax].reshape(3, 3)
                w_t = d.cvel[self.thorax][:3]
                d.ctrl[self._neck_ids] = self.head.update(Rh.T @ w_t, cfg.PHYSICS_DT)
            self.physics.step()
            if hd:
                z_t = d.xmat[self.thorax].reshape(3, 3)[:, 2]
                wb = float(d.cvel[self.thorax][:3] @ z_t)
                wg = float(d.cvel[self.head_body][:3] @ z_t)
                h_gaze += wg
                h_body += wb
                if abs(wb) > HR.TURN_RATE:
                    h_turn += 1
                    h_turn_lt += int(abs(wg) < abs(wb))
                np.maximum(h_qmax, np.abs(d.qpos[self._neck_qadr]), out=h_qmax)
            n = d.ncon
            if n:
                g1 = d.contact.geom1[:n]
                g2 = d.contact.geom2[:n]
                hit = np.isin(g1, self.tower_ids) | np.isin(g2, self.tower_ids)
                if hit.any():
                    pen_max = max(pen_max, float(-d.contact.dist[:n][hit].min()))
            if k + 1 in render_at:
                frames.append(self.update_vision().copy())
        self.sim.curr_time += n_steps * cfg.PHYSICS_DT
        self.max_tower_penetration = max(self.max_tower_penetration, pen_max)
        return dict(force=F_acc / n_steps, torque=T_acc / n_steps, tower_penetration=pen_max,
                    badqacc=self.badqacc_count() - self.badqacc0, qpos=snaps, qvel=vsnaps, frames=frames,
                    haltere_yaw=hal_yaw / n_steps,
                    head=dict(q=d.qpos[self._neck_qadr].copy(), target=self.head.target.copy(), q_absmax=h_qmax,
                              gaze_yaw_rate=h_gaze / n_steps, body_yaw_rate=h_body / n_steps,
                              turn_sub=h_turn, turn_sub_lt=h_turn_lt) if hd else None)

    def _advance_leg_target(self):
        """PD joint target for the next physics step (cosine ramp while a transition runs)."""
        if self._ramp is not None:
            start, end, i, n = self._ramp
            i += 1
            s = 0.5 * (1.0 - np.cos(np.pi * i / n))
            self.leg_target = start + s * (end - start)
            self._ramp = None if i >= n else (start, end, i, n)
        return self.leg_target

    @property
    def leg_ramp_active(self):
        return self._ramp is not None

    def update_vision(self):
        """Render both compound eyes now (FlyGym ommatidia readout, (2, 721, 2)).
        Needs enable_vision=True. Called once per decision step."""
        self.fly._last_vision_update_time = -np.inf
        self.fly._update_vision(self.sim)
        return self.fly._curr_visual_input

    def set_velocity(self, v_world):
        """Set the free-joint linear velocity (tests / initial conditions)."""
        adr = self.m.jnt_dofadr[self.m.body_jntadr[self.root]]
        self.d.qvel[adr:adr + 3] = v_world
        mujoco.mj_forward(self.m, self.d)
