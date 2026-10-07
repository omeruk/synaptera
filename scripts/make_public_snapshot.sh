#!/usr/bin/env bash
# Build a clean public snapshot of this work in a separate directory (default ../synaptera).
#
#   bash scripts/make_public_snapshot.sh [DEST]
#
# What goes in: an allow-list = the "files added in this work" table of docs/FILE_PROVENANCE.md (§B) plus
# the files committed after that table was generated (EXTRA below), minus the exclusions below. Files are
# taken from the committed HEAD (git archive), not from the working tree. Nothing in this repository is
# changed, moved or deleted; DEST must not exist yet.
#
# What stays out:
#   - every file of the upstream NeuroFly tree (b59264a), except README.md, whose content was replaced
#     entirely in this work (checked below: no line of the upstream README is left);
#   - brain_model/ (Shiu et al. copy and FlyWire data; scripts/fetch_data.py downloads it);
#   - all FlyWire / Codex raw and derived data files, i.e. everything in data/ except data/README.md
#     (scripts/fetch_data.py rebuilds them), incl. data/orn_spontaneous_783.csv;
#   - HDF5 run files, videos (the README GIF previews and stills in media/ are kept), archive/, docs/NEUROFLY_FLIGHT_YENI_PROJE_MASTER_DONUSUM_REHBERI.md,
#     docs/neurofly_upstream/;
#   - plots/ (figures rendered from the run files and Codex-derived neuron positions; licence conditional
#     on the FlyWire/Codex terms, THIRD_PARTY.md §2);
#   - CLAUDE.md, docs/UCUS_PROMPTU.md, docs/NEUROFLY_MASTER_DOKUMANTASYON_VE_SISTEM_PROMPTU.md (working
#     prompts in Turkish; the last one describes the upstream NeuroFly system).
#
# Layout changes in the snapshot only: REPORT_*.md and SPEC_*.md move to docs/tr/ (lab notebook, in
# Turkish) with a note at the top; links are rewritten; README.md gets snapshot wording and NOTICE.md describes the copy;
# a new .gitignore and docs/SNAPSHOT_MANIFEST.md (file list with SHA-256) are written. LICENSE (MIT, this work
# only) is part of the allow-list; no upstream file is in the copy.
set -euo pipefail

SRC=$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)
DEST=${1:-$SRC/../synaptera}
UPSTREAM=b59264a
PY=${PYTHON:-python3}

if [ -e "$DEST" ]; then
    echo "error: $DEST exists; choose a new directory (this script never deletes anything)" >&2
    exit 1
fi
cd "$SRC"
HEAD=$(git rev-parse --short HEAD)
if ! git diff --quiet HEAD -- docs/FILE_PROVENANCE.md scripts/make_public_snapshot.sh; then
    echo "error: commit docs/FILE_PROVENANCE.md and this script first (the snapshot is built from HEAD)" >&2
    exit 1
fi

# files committed after docs/FILE_PROVENANCE.md was generated (a59fc28); all written in this work
EXTRA=(
    LICENSE
    requirements-flight.txt
    docs/FILE_PROVENANCE.md
    media/README.md
    docs/ADAPTED_CODE.md
    docs/PREREGISTRATION_LOG.md
    scripts/fetch_data.py
    scripts/make_descending_neurons.py
    scripts/make_public_snapshot.sh
    THIRD_PARTY.md
    REPORT.md
    run_videos_en.sh
    run_videos_vis.sh
)
# upstream paths whose content was replaced entirely in this work
REPLACED=(README.md)

LIST=$(mktemp)
trap 'rm -f "$LIST"' EXIT
"$PY" - "$UPSTREAM" "$LIST" "${EXTRA[@]}" -- "${REPLACED[@]}" <<'EOF'
import fnmatch, re, subprocess, sys
upstream, out = sys.argv[1], sys.argv[2]
rest = sys.argv[3:]
extra, replaced = rest[:rest.index("--")], rest[rest.index("--") + 1:]
git = lambda *a: subprocess.run(["git", *a], check=True, capture_output=True, text=True).stdout
prov = open("docs/FILE_PROVENANCE.md").read()
section_b = prov[prov.index("## B. Files added in this work"):]
listed = re.findall(r"^\| `([^`]+)` \| [0-9a-f]{7}", section_b, re.M)
up = set(git("ls-tree", "-r", "--name-only", upstream).split("\n")) - {""}
head = set(git("ls-tree", "-r", "--name-only", "HEAD").split("\n")) - {""}
EXCLUDE = ["brain_model/*", "data/*", "simulations/*", "*.h5", "*.mp4", "simulations/*.gif", "archive/*", "plots/*",
           "docs/NEUROFLY_FLIGHT_YENI_PROJE_MASTER_DONUSUM_REHBERI.md", "docs/neurofly_upstream/*",
           "CLAUDE.md", "docs/UCUS_PROMPTU.md", "docs/NEUROFLY_MASTER_DOKUMANTASYON_VE_SISTEM_PROMPTU.md",
           "logs/*", "simulation.pid"]
KEEP = {"data/README.md"}
keep, dropped = [], []
for f in dict.fromkeys(listed + extra):
    if f not in head:
        sys.exit(f"error: {f} is listed but not tracked at HEAD")
    if f in up:
        dropped.append((f, "upstream path"))
    elif f not in KEEP and any(fnmatch.fnmatch(f, p) for p in EXCLUDE):
        dropped.append((f, "excluded"))
    else:
        keep.append(f)
for f in replaced:          # replaced upstream files: no line (> 30 chars) of the upstream version may remain
    old = {l.strip() for l in git("show", f"{upstream}:{f}").split("\n") if len(l.strip()) > 30}
    new = {l.strip() for l in git("show", f"HEAD:{f}").split("\n") if len(l.strip()) > 30}
    if old & new:
        sys.exit(f"error: {f} still shares {len(old & new)} lines with the upstream version")
    keep.append(f)
untracked_new = sorted(head - up - set(listed) - set(extra) - set(replaced))
leftover = [f for f in untracked_new if not (any(fnmatch.fnmatch(f, p) for p in EXCLUDE) and f not in KEEP)]
if leftover:
    print("note: tracked files of this work not in the allow-list (left out):", *leftover, sep="\n  ")
open(out, "w").write("\n".join(sorted(keep)) + "\n")
print(f"allow-list: {len(keep)} files; left out from the provenance list: {len(dropped)}")
EOF

mkdir -p "$DEST"
git archive --format=tar HEAD $(cat "$LIST") | tar -x -C "$DEST"
cp "$LIST" "$DEST/.snapshot_files"

"$PY" - "$DEST" "$HEAD" <<'EOF'
import hashlib, re, sys
from pathlib import Path
dest, head = Path(sys.argv[1]), sys.argv[2]
tr = dest / "docs" / "tr"
tr.mkdir(parents=True, exist_ok=True)
moved = sorted(p.name for p in dest.glob("REPORT_*.md")) + sorted(p.name for p in dest.glob("SPEC_*.md"))
NOTE = ("> **Lab notebook, in Turkish.** Working record of this project, kept as written during the work "
        "(moved here from the repository root for the public snapshot). The English consolidated report is "
        "[REPORT.md](../../REPORT.md); the English summary is the [README](../../README.md).\n\n")
link = re.compile(r"\]\((?!https?://|#|mailto:)([^)\s]+)\)")

def rewrite_moved(m):          # links inside the moved files: other moved files stay siblings
    t = m.group(1)
    base = t.split("#")[0]
    if base in moved or base == "":
        return m.group(0)
    return f"](../../{t})"

def rewrite_other(path):       # links from other files to the moved files
    def f(m):
        t = m.group(1)
        base, _, frag = t.partition("#")
        name = base.split("/")[-1]
        if name in moved and not base.startswith("docs/tr/"):
            rel = Path("docs/tr") / name
            up = "../" * (len(path.relative_to(dest).parts) - 1)
            return f"]({up}{rel}{'#' + frag if frag else ''})"
        return m.group(0)
    return f

for name in moved:
    src = dest / name
    text = link.sub(rewrite_moved, src.read_text())
    (tr / name).write_text(NOTE + text)
    src.unlink()
for p in dest.rglob("*.md"):
    if p.parent == tr:
        continue
    p.write_text(link.sub(rewrite_other(p), p.read_text()))

def edit(path, pairs):
    s = path.read_text()
    for old, new in pairs:
        if old not in s:
            sys.exit(f"error: snapshot edit anchor not found in {path.name}: {old[:70]!r}")
        s = s.replace(old, new)
    path.write_text(s)

for name in ("README.md", "REPORT.md"):    # backticked names of the moved Turkish documents
    doc = dest / name
    s = doc.read_text()
    s = re.sub(r"`((?:REPORT|SPEC)_[A-Z0-9_/]*(?:\*)?\.md)`", lambda m: f"`docs/tr/{m.group(1)}`", s)
    doc.write_text(s)
readme = dest / "README.md"
edit(readme, [
    ("The walking code (`fly_brain_body_simulation.py`, `generate_plots.py`) is kept (one Linux/memory fix only, 86ea1fc); the upstream READMEs are in `docs/neurofly_upstream/`.",
     "**This is a public snapshot that contains only the files written in this work** (list: "
     "[docs/SNAPSHOT_MANIFEST.md](docs/SNAPSHOT_MANIFEST.md)). NeuroFly's own files (walking code, "
     "`brain_model/` copy, assets, data) are not included; parts of the flight code are adapted from the "
     "NeuroFly walking script ([docs/ADAPTED_CODE.md](docs/ADAPTED_CODE.md)). No data files are included: "
     "`scripts/fetch_data.py` downloads and rebuilds them (see [Data](#data))."),
    ("and the pre-registration documents (`docs/tr/SPEC_*.md`) are in Turkish.",
     "and the pre-registration documents (`docs/tr/SPEC_*.md`) are a lab notebook, in Turkish."),
    ("Note: this repository currently still contains FlyWire files (most of them came from the upstream repository); recommendations: [docs/REPO_CLEANUP_REPORT.md](docs/REPO_CLEANUP_REPORT.md).",
     "This snapshot contains no FlyWire, Codex or other third-party data file. Rebuild them with\n"
     "`env -u PYTHONPATH python scripts/fetch_data.py --codex-dir <Codex downloads> --model-runs`: it downloads "
     "the Shiu et al. files and the FlyWire annotations from pinned commits (SHA-256 checked), rebuilds "
     "`brain_model/descending_neurons.csv` and the `data/` files, and prints a hash table against the files "
     "used by the reported runs. The Codex downloads need a sign-in; `--codex-help` prints step-by-step "
     "instructions. The HDF5 run files are not included (available on request); tests that need a missing "
     "data file are skipped."),
    ("`tests/` (walking + `tests/flight`).\n- `fly_brain_body_simulation.py`, `generate_plots.py`: NeuroFly walking code (in the flight work only the 86ea1fc fix).\n",
     "`tests/flight` (pytest).\n- `docs/tr/`: lab notebook in Turkish (reports and pre-registrations); `docs/`: provenance, "
     "adapted code, pre-registration log, snapshot manifest.\n"),
    ("**The public copy contains no video file and no HDF5 run file.** In this development repository the flight videos are not committed either (`.gitignore`: `*.mp4`); of the flight run files only the three final-v1 files (`simulations/flight_v11/v12/v13_*_data.h5`) are committed.",
     "**This copy contains no video file and no HDF5 run file** (`.gitignore`: `*.mp4`, `*.h5`)."),
    ("# the walking code (NeuroFly) needs requirements.txt instead / in addition\n",
     "env -u PYTHONPATH python scripts/fetch_data.py --codex-dir ~/Downloads --model-runs   # data, see Data\n"),
])
notice = dest / "NOTICE.md"      # describes this copy, not the development repository
edit(notice, [
    ("This repository is a continuation of NeuroFly; the first commits of the git history (2026-03-25 – 2026-04-05) belong to NeuroFly.",
     "Synaptera was developed as a continuation of NeuroFly: the history of its development repository starts with "
     "NeuroFly's commits (2026-03-25 – 2026-04-05)."),
    ("- Parts that come from NeuroFly: the walking simulation (`fly_brain_body_simulation.py`, `generate_plots.py`, `fruitfly/`, the NeuroFly files in `simulation_data/`, the walking tests, `Dockerfile`, `run.bat`), the copy of `brain_model/` and the upstream READMEs (`docs/neurofly_upstream/README.fr.md`, `README.en.md`; moved from the root, only relative links fixed). Of these, only `fly_brain_body_simulation.py` was changed in this work (86ea1fc: HDF5 written before the video, Linux FlyGym path, memory fixes); the rest is unchanged.",
     "- **This copy contains no NeuroFly file.** NeuroFly's walking simulation (`fly_brain_body_simulation.py`, "
     "`generate_plots.py`, `fruitfly/`, its `simulation_data/` files, the walking tests, `Dockerfile`, `run.bat`), its "
     "copy of `brain_model/` and its READMEs are not included. `README.md` has the same path as NeuroFly's README, but "
     "its content was written entirely in this work (no line of the upstream README remains; checked when the copy "
     "is built)."),
    ("- The flight code (`fly_flight_brain_body_simulation.py`, `flight/`, `simulation_data/odor_field_3d.py`, `scripts/`, `tests/flight/`, `render_flight_*.py`, `generate_flight_plots.py`) was written in this work;",
     "- Every file of this copy was written in this work (list with SHA-256: "
     "[docs/SNAPSHOT_MANIFEST.md](docs/SNAPSHOT_MANIFEST.md)). The flight code (`fly_flight_brain_body_simulation.py`, "
     "`flight/`, `simulation_data/odor_field_3d.py`, `scripts/`, `tests/flight/`, `render_flight_*.py`, "
     "`generate_flight_plots.py`) is new;"),
    ("redistribution and licensing of the adapted parts depend on the upstream author; the MIT licence of this work does not extend to any upstream file.",
     "because parts of the flight code are adapted from it, redistribution and licensing of the adapted parts depend "
     "on the upstream author; the MIT licence of this work does not extend to any upstream file (none is in this copy)."),
    ("- Used: `Completeness_783.csv`, `Connectivity_783.parquet`, `flywire_annotations.tsv`,",
     "- Used by the code (**none of them is included in this copy**; `scripts/fetch_data.py` downloads and rebuilds "
     "them): `Completeness_783.csv`, `Connectivity_783.parquet`, `flywire_annotations.tsv`,"),
    ("\n- Note: this repository currently contains FlyWire files (`brain_model/`, `simulation_data/flywire_connectome_v783/`; they came from the upstream repository). Removing them before publication is recommended (docs/REPO_CLEANUP_REPORT.md).", ""),
    ("- `data/orn_spontaneous_783.csv` was derived from the `SFR` rows of DoOR.data (Hallem & Carlson 2006 column).",
     "- `data/orn_spontaneous_783.csv` (not included in this copy; `scripts/make_orn_spontaneous.py`, run by "
     "`scripts/fetch_data.py`, rebuilds it) is derived from the `SFR` rows of DoOR.data (Hallem & Carlson 2006 column)."),
    ("the recommendation is to stop distributing it and keep the generating script (THIRD_PARTY.md §3).",
     "therefore this copy does not distribute it and contains only the generating script (THIRD_PARTY.md §3)."),
    ("| `brain_model/` (copy), recurrent synapse set-up and LIF parameters |",
     "| `brain_model/model.py` (downloaded by `scripts/fetch_data.py`, not included), recurrent synapse set-up and LIF parameters |"),
    ("they were not copied into the repository.", "they are not included in this copy."),
])
tp = dest / "THIRD_PARTY.md"
tp.write_text(tp.read_text().replace("\n", "\n\n> Public snapshot: this audit was made on the development repository. "
                                     "The snapshot contains only the files in docs/SNAPSHOT_MANIFEST.md; \"copy in repo: yes\" "
                                     "refers to the development repository.\n", 1))

(dest / ".gitignore").write_text("""# data fetched or rebuilt by scripts/fetch_data.py (not distributed)
brain_model/
data/*
!data/README.md
# run outputs and media
simulations/
plots/
logs/
*.h5
*.mp4
*.gif
!media/*.gif
# Python
__pycache__/
*.py[cod]
.pytest_cache/
""")

files = sorted(p for p in dest.rglob("*") if p.is_file() and p.name != ".snapshot_files")
rows = [f"| `{p.relative_to(dest)}` | {p.stat().st_size:,} | `{hashlib.sha256(p.read_bytes()).hexdigest()}` |"
        for p in files if p.name != "SNAPSHOT_MANIFEST.md"]
(dest / "docs" / "SNAPSHOT_MANIFEST.md").write_text(
    f"# Snapshot manifest\n\nPublic snapshot built by `scripts/make_public_snapshot.sh` from development-repository "
    f"commit `{head}` (private; available on request). {len(rows)} files (this manifest not counted).\n\n"
    "| file | bytes | SHA-256 |\n|---|---|---|\n" + "\n".join(rows) + "\n")
(dest / ".snapshot_files").unlink()
print(f"moved to docs/tr/: {', '.join(moved)}")
print(f"{len(rows) + 1} files written")
EOF

# final checks on the snapshot
# media/preview_*.gif (cut from the videos; the videos themselves stay out) and media/stills/stills.csv are allowed.
# figures/data/*.csv are the aggregated plotted data of the figures (derived results, CC BY-NC 4.0; docs: THIRD_PARTY.md §2.4), allowed
bad=$(cd "$DEST" && find . -path ./figures/data -prune -o -path './media/preview_*.gif' -prune -o -path ./media/stills/stills.csv -prune -o -type f \( -name '*.h5' -o -name '*.mp4' -o -name '*.gif' -o -name '*.parquet' \
      -o -name '*.npz' -o -name '*.csv' -o -name '*.csv.gz' -o -name '*.tsv' \) -print | sort)
if [ -n "$bad" ]; then echo "error: unexpected files in the snapshot:"; echo "$bad"; exit 1; fi
for d in brain_model archive plots simulations docs/neurofly_upstream; do
    [ -e "$DEST/$d" ] && { echo "error: $d present in the snapshot"; exit 1; }
done
root_tr=$(cd "$DEST" && ls REPORT_*.md SPEC_*.md CLAUDE.md 2>/dev/null || true)
[ -n "$root_tr" ] && { echo "error: Turkish documents at the root: $root_tr"; exit 1; }
echo "snapshot of $HEAD written to $DEST ($(du -sh "$DEST" | cut -f1))"
