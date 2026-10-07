"""FlyVis -> FlyWire visual input: per-neuron Poisson rates for T4a-d / T5a-d
(SPEC_BRAIN_CONTROL.md R4, Step 0).

Pipeline per 25 ms decision step:
  FlyGym compound-eye frames (VIS_SUBFRAMES per step, (2, 721, 2) each)
  -> FlyVis connectome-constrained network (Lappalainen et al. 2024, flow/0000/000),
     both eyes as a batch of 2, dt = 25 ms / VIS_SUBFRAMES
  -> activity of the T4/T5 node in each FlyVis column, averaged over the subframes
  -> r = R_MAX * relu(a - a0[type]) / a_ref[type], clipped to R_CLIP
  -> PoissonGroup.rates of the FlyWire T4/T5 neuron assigned to that column.

Column alignment (anatomical, no behaviour involved):
  FlyWire columns (Matsliah et al. 2024 / Zhao et al. 2024, data/column_assignment.csv.gz)
  use hex coordinates (p, q) with neighbours +-(1,0), +-(0,1), +-(1,1); axial
  (a, b) = (p, -q). FlyVis uses axial (u, v) with neighbours +-(1,0), +-(0,1), +-(1,-1).
  The lattice map FlyWire -> FlyVis is the point-group operation (rotation by
  k*60 deg, optional reflection) that best aligns the synapse-weighted input
  offsets (Mi4, Mi9, Tm9, ... -> T4/T5 subtype) of the two connectomes
  (fit_alignment). Result: rotation by +60 deg, no reflection, the same for both
  hemispheres (FlyWire p, q are mirror-consistent). FlyWire columns outside the
  FlyVis extent (radius 15) take the nearest FlyVis column.

Eye convention (measured, tests/flight/test_visual_input.py):
  FlyVis tuning (flyvis.analysis: T4a 180, T4b 0, T4c 90, T4d 270 deg) with a
  FlyGym image passed through RetinaMapper: image rightward -> T4b, upward -> T4c.
  The FlyGym left-eye image has anterior on the right (rightward = back-to-front)
  and dorsal up, i.e. it is already in the FlyVis eye frame. The right-eye image
  has anterior on the left, so it is mirrored horizontally (R_EYE_FLIP) before
  FlyVis; then front-to-back motion drives T4a/T5a in both eyes.

Transduction constants (data/t45_transduction.json) come once from a grey screen
and a standard grating (calibrate_transduction): a0 per FlyVis node (its grey
steady-state activity; FlyVis columns differ, especially at the lattice edge),
a_ref per subtype; R_MAX / R_CLIP are
fixed ASSUMPTIONS (VARSAYIM), not tuned on behaviour.
"""
import json
from pathlib import Path

import numpy as np
import torch

from flight import groups as G

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PATH_TRANSDUCTION = DATA_DIR / "t45_transduction.json"

FLYVIS_MODEL = "flow/0000/000"
FLYVIS_EXTENT = 15
ALIGN_ROT = 1            # FlyWire -> FlyVis: rotation by ALIGN_ROT * 60 deg (fit_alignment)
ALIGN_REFLECT = False
R_EYE_FLIP = True        # mirror the right-eye image horizontally (see module doc)

DECISION_S = 0.025
VIS_SUBFRAMES = 2        # renders per decision step -> FlyVis dt 12.5 ms (FlyVis warns above 20 ms)
FLYVIS_DT = DECISION_S / VIS_SUBFRAMES
GREY_S = 1.0             # grey steady state before use

# Transduction (VARSAYIM): the reference response a_ref maps to R_MAX. 50 Hz is the
# per-neuron T4/T5 rate that gave clean lateral DN codes in R3 (yaw optic flow).
R_MAX = 50.0
R_CLIP = 150.0
# Standard grating for a_ref (FlyGym image px; 157 deg / 512 px ~ 0.31 deg/px)
GRATING_PERIOD_PX = 64.0     # ~20 deg
GRATING_TF_HZ = 2.0          # ~40 deg/s
GRATING_CONTRAST = 0.8       # 0.1 .. 0.9
# Preferred direction of each subtype as a FlyGym image direction (x right, y down)
# in the FlyVis eye frame: front-to-back = leftward, up = -y.
PD_IMAGE = {"a": (-1, 0), "b": (1, 0), "c": (0, -1), "d": (0, 1)}

E1 = np.array([1.0, 0.0])
E2 = np.array([0.5, np.sqrt(3) / 2])


def axial_to_cart(a, b):
    return np.outer(np.asarray(a, float), E1) + np.outer(np.asarray(b, float), E2)


def flywire_cart(p, q):
    return axial_to_cart(p, -np.asarray(q))


def lattice_op(rot, reflect):
    th = rot * np.pi / 3
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    return R @ (np.diag([1.0, -1.0]) if reflect else np.eye(2))


def flyvis_hex(extent=FLYVIS_EXTENT):
    from flyvis.utils.hex_utils import get_hex_coords
    return get_hex_coords(extent)


def map_columns(p, q, rot=ALIGN_ROT, reflect=ALIGN_REFLECT, extent=FLYVIS_EXTENT):
    """FlyWire (p, q) -> nearest FlyVis (u, v). Returns u, v and the distance in
    column spacings (0 inside the FlyVis extent)."""
    xy = flywire_cart(p, q) @ lattice_op(rot, reflect).T
    u, v = flyvis_hex(extent)
    fv = axial_to_cart(u, v)
    d2 = ((xy[:, None, :] - fv[None, :, :]) ** 2).sum(-1)
    j = d2.argmin(1)
    return u[j], v[j], np.sqrt(d2[np.arange(len(j)), j])


def fit_alignment(path_con=G.PATH_CON, path_col=G.PATH_COLUMNS, flyvis_edges=None):
    """Score every hex point-group operation FlyWire -> FlyVis per hemisphere.

    For each (T4/T5 subtype, columnar input type) pair: synapse-weighted mean
    column offset input - target, in both connectomes (FlyVis: edges onto the
    central column). Score = weighted mean dot product after the operation.
    Returns {hemisphere: [(score, rot, reflect), ...] best first} and the
    per-pair vectors of the best operation."""
    import pandas as pd
    col = pd.read_csv(path_col).set_index("root_id")
    con = pd.read_parquet(path_con, columns=["Presynaptic_ID", "Postsynaptic_ID", "Connectivity"])
    con = con[con["Presynaptic_ID"].isin(col.index) & con["Postsynaptic_ID"].isin(col.index)]
    pre, post = col.loc[con["Presynaptic_ID"]], col.loc[con["Postsynaptic_ID"]]
    e = pd.DataFrame(dict(src=pre["type"].to_numpy(), tgt=post["type"].to_numpy(),
                          hemi=post["hemisphere"].to_numpy(), same=pre["hemisphere"].to_numpy() == post["hemisphere"].to_numpy(),
                          dp=pre["p"].to_numpy() - post["p"].to_numpy(), dq=pre["q"].to_numpy() - post["q"].to_numpy(),
                          w=con["Connectivity"].to_numpy()))
    e = e[e["same"] & e["tgt"].isin(G.T45_TYPES)]
    if flyvis_edges is None:
        flyvis_edges = load_flyvis_net().connectome.edges
    E = flyvis_edges
    fv = pd.DataFrame(dict(src=E.source_type[:].astype(str), tgt=E.target_type[:].astype(str), du=E.du[:],
                           dv=E.dv[:], w=E.n_syn[:], tu=E.target_u[:], tv=E.target_v[:]))
    fv = fv[(fv["tu"] == 0) & (fv["tv"] == 0) & fv["tgt"].isin(G.T45_TYPES)]
    ref = {}
    for (t, s), g in fv.groupby(["tgt", "src"]):
        ref[(t, s)] = ((axial_to_cart(g["du"], g["dv"]) * g["w"].to_numpy()[:, None]).sum(0) / g["w"].sum(),
                       float(g["w"].sum()))
    out, vecs = {}, {}
    for h in ("left", "right"):
        fw = {}
        for (t, s), g in e[e["hemi"] == h].groupby(["tgt", "src"]):
            fw[(t, s)] = (flywire_cart(g["dp"], g["dq"]) * g["w"].to_numpy()[:, None]).sum(0) / g["w"].sum()
        res = []
        for rot in range(6):
            for refl in (False, True):
                M = lattice_op(rot, refl)
                keys = [k for k in ref if k in fw]
                sc = sum(ref[k][1] * float((M @ fw[k]) @ ref[k][0]) for k in keys) / sum(ref[k][1] for k in keys)
                res.append((sc, rot, refl))
        res.sort(reverse=True)
        out[h] = res
        M = lattice_op(res[0][1], res[0][2])
        vecs[h] = {k: (M @ fw[k], ref[k][0]) for k in ref if k in fw}
    return out, vecs


def load_flyvis_net():
    import flyvis
    from flyvis import NetworkView
    net = NetworkView(flyvis.results_dir / FLYVIS_MODEL).init_network(checkpoint="best")
    net.eval()
    for prm in net.parameters():
        prm.requires_grad = False
    return net


def load_transduction(path=PATH_TRANSDUCTION):
    with open(path) as f:
        d = json.load(f)
    return d


class FlyVisEyes:
    """Both eyes through FlyVis; per-neuron rates for the FlyWire T4/T5 input groups.

    t45_index: dict side -> global Completeness indices (sorted, = brain groups t45_L/R);
    the rate arrays returned by rates() follow that order."""

    def _init_flyvis(self):
        from flygym.examples.vision.vision_network import RetinaMapper
        from flyvis.datasets.rendering import BoxEye

        self.net = load_flyvis_net()
        self.rm = RetinaMapper()
        rc = BoxEye(extent=FLYVIS_EXTENT).receptor_centers.cpu().numpy()
        mirrored = rc * np.array([1.0, -1.0])          # negate the horizontal (column) coordinate
        self.flip_h = ((mirrored[:, None, :] - rc[None, :, :]) ** 2).sum(-1).argmin(1)
        assert len(np.unique(self.flip_h)) == len(rc)

    def __init__(self, t45_index, transduction=None, verbose=True):
        self._init_flyvis()

        # FlyVis node index of every (type, u, v)
        nodes = self.net.connectome.nodes
        ntype = np.array(nodes.type[:]).astype(str)
        nu, nv = np.asarray(nodes.u[:]), np.asarray(nodes.v[:])
        lookup = {(t, int(a), int(b)): i for i, (t, a, b) in enumerate(zip(ntype, nu, nv)) if t in G.T45_TYPES}

        # FlyWire T4/T5 -> FlyVis node, in the order of the brain input groups
        col = G.load_t45_columns()
        rid = G.load_root_ids()
        r2i = G.root_to_index(rid)
        col = col[col["root_id"].isin(r2i)].copy()
        col["idx"] = col["root_id"].map(r2i)
        u, v, dist = map_columns(col["p"].to_numpy(), col["q"].to_numpy())
        col["node"] = [lookup[(t, int(a), int(b))] for t, a, b in zip(col["type"], u, v)]
        col["dist"] = dist
        self.node, self.type_code, self.n_outside = {}, {}, {}
        for s, sd in (("L", "left"), ("R", "right")):
            c = col[col["hemisphere"] == sd].set_index("idx").loc[np.asarray(t45_index[s])]
            self.node[s] = c["node"].to_numpy()
            self.type_code[s] = np.array([G.T45_TYPES.index(t) for t in c["type"]])
            self.n_outside[s] = int((c["dist"] > 0.5).sum())
        if verbose:
            print(f"  FlyVis->FlyWire T4/T5: L {len(self.node['L'])}, R {len(self.node['R'])} neurons; "
                  f"outside FlyVis extent (nearest column): L {self.n_outside['L']}, R {self.n_outside['R']}")
        li = self.net.stimulus.layer_index
        self.t5a, self.t5b = li["T5a"], li["T5b"]

        tr = transduction if transduction is not None else load_transduction()
        a0_node = np.full(len(ntype), np.nan)
        for t in G.T45_TYPES:
            a0_node[li[t]] = tr["a0"][t]
        self.a0 = {s: a0_node[self.node[s]] for s in ("L", "R")}
        self.a_ref = np.array([tr["a_ref"][t] for t in G.T45_TYPES])
        self.state = None
        self.reset()

    # ── FlyVis ──────────────────────────────────────────────────────────────
    def _forward(self, frame):
        """frame: (2, 721) FlyVis-ordered intensities. Returns activity (2, n_nodes) numpy."""
        with torch.no_grad():
            self.net.stimulus.zero(2, 1)
            self.net.stimulus.add_input(torch.as_tensor(frame, dtype=torch.float32).reshape(2, 1, 1, -1))
            self.state = self.net.forward(self.net.stimulus(), FLYVIS_DT, state=self.state, as_states=True)[-1]
        return self.state.nodes.activity.numpy()

    def reset(self):
        self.state = None
        grey = np.full((2, 721), 0.5, np.float32)
        for _ in range(int(round(GREY_S / FLYVIS_DT))):
            self._forward(grey)

    def to_flyvis(self, vision, flip_right=R_EYE_FLIP):
        """FlyGym ommatidia readout (2, 721, 2) -> FlyVis-ordered (2, 721), right eye mirrored."""
        g = vision.max(axis=2)
        L = self.rm.flygym_to_flyvis(g[0])
        R = self.rm.flygym_to_flyvis(g[1])
        if flip_right:
            R = R[self.flip_h]
        return np.stack([L, R]).astype(np.float32)

    def step(self, frames):
        """frames: list of FlyGym vision readouts rendered during the last decision step.
        Returns (activity per T4/T5 neuron {L, R}, T5 L/R loom summary)."""
        acc = {"L": 0.0, "R": 0.0}
        for fr in frames:
            act = self._forward(self.to_flyvis(fr))
            acc["L"] = acc["L"] + act[0, self.node["L"]]
            acc["R"] = acc["R"] + act[1, self.node["R"]]
        a = {s: acc[s] / len(frames) for s in acc}
        loom = tuple(float(np.abs(act[e, self.t5a]).mean() + np.abs(act[e, self.t5b]).mean()) for e in (0, 1))
        return a, loom

    def rates(self, a):
        """Activity per neuron -> Poisson rate (Hz) per neuron."""
        out = {}
        for s in ("L", "R"):
            tc = self.type_code[s]
            out[s] = np.clip(R_MAX * np.maximum(a[s] - self.a0[s], 0.0) / self.a_ref[tc], 0.0, R_CLIP)
        return out

    def type_means(self, r):
        """(2, 8) mean rate per eye x subtype (T4a..T5d) for recording."""
        return np.array([[r[s][self.type_code[s] == k].mean() for k in range(len(G.T45_TYPES))] for s in ("L", "R")])


# ── transduction calibration (run once: scripts/make_t45_transduction.py) ───
def grating_frames(direction, n, period=GRATING_PERIOD_PX, tf=GRATING_TF_HZ, contrast=GRATING_CONTRAST,
                   dt=FLYVIS_DT):
    """Sinusoidal grating in the FlyGym image, moving along `direction`
    (x right, y down); yields FlyGym-format readouts (2, 721, 2) (same image, both eyes)."""
    from flygym.vision import Retina
    ret = Retina()
    yy, xx = np.mgrid[0:512, 0:450].astype(float)
    dx, dy = direction
    for k in range(n):
        ph = 2 * np.pi * ((xx * dx + yy * dy) / period - tf * dt * k)
        img = np.clip(0.5 + 0.5 * contrast * np.sin(ph), 0, 1)
        img = (np.repeat(img[..., None], 3, axis=2) * 255).astype(np.uint8)
        hx = ret.raw_image_to_hex_pxls(img)
        yield np.stack([hx, hx])


def calibrate_transduction(eyes=None, t_grating=1.0, t_skip=0.25):
    """a0: grey steady-state activity of every T4/T5 FlyVis node (list per subtype in
    layer_index order); a_ref: time- and column-mean of relu(a - a0) per subtype for
    the standard grating moving in the subtype's preferred direction, with the
    activity averaged over VIS_SUBFRAMES frames per decision step as at run time
    (canonical eye frame: no right-eye flip, both batch entries)."""
    net = eyes.net if eyes is not None else load_flyvis_net()
    li = net.stimulus.layer_index

    def fwd(frame, state):
        with torch.no_grad():
            net.stimulus.zero(2, 1)
            net.stimulus.add_input(torch.as_tensor(frame, dtype=torch.float32).reshape(2, 1, 1, -1))
            return net.forward(net.stimulus(), FLYVIS_DT, state=state, as_states=True)[-1]

    from flygym.examples.vision.vision_network import RetinaMapper
    rm = RetinaMapper()
    grey = np.full((2, 721), 0.5, np.float32)
    state = None
    for _ in range(int(round(GREY_S / FLYVIS_DT))):
        state = fwd(grey, state)
    act0 = state.nodes.activity.numpy()
    assert np.allclose(act0[0], act0[1])
    a0 = {t: act0[0, li[t]].astype(float) for t in G.T45_TYPES}
    state0 = state
    a_ref = {}
    n = int(round(t_grating / FLYVIS_DT))
    k0 = int(round(t_skip / FLYVIS_DT))
    for d, direction in PD_IMAGE.items():
        state = state0
        acc = {t: [] for t in G.T45_TYPES if t.endswith(d)}
        sub = 0.0
        for k, fr in enumerate(grating_frames(direction, n)):
            g = fr.max(axis=2)
            state = fwd(np.stack([rm.flygym_to_flyvis(g[0]), rm.flygym_to_flyvis(g[1])]), state)
            sub = sub + state.nodes.activity.numpy()
            if (k + 1) % VIS_SUBFRAMES == 0:
                if k >= k0:
                    for t in acc:
                        acc[t].append(np.maximum(sub[:, li[t]] / VIS_SUBFRAMES - a0[t], 0).mean())
                sub = 0.0
        for t, xs in acc.items():
            a_ref[t] = float(np.mean(xs))
    return dict(a0={t: v.tolist() for t, v in a0.items()}, a_ref=a_ref, model=FLYVIS_MODEL, dt=FLYVIS_DT, grey_s=GREY_S,
                grating=dict(period_px=GRATING_PERIOD_PX, tf_hz=GRATING_TF_HZ, contrast=GRATING_CONTRAST,
                             t=t_grating, t_skip=t_skip, pd_image=PD_IMAGE),
                r_max=R_MAX, r_clip=R_CLIP)
