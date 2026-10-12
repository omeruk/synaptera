#!/usr/bin/env bash
# Yeni proje kurulumu: synaptera-banc-brain
#
# Ne yapar (hiçbir kaynağı değiştirmez, hiçbir şey silmez):
#   1. NEW klasörünü 05_MIMARI_PLAN.md §5 düzeniyle oluşturur (klasör varsa ve boş değilse durur).
#   2. Planı ve analizleri docs/, analiz betiklerini scripts/analysis/ altına kopyalar; CLAUDE.md'yi köke koyar.
#   3. tasinacaklar.tsv'de take/adapt/pattern olarak işaretli Synaptera dosyalarını DEĞİŞTİRMEDEN
#      vendor/synaptera_v1/<özgün yol> altına kopyalar; kaynak commit ve SHA-256'larıyla MANIFEST.md yazar.
#      Uyarlama (BANC desteği, Y1–Y5 düzeltmeleri) Claude Code ile, TASINMA_LISTESI.md sırasıyla yapılır.
#   4. DEV_REPO verilirse veri dosyalarını (brain_model/, data/) kopyalar (cp -n: var olanın üzerine yazmaz).
#   5. .gitignore yazar, git deposunu başlatır ve ilk commit'i atar.
#
# Kullanım:
#   SYNAPTERA=~/synaptera DEV_REPO=~/<geliştirme-reposu> bash ~/synaptera/synaptera-banc-brain/yeni_proje/kur.sh
#   (isteğe bağlı) NEW=~/synaptera-banc-brain   hedef klasör (varsayılan bu)
set -euo pipefail

SYNAPTERA=${SYNAPTERA:?"SYNAPTERA: synaptera klonunun yolu (ör. ~/synaptera)"}
NEW=${NEW:-$HOME/synaptera-banc-brain}
DEV_REPO=${DEV_REPO:-}
HERE="$SYNAPTERA/synaptera-banc-brain"
TSV="$HERE/yeni_proje/tasinacaklar.tsv"

die() { echo "HATA: $*" >&2; exit 1; }
[ -f "$TSV" ] || die "$TSV yok; SYNAPTERA doğru mu ve main güncel mi (git pull)?"
[ -d "$SYNAPTERA/.git" ] || die "$SYNAPTERA bir git deposu değil"
if [ -e "$NEW" ] && [ -n "$(ls -A "$NEW" 2>/dev/null)" ]; then
    die "$NEW zaten var ve boş değil; karışmaması için durdum (başka bir NEW verin ya da klasörü kendiniz taşıyın)"
fi
SRC_COMMIT=$(git -C "$SYNAPTERA" rev-parse HEAD)
SRC_DIRTY=$(git -C "$SYNAPTERA" status --porcelain -- . ':!brain_model' ':!data' | wc -l)
[ "$SRC_DIRTY" -eq 0 ] || echo "UYARI: $SYNAPTERA içinde commit edilmemiş değişiklik var; MANIFEST commit $SRC_COMMIT'i gösterecek"

echo "[1/5] klasör düzeni: $NEW"
mkdir -p "$NEW"
for d in connectome engine sense motor body coupling tasks train prereg scripts/analysis configs tests docs/veri \
         vendor/synaptera_v1; do
    mkdir -p "$NEW/$d"
done

echo "[2/5] plan, analizler, CLAUDE.md"
cp -n "$HERE"/0*.md "$NEW/docs/"
cp -n "$HERE/README.md" "$NEW/docs/00_SYNAPTERA_ANALIZ_OZETI.md"
cp -n "$HERE"/veri/* "$NEW/docs/veri/"
cp -n "$HERE"/scripts/*.py "$NEW/scripts/analysis/"
cp -n "$HERE/yeni_proje/CLAUDE.md" "$NEW/CLAUDE.md"
cp -n "$SYNAPTERA/LICENSE" "$NEW/LICENSE"

echo "[3/5] Synaptera dosyaları -> vendor/synaptera_v1 (değiştirilmeden)"
MAN="$NEW/vendor/synaptera_v1/MANIFEST.md"
LIST="$NEW/TASINMA_LISTESI.md"
{
    echo "# vendor/synaptera_v1 — Synaptera v1.0.0'dan değiştirilmeden kopyalanan dosyalar"
    echo
    echo "Kaynak: https://github.com/omeruk/synaptera, commit \`$SRC_COMMIT\`. Bu dosyalar **referanstır**, içe aktarılmaz;"
    echo "yeni kod proje düzeninde yazılır ve her dosyanın başına kaynağı (yol + bu commit) not edilir."
    echo
    echo "| dosya | karar | hedef | SHA-256 |"
    echo "|---|---|---|---|"
} > "$MAN"
{
    echo "# Taşıma listesi"
    echo
    echo "Kaynak commit \`$SRC_COMMIT\`. Ayrıntılar ve gerekçeler: \`docs/06_YENI_PROJE_KURULUMU.md\`."
    echo "Sıra önemlidir (bağımlılık sırası). Her madde: uyarla → test → commit."
    echo
} > "$LIST"
n_copy=0
while IFS=$'\t' read -r order path decision target note; do
    [ "$order" = "order" ] && continue          # başlık
    [ -z "$path" ] && continue
    case "$decision" in
        take|adapt|pattern)
            src="$SYNAPTERA/$path"
            [ -f "$src" ] || die "TSV'deki dosya bulunamadı: $path"
            mkdir -p "$NEW/vendor/synaptera_v1/$(dirname "$path")"
            cp -n "$src" "$NEW/vendor/synaptera_v1/$path"
            sha=$(sha256sum "$src" | cut -d' ' -f1)
            echo "| \`$path\` | $decision | \`$target\` | \`${sha:0:16}…\` |" >> "$MAN"
            echo "- [ ] **$order.** \`$path\` → \`$target\` ($decision): $note" >> "$LIST"
            n_copy=$((n_copy + 1))
            ;;
        leave) ;;
        *) die "bilinmeyen karar '$decision' ($path)" ;;
    esac
done < "$TSV"
echo "    $n_copy dosya kopyalandı"

echo "[4/5] veri"
if [ -n "$DEV_REPO" ]; then
    [ -d "$DEV_REPO/brain_model" ] || die "$DEV_REPO/brain_model yok"
    mkdir -p "$NEW/brain_model" "$NEW/data"
    cp -rn "$DEV_REPO/brain_model/." "$NEW/brain_model/"
    find "$DEV_REPO/data" -maxdepth 1 -type f -exec cp -n {} "$NEW/data/" \;
    echo "    brain_model/ ve data/ kopyalandı ($DEV_REPO); Codex indirmeleri yerinde kalır (--codex-dir)"
else
    echo "    DEV_REPO verilmedi: veri adımı atlandı (sonra: DEV_REPO=... ile tekrar değil, elle cp -n)"
fi

echo "[5/5] git"
cat > "$NEW/.gitignore" <<'EOF'
# veri (asla commit edilmez; scripts/fetch_data.py ile indirilir)
brain_model/
data/
banc/
runs/
*.h5
*.npz
*.parquet
*.feather
# çıktı
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
commit and SHA-256), porting checklist in TASINMA_LISTESI.md."
echo
echo "Hazır: $NEW ($(git rev-parse --short HEAD))"
echo "Sonraki adımlar:"
echo "  1. GitHub'da boş bir repo açın: omeruk/synaptera-banc-brain (README/licence eklemeden)"
echo "  2. cd $NEW && git remote add origin https://github.com/omeruk/synaptera-banc-brain.git && git push -u origin main"
echo "  3. conda activate neurofly && claude   (ilk istek: docs/06_YENI_PROJE_KURULUMU.md §4)"
