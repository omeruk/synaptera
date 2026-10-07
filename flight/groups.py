"""Neuron groups for flight: annotations -> root_id -> Completeness_783.csv row index.

Every group is built through the root_id -> row mapping (never by slicing).

Input groups (brain-control Step 0, SPEC_BRAIN_CONTROL.md; Poisson-driven):
  orn_food_L/R/C  ORNs of food-odour glomeruli FOOD_GLOMERULI (Semmelhack & Wang
                  2009; Hallem & Carlson 2006), side = antenna of origin (C: side na)
  sugar           sugar GRNs: the 20 Shiu et al. 2023 LB3 neurons (left) + their
                  right homologs chosen by connectivity profile (data/sugar_grn_783.csv,
                  select_sugar_homologs)
  t45_L/R         T4a-d / T5a-d with a medulla/lobula column (data/column_assignment.csv.gz),
                  driven per neuron by FlyVis (flight/visual_input.py)
  ascending       all 1736 ANs; driven only with --asc-legacy (no anatomical basis)
Legacy input groups (walking selectors, R0-R3 diagnosis; inputs="legacy" in
FlightBrain): ascending 1736, olf_L/R/C (all 2279 ORNs), sez 408 (all GRNs),
vis_L/R (LA>ME 8025). They are still built and recorded as neuron groups.

DN readouts:
  dng02_L/R  DNg02_a..h (25)   collective wing-stroke amplitude [Namiki et al. 2022]
  steer_L/R  DNa01 + DNa02     ASSUMPTION (VARSAYIM): steering DNs from walking studies;
                               their role in flight is not established
  dnp01      giant fibre (1+1) [von Reyn et al. 2014], recorded only
  dn_L/R/C   all 1299 DNs: turn readout (walking method, baseline-subtracted)
  brain_mn   brain motor neurons (cell_class brain_motor_neuron; mostly SEZ
             proboscis/pharynx/antenna motor neurons): SEZ output rate in feeding
"""
from pathlib import Path

import numpy as np
import pandas as pd

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain_model"
PATH_COMP = BRAIN_DIR / "Completeness_783.csv"
PATH_CON = BRAIN_DIR / "Connectivity_783.parquet"
PATH_ANN = BRAIN_DIR / "flywire_annotations.tsv"
PATH_DN = BRAIN_DIR / "descending_neurons.csv"

OLFACTORY_PATTERN = r"olfactory|olfactori|\born\b|projection.neuron"
SEZ_PATTERN = r"sez|fdg|feeding|subesophageal|pharyngeal|gustatory"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PATH_COLUMNS = DATA_DIR / "column_assignment.csv.gz"
PATH_SUGAR = DATA_DIR / "sugar_grn_783.csv"
PATH_LEG_SUGAR = DATA_DIR / "leg_sugar_grn_783.csv"
PATH_NT_SILENT = DATA_DIR / "nt_modulatory_silent_783.csv"
PATH_NT_LIT = DATA_DIR / "nt_literature_783.csv"   # --nt-literature (scripts/make_nt_literature.py)
PATH_NT_IMPUTE = DATA_DIR / "nt_impute_783.csv"   # --nt-impute, MODEL VARIANT N1 (scripts/make_nt_impute.py)
NT_MODULATORY = ("DA", "SER", "OCT")   # --nt-modulatory-silent: slow modulators (+ no NT prediction)

# Poisson-driven input groups; each neuron belongs to at most one (checked below)
INPUT_GROUPS = ("ascending", "orn_food_L", "orn_food_R", "orn_food_C", "sugar", "t45_L", "t45_R")
LEGACY_INPUT_GROUPS = ("ascending", "olf_L", "olf_R", "olf_C", "vis_L", "vis_R", "sez")

# Food-odour glomeruli (vinegar / fruit / yeast odours; Semmelhack & Wang 2009,
# Hallem & Carlson 2006). Fixed before any run; not tuned on behaviour.
FOOD_GLOMERULI = ("DM1", "DM2", "DM4", "VA2", "VM2", "DP1m")
T45_TYPES = ("T4a", "T4b", "T4c", "T4d", "T5a", "T5b", "T5c", "T5d")

# Shiu et al. 2023 sugar GRNs (brain_model/figures.ipynb, v630 root ids updated to v783);
# 720575940620900446 is not in v783, 20 remain (all LB3, annotations side "left").
SHIU_SUGAR = (720575940624963786, 720575940630233916, 720575940637568838, 720575940638202345,
              720575940617000768, 720575940630797113, 720575940632889389, 720575940621754367,
              720575940621502051, 720575940640649691, 720575940639332736, 720575940616885538,
              720575940639198653, 720575940620900446, 720575940617937543, 720575940632425919,
              720575940633143833, 720575940612670570, 720575940628853239, 720575940629176663,
              720575940611875570)
SUGAR_KNN = 5
READOUT_GROUPS = ("dng02_L", "dng02_R", "steer_L", "steer_R", "dnp01", "dn_L", "dn_R", "dn_C",
                  "brain_mn")


def load_root_ids(path_comp=PATH_COMP):
    """root_id of each Completeness row; row position = Brian neuron index."""
    return pd.read_csv(path_comp, index_col=0).index.to_numpy(dtype=np.int64)


def root_to_index(root_ids):
    return {int(r): i for i, r in enumerate(root_ids)}


def _idx(roots, r2i):
    return np.array(sorted(r2i[int(r)] for r in roots if int(r) in r2i), dtype=np.int64)


def _side(series):
    return series.astype(str).str.strip().str.lower()


_TEXT_COLUMNS = ("cell_class", "cell_type", "super_class")
_SIDES = ("left", "right")


def _text_hits(table, pattern):
    """Boolean mask of the rows for which at least one text column contains `pattern`
    (case-insensitive; missing values count as the text "nan")."""
    hit = np.zeros(len(table), dtype=bool)
    for col in _TEXT_COLUMNS:
        lowered = table[col].astype(str).str.lower()
        hit |= lowered.str.contains(pattern, regex=True).to_numpy()
    return hit


def _by_side(table, rows, r2i):
    """(left, right, no side) index arrays of the selected rows of `table`."""
    side = _side(table["side"])[rows]
    roots = table["root_id"][rows]
    return tuple(_idx(roots[mask], r2i)
                 for mask in (side == "left", side == "right", ~side.isin(_SIDES)))


def _annotation_groups(ann, dn, r2i):
    """Groups that follow from the annotation tables alone (docs/ADAPTED_CODE.md D.1)."""
    out = {}
    out["ascending"] = _idx(ann["root_id"][ann["super_class"] == "ascending"], r2i)

    out["olf_L"], out["olf_R"], out["olf_C"] = _by_side(ann, _text_hits(ann, OLFACTORY_PATTERN), r2i)
    out["sez"] = _idx(ann["root_id"][_text_hits(ann, SEZ_PATTERN)], r2i)

    out["vis_L"], out["vis_R"], unsided = _by_side(ann, (ann["cell_class"] == "LA>ME").to_numpy(), r2i)
    if len(unsided):
        raise ValueError("LA>ME neurons without side; add a bilateral visual channel")

    out["brain_mn"] = _idx(ann["root_id"][ann["cell_class"] == "brain_motor_neuron"], r2i)

    everything = np.ones(len(dn), dtype=bool)
    out["dn_L"], out["dn_R"], out["dn_C"] = _by_side(dn, everything, r2i)
    ctype = dn["cell_type"].astype(str)
    for name, rows in (("dng02", ctype.str.match(r"^DNg02(_|$)").to_numpy()),
                       ("steer", ctype.isin(["DNa01", "DNa02"]).to_numpy())):
        out[f"{name}_L"], out[f"{name}_R"], _ = _by_side(dn, rows, r2i)
    out["dnp01"] = _idx(dn["root_id"][ctype == "DNp01"], r2i)
    return out


def build_groups(root_ids, path_ann=PATH_ANN, path_dn=PATH_DN):
    """Return {group name: sorted np.int64 array of Completeness row indices}."""
    r2i = root_to_index(root_ids)
    ann = pd.read_csv(path_ann, sep="\t", low_memory=False)
    ann = ann[ann["root_id"].isin(r2i)].reset_index(drop=True)
    g = _annotation_groups(ann, pd.read_csv(path_dn), r2i)

    # ── brain-control inputs ────────────────────────────────────────────────
    orn = ann[ann["cell_type"].astype(str).isin([f"ORN_{x}" for x in FOOD_GLOMERULI])]
    s = _side(orn["side"])
    g["orn_food_L"] = _idx(orn.loc[s == "left", "root_id"], r2i)
    g["orn_food_R"] = _idx(orn.loc[s == "right", "root_id"], r2i)
    g["orn_food_C"] = _idx(orn.loc[~s.isin(["left", "right"]), "root_id"], r2i)

    g["sugar"] = _idx(pd.read_csv(PATH_SUGAR)["root_id"], r2i)

    col = load_t45_columns()
    for sd in ("left", "right"):
        g[f"t45_{sd[0].upper()}"] = _idx(col.loc[col["hemisphere"] == sd, "root_id"], r2i)

    for names in (INPUT_GROUPS, LEGACY_INPUT_GROUPS):
        seen = np.zeros(len(root_ids), dtype=np.int8)
        for name in names:
            seen[g[name]] += 1
        if seen.max() > 1:
            raise ValueError(f"a neuron belongs to more than one Poisson input group of {names}")
    return g


def apl_kc_indices(root_ids, path_ann=PATH_ANN):
    """Completeness row indices of the APL neurons (cell_type APL, 1 per side) and of all
    Kenyon cells (cell_type KC*). Kept out of build_groups so that the recorded groups and
    the DEV subnet are unchanged; used only by the --apl-graded output mechanism."""
    r2i = root_to_index(root_ids)
    ann = pd.read_csv(path_ann, sep="\t", low_memory=False, usecols=["root_id", "cell_type"])
    ann = ann[ann["root_id"].isin(r2i)]
    ct = ann["cell_type"].astype(str)
    return _idx(ann.loc[ct == "APL", "root_id"], r2i), _idx(ann.loc[ct.str.startswith("KC"), "root_id"], r2i)


NT_SILENT_VARIANTS = ("broad", "narrow")


def nt_silent_indices(root_ids, variant="broad", path=PATH_NT_SILENT):
    """--nt-modulatory-silent (SPEC_BRAIN_CONTROL, Step 0 decisions II): Completeness row indices
    of the neurons whose Codex v783 nt_type is DA/SER/OCT or missing (broad) / DA/SER/OCT only
    (narrow) (scripts/make_nt_silent.py), and their nt_type labels (same order). The
    Poisson-input exception is applied by the caller (FlightBrain)."""
    if variant not in NT_SILENT_VARIANTS:
        raise ValueError(variant)
    r2i = root_to_index(root_ids)
    df = pd.read_csv(path)
    df = df[df["root_id"].isin(r2i)]
    if variant == "narrow":
        df = df[df["nt_type"].isin(NT_MODULATORY)]
    idx = df["root_id"].map(r2i).to_numpy(np.int64)
    o = np.argsort(idx)
    return idx[o], df["nt_type"].to_numpy(str)[o]


def nt_literature_indices(root_ids, path=PATH_NT_LIT, path_ann=PATH_ANN):
    """--nt-literature (SPEC_SENSORY_INPUTS §3.2c): Completeness row indices of the neurons whose cell
    type has a literature sign (sign_lit != 0 in data/nt_literature_783.csv), that sign (+1/-1, same
    order) and the type of each. Type = annotations cell_type, else hemibrain_type (as in
    scripts/diag/sa2_diag.py)."""
    lit = pd.read_csv(path)
    lit = lit[lit["sign_lit"] != 0].set_index("cell_type")["sign_lit"]
    r2i = root_to_index(root_ids)
    ann = pd.read_csv(path_ann, sep="\t", low_memory=False, usecols=["root_id", "cell_type", "hemibrain_type"])
    ann = ann.drop_duplicates("root_id")
    ann = ann[ann["root_id"].isin(r2i)]
    typ = ann["cell_type"].fillna(ann["hemibrain_type"])
    sel = typ.isin(lit.index)
    idx = ann.loc[sel, "root_id"].map(r2i).to_numpy(np.int64)
    t = typ[sel].to_numpy(str)
    o = np.argsort(idx)
    return idx[o], lit.reindex(t[o]).to_numpy(np.int64), t[o]


def nt_impute_indices(root_ids, path=PATH_NT_IMPUTE):
    """--nt-impute (MODEL VARIANT N1, SPEC_SENSORY_INPUTS §3.4b): Completeness row indices of the neurons that have no
    Codex nt_type and got an imputed sign (imputed_sign != 0 in data/nt_impute_783.csv), that sign (+1/-1, same order)
    and the type of each."""
    t = pd.read_csv(path)
    t = t[t["imputed_sign"] != 0]
    idx = t["root_id"].map(root_to_index(root_ids)).to_numpy(np.int64)
    o = np.argsort(idx)
    return idx[o], t["imputed_sign"].to_numpy(np.int64)[o], t["cell_type"].fillna("").to_numpy(str)[o]


def load_t45_columns(path=PATH_COLUMNS):
    """T4a-d / T5a-d rows of the FlyWire column assignment (root_id, hemisphere, type, p, q)."""
    col = pd.read_csv(path)
    return col[col["type"].isin(T45_TYPES)].reset_index(drop=True)


def select_sugar_homologs(path_ann=PATH_ANN, path_con=PATH_CON, k=SUGAR_KNN):
    """Right-side LB3 homologs of the Shiu sugar GRNs by connectivity profile.

    Features per LB3 neuron: synapse counts to/from each partner cell type, split
    by partner side relative to the neuron (ipsi / contra), L2-normalised, so the
    profile is mirror-invariant. Labels exist on the left only (Shiu set vs the
    other left LB3 = water/other). A right LB3 is a sugar homolog if the majority
    of its k most cosine-similar left LB3 are Shiu neurons. Chosen over the
    nearest-centroid rule by leave-one-out on the left (both directions, k=5:
    19/20 sugar, 2/44 false positives).
    Returns (DataFrame root_id, side, source, knn_frac, loo) where loo = dict of
    left leave-one-out counts."""
    ann = pd.read_csv(path_ann, sep="\t", low_memory=False,
                      usecols=["root_id", "cell_type", "hemibrain_type", "side"]).set_index("root_id")
    lb3 = ann.index[ann["cell_type"] == "LB3"].to_numpy()
    X = partner_profiles(lb3, ann, path_con)
    left = ann["side"].reindex(lb3).to_numpy() == "left"
    shiu = np.isin(lb3, SHIU_SUGAR)
    Li = np.flatnonzero(left)

    def knn_frac(i, pool):
        s = X[pool] @ X[i]
        return float(shiu[pool[np.argsort(-s, kind="stable")[:k]]].mean())

    loo = np.array([knn_frac(i, Li[Li != i]) > 0.5 for i in Li])
    loo_stats = dict(tp=int((loo & shiu[Li]).sum()), n_sugar=int(shiu[Li].sum()),
                     fp=int((loo & ~shiu[Li]).sum()), n_other=int((~shiu[Li]).sum()))
    rows = [dict(root_id=int(r), side="left", source="shiu2023", knn_frac=np.nan)
            for r in lb3[left & shiu]]
    for i in np.flatnonzero(~left):
        fr = knn_frac(i, Li)
        if fr > 0.5:
            rows.append(dict(root_id=int(lb3[i]), side=str(ann["side"].get(lb3[i])), source=f"homolog_knn{k}",
                             knn_frac=fr))
    return pd.DataFrame(rows), loo_stats


def partner_profiles(ids, ann, path_con=PATH_CON):
    """Rows of L2-normalised synapse counts to/from each partner cell type (cell_type, else
    hemibrain_type), split by partner side relative to the neuron (ipsi / contra) and by direction
    (in / out); mirror-invariant. ann: annotations indexed by root_id. Row order = ids."""
    con = pd.read_parquet(path_con, columns=["Presynaptic_ID", "Postsynaptic_ID", "Connectivity"])
    ptype = ann["cell_type"].fillna(ann["hemibrain_type"])
    parts = []
    for d, me, other in (("out", "Presynaptic_ID", "Postsynaptic_ID"), ("in", "Postsynaptic_ID", "Presynaptic_ID")):
        e = con[con[me].isin(ids)]
        pt = ptype.reindex(e[other]).to_numpy()
        rel = np.where(ann["side"].reindex(e[other]).to_numpy() == ann["side"].reindex(e[me]).to_numpy(), "i", "c")
        f = pd.DataFrame(dict(id=e[me].to_numpy(), feat=[f"{d}|{x}|{r}" for x, r in zip(pt, rel)],
                              w=e["Connectivity"].to_numpy()))
        parts.append(f[~pd.isna(pt)])
    del con
    f = pd.concat(parts)
    M = f.pivot_table(index="id", columns="feat", values="w", aggfunc="sum", fill_value=0).reindex(ids).fillna(0)
    X = M.to_numpy(float)
    X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
    return X


LEG_GRN_SUBCLASS = "SA_VTV_pro_meso_meta"   # sensory_ascending / gustatory: leg (pro/meso/meta) GRNs, 74


def select_leg_sugar_grns(path_ann=PATH_ANN, path_con=PATH_CON, k=SUGAR_KNN):
    """Sugar-like leg GRNs by connectivity profile (SPEC_SENSORY_INPUTS §2.4, §3.2b; VARSAYIM).

    Same features as select_sugar_homologs (partner_profiles). Labelled pool: labellar GRNs of
    cell_sub_class sugar/water (129) and bitter (65). A leg GRN (super_class sensory_ascending,
    cell_class gustatory, 74) is selected if the majority of its k most cosine-similar pool neurons
    are sugar/water. Method accuracy: leave-one-out inside the pool.
    Returns (DataFrame of all leg GRNs: root_id, side, cell_type, knn_frac, selected; loo dict)."""
    ann = pd.read_csv(path_ann, sep="\t", low_memory=False,
                      usecols=["root_id", "super_class", "cell_class", "cell_sub_class", "cell_type",
                               "hemibrain_type", "side"]).set_index("root_id")
    gust = ann["cell_class"] == "gustatory"
    sugar = ann.index[gust & (ann["super_class"] == "sensory") & (ann["cell_sub_class"] == "sugar/water")]
    bitter = ann.index[gust & (ann["super_class"] == "sensory") & (ann["cell_sub_class"] == "bitter")]
    leg = ann.index[gust & (ann["super_class"] == "sensory_ascending") & (ann["cell_sub_class"] == LEG_GRN_SUBCLASS)]
    pool = np.concatenate([sugar.to_numpy(), bitter.to_numpy()])
    is_sug = np.r_[np.ones(len(sugar), bool), np.zeros(len(bitter), bool)]
    X = partner_profiles(np.concatenate([pool, leg.to_numpy()]), ann, path_con)
    P, Q = X[:len(pool)], X[len(pool):]

    def frac(x, keep):
        s = P[keep] @ x
        return float(is_sug[keep][np.argsort(-s, kind="stable")[:k]].mean())

    allp = np.arange(len(pool))
    loo = np.array([frac(P[i], allp[allp != i]) > 0.5 for i in allp])
    loo_stats = dict(tp=int((loo & is_sug).sum()), n_sugar=int(is_sug.sum()),
                     fp=int((loo & ~is_sug).sum()), n_bitter=int((~is_sug).sum()), k=k)
    fr = np.array([frac(q, allp) for q in Q])
    df = pd.DataFrame(dict(root_id=leg.to_numpy(np.int64), side=ann.loc[leg, "side"].astype(str).to_numpy(),
                           cell_type=ann.loc[leg, "cell_type"].astype(str).to_numpy(), knn_frac=fr,
                           selected=fr > 0.5))
    return df, loo_stats


def leg_sugar_group(root_ids, path=PATH_LEG_SUGAR):
    """{"leg_sugar": sorted Completeness row indices} of the selected leg GRNs (--leg-grn)."""
    df = pd.read_csv(path)
    return {"leg_sugar": _idx(df.loc[df["selected"], "root_id"], root_to_index(root_ids))}


def group_counts(g):
    """Summary counts in the SPEC table form."""
    return {
        "ascending": len(g["ascending"]),
        "olfactory": len(g["olf_L"]) + len(g["olf_R"]) + len(g["olf_C"]),
        "sez": len(g["sez"]),
        "dn": len(g["dn_L"]) + len(g["dn_R"]) + len(g["dn_C"]),
        "la_me": len(g["vis_L"]) + len(g["vis_R"]),
        "dng02": len(g["dng02_L"]) + len(g["dng02_R"]),
        "steer": len(g["steer_L"]) + len(g["steer_R"]),
        "dnp01": len(g["dnp01"]),
        "brain_mn": len(g["brain_mn"]),
        "orn_food": len(g["orn_food_L"]) + len(g["orn_food_R"]) + len(g["orn_food_C"]),
        "sugar": len(g["sugar"]),
        "t45": len(g["t45_L"]) + len(g["t45_R"]),
    }


def neuron_positions(root_ids, path_ann=PATH_ANN):
    """Soma coordinates for the frontal brain panel (docs/ADAPTED_CODE.md D.2).
    Returns dict x, z (z = -y: dorsal up, float32) and idx (Completeness row index, int32), sorted by idx.
    Each coordinate falls back to the neuropil centroid (pos_*) when the soma one (soma_*) is missing."""
    r2i = root_to_index(root_ids)
    cols = ["root_id", "soma_x", "soma_y", "pos_x", "pos_y"]
    ann = pd.read_csv(path_ann, sep="\t", low_memory=False, usecols=cols)
    ann = ann[ann["root_id"].isin(r2i)]
    horiz = ann["soma_x"].fillna(ann["pos_x"])
    vert = ann["soma_y"].fillna(ann["pos_y"])
    usable = (horiz.notna() & vert.notna()).to_numpy()
    row = np.array([r2i[int(r)] for r in ann["root_id"].to_numpy()[usable]], dtype=np.int32)
    order = np.argsort(row)
    return dict(x=horiz.to_numpy()[usable].astype(np.float32)[order],
                z=-vert.to_numpy()[usable].astype(np.float32)[order], idx=row[order])
