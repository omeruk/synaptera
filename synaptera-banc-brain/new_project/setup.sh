#!/usr/bin/env bash
# New project setup: synaptera-banc-brain
#
# What it does (changes no source, deletes nothing):
#   1. Creates the NEW folder with the layout of 05_ARCHITECTURE_PLAN.md section 5 (stops if it exists and is not empty).
#   2. Copies the plan and analyses to docs/, the analysis scripts to scripts/analysis/, CLAUDE.md to the root.
#   3. Copies the Synaptera files marked take/adapt/pattern in migration.tsv UNCHANGED to
#      vendor/synaptera_v1/<original path>; writes MANIFEST.md with the source commit and SHA-256 of each file.
#      The porting (BANC support, H1-H5 fixes) is done with Claude Code, in the order of MIGRATION_CHECKLIST.md.
#   4. If DEV_REPO is given, copies the data files (brain_model/, data/) (cp -n: never overwrites).
#   5. Writes .gitignore, initialises the git repository and makes the first commit.
#
# Usage:
#   SYNAPTERA=~/synaptera DEV_REPO=~/Documents/NeuroFly bash ~/synaptera/synaptera-banc-brain/new_project/setup.sh
#   (optional) NEW=~/synaptera-banc-brain   target folder (this is the default)
set -euo pipefail

SYNAPTERA=${SYNAPTERA:?"SYNAPTERA: path of the synaptera clone (e.g. ~/synaptera)"}
NEW=${NEW:-$HOME/synaptera-banc-brain}
DEV_REPO=${DEV_REPO:-}
HERE="$SYNAPTERA/synaptera-banc-brain"
TSV="$HERE/new_project/migration.tsv"

die() { echo "ERROR: $*" >&2; exit 1; }
# cp -n: never overwrites an existing file (GNU cp 9.x prints a "-n is non-portable" warning, filtered here)
cpn() { cp -n "$@" 2> >(grep -v "behavior of -n is non-portable" >&2); }
[ -f "$TSV" ] || die "$TSV not found; is SYNAPTERA right and main up to date (git pull)?"
[ -d "$SYNAPTERA/.git" ] || die "$SYNAPTERA is not a git repository"
if [ -e "$NEW" ] && [ -n "$(ls -A "$NEW" 2>/dev/null)" ]; then
    die "$NEW already exists and is not empty; stopping so nothing gets mixed up (give another NEW or move the folder yourself)"
fi
SRC_COMMIT=$(git -C "$SYNAPTERA" rev-parse HEAD)
SRC_DIRTY=$(git -C "$SYNAPTERA" status --porcelain -- . ':!brain_model' ':!data' | wc -l)
[ "$SRC_DIRTY" -eq 0 ] || echo "WARNING: uncommitted changes in $SYNAPTERA; MANIFEST will show commit $SRC_COMMIT"

echo "[1/5] folder layout: $NEW"
mkdir -p "$NEW"
for d in connectome engine sense motor body coupling tasks train prereg scripts/analysis configs tests docs/results \
         vendor/synaptera_v1; do
    mkdir -p "$NEW/$d"
done

echo "[2/5] plan, analyses, CLAUDE.md"
cpn "$HERE"/0*.md "$NEW/docs/"
cpn "$HERE/README.md" "$NEW/docs/00_SYNAPTERA_REVIEW_SUMMARY.md"
cpn "$HERE"/results/* "$NEW/docs/results/"
cpn "$HERE"/scripts/*.py "$NEW/scripts/analysis/"
cpn "$HERE/new_project/CLAUDE.md" "$NEW/CLAUDE.md"
cpn "$SYNAPTERA/LICENSE" "$NEW/LICENSE"

echo "[3/5] Synaptera files -> vendor/synaptera_v1 (unchanged)"
MAN="$NEW/vendor/synaptera_v1/MANIFEST.md"
LIST="$NEW/MIGRATION_CHECKLIST.md"
write_manifest_header() {
    echo "# vendor/synaptera_v1 — files copied unchanged from Synaptera v1.0.0"
    echo
    echo "Source: https://github.com/omeruk/synaptera, commit \`$1\`. These files are **reference only** and are never"
    echo "imported; the new code is written in the project layout and each new file notes its source (path + this commit)."
    echo
    echo "| file | decision | target | SHA-256 |"
    echo "|---|---|---|---|"
}
write_checklist_header() {
    echo "# Migration checklist"
    echo
    echo "Source commit \`$1\`. Details and reasons: \`docs/06_NEW_PROJECT_SETUP.md\`."
    echo "Order matters (dependency order). Each item: adapt -> test -> commit."
    echo
}
write_manifest_header "$SRC_COMMIT" > "$MAN"
write_checklist_header "$SRC_COMMIT" > "$LIST"
n_copy=0
while IFS=$'\t' read -r order path decision target note; do
    [ "$order" = "order" ] && continue          # header
    [ -z "$path" ] && continue
    case "$decision" in
        take|adapt|pattern)
            src="$SYNAPTERA/$path"
            [ -f "$src" ] || die "file of the TSV not found: $path"
            mkdir -p "$NEW/vendor/synaptera_v1/$(dirname "$path")"
            cpn "$src" "$NEW/vendor/synaptera_v1/$path"
            sha=$(sha256sum "$src" | cut -d' ' -f1)
            echo "| \`$path\` | $decision | \`$target\` | \`${sha:0:16}…\` |" >> "$MAN"
            echo "- [ ] **$order.** \`$path\` → \`$target\` ($decision): $note" >> "$LIST"
            n_copy=$((n_copy + 1))
            ;;
        leave) ;;
        *) die "unknown decision '$decision' ($path)" ;;
    esac
done < "$TSV"
echo "    $n_copy files copied"

echo "[4/5] data"
if [ -n "$DEV_REPO" ]; then
    [ -d "$DEV_REPO/brain_model" ] || die "$DEV_REPO/brain_model not found"
    mkdir -p "$NEW/brain_model" "$NEW/data"
    cpn -r "$DEV_REPO/brain_model/." "$NEW/brain_model/"
    find "$DEV_REPO/data" -maxdepth 1 -type f -exec cp -n {} "$NEW/data/" \; 2> >(grep -v "behavior of -n is non-portable" >&2)
    echo "    brain_model/ and data/ copied ($DEV_REPO); the Codex downloads stay where they are (--codex-dir)"
else
    echo "    DEV_REPO not given: data step skipped (later: copy by hand with cp -n)"
fi

echo "[5/5] git"
cat > "$NEW/.gitignore" <<'EOF'
# data (never committed; downloaded by scripts/fetch_data.py)
brain_model/
data/
banc/
runs/
*.h5
*.npz
*.parquet
*.feather
# outputs
*.mp4
plots/
logs/
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
EOF
cd "$NEW"
git init -q -b main
git add -A
git commit -q -m "Initial skeleton from Synaptera v1.0.0 ($SRC_COMMIT)

Plan and analyses in docs/, CLAUDE.md, unchanged reference copies of the
carried Synaptera files in vendor/synaptera_v1/ (MANIFEST.md lists source
commit and SHA-256), porting checklist in MIGRATION_CHECKLIST.md."
echo
echo "Ready: $NEW ($(git rev-parse --short HEAD))"
echo "Next steps:"
echo "  1. On GitHub create an empty repository: omeruk/synaptera-banc-brain (no README/licence)"
echo "  2. cd $NEW && git remote add origin https://github.com/omeruk/synaptera-banc-brain.git && git push -u origin main"
echo "  3. conda activate neurofly && claude   (first prompt: docs/06_NEW_PROJECT_SETUP.md section 4)"
