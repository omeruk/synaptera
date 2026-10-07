"""Body-frame visual stimuli for the open-loop DN screen (SPEC_SENSORY_INPUTS.md §3.5).

The 10 conditions of the pre-registration are defined in body-frame angles (azimuth, + = left) and
rendered to the raw 512 x 450 eye images of the FlyGym eyes by ray casting: every raw pixel is a
pinhole camera ray (vertical field of view 157 deg) rotated into the body frame with the MuJoCo
camera orientation. From the raw image on, the existing path is used unchanged (uint8 RGB ->
Retina.raw_image_to_hex_pxls -> FlyVis -> boundary layer), exactly as visual_input.grating_frames.

Conditions (1-based, SPEC §3.5): 1 yaw-CW, 2 yaw-CCW, 3 static grating, 4 loom-left, 5 loom-right,
6 loom-front, 7 receding-left, 8 receding-right, 9 expanding flow, 10 grey;
added for SPEC §3.5b: 11 receding-front (time reversal of 6).
"""
import numpy as np

from flight import visual_input as V

H_PX, W_PX = 512, 450
FOVY_DEG = 157.0
GREY, CONTRAST = 0.5, V.GRATING_CONTRAST          # 0.8
WAVELENGTH_DEG, TF_HZ = 30.0, 2.0
LOOM_TAU = 0.040                                  # l/v
LOOM_START_DEG, LOOM_END_DEG = 5.0, 90.0
LOOM_TC = LOOM_TAU / np.tan(np.radians(LOOM_START_DEG / 2))     # time of collision (s)
LOOM_T90 = LOOM_TC - LOOM_TAU                                   # time at which the size is 90 deg
LOOM_DISC = GREY - 0.5 * CONTRAST                 # dark disc, 0.1
STIM_S, GREY_LEAD_S = 1.0, 0.5
FLOW_SPEED, FLOW_RADIUS, FLOW_PERIOD = 50.0, 50.0, 25.0         # mm/s, mm, mm
LOOM_AZ = {4: 60.0, 5: -60.0, 6: 0.0}
CONDITIONS = {1: "yaw_cw", 2: "yaw_ccw", 3: "static_grating", 4: "loom_left", 5: "loom_right", 6: "loom_front",
              7: "recede_left", 8: "recede_right", 9: "expanding_flow", 10: "grey", 11: "recede_front"}
N_STEPS, N_GREY_STEPS = 60, 20


def camera_rays(model, data, root_body):
    """Body-frame unit ray of every raw pixel, per eye: (2, 512, 450, 3), eye 0 = left, 1 = right.
    Body frame: x forward, y left, z up. Pose query only (needs mj_forward done)."""
    import mujoco
    f = (H_PX / 2) / np.tan(np.radians(FOVY_DEG) / 2)
    rr, cc = np.mgrid[0:H_PX, 0:W_PX]
    v = np.stack([(cc + 0.5 - W_PX / 2) / f, -(rr + 0.5 - H_PX / 2) / f, -np.ones_like(rr, float)], -1)
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    Rb = data.xmat[root_body].reshape(3, 3)
    out = []
    for name in ("LEye_cam", "REye_cam"):
        i = next(k for k in range(model.ncam) if mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_CAMERA, k).endswith(name))
        Rc = data.cam_xmat[i].reshape(3, 3)
        out.append(v @ (Rb.T @ Rc).T)
    return np.stack(out)


def azimuth(rays):
    return np.degrees(np.arctan2(rays[..., 1], rays[..., 0]))


def loom_size(t):
    """Full angular size (deg) of the loom disc at time t since onset (5 deg at 0, 90 deg at LOOM_T90, held)."""
    t = np.asarray(t, float)
    th = 2 * np.degrees(np.arctan(LOOM_TAU / np.maximum(LOOM_TC - np.minimum(t, LOOM_T90), 1e-9)))
    return np.where(t >= LOOM_T90, LOOM_END_DEG, th)


def size_at(cond, t):
    """Disc size for conditions 4-8 (receding = time reversal over the whole stimulus)."""
    if cond in (7, 8, 11):
        return float(loom_size(STIM_S - t))
    return float(loom_size(t))


def luminance(cond, t, rays):
    """Luminance in [0, 1] of every raw pixel, per eye (2, 512, 450). t = time since onset (s) or None (grey lead-in)."""
    if t is None or cond == 10:
        return np.full(rays.shape[:-1], GREY)
    if cond in (1, 2, 3):
        az = azimuth(rays) / WAVELENGTH_DEG
        tt = 0.0 if cond == 3 else t
        sgn = {1: +1.0, 2: -1.0, 3: 0.0}[cond]
        return GREY + 0.5 * CONTRAST * np.sin(2 * np.pi * (az + sgn * TF_HZ * tt))
    if cond in (4, 5, 6, 7, 8, 11):
        c = {4: 4, 5: 5, 6: 6, 7: 4, 8: 5, 11: 6}[cond]
        a = np.radians(LOOM_AZ[c])
        ctr = np.array([np.cos(a), np.sin(a), 0.0])
        half = np.radians(size_at(cond, t)) / 2
        inside = rays @ ctr > np.cos(half)
        return np.where(inside, LOOM_DISC, GREY)
    if cond == 9:
        dr = np.maximum(np.hypot(rays[..., 1], rays[..., 2]), 1e-3)
        x_hit = rays[..., 0] * FLOW_RADIUS / dr
        return GREY + 0.5 * CONTRAST * np.sin(2 * np.pi * (x_hit + FLOW_SPEED * t) / FLOW_PERIOD)
    raise ValueError(cond)


def encode(lum, retina):
    """Luminance (2, 512, 450) -> FlyGym-format readout (2, 721, 2), encoded as visual_input.grating_frames."""
    out = []
    for e in range(2):
        img = (np.repeat(np.clip(lum[e], 0, 1)[..., None], 3, axis=2) * 255).astype(np.uint8)
        out.append(retina.raw_image_to_hex_pxls(img))
    return np.stack(out)


def step_frames(cond, k, rays, retina):
    """The V.VIS_SUBFRAMES readouts of decision step k (0-based) of the 60-step protocol."""
    fr = []
    for j in range(V.VIS_SUBFRAMES):
        if k < N_GREY_STEPS:
            t = None
        else:
            t = ((k - N_GREY_STEPS) * V.VIS_SUBFRAMES + j + 1) * V.FLYVIS_DT
        fr.append(encode(luminance(cond, t, rays), retina))
    return fr
