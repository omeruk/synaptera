> **Lab notebook, in Turkish.** Working record of this project, kept as written during the work (moved here from the repository root for the public snapshot). The English consolidated report is [REPORT.md](../../REPORT.md); the English summary is the [README](../../README.md).

# REPORT_SENSORY_A2 — koku kalıcı durumunun kaynağı ve literatür NT işaretleri

Önceki tur: REPORT_SENSORY_A.md. Orada `--olfaction-full` ile iki APL varyantı da B-K2'de (girdi kesildikten sonra ağın susması) kaldı, koku tam koşuda yalnız besin glomerülleriyle kullanıldı.
Bu tur: kalıcı durumu taşıyan nöron tipleri, bu tiplerin literatürdeki nörotransmitteri, ve yalnız literatür kaynaklı işaret ataması (`--nt-literature`) ile Aşama A smoke'larının tekrarı. Kazanç, eşik ya da hız ayarı yok. Tam koşu ve DNp15 kalibrasyonu yok.

## Özet
1. **Teşhis:**
   - Kalıcı durum AL'nin LN/PN çekirdeğinde: döngü çıkışının %60–73'ü.
   - Codex NT tahmini olmayan ya da düşük güvenli 428 nöron, döngü çıkışının %27 (spiking) / %38'ini (graded) veriyor; neredeyse hepsi modelde uyarıcı.
   - En büyük tek katkıcı lLN1_bc: 30 nöron, %6.9 / %9.8.
2. **Literatür:**
   - lLN1_bc literatürde **kolinerjik**: Shang et al. 2007; Eckstein et al. 2024 tartışması; Huang et al. 2010; güven orta. Modeldeki uyarıcı işaret zaten bu.
   - Döngüdeki 775 tipin 370'inin literatür NT'si var (Schlegel et al. 2024 derlemesi). Bunların yalnız 8 tipinde (24 nöron) model literatürle çelişiyor.
   - lLN2X/lLN2F/v2LN30 gibi kaynaksız tiplere dokunulmadı.
3. **Kural:** `--nt-literature`, varsayılan kapalı. `w = |w| · sign_lit`; kazanç, eşik ve hız değişmiyor. SPEC §3.2c'ye koşudan önce yazıldı.
4. **Test:**
   - Kalıcı durum küçüldü ama kalmadı. Tüm girdiler 0 iken ağ 3.45 → 2.45 Hz (spiking), 1.95 → 1.54 Hz (graded). Besin glomerülleriyle de aynı.
   - **B-K2 dört yapılandırmanın dördünde de kaldı.** Spiking ayrıca (ii) ve B-K1'de kaldı.
5. **Karar:** hiçbiri geçmedi; **koku final'de kapalı kalır** (final_sB yapılandırması). Tam koşu yapılmadı.

## 1. Teşhis (yalnız okuma; `scripts/diag/sa2_diag.py`)

**Veri:** Aşama A smoke'ları, yeniden koşulmadı.
- v17 (spiking APL) ve v18 (graded APL): `--n-steps 20 --persist-steps 40 --hybrid --vision-boundary --olfaction-full --ablate-dn DNp15 --seed 3`.
- **Kesme penceresi:** 40 kesme adımının son 20'si, yani tüm Poisson girdileri 0 iken kesmeden 500–1000 ms sonra. Bu pencerede ≥1 spike atan nöron "döngüye katılıyor" sayıldı.
  - spiking: 8,223 aktif nöron, ağ ort. 3.45 Hz.
  - graded: 4,672 aktif nöron, ağ ort. 1.95 Hz.
- **Tip:** `flywire_annotations.tsv` `cell_type`. Yoksa `hemibrain_type`, o da yoksa `[cell_class]`. Nöropil = baskın nöropil (`data/neuron_neuropil.npz`).
- **Ölçüler:**
  - **spike %:** tipin kesme penceresindeki spike'larının tüm ağın spike'larına oranı.
  - **döngü çıkışı %:** Σ (sinaps sayısı × presinaptik hız), yalnız kesmede aktif hedeflere giden sinapslar üzerinden, tüm ağın aynı toplamına oranı. İşaretsiz: uyarıcı ve inhibitör çıkışın ikisi de sayılır. Döngüyü kimin "beslediğinin" kaba ölçüsü. Nedensellik değil.
- **NT alanları:**
  - Codex v783 `neurons.csv`: `nt_type` ve `nt_type_score`, yani Eckstein et al. 2024 tahmini. NaN = tahmin yok, skor 0.
  - Model işareti = `Connectivity_783.parquet` `Excitatory`, yani Shiu konvansiyonu: yalnız GABA/Glu tahmini −; NaN dahil diğer her şey +.

### 1.1 Döngü nerede
| baskın nöropil | spiking: kesmede aktif / spike % / döngü çıkışı % | graded: aynı |
|---|---|---|
| AL | 1,028 / 22.9 / 59.8 | 1,020 / 38.7 / 73.0 |
| LH | 1,585 / 22.8 / 12.9 | 1,508 / 35.8 / 15.2 |
| MB_CA (KC dendritleri) | 3,389 / 35.8 / 9.4 | 481 / 5.4 / 2.2 |
| MB lobları (ML/PED/VL) | 136 / 2.4 / 8.1 | 5 / 0.2 / 0.7 |
| diğer | 2,085 / 16.2 / 9.8 | 1,658 / 20.0 / 9.0 |

- Döngü çıkışının %60–73'ü AL'de. Graded APL, KC'leri ve MB'yi büyük ölçüde susturuyor; AL/LH çekirdeği aynı kalıyor (AL ~1,020 aktif nöron, iki varyantta da).
- ORN'ler kesmede neredeyse sessiz (spike'ların %2.7 / %4.5'i). Yani durum girdiden değil, AL içi yerel nöronlardan (LN) ve PN'lerden geliyor.

### 1.2 NT tahmini olmayan ya da düşük güvenli tipler
AL/LH/MB'de ORN dışı nöronlar, Codex sınıfına göre:

| Codex sınıfı | n | kesmede aktif (s / g) | spike % (s / g) | döngü çıkışı % (s / g) | bunun + işaretli kısmı (s / g) |
|---|---|---|---|---|---|
| nt_type NaN | 279 | 199 / 197 | 6.3 / 10.8 | 16.7 / 23.7 | 15.1 / 21.4 |
| skor < 0.5 | 149 | 123 / 114 | 4.1 / 6.7 | 10.4 / 14.6 | 9.4 / 13.4 |
| skor ≥ 0.5 | 7,935 | 5,477 / 2,366 | 70.7 / 58.0 | 62.4 / 51.8 | 43.0 / 34.3 |

- Sayıca %5'ten az olan bu 428 nöron, döngü çıkışının %27 (spiking) / %38'ini (graded) veriyor. Neredeyse tamamı modelde uyarıcı. Hepsi kesmede 250–300 Hz'e yakın ateşliyor.
- Döngü çıkışı ≥ %0.2 olan NaN / düşük güvenli tipler aşağıda (s = spiking v17, g = graded v18). Toplamları: döngü çıkışının %26.2'si (s) / %37.0'si (g).

| tip | n | nöropil | Codex nt_type (medyan skor) | model işareti | kesmede aktif s/g | Hz s / g | spike % s / g | döngü çıkışı % s / g |
|---|---|---|---|---|---|---|---|---|
| **lLN1_bc** | 30 | AL | NaN29 / SER1 (0.00) | + | 30/30 | 292 / 287 | 1.83 / 3.19 | **6.86 / 9.81** |
| lLN2X12 | 13 | AL | NaN7 / ACH6 (0.00) | + | 13/13 | 255 / 253 | 0.69 / 1.22 | 2.03 / 2.93 |
| lLN2X03 | 6 | AL | SER5 / NaN1 (0.36) | + | 6/6 | 289 / 288 | 0.36 / 0.64 | 1.68 / 2.43 |
| lLN2F_a | 4 | AL | NaN2 / GABA2 (0.18) | + | 4/4 | 286 / 281 | 0.24 / 0.42 | 1.51 / 2.16 |
| v2LN30 | 2 | AL | NaN2 (0.00) | + | 2/2 | 302 / 297 | 0.13 / 0.22 | 1.39 / 1.98 |
| lLN2X04 | 4 | AL | NaN2 / GABA2 (0.19) | + | 4/4 | 284 / 280 | 0.24 / 0.42 | 1.24 / 1.79 |
| lLN2T_c | 4 | AL | SER4 (0.35) | + | 4/4 | 286 / 278 | 0.24 / 0.41 | 1.13 / 1.60 |
| il3LN6 | 2 | AL | NaN2 (0.00) | + | 2/2 | 292 / 289 | 0.12 / 0.21 | 1.11 / 1.59 |
| lLN2T_b | 4 | AL | NaN4 (0.00) | + | 4/4 | 262 / 255 | 0.22 / 0.38 | 1.06 / 1.50 |
| lLN2X11 | 4 | AL | SER4 (0.41) | + | 4/4 | 270 / 266 | 0.23 / 0.39 | 1.06 / 1.51 |
| lLN2P_b | 12 | AL | NaN8 / GABA4 (0.00) | + | 12/12 | 254 / 251 | 0.64 / 1.11 | 0.94 / 1.34 |
| lLN2X05 | 4 | AL | SER3 / NaN1 (0.37) | + | 4/4 | 282 / 276 | 0.24 / 0.41 | 0.91 / 1.30 |
| lLN2T_e | 4 | AL | SER2 / NaN2 (0.17) | + | 4/4 | 283 / 278 | 0.24 / 0.41 | 0.86 / 1.24 |
| lLN2P_a | 13 | AL | NaN10 / GLUT3 (0.00) | −/+ | 13/13 | 252 / 247 | 0.69 / 1.19 | 0.77 / 1.09 |
| lLN1_a | 3 | AL | SER3 (0.42) | + | 3/3 | 288 / 285 | 0.18 / 0.32 | 0.68 / 0.98 |
| lLN2X10 | 4 | AL | ACH4 (0.46) | + | 4/4 | 220 / 216 | 0.18 / 0.32 | 0.46 / 0.65 |
| AL-MBDL1 | 2 | AL | NaN2 (0.00) | −/+ | 2/2 | 135 / 149 | 0.06 / 0.11 | 0.41 / 0.65 |
| MBON05 | 2 | MB_ML | NaN1 / GLUT1 (0.28) | −/+ | 2/0 | 250 / 0 | 0.10 / 0.00 | 0.37 / 0.00 |
| lLN2X02 | 6 | AL | GABA6 (0.49) | − | 6/6 | 145 / 144 | 0.18 / 0.32 | 0.32 / 0.46 |
| lLN2X07 | 3 | AL | ACH3 (0.48) | + | 3/3 | 213 / 212 | 0.13 / 0.24 | 0.26 / 0.38 |
| lLN2X06 | 3 | AL | ACH2 / NaN1 (0.42) | + | 3/3 | 193 / 191 | 0.12 / 0.21 | 0.23 / 0.33 |
| v2LN3A1_b | 8 | AL | NaN6 / ACH2 (0.00) | + | 8/8 | 120 / 122 | 0.20 / 0.36 | 0.21 / 0.32 |
| CB3417 | 7 | AL | NaN5 / GLUT2 (0.00) | −/+ | 7/7 | 172 / 171 | 0.25 / 0.44 | 0.17 / 0.25 |
| LHAV4a1_b | 8 | LH | GABA6 / GLUT1 / NaN1 (0.67) | − | 8/8 | 142 / 122 | 0.24 / 0.36 | 0.17 / 0.21 |
| ALBN1 | 2 | AL | NaN1 / GLUT1 (0.22) | − | 2/2 | 196 / 191 | 0.08 / 0.14 | 0.17 / 0.24 |
| CB1676 | 4 | AL | NaN3 / ACH1 (0.00) | −/+ | 4/4 | 152 / 150 | 0.13 / 0.22 | 0.16 / 0.23 |

Karşılaştırma için güvenli tahminli en büyük katkıcılar (s / g):
- APL: GABA, −; döngü çıkışı 5.21 / 0.70.
- KCg-m: ACh, +; 3.11 / 0.08.
- KCab: ACh, +; 2.70 / 0.02.
- lLN2F_b: GABA, −; 2.44 / 3.52.
- DP1m_adPN: ACh, +; 2.26 / 2.16.
- lLN2P_c: GABA, −; 1.36 / 1.93.

**Okuma:**
- Kalıcı durumun çekirdeği, AL'deki lateral LN'ler (lLN1/lLN2 aileleri) ve PN'ler. Hepsi kesmede ~250–300 Hz'de, yani refrakter sınırına yakın.
- En büyük tek katkıcı yine **lLN1_bc**: 30 nöron, döngü çıkışının %6.9 / %9.8'i, modelde uyarıcı. Bu, SPEC_BRAIN_CONTROL Adım 0'daki bulguyla aynı.
- Tablo yalnız betimleyici. Bir tipin işaretini değiştirmenin döngüyü kırıp kırmayacağını göstermez.

## 2. Literatür: döngü tiplerinin nörotransmitteri

### 2.1 Kaynak ve yöntem (`scripts/make_nt_literature.py` → `data/nt_literature_783.csv`)
- **Birincil tablo:** `brain_model/flywire_annotations.tsv` içindeki `known_nt` / `known_nt_source` sütunları. Bunlar Schlegel et al. 2024'ün (*Nature* 634:139) literatür derlemesi; her tip için birincil yayını ve yöntemi (immuno, TAPIN, EASI-FISH, scRNA-seq, soy hattı) adlandırıyor.
  - Repo'da zaten var; yeni bağımlılık ya da indirme yok.
- **Kapsam:** §1'deki döngüye katılan 775 tip (AL/LH/MB, ORN değil, v17 ya da v18 kesme penceresinde ≥1 spike). `[sınıf]` yer tutucuları hariç.
  - Bunların **370'inin** literatür NT'si var. Kalan tipler için kaynak yok ve **dokunulmadı**.
- **İşaret kuralı** (koşmadan önce sabit; §3, SPEC §3.2c):
  - Yalnız hızlı vericiler sayılır: ACh → +, GABA → −, Glu → −. Bu, modelin kendi NT→işaret eşlemesi; değişmedi.
  - Tipin `known_nt`'sinde tam bir hızlı verici varsa o işaret atanır. "-negative" girdileri, peptitler, NO ve aminler yok sayılır.
  - Hiç hızlı verici yoksa (yalnız DA/5-HT/OA ya da yalnız "gaba-negative"), birden fazlaysa (ör. "acetylcholine, glutamate") ya da tipin her nöronu aynı `known_nt`'yi taşımıyorsa: işaret yok, dokunulmaz.
  - Sonuç: 272 tipe işaret atandı, 98 tip belirsiz.
- **Güven** (yalnız raporlanır, kuralda kullanılmaz):
  - **orta:** kanıt yalnız scRNA-seq ya da soy hattı / trakt tabanlı; veya tip, Shang et al. 2007 kolinerjik eLN'lerine morfolojiyle eşlenmiş.
  - **yüksek:** tanımlı tipte immuno / TAPIN / EASI-FISH / RNAi / kesişim.
  - Dağılım: 182 yüksek, 188 orta.
- **Doğrulama sınırı:**
  - Schlegel derlemesindeki birincil yayınların hepsi bu turda tek tek yeniden okunmadı.
  - Metinden doğrulanan yalnız lLN1_bc (§2.2). İşaret değiştiren tiplerin kaynağı derlemedeki atıftır.

### 2.2 lLN1_bc ve kullanıcının saydığı kaynaklar
- **lLN1_bc** (30 nöron, Codex NaN; `top_nt` DA 12 / ACh 11 / 5-HT 7):
  - Schlegel 2024: ACh (Shang et al. 2007, immuno).
  - Eckstein et al. 2024 (*Cell* 187:2574) tartışma bölümü, metinden okundu (Europe PMC PMC11106717):
    - 'ALl1 dorsal' soy hattındaki tek taraflı, "broad" (pan-glomerüler) LN'ler, tahmin edilen kolinerjik LN'lerle örtüşüyor.
    - "Positioned closely among them are other local lLN1_bc neurons that are predicted to be dopaminergic."
    - Yazarlar bu LN'lerde DA/5-HT bildirilmediğini, bunların "mostly … GABAergic or cholinergic, perhaps mostly the latter" olması gerektiğini yazıyor. Kaynak olarak Shang et al. 2007 ve Huang et al. 2010 (*Neuron* 67:1021) gösteriliyor.
  - **Sonuç: literatür lLN1_bc için kolinerjik (uyarıcı) diyor; güven orta.** Gerekçe: tip eşlemesi morfolojiye dayanıyor, ve Shang 2007 / Huang 2010 eLN'lerinin PN'lere etkisi kısmen elektriksel.
  - **Modeldeki işaret (+) zaten bu. `--nt-literature` lLN1_bc'yi değiştirmez.**
  - Not: bir web aramasının özet metninde "lLN1_bc … curated GABAergic … signed GABAergic because … self-excitation" cümlesi çıktı. Kaynağı bulunamadı; Dorkenwald 2024, Pospisil 2024, Shiu 2024, Schlegel 2024, Lin 2024 ve Matsliah 2024 tam metinlerinde (Europe PMC) "lLN1" geçmiyor. **Kullanılmadı.**
- **Wilson & Laurent 2005, Chou et al. 2010:**
  - Sınıf düzeyinde bilgi veriyorlar: AL LN'lerinin çoğu GABAerjik; bir kısmı kolinerjik ya da glutamaterjik (GABA-negatif); Glu, GluClα ile inhibitör (Liu & Wilson 2013).
  - FlyWire tipine eşleme vermedikleri için tek başına hiçbir tipe işaret atamak için kullanılmadı.
- **Task et al. 2022** (*eLife* 11:e72599): reseptör ko-ekspresyonu. LN/PN nörotransmitteri vermiyor; kullanılmadı.
- **Eckstein et al. 2024 NT tahmini:** zaten modeldeki işaretin kaynağı, Codex `nt_type`. Tahmin literatür sayılmadı. Yalnız tartışma metnindeki literatür atıfı (lLN1_bc) kullanıldı.

### 2.3 §1 tablosundaki NaN / düşük güvenli tipler: literatür
| tip | known_nt | kaynak | güven | model → `--nt-literature` |
|---|---|---|---|---|
| lLN1_bc | acetylcholine | Shang et al. 2007 (immuno); Eckstein et al. 2024 tartışma; Huang et al. 2010 | orta | + → + (değişmez) |
| lLN2X03 | acetylcholine | Shang et al. 2007 (immuno) | orta | + → + |
| lLN2T_c | acetylcholine | Shang et al. 2007 (immuno) | orta | + → + |
| lLN2T_b | acetylcholine | Shang et al. 2007 (immuno) | orta | + → + |
| **il3LN6** | gaba | Tanaka et al. 2012 (immuno) | yüksek | **+ → −** |
| **lLN2P_b** | gaba, MIP; ACh-negatif | Sizemore et al. 2023 (immuno); Croset et al. 2018 (scRNA-seq) | yüksek | **+ → −** |
| **MBON05** | glutamate | Aso et al. 2014 (immuno) | yüksek | **−/+ → −** |
| LHAV4a1_b | gaba | Dolan et al. 2019 (immuno) | yüksek | − → − |
| lLN2X12, lLN2F_a, v2LN30, lLN2X04, lLN2X11, lLN2X05, lLN2T_e, lLN2P_a, lLN1_a, lLN2X10, AL-MBDL1, lLN2X02, lLN2X07, lLN2X06, v2LN3A1_b, CB3417, ALBN1, CB1676 | – | kaynak yok | – | dokunulmadı |

### 2.4 İşareti değişen tüm tipler (8 tip, 24 nöron)
Döngü çıkışı = §1'deki pay, s = spiking (v17) / g = graded (v18).

| tip | n | literatür hızlı NT | kaynak (Schlegel 2024 derlemesi) | güven | model → literatür | değişen nöron | döngü çıkışı % s / g |
|---|---|---|---|---|---|---|---|
| il3LN6 | 2 | GABA | Tanaka et al. 2012 (immuno) | yüksek | + → − | 2 | 1.11 / 1.59 |
| lLN2P_b | 12 | GABA | Sizemore et al. 2023; Croset et al. 2018 | yüksek | + → − | 12 | 0.94 / 1.34 |
| DPM | 2 | GABA (+5-HT) | Lee 2011; Waddell 2000; Haynes 2015 (immuno); Aso 2019 | yüksek | + → − | 2 | 0.68 / 0.00 |
| MBON05 | 2 | Glu | Aso et al. 2014 (immuno) | yüksek | −/+ → − | 1 | 0.37 / 0.00 |
| v2LN36 | 2 | Glu | Chou et al. 2022 (immuno) | yüksek | + → − | 2 | 0.14 / 0.21 |
| LHPV6o1 | 2 | ACh | Dolan et al. 2019 (immuno) | yüksek | − → + | 2 | 0.04 / 0.05 |
| PPL203 | 2 | GABA (+DA) | Mao & Davis 2009; Niens 2017 (immuno); Aso 2019 | yüksek | + → − | 2 | 0.01 / 0.02 |
| DN1a | 4 | Glu | Reinhard 2023; Ma 2021 (scRNA-seq) | orta | −/+ → − | 1 | 0.00 / 0.00 |

- **Toplam döngü çıkışı payı:** spiking %3.3, graded %3.2. Bunun %2.1 / %2.9'u AL'deki üç LN tipinden (il3LN6, lLN2P_b, v2LN36), ki bunlar uyarıcıdan inhibitöre dönüyor.
- **Beklenti (koşmadan önce yazıldı):** döngünün en büyük kaynağı lLN1_bc ve kaynaksız lLN2 tiplerinin (~%20) işareti değişmiyor. Bu yüzden B-K2'yi geçmesi olası değil. Bu bir tahmindir; ölçüt §4'te ölçülür.

## 3. Test (`--nt-literature`; SPEC §3.2c; tam beyin, ayar yok)

**Uygulanan değişiklik** (her koşuda aynı; `meta/nt_literature`):
- 272 tip, 6,221 nöron tabloda.
- İşareti değişen: 24 nöron, 19,977 kenar. Bunlar 78,317 sinapsın uyarıcıdan inhibitöre, 3,704 sinapsın inhibitörden uyarıcıya dönmesi demek.
- Değişen tipler: il3LN6, lLN2P_b, v2LN36, DPM, PPL203, MBON05, DN1a, LHPV6o1.
- Diğer bütün sinapslar parquet ile aynı; `tests/flight/test_nt_literature.py` bunu DEV alt-ağında doğruluyor.

### 3.1 Açık döngü (`scripts/diag/sa_criteria.py … --nt-literature [--food-only]`; seed 0/1/2)
Protokol §3.2b ile aynı. Besin glomerülleri varyantında (BS/BG) sürülen ORN'ler `orn_food` (298; S/P 8 Hz, O 150 Hz). Bu yüzden diğer 1,977 ORN, BS/BG'de "AL" ortalamasının içinde ve sessiz; AL tabanı bu nedenle düşük.

| ölçüt | FS: tam koku, spiking | FG: tam koku, graded | BS: besin, spiking | BG: besin, graded |
|---|---|---|---|---|
| (i) AL taban → 1.0–1.5 s, Hz | 100.1→100.7 / 100.4→100.3 / 100.4→100.2 ✓✓✓ | 95.4→95.4 / 95.1→95.0 / 95.3→95.4 ✓✓✓ | 29.6→29.6 / 29.4→29.6 / 29.5→29.6 ✓✓✓ | 28.1→28.1 / 28.1→28.1 / 28.1→28.0 ✓✓✓ |
| (i) KC taban → 1.0–1.5 s, Hz | 22.2→22.3 / 22.4→22.3 / 22.1→22.4 ✓✓✓ | 1.63→1.60 / 1.61→1.62 / 1.61→1.61 ✓✓✓ | 20.8→20.9 / 20.6→20.6 / 20.6→20.6 ✓✓✓ | 1.57→1.57 / 1.57→1.57 / 1.56→1.56 ✓✓✓ |
| (ii) KC ≥1 spike, koku 250–1000 ms (%5–15) | 59.1 / 58.9 / 58.8 % **✗✗✗** | 8.1 / 8.0 / 8.1 % ✓✓✓ | 56.3 / 56.5 / 56.3 % **✗✗✗** | 7.9 / 8.0 / 7.9 % ✓✓✓ |
| (iii) MN9 adım 0–139 (< 10 Hz) | 0.00 ✓✓✓ | 0.00 ✓✓✓ | 0.00 ✓✓✓ | 0.00 ✓✓✓ |
| K1 sürülmeyen ort. · son/ilk · en yüksek nöropil | 2.72 · 1.03 · LH 40.7 ✓✓✓ | 1.65 · 1.02 · AL 37.8 ✓✓✓ | 2.56 · 1.03 · LH 39.1 ✓✓✓ | 1.58 · 1.02 · LH 34.3 ✓✓✓ |
| kayıt: tüm girdiler 0, 100–200 ms ağ | 2.45 / 2.46 / 2.44 Hz | 1.55 / 1.53 / 1.56 Hz | 2.45 / 2.43 / 2.46 Hz | 1.54 / 1.55 / 1.53 Hz |
| kayıt: X 500–1000 ms, AL / KC / LH (s0) | 97.2 / 20.3 / 38.4 | 92.4 / 1.56 / 33.5 | 29.4 / 20.3 / 38.3 | 28.0 / 1.56 / 33.5 |
| Aşama A, bayraksız (REPORT_SENSORY_A §3.1): X 100–200 ms | 3.44–3.48 Hz | 1.94–1.95 Hz | – | – |

DN'ler (s0; S son 500 ms | koku | kesme 1.0–1.5 s; L/R Hz):
- FS: DNa02 34/4 | 60/0 | 40/2; DNp10 40/0 | 35/0 | 42/0.
- FG: DNa02 52/18 | 49/1 | 34/12; DNp10 40/0 | 32/0 | 40/0.
- DNp15 ve DNp01 her yerde 0. Kokuyla belirgin, tutarlı bir değişim yok.

### 3.2 Smoke (kapalı döngü; `--n-steps 20 --persist-steps 40 --hybrid --vision-boundary --ablate-dn DNp15 --seed 3 --no-video --nt-literature` [+ `--olfaction-full`] [+ `--apl-graded`]; `scripts/diag/sa2_report.py`)

| ölçüt | FS v20 | FG v21 | BS v22 | BG v23 |
|---|---|---|---|---|
| B-K1 sürülmeyen ort. < 5 Hz · son/ilk · en yüksek nöropil | **5.44 ✗** · 1.02 · LH 40.2 | 4.07 ✓ · 1.01 · UNASGD 37.5 | **5.18 ✗** · 1.01 · LH 38.6 | 3.93 ✓ · 1.03 · LH 33.7 |
| B-K2 1 s kesme, son 200 ms < 0.1 Hz | **2.44 ✗** (hiç 0.1 altına inmedi) | **1.53 ✗** (hiç) | **2.46 ✗** (hiç) | **1.53 ✗** (hiç) |
| B-K3 adım / RSS | 0.98 s / 3.52 GB ✓ | 1.02 s / 3.51 GB ✓ | 0.97 s / 3.51 GB ✓ | 1.00 s / 3.51 GB ✓ |
| B-K4 temassız MN9 | 0.00 Hz ✓ | 0.00 Hz ✓ | 0.00 Hz ✓ | 0.00 Hz ✓ |
| perch ağ ort. | 10.33 Hz | 9.45 Hz | 10.07 Hz | 9.21 Hz |
| Aşama A, bayraksız: B-K2 (B-K1) | v17: 3.46 (6.60) | v18: 1.95 (4.46) | v19 tam koşu: 3.4 (6.94) | – |

Dosyalar: `simulations/flight_v2{0,1,2,3}_hybrid_[sA_]sB_ablDN-DNp15[_aplG]_ntLit_smoke_sA2_data.h5`.

**Okuma:**
- **Literatür işaretleri kalıcı durumu küçültüyor ama kaldırmıyor.**
  - Tüm girdiler sıfırken ağ hızı spiking'de 3.45 → 2.45 Hz, graded'de 1.95 → 1.54 Hz.
  - Açık döngü AL tabanı 121 → 100 Hz (spiking), 116 → 95 Hz (graded).
  - KC seyrekliği spiking'de %68 → %59. Hâlâ aralığın çok dışında.
- **Kalıcılık girdi setinden bağımsız.** Besin glomerülleri varyantı (298 ORN), tam kokuyla (2,275 ORN) aynı kesme hızına oturuyor: 2.45 / 1.54 Hz. Yani durum, AL'de bir kez tetiklendikten sonra kendini sürdürüyor; girdi büyüklüğü belirleyici değil.
- **Kalanın kaynağı:** döngüyü taşıyan lLN1_bc ve kaynağı olmayan lLN2/v2LN tipleri (§1'deki döngü çıkışının ~%20'si) bu kuralla değişmedi. lLN1_bc'nin kendisi literatürde zaten uyarıcı (§2.2).
- **Spiking APL, (ii) ve B-K1'de yine kalıyor.** Graded APL, (i)–(iii) ve B-K1'i geçiyor. Hepsi yalnız B-K2'de kalıyor.

## 4. Karar (mekanik, SPEC §3.2c)
| yapılandırma | (i) | (ii) | (iii) | B-K1 | B-K2 | geçer mi |
|---|---|---|---|---|---|---|
| FS: tam koku, spiking | 3/3 | 0/3 | 3/3 | ✗ | ✗ | hayır |
| FG: tam koku, graded | 3/3 | 3/3 | 3/3 | ✓ | ✗ | hayır |
| BS: besin glomerülleri, spiking | 3/3 | 0/3 | 3/3 | ✗ | ✗ | hayır |
| BG: besin glomerülleri, graded | 3/3 | 3/3 | 3/3 | ✓ | ✗ | hayır |

- **Hiçbir yapılandırma geçmedi. Kural gereği koku final'de KAPALI kalır.**
  - Beyin girdisi `--no-olfaction`. HAND koku navigasyonu hibritte koku alanını doğrudan okur; bu değişmez.
  - Bu, final_sB'nin (`flight_v16_hybrid_sB_ablDN-DNp15_noOlf_final_sB`) yapılandırması. Yeni tam koşu gerekmiyor ve yapılmadı.
  - `--nt-literature` koku kapalıyken test edilmedi; final'de kullanılmıyor (varsayılan kapalı kalır).
  - Önceki turun "yalnız besin glomerülleri" kararı (v19 final_sA) bununla geçersiz: orada da B-K1/B-K2 kalmıştı.
- Başka ayar, tablo ya da tip denenmedi. DNp15 kalibrasyonu yapılmadı.
- K1, B-K3, B-K4 bütün yapılandırmalarda geçti; karara etkisi yok.
- **Açık not:**
  - FG ve BG, kullanıcının saydığı ölçütlerden yalnız B-K2'de kalıyor. Bu, REPORT_SENSORY_A'daki graded sonucuyla aynı.
  - Kesme sonrası 1.5 Hz, sürülmeyen ağın Aşama A'dakinden %21 daha düşük hızı; ama 0.1 Hz eşiğinin 15 katı.
  - Kalıcı durumu kırmak, ya kaynağı olmayan lLN2/v2LN tiplerinin işaretine ya da işaret dışı bir mekanizmaya bağlı. Bu, elektriksel sinapslara karşılık gelebilir: Shang 2007 / Huang 2010 / Yaksi & Wilson 2010'da eLN→PN etkisi kısmen gap junction'la. Model yalnız kimyasal sinaps içeriyor.
  - Hangisinin doğru olduğu bu turda test edilmedi. Literatür kaynağı olmayan bir işaret değişikliği bu turun kuralı dışında.

## 5. El yapımı / konnektom ayrımı (değişmedi)
- **Davranış:** final_sB ile aynı. Rota, irtifa, yaklaşma ve iniş EL YAPIMI. Beyinden gelen tek davranış kararı beslenme (MN9). Yön terimi DNp15 ablasyonuyla sabit.
- **Bu turun eklediği:** yalnız bir model seçeneği, `--nt-literature`. Varsayılan kapalı ve final'de kullanılmıyor. Davranışa etkisi yok.

## 6. Dosyalar ve yeniden üretim
- **Teşhis:**
  - `scripts/diag/sa2_diag.py`: v17/v18'i okur, `sa2_diag_types.csv` ve `sa2_diag_neurons.parquet` yazar (bulunulan dizine).
  - Codex `neurons.csv.gz` gerekir (`--codex-dir`).
- **Literatür tablosu:** `scripts/make_nt_literature.py --diag sa2_diag_neurons.parquet` → `data/nt_literature_783.csv` (`data/README.md`).
- **Kod:**
  - `flight/brain.py`: `nt_literature`, `_apply_nt_literature`.
  - `flight/groups.py`: `nt_literature_indices`, `PATH_NT_LIT`.
  - `flight/recorder.py`: `_ntLit`.
  - `fly_flight_brain_body_simulation.py`: `--nt-literature`, `meta/nt_literature`, `nt_literature/idx`.
  - `scripts/diag/sa_criteria.py`: `--nt-literature`, `--food-only`.
  - `scripts/diag/sa2_report.py`.
- **Testler:** `tests/flight/test_nt_literature.py`. `pytest tests/`: 113 passed, 10 skipped.
- **Koşular:**
  - Açık döngü: `sa_criteria.py --variant spiking|graded --nt-literature [--food-only]` (seed 0/1/2), sonra `--report sa_criteria_*_ntLit_s*.npz`.
  - Smoke: v20 (FS), v21 (FG), v22 (BS), v23 (BG), seed 3.
