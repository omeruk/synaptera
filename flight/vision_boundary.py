"""--vision-boundary (SPEC_SENSORY_INPUTS.md §2.1, Stage B): FlyVis -> FlyWire boundary layer.

Which neurons (fixed before any behaviour, scripts/make_vision_boundary.py -> data/):
  A FlyVis-matched FlyWire type is driven when >= BOUNDARY_FRAC of its outgoing synapses
  (Connectivity_783.parquet, synapse-count weighted) go to neurons that are NOT of a
  FlyVis-matched type (VPNs, LPTCs, central brain, optic-lobe types FlyVis lacks).
  Cell types: Codex v783 consolidated_cell_types (primary_type). Result: 32 FlyWire
  types, 34,121 neurons (data/vision_boundary_783.csv). These replace the T4/T5 group;
  the other FlyVis types are not driven (display layer only, below).

Column of every driven neuron:
  * from data/column_assignment.csv.gz when present (25,096 neurons);
  * else (VARSAYIM) the column nearest to the synapse-weighted mean column of its columnar
    partners (pre + post, same hemisphere, column_assignment, parquet counts). Chosen over the
    SPEC's arbor-centroid regression by validation on the columnar driven neurons, before any
    behaviour (hidden own column: partner mean <= 1 column for 97 %, centroid 22 %;
    data/vision_boundary_types.json);
  * no columnar partner -> arbor centroid (data/neuron_arbor_centroids.npz `xyz`): per
    hemisphere and neuropil a cubic surface (p, q) -> centroid fitted on a columnar reference
    type (ME: Mi1, LO: Tm1, LOP: T4a-d); nearest predicted column. Neuropil = dominant
    neuropil (data/neuron_neuropil.npz); not ME/LO/LOP -> the nearest of the three surfaces.
  Wide-field types (Tm5, TmY, ...) get only their own centre column.
  (p, q) -> FlyVis (u, v) as for T4/T5 (visual_input.map_columns).

Graded activity -> rate (generalisation of the T4/T5 transduction, VARSAYIM):
  r = clip(R_MAX * relu(a - a0[node]) / a_ref[FlyVis type], 0, R_CLIP), R_MAX/R_CLIP as T4/T5.
  a0: grey steady state of every FlyVis node. a_ref: the type's largest mean positive response
  to a fixed standard stimulus set (grating in the 4 T4/T5 preferred directions, full-field ON
  step 0.5->0.8, OFF step 0.5->0.2), 250-1000 ms, central columns (hex radius <= R_CENTRAL),
  both eyes, activity averaged over VIS_SUBFRAMES as at run time. Measured once
  (scripts/make_visual_transduction.py -> data/visual_transduction.json); never tuned on behaviour.
  Many of these types are non-spiking in the fly; the Poisson rate is a stand-in.
  a_ref < A_REF_MIN (fixed before any run): the type stays in the group, rate held at 0 Hz.

Display layer (not an input): FlyVis activity a - a0 of every node of the NOT driven FlyVis
types, per decision step, float16, streamed to the HDF5 (/flyvis/activity).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch  # noqa: F401  (FlyVis)

from flight import groups as G
from flight import visual_input as V

DATA_DIR = G.DATA_DIR
PATH_TABLE = DATA_DIR / "vision_boundary_783.csv"
PATH_TYPES = DATA_DIR / "vision_boundary_types.json"
PATH_TRANSDUCTION = DATA_DIR / "visual_transduction.json"
PATH_CODEX_TYPES = Path.home() / "Downloads" / "consolidated_cell_types.csv.gz"

BOUNDARY_FRAC = 0.5
A_REF_MIN = 1e-3         # a_ref below this = no measurable positive response to the standard set:
                         # the type is "unresponsive" and its rate is held at 0 Hz (Tm4: 1.1e-5)
R_CENTRAL = 10           # hex radius of the "central columns" for a_ref (FlyVis extent 15; rim a0 differs)
CENTROID_REF = {"ME": ("Mi1",), "LO": ("Tm1",), "LOP": ("T4a", "T4b", "T4c", "T4d")}
SURFACE_DEG = 3
STEP_ON, STEP_OFF = 0.8, 0.2    # full-field steps from grey 0.5

# FlyVis type -> FlyWire primary_type(s) (Codex v783). Not in v783: Mi3, Mi11, Mi12, Tm5Y, Tm28,
# Tm30, TmY13, TmY18. R1..R6 = R1-6, CT1(Lo1)/CT1(M10) = compartments of CT1, Am = Am1.
FLYVIS_TO_FLYWIRE = {**{f"R{k}": ("R1-6",) for k in range(1, 7)}, "CT1(Lo1)": ("CT1",), "CT1(M10)": ("CT1",),
                     "TmY9": ("TmY9q", "TmY9q__perp"), "Am": ("Am1",)}


def flywire_names(fv_type):
    return FLYVIS_TO_FLYWIRE.get(fv_type, (fv_type,))


def flywire_to_flyvis(fv_types, present):
    """{FlyWire type: FlyVis type} for the FlyVis types whose FlyWire name exists (one FlyVis
    type per FlyWire type: R1-6 -> R1, CT1 -> CT1(Lo1), only used for the matched-set test)."""
    out = {}
    for t in fv_types:
        for n in flywire_names(t):
            if n in present and n not in out:
                out[n] = t
    return out


def hex_dist_flywire(dp, dq):
    """Hex distance in FlyWire (p, q) (neighbours +-(1,0), +-(0,1), +-(1,1))."""
    dp, dq = np.asarray(dp), np.asarray(dq)
    return np.where(dp * dq >= 0, np.maximum(np.abs(dp), np.abs(dq)), np.abs(dp) + np.abs(dq))


def hex_radius_flyvis(u, v):
    u, v = np.asarray(u), np.asarray(v)
    return (np.abs(u) + np.abs(v) + np.abs(u + v)) // 2


# ── selection (scripts/make_vision_boundary.py) ─────────────────────────────
def load_codex_types(root_ids, path=PATH_CODEX_TYPES):
    ct = pd.read_csv(path).set_index("root_id")["primary_type"]
    return ct.reindex(root_ids).to_numpy(dtype=object)


def boundary_fractions(cell_type, fv_types, path_con=G.PATH_CON):
    """Per FlyVis-matched FlyWire type: n neurons, outgoing synapses, share going to neurons
    that are not of a FlyVis-matched type. cell_type: per Completeness row."""
    present = set(pd.Series(cell_type).dropna().unique())
    matched = flywire_to_flyvis(fv_types, present)
    is_fv = pd.Series(cell_type).isin(list(matched)).to_numpy()
    con = pd.read_parquet(path_con, columns=["Presynaptic_Index", "Postsynaptic_Index", "Connectivity"])
    pre, post = con["Presynaptic_Index"].to_numpy(), con["Postsynaptic_Index"].to_numpy()
    w = con["Connectivity"].to_numpy().astype(float)
    del con
    m = is_fv[pre]
    df = pd.DataFrame(dict(t=cell_type[pre[m]], out=~is_fv[post[m]], w=w[m]))
    tot = df.groupby("t")["w"].sum()
    outw = df[df["out"]].groupby("t")["w"].sum().reindex(tot.index).fillna(0.0)
    n = pd.Series(cell_type[is_fv]).value_counts()
    res = pd.DataFrame(dict(n=n.reindex(tot.index).astype(int), syn_out=tot, frac_out_nonflyvis=outw / tot))
    res["flyvis_type"] = [matched[t] for t in res.index]
    res["driven"] = res["frac_out_nonflyvis"] >= BOUNDARY_FRAC
    missing = [t for t in fv_types if not any(n in present for n in flywire_names(t))]
    return res.sort_values("frac_out_nonflyvis", ascending=False), missing


def _poly(pq, deg=SURFACE_DEG):
    p, q = pq[:, 0].astype(float), pq[:, 1].astype(float)
    return np.stack([p ** i * q ** j for i in range(deg + 1) for j in range(deg + 1 - i)], axis=1)


class ColumnSurfaces:
    """Per hemisphere x neuropil: cubic (p, q) -> arbor centroid fitted on the reference type."""

    def __init__(self, col, xyz, r2i):
        self.fit = {}
        for hemi in ("left", "right"):
            for npl, types in CENTROID_REF.items():
                c = col[(col["hemisphere"] == hemi) & col["type"].isin(types) & col["root_id"].isin(r2i)]
                X = xyz[c["root_id"].map(r2i).to_numpy()].astype(float)
                pq = c[["p", "q"]].to_numpy()
                coef, *_ = np.linalg.lstsq(_poly(pq), X, rcond=None)
                cols = np.unique(pq, axis=0)
                pred = _poly(cols) @ coef
                resid = np.linalg.norm(_poly(pq) @ coef - X, axis=1)
                self.fit[(hemi, npl)] = dict(cols=cols, pred=pred, resid_med_um=float(np.median(resid)) / 1e3,
                                             n_ref=len(c))

    def assign(self, hemi, npl, xyz):
        """Nearest reference column. npl None -> nearest over the three neuropils.
        Returns (p, q, distance um, neuropil used)."""
        cand = [npl] if npl in CENTROID_REF else list(CENTROID_REF)
        best = None
        for n in cand:
            f = self.fit[(hemi, n)]
            d = np.linalg.norm(f["pred"] - xyz[None, :], axis=1)
            j = int(d.argmin())
            if best is None or d[j] < best[2]:
                best = (int(f["cols"][j, 0]), int(f["cols"][j, 1]), float(d[j]) / 1e3, n)
        return best


def build_table(root_ids, cell_type, driven_types, path_ann=G.PATH_ANN):
    """One row per driven neuron: root_id, fw_type, flyvis_type, hemisphere, p, q, col_source,
    centroid_dist_um, u, v, extent_dist. Also returns the validation of the centroid rule on the
    columnar neurons of the driven non-reference types."""
    r2i = G.root_to_index(root_ids)
    fw2fv = {t: ft for t, ft in driven_types.items()}
    idx = np.flatnonzero(pd.Series(cell_type).isin(list(fw2fv)).to_numpy())
    col = pd.read_csv(G.PATH_COLUMNS)
    col = col[col["root_id"].isin(r2i)]
    cc = col.set_index("root_id")
    cen = np.load(DATA_DIR / "neuron_arbor_centroids.npz")
    assert np.array_equal(cen["root_id"], root_ids)
    xyz = cen["xyz"]
    npz = np.load(DATA_DIR / "neuron_neuropil.npz")
    dom = npz["neuropils"][npz["dominant"]]
    ann = pd.read_csv(path_ann, sep="\t", usecols=["root_id", "side"], low_memory=False).set_index("root_id")["side"]
    surf = ColumnSurfaces(col, xyz, r2i)
    pm_cols, pm_w, pm_side = partner_columns(root_ids, idx, col, ann)

    rows = []
    for i in idx:
        r = int(root_ids[i])
        t = cell_type[i]
        if r in cc.index:
            hemi, p, q = cc.at[r, "hemisphere"], int(cc.at[r, "p"]), int(cc.at[r, "q"])
            src, dist = "column_assignment", 0.0
        elif pm_w[i] > 0:
            hemi, (p, q), dist = pm_side[i], pm_cols[i], 0.0
            src = "partner_mean"
        else:
            hemi = pm_side[i]
            p, q, dist, npl = surf.assign(hemi, dom[i] if dom[i] in CENTROID_REF else None, xyz[i])
            src = f"centroid_{npl}"
        rows.append(dict(root_id=r, fw_type=t, flyvis_type=fw2fv[t], hemisphere=hemi, p=p, q=q, col_source=src,
                         centroid_dist_um=dist))
    tab = pd.DataFrame(rows)
    u, v, d = V.map_columns(tab["p"].to_numpy(), tab["q"].to_numpy())
    tab["u"], tab["v"], tab["extent_dist"] = u, v, d

    # validation on columnar neurons of driven types that are not centroid reference types: both
    # rules with the neuron's own column hidden (a neuron is never its own partner)
    ref_types = {t for ts in CENTROID_REF.values() for t in ts}
    val = []
    for i in idx:
        r = int(root_ids[i])
        if r not in cc.index or cell_type[i] in ref_types:
            continue
        hemi, p0, q0 = cc.at[r, "hemisphere"], cc.at[r, "p"], cc.at[r, "q"]
        p, q, _, _ = surf.assign(hemi, dom[i] if dom[i] in CENTROID_REF else None, xyz[i])
        pp, pq = pm_cols[i] if pm_w[i] > 0 else (10 ** 6, 10 ** 6)
        val.append(dict(fw_type=cell_type[i], centroid=int(hex_dist_flywire(p - p0, q - q0)),
                        partner_mean=int(hex_dist_flywire(pp - p0, pq - q0))))
    val = pd.DataFrame(val)

    def st(d):
        return dict(exact=float((d == 0).mean()), le1=float((d <= 1).mean()), le2=float((d <= 2).mean()),
                    median=float(d.median()), per_type_le1={t: float((g <= 1).mean()) for t, g in d.groupby(val["fw_type"])})
    vstats = dict(n=len(val), centroid=st(val["centroid"]), partner_mean=st(val["partner_mean"]),
                  surfaces={f"{h}/{n}": dict(n_ref=f["n_ref"], resid_med_um=f["resid_med_um"])
                            for (h, n), f in surf.fit.items()})
    return tab, vstats


def partner_columns(root_ids, idx, col, ann, path_con=G.PATH_CON):
    """For the neurons idx: nearest column (same hemisphere) to the synapse-weighted mean column
    (FlyWire cartesian) of their columnar partners, pre and post. Returns ({i: (p, q)},
    {i: summed partner synapses}, {i: hemisphere}); hemisphere = column_assignment, else
    annotations side."""
    r2i = G.root_to_index(root_ids)
    n = len(root_ids)
    ci = col["root_id"].map(r2i).to_numpy()
    h = np.full(n, -1)
    h[ci] = (col["hemisphere"] == "right").to_numpy(int)
    side = pd.Series(ann.reindex(root_ids).to_numpy()).map({"left": 0, "right": 1}).fillna(-1).to_numpy(int)
    side[ci] = h[ci]
    if (side[idx] < 0).any():
        raise ValueError("driven neuron without side")
    xy = np.full((n, 2), np.nan)
    xy[ci] = V.flywire_cart(col["p"].to_numpy(), col["q"].to_numpy())
    ok = h >= 0
    isb = np.zeros(n, bool)
    isb[idx] = True
    con = pd.read_parquet(path_con, columns=["Presynaptic_Index", "Postsynaptic_Index", "Connectivity"])
    pre, post = con["Presynaptic_Index"].to_numpy(), con["Postsynaptic_Index"].to_numpy()
    w = con["Connectivity"].to_numpy().astype(float)
    del con
    acc, ws = np.zeros((n, 2)), np.zeros(n)
    for a, b in ((pre, post), (post, pre)):
        m = isb[a] & ok[b] & (h[b] == side[a])
        np.add.at(acc, a[m], xy[b[m]] * w[m, None])
        np.add.at(ws, a[m], w[m])
    out = {}
    for hh, name in ((0, "left"), (1, "right")):
        cols = np.unique(col.loc[col["hemisphere"] == name, ["p", "q"]].to_numpy(), axis=0)
        cxy = V.flywire_cart(cols[:, 0], cols[:, 1])
        sel = idx[(side[idx] == hh) & (ws[idx] > 0)]
        mxy = acc[sel] / ws[sel, None]
        j = ((mxy[:, None, :] - cxy[None]) ** 2).sum(-1).argmin(1)
        out.update({int(i): (int(cols[k, 0]), int(cols[k, 1])) for i, k in zip(sel, j)})
    return out, ws, {int(i): ("left", "right")[side[i]] for i in idx}


def load_table(path=PATH_TABLE):
    return pd.read_csv(path)


def load_types(path=PATH_TYPES):
    with open(path) as f:
        return json.load(f)


# ── transduction (scripts/make_visual_transduction.py) ──────────────────────
def standard_stimuli():
    """name -> callable(n) yielding FlyVis-ordered frames (2, 721) (both eyes, canonical frame)."""
    from flygym.examples.vision.vision_network import RetinaMapper
    rm = RetinaMapper()

    def grating(direction):
        def gen(n):
            for fr in V.grating_frames(direction, n):
                g = fr.max(axis=2)
                yield np.stack([rm.flygym_to_flyvis(g[0]), rm.flygym_to_flyvis(g[1])]).astype(np.float32)
        return gen

    def step(level):
        def gen(n):
            for _ in range(n):
                yield np.full((2, 721), level, np.float32)
        return gen

    st = {f"grating_{d}": grating(v) for d, v in V.PD_IMAGE.items()}
    st["on_step"] = step(STEP_ON)
    st["off_step"] = step(STEP_OFF)
    return st


def calibrate(net=None, types=None, t_stim=1.0, t_skip=0.25):
    """a0 of every FlyVis node (grey steady state) and a_ref per FlyVis type (see module doc)."""
    net = net if net is not None else V.load_flyvis_net()
    nodes = net.connectome.nodes
    ntype = np.array(nodes.type[:]).astype(str)
    nu, nv = np.asarray(nodes.u[:]), np.asarray(nodes.v[:])
    central = hex_radius_flyvis(nu, nv) <= R_CENTRAL
    types = types or list(dict.fromkeys(ntype))

    def fwd(frame, state):
        with torch.no_grad():
            net.stimulus.zero(2, 1)
            net.stimulus.add_input(torch.as_tensor(frame, dtype=torch.float32).reshape(2, 1, 1, -1))
            return net.forward(net.stimulus(), V.FLYVIS_DT, state=state, as_states=True)[-1]

    grey = np.full((2, 721), 0.5, np.float32)
    state = None
    for _ in range(int(round(V.GREY_S / V.FLYVIS_DT))):
        state = fwd(grey, state)
    act0 = state.nodes.activity.numpy()
    assert np.allclose(act0[0], act0[1])
    a0 = act0[0].astype(float)
    state0 = state
    sel = {t: np.flatnonzero((ntype == t) & central) for t in types}
    n = int(round(t_stim / V.FLYVIS_DT))
    k0 = int(round(t_skip / V.FLYVIS_DT))
    resp = {}
    for name, gen in standard_stimuli().items():
        state = state0
        acc = {t: [] for t in types}
        sub = 0.0
        for k, fr in enumerate(gen(n)):
            state = fwd(fr, state)
            sub = sub + state.nodes.activity.numpy()
            if (k + 1) % V.VIS_SUBFRAMES == 0:
                if k >= k0:
                    a = sub / V.VIS_SUBFRAMES
                    for t in types:
                        acc[t].append(float(np.maximum(a[:, sel[t]] - a0[sel[t]], 0).mean()))
                sub = 0.0
        resp[name] = {t: float(np.mean(x)) for t, x in acc.items()}
    a_ref = {t: max(resp[s][t] for s in resp) for t in types}
    best = {t: max(resp, key=lambda s: resp[s][t]) for t in types}
    return dict(a0=a0.tolist(), node_type=ntype.tolist(), a_ref=a_ref, a_ref_stimulus=best, responses=resp,
                model=V.FLYVIS_MODEL, dt=V.FLYVIS_DT, grey_s=V.GREY_S, r_central=R_CENTRAL,
                window_s=[t_skip, t_stim], stimuli=dict(grating=dict(period_px=V.GRATING_PERIOD_PX,
                                                                     tf_hz=V.GRATING_TF_HZ,
                                                                     contrast=V.GRATING_CONTRAST,
                                                                     pd_image=V.PD_IMAGE),
                                                        on_step=[0.5, STEP_ON], off_step=[0.5, STEP_OFF]),
                r_max=V.R_MAX, r_clip=V.R_CLIP)


def load_transduction(path=PATH_TRANSDUCTION):
    with open(path) as f:
        return json.load(f)


# ── groups ──────────────────────────────────────────────────────────────────
def boundary_groups(root_ids, path=PATH_TABLE):
    """{"vbnd_L", "vbnd_R"}: sorted Completeness row indices (root_id map) of the driven neurons."""
    r2i = G.root_to_index(root_ids)
    tab = load_table(path)
    return {f"vbnd_{h[0].upper()}": G._idx(tab.loc[tab["hemisphere"] == h, "root_id"], r2i)
            for h in ("left", "right")}


# ── run time ────────────────────────────────────────────────────────────────
def node_of(lookup, ntype, nu, nv, t, u, v):
    """FlyVis node of type t at column (u, v); types on a sparse FlyVis lattice (Lawf1/Lawf2: 123
    of 721 columns) take the type's nearest node."""
    k = lookup.get((t, int(u), int(v)))
    if k is not None:
        return k
    cand = np.flatnonzero(ntype == t)
    d = ((V.axial_to_cart(nu[cand], nv[cand]) - V.axial_to_cart([u], [v])) ** 2).sum(1)
    return int(cand[d.argmin()])


class BoundaryEyes(V.FlyVisEyes):
    """Both eyes through FlyVis; per-neuron rates for the boundary layer (vbnd_L/R order) and the
    display-layer activity of the not-driven FlyVis types. loom (T5a/b) as FlyVisEyes."""

    def __init__(self, vbnd_index, transduction=None, table=None, verbose=True):
        self._init_flyvis()
        tab = (table if table is not None else load_table()).copy()
        rid = G.load_root_ids()
        r2i = G.root_to_index(rid)
        tab = tab[tab["root_id"].isin(r2i)]
        tab["idx"] = tab["root_id"].map(r2i)
        nodes = self.net.connectome.nodes
        ntype = np.array(nodes.type[:]).astype(str)
        nu, nv = np.asarray(nodes.u[:]), np.asarray(nodes.v[:])
        lookup = {(t, int(a), int(b)): i for i, (t, a, b) in enumerate(zip(ntype, nu, nv))}
        self.fw_types = tuple(sorted(tab["fw_type"].unique(), key=lambda t: (not t.startswith(("T4", "T5")), t)))
        tr = transduction if transduction is not None else load_transduction()
        a0_all = np.asarray(tr["a0"], float)
        assert len(a0_all) == len(ntype) and list(tr["node_type"]) == ntype.tolist()
        self.a0_all = a0_all
        self.node, self.tcode, self.a0, self.aref, self.n_outside = {}, {}, {}, {}, {}
        self.t45_mask, self.t45_code = {}, {}
        for s, sd in (("L", "left"), ("R", "right")):
            c = tab[tab["hemisphere"] == sd].set_index("idx").loc[np.asarray(vbnd_index[s])]
            self.node[s] = np.array([node_of(lookup, ntype, nu, nv, t, a, b)
                                     for t, a, b in zip(c["flyvis_type"], c["u"], c["v"])])
            self.tcode[s] = np.array([self.fw_types.index(t) for t in c["fw_type"]])
            self.a0[s] = a0_all[self.node[s]]
            self.aref[s] = np.array([tr["a_ref"][t] for t in c["flyvis_type"]])
            self.aref[s] = np.where(self.aref[s] < A_REF_MIN, np.inf, self.aref[s])     # unresponsive -> 0 Hz
            self.n_outside[s] = int((c["extent_dist"] > 0.5).sum())
            m = c["fw_type"].isin(G.T45_TYPES).to_numpy()
            self.t45_mask[s] = m
            self.t45_code[s] = np.array([G.T45_TYPES.index(t) for t in c["fw_type"][m]])
        self.unresponsive = tuple(sorted({t for t in tab["fw_type"]
                                          if tr["a_ref"][tab.loc[tab["fw_type"] == t, "flyvis_type"].iloc[0]] < A_REF_MIN}))
        driven_fv = set(tab["flyvis_type"])
        self.display_types = tuple(t for t in dict.fromkeys(ntype) if t not in driven_fv)
        self.display_nodes = np.flatnonzero(np.isin(ntype, self.display_types))
        self.display_type = ntype[self.display_nodes]
        self.display_u, self.display_v = nu[self.display_nodes], nv[self.display_nodes]
        # FlyWire neurons drawn by the display layer: columnar neurons (column_assignment) whose type is
        # a display FlyVis type with a unique FlyWire name (R1-6, CT1 skipped: several FlyVis nodes per neuron)
        col = pd.read_csv(G.PATH_COLUMNS)
        col = col[col["root_id"].isin(r2i)]
        fw2disp = {flywire_names(t)[0]: t for t in self.display_types
                   if len(flywire_names(t)) == 1 and flywire_names(t)[0] not in ("R1-6", "CT1")}
        col = col[col["type"].isin(list(fw2disp))]
        u, v, _ = V.map_columns(col["p"].to_numpy(), col["q"].to_numpy())
        pos = {n: k for k, n in enumerate(self.display_nodes)}
        self.display_fw = dict(idx=col["root_id"].map(r2i).to_numpy(np.int32),
                               eye=(col["hemisphere"] == "right").to_numpy(np.int8),
                               pos=np.array([pos[lookup[(fw2disp[t], int(a), int(b))]]
                                             for t, a, b in zip(col["type"], u, v)], np.int32))
        self.display = None
        if verbose:
            print(f"  FlyVis -> FlyWire boundary layer: {len(self.fw_types)} types, L {len(self.node['L'])}, "
                  f"R {len(self.node['R'])} neurons; outside FlyVis extent: L {self.n_outside['L']}, "
                  f"R {self.n_outside['R']}; display layer {len(self.display_types)} FlyVis types, "
                  f"{len(self.display_nodes)} nodes/eye; unresponsive (0 Hz): {self.unresponsive}")
        li = self.net.stimulus.layer_index
        self.t5a, self.t5b = li["T5a"], li["T5b"]
        self.state = None
        self.reset()

    def step(self, frames):
        acc = 0.0
        for fr in frames:
            act = self._forward(self.to_flyvis(fr))
            acc = acc + act
        full = acc / len(frames)
        a = {"L": full[0, self.node["L"]], "R": full[1, self.node["R"]]}
        self.display = (full[:, self.display_nodes] - self.a0_all[self.display_nodes]).astype(np.float16)
        loom = tuple(float(np.abs(act[e, self.t5a]).mean() + np.abs(act[e, self.t5b]).mean()) for e in (0, 1))
        return a, loom

    def rates(self, a):
        return {s: np.clip(V.R_MAX * np.maximum(a[s] - self.a0[s], 0.0) / self.aref[s], 0.0, V.R_CLIP)
                for s in ("L", "R")}

    def type_means(self, r):
        """(2, 32) mean rate per eye x FlyWire boundary type (self.fw_types order)."""
        return np.array([[r[s][self.tcode[s] == k].mean() for k in range(len(self.fw_types))] for s in ("L", "R")])

    def t45_view(self, r):
        """T4/T5 members only: {L, R} rates and the (2, 8) per-subtype means (t45_* recording)."""
        v = {s: r[s][self.t45_mask[s]] for s in ("L", "R")}
        tm = np.array([[v[s][self.t45_code[s] == k].mean() for k in range(len(G.T45_TYPES))] for s in ("L", "R")])
        return v, tm


class DisplayWriter:
    """Streams /flyvis/activity (steps x 2 eyes x display nodes, float16) into the run's HDF5,
    one chunk per decision step; nothing accumulates in RAM. Close before write_h5(mode="a")."""

    def __init__(self, path, eyes):
        import h5py
        self.f = h5py.File(path, "w")
        g = self.f.create_group("flyvis")
        nd = len(eyes.display_nodes)
        self.ds = g.create_dataset("activity", shape=(0, 2, nd), maxshape=(None, 2, nd), dtype=np.float16,
                                   chunks=(1, 2, nd), compression="gzip", compression_opts=1)
        self.ds.attrs["content"] = ("FlyVis node activity a - a0 (grey steady state) of the NOT driven FlyVis types, "
                                    "decision-step mean; display only, never a simulation input")
        self.ds.attrs["axes"] = "step_row, eye (0 = left, 1 = right; right eye image mirrored), node"
        g.create_dataset("node_index", data=eyes.display_nodes.astype(np.int32))
        g.create_dataset("node_type", data=np.array(eyes.display_type, dtype="S16"))
        g.create_dataset("node_u", data=eyes.display_u.astype(np.int16))
        g.create_dataset("node_v", data=eyes.display_v.astype(np.int16))
        m = g.create_group("flywire_map")
        m.attrs["content"] = ("FlyWire neuron (global index) -> eye and column of /flyvis/activity (display "
                              "position); columnar neurons of the display types (column_assignment)")
        for k, val in eyes.display_fw.items():
            m.create_dataset(k, data=val)
        self.steps = []

    def add(self, step, display):
        n = self.ds.shape[0]
        self.ds.resize(n + 1, axis=0)
        self.ds[n] = display
        self.steps.append(int(step))

    def close(self):
        self.f["flyvis"].create_dataset("step_idx", data=np.asarray(self.steps, np.int32))
        self.f["flyvis"]["step_idx"].attrs["content"] = "decision step of each row (negative = perch / input cut)"
        self.f.close()
