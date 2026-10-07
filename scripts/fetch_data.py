#!/usr/bin/env python
"""Fetch the third-party input files and rebuild the derived data files.

The public snapshot of this repository ships no FlyWire, Codex or other third-party data. This script
downloads the inputs from pinned commits, checks them by SHA-256, and rebuilds every derived file with the
scripts of this repository. At the end it prints a hash table that compares each file with the copy used
in the development repository (the files the reported runs used).

Steps (run in this order; each step skips files that already exist unless --force):

  fetch    brain_model/model.py, LICENSE, Completeness_783.csv, Connectivity_783.parquet
               philshiu/Drosophila_brain_model @ 91bdd1e (MIT; data files: FlyWire v783)
           brain_model/flywire_annotations.tsv
               flyconnectome/flywire_annotations @ c03ad462aa, supplemental_files/Supplemental_file1_neuron_annotations.tsv
  derive   brain_model/descending_neurons.csv          scripts/make_descending_neurons.py
           data/sugar_grn_783.csv                      scripts/make_sugar_grn.py
           data/leg_sugar_grn_783.csv                  scripts/make_leg_sugar_grn.py
           data/orn_spontaneous_783.csv                scripts/make_orn_spontaneous.py (downloads DoOR.data @ db323a4, CC BY-SA 4.0)
           data/t45_transduction.json                  scripts/make_t45_transduction.py   (needs the FlyVis weights)
           data/visual_transduction.json               scripts/make_visual_transduction.py (needs the FlyVis weights)
  codex    (only with --codex-dir DIR: FlyWire Codex downloads need a sign-in, see --codex-help)
           data/column_assignment.csv.gz               copied unchanged from DIR
           data/nt_modulatory_silent_783.csv           scripts/make_nt_silent.py
           data/neuron_arbor_centroids.npz, neuron_neuropil.npz, neuron_class.npz
                                                       scripts/prepare_neuron_geometry.py
           data/vision_boundary_783.csv, vision_boundary_types.json
                                                       scripts/make_vision_boundary.py
  model    (only with --model-runs: full-brain runs, a few minutes each, ~4 GB RAM)
           data/dn_lr_reference.json                   scripts/make_dn_reference.py
           data/dn_lr_reference_sB.json                scripts/make_dn_reference.py --vision-boundary

Not rebuilt here: data/nt_literature_783.csv (only for --nt-literature; it needs the output of
scripts/diag/sa2_diag.py on the Stage A smoke runs v17/v18, see the docstring of scripts/make_nt_literature.py).

    env -u PYTHONPATH python scripts/fetch_data.py                                  # fetch + derive
    env -u PYTHONPATH python scripts/fetch_data.py --codex-dir ~/Downloads --model-runs
    env -u PYTHONPATH python scripts/fetch_data.py --report-only                    # hash table only
    env -u PYTHONPATH python scripts/fetch_data.py --codex-help                     # Codex instructions

Licences: see THIRD_PARTY.md. The downloaded and derived files are not covered by the licence of this
repository; FlyWire-derived files are treated as CC BY-NC 4.0 (non-commercial) until verified.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAIN = ROOT / "brain_model"
DATA = ROOT / "data"

SHIU = "philshiu/Drosophila_brain_model", "91bdd1e7dcf193f3e7ca5a8933497fcef63b7960"
ANNOT = "flyconnectome/flywire_annotations", "c03ad462aa19876d80ea54f25a028619348f8d43"

# (target, repository, commit, path in repository, SHA-256)
DOWNLOADS = [
    (BRAIN / "model.py", *SHIU, "model.py",
     "fc45837d7122c6ce2a7f3f2f23c515992e4b232aadb919efabb72337fac88e4e"),
    (BRAIN / "LICENSE", *SHIU, "LICENSE",
     "3621f6d6476189190e2960fa43f11b275ba4eca848fdac50a1ba2925de6223e8"),
    (BRAIN / "Completeness_783.csv", *SHIU, "Completeness_783.csv",
     "bbb847a4cc2caaa7a16349722d220c087317b946d148d4d592d94d250617a311"),
    (BRAIN / "Connectivity_783.parquet", *SHIU, "Connectivity_783.parquet",
     "efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347"),
    (BRAIN / "flywire_annotations.tsv", *ANNOT, "supplemental_files/Supplemental_file1_neuron_annotations.tsv",
     "533db093e12d8de350fd20875a967f8f74acace633ff22118eefff550d5dcbc1"),
]

# FlyWire Codex downloads (materialization v783) used in the development repository.
CODEX = {
    "column_assignment.csv.gz": "bdf4ce7f62cc63493d53eefad3816ff2dfd08b190e97b35a492e0e453df2f0f6",
    "neurons.csv.gz": "6a6b3759e635f0f35a677d169052362131ec61d95f55919298b55c43fce4e719",
    "consolidated_cell_types.csv.gz": "8aba246d71dc40361677493629972ce3883048c3d02010adc42bda22962a1a2d",
    "classification.csv.gz": "e946b552f4056dfc977707be0674609832c3f64332a22d69dc0d9615e7aae663",
    "neuropil_synapse_table.csv.gz": "e525bdea7bc2fe585cf8ab8f9fc76bea5e29f2c3e5240588b6add518bcda5ab1",
    "synapse_coordinates.csv.gz": "dfcb423d9f685d56c81160e50ca158c9ab589871cb01922af2a5b8c4442216b1",
    "coordinates.csv.gz": "14337121f451f98c2576cee72c24409ada5aaf7948b7c7ca8de9040296840e05",
}

# SHA-256 of the files used by the reported runs (development repository, commit 1d133f8).
EXPECTED = {
    "brain_model/descending_neurons.csv": "8ebafd9627fb416c2078708da174d5740bbe14e3cbc94363b01bbf46d31e1044",
    "data/sugar_grn_783.csv": "014417652b97bbbb13c08053635d47e0bb68862c93e7fb2cebdf8f6f034035c8",
    "data/leg_sugar_grn_783.csv": "da8d8741e5d2d8dd1297f3288387974207b154ac03a703fbbd33ca2a148b841e",
    "data/orn_spontaneous_783.csv": "7809c96455955fa8f7458c7b2bbc7c64a3321e467a3b31738884e5974dcf4e66",
    "data/t45_transduction.json": "5498602fe0a124780b386d3061031c5719643c858e883c2140b4641349653e2b",
    "data/visual_transduction.json": "83ec486afdc788afcf4b46e625f682759976c9e29a291749e7a096468f8ccfab",
    "data/column_assignment.csv.gz": "bdf4ce7f62cc63493d53eefad3816ff2dfd08b190e97b35a492e0e453df2f0f6",
    "data/nt_modulatory_silent_783.csv": "c2a5eb10db27d9f02ff3ac5f5f44c3ef378ec80e48c754eb9e697199c462aed5",
    "data/neuron_arbor_centroids.npz": "f97d7a893e3946f2a362cc79a3d48d802753ec7b8987254f2322feeb9f1322bf",
    "data/neuron_neuropil.npz": "f225e5400203ea2443f2e9f5acfb36a2be29a01cc0317bf45021bf54da7d60a6",
    "data/neuron_class.npz": "26bc7bdf34b8acf335e8b6681d5e56c108b6273e75452c4e714c61e475cce968",
    "data/vision_boundary_783.csv": "2749472d4cda5698074802be5dae19cf1fea2aebe1e8a58e48582b3dc29d44b7",
    "data/vision_boundary_types.json": "e387773f12348720c7f2199af6dd9cfb41579fbcb4a76f1c487c426314c2856f",
    "data/dn_lr_reference.json": "8f4ecb34e0a01394dfb6d858b05b93498a3018739319c8862e851f683bf51cf3",
    "data/dn_lr_reference_sB.json": "6094c2756c82b0397a552fbcefd8710acd022ba744824fa5fa9709d858cbc790",
    "data/nt_literature_783.csv": "4fd69979a9b19733041560ab0a3c5e8e0f8be5fd04fb9898ffb50669b4ac6c89",
}

CODEX_HELP = """FlyWire Codex downloads (needed for --codex-dir; they cannot be fetched by a script because the
download page requires a sign-in, and they are not redistributed here):

  1. Open https://codex.flywire.ai and sign in (a Google account; accept the FlyWire terms of use,
     https://flywire.ai/tos). Read the terms that apply to the downloads.
  2. Open the download page: https://codex.flywire.ai/api/download
  3. Select the data version (materialization) 783.
  4. Download these files (keep the .csv.gz names):
       column_assignment.csv.gz        (visual columns)
       neurons.csv.gz                  (neurotransmitter predictions)
       consolidated_cell_types.csv.gz  (cell types)
       classification.csv.gz           (super class / class / side)
       neuropil_synapse_table.csv.gz   (synapses per neuropil)
       synapse_coordinates.csv.gz      (~320 MB; only for the video brain panel and the boundary-layer columns)
       coordinates.csv.gz              (neuron positions)
  5. Put them into one directory and run
       env -u PYTHONPATH python scripts/fetch_data.py --codex-dir <that directory>
  The script compares each download with the SHA-256 of the file used for the reported runs and warns
  if it differs (a later Codex export can differ in bytes; the derived files are then compared too).
  Attribution: Dorkenwald et al. 2024, Schlegel et al. 2024, Matsliah et al. 2024 (see README)."""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(target, repo, commit, path, digest, force=False):
    rel = target.relative_to(ROOT)
    if target.exists() and not force:
        got = sha256(target)
        if got == digest:
            print(f"  ok (present)  {rel}")
            return True
        print(f"  present but SHA-256 differs, downloading again: {rel}")
    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    tmp = target.with_name(target.name + ".part")
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"  download {url}")
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
    got = sha256(tmp)
    if got != digest:
        tmp.unlink()
        print(f"  SHA-256 MISMATCH for {rel}: got {got}, expected {digest}; file not written")
        return False
    tmp.replace(target)
    print(f"  ok            {rel}")
    return True


def run(py, script, *args, outputs=(), force=False):
    outs = [ROOT / o for o in outputs]
    if outs and all(o.exists() for o in outs) and not force:
        print(f"  skip (present) {', '.join(outputs)}")
        return True
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.setdefault("MUJOCO_GL", "egl")
    cmd = [py, str(ROOT / "scripts" / script), *map(str, args)]
    print("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT, env=env)
    if r.returncode != 0:
        print(f"  FAILED ({script}, exit {r.returncode})")
    return r.returncode == 0


def flyvis_weights_present():
    try:
        import flyvis
        return (Path(flyvis.results_dir) / "flow" / "0000" / "000").exists()
    except Exception:
        return False


def step_fetch(a):
    print("[fetch] third-party inputs from pinned commits")
    return all([download(*d, force=a.force) for d in DOWNLOADS])


def step_derive(a):
    print("[derive] files that need only the fetched inputs (and DoOR / FlyVis)")
    ok = run(a.python, "make_descending_neurons.py", outputs=["brain_model/descending_neurons.csv"], force=a.force)
    ok &= run(a.python, "make_sugar_grn.py", outputs=["data/sugar_grn_783.csv"], force=a.force)
    ok &= run(a.python, "make_leg_sugar_grn.py", outputs=["data/leg_sugar_grn_783.csv"], force=a.force)
    ok &= run(a.python, "make_orn_spontaneous.py", outputs=["data/orn_spontaneous_783.csv"], force=a.force)
    if flyvis_weights_present():
        ok &= run(a.python, "make_t45_transduction.py", outputs=["data/t45_transduction.json"], force=a.force)
        ok &= run(a.python, "make_visual_transduction.py", outputs=["data/visual_transduction.json"], force=a.force)
    else:
        print("  FlyVis weights not found: run `flyvis download-pretrained`, then this script again "
              "(t45_transduction.json, visual_transduction.json skipped)")
        ok = False
    return ok


def step_codex(a):
    print("[codex] files derived from FlyWire Codex downloads")
    if not a.codex_dir:
        print("  skipped (no --codex-dir). Instructions:\n")
        print(CODEX_HELP)
        return None
    src = Path(a.codex_dir).expanduser()
    missing = [n for n in CODEX if not (src / n).exists()]
    if missing:
        print(f"  missing in {src}: {', '.join(missing)}\n")
        print(CODEX_HELP)
        return False
    for n, digest in CODEX.items():
        same = sha256(src / n) == digest
        print(f"  {'ok' if same else 'WARNING: differs from the development copy'}  {n}")
    DATA.mkdir(exist_ok=True)
    dst = DATA / "column_assignment.csv.gz"
    if not dst.exists() or a.force:
        shutil.copyfile(src / "column_assignment.csv.gz", dst)
        print(f"  copied {dst.relative_to(ROOT)}")
    ok = run(a.python, "make_nt_silent.py", "--codex-dir", src,
             outputs=["data/nt_modulatory_silent_783.csv"], force=a.force)
    geo = ["data/neuron_arbor_centroids.npz", "data/neuron_neuropil.npz", "data/neuron_class.npz"]
    ok &= run(a.python, "prepare_neuron_geometry.py", "--src", src, *(["--force"] if a.force else []),
              outputs=geo, force=a.force)
    ok &= run(a.python, "make_vision_boundary.py", "--codex-dir", src,
              outputs=["data/vision_boundary_783.csv", "data/vision_boundary_types.json"], force=a.force)
    return ok


def step_model(a):
    print("[model] reference rates from full-brain runs")
    if not a.model_runs:
        print("  skipped (no --model-runs); data/dn_lr_reference.json and data/dn_lr_reference_sB.json are "
              "needed for the closed-loop runs")
        return None
    ok = run(a.python, "make_dn_reference.py", outputs=["data/dn_lr_reference.json"], force=a.force)
    ok &= run(a.python, "make_dn_reference.py", "--vision-boundary",
              outputs=["data/dn_lr_reference_sB.json"], force=a.force)
    return ok


def report(out=None):
    rows = ["| file | SHA-256 (this copy) | same as the development repository? |", "|---|---|---|"]
    n_same = n_diff = n_missing = 0
    for rel, digest in EXPECTED.items():
        p = ROOT / rel
        if not p.exists():
            status, got = "missing", "—"
            n_missing += 1
        else:
            got = sha256(p)
            same = got == digest
            status = "**identical**" if same else f"DIFFERS (expected `{digest[:16]}…`)"
            n_same += same
            n_diff += not same
        rows.append(f"| `{rel}` | `{got[:16]}…` | {status} |" if got != "—" else f"| `{rel}` | — | {status} |")
    rows.append("")
    rows.append(f"{n_same} identical, {n_diff} different, {n_missing} missing (of {len(EXPECTED)}).")
    text = "\n".join(rows)
    print("\n[report] derived files vs. the files used by the reported runs\n")
    print(text)
    if out:
        Path(out).write_text(text + "\n")
        print(f"\nwritten {out}")
    return n_diff == 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--codex-dir", default=None, help="directory with the FlyWire Codex v783 downloads")
    ap.add_argument("--model-runs", action="store_true", help="also rebuild the DN reference files (model runs)")
    ap.add_argument("--force", action="store_true", help="rebuild files that already exist")
    ap.add_argument("--python", default=sys.executable, help="interpreter for the generating scripts")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--report", default=None, help="also write the hash table (Markdown) to this file")
    ap.add_argument("--codex-help", action="store_true", help="print the Codex download instructions")
    a = ap.parse_args(argv)
    if a.codex_help:
        print(CODEX_HELP)
        return 0
    if not a.report_only:
        if not step_fetch(a):
            print("\nfetch failed; nothing derived")
            return 1
        res = [step_derive(a), step_codex(a), step_model(a)]
        print("\n[not rebuilt] data/nt_literature_783.csv (needs scripts/diag/sa2_diag.py output of runs v17/v18; "
              "only for --nt-literature)")
        if any(r is False for r in res):
            print("\nsome steps failed or were incomplete (see above)")
    report(a.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
