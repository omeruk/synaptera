#!/usr/bin/env python
"""Build the data bundle (run records read by scripts/verify_report_final.py and the report scripts) in a new directory.

    env -u PYTHONPATH python scripts/make_data_bundle.py [--dest ../synaptera_data_v1] [--videos-dest ../synaptera_videos_v1]
                                                         [--list FILE]     # use a saved trace instead of tracing verify

The file list is not written by hand: `scripts/verify_report_final.py` is run under `strace -f -e trace=openat` and every regular
file it (and the report scripts it calls) opens read-only under logs/, simulations/ and data/ is collected. From data/ only the files
that `scripts/fetch_data.py` cannot rebuild from public sources are taken (its `outputs=[...]` of the derive step are rebuilt there).
Files are COPIED with their relative paths; the originals are never touched. Nothing is simulated or rendered.

Personal information is removed in the copies only: absolute paths and user / machine names in text files, npz string arrays and
HDF5 attributes / string datasets are replaced ($HOME, relative path); the replaced fields are written to MANIFEST.tsv. Numerical
content is identical to the original records.

Outputs in DEST: the files at their relative paths, README_DATA.md, MANIFEST.tsv (file, bytes, sha256, REPORT.md section, sanitised
fields), SHA256SUMS. In VIDEOS_DEST: the three *_en_vis.mp4 files and a short README.md.
"""
import argparse
import getpass
import hashlib
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

# path pattern -> section of REPORT.md (documentation of the bundle, not a file list)
SECTIONS = [
    (r"logs/final/|flight_v1[123]_.*final_[abc]_data", "§1, §3.1 (final-v1 runs final_a/b/c)"),
    (r"flight_v16_.*final_sB", "§3.1 (final_sB, Stage B)"),
    (r"logs/final_v2/|final_v2[ac]_data", "§3.1 (final-v2 runs final_v2a/v2c)"),
    (r"v2val_data", "§3.2 (DNp15 validation, closed loop)"),
    (r"flight_v(17|18|20|21)_.*smoke", "§4 (negative findings; Stage A/A2 smoke runs)"),
    (r"logs/natural/|_n[12]_data\.h5", "§3.3, §3.4 (n1 / n2)"),
    (r"logs/seeds/|_n[12]_s1[0-4]_data", "§3.4 (multi-seed repeat)"),
    (r"logs/starts/|_st_[a-z0-9]+_data", "§3.5 (start position / heading)"),
    (r"\.mp4$", "§3.6 (videos; ffprobe check)"),
    (r"logs/smell/o1_nf", "§3.7 (comparison check, upstream-style drive)"),
    (r"logs/smell/o1_diag", "§3.7 (exploratory diagnostic)"),
    (r"logs/smell/o1_N[12]", "§3.7 (O1 under the sign variants N1 / N2)"),
    (r"logs/smell/robust", "§3.7 (robustness records)"),
    (r"logs/smell/o1", "§3.7 (O1, open loop)"),
    (r"logs/vis_dn/", "§3.8 (visual DN screen)"),
    (r"logs/vis_loom/", "§3.8b (loom follow-up)"),
    (r"logs/ladder/(teacher|replay_audit)", "§3.9 (teacher flights, replay)"),
    (r"logs/ladder/", "§3.9b (trial 1: readouts, replays, validation flights)"),
    (r"^data/", "inputs read by verify; not rebuildable from public sources (FlyWire-derived)"),
]


def section(rel):
    for pat, name in SECTIONS:
        if re.search(pat, rel):
            return name
    return "report scripts"


def trace_files(dest_trace):
    """Run verify under strace; return the set of relative paths opened read-only under the repository."""
    cmd = ["strace", "-f", "-qq", "-e", "trace=openat,open,chdir", "-o", str(dest_trace), "env", "-u", "PYTHONPATH", PY, str(ROOT / "scripts" / "verify_report_final.py")]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(r.stdout[-300:])
    if "ALL OK" not in r.stdout:
        sys.exit("verify did not end with ALL OK; the file list would be incomplete")
    return parse_trace(dest_trace)


def parse_trace(path):
    """Relative paths (to the repository) of files opened read-only; relative opens are resolved against the chdir of the same pid."""
    out, cwd = set(), {}
    for ln in open(path, errors="replace"):
        pid = ln.split(" ", 1)[0]
        m = re.search(r'chdir\("([^"]+)"\) = 0', ln)
        if m:
            cwd[pid] = Path(m.group(1)) if m.group(1).startswith("/") else cwd.get(pid, ROOT) / m.group(1)
            continue
        m = re.search(r'openat\(AT_FDCWD, "([^"]+)", ([A-Z_|]+)[^)]*\) = (\d+)', ln)
        if not m:
            continue
        p, flags, _ = m.groups()
        if any(f in flags for f in ("O_WRONLY", "O_RDWR", "O_CREAT")):
            continue
        q = Path(p) if p.startswith("/") else cwd.get(pid, ROOT) / p
        try:
            rel = q.resolve().relative_to(ROOT)
        except ValueError:
            continue
        if q.is_file():
            out.add(str(rel))
    return out


def rebuildable():
    """data/ files that fetch_data.py rebuilds from public sources (outputs of its derive step)."""
    txt = (ROOT / "scripts" / "fetch_data.py").read_text()
    step = txt[txt.index("def step_derive"):txt.index("def step_codex")]
    return set(re.findall(r'outputs=\["([^"]+)"\]', step))


def select(opened):
    skip = rebuildable()
    keep = []
    for rel in sorted(opened):
        top = rel.split("/")[0]
        if top in ("logs", "simulations") or (top == "data" and rel not in skip):
            keep.append(rel)
    return keep


class Sanitiser:
    def __init__(self):
        self.user = getpass.getuser()
        self.host = socket.gethostname()
        self.root = str(ROOT)
        self.home = str(Path.home())
        self.pairs = [(self.root + "/", ""), (self.root, "."), (self.home, "$HOME")]
        self.changed = []

    def text(self, s):
        o = s
        for a, b in self.pairs:
            s = s.replace(a, b)
        return s, s != o

    def bytes_has_pii(self, b):
        return any(x.encode() in b for x in (self.home, self.root))


def sanitise_text(src, dst, san):
    raw = src.read_bytes()
    try:
        s = raw.decode()
    except UnicodeDecodeError:
        dst.write_bytes(raw)
        return []
    s2, ch = san.text(s)
    dst.write_text(s2) if ch else dst.write_bytes(raw)
    return ["text: absolute path"] if ch else []


def sanitise_npz(src, dst, san):
    z = np.load(src, allow_pickle=False)
    arrs, fields = {}, []
    for k in z.files:
        a = z[k]
        if a.dtype.kind in "US":
            flat = [str(x) for x in a.ravel()]
            new = [san.text(x)[0] for x in flat]
            if new != flat:
                a = np.array(new, dtype=a.dtype.kind + str(max(len(x) for x in new))).reshape(a.shape)
                fields.append(f"npz array {k}")
        arrs[k] = a
    if fields:
        np.savez_compressed(dst, **arrs)
    else:
        shutil.copy2(src, dst)
    return fields


def sanitise_h5(src, dst, san):
    shutil.copy2(src, dst)
    fields = []
    with h5py.File(dst, "r+") as f:
        def fix(name, o):
            for k, v in list(o.attrs.items()):
                if isinstance(v, str):
                    s, ch = san.text(v)
                    if ch:
                        o.attrs[k] = s
                        fields.append(f"attr {name}@{k}")
            if isinstance(o, h5py.Dataset) and o.dtype.kind in "OS" and o.size < 100000:
                a = o[()]
                flat = np.array(a, dtype=object).ravel()
                strs = [x.decode() if isinstance(x, bytes) else str(x) for x in flat]
                new = [san.text(x)[0] for x in strs]
                if new != strs:
                    o[...] = np.array(new, dtype=object).reshape(np.shape(a))
                    fields.append(f"dataset {name}")
        f.visititems(fix)
        for k, v in list(f.attrs.items()):
            if isinstance(v, str):
                s, ch = san.text(v)
                if ch:
                    f.attrs[k] = s
                    fields.append(f"attr /@{k}")
    return fields


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def build(files, dest, san):
    rows = []
    for rel in files:
        src, dst = ROOT / rel, dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        ext = src.suffix
        if ext == ".h5":
            fields = sanitise_h5(src, dst, san)
        elif ext == ".npz":
            fields = sanitise_npz(src, dst, san)
        elif ext == ".mp4":
            shutil.copy2(src, dst)
            fields = []
        else:
            fields = sanitise_text(src, dst, san)
        rows.append((rel, dst.stat().st_size, sha256(dst), section(rel), "; ".join(fields)))
    return rows


def human(n):
    return f"{n / 1e9:.2f} GB" if n >= 1e9 else f"{n / 1e6:.1f} MB"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dest", default=str(ROOT.parent / "synaptera_data_v1"))
    ap.add_argument("--videos-dest", default=str(ROOT.parent / "synaptera_videos_v1"))
    ap.add_argument("--list", help="strace output of a verify run (skips the tracing)")
    ap.add_argument("--max-gb", type=float, default=45.0)
    a = ap.parse_args()
    dest, vdest = Path(a.dest), Path(a.videos_dest)
    for d in (dest, vdest):
        if d.exists():
            sys.exit(f"error: {d} exists; this script never deletes anything")
    opened = parse_trace(a.list) if a.list else trace_files(Path(tempfile.mkdtemp()) / "verify_strace.out")
    files = select(opened)
    total = sum((ROOT / f).stat().st_size for f in files)
    print(f"{len(files)} files, {human(total)}")
    if total > a.max_gb * 1e9:
        sys.exit(f"total {human(total)} exceeds {a.max_gb} GB: stop and ask for a split")
    san = Sanitiser()
    dest.mkdir(parents=True)
    rows = build(files, dest, san)
    (dest / "MANIFEST.tsv").write_text("file\tbytes\tsha256\treport_section\tsanitised_fields\n" + "\n".join("\t".join(map(str, r)) for r in rows) + "\n")
    (dest / "SHA256SUMS").write_text("".join(f"{r[2]}  {r[0]}\n" for r in rows))
    tot = sum(r[1] for r in rows)
    big = sorted(rows, key=lambda r: -r[1])[:10]
    n_san = sum(bool(r[4]) for r in rows)
    sec = {}
    for r in rows:
        s = sec.setdefault(r[3], [0, 0])
        s[0] += 1
        s[1] += r[1]
    lines = "\n".join(f"| {k} | {v[0]} | {human(v[1])} |" for k, v in sorted(sec.items()))
    (dest / "README_DATA.md").write_text(README.format(n=len(rows), size=human(tot), sections=lines, n_san=n_san,
                                                      big="\n".join(f"- `{r[0]}` ({human(r[1])})" for r in big)))
    # videos
    vdest.mkdir(parents=True)
    for f in sorted(files):
        if f.endswith("_en_vis.mp4"):
            shutil.copy2(ROOT / f, vdest / Path(f).name)
    (vdest / "README.md").write_text(VID_README)
    (vdest / "SHA256SUMS").write_text("".join(f"{sha256(p)}  {p.name}\n" for p in sorted(vdest.glob("*.mp4"))))
    print("bundle:", dest, len(rows), "files", human(tot))
    print("sanitised files:", n_san)
    for r in big:
        print(human(r[1]), r[0])


README = """# Data bundle for Synaptera (run records)

Run records read by `scripts/verify_report_final.py` and the report scripts of the code repository (Synaptera, branch
`sensory-inputs`). With this bundle in place, `verify_report_final.py` prints `ALL OK`. DOI of this bundle: to be added.

## Content
{n} files, {size}. The file list was not written by hand: it is the set of files that `verify_report_final.py` (and the report
scripts it calls) opens, recorded with `strace` (`scripts/make_data_bundle.py`).

| REPORT.md section | files | size |
|---|---|---|
{sections}

Largest files:
{big}

Folder structure = the relative paths of the code repository: `logs/…` (npz / json / DONE files), `simulations/…` (HDF5 run
records `*_data.h5` and the six videos that verify checks with ffprobe), `data/…` (derived input files that need FlyWire Codex
downloads or full-brain runs and therefore cannot be rebuilt by `scripts/fetch_data.py` without a sign-in). `MANIFEST.tsv` lists every
file with size, SHA-256 and the REPORT.md section; `SHA256SUMS` can be checked with `sha256sum -c SHA256SUMS`.

## How to use
1. Get the code repository (public copy) and run `env -u PYTHONPATH python scripts/fetch_data.py` once (downloads and rebuilds
   `brain_model/` and the derivable `data/` files; the FlyVis weights are needed: `flyvis download-pretrained`).
2. Unpack this bundle into the root of the code repository (`logs/`, `simulations/` and `data/` merge with the existing folders).
3. Run `env -u PYTHONPATH python scripts/verify_report_final.py`.

Without the bundle, `verify_report_final.py` stops with the message "run records not present" and a non-zero exit code.

## Sanitised fields
Numerical content is identical to the original records; path strings are sanitised. In {n_san} files an absolute path of the
author's machine was replaced (`$HOME`, or a path relative to the repository root); the fields are listed in the last column of
`MANIFEST.tsv`. No simulation was run and no video was rendered for this bundle; videos are copies of the rendered files.

## Licence and attribution
The records are derived from the FlyWire connectome (public release, version 783), whose data FlyWire makes available under
**CC BY-NC 4.0** (https://flywire.ai/guidelines, opened 2026-10-07); this bundle is shared under **CC BY-NC 4.0**, non-commercial use,
with attribution to FlyWire and the following papers: Dorkenwald, S. et al. (2024), *Nature* 634, 124–138,
doi:10.1038/s41586-024-07558-y; Schlegel, P. et al. (2024), *Nature* 634, 139–152, doi:10.1038/s41586-024-07686-5; Matsliah, A. et al.
(2024), *Nature* 634, 166–180, doi:10.1038/s41586-024-07981-1 (visual columns); Shiu, P. K. et al. (2024), *Nature* 634, 210–219,
doi:10.1038/s41586-024-07763-9 (the brain model); FlyWire Codex (codex.flywire.ai). The FlyVis network: Lappalainen, J. K. et al. (2024),
*Nature* 634, 1132–1140, doi:10.1038/s41586-024-07939-3; the body: Wang-Chen, S. et al. (2024), *Nature Methods* 21, 2353–2362,
doi:10.1038/s41592-024-02497-y. Code, report and figures: the code repository (README, NOTICE, THIRD_PARTY).
"""

VID_README = """# Synaptera videos (n1, n2, n1 | n2)

Copies of the rendered videos of REPORT.md §3.6 (`render_flight_video_v2.py`, `run_videos_vis.sh`); nothing was re-rendered.
H.264, yuv420p, 1920×1080, 30 fps. The hand-made route takes the fly to the food; the brain decides to feed (the on-screen
"brain odour input OFF" refers to the brain only). Brain panels are a display setting, not a measurement.

| file | content |
|---|---|
| `flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change_en_vis.mp4` | n1 (hand-made route, brain feeding decision) |
| `flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change_en_vis.mp4` | n2 (brain only, hand-made flight programme) |
| `flight_n1_vs_n2_v2_compare_en_vis.mp4` | n1 and n2 side by side |

Licence: derived from FlyWire data (CC BY-NC 4.0, https://flywire.ai/guidelines, opened 2026-10-07); shared under **CC BY-NC 4.0**,
non-commercial use, with attribution to FlyWire (Dorkenwald et al. 2024; Schlegel et al. 2024), Shiu et al. 2024, Lappalainen et al. 2024
and Wang-Chen et al. 2024; full references in the code repository (README). DOI: to be added.
"""

if __name__ == "__main__":
    main()
