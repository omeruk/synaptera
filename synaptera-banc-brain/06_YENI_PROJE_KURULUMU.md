# 06 — Yeni proje kurulumu: synaptera-banc-brain

Tarih: 2026-10-12. Karar: Synaptera v1.0.0 **donmuş arşiv** olarak kalır; sonraki çalışma (`05_MIMARI_PLAN.md`) yeni
bir klasör ve yeni bir repoda (`omeruk/synaptera-banc-brain`) yürür. v1'deki hatalar (Y1–Y5, O1–O10, D1–D9;
`01_KOD_INCELEMESI.md`) eski repoya yamanmaz, yeni kodun tasarımına baştan girer.

Kurulum paketi: `yeni_proje/kur.sh` (betik), `yeni_proje/tasinacaklar.tsv` (taşıma listesi, tek kaynak),
`yeni_proje/CLAUDE.md` (yeni reponun kalıcı kuralları).

## 1. Kurulum (sizin bilgisayarınızda, bir kez)

```bash
cd ~/synaptera && git pull origin main
SYNAPTERA=~/synaptera DEV_REPO=<geliştirme-reposunun-yolu> bash synaptera-banc-brain/yeni_proje/kur.sh
```

Betik:
1. `~/synaptera-banc-brain` klasörünü plandaki düzenle açar (`connectome/ engine/ sense/ motor/ body/ coupling/
   tasks/ train/ prereg/ scripts/ configs/ tests/ docs/`). Klasör varsa ve doluysa **durur**.
2. Bu klasördeki belgeleri `docs/`, analiz betiklerini `scripts/analysis/`, `CLAUDE.md`'yi köke koyar.
3. `tasinacaklar.tsv`'deki 52 dosyayı **değiştirmeden** `vendor/synaptera_v1/` altına kopyalar; `MANIFEST.md`
   kaynak commit'i ve her dosyanın SHA-256'sını yazar; `TASINMA_LISTESI.md` sıralı kontrol listesini üretir.
4. `brain_model/` ve `data/`'yı geliştirme reposundan kopyalar (`cp -n`, üzerine yazmaz). Codex indirmeleri
   `~/Downloads`'ta kalır.
5. `.gitignore` yazar, `git init` ve ilk commit (sizin git kimliğinizle).

Sonra:
```bash
# GitHub'da boş repo: omeruk/synaptera-banc-brain (README/lisans EKLEMEDEN)
cd ~/synaptera-banc-brain
git remote add origin https://github.com/omeruk/synaptera-banc-brain.git && git push -u origin main
conda activate neurofly && claude
```

Bu ortamda (bulut) deneme klasöründe doğrulandı: 52 dosya, manifest, kontrol listesi, veri kopyası, ilk commit;
ikinci çalıştırmada "klasör dolu" diye durdu.

## 2. Taşıma ilkesi

| karar | anlamı | sayı |
|---|---|---|
| `take` | olduğu gibi alınır (yalnız import yolu) | 3 |
| `adapt` | alınır ve uyarlanır (BANC desteği, v1 hatalarının düzeltmesi, eski bayrakların silinmesi) | 35 |
| `pattern` | kod kopyalanmaz, tasarım/desen yeniden kullanılır | 14 |
| `leave` | taşınmaz | gerisi |

`vendor/synaptera_v1/` yalnız **referanstır**, içe aktarılmaz. Yeni dosya yazılınca başına
`# Ported from synaptera@<commit>:<yol>` notu konur; taşıma bitince `vendor/` silinebilir (MANIFEST kalır).

**Taşınmayanlar ve nedeni:**
- NeuroFly'dan uyarlanan parçalar (Synaptera `docs/ADAPTED_CODE.md`): eski grup kuralı ve `neuron_positions`
  (`groups.py`), koku dönüş haritası `turn_hand` (`hybrid.py`), `LoomBias` (`sensors.py`) ve ilgili sabitler — lisans
  durumu belirsiz ve BANC projesinde gereksiz.
- Eski bayraklar ve yollar: `inputs="legacy"`, `--asc-legacy`, tüm-DN dönüş okuması, DNp15 post-hoc seçimi.
- v1.0.0'a özgü: `run_*.sh`, `scripts/diag/*`, rapor/şekil/medya betikleri (`make_figures`, `make_media`,
  `make_public_snapshot`, `make_data_bundle`, `check_*`), `render_flight_video.py`, `render_flight_compare.py`,
  `generate_flight_plots.py`, `flight/controller.py` (desen olarak), `tests/flight/test_adapted_spec.py`,
  `test_controller.py`, `test_leg_grn.py`, `test_nt_*`.
- Raporlar, SPEC'ler, şekiller, medya: kopyalanmaz; v1 reposuna bağlantı verilir.

Tam liste, hedef yollar ve dosya başına notlar: `yeni_proje/tasinacaklar.tsv`.

## 3. Taşıma sırası (bağımlılık sırası)

1. **connectome/** — ortak şema, FlyWire 783 adaptörü, crosswalk, işaret kuralları, QA (simetri kapısı).
2. **engine/** — `NeuralEngine` arayüzü, Shiu-LIF (Brian2), gecikmesiz Poisson girdisi; `third_party/` altında
   hash'li `model.py`.
3. **body/** — `ArenaSpec`, FlyGym gövdesi, kanat modeli (genlik sınırı), gürültü.
4. **sense/** — FlyVis görme + sınır katmanı (koku ertelendi).
5. **motor/** — okumalar (ön-kayıtlı tipler), el yapımı köprü ve refleksler **kontrol kolu** olarak.
6. **coupling/** — nedensel komut kuyruğu, kayıt (üzerine yazma koruması), tekrar oynatma.
7. **tasks/**, **train/**, **scripts/**, **tests/**.

**İlk kabul testi (F0 karşılığı):** yeni kodla FlyWire üzerinde, el yapımı köprü kolu ve komut gecikmesi = 0 ayarıyla
v1'in n1 uçuşu yeniden üretilir (S1 ✓, S2 ✓; konum izi v1 HDF5 kaydıyla karşılaştırılır). Sonra gecikme = 1 aralık
(nedensel) ile aynı uçuş koşulur ve fark raporlanır. Bu geçmeden BANC'e (F1) geçilmez.

## 4. Terminalde ilk istek (Claude Code'a)

> `CLAUDE.md`'yi ve `docs/05_MIMARI_PLAN.md`, `docs/06_YENI_PROJE_KURULUMU.md`'yi oku. `TASINMA_LISTESI.md`'yi sırayla
> uygula: her madde için `vendor/synaptera_v1/`'deki özgün dosyadan hedef konuma uyarlanmış kodu yaz, testini ekle,
> testleri çalıştır, maddeyi işaretle ve commit et. `connectome/` ve `engine/` bitince dur ve bana özet ver.
> NeuroFly'dan uyarlanmış parçaları taşıma; `main`'e doğrudan değil `omeruk/tasima-1` dalına commit et.

Sonraki istekler (her biri ayrı dal + PR):
1. "Taşımaya devam et: `body/`, `sense/`, `motor/`, `coupling/`; sonra §3'teki ilk kabul testini çalıştır."
2. "F1: BANC 888'i Dataverse'ten indir (hash'le), `connectome/adapters/banc888.py` ve crosswalk'u yaz, QA raporunu üret."
3. "F2 ön-kaydı: `05_MIMARI_PLAN.md` F2'deki 5 açık döngü testinin kriterlerini `prereg/`'e yaz; koşmadan önce bana göster."
