#!/usr/bin/env python
"""One-off cache for render_flight_video_v2.py: per-neuron arbor centroids + dominant neuropil.

Inputs (Codex FlyWire v783 downloads, default ~/Downloads):
    synapse_coordinates.csv.gz   pre_root_id, post_root_id, x, y, z  (nm; one row per synapse)
        Empty root_id cells repeat the previous row's value, per column independently
        (verified: after a per-column forward fill, every (pre, post) block length equals the
        Connectivity_783 synapse count). Rows are sorted by pre_root_id.
    coordinates.csv.gz           root_id, "[x y z]" (nm; several rows per neuron) -> fallback
    neuropil_synapse_table.csv.gz  input/output synapses per neuropil (_L/_R = hemisphere)
    classification.csv.gz        super_class / class / side -> display class

Outputs (order = Completeness_783.csv rows, i.e. the simulation's neuron index):
    data/neuron_arbor_centroids.npz  root_id, pre/post/all centroid (float32 nm), n_pre, n_post,
                                     xyz (all-synapse centroid, else coordinates.csv mean), source
    data/neuron_neuropil.npz         neuropils (names without side), dominant (index, -1 = none),
                                     side ("L"/"R"/"C"/""), frac (dominant share of in+out synapses)
    data/neuron_class.npz            cls (index into labels: other, visual, olfactory, taste, DN, motor), side

Axes (checked on neuropil medians): x grows towards the fly's right (AL_L x 508 < AL_R 560 um),
y grows ventral (MB_CA 152 < GNG 328 um), z grows posterior (AL 45 < PB 175 um).

The synapse file is streamed in pyarrow blocks and reduced with np.bincount; peak RSS ~1 GB.
    env -u PYTHONPATH python scripts/prepare_neuron_geometry.py
"""
import argparse
import re
import resource
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pcsv

ROOT = Path(__file__).resolve().parent.parent
PATH_COMP = ROOT / "brain_model" / "Completeness_783.csv"
OUT_CENT = ROOT / "data" / "neuron_arbor_centroids.npz"
OUT_NP = ROOT / "data" / "neuron_neuropil.npz"
OUT_CLS = ROOT / "data" / "neuron_class.npz"
CLASS_LABELS = ("other", "visual", "olfactory", "taste", "DN", "motor")


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


def load_root_ids():
    return pd.read_csv(PATH_COMP, index_col=0).index.to_numpy(np.int64)


def index_of(sorted_ids, order, ids):
    """Completeness row index for each root id (-1 if not in the model)."""
    k = np.searchsorted(sorted_ids, ids)
    k = np.clip(k, 0, len(sorted_ids) - 1)
    ok = sorted_ids[k] == ids
    out = np.full(len(ids), -1, np.int64)
    out[ok] = order[k[ok]]
    return out


def synapse_centroids(path, root_ids, block_mb=64):
    n = len(root_ids)
    order = np.argsort(root_ids)
    sorted_ids = root_ids[order]
    acc = {s: np.zeros((4, n), np.float64) for s in ("pre", "post")}   # sum x, y, z, count
    types = {"pre_root_id": pa.int64(), "post_root_id": pa.int64(),
             "x": pa.int64(), "y": pa.int64(), "z": pa.int64()}
    reader = pcsv.open_csv(path, read_options=pcsv.ReadOptions(block_size=block_mb << 20),
                           convert_options=pcsv.ConvertOptions(column_types=types))
    last = {"pre_root_id": None, "post_root_id": None}
    rows = unmapped = 0
    t0 = time.time()
    for batch in reader:
        xyz = [batch.column(c).to_numpy().astype(np.float64) for c in "xyz"]
        for side, col in (("pre", "pre_root_id"), ("post", "post_root_id")):
            a = batch.column(col).combine_chunks() if hasattr(batch.column(col), "combine_chunks") \
                else batch.column(col)
            if last[col] is not None:   # carry the previous block's last id across the boundary
                a = pa.concat_arrays([pa.array([last[col]], pa.int64()), a])
                ids = pc.fill_null_forward(a).to_numpy()[1:]
            else:
                ids = pc.fill_null_forward(a).to_numpy()
            last[col] = int(ids[-1])
            idx = index_of(sorted_ids, order, ids)
            ok = idx >= 0
            unmapped += int((~ok).sum()) if side == "pre" else 0
            for j in range(3):
                acc[side][j] += np.bincount(idx[ok], weights=xyz[j][ok], minlength=n)
            acc[side][3] += np.bincount(idx[ok], minlength=n)
        rows += batch.num_rows
        if rows // 10_000_000 != (rows - batch.num_rows) // 10_000_000:
            print(f"  {rows / 1e6:6.1f} M synapses  {time.time() - t0:5.0f} s  peak RSS {rss_gb():.2f} GB",
                  flush=True)
    print(f"synapses: {rows:,} rows, {unmapped:,} with pre neuron not in Completeness_783")
    return acc, rows


def soma_fallback(path, root_ids):
    df = pd.read_csv(path, usecols=["root_id", "position"])
    xyz = np.array([np.array(p.strip("[]").split(), float) for p in df["position"]])
    order = np.argsort(root_ids)
    idx = index_of(root_ids[order], order, df["root_id"].to_numpy(np.int64))
    ok = idx >= 0
    n = len(root_ids)
    s = np.stack([np.bincount(idx[ok], weights=xyz[ok, j], minlength=n) for j in range(3)])
    c = np.bincount(idx[ok], minlength=n)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (s / c).T, c > 0


def neuropils(path, root_ids):
    df = pd.read_csv(path)
    cols = [c for c in df.columns if re.match(r"(input|output) synapses in ", c)]
    names = sorted({c.split(" in ", 1)[1] for c in cols})
    tot = np.stack([df[f"input synapses in {nm}"].to_numpy(float) + df[f"output synapses in {nm}"].to_numpy(float)
                    for nm in names], axis=1)
    base = [re.sub(r"_(L|R)$", "", nm) for nm in names]
    side = [nm[-1] if re.search(r"_(L|R)$", nm) else "C" for nm in names]
    bases = sorted(set(base))
    order = np.argsort(root_ids)
    idx = index_of(root_ids[order], order, df["root_id"].to_numpy(np.int64))
    ok = idx >= 0
    n = len(root_ids)
    dom = np.full(n, -1, np.int16)
    dside = np.full(n, "", "<U1")
    frac = np.zeros(n, np.float32)
    s = tot.sum(1)
    j = tot.argmax(1)
    has = ok & (s > 0)
    dom[idx[has]] = [bases.index(base[k]) for k in j[has]]
    dside[idx[has]] = np.array(side)[j[has]]
    frac[idx[has]] = tot[has, j[has]] / s[has]
    return dict(neuropils=np.array(bases), dominant=dom, side=dside, frac=frac,
                n_in_table=int(ok.sum()), n_not_in_model=int((~ok).sum()))


def classes(path, root_ids):
    df = pd.read_csv(path, usecols=["root_id", "super_class", "class", "side"])
    sup, cl = df["super_class"].fillna(""), df["class"].fillna("")
    code = np.zeros(len(df), np.int8)
    code[sup.isin(["optic", "visual_projection", "visual_centrifugal"]) | cl.isin(["visual", "ocellar"])] = 1
    code[cl.isin(["olfactory", "ALPN", "ALLN", "ALIN", "ALON"])] = 2
    code[cl.eq("gustatory")] = 3
    code[sup.eq("descending")] = 4
    code[sup.eq("motor")] = 5
    order = np.argsort(root_ids)
    idx = index_of(root_ids[order], order, df["root_id"].to_numpy(np.int64))
    ok = idx >= 0
    n = len(root_ids)
    cls = np.zeros(n, np.int8)
    side = np.full(n, "", "<U1")
    cls[idx[ok]] = code[ok]
    side[idx[ok]] = df["side"].fillna("").str[:1].str.upper().to_numpy()[ok]
    return dict(cls=cls, labels=np.array(CLASS_LABELS), side=side, n_classified=int(ok.sum()))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=str(Path.home() / "Downloads"))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    src = Path(args.src)
    root_ids = load_root_ids()
    n = len(root_ids)
    print(f"Completeness_783: {n:,} neurons")

    if OUT_CENT.exists() and not args.force:
        print(f"cached: {OUT_CENT}")
    else:
        acc, rows = synapse_centroids(src / "synapse_coordinates.csv.gz", root_ids)
        cent = {}
        with np.errstate(invalid="ignore", divide="ignore"):
            for s in ("pre", "post"):
                cent[s] = (acc[s][:3] / acc[s][3]).T.astype(np.float32)
            both = acc["pre"] + acc["post"]
            cent["all"] = (both[:3] / both[3]).T.astype(np.float32)
        has = both[3] > 0
        fb, fb_ok = soma_fallback(src / "coordinates.csv.gz", root_ids)
        xyz = cent["all"].copy()
        use_fb = ~has & fb_ok
        xyz[use_fb] = fb[use_fb]
        source = np.where(has, 1, np.where(use_fb, 2, 0)).astype(np.int8)   # 1 synapses, 2 coordinates, 0 none
        print(f"centroids: {has.sum():,} from synapses, {use_fb.sum():,} from coordinates.csv fallback, "
              f"{(source == 0).sum():,} without any position")
        np.savez_compressed(OUT_CENT, root_id=root_ids, pre=cent["pre"], post=cent["post"], all=cent["all"],
                            n_pre=acc["pre"][3].astype(np.int32), n_post=acc["post"][3].astype(np.int32),
                            xyz=xyz, source=source, unit="nm", n_synapse_rows=rows)
        print(f"written {OUT_CENT}")

    if OUT_NP.exists() and not args.force:
        print(f"cached: {OUT_NP}")
    else:
        npl = neuropils(src / "neuropil_synapse_table.csv.gz", root_ids)
        print(f"neuropils: {len(npl['neuropils'])} names, {(npl['dominant'] >= 0).sum():,} neurons with a "
              f"dominant neuropil, {npl['n_not_in_model']} table rows not in the model")
        np.savez_compressed(OUT_NP, **npl)
        print(f"written {OUT_NP}")
    if OUT_CLS.exists() and not args.force:
        print(f"cached: {OUT_CLS}")
    else:
        c = classes(src / "classification.csv.gz", root_ids)
        print("classes: " + ", ".join(f"{lab} {(c['cls'] == k).sum():,}" for k, lab in enumerate(CLASS_LABELS))
              + f" ({c['n_classified']:,} of {n:,} in classification.csv)")
        np.savez_compressed(OUT_CLS, **c)
        print(f"written {OUT_CLS}")
    print(f"peak RSS {rss_gb():.2f} GB")


if __name__ == "__main__":
    main()
