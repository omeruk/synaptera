#!/usr/bin/env bash
# One-time update of a synaptera-banc-brain folder that was set up with the earlier Turkish package (kur.sh).
#
# What it does (only in NEW; Synaptera and the data are not touched):
#   1. Replaces the Turkish documents in docs/ with the English ones (docs/results/ instead of docs/veri/).
#   2. Replaces CLAUDE.md and the analysis scripts in scripts/analysis/ with the English versions.
#   3. Renames TASINMA_LISTESI.md to MIGRATION_CHECKLIST.md with English notes; ticked items stay ticked.
#   4. Rewrites vendor/synaptera_v1/MANIFEST.md in English (same source commit, SHA-256 recomputed).
#   5. Commits these paths on the current branch.
# Run it while no Claude Code session is working in NEW.
#
# Usage:
#   SYNAPTERA=~/synaptera bash ~/synaptera/synaptera-banc-brain/new_project/update_to_english.sh
#   (optional) NEW=~/synaptera-banc-brain
set -euo pipefail

SYNAPTERA=${SYNAPTERA:?"SYNAPTERA: path of the synaptera clone (e.g. ~/synaptera)"}
NEW=${NEW:-$HOME/synaptera-banc-brain}
HERE="$SYNAPTERA/synaptera-banc-brain"
TSV="$HERE/new_project/migration.tsv"
die() { echo "ERROR: $*" >&2; exit 1; }
[ -f "$TSV" ] || die "$TSV not found; run 'git pull origin main' in $SYNAPTERA first"
[ -d "$NEW/.git" ] || die "$NEW is not a git repository"
cd "$NEW"

echo "[1/5] documents"
for f in docs/00_SYNAPTERA_ANALIZ_OZETI.md docs/01_KOD_INCELEMESI.md docs/02_MODEL_FIZIK_TEST_ANALIZI.md \
         docs/03_BANC_OLANAKLARI.md docs/04_ARASTIRMA_NOTLARI.md docs/05_MIMARI_PLAN.md docs/06_YENI_PROJE_KURULUMU.md; do
    git rm -q --ignore-unmatch -- "$f"; rm -f "$f"
done
git rm -q -r --ignore-unmatch -- docs/veri; rm -rf docs/veri
mkdir -p docs/results scripts/analysis
cp -f "$HERE"/0*.md docs/
cp -f "$HERE/README.md" docs/00_SYNAPTERA_REVIEW_SUMMARY.md
cp -f "$HERE"/results/* docs/results/

echo "[2/5] CLAUDE.md and analysis scripts"
cp -f "$HERE/new_project/CLAUDE.md" CLAUDE.md
cp -f "$HERE"/scripts/*.py scripts/analysis/

echo "[3/5] checklist"
src_commit=$(grep -o 'commit `[0-9a-f]*`' vendor/synaptera_v1/MANIFEST.md | head -1 | tr -d '`' | cut -d' ' -f2)
[ -n "$src_commit" ] || die "could not read the source commit from vendor/synaptera_v1/MANIFEST.md"
done_items=""
if [ -f TASINMA_LISTESI.md ]; then
    done_items=$(grep -oE '^- \[[xX]\] \*\*[0-9]+\.' TASINMA_LISTESI.md | grep -oE '[0-9]+' | tr '\n' ' ' || true)
elif [ -f MIGRATION_CHECKLIST.md ]; then
    done_items=$(grep -oE '^- \[[xX]\] \*\*[0-9]+\.' MIGRATION_CHECKLIST.md | grep -oE '[0-9]+' | tr '\n' ' ' || true)
fi
{
    echo "# Migration checklist"
    echo
    echo "Source commit \`$src_commit\`. Details and reasons: \`docs/06_NEW_PROJECT_SETUP.md\`."
    echo "Order matters (dependency order). Each item: adapt -> test -> commit."
    echo
    while IFS=$'\t' read -r order path decision target note; do
        [ "$order" = "order" ] && continue
        case "$decision" in take|adapt|pattern) ;; *) continue ;; esac
        box=" "
        for d in $done_items; do [ "$d" = "$order" ] && box="x"; done
        echo "- [$box] **$order.** \`$path\` → \`$target\` ($decision): $note"
    done < "$TSV"
} > MIGRATION_CHECKLIST.md
git rm -q --ignore-unmatch -- TASINMA_LISTESI.md; rm -f TASINMA_LISTESI.md
echo "    ticked items kept: ${done_items:-none}"

echo "[4/5] vendor manifest"
{
    echo "# vendor/synaptera_v1 — files copied unchanged from Synaptera v1.0.0"
    echo
    echo "Source: https://github.com/omeruk/synaptera, commit \`$src_commit\`. These files are **reference only** and are never"
    echo "imported; the new code is written in the project layout and each new file notes its source (path + this commit)."
    echo
    echo "| file | decision | target | SHA-256 |"
    echo "|---|---|---|---|"
    while IFS=$'\t' read -r order path decision target note; do
        [ "$order" = "order" ] && continue
        case "$decision" in take|adapt|pattern) ;; *) continue ;; esac
        f="vendor/synaptera_v1/$path"
        [ -f "$f" ] || die "missing vendor copy: $f"
        sha=$(sha256sum "$f" | cut -d' ' -f1)
        echo "| \`$path\` | $decision | \`$target\` | \`${sha:0:16}…\` |"
    done < "$TSV"
} > vendor/synaptera_v1/MANIFEST.md

echo "[5/5] commit"
git add -A -- CLAUDE.md MIGRATION_CHECKLIST.md docs scripts/analysis vendor/synaptera_v1/MANIFEST.md
git commit -q -m "Switch documentation to English

English versions of the plan and analyses (docs/), CLAUDE.md and the
analysis scripts; TASINMA_LISTESI.md renamed to MIGRATION_CHECKLIST.md
(ticked items kept); vendor manifest text in English." || echo "    nothing to commit"
echo "Done: $(git log -1 --format='%h %s')"
