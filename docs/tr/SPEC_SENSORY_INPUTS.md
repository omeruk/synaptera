> **Lab notebook, in Turkish.** Working record of this project, kept as written during the work (moved here from the repository root for the public snapshot). The English consolidated report is [REPORT.md](../../REPORT.md); the English summary is the [README](../../README.md).

# NeuroFly Flight — SPEC_SENSORY_INPUTS: tüm duyu girdilerinin gerçek uyaranlarla sürülmesi (keşif + plan)

> Durum: **yalnız keşif ve plan.** Kod yazılmadı, simülasyon koşulmadı. Bu belgedeki sayıların hepsi mevcut dosyalardan salt okunarak hesaplandı. Kaynaklar: `final_a` HDF5, `Connectivity_783.parquet`, `flywire_annotations.tsv`, Codex `classification` / `consolidated_cell_types` / `visual_neuron_types`, `data/`.
> Betikler: scratchpad'te (`s0_activity.py`, `s1_inventory.py`, `s4_dn.py`). Uygulama turunda `scripts/diag/` altına taşınır.
> Branch: `brain-control`. Kullanıcı kararları 2026-10-01'de alındı, aşağıda "Kullanıcı kararları" başlığında.

**Değişmeyenler:**
- konnektom, nöron ve sinaps sayısı;
- LIF parametreleri;
- dt = 0.1 ms ve 25 ms karar adımı;
- NT işaretleri.

"Tüm nöronlara rastgele girdi" **yok.** Her girdi, simülasyondaki fiziksel bir büyüklükten türetilir ve bir duyu ya da optik lob hücre tipine bağlanır.

## Kullanıcı kararları (2026-10-01)
1. **Görme: sınır katmanı.** Yalnız FlyWire çıkış sinapslarının ≥%50'si FlyVis tiplerinin dışına giden FlyVis karşılıklı tipler sürülür (§2.1).
   - FlyVis'in optik lob iç tiplerinin aktivitesi ayrı bir **gösterim katmanı** olarak çizilir: R1–R8, L1–L5, Mi, Tm, C2/C3 vb., eşlenen FlyWire nöronlarının konumlarında.
   - Bu katman simülasyona girdi değildir. Videoda "FlyVis (gösterim, sürülmez)" etiketi taşır.
   - Bu katman için gereken FlyVis tip/kolon aktivitesi HDF5'e kaydedilir.
2. **Koku: spiking APL ve `--apl-graded` yan yana.** Hiçbir kazanç ayarlanmaz.
   - Spontan hız glomerül başına Hallem & Carlson 2006'dan alınır. Eşleşmeyen glomerüllere tek bir düşük hız verilir (§2.2).
   - Ölçütler önceden yazılır (§3.2).
   - Ana hat: ölçütleri geçen varyant. İkisi de geçerse spiking APL seçilir.
   - İkisi de geçmezse sonuç olduğu gibi raporlanır ve koku yalnız besin glomerülleriyle sürülür (önceki durum). Başka ayar denenmez.
3. **Mekanik: yalnız birincil afferentler.**
   - Haltere (SA_DMetaN): gövde açısal hızından.
   - Kanat (SA_DMT_ADMN): stroke genliği ve frekansından.
   - Johnston organı: antene göre hava akışından.
   - Hepsi L/R ayrı ve VARSAYIM.
   - AN'ler 0. El yapımı `r_asc` sürüşü kapalı kalır ve raporda belirtilir.
   - MANC eşlemesi gelecek iş (§6).
4. **Bacak tadı: bağlantıyla seçilen şeker benzeri alt küme.** Seçim davranıştan önce sabitlenir.
   - Bacak–besin temasında sürülür.
   - Hortumun (labellar) 36 şeker GRN'inin mevcut sürüşü değişmez.
   - Kısa test: yalnız bacak GRN'leriyle MN9 > 10 Hz oluyor mu? Ayar yapılmaz.
5. Ek bölümler istendi: §7 "Biyolojik kontrol haritası ve doğallık" ve §8 "Video".

---

## 0. Mevcut durum: final_a (`flight_v11_hybrid_noOlf_final_a_data.h5`, yalnız okuma)

**Sinaps sayısı.** Modeldeki `Synapses` = **15,091,983** (HDF5 `meta/n_synapses`). Parquet satır sayısı da **15,091,983**, yani birebir aynı.
- Her satır bir nöron çifti. Ağırlık = sinaps sayısı × işaret × w_syn.
- Toplam sinaps sayısı 54,492,922. Yinelenen çift yok, 0 sayılı satır yok.

**Aktif nöronlar** (≥1 spike). Kapalı döngü, adım 0–299 = 7.5 s, seed 3, `--hybrid --no-olfaction`:

| | nöron | oran |
|---|---|---|
| Toplam aktif | **13,140 / 138,639** | **%9.48** |
| Perch kalibrasyonu dahil (adım −18…299) | 13,782 | %9.94 |
| Sürülen girdi nöronları (T4/T5 11,822 + şeker 36) | 10,786 / 11,858 aktif | %91.0 |
| **Sürülmeyen nöronlar** | **2,354 / 126,781** | **%1.86** |
| Ağ ortalaması | 1.04 Hz | |

Sürülmeyen nöronların yalnız %1.9'u en az bir kez ateşliyor. "%9.5 aktif" sayısının neredeyse tamamı doğrudan sürdüğümüz T4/T5'ten geliyor.

**Baskın nöropile göre** (`data/neuron_neuropil.npz`; L/R birleşik; "ort. Hz" tüm nöronların ortalaması, "aktif Hz" yalnız aktiflerin):

| nöropil | toplam | aktif | %aktif | ort. Hz | aktif Hz |
|---|---|---|---|---|---|
| ME | 58,598 | 3,101 | 5.3 | 0.50 | 9.4 |
| LO | 16,751 | 3,465 | 20.7 | 2.42 | 11.7 |
| LOP | 8,027 | 5,495 | 68.5 | 8.01 | 11.7 |
| LA | 6,668 | 0 | 0 | 0 | – |
| GNG | 5,222 | 405 | 7.8 | 1.45 | 18.6 |
| (nöropil tablosunda yok) | 4,458 | 7 | 0.2 | 0.03 | – |
| MB_CA | 3,862 | 0 | 0 | 0 | – |
| AVLP | 3,803 | 68 | 1.8 | 0.01 | 0.8 |
| SMP | 3,556 | 2 | 0.1 | 0.00 | 2.3 |
| SLP | 3,039 | 3 | 0.1 | 0.00 | 1.6 |
| AL | 2,977 | 0 | 0 | 0 | – |
| LH | 2,383 | 0 | 0 | 0 | – |
| PLP | 2,233 | 68 | 3.0 | 0.10 | 3.4 |
| FB | 1,837 | 0 | 0 | 0 | – |
| PVLP | 1,728 | 102 | 5.9 | 0.05 | 0.9 |
| IPS | 1,558 | 160 | 10.3 | 0.58 | 5.7 |
| SPS | 1,418 | 73 | 5.1 | 0.20 | 3.8 |
| MB_ML | 1,123 | 0 | 0 | 0 | – |
| AOTU | 1,076 | 0 | 0 | 0 | – |
| LAL | 990 | 92 | 9.3 | 0.63 | 6.8 |
| SAD | 982 | 14 | 1.4 | 0.04 | 2.9 |
| ICL | 925 | 6 | 0.6 | 0.00 | 0.7 |
| CRE | 732 | 0 | 0 | 0 | – |
| PRW | 556 | 36 | 6.5 | 0.89 | 13.8 |
| AMMC | 509 | 0 | 0 | 0 | – |
| VES | 450 | 27 | 6.0 | 0.09 | 1.4 |
| NO | 405 | 5 | 1.2 | 0.23 | 18.7 |
| EB | 403 | 1 | 0.2 | 0.00 | 1.2 |
| SIP / SCL / WED / FLA / OCG / IB / MB_VL / PB | 372 / 362 / 354 / 328 / 272 / 205 / 149 / 100 | 0 / 0 / 5 / 2 / 0 / 2 / 0 / 1 | ≤1.4 | ≤0.02 | |
| GOR, ATL, MB_PED, AME, BU, GA, EPA, UNASGD, CAN | 61…3 | 0 | 0 | 0 | – |

Okuma:
- Optik lob dışında aktivite yalnız görsel→motor yolunda: PLP, PVLP, IPS, SPS, LAL, GNG, ve PRW/GNG (şeker teması → MN9).
- AL, LH ve MB tamamen sessiz (`--no-olfaction`).
- LA tamamen sessiz: lamina hiç sürülmüyor.
- Merkez kompleks ve SMP/SLP fiilen kapalı.

Görüntü sınıfına göre (`data/neuron_class.npz`):

| sınıf | toplam | aktif | ort. Hz |
|---|---|---|---|
| görsel | 96,962 | 12,210 | 1.39 |
| koku | 3,431 | 0 | 0 |
| tat | 408 | 36 | 5.5 |
| DN | 1,301 | 175 | 1.04 |
| motor | 110 | 42 | 6.7 |
| diğer | 36,427 | 677 | 0.17 |

**Girdi nöronlarından uzaklığa göre aktif nöronlar.** Kaynak T4/T5 + şeker (final_a'da sürülenler). Yönlü en kısa yol.

| hop | tüm kenarlar: n | aktif | %aktif | ort. Hz | yalnız uyarıcı: n | aktif | %aktif |
|---|---|---|---|---|---|---|---|
| 0 (girdi) | 11,858 | 10,786 | 91.0 | 10.7 | 11,858 | 10,786 | 91.0 |
| 1 | 27,274 | 1,220 | 4.5 | 0.28 | 26,920 | 1,254 | 4.7 |
| 2 | 67,369 | 868 | 1.3 | 0.10 | 63,703 | 965 | 1.5 |
| 3 | 27,079 | 212 | 0.8 | 0.12 | 29,643 | 103 | 0.3 |
| 4+ | 3,130 | 54 | 1.7 | 0.12 | 3,237 | 32 | 1.0 |
| ulaşılamaz | 1,929 | 0 | – | – | 3,278 | 0 | – |

- Ağın %77'si 1–2 hop uzakta. Yani sorun erişim değil.
- 1 hop'taki 27k nöronun yalnız %4.5'i ateşliyor. Tek bir kaynak tipinden gelen girdi çoğu hedefte eşiği aşmıyor (eşik ~5100 sinaps·Hz net uyarı, SPEC_BRAIN_CONTROL R1).
- Ulaşılamayan 1,929 nöron, girişi olmayan duyu nöronları ve benzerleri.

---

## 1. Envanter: duyu ve duyu-benzeri girdiler (Codex v783 `classification` ∩ simülasyondaki 138,639 nöron)

"Şu an": final_a ayarı. "Koku açık" = `--no-olfaction` olmadan varsayılan.

| super_class / class | alt sınıf / tip | sayı (L/R/merkez) | şu an | plan |
|---|---|---|---|---|
| **sensory / visual** | R1-6 | 7,938 (4048/3890) | sürülmüyor | gösterim katmanı (sürülmez) |
| | R7 / R8 | 1,332 / 1,346 | sürülmüyor | R7 sınır katmanında (B); R8 gösterim |
| | ocellar_retinula_cell | 273 (100/97/76) | sürülmüyor | **sürülmüyor** (FlyGym'de oselus yok) |
| **sensory / olfactory** | ORN_*, 53 glomerül | 2,275 tipli + 4 tipsiz (2,279) | koku açık: 6 besin glomerülü, 298 nöron; final_a: 0 | A: 53 glomerülün hepsi |
| | pheromone alt sınıfı (DA1, VA1v, VL2a, …) | 430 (yukarıdakinin içinde) | sürülmüyor | A: yalnız spontan (feromon kaynağı yok) |
| **sensory / gustatory** (labellum/farinks) | sugar/water | 129 (67/62) | 36 şeker GRN (Shiu 20 + 16 homolog), tarsus temasında 100 Hz | değişmez (kullanıcı kararı 4) |
| | bitter | 65 | sürülmüyor | sürülmüyor (acı uyaran yok) |
| | low-salt / taste_peg / farinks (aPhN, PhN) | 19 / 71 / 50 | sürülmüyor | sürülmüyor (tuz/su uyaranı yok; yutma modellenmiyor) |
| **sensory_ascending / gustatory** (bacak GRN) | SA_VTV_1…10 | 74 (37/37) | sürülmüyor | C: şeker benzeri alt küme, bacak–besin temasında |
| **sensory / mechanosensory** | JO-A, JO-B (işitsel) | 94 / 296 | sürülmüyor | **sürülmüyor** (ses/yakın alan kaynağı yok) |
| | JO-C*, JO-E* (rüzgâr/yerçekimi) | 430 | sürülmüyor | C: hava akışı |
| | JO-D* | 53 | sürülmüyor | sürülmüyor (titreşim; kaynak yok) |
| | JO-F* (temizlenme), JO-mz | 200 / 37 | sürülmüyor | sürülmüyor |
| | göz kılları BM_InOm | 1,113 | sürülmüyor | sürülmüyor (temas yok) |
| | baş kılları BM_* | 304 | sürülmüyor | sürülmüyor |
| | tat çukuru mekanik (TPMN1/2) | 75 | sürülmüyor | sürülmüyor (hortum eklemi yok, §7) |
| | farinks mekanik (aPhM*) | 47 | sürülmüyor | sürülmüyor |
| **sensory_ascending / AN** (birincil afferent) | SA_DMT_DMetaN (haltere siniri) | 367 (**135/232**) | sürülmüyor | C: haltere |
| | SA_DMT_ADMN (kanat siniri) | 80 (36/44) | sürülmüyor | C: kanat |
| | SA_DLV, SA_MDA, SA_VTV_DProN/PDMN, tipsiz | 25+17+4+25 | sürülmüyor | sürülmüyor (işlev bilinmiyor) |
| | unknown_sensory SA_VTV_6 | 12 | sürülmüyor | sürülmüyor |
| **ascending (AN)** | 36 alt sınıf (AN_GNG 654, AN_multi 274, AN_AVLP 190, …) | 1,736 | 0 (varsayılan; `--asc-legacy` ile \|ω\|) | 0; MANC eşlemesi gelecek iş |
| **sensory / thermosensory** | cold / heating / humid | 9 / 7 / 13 | sürülmüyor | **sürülmüyor** (sıcaklık modeli yok) |
| **sensory / hygrosensory** | dry / moist / cooling / evap. | 29 / 16 / 13 / 16 | sürülmüyor | **sürülmüyor** (nem modeli yok) |
| **sensory / unknown_sensory** | | 118 | sürülmüyor | sürülmüyor |
| **optic** (FlyVis karşılıklı, interneuron) | 52 FlyWire tipi | 63,994 | T4a–d/T5a–d 11,822 (FlyVis) | B: sınır katmanı 34,121; geri kalanı gösterim |
| visual_projection / ocellar | ocellar interneuron | 20 | sürülmüyor | sürülmüyor |

Notlar:
- SA_DMetaN taraf sayısı asimetrik (135/232). Bu, proofreading ya da sınıflandırma farkı olabilir; ayrılmadı. Taraf başına normalize edilmiş oranlar kullanılacak, ama toplam girdi asimetrik kalacak. Bu, raporda bir risk olarak yazılır.
- Shiu'nun 408'lik `sez` grubu (tüm GRN'ler) yalnız eski yolda (legacy). Burada kullanılmıyor.
- "Duyu" toplamı: sensory 16,385 + sensory_ascending 581 = 16,966.
  - Plan sonunda sürülen duyu nöronları ≈ 2,279 ORN + 36 + ≤74 GRN + 430 JO + 367 + 80 + 1,332 R7 ≈ **4.6k** (duyu nöronlarının %27'si).
  - Buna 32.8k optik lob interneuronu (sınır katmanı) eklenir.
  - Toplam Poisson nöronu ≈ 37.4k (beynin %27'si). Şu an 11.9k.

---

## 2. Gruplar için simülasyon karşılığı ve eşleme önerisi

### 2.1 Görme: FlyVis → FlyWire sınır katmanı (kullanıcı kararı 1)
**FlyVis–FlyWire tip eşleşmesi.**
- FlyVis'te (Lappalainen et al. 2024, *Nature* 634:1132; `flow/0000/000`) 65 tip var. Bunlardan **52 FlyWire tipi, 63,994 nöron** eşleşiyor.
  - FlyVis'teki R1…R6, FlyWire'da tek tip `R1-6`.
  - CT1(Lo1) ve CT1(M10), tek nöron olan `CT1`'in bölmeleri.
  - `TmY9` = `TmY9q` + `TmY9q__perp`.
- Eşleşmeyen 8 FlyVis tipi: Mi3, Mi11, Mi12, Tm5Y, Tm28, Tm30, TmY13, TmY18. FlyWire v783 `consolidated_cell_types`'ta bu adlar yok.
- Kolon ataması (`data/column_assignment.csv.gz`) 30 FlyVis tipinde var. Tm21 de var ama FlyVis'te yok.

**Çift sayım sorunu (neden sınır katmanı).**
- Poisson ile sürülen bir nöronda rfc = 0 ve tek girdi spike'ı 68.75 mV. Bu nöron FlyWire'daki tekrarlayan sinapslardan da girdi almaya devam eder ve fazladan spike atar.
- T4/T5'in giriş sinapslarının ~%80'i başka FlyVis tiplerinden geliyor. Bu tiplerin hepsi sürülürse aynı görsel bilgi iki kez sayılır.

**Sınır kuralı (sabit, davranıştan önce).**
- Bir FlyVis tipi, parquet'teki çıkış sinapslarının **≥%50'si FlyVis-karşılıklı olmayan** nöronlara gidiyorsa sürülür. Bu nöronlar VPN, LPTC, merkez beyin ve FlyVis'te olmayan optik lob tipleri (Dm, Pm, Li, …).
- Sonuç: **32 tip, 34,121 nöron**:

| grup | tipler (çıkışın FlyVis dışına giden payı) | nöron | kolonlu |
|---|---|---|---|
| T4/T5 (mevcut) | T4a–d, T5a–d (0.64–0.81) | 12,245 | 11,822 |
| T2/T3 | T2 0.83, T2a 0.85, T3 0.90 | 4,916 | 4,454 |
| Tm | Tm1 0.64, Tm3 0.52, Tm4 0.51, Tm20 0.84, Tm5a 0.96, Tm5b 0.89, Tm5c 0.79, Tm16 0.53 | 8,170 | 5,986 |
| TmY | TmY3 0.69, TmY4 0.82, TmY5a 0.88, TmY9q 0.73, TmY9q__perp 0.76, TmY10 0.74, TmY14 0.79 | 3,901 | 0 |
| Mi | Mi1 0.52, Mi10 0.54, Mi14 0.53, Mi15 0.82 | 3,211 | 1,581 |
| Lawf2 | 0.51 | 346 | 0 |
| R7 | 0.71 | 1,332 | 1,253 |

- Sınırın hemen altında kalanlar, kurala göre **sürülmez**: Tm2 (0.4999), Mi9 (0.49), Mi2 (0.47), Mi4 (0.46).
- Sürülmeyen FlyVis tipleri (gösterim katmanı): R1-6, R8, L1–L5, Lawf1, Am1, C2, C3, CT1, Mi2, Mi4, Mi9, Mi13, T1, Tm2, Tm9, TmY15. Toplam ~29.9k nöron.
- **Kalan çift sayım (risk, ölçülecek):** sınır katmanı nöronlarının girdisinin %31'i yine sınır katmanından geliyor. T4/T5 için bu oran %42; Mi1→T4 ve Tm1/Tm4→T5 bu kümede. Sayılar §3.1'de ölçülür.

**Kolonsuz ~9.0k nöron** (TmY*, Tm5a–c, Tm16, Mi10/14/15, Lawf2 ve diğer tiplerin kolonsuz kısmı). VARSAYIM ile en yakın kolona atanır:
- `data/neuron_arbor_centroids.npz`'deki arbor ağırlık merkezi kullanılır.
- Referans: aynı hemisferde, aynı nöropilde kolonlu nöronların (p, q) → merkez regresyonu (ME için Mi1, LO için Tm1, LOP için T4).
- Atanan kolonun FlyVis düğümü kullanılır.
- Geniş alanlı tiplerde (Tm5, TmY) FlyWire nöron sayısı kolon sayısından az. Her nöron yalnız kendi merkez kolonunu alır. Bu bir alıcı alan basitleştirmesidir; VARSAYIM.

**Dereceli aktivite → hız** (T4/T5 kalibrasyonunun genellemesi, `t45_transduction.json` → `visual_transduction.json`):
- r = clip(R_MAX · relu(a − a0) / a_ref_tip, 0, R_CLIP). R_MAX = 50 Hz ve R_CLIP = 150 Hz değişmez (VARSAYIM).
- a0: düğüm başına gri ekran dengesi (mevcut yöntem).
- a_ref_tip: sabit bir standart uyaran setine tipin en büyük ortalama pozitif tepkisi. Davranışa bakılmadan bir kez ölçülür.
  - Set: mevcut standart ızgara, 4 yön; tam alan ON basamağı 0.5→0.8; OFF basamağı 0.5→0.2.
  - Pencere: 250–1000 ms, merkez kolonlar.
  - OFF tipleri ışık azalmasında depolarize olur; relu bu tepkiyi doğru yakalar.
- **VARSAYIM:** biyolojide birçok tip spike atmaz ve dereceli çalışır (R7, Tm'lerin bir kısmı, Mi1/Tm3 de kısmen). Poisson hızı bunun yerine geçen bir dönüşümdür. Hiperpolarizasyon 0 Hz'e kırpılır.

**Gösterim katmanı (kullanıcı kararı 1).**
- Her adımda FlyVis düğüm aktivitesi HDF5'e yazılır: 65 tip × 721 kolon × 2 göz, float16, a − a0. Boyut adım başına 187 KB; 300 adımda 56 MB.
- **RAM'de biriktirilmez.** Döngü başında `flyvis/activity` adlı, büyüyebilen, chunk = 1 adımlık bir HDF5 dataset'i açılır ve her adımda yazılır. CLAUDE.md'deki "döngü biter bitmez HDF5" kuralı korunur: spike/davranış yazımı aynı kalır, bu dataset yalnız ek.
- Gösterim, sürülmeyen tipleri eşlenen FlyWire nöronlarının konumunda çizer. Etiketi: "FlyVis (gösterim, sürülmez)". Kolon → nöron eşlemesi aynı tablodan gelir.

### 2.2 Koku: 53 glomerülün hepsi (kullanıcı kararı 2)
- **Spontan hız, glomerül başına.**
  - Hallem & Carlson 2006 (*Cell* 125:143–160) reseptör başına spontan hızlarından alınır.
  - Reseptör → glomerül eşlemesi: Couto et al. 2005 (*Curr Biol* 15:1535); Fishilevich & Vosshall 2005 (*Curr Biol* 15:1548).
  - **Değerler bu belgede yok.** Uygulama turunun ilk işi tabloyu makaleden `data/orn_spontaneous_783.csv`'e aktarmak: glomerül, reseptör, spontan Hz, kaynak satırı. Tablo kod yazılmadan önce kullanıcıya gösterilir. **DOĞRULANMADI.**
- **Eşleşmeyen glomerüller:** Hallem & Carlson'ın 24 reseptörü dışındakiler. Ir/Gr ve coeloconic glomerüller (ör. DP1m, DC4, DL2d/v, VM4, V) ve eşleşmeyen Or glomerülleri buraya girer.
  - **5 Hz, tek değer (VARSAYIM).**
  - Gerekçe: de Bruyne et al. 2001 (*Neuron* 30:537) bazikonik ORN spontan hızlarını tek haneliden ~20 Hz'e kadar raporlar. Bu aralığın alt kısmı seçildi, çünkü eşleşmeyenlerin çoğu Ir tabanlı coeloconic ORN'ler. Onların spontan aktivitesinin düşük olduğu varsayılıyor (künye doğrulanacak).
  - Düşük değer, kalıcı durum riskini artırmamak için de muhafazakâr.
- **Besin kokusu.** Yalnız 6 besin glomerülünün (DM1, DM2, DM4, VA2, VM2, DP1m; Semmelhack & Wang 2009) hızını artırır: r = r_spont,g + (150 − r_spont,g) · f(c). f(c), mevcut `odor_norm`.
  - Taraf ağırlığı mevcut kuralla aynı (ipsi 1, kontra 0).
  - Diğer 47 glomerül besin kokusundan bağımsız olarak spontan hızda kalır.
- Feromon glomerülleri (DA1, VA1v, VL2a, …): yalnız spontan.
- El yapımı koku terimleri (`turn_odor`, `pitch_odor`) yeni yolda kapalı kalır. Hibrit koşularda HAND olarak etiketli kalır.
- Sürülen nöron: 2,275 tipli ORN. 4 tipsiz olfactory nöron sürülmez.
  - Tarafı `na` olan 30 ORN, mevcut kuralla L/R ortalamasını alır.

### 2.3 Mekanik: birincil afferentler (kullanıcı kararı 3)
Hepsi VARSAYIM. Kazançlar fiziksel büyüklüğün literatürdeki tipik değerine göre bir kez sabitlenir, davranışa göre ayarlanmaz.

**Johnston organı, JO-C* ve JO-E* (430).** Kaynak: Yorozu et al. 2009 (*Nature* 458:201); Kamikouchi et al. 2009 (*Nature* 458:165).
- Hava akışı: v_air = −v_body (durgun hava), anten çerçevesine dönüştürülür.
- Arista sapması tarafa bağlıdır. Suver et al. 2019 (*Neuron* 102:828): lateral rüzgâr iki anteni zıt yönde saptırır.
  - Öneri: d_s = |v_air|/v_ref · (cos ψ ± sin ψ)/√2. ψ, kafa çerçevesinde rüzgâr açısı; + işareti sol anten içindir.
  - v_ref = 0.4 m/s, serbest uçuş hızı mertebesi (Fuller et al. 2014, *PNAS* 111:E1182; Mamiya et al. 2011, *J Neurosci* 31:6900).
- JO-E, sapmanın bir yönüne; JO-C öbür yönüne tepki verir (Yorozu 2009): r_E,s = R_MAX · relu(d_s), r_C,s = R_MAX · relu(−d_s), ≤ R_CLIP.
- Hangi sapma yönünün "çekme", hangisinin "itme" olduğu ve JO-C/E'ye nasıl eşlendiği VARSAYIM. Uygulamadan önce Yorozu 2009 Şekil 2'den doğrulanır.
- Kayıt: v_air (anten çerçevesi), d_L, d_R.
- Gösterim: arista eklemleri (`joint_LArista_yaw` vb.) MJCF'de var ama aktüatörsüz. Sapma yalnız kaydedilir.

**Haltere afferentleri, SA_DMT_DMetaN (367).** Haltere siniri = dorsal metatorasik sinir. Kaynak: Dickinson 1999 (*Phil Trans R Soc B* 354:903); Nalbach 1993 (*J Comp Physiol A* 173:293); Fayyazuddin & Dickinson 1996 (*J Neurosci* 16:5225).
- Kanatlar açıkken afferentler her stroke'ta faz kilitli ateşler. Coriolis kuvvetiyle açısal hızı kodlarlar.
- Öneri: r_s = R_TONIC · wings_on + R_MAX · relu(n_s · ω_body / ω_ref), ≤ R_CLIP.
  - n_s: tarafın duyarlılık ekseni. Haltere vuruş düzlemi ~30° arkaya eğik olduğu için yaw ve roll bileşenleri taraflar arasında zıt işaretli, pitch iki tarafta aynı (Nalbach 1993).
  - R_TONIC = 50 Hz. Gerçekte faz kilidi ~218 Hz'dir; 150 Hz kırpmanın altında kalınır.
  - ω_ref = 10 rad/s (kontrollü uçuşta saccade tepe hızı mertebesi).
- 12 alt tip (DMetaN_1…12) işlevsel olarak ayrılamıyor; hepsi aynı kuralla sürülür.
- Taraf sayıları asimetrik (135/232); §1'e bakın.
- Gövdedeki el yapımı haltere PD refleksi aynen kalır. Refleksler beyinden geçmez (§7). Beyin afferentlerin bir kopyasını alır.

**Kanat afferentleri, SA_DMT_ADMN (80).** Kaynak: Dickinson & Palka 1987 (*J Neurosci* 7:4201).
- Kanat çan sensilleri stroke'a faz kilitli ateşler.
- Öneri: r_s = R_MAX · (Φ_s / Φ_hover) · (f / 218 Hz) · wings_on, ≤ R_CLIP. Kaydedilen `stroke_amp_L/R` ve `stroke_freq` kullanılır.

**Bacak teması.** Bacak mekanosensör aksonları beyne doğrudan gelmiyor; VNC → AN yoluyla geliyor (Tsubouchi et al. 2017, *Science* 358:615). AN'ler 0 olduğu için bacak teması mekanik girdi olarak **sürülmüyor**. MANC eşlemesi gelecek iş.

**AN'ler (1736): 0.**
- `--asc-legacy` ile \|ω\| → tüm AN eşlemesi eski koşuları yeniden üretmek için kalır. Yeni bayraklarla birlikte kullanılamaz; argüman hatası verir.
- final_a'da `asc_rate` zaten 0. Rapora "el yapımı r_asc sürüşü kapalı" diye yazılır.

### 2.4 Tat: yalnız temasla (kullanıcı kararı 4)
- **Hortum (labellar) şeker GRN'leri, 36:** değişmez. Tarsus–besin platformu temasında 100 Hz (mevcut VARSAYIM).
- **Bacak GRN'leri (SA_VTV gustatory, 74).**
  - Şeker benzeri alt küme, `select_sugar_homologs` ile aynı yöntemle seçilir: giriş+çıkış partner-tipi profili (ipsi/kontra, L2-normalize), k = 5.
  - Referans: labellar sugar/water (129) ve bitter (65) GRN'leri.
  - Bir bacak GRN'i, 5 komşusunun çoğunluğu şeker GRN'iyse seçilir.
  - Seçim ve yöntem doğruluğu davranıştan önce sabitlenir: labellar setinde birini dışarıda bırakma doğruluğu raporlanır. Sonuç `data/leg_sugar_grn_783.csv`'e yazılır.
  - **VARSAYIM:** bacak ve labellum GRN'lerinin bağlantı profilleri benzer olmayabilir. Çoğunluk kuralı 0 nöron seçebilir. Bu durumda olduğu gibi raporlanır ve bacak GRN'leri sürülmez.
  - Sürüş: herhangi bir tarsus besin platformuna değdiğinde 100 Hz. Tarsus–GRN eşlemesi yok; 74 nöronun hangi bacaktan geldiği bilinmiyor.
- **Kısa test** (açık döngü, 1 s, 3 seed; ayar yok): yalnız bacak şeker GRN'leri 100 Hz, labellar kapalı → MN9 ort. > 10 Hz mi? Sonuç olduğu gibi yazılır.
- Bitter, düşük tuz ve farinks GRN'leri: sürülmüyor (uyaran yok).

### 2.5 Karşılığı olmayanlar: sürülmüyor
- Oselus: 273 fotoreseptör, 20 interneuron. FlyGym'de oselus kamerası yok.
- Sıcaklık: 16. Nem: 74. Isıl ve nem alanı modellenmiyor.
- Ses ve yakın alan: JO-A/B 390, JO-D 53.
- Temizlenme: JO-F 200. Göz ve baş kılları: 1,417.
- Farinks ve labellum mekaniği: 122. Hortum eklemi yok.
- Bilinmeyen duyu: 118.
- AN'ler: 1,736.

---

## 3. Riskler ve önceden kaydedilecek kontrol ölçütleri
Ölçütler koşudan önce yazılır, sonradan değiştirilmez. Başarısızlık olduğu gibi raporlanır. Hiçbir kazanç davranışa ya da ölçüte göre ayarlanmaz.

### 3.1 Genel (her aşamada)
- **K1, kaçak uyarılma.** Kapalı döngü smoke ve 1 s açık döngü koşullarında:
  - sürülmeyen nöronların ortalaması < 5 Hz;
  - son %25'lik dilimin hızı ilk %25'liğin ≤ 1.5 katı (monoton büyüme yok);
  - hiçbir nöropilin ortalaması > 50 Hz değil.
- **K2, kalıcılık.** Tüm girdiler kesildikten sonra 100–200 ms penceresinde ağ < 0.1 Hz. Mevcut (a) ölçütü; kapalı döngüde `persist_net_rate_hz`.
- **K3, adım süresi ve RAM.** Ölçüm: `step_time` ve `rss_gb`.
  - Kabul: 300 adımlık koşuda ort. adım ≤ 2.0 s ve tepe RSS ≤ 8 GB. RAM 15 GB + 8 GB swap; geçmişte OOM yaşandı.
  - Aşılırsa koşu yapılmaz, raporlanır.
- **K4, MN9'un temassız ateşlemesi.** Temas yokken (uçuş, perch) MN9 ort. < 10 Hz. Bu, kullanıcının (iii) ölçütü. Yeni girdiler (JO, ORN, GRN) SEZ'i sürebilir; temassız uzatma yanlış beslenme kararı demektir.
- **K5, R0 regresyonu.** Şeker 100 Hz, yeni girdi tabanı üstünde → MN9 > 10 Hz (eşik), 3 seed.
- **K6, çift sayım (yalnız B).**
  - Sürülen sınır nöronunun gerçekleşen spike hızı / FlyVis'in hedef Poisson hızı oranı, tip başına medyan.
  - > 1.5 ise çift sayım raporlanır. Ölçüt "geçti/kaldı" değil, kayıttır; sınır kuralı değiştirilmez.

**Maliyet tahmini** (ölçüme dayalı, doğrulanacak):
- final_a'da adım 0.887 s, bunun 0.319 s'i beyin; 1.04 Hz ağda.
- Eski girdilerle ~9–10 Hz ağda (v6/v7/v9) beyin süresi 0.37 s. Eğim ≈ 0.006 s/Hz.
- Poisson nöron sayısı 11.9k → ~37.4k. Ek RNG maliyeti tahmini ≤ 0.05 s/adım; smoke'ta ölçülür.
- FlyVis zaten 65 tipin hepsini hesaplıyor. Ek maliyet yalnız indeksleme ve HDF5 yazımı (~0.01 s).
- Tahmin: ağ ortalaması 3–5 Hz olursa adım ≈ **0.95–1.05 s** (+%10–20). 300 adım ≈ 5–6 dk döngü + ~3 dk kurulum.
- RAM:
  - Brian2 `SpikeMonitor` tüm geçmişi tutar (model.py, değişmez) ve `SpikeCounter` parçaları da birikir. 5 Hz ağda bu ~0.7M spike/s simülasyon × ~20 B ≈ 14 MB/s simülasyon. 300 adımda (7.5 s) ~100 MB; 2000 adımda ~0.7 GB.
  - Poisson sinapsları < 10 MB.
  - Tahmini tepe RSS: 3.5 → **≤ 4.5 GB**.
  - Kalıcı durum (spiking APL) oluşursa ağ 3–5 Hz yerine ~10 Hz olabilir. Bu da kabul sınırı içinde.

### 3.2 Koku (A), kullanıcının ölçütleri, önceden kayıtlı
Her varyant için ayrı (spiking APL, `--apl-graded` g = 2.0 sabit). 3 seed, her koşul temiz başlangıçtan (`net.restore`).
- **(i) Kalıcı durum yok.**
  - Protokol: 1 s spontan + besin kokusu 150 Hz → koku kesilir (ORN'ler spontan hızına döner) → 1.5 s.
  - Taban: aynı seed'de, temiz başlangıçtan 1 s yalnız spontan; son 500 ms.
  - Kesmeden sonraki **1.0–1.5 s** penceresinde AL (baskın nöropil AL) ve KC ortalama hızı tabandan en fazla max(0.2 · taban, 0.1 Hz) farklı.
  - AL ve KC ayrı ayrı geçmeli.
- **(ii) KC seyrekliği.** Koku varken 250–1000 ms'de ≥1 spike atan KC oranı **%5–15**.
- **(iii) MN9.** Temas yokken MN9 < 10 Hz (= K4).
- **Ana hat kararı (mekanik):**
  - Ölçütleri geçen varyant seçilir. İkisi de geçerse spiking APL.
  - İkisi de geçmezse olduğu gibi raporlanır ve koku önceki duruma, yalnız 6 besin glomerülüne döner (`orn_food`, 8 Hz spontan). Başka ayar denenmez.

### 3.2b Aşama A ölçütleri (önceden kayıtlı, 2026-10-01; açık döngü, smoke ve tam koşudan ÖNCE yazıldı)
Kapsam: `--olfaction-full` (53 glomerül, `data/orn_spontaneous_783.csv`) iki APL varyantıyla: **spiking APL** (varsayılan) ve **`--apl-graded`** (g = `APL_GAIN` = 2.0, değişmeden). Hiçbir kazanç, hız ya da eşik ayarlanmaz; DNp15 kalibrasyonu ve doğrulaması bu turda yok.

**Tanımlar.**
- AL: `data/neuron_neuropil.npz` baskın nöropili AL olan nöronlar (L/R birleşik), **Poisson ile sürülen ORN'ler hariç** (ORN hızı girdinin kendisidir).
- KC: `cell_type` KC* (5,177; `groups.apl_kc_indices`).
- MN9: CB0701 L/R, Hz/nöron, L/R ortalaması.
- "Sürülmeyen": Poisson girdi gruplarının (orn_all, vbnd, şeker) dışındaki tüm nöronlar.

**Açık döngü protokolü** (`scripts/diag/sa_criteria.py`). Tam beyin, yalnız `orn_all_L/R/C` girdisi (görme, şeker, AN yok). Seed 0, 1, 2; her seed temiz başlangıçtan (`net.restore` + `brian2.seed`). 25 ms adımlar:
- S, adım 0–39 (1 s): tüm ORN'ler spontan hızda.
- O, adım 40–79 (1 s): besin kokusu, iki anten f = 1 (6 besin glomerülü 150 Hz, diğerleri spontan).
- P, adım 80–139 (1.5 s): koku kesildi, ORN'ler spontan hızda.
- X, adım 140–179 (1 s): tüm girdiler 0 (yalnız kayıt).

**Ölçütler** (her biri her varyant için 3 seed'in **3'ünde** geçmeli):
- **(i) tabana dönüş:** taban = S'nin son 500 ms'i (adım 20–39). Pencere = kesmeden 1.0–1.5 s sonra (adım 120–139). AL ve KC ortalama hızı (Hz/nöron) ayrı ayrı |pencere − taban| ≤ max(0.2 · taban, 0.1 Hz).
- **(ii) KC seyrekliği:** O'nun 250–1000 ms'inde (adım 50–79) ≥1 spike atan KC oranı **%5–15**.
- **(iii) MN9:** açık döngüde (temas yok, şeker 0) adım 0–139 ortalaması **< 10 Hz**. Kapalı döngüde B-K4 (aşağıda).
- **K1 kaçak uyarılma (açık döngü, adım 0–139):** sürülmeyen ortalama < 5 Hz; sürülmeyenlerin adım başı hızında son %25 (adım 105–139) ≤ 1.5 × ilk %25 (adım 0–34); hiçbir baskın nöropilin (tüm nöronlar, L/R birleşik) ortalaması > 50 Hz değil.
- Kayıt (ölçüt değil): X'te 100–200 ms (adım 144–147) ağ hızı; AL/KC/LH zaman seyri; DN L/R.

**Smoke (kapalı döngü, iki varyant).** `--n-steps 20 --persist-steps 40 --hybrid --vision-boundary --olfaction-full --ablate-dn DNp15 --seed 3 --no-video` (+ `--apl-graded`). Ölçütler §3.3b'deki gibi:
- B-K1: sürülmeyen ort. < 5 Hz, son/ilk %25 ≤ 1.5, nöropil ≤ 50 Hz;
- B-K2: 1 s kesmenin son 200 ms'i < 0.1 Hz;
- B-K3: ort. adım ≤ 2.0 s, tepe RSS ≤ 8 GB;
- B-K4: temassız MN9 < 10 Hz.

**Ana hat kararı (mekanik).**
- Bir varyant, açık döngüde (i), (ii), (iii) ve K1'i 3/3 seed'de ve smoke'ta B-K1…K4'ü geçerse "geçer".
- İkisi de geçerse spiking APL; biri geçerse o.
- İkisi de geçmezse sonuç olduğu gibi raporlanır. Tam koşu `--olfaction-full` olmadan yapılır: koku yalnız 6 besin glomerülüyle (`orn_food`, 8 Hz spontan), spiking APL. Başka ayar denenmez.

**Tam koşu** (seçilen varyant; seed 3, 300 adım, `--hybrid --vision-boundary --olfaction-full --ablate-dn DNp15 --no-video` [+ `--apl-graded`]). final_sB ile yan yana:
- B-K1…K4 (§3.3b tanımları; sürülmeyen = orn_all, vbnd, şeker dışı);
- kayıt: KC seyrekliği (faz pencerelerinde ≥1 spike atan KC oranı), AL/MB/LH nöropil hızları, DNp07/DNp10 pencereleri, DNp15 L/R;
- kayıt: DN L−R ile koku asimetrisi `I_asym` arasındaki ilişki (Pearson r, kanatlar açık adımlar). Bu yalnız tanımlayıcıdır; yön terimi ablasyonla sabit olduğu için davranışa geçmez.

**Bacak GRN'leri** (§2.4; `--leg-grn`, varsayılan KAPALI; tam koşu komutunda yok).
- Seçim, davranıştan önce yalnız bağlantıyla yapılır.
  - Özellikler `select_sugar_homologs` ile aynı: partner `cell_type` (yoksa `hemibrain_type`) × giriş/çıkış × ipsi/kontra, sinaps sayısı, L2-normalize, kosinüs.
  - Havuz: labellar `sugar/water` (129) + `bitter` (65).
  - Bir SA_VTV gustatory nöronu (74), 5 en yakın havuz komşusunun çoğunluğu (≥3) sugar/water ise seçilir.
  - Yöntem doğruluğu: havuzda birini dışarıda bırakma (sugar/water doğru pozitif, bitter yanlış pozitif) raporlanır. 0 nöron seçilirse olduğu gibi raporlanır ve bacak GRN'leri sürülmez.
- Kısa test (`scripts/diag/sa_leg_grn.py`):
  - açık döngü, tam beyin, seed 0/1/2, temiz başlangıç;
  - yalnız seçilen bacak GRN'leri 100 Hz, 1 s; labellar şeker ve diğer tüm girdiler 0;
  - MN9 L/R ortalaması (0–1000 ms) seed başına ve 3 seed ortalaması;
  - "MN9 > 10 Hz?" sorusu 3 seed ortalamasıyla yanıtlanır, seed değerleri yazılır. Ayar yok.
- Kapalı döngüde `--leg-grn`: herhangi bir tarsus besin platformuna değdiğinde bacak GRN'leri 100 Hz (`SUGAR_RATE_CONTACT`). Labellar sürüş aynı.

**§3.2b sonuçları (2026-10-01; ölçütler yukarıda, sonuçtan önce yazıldı ve değiştirilmedi).** Betikler: `scripts/diag/sa_criteria.py` (açık döngü), `sa_report.py` (smoke ve tam koşu). Ayrıntı: REPORT_SENSORY_A.md.

| ölçüt | spiking APL | `--apl-graded` (g = 2.0) |
|---|---|---|
| (i) AL tabana dönüş (3 seed) | 3/3 geçti (taban 121.0–121.3 Hz) | 3/3 geçti (taban 116.3–116.4 Hz) |
| (i) KC tabana dönüş | 3/3 geçti (taban 33.2–33.3 Hz) | 3/3 geçti (taban 1.88–1.89 Hz) |
| (ii) KC seyrekliği %5–15 | **0/3** (%67.9–68.2) | 3/3 (%8.5–8.6) |
| (iii) MN9 açık döngü < 10 Hz | 3/3 (0.14–0.29 Hz) | 3/3 (0.00 Hz) |
| K1 açık döngü | 3/3 (sürülmeyen 3.55 Hz, AL 48.4 Hz) | 3/3 (1.95 Hz, AL 47.1 Hz) |
| kayıt: tüm girdiler 0, 100–200 ms ağ | 3.44–3.48 Hz | 1.94–1.95 Hz |
| smoke B-K1 | **KALDI** (sürülmeyen 6.60 Hz) | geçti (4.46 Hz; AL 43.5 Hz) |
| smoke B-K2 (1 s kesme, son 200 ms < 0.1 Hz) | **KALDI** (3.46 Hz) | **KALDI** (1.95 Hz) |
| smoke B-K3 | geçti (1.00 s, 3.50 GB) | geçti (1.03 s, 3.50 GB) |
| smoke B-K4 | geçti (0.00 Hz) | geçti (0.00 Hz) |

- **Karar (mekanik): iki varyant da geçmedi.**
- (i) geçiyor, ama bu anlamlı bir tabana dönüş değil. Spontan ORN girdisi ağı kendini sürdüren bir duruma sokuyor: tüm girdiler sıfırken (X penceresi, smoke B-K2) ağ sönmüyor. (i)'nin tabanı bu kalıcı durumun kendisi.
- Tam koşu kurala göre `--olfaction-full` **olmadan** yapılır: koku yalnız 6 besin glomerülüyle (`orn_food`, 8 Hz spontan), spiking APL. Başka ayar denenmedi.
- Not: kullanıcının saydığı ölçütler yalnız (i)–(iii) ve kaçak uyarılmaydı (B-K1). B-K2'yi karar kuralına koşudan önce bu belge ekledi. Yalnız o dört ölçüte bakılsaydı graded varyant geçerdi. Kural sonradan değiştirilmedi.

### 3.2c Aşama A2: literatür NT işaretleri (`--nt-literature`; önceden kayıtlı, 2026-10-01, kod ve koşulardan ÖNCE yazıldı)
Gerekçe ve teşhis: REPORT_SENSORY_A2 §1–2. Kalıcı koku durumu AL'deki LN/PN çekirdeğinde. Döngü çıkışının ~%27–38'i Codex NT tahmini olmayan ya da düşük güvenli nöronlardan geliyor.
Bu tur "NT işaretlerine dokunulmaz" kuralına ikinci, bayrakla açılan bir istisna ekler. Kural aşağıda; **kazanç, eşik, hız, LIF parametresi ya da sinaps sayısı değişmez.**

**Kural (`--nt-literature`, varsayılan KAPALI).**
- **Tablo:** `data/nt_literature_783.csv` (`scripts/make_nt_literature.py`; tip → `known_nt` → kaynak → güven → `sign_lit`).
  - Kapsam: §1'de döngüye katılan tipler (baskın nöropil AL/LH/MB_*, ORN değil, Aşama A smoke'ları v17/v18'in kesme penceresinde ≥1 spike).
  - Kaynak: `flywire_annotations.tsv` `known_nt` / `known_nt_source` (Schlegel et al. 2024 literatür derlemesi).
  - lLN1_bc kaynağına Eckstein et al. 2024 tartışması ve Huang et al. 2010 eklendi.
- **`sign_lit`:**
  - `known_nt`'de tam bir hızlı verici varsa: ACh → +1, GABA → −1, Glu → −1 (modelin kendi eşlemesi).
  - Aksi halde 0: hızlı verici yok, birden fazla var, ya da tipin her nöronu aynı `known_nt`'yi taşımıyor.
- **Uygulama:**
  - `sign_lit ≠ 0` olan tiplerin (tip = `cell_type`, yoksa `hemibrain_type`) tüm nöronlarının bütün çıkış sinapsları: `w = |w| · sign_lit`. Sinaps listesi ve sayıları aynı; yalnız işaret.
  - Tabloda olmayan ya da `sign_lit = 0` olan tiplere dokunulmaz.
  - Graded APL'den sonra uygulanır. APL tabloda GABA (−) olduğundan zaten değişmiyor; graded yolda APL'nin spike ağırlığı 0 kalır.
  - `--nt-modulatory-silent` ile birlikte kullanılamaz.
- **Beklenen etki** (tablodan, koşudan önce):
  - 272 tipe işaret atanır; **yalnız 8 tipte 24 nöronun işareti değişir**: il3LN6, lLN2P_b, v2LN36, DPM, PPL203, MBON05 (1), DN1a (1) → −; LHPV6o1 → +.
  - lLN1_bc literatürde kolinerjik; işareti değişmez.
- **Kayıt:**
  - HDF5 `meta/nt_literature`: tip sayısı, değişen nöron ve kenar sayıları, uyarıcı→inhibitör ve inhibitör→uyarıcı sinaps toplamları.
  - `nt_literature/idx`.
  - Dosya adında `_ntLit`.
- **Test:** `tests/flight/test_nt_literature.py`.
  - Tablo kuralı.
  - root_id eşlemesi.
  - Ağırlıkların |w| korunarak işaretinin değişmesi.
  - Bayrak kapalıyken ağırlıkların parquet ile aynı olması.
  - DEV alt-ağında uygulama (DEV yalnız test içindir).

**Test matrisi** (hepsi `--nt-literature`; tam beyin; ayar yok):

| kod | koku girdisi | APL | açık döngü (i)(ii)(iii)+K1, seed 0/1/2 | smoke, seed 3 |
|---|---|---|---|---|
| FS | `--olfaction-full` | spiking | `sa_criteria.py --variant spiking --nt-literature` | `--n-steps 20 --persist-steps 40 --hybrid --vision-boundary --olfaction-full --ablate-dn DNp15 --seed 3 --no-video --nt-literature` |
| FG | `--olfaction-full` | graded | aynı + `graded` | aynı + `--apl-graded` |
| BS | yalnız besin glomerülleri (`orn_food`) | spiking | `--food-only`: S/P 8 Hz, O 150 Hz (`cfg.ORN_FOOD_RATE`) | FS'nin `--olfaction-full`'suz hali |
| BG | yalnız besin glomerülleri | graded | aynı + `graded` | BS + `--apl-graded` |

- Açık döngü protokolü ve ölçüt tanımları §3.2b ile aynı. BS/BG'de "AL"den ve "sürülmeyen"den çıkarılan girdi nöronları `orn_food` (298) olur.
- Smoke ölçütleri §3.2b / §3.3b ile aynı: B-K1, B-K2 (1 s kesmenin son 200 ms'i < 0.1 Hz), B-K3, B-K4.

**Karar (mekanik).**
- Bir yapılandırma şu durumda "geçer": açık döngüde (i), (ii), (iii) 3/3 seed'de, smoke'ta B-K1 ve B-K2 geçti. Bu, kullanıcının saydığı ölçüt seti.
- K1, B-K3 ve B-K4 de ölçülür ve raporlanır. Bunlardan biri, geçen bir yapılandırmada kalırsa karar kullanıcıya bırakılır.
- **Birden fazla geçerse tercih sırası:** FS > FG > BS > BG. Önce tam koku, sonra spiking APL (§3.2b'deki sıra).
- Seçilen yapılandırma final koşusunda koku AÇIK olarak kullanılır, `--nt-literature` ile.
- **Hiçbiri geçmezse koku final'de KAPALI kalır** (`--no-olfaction`, final_sB beyin girdisi). Bu, §3.2b'nin "yalnız besin glomerülleri" kararının yerine geçer. Gerekçe: v19 tam koşusunda besin glomerülleriyle de kalıcı durum oluştu, B-K1/B-K2 kaldı.
- Sonuç olduğu gibi raporlanır. Başka ayar, başka tablo ya da başka tip denenmez.
- Bu turda tam koşu ve DNp15 kalibrasyonu yok.

**§3.2c sonuçları (2026-10-01; kural ve ölçütler yukarıda, sonuçtan önce yazıldı ve değiştirilmedi).** Ayrıntı: REPORT_SENSORY_A2.md §3–4.
- Açık döngü (3 seed): FS ve BS (ii)'de 0/3 kaldı (KC %56–59). FG ve BG (i), (ii), (iii) ve K1'de 3/3 geçti.
- Smoke B-K2: FS 2.44, FG 1.53, BS 2.46, BG 1.53 Hz; **dördü de kaldı**. B-K1: FS 5.44 ve BS 5.18 kaldı; FG ve BG geçti. B-K3 ve B-K4 hepsinde geçti.
- **Karar: hiçbiri geçmedi → koku final'de KAPALI** (`--no-olfaction`, final_sB). `--nt-literature` varsayılan kapalı kalır.

### 3.3 DNp15 referansının geçersizleşmesi
- `data/dn_lr_reference.json` yalnız T4/T5 girdisiyle ölçüldü. Yeni görsel ve mekanik girdiler DNp15 tabanını değiştirir. Eski referans yeni ağda **geçersizdir**.
- **Yeniden kalibrasyon:**
  - Aynı sym_prog uyaranı, aynı protokol (2 s, 250–2000 ms), seed 0/1/2.
  - Yeni girdi setiyle, hangi aşamadaysa o bayraklar açık.
  - Yeni dosya: `data/dn_lr_reference_<inputset>.json`. Eskisi korunur.
- **Doğrulama yeni seed'lerle: 6/7/8.** 3/4/5 Adım 2 doğrulamasında ve final koşularında kullanıldı.
  - Ölçüt aynı: Adım 2 (a) açık döngü optomotor işareti, 4 koşulun ≥3'ünde doğru.
- Okuma hâlâ **post-hoc** (DNp15, Adım 2 kararı). Bu etiket kalır.
- MN9 eşiği (10 Hz) R0 eğrisinden geldi. K5'te kontrol edilir; eşik değiştirilmez.

### 3.3b Aşama B ölçütleri (önceden kayıtlı, 2026-10-01, smoke ve tam koşudan ÖNCE yazıldı)
Kapsam: `--vision-boundary` smoke'u (`--n-steps 20 --persist-steps 40`, tam beyin, `--hybrid --no-olfaction`, seed 3) ve tek tam koşu (seed 3, 300 adım, `--hybrid --vision-boundary --ablate-dn DNp15 --no-olfaction --no-video`). Karşılaştırma final_b (`flight_v12_hybrid_ablDN-DNp15_noOlf_final_b`). Hiçbir kazanç ayarlanmaz; DNp15 yeniden kalibrasyonu ve doğrulaması bu turda yok. Yön terimi `--ablate-dn DNp15` ile perch tabanında tutulur (final_b gibi).

- **B-K1, kaçak uyarılma** (tam koşu, kapalı döngü adım 0–299):
  - sürülmeyen nöronların (vbnd ve şeker dışı) ortalama hızı **< 5 Hz** (SPEC §3.1 K1 üst sınırı);
  - sürülmeyen nöronların adım başına hızında son %25'lik dilimin ortalaması ilk %25'liğin **≤ 1.5 katı**;
  - hiçbir baskın nöropilin (tüm nöronlar, L/R birleşik) ortalaması **> 50 Hz değil**.
- **B-K2, girdiler kesilince tabana dönüş:**
  - smoke'ta perch kalibrasyonundan sonra tüm girdiler **1 s** (40 adım) kesilir;
  - **geçer:** son 200 ms'de (adım 32–39) ağ ortalaması **< 0.1 Hz** (taban = girdisiz LIF ağı, gürültü yok);
  - ayrıca kayıt: 0.1 Hz altına ilk inilen adım ve K2'nin 100–200 ms penceresi;
  - tam koşuda varsayılan 8 adımlık kesmede K2 (100–200 ms < 0.1 Hz) kaydedilir.
- **B-K3, adım süresi ve RAM:** ortalama adım süresi ve beyin süresi final_b ile yan yana raporlanır (artış yüzdesi). Kabul: ortalama adım ≤ 2.0 s, tepe RSS ≤ 8 GB (§3.1 K3). Smoke'ta aşılırsa tam koşu yapılmaz.
- **B-K4, temassız MN9:** kapalı döngüde bacak–platform teması olmayan adımlarda MN9 (CB0701 L/R ortalaması, ham sayımdan Hz/nöron) ortalaması **< 10 Hz**. Perch adımları (şeker 0) ayrıca raporlanır.
- **B-K6, çift sayım (kayıt, geçti/kaldı değil):**
  - Sürülen her sınır nöronu için gerçekleşen spike hızı / FlyVis hedef Poisson hızı (kapalı döngü ortalamaları; hedef ≥ 1 Hz olan nöronlar). Tip başına medyan.
  - T4/T5 için ayrıca tip başına ortalama oranı (gerçekleşen / hedef), final_b'deki aynı oranla yan yana. final_b'de hedef `t45_type_rate`'ten gelir.
  - > 1.5 ise "çift sayım" olarak yazılır. Sınır kuralı değiştirilmez.
- **Rapor:** aktif nöron sayısı/oranı, nöropil tablosu, hop tablosu (§0 yöntemi, kaynak = sürülen girdiler); DN'ler (DNp07/DNp10 özellikle yaklaşma/alçalma/iniş pencerelerinde; DNp15 L/R tabanı, DNp01, DNg02, MDN, boyun MN, MN9) final_b ile yan yana; davranış (iniş, beslenme, kule teması/penetrasyon).

**Uygulamada SPEC §2.1'den sapmalar** (hepsi davranıştan önce, yalnız anatomi/FlyVis verisiyle; `data/vision_boundary_types.json`, `data/visual_transduction.json`):
1. **Kolonsuz nöronların kolonu:** SPEC'teki arbor-merkezi regresyonu doğrulamada başarısız oldu. Doğrulama seti: sürülen tiplerin kolonlu nöronları (referans tipler hariç), kendi kolonları gizli. Arbor-merkezi yöntemi bu 15,981 nöronun yalnız %22'sini ≤1 kolon içinde buldu (medyan 4 kolon hata). Birleşik merkez, çok nöropilli tiplerde (T5, T2a, T3) tek nöropil yüzeyinde durmuyor. Yerine, **kolonlu partnerlerin (pre+post, aynı hemisfer) sinaps ağırlıklı ortalama kolonuna en yakın kolon** kullanıldı: %97.1 ≤1 kolon, %77 tam isabet. Kolonlu partneri olmayan 51 nöronda SPEC'teki arbor-merkezi yöntemi kullanıldı. Sonuç: 25,096 kolonlu + 8,974 partner ortalaması + 51 arbor merkezi.
2. **Merkez kolonlar** (a_ref): FlyVis altıgen yarıçapı ≤ 10 (721 kolonun 331'i; kenar halkasında a0 sapıyor).
3. **Tepkisiz tip:** a_ref < 1e-3 (standart setin hiçbir uyaranına ölçülebilir pozitif tepki yok) olan tip grupta kalır, hızı 0 Hz'de tutulur. Yalnız **Tm4** (a_ref 1.1e-5, 1,490 nöron). Tm4 fiilen sürülmüyor, sadece refrakter süresi 0 (Poisson hedefi).
4. **Seyrek FlyVis kafesi:** Lawf1/Lawf2'nin FlyVis'te 123 düğümü var. Lawf2 nöronları tipin en yakın düğümüne eşlendi.
5. T4/T5 a_ref'i yeni standart setle (merkez kolonlar) yeniden ölçüldü. `t45_transduction.json` bayrak kapalıyken aynen kullanılır.

### 3.3c Final-v2: DNp15 yeniden kalibrasyonu (sB) ve doğrulama (önceden kayıtlı, 2026-10-02; doğrulama koşularından ÖNCE yazıldı)
Kullanıcı kararı (2026-10-02): koku kararı kesin, final'de beynin koku girdisi **KAPALI** (`--no-olfaction`). `--olfaction-full`, `--leg-grn`, `--nt-literature` kapalı. **Final yapılandırma (sB):** `--hybrid --vision-boundary --no-olfaction` + mevcut bacak rampası (varsayılan açık, b075aa9).

**Kalibrasyon** (§3.3 yöntemi, değişmeden; `scripts/make_dn_reference.py --vision-boundary`):
- Aynı sym_prog uyaranı (FlyVis standart ızgarası, iki gözde önden-arkaya, ayna simetrik), 2 s, 250–2000 ms, seed 0/1/2, temiz başlangıç.
- Fark yalnız girdi yolu: FlyVis → sınır katmanı (32 tip, `vbnd_L/R`) → FlyWire; beyin `olfaction=False`, spiking APL, NT değişmemiş.
- Yeni dosya `data/dn_lr_reference_sB.json`. Eski `data/dn_lr_reference.json` korunur ve bayraksız varsayılan kalır.
- Simülasyonda seçim açık bayrakla: `--dn-reference data/dn_lr_reference_sB.json` (HDF5 `meta/bridge/steer_reference_path`).
- Okuma formülü, K_STEER = 1, işaret (ipsilateral), τ = 50 ms, ±2.5 kırpma değişmez. Okuma hâlâ **post-hoc** (DNp15).

**Doğrulama** — ölçüt ve eşikler SPEC_BRAIN_CONTROL "Adım 2 kararları"ndaki ile **aynen**; yalnız girdi seti (sB), referans dosyası ve seed'ler farklı. **Seed 6/7/8** (0/1/2 kalibrasyon, 3/4/5 Adım 2 doğrulaması ve final koşuları). Tam beyin, DEV değil.
- **(a) Açık döngü optomotor işareti.** Uyaran dizileri sınır katmanından: `a0_visual.py --vision-boundary`, `a2_visual.py --vision-boundary --no-platform` (aynı sahneler, aynı kinematik). `a2_openloop.py --vision-boundary --seeds 6 7 8`, rapor `--dn-reference data/dn_lr_reference_sB.json`.
  - Koşullar ve beklenen işaret: `syn_yaw_ccw` SOL (turn < 0), `syn_yaw_cw` SAĞ, arena `yaw_R` SOL, arena `yaw_L` SAĞ.
  - Ölçüt: normal köprünün 250–1000 ms ortalama turn_bias işareti **4 koşul × 3 seed = 12/12** doğru.
- **(b) Kapalı döngü stabilizasyon** (hover + ani yaw bozulması; `a2b_perturb.py` ile analiz).
  - Komut: `fly_flight_brain_body_simulation.py --no-olfaction --vision-boundary --dn-reference data/dn_lr_reference_sB.json --spawn-air 440 -170 160 90 --hover --yaw-perturb 0.5 ±30 --n-steps 60 --seed {6,7,8} --no-video` [+ `--ablate-dn steer`] → 12 koşu.
  - `--hybrid` yok: hibrit `--spawn-air`'i dışlar ve HAND dönüş terimleri b2/b3'ü kirletir. Adım 2 kararlarıyla aynı deney tasarımı.
  - **b1:** normal koşuda ort. |ω| [t_on+0.4, t_on+0.5] < 0.5·ω_p (2.62 rad/s), 6/6.
  - **b2:** normal koşuda Δturn = ort. turn_bias [t_on, t_on+0.5] − ort. turn_bias [t_on−0.25, t_on], işareti bozulmaya zıt, 6/6.
  - **b3:** |Δψ_normal| < |Δψ_ablate| (aynı seed ve yön), 6/6.
  - (b) geçer ⇔ b1 ∧ b2 ∧ b3.
- **(c) Sabit sapma yok.** Açık döngü statik sahneler `perch`, `air_static`, `sym_static` (sınır katmanından): 250–1000 ms ort. turn_bias |.| < 0.3, **3 koşul × 3 seed = 9/9**. Kapalı döngü hover'ın bozulma öncesi [0.25, 0.5] s penceresi yalnız kayıt.
- **Doğrulama geçer ⇔ (a) ∧ (b) ∧ (c).**

**Karar (mekanik).**
- **Geçerse:** final koşularda DNp15 terimi aktif, `--dn-reference data/dn_lr_reference_sB.json` ile.
- **Geçmezse:** DNp15 terimi final koşularda `--ablate-dn DNp15` ile perch tabanında tutulur ve raporda yazılır. Başka okuma, kazanç ya da normalizasyon denenmez.
  - "Final koşularda" yalnız-beyin koşusunu (c) da kapsar: orada da yön terimi ablasyonla tabanda tutulur.
  - Ablasyon tabanı da referansa bağlıdır (perch hızı − referans). Final-v2'de her koşu sB referansını kullanır.

**Final koşular** (seed 3, 300 adım, `--no-video`, tam beyin; `run_final_v2.sh`, detached, `DONE_*` işaretleri; ortak bayraklar `--vision-boundary --no-olfaction --dn-reference data/dn_lr_reference_sB.json`):
- (a) `final_v2a`: `--hybrid` (+ `--ablate-dn DNp15` doğrulama geçmediyse);
- (b) `final_v2b`: `--hybrid --ablate-dn DNp15` (a zaten ablasyonluysa atlanır);
- (c) `final_v2c`: yalnız beyin (+ `--ablate-dn DNp15` doğrulama geçmediyse).

**§3.3c sonuçları (2026-10-02; ölçütler yukarıda, sonuçtan önce yazıldı ve değiştirilmedi).**

*Kalibrasyon* (`data/dn_lr_reference_sB.json`, seed 0/1/2): DNp15 L/R **22.1 / 63.6 Hz** (T4/T5 referansı 15.2 / 63.2); DNa02 17.9 / 16.2 (31.4 / 2.5). Seedler arası fark ≤ 4 Hz. Taban farkı −41.5 Hz, ortak ölçek 42.9 Hz.

*(a) Açık döngü optomotor işareti: GEÇTİ, 12/12.* turn_bias (+ = sağ), 250–1000 ms, s6/s7/s8:

| koşul | beklenen | normal | ham DNp15 L−R (Hz) |
|---|---|---|---|
| sentetik yaw, dünya CCW | SOL | −2.42 / −2.46 / −2.45 | +72.9 |
| sentetik yaw, dünya CW | SAĞ | +1.71 / +1.61 / +1.69 | −113.2 |
| arena yaw_R | SOL | −0.44 / −0.33 / −0.42 | −24.4 |
| arena yaw_L | SAĞ | +0.87 / +0.88 / +0.93 | −79.8 |

- Ablasyon (perch tabanı) +0.40 / +0.43 / +0.34. swap her koşulda işareti çeviriyor (tanım gereği).
- Kayıt: loom_L +0.07…+0.31 (beklenen SAĞ), loom_R +0.51…+0.61 (yanlış yön). sym_prog −0.02…+0.08 (referans uyaranı, beklendiği gibi ~0).

*(c) Sabit sapma: BAŞARISIZ, 0/9.*

| statik sahne | s6 / s7 / s8 | ham DNp15 L−R (Hz) | \|.\| < 0.3 |
|---|---|---|---|
| perch | +0.40 / +0.46 / +0.33 | −58.5 | 0/3 |
| air_static | +0.37 / +0.40 / +0.34 | −57.5 | 0/3 |
| sym_static | −0.92 / −0.92 / −0.87 | −2.8 | 0/3 |

- Adım 2 kararlarında perch/hover eşiğin altındaydı (+0.09…+0.26); sB'de referans DNp15 L'si yükseldi (15.2 → 22.1 Hz), statik arena sahnelerinde DNp15 L hâlâ ~0 → sağa sapma +0.33…+0.46.
- sym_static'te DNp15 iki tarafta da sessiz; taban çıkarımı bunu güçlü bir sol komut olarak okuyor (Adım 2 kararlarındaki aynı formül sorunu; −1.22 → −0.92).
- Kapalı döngü hover, bozulma öncesi [0.25, 0.5] s (kayıt): +0.02 / +0.17 / −0.08.

*(b) Hover + 30° yaw bozulması: BAŞARISIZ (b1 6/6, b2 3/6, b3 3/6).* `simulations/flight_v30…v41_*_v2val_data.h5`.

| seed | bozulma | normal Δturn | normal Δψ (°) | ablasyon Δψ (°) | \|ω\| son pencere normal / abl. (rad/s) |
|---|---|---|---|---|---|
| 6 | +30 (sola) | +0.29 ✓ | +8.8 ✓ | +30.0 | 0.63 / 0.29 |
| 7 | +30 | +0.11 ✓ | −1.5 ✓ | +30.0 | 0.88 / 0.18 |
| 8 | +30 | +0.31 ✓ | −18.6 ✓ | +30.0 | 1.68 / 0.29 |
| 6 | −30 (sağa) | +0.20 ✗ | −35.8 ✗ | −30.0 | 0.10 / 0.29 |
| 7 | −30 | +0.03 ✗ | −48.7 ✗ | −30.0 | 1.25 / 0.18 |
| 8 | −30 | +0.29 ✗ | −74.0 ✗ | −30.0 | 2.03 / 0.29 |

- b1 ablasyonda da 6/6 (pasif sönüm; önceden yazıldığı gibi tek başına anlamsız).
- Sola bozulmada beyin 3/3 sağa karşı-dönüş üretiyor ve sapmayı azaltıyor. Sağa bozulmada da Δturn > 0 (yine sağa), yani sapmayı 3/3 **büyütüyor** (−36…−74°). Adım 2 kararlarındaki tek yönlü stabilizasyonun aynısı, daha belirgin.
- Not: ablasyon koşularında s6 ve s8 sayıları birebir aynı (hover tabanı iki seed'de aynı çıktı; filtrelenmiş taban hızları seyrek spike sayılarından geliyor). Kayıt.

**Karar (mekanik): doğrulama GEÇMEDİ** ((a) geçti; (b) ve (c) kaldı). Final koşularda DNp15 terimi `--ablate-dn DNp15` ile perch tabanında: final_v2a ablasyonlu hibrit, final_v2b atlanır, final_v2c ablasyonlu yalnız beyin. Başka okuma, kazanç ya da normalizasyon denenmedi.

**Final ölçütleri** (SPEC_BRAIN_CONTROL "Dürüst hibrit final" ile aynı, değişmeden): S1 touchdown'a kadar kule teması yok (adım sonu bayrağı ve adım-içi penetrasyon 0); S2 touchdown'dan sonra en az bir adımda `is_feeding` = 1; başarı = S1 ∧ S2. Ayrıca §3.3b'nin B-K1, B-K3, B-K4'ü kayıt olarak. Final-v1 (final_a/b/c) ile yan yana: aktif nöron oranı, iniş, beslenme, MN9, dönüş payları, DN'ler. Rapor: `REPORT_FINAL_V2.md`.

### 3.3d Doğallık turu ve ek kontrol (2026-10-02)
Final yapılandırma aynı: `--hybrid --vision-boundary --no-olfaction` (+ `--dn-reference data/dn_lr_reference_sB.json`, bacak rampaları). §3.3c'nin ön-kayıtlı sonuçları (final_v2a S1 ✗, S2 ✓; final_v2c ✗) **aynen kalır**; bu bölüm onları değiştirmez ve yeniden yorumlamaz.

**Ek kontrol: `--no-brain-steer` — sonradan eklendi (post-hoc).**
- final_v2a'da DNp15 terimi ablasyonla perch tabanında tutuldu. Bu taban sB referansıyla sabit **+0.244** sağa dönüş demek (REPORT_FINAL_V2 "Ne beyinden"). Yani ablasyon "beyinsiz" bir taban değil.
- `--no-brain-steer`: DNp15 dönüş terimi **tam 0**; perch tabanı sabiti de yok. DNp15 okuması (`steer_norm`, `dn_readout_rate`) hesaplanır ve kaydedilir, komuta girmez. Hibritte `turn_total = clip(turn_hand + turn_flyvis)`; yalnız beyin kolunda yön komutu 0.
- Bu kontrol final_v2a'nın sonucu görüldükten **sonra** eklendi. Bu yüzden ön kayıt değil; sonucu "ek kontrol" olarak raporlanır, final_v2a'nın yerine geçmez.
- Çıktı adında `_noBrSteer`; HDF5 `meta/flags/no_brain_steer`, `meta/bridge/turn`.

**Baş sabitleme refleksi `--head-reflex` (HAND refleks, VARSAYIM; sabitler koşulardan ÖNCE yazıldı, sonradan ayarlanmaz).**
- **Eklemler** (FlyGym MJCF; eksenler ölçüldü, adlar değil): `joint_Head_roll` gövde z'si etrafında → **yaw**; `joint_Head` gövde y'si → **pitch** (+ = burun aşağı); `joint_Head_yaw` gövde x'i → **roll** (+ = sağ aşağı). FlyGym'in kendi "thorax" baş stabilizasyonu da `joint_Head_yaw`'ı roll için kullanıyor. MJCF'te eklem sınırı yok (`limited=0`); pasif yay 10, sönüm 1 (FlyGym `neck_stiffness`, `non_actuated_joint_damping`, değişmez).
- Göz kameraları `Head` gövdesine bağlı (`LEye_cam_body → LEye → Head`). Baş dönünce FlyVis girdisi değişir; raporlanır.
- **Refleks (her fizik alt adımında, beyinden geçmez; haltere refleksi gibi):** ω_b = gövde açısal hızı (toraks ekseninde). Eksen başına hedef:
  dθ*/dt = −G·ω_b − θ*/τ_rc, |θ*| ≤ θ_max.
  - **G_yaw = 0.6**: Drosophila baş hareketi yaw retinal kaymasını %60'a kadar azaltıyor (Cellini, Salem & Mongeau 2022, *PLoS Comput Biol* 18:e1011746 / bioRxiv 2021.12.29.474433).
  - **G_roll = G_pitch = 0.5**: blowfly baş roll kompanzasyonu toraks roll'unun ~%50'si (Hengstenberg 1988, *J Comp Physiol A* 163:151, "Mechanosensory control of compensatory head roll…"). Pitch için Drosophila ölçümü bulunamadı; roll ile aynı (VARSAYIM).
  - **θ_max = 15°** her eksende: Drosophila baş yaw çalışma aralığı ~±15° (Cellini et al. 2022). Roll/pitch için aynı sınır (VARSAYIM). Bu sınır testteki "eklem sınırı"dır.
  - **Yaw reset sakkadı:** |θ*_yaw| ≥ **9°** olunca θ*_yaw = 0 (Cellini et al. 2022: düzgün stabilizasyon ~±9°'ye kadar, sonra reset sakkadı). Roll/pitch'te reset yok.
  - **τ_rc = 0.2 s** (merkeze dönüş sızıntısı): literatür değeri bulunamadı, VARSAYIM.
- **Aktüatör:** üç eklemde MuJoCo position aktüatörü, k_p = 190 (N·mm/rad birimleri modelinkiyle aynı). Pasif yay 10 ve sönüm 1 ile birinci derece izleme zaman sabiti τ = 1/(190 + 10) = **5 ms** ≈ haltere aracılı baş refleksi gecikmesi (~5 ms, Hengstenberg 1988/1991; gecikme zaman sabiti olarak kullanıldı, VARSAYIM). DC izleme kazancı 190/200 = 0.95 (pasif yay nedeniyle; telafi edilmez).
- Kayıt (adım başına): baş eklem açıları ve hedefleri (yaw/pitch/roll), alt adım ortalaması bakış ve gövde yaw hızı (toraks z'si etrafında), dönüşteki alt adım sayaçları.
- Bayrak kapalıyken model değişmez (aktüatör eklenmez).
- **Correction note (2026-10-05; added after the runs; the pre-registered text above is unchanged):** the constants G_yaw 0.6, θ_max 15° and the 9° yaw reset saccade are hand-set; motivated by the fly gaze-stabilisation literature; not traced to a specific source. The citation given above ("Cellini, Salem & Mongeau 2022, *PLoS Comput Biol* 18:e1011746 / bioRxiv 2021.12.29.474433") mixes two papers: Davis, B. A. & Mongeau, J.-M. (2023), *PLoS Comput Biol* 19, e1011746, doi:10.1371/journal.pcbi.1011746, and Cellini, B., Salem, W. & Mongeau, J.-M. (2022), *PNAS* 119, e2121660119, doi:10.1073/pnas.2121660119. Both are related literature only; neither was checked to contain these values. The values themselves were not changed.

**Testler (`tests/flight`, koşulardan önce):** BADQACC yok; baş açısı |θ| ≤ 15° (ölçülen eklem açısı); dönüş sırasında bakış yaw hızı gövdeninkinden küçük (aşağıdaki B-H3 tanımıyla, gövde-yalnız sabit dönüş testi).

**Duruşlar `--postures` (HAND, VARSAYIM; koşulardan önce, render + hover/perch kontrolüyle belirlendi, davranışa göre ayarlanmaz).** `flight/config.py`.
- **Uçuş duruşu** (`FLIGHT_POSE_OFFSETS`, tuck pozunun yerine): ön bacaklar önde ve başın altında katlı (FCoxa −35°, FFemur −45°, FTibia +75°), orta ve arka bacaklar karın boyunca geride (Coxa +30°, Femur +15°, Tibia −25°), Coxa_roll −25…−35° (gövdeye yakın). FlyGym'de Coxa − = ileri (render ile doğrulandı). Drosophila uçuşunda bacak açısı ölçümü bulunamadı; duruş nitel tarif, uyum değil. Eski tuck pozu tek bir "toplu" poz: bacakları gövde altında aşağı sarkık topluyordu.
  - Kalkışta toplama refleksi (75 ms) ve yaklaşmada açılma (150 ms) aynen; yalnız hedef poz değişti.
- **İniş sonrası:** açılma rampası zaten FlyGym'in doğal durma duruşuna (`PreprogrammedSteps().default_pose`) gidiyor; touchdown'da poz atlaması yok.
- **Beslenme duruşu** (`FEED_POSE_OFFSETS`): ön bacak daha bükük (FFemur −15°, FTibia +30°), arka bacak daha uzun (HFemur +15°, HTibia −20°). Kaide üzerinde ölçülen öne eğilme **+5.7°** (burun aşağı; koşulardan önce). Geçiş 0.3 s rampa (VARSAYIM), iki yönde.
  - Tetikleyici: platformda ve MN9 hortum kararı (BRAIN) açıkken `feed`, değilken `stand`. Duruşun kendisi HAND.
- Kayıt: `behavior/leg_pose` (0 stand, 1 uçuş/tuck, 2 feed), `meta/postures`.

**Doğallık koşuları ve ölçütleri (önceden kayıtlı, 2026-10-02; smoke ve koşulardan ÖNCE yazıldı, sonradan değiştirilmez).**
Ortak: seed 3, 300 adım, `--no-video`, tam beyin (DEV değil), `--vision-boundary --no-olfaction --dn-reference data/dn_lr_reference_sB.json --no-brain-steer --head-reflex --postures`; `run_natural.sh`, detached, `DONE_*` işaretleri.
- **n1:** `--hybrid` + ortak bayraklar.
- **n2:** yalnız beyin + ortak bayraklar (yön komutu 0; VNC programı, irtifa hedefi yok).

Ölçütler (tanımlar §3.3c ve §3.3b'deki ile **aynen**):
- **S1:** touchdown'a kadar kule teması yok (adım sonu bayrağı ve adım-içi penetrasyon 0). **S2:** touchdown'dan sonra en az bir adımda `is_feeding` = 1. **Başarı = S1 ∧ S2** (n1 ve n2 için ayrı ayrı).
- **B-K1** (sürülmeyen < 5 Hz; son/ilk %25 ≤ 1.5; hiçbir nöropil > 50 Hz), **B-K3** (ort. adım ≤ 2.0 s, tepe RSS ≤ 8 GB), **B-K4** (temassız adımlarda MN9 ort. **< 10 Hz**). Kayıt olarak, geçti/kaldı yazılır.
- **Baş refleksi** (kayıt ölçütleri, geçti/kaldı yazılır):
  - **B-H1:** koşu boyunca BADQACC yok (log'da `BADQACC` uyarısı 0).
  - **B-H2:** her adımda baş eklem açısı |θ| ≤ 15° (`head_q_absmax`, alt adımların en büyüğü), üç eksen.
  - **B-H3:** kanatlar açık adımlarda, dönüş alt adımlarının (|gövde yaw hızı| > 1 rad/s) **> %50**'sinde |bakış yaw hızı| < |gövde yaw hızı| (Σ`head_turn_sub_lt` / Σ`head_turn_sub`). Dönüş alt adımı yoksa "uygulanamaz". Not: süren bir dönüşte reset sakkadları yüzünden bakışın **zaman ortalaması** gövdeninkine eşit olmak zorunda; ölçüt bu yüzden alt adım oranı üzerinden.
- **Kayıt (ölçüt değil):** iniş zamanı/hızı, beslenme adımı ve MN9, besine en yakın uzaklık, aktif nöron oranı (toplam/sürülen/sürülmeyen), DN pencere tabloları, dönüş payları; baş: yaw reset sayısı, açı dağılımı, bakış/gövde yaw hızı; görsel girdi: sınır katmanı hedef hızları (`vbnd_type_rate`) ve DNp15/DNa02 hızları final_v2a ve final_sB ile yan yana.
  - Sınırlama, önceden yazıldı: n1 final_v2a'dan üç şeyle (yön terimi, baş, duruş) ayrılıyor ve rota da değişiyor. Baş refleksinin görsel girdiye ve DN'lere etkisi bu koşulardan **ayrıştırılamaz**; yalnız yan yana kayıt yapılır, nedensellik iddiası yok.

**§3.3d sonuçları (2026-10-02; ölçütler yukarıda, sonuçtan önce yazıldı ve değiştirilmedi; ayrıntı REPORT_FINAL_V2 §6).**
- **n1** (hibrit): **S1 ✓, S2 ✓** (touchdown 3.02 s, kule teması/penetrasyon 0, 180 beslenme adımı). B-K1/K3/K4 geçti. B-H1/H2/H3 geçti (BADQACC 0; en büyük |θ| 7.3°; %99.8).
- **n2** (yalnız beyin): S1 ✗, S2 ✗ (adım 36'da kule 1 yüzüne çarptı, 264 temas adımı, en büyük penetrasyon 35.3 µm). B-K1/K3/K4 geçti (adım 1.454 s). B-H1/H2/H3 geçti (%96.2).
- Post-hoc ek kontrol: final_v2a'nın ön-kayıtlı S1 ✗ sonucu aynen geçerli.

### 3.4 Diğer riskler
- **Fotoreseptör sinaps işareti:**
  - Modelde R1-6→L1/L2 sinapsları %65 uyarıcı. Biyolojide histamin klorür kanalıyla inhibitör.
  - FlyWire NT sınıflayıcısında histamin sınıfı yok.
  - R1-6 sürülmediği için B'yi etkilemiyor. R7 (sürülüyor) çıkışı %36 inhibitör işaretli. İşaret değiştirilmez; kayıt.
- **Koku kalıcı durumu:** Adım 0'da yalnız 6 glomerül 8 Hz'de bile tetikledi. 53 glomerülde neredeyse kesin. §3.2 bu yüzden var.
- **T4d seçici değil; T5 zayıf seçici** (FlyVis modeli). Sınır katmanında da benzer model sınırları olacak. Kayıt.
- **Taraf asimetrisi:** görsel yoldaki konnektom asimetrisi (SPEC_BRAIN_CONTROL Karar 3) ve SA_DMetaN 135/232. Simetrik uyaranla taraf farkı ölçülüp raporlanır.
- **Statik sahne tonik sürüşü:** 34k sınır nöronu statik dokulu sahnede de ateşleyebilir. Ağ tabanı yükselir. K1 bunu ölçer.

---

## 4. Aşamalı plan
Her aşamanın yapısı:
- bayrak (varsayılan KAPALI);
- `pytest tests/`;
- smoke `--n-steps 20`;
- açık döngü ölçüt betiği (3 seed);
- aktif nöron oranı + nöropil tablosu + hop tablosu (§0 betiği, HDF5'ten);
- davranış karşılaştırması.

Davranış karşılaştırması: aynı spawn, aynı seed. Aşamanın bayrağı açık ve kapalı (final_a ayarı, `--hybrid`); ayrıca yalnız beyin (final_c ayarı). Ölçülenler:
- besine uzaklık;
- kule teması / adım-içi penetrasyon;
- MN9 ve beslenme;
- dönüş terimi payları;
- BADQACC.

Tam koşuları kullanıcı başlatır; komut verilir. Çıktı adlarında aşama etiketi geçer (`_sA`, `_sB`, …). Mevcut yürüyüş kodu ve `tests/` bozulmaz.

| aşama | bayrak | içerik | ölçütler | tahmini süre |
|---|---|---|---|---|
| **A, koku tam** | `--olf-all` (+ `--apl-graded` varyantı) | H&C spontan tablosu (önce kullanıcı onayı); 53 glomerül; besin kokusu 6 glomerülü artırır | §3.2 (i)–(iii), K1–K5 | tablo aktarımı 0.5 gün; kod + test 1 gün; açık döngü 2 varyant × 3 seed ~1 saat; smoke ve 300 adımlık koşular ~30 dk |
| **B, görme sınır katmanı** | `--vis-boundary` (T4/T5 grubunun yerine geçer), `--record-flyvis` | kolonsuz atama, `visual_transduction.json` (bir kez), 32 tip, gösterim kaydı | K1–K6; Adım 2 (a) optomotor matrisi yeniden (yalnız kayıt); T4/T5-only ile aktif oran / nöropil karşılaştırması | kod + kolon atama testleri 1.5–2 gün; transdüksiyon kalibrasyonu ~30 dk; açık döngü ~1 saat |
| **C, mekanik + bacak tadı** | `--mech` (JO, haltere, kanat), `--leg-grn` | sensör türetme (v_air, ω, Φ), bacak GRN kNN seçimi + kısa MN9 testi | K1–K5; JO L/R lateral rüzgâr testi (açık döngü, sol/sağ rüzgârda JO-C/E farkı); hover vs seyir ağ tabanı | 1.5 gün; açık döngü ~1 saat |
| **D, hepsi birlikte** | `--olf-all --vis-boundary --mech --leg-grn` (A'nın ana hat varyantıyla) | DNp15 referansı yeniden (seed 0/1/2), doğrulama seed 6/7/8 | K1–K5, §3.3; final_a/b/c tasarımının tekrarı (seed 3 + 6/7/8) | 1 gün + koşular (kullanıcı başlatır; her biri ~10 dk) |

**Video etiketi (her aşamada, kalıcı):**
- "Yön bulma, irtifa, iniş: EL YAPIMI (koku haritası) · Beyin: \<o koşudaki beyin kararları\>".
- İkinci kısım HDF5 `meta/flags` ve `meta/bridge`'ten otomatik üretilir. Örnek: "Beyin: dönüş katkısı DNp15 (post-hoc), beslenme MN9".
- Yalnız beyin koşularında ilk kısım, o koşuda gerçekten el yapımı olanları listeler (`meta/hand_made`).
- Ayrıntı §8'de.

---

## 5. Toplam tahmini süre
- Geliştirme: ~6–7 gün (A 1.5, B 2, C 1.5, D 1, video turu 1).
- Hesaplama: açık döngü ölçümleri ~4 saat. Kapalı döngü koşuları aşama başına ~30–60 dk (kullanıcı başlatır).

## 6. Gelecek iş
- **MANC eşlemesi.** Stürner et al. (FlyWire↔MANC DN/AN eşlemesi; *Nature* 2025, künye doğrulanacak) ile AN'ler VNC giriş nöropiline (bacak / kanat / haltere / boyun) göre gruplanır. Sonra bacak teması, bacak propriosepsiyonu ve kanat yükü AN'ler üzerinden sürülür. Yeni veri dosyası gerekir.
- Oselus: dorsal parlaklık kamerası.
- JO-A/B: kanat yakın alan sesi.
- Sıcaklık/nem alanı.
- **Koku kalıcı durumu** (Aşama A/A2; REPORT_SENSORY_A, REPORT_SENSORY_A2). Spontan ORN girdisi AL'nin LN/PN döngüsünü kendini sürdüren bir duruma sokuyor; tüm girdiler kesilince ağ sönmüyor (B-K2 dört yapılandırmanın dördünde kaldı, `--nt-literature` ile de). Olası eksik mekanizmalar (hipotez, test edilmedi):
  - LN'ler arası ve LN–PN **gap junction**'ları (konnektomda yok; yalnız kimyasal sinaps);
  - ORN/PN/LN **adaptasyonu** (uniform LIF'te yok);
  - **kaynaksız lLN2 / v2LN tipleri** (lLN2X/lLN2F/lLN2T/lLN2P, v2LN30 vb.): literatür NT'si yok, modelde çoğu uyarıcı.
  Final'de beynin koku girdisi bu yüzden kapalı.
- **Bacak GRN → MN9 yolu çalışmıyor.** Bağlantıyla seçilen 12 SA_VTV_2 nöronu 100 Hz'de MN9'u 0.0 Hz'de bırakıyor (3/3 seed; REPORT_SENSORY_A §4). Yol 2–3 hop; mevcut ağırlıklarla eşiğe ulaşmıyor. `--leg-grn` varsayılan kapalı kalır.

---

## 7. Biyolojik kontrol haritası ve doğallık (kod yok)
**İlke:** her işlevi gerçek sinekte onu kim kontrol ediyorsa o kontrol etsin.
- Beyin, davranış kararlarını verir (DN'ler).
- VNC ritmi, adım dizisini ve refleksleri yürütür. Bunlar el yapımı ama biyolojik zamanlamayla.
- Refleksler beyinden geçmez.
- Hareketler doğal olmalı; ani poz atlaması yok.

### 7.1 Tablo

| işlev | gerçek sinekte | bizde şu an | hedef |
|---|---|---|---|
| Kalkış | Görsel looming → dev lif DNp01 ile hızlı kaçış; ya da DNp01'siz yavaş, gönüllü kalkış (von Reyn et al. 2014, *Nat Neurosci* 17:962) | HAND zamanlayıcı + kaldırma artışı. DNp01 kalkışta 0 Hz (final_a/b) | Karar adayı: DNp01 (looming varsa) ya da HAND zamanlayıcı "gönüllü kalkış" etiketiyle. Kalkış mekaniği VNC'de |
| Uçuşta bacak toplama | Tarsal temas kaybı refleksi, VNC (Fraenkel 1932, tarsal refleks; künye doğrulanacak) | `set_legs("tuck")` tek adımda, ani poz değişimi | VNC refleksi: tarsal temas kaybı + kanat açık → PD hedef rampası, ~50–100 ms (VARSAYIM; süre literatürden doğrulanacak) |
| İniş bacak açılması | Görsel genişleme → DNp07/DNp10 (Ache et al. 2019, *Nat Neurosci*, künye doğrulanacak); van Breugel & Dickinson 2012 (*J Exp Biol*); Tammero & Dickinson 2002 (*J Exp Biol* 205:2785) | HAND: yaklaşma yarıçapında `set_legs("stand")`, ani | Karar: DNp07 + DNp10 > eşik (MN9 yaklaşımı). Hareket: PD rampası, literatür süresiyle |
| İrtifa / kolektif güç | DNg02 popülasyonu (Namiki et al. 2022) + VNC | HAND (irtifa hedefi, tırmanma tabanı). DNg02 her koşulda 0 | Değişmez: "konnektomdan okunamadı". D aşamasında DNg02 yeniden ölçülür (kayıt) |
| Dönme (yaw) | DNa02 / DNp15 / DNb06 vb. + haltere refleksi (Namiki et al. 2018, *eLife* 7:e34272; Rayshubskiy et al. 2020, bioRxiv) | BRAIN (DNp15, post-hoc) + HAND koku haritası + FLYVIS | HAND koku haritası, D'de yalnız beyin kolunda kapalı |
| Baş stabilizasyonu | Optik akış → LPTC (HS/VS) → DN'ler ve boyun motor nöronları (26 boyun MN beyinde, `brain_motor_neuron`); Hengstenberg 1993 (blowfly) | Baş sabit; boyun eklemleri aktüatörsüz | §7.3 |
| Platformda durma / yürüme | MDN (geri; Bidaye et al. 2014, *Science* 344:97), oDN1 (ileri; Bidaye et al. 2020, *Neuron* 108:469), DNp09 | Landed: sabit duruş + yapışma | Adaylar §7.4'te; hepsi 0 Hz. Düşük öncelik |
| Hortum | MN9 (Shiu et al. 2023, beyin MN'i) | BRAIN: MN9 > 10 Hz → `is_feeding`. FlyGym'de hortum eklemi yok | Değişmez; gösterim kaydı |
| Anten temizliği | JO-F / kıl uyarımı → aBN → aDN komut zinciri (Hampel et al. 2015, *eLife* 4:e08758) | Yok | Yok: tetikleyici uyaran yok (toz). FlyWire'da "aDN" adı başka bir nörona (SMP029, Nojima 2021 kur yapma aDN'i) ait; karıştırılmamalı |
| Haltere refleksi | Haltere afferent → kanat/boyun MN, VNC, beyinden geçmez (Fayyazuddin & Dickinson 1996) | REFLEX: haltere PD, her fizik alt adımında | Değişmez. C'de beyin afferentlerin kopyasını alır |

### 7.2 Bacaklar
- Şu an iki sabit duruş var (`stand`, `tuck`; `flight/body.py:leg_poses`). Geçiş tek adımda, ani.
- **Kalkışta toplama (VNC refleksi):**
  - Tetikleyici: tarsal temas kaybı ve kanat açık. Bu bir **refleks**, beyinden geçmez.
  - Hareket: eklem hedefi stand → tuck, doğrusal ya da kosinüs rampası, T_tuck ≈ 50–100 ms (VARSAYIM). PD kontrolcü mevcut aktüatörler.
- **İnişte açılma (beyin kararı):**
  - Karar: DNp07 + DNp10 filtreli hızı (τ = 50 ms) > eşik.
  - Hareket: tuck → stand, T_ext ≈ 100–200 ms (VARSAYIM; Tammero & Dickinson 2002 ve van Breugel & Dickinson 2012'den doğrulanacak).
  - Eşik ve ablasyon kontrolü §7.4'te.
- Risk: DNp07/10 iniş sırasında 0 Hz (§7.4). Karar beyinden gelirse bacaklar hiç açılmaz ve iniş sert olur.
  - Bu olduğu gibi raporlanır. HAND zamanlayıcı yalnız `--legacy-landing` bayrağıyla kalır.

### 7.3 Baş
- FlyGym MJCF'te `joint_Head` (pitch), `joint_Head_roll` ve `joint_Head_yaw` var. Mevcut kurulumda aktüatörsüzler. Göz kameraları başa bağlı.
- **Öneri:**
  - Okuma: 26 boyun MN'i (13 L / 13 R, beyinde).
  - Dönüşüm: yaw = k · (L − R), roll benzer. Sabit doğrusal köprü, VARSAYIM.
  - Uygulama: baş eklemlerine PD.
  - El yapımı kısım: köprü kazancı ve PD.
  - Beyinden gelen kısım: HS/VS → DN/boyun MN yolu (konnektom).
- final_a/b'de boyun MN'leri **0–0.9 Hz**, fiilen sessiz. B ve D aşamalarından sonra yeniden ölçülür.
- Risk:
  - Baş dönerse görüş de döner. Bu biyolojik olarak doğru ama kapalı döngüyü değiştirir.
  - Kamera/baş geom'u temas setine dahil. Arena temas parametreleri değişmez; sinek–arena pair'leri FlyGym varsayılanında kalır.

### 7.4 Beyin kararı adayları: final_a/b'de hızlar (yalnız okuma, Hz/nöron, L/R)
Pencereler (final_a):
- perch kalibrasyonu: adım −18…−9;
- kalkış: ilk 4 adım;
- seyir 9–60, yaklaşma 61–99, alçalma 100–113;
- touchdown: adım 114, ±4 adım;
- landed.

final_b'de touchdown adım 122. Tek nöronda 4 adımda 1 spike = 10 Hz; çözünürlük düşük.

| DN | n (L/R) | perch | kalkış | seyir | yaklaşma | alçalma | iniş −4…0 | iniş 0…+4 | landed |
|---|---|---|---|---|---|---|---|---|---|
| DNp01 (dev lif) | 1/1 | 0 / 4.4 | 0 / 0 | 1.5 / 2.3 | 2.1 / 6.2 | 0 / 0 | 0 / 0 | 0 / 10 | 0 / 0 |
| DNp07 | 1/1 | 4.4 / 8.9 | 0 / 0 | 0.8 / 1.5 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| DNp10 | 1/1 | 17.8 / 0 | 0 / 0 | 3.8 / 0 | 1.0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| DNa02 | 1/1 | 31 / 0 | 30 / 0 | 45 / 20 | 52 / 11 | 40 / 11 | 20 / 10 | 20 / 10 | 15 / 3 |
| DNp15 | 1/1 | 4.4 / 53 | 0 / 50 | 4.6 / 61 | 8.2 / 61 | 0 / 51 | 0 / 50 | 0 / 50 | 0 / 36 |
| MDN | 2/2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| DNp09 (+DNp71 ad eşleşmesi) | 2/2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| DNa01 (+DNae001) | 2/2 | 0 | 0 | 1.2 / 0.8 | 1.0 / 2.1 | 0 | 0 | 0 | 0 / 0.1 |
| DNg02 (25) | 13/12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| boyun MN | 13/13 | 0 | 0 | 0.2 / 0.8 | 0.6 / 0.9 | 0 | 0 | 0 | 0 |

- final_b aynı tablo: değerler aynı mertebede.
  - DNp07/DNp10 seyirden sonra 0.
  - DNp01 R, inişten önceki 4 adımda 10 Hz (1 spike).
  - DNa02 iniş −4…0'da L 60 / R 10.
- oDN1: FlyWire annotations'ta bu adla bir nöron bulunamadı. Bidaye 2020'deki kimlik eşlemesi gerekiyor.
- Okuma: **iniş adayları (DNp07/10) inişte sessiz.** Mevcut girdilerle iniş kararı beyinden gelmez. Yürü/dur adayları da tamamen sessiz.
  - Bu, B ve D aşamalarından sonra yeniden ölçülür. Genişleme yolu sınır katmanıyla (T2/T3, Tm, LPLC/LC girdileri) güçlenebilir; bu bir hipotez, iddia değil.

**Önceden kaydedilecek eşik + ablasyon** (MN9 yaklaşımı; her biri davranıştan önce):
- **İniş (DNp07+DNp10, L+R ort.):**
  - Eşik = açık döngü "yaklaşan platform" uyaranı (150→10 mm, 60 mm/s) ile "statik hover" tepkisinin orta noktası. 3 seed, D girdi setiyle, bir kez.
  - Kontroller: `--ablate-dn landing` (perch/hover tabanına sabit) → bacaklar açılmaz; temassız erken açılma oranı kayıt.
  - Başarı: platformdan ≤ 20 mm'de ve temas öncesi açılma, 3/3 seed.
- **Kalkış (DNp01):**
  - Eşik = looming uyaranı (R3 protokolü) ile perch orta noktası.
  - Kontrol: `--ablate-dn dnp01`.
  - Başarı: looming varken kalkış, yokken kalkış yok.
  - Gönüllü kalkış HAND olarak kalır ve öyle etiketlenir.
- **Yürü/dur (MDN, oDN1, DNp09):** şu an sessiz. Platformda yürüme eklenirse eşik aynı yöntemle belirlenir. Kontrol: ablasyon. Düşük öncelik.
- **Dönme (DNa02):** yalnız kayıt (Adım 2 kararı); DNp15 ana okuma, post-hoc.

### 7.5 Önceliklendirme (doğallık katkısı / risk / maliyet)

| sıra | iş | doğallık | risk | maliyet | not |
|---|---|---|---|---|---|
| 1 | Bacak rampaları (toplama refleksi + açılma rampası; açılma tetikleyicisi şimdilik HAND) | yüksek: ani poz atlaması kalkar | düşük | 0.5 gün | Temas/yapışma testleri (`tests/flight`) tekrar |
| 2 | Video: kanat hareket bulanıklığı (§8) | yüksek (görsel) | çok düşük (yalnız render) | 0.5–1 gün | |
| 3 | İniş açılma kararı DNp07/10 | orta–yüksek: karar beyinde | **yüksek**: şu an sessiz, sert iniş | 0.5 gün + ölçüm | D'den sonra |
| 4 | Baş stabilizasyonu (boyun MN) | orta | orta: görüş/kapalı döngü değişir, MN'ler sessiz | 1–1.5 gün | D'den sonra |
| 5 | Kalkış DNp01 kararı | orta | orta: looming uyaranı deney tasarımı | 0.5 gün | |
| 6 | Platformda yürüme / durma | düşük–orta | yüksek: DN'ler sessiz, yürüme CPG entegrasyonu | 2+ gün | |

**Sınırlar:**
- Aerodinamik stroke-ortalamalı (quasi-steady). Kanat açısı görsel; kuvvet stroke içinde değişmiyor.
- Hortum eklemi yok.
- Sessiz DN'ler: DNg02, DNp07/10 inişte, MDN/oDN1/DNp09, boyun MN.
- Anten temizliği uyaranı yok.
- Baş eklemleri ve arista aktüatörsüz.

---

## 8. Video (yalnız render; yeni koşulardan sonraki video turunda)
- **Kaldırılır:** takip kamerasındaki renkli stroke zarfı yelpazeleri (L mavi, R turuncu). Bunlar `render_flight_video_v2.py:370` `envelope()` ve `:760`'taki etiket.
- **Yerine kanat hareket bulanıklığı:**
  - Her karede bir çırpma döngüsü boyunca kanadın N ≈ 16 pozisyonu üst üste, düşük opaklıkla çizilir. Kanat geom'unun kopyaları, gerçek kanat rengiyle, renksiz.
  - Faz noktaları φ_k = 2πk/N. Stroke açısı = Φ_s/2 · cos φ_k, kaydedilen L/R genlikle. Frekans kaydedilen `stroke_freq` (218 Hz). Kamera pozlama süresinin bir döngüyü kapsadığı varsayılır.
  - Opaklık sinüzoidal hareketin kalış yoğunluğuyla orantılı: dönüş uçlarında daha koyu. Gerçek kameradaki yarı saydam bulanık disk görünümü bu.
  - Kanat kapalıyken bulanıklık yok.
- **HUD'da L/R genlik kalır.**
- **Kalıcı etiket:** "Yön bulma, irtifa, iniş: EL YAPIMI (koku haritası) · Beyin: \<o koşudaki beyin kararları\>". HDF5 meta'dan otomatik üretilir (§4).
- **FlyVis gösterim katmanı:**
  - Beyin panelinde ayrı katman, "FlyVis (gösterim, sürülmez)" etiketiyle.
  - Sürülmeyen FlyVis tipleri, eşlenen FlyWire nöron konumlarında `flyvis/activity`'den renklenir.
  - Sürülen sınır katmanı FlyWire spike'larıyla çizilir (mevcut).
- Bellek kuralları: kareler `writer.append_data` ile stream edilir, `plt.close(fig)`, `buffer_rgba`.

---

## Ek: yeniden üretim
- §0: final_a HDF5'inden `spikes/neuron_idx`, `spikes/count`, `spikes/step_idx` (adım ≥ 0); nöropil `data/neuron_neuropil.npz`; hop BFS parquet üzerinden (`Excitatory x Connectivity` > 0 = uyarıcı).
- §1: Codex `classification.csv.gz` + `consolidated_cell_types.csv.gz`, Completeness'taki root_id'lerle kesişim.
- §2.1: tip başına çıkış sinapslarının FlyVis dışı payı, parquet `Connectivity` ağırlıklı. FlyVis tip listesi `flow/0000/000` connectome düğümlerinden.
- §7.4: `spikes/*` + `behavior/phase`. DN kimlikleri `flywire_annotations.tsv` `cell_type`.

### 3.3e Çok seed'li tekrar (ön kayıt, 2026-10-02, koşulardan önce)
n1 (hibrit) ve n2 (yalnız beyin) yapılandırmaları aynen, seed 10/11/12/13/14, 300 adım. Ölçütler §3.3d ile aynı (S1, S2, B-K1/K3/K4). Hiçbir ayar değişmez; sonuç kaç seed'de geçtiği olarak raporlanır.
**§3.3e sonuçları (2026-10-04; ölçütler yukarıda, koşulardan önce yazıldı; ayrıntı REPORT_FINAL_V2 §6.7).** n1 S1 ∧ S2 5/5, n2 0/5; B-K1/K3/K4 10/10. Yön terimi 0 olduğu için rota seed'den bağımsız: konum, touchdown adımı ve kule değerleri beş seed'de seed 3 ile bit düzeyinde aynı, yani S1 sonucu 5 bağımsız doğrulama değil. Seed'e bağlı tek sonuç MN9: temas adımında 5/5 eşiğin üstünde, en düşük 15.7 Hz.

### 3.3f Kalkış konumu / yönü testi (ön kayıt, 2026-10-05, koşulardan önce)
**Amaç:** §3.3e'de rota seed'den bağımsız çıktı; S1 5/5 bağımsız doğrulama değildi. Bu test rotayı gerçekten değiştirir: kalkış kaidesi (ve sinek) ötelenir ya da başlangıç yönü döndürülür. Ölçülen şey el yapımı (HAND) rota/iniş zincirinin ve MN9 beslenme kararının farklı başlangıçlara dayanıklılığıdır; yön terimi 0 olduğu için **beynin rota kontrolü test edilmez.**

**Bayraklar** (yalnız deney tasarımı; HAND sabitleri, LIF, konnektom değişmez):
- `--start-offset DX DY` (mm): kalkış kaidesi ve sineğin başlangıcı birlikte ötelenir. Kaide aynı yükseklik ve yarıçapta (r 5 mm, üst z 19.5); koku alanındaki kaide engeli de birlikte taşınır (`cfg.move_takeoff_pedestal`, koku ızgarası ve kulelerle çakışma denetimi).
- `--start-yaw DEG`: kaide üzerindeki başlangıç yönü (+ = sola/CCW; 0 = +x).
- Varsayılan `0 0` / `0`: kod yolu ve çıktı adı değişmez; mevcut koşular aynen tekrar üretilir (smoke, 20 adım: n1 seed 3 HDF5'iyle pos, heading, turn_total, phase, mn9_rate, net_rate, vbnd_type_rate farkı 0). Öteleme + yön smoke'u (`--start-offset 40 -40 --start-yaw 60`, 20 adım): kaide ve başlangıç (40.2, −40.3) mm, meta doğru; davranış sonucu değil.
- Çıktı adında `_start<dx>_<dy>` / `_startYaw<deg>`; HDF5 `meta` öznitelikleri: `flags` (`start_offset`, `start_yaw`), `geometry` (`pedestal`), `experiment_design`.

**Koşullar (8, sıra sabit; `run_starts.sh`, detached, aynı anda tek koşu, `logs/starts/DONE_*`):**

| tag | bayrak | kaide merkezi (mm) | başlangıç yönü |
|---|---|---|---|
| st_xp40 | `--start-offset 40 0` | (40, 0) | 0° |
| st_xm40 | `--start-offset -40 0` | (−40, 0) | 0° |
| st_yp40 | `--start-offset 0 40` | (0, 40) | 0° |
| st_ym40 | `--start-offset 0 -40` | (0, −40) | 0° |
| st_yawp30 | `--start-yaw 30` | (0, 0) | +30° |
| st_yawm30 | `--start-yaw -30` | (0, 0) | −30° |
| st_yawp60 | `--start-yaw 60` | (0, 0) | +60° |
| st_yawm60 | `--start-yaw -60` | (0, 0) | −60° |

Ortak (n1 yapılandırması aynen, §3.3d): seed 3, 300 adım, `--no-video`, tam beyin (DEV değil), `--hybrid --vision-boundary --no-olfaction --dn-reference data/dn_lr_reference_sB.json --no-brain-steer --head-reflex --postures`.

**Ölçütler (tanımlar §3.3c/§3.3d ile aynen):**
- **S1:** touchdown'a kadar kule teması yok (adım sonu bayrağı ve adım-içi penetrasyon 0). Touchdown yoksa S1 ✗ (iniş yok), önceki raporlardaki gibi.
- **S2:** touchdown'dan sonra en az bir adımda `is_feeding` = 1.
- **Başarı = S1 ∧ S2**, koşul başına. **Sonuç "k / 8 koşulda geçti" olarak raporlanır.**
- Kayıt (geçti/kaldı yazılır, başarı sayımına girmez): B-K1/K3/K4 (§3.3b), B-H1/H2/H3 (§3.3d), BADQACC.
- Kayıt (ölçüt değil): touchdown adımı/zamanı, temas adımında MN9, beslenme adımı, besine en yakın uzaklık, toplam yön değişimi (kanatlar açık), en büyük penetrasyon ve temas konumu.

**Kurallar:** Başarısızlık olduğu gibi yazılır. Hiçbir HAND sabiti, kazanç, eşik ya da koşul listesi sonuçtan sonra değiştirilmez; koşul eklenmez/çıkarılmaz. Teknik çökme (exit ≠ 0, HDF5 yazılmadan) olursa aynı komut bir kez tekrar koşulur ve raporda belirtilir; davranış sonucu için tekrar yok. Tek seed (3): MN9'un seed'e bağlılığı §3.3e'de ayrıca ölçüldü.

**Önceden yazılan sınırlama:** Yön terimi 0 ve rota/irtifa/iniş HAND olduğundan, geçen bir koşul el yapımı denetleyicinin dayanıklılığını, kalan bir koşul da onun sınırını gösterir; ikisi de beynin rota kontrolü hakkında kanıt değildir. Beyinden gelen tek karar, touchdown sonrası MN9 beslenme kararıdır.
**§3.3f sonuçları (2026-10-05; ölçütler yukarıda, koşulardan önce yazıldı ve değiştirilmedi; ayrıntı REPORT_FINAL_V2 §6.8).** S1 ∧ S2 **8/8** (8 koşunun hepsi exit 0, teknik tekrar yok). B-K1/K3/K4 8/8, B-H1/H2/H3 8/8. Kayıt: rota farklı başlangıçlardan aynı koku hattına yakınsıyor; hepsi kule 2'nin üstünü gövde merkezi en yakın kule yüzeyine 2.8–5.5 mm olacak şekilde geçiyor. Önceden yazılan sınırlama geçerli: bu el yapımı rotanın dayanıklılığıdır, beynin rota kontrolü değil.

### 3.4a Smell circuit, part 1/4: does odour carry direction? (pre-registration, 2026-10-05, written BEFORE any simulation of this part)
**Scope.** Branch `sensory-inputs`. Open loop, no body, no closed-loop flight run in this part. Full brain; LIF parameters, connectome, NT signs, dt and the 25 ms decision step are unchanged; nothing is pruned. Established finding (REPORT.md §4): with realistic spontaneous ORN input the antennal lobe locks into a self-sustaining state. O1 tests whether the circuit decays when there is **no resting ORN input** and only the odour drive is present. O2 (criteria written here, **not run in this part**) asks whether the left/right asymmetry of the odour drive appears as a left/right difference in descending neurons (DNs).
The literature expectations given for this part come from a literature scan (some sources are preprints or were not read in full text). None is taken as true here; each is tested on our data and the outcome is reported as found.

#### Step 0: anatomy (no simulation; `scripts/diag/so_anatomy.py`, files: `Completeness_783.csv`, `Connectivity_783.parquet`, `flywire_annotations.tsv`, `descending_neurons.csv`)
Edges of the model graph are all stored edges of `Connectivity_783`; path search uses edges with ≥ 5 synapses. Side = annotation `side`.

**(a) Food glomeruli (DM1, DM2, DM4, VA2, VM2, DP1m).**
- ORNs (all typed `ORN_<glomerulus>`, side known for all): DM1 35 L / 33 R; DM2 29 / 25; DM4 20 / 20; VA2 34 / 33; VM2 19 / 18; DP1m 16 / 16. Total **153 L / 145 R = 298**, none with unknown side.
- ORN → PN synapses (PN = all `ALPN`), summed synapse counts, ipsilateral vs contralateral PN soma side:
  - food ORNs → all ALPN: ipsi 21,534 / contra 15,856 = **1.36 (ipsi +35.8 %)**, 149 target PNs. This matches the expectation (~ +35 %, Tobin, Wilson & Lee 2017).
  - food ORNs → uniglomerular ALPN only: 16,114 / 13,280 = 1.21 (+21.3 %), 45 targets.
  - all 53 glomeruli → all ALPN: 99,492 / 65,829 = 1.51 (+51.1 %); 840 synapses have an unassigned side.
  - By glomerulus (ORN → all ALPN, ipsi/contra): DM1 1.31, DM2 0.96, DM4 1.25, VA2 0.99, VM2 1.27, DP1m 1.73. The ipsilateral excess is therefore not uniform: DM2 and VA2 are about symmetric. The +35.8 % is dominated by DP1m (9,394 of 21,534 ipsi synapses) and DM1.
  - Restricted to PNs whose type name starts with the ORN's own glomerulus: DM1 1.18, DM2 0.89, DM4 1.20, VA2 0.95, VM2 1.11, DP1m 1.62.
- Consequence for O2: a left/right asymmetry that propagates is at most ~ +20–35 % at the first synapse, not a strong lateralisation; this is why O2 tests the sign of L−R, not a large effect.

**(b) Descending neurons (model DN list `descending_neurons.csv`, 1,299 neurons, all simulated).**

| query | FlyWire `cell_type` in model DN list | cells (L/R) | note |
|---|---|---|---|
| DNa02 | DNa02 | 1 / 1 | hemibrain_type DNa02 |
| DNa01 | DNa01 | 1 / 1 | **hemibrain_type VES006**, not the hemibrain DNa01 |
| DNa01 (hemibrain name) | DNae001 | 1 / 1 | hemibrain_type DNa01. The literature "DNa01" (steering DN) is most likely this type |
| DNae014 | none | 0 / 0 | **not present** in the annotations under cell_type, hemibrain_type or synonyms (the DNae series stops at DNae010). **UNVERIFIED**: no evidence that it exists in v783, or is the same as DNa15 |
| DNa15 | DNa15 | 1 / 1 | hemibrain_type PS017. Equivalence to "DNae014" **UNVERIFIED**, not assumed |
| DNb01 | DNb01 | 1 / 1 | (DNb09 has hemibrain_type DNb01 as well, 1 / 1) |
| DNg02 | DNg02_a … DNg02_h (8 sub-types) | 13 / 12 in total (a 3/3, b 4/3, c–h 1/1 each) | no cell is named plain `DNg02`; the type total is the sum over the 8 sub-types |
| DNp03 | DNp03 | 1 / 1 | |
| DNa04 | DNa04 | 1 / 1 | hemibrain_type PS015; DNae002 has hemibrain_type DNa04 (1 / 1) |
| DNa05 | DNa05 | 1 / 1 | hemibrain_type PS028; DNae004 has hemibrain_type DNa05 (1 / 1) |

**FlyWire / hemibrain naming conflict (decided before any run).** For DNa01, DNa04, DNa05 the FlyWire cell_type of the same name is a different cell from the hemibrain neuron of that name. For the literature-motivated hypotheses the hemibrain-named cell is used; the FlyWire-named cell is recorded as well and labelled as such:
- "DNa01" (secondary hypothesis) := **DNae001** (hemibrain_type DNa01). FlyWire `DNa01` (VES006) is reported separately and does not count for the hypothesis.
- DNa04 / DNa05: same rule (DNae002 / DNae004), recorded in the exploratory sweep only.
Primary hypothesis DNa02 has no such ambiguity. This mapping is from the annotation columns only; it is not confirmed from the literature (UNVERIFIED).

**(c) Shortest ORN → DNa02 paths** (sources: 298 food ORNs; edges ≥ 5 synapses; BFS over all neurons).
- **Minimum 3 hops** to both DNa02 cells (root_id index 904 R, 92992 L); 1,599 distinct shortest paths.
- Layers on shortest paths: hop 1 = 7 neurons (`M_l2PNl20` ×2, `CB0683` ×2, `lLN2F_b`, `M_lvPNm24`, `M_spPN5t10`); hop 2 = 31 neurons, mostly LAL types (`LAL030a–d`, `LAL035`, `LAL171/172`, `LAL011`), plus `CB0356`, `SIP022`, `AOTU015b`, `CB0359` and one `MBON31`; hop 3 = DNa02.
- Share of shortest paths through a type: `M_l2PNl20` 62 %, `CB0683` 22 %, `lLN2F_b` 15 %, `LAL171/172` 15 %, `LAL030b` 15 %.
- **Through Kenyon cells: 0 %. Through MBON32: 0 %** (MBON32 exists, 1 L + 1 R; one `MBON31` appears at hop 2 in 0.06 % of paths). The expectation "via Kenyon cells and MBON32" is **not found** for the shortest (3-hop) paths at the ≥ 5 synapse threshold. It was not tested whether longer paths through KC/MBON32 exist or carry more total drive.

#### O1: open loop, no resting input, 8 drive rates (pre-registered)
**Protocol.** Script `scripts/diag/so_o1.py` (to be written after this commit). Full brain (`FlightBrain`, `olfaction_full=True`, spiking APL, default NT signs, no `--nt-literature`, no DEV subnet), fresh state per run (`net.restore` + `brian2.seed`), 25 ms steps:
- steps 0–39 (1 s): the 298 food-glomerulus ORNs (both sides) are Poisson-driven at rate r; **every other input group (the other ORNs, vision, sugar, mechanical) is 0 Hz**;
- steps 40–79 (1 s): all inputs 0 Hz, recording only.
- Rates r (Hz, log-spaced 10·20^(k/7), rounded): **10.0, 15.3, 23.5, 36.1, 55.4, 85.0, 130.3, 200.0**.
- Seeds: **101, 102, 103, 104, 105** (never used before in this repository). 8 rates × 5 seeds = **40 runs**, one process at a time.

**Definitions.**
- Driven set = all neurons of `orn_all_L/R/C` (2,275 ORNs; they are Poisson inputs, 0 Hz outside the 298 driven ones).
- AL = neurons whose dominant neuropil (`data/neuron_neuropil.npz`) is AL, minus the driven set. Not-driven network = all neurons outside the driven set.
- Rates are mean spikes per neuron per second over the window, from per-step counts.
- Cut = end of step 39 (t = 1.000 s). Window W1 = 100–200 ms after the cut = steps 44–47. Window W2 = 400–500 ms after the cut = steps 56–59.

**Criterion (per rate, per seed).** PASS iff AL mean rate < 0.1 Hz **and** not-driven network mean rate < 0.1 Hz in W1. A rate passes iff it passes in **5/5 seeds**. Result is reported per rate (pass/fail), with the per-seed values.

**Recorded (not criteria).**
- PN response vs drive rate: mean rate of ALPN neurons (`cell_class == ALPN`; also uniglomerular only) in drive steps 10–39 (250–1000 ms), per seed and mean over seeds; "monotone" = the seed-mean is non-decreasing over the 8 rates (number of inversions reported).
- Lock-up onset = the lowest rate at which at least one seed fails.
- AL and not-driven rates in W2 (400–500 ms after the cut), per rate and seed.
- Time courses of AL, KC, LH, not-driven, ALPN rates (per step); DN rates.

**Stopping rule (mechanical).** If **no** rate passes in 5/5 seeds, odour stays **off** (as in the final runs), O2 is **not run**, and the result is reported as is. No parameter, gain, threshold, NT sign, rate or seed is adjusted after seeing O1. If several rates pass, O2 uses the highest passing rate (even if lower rates fail, which would be reported).

#### O2: left/right asymmetry (criteria only; NOT run in this part; to be run only at the highest rate that passes O1 in 5/5 seeds)
- **Conditions** (1 s each, steps 0–39, food-glomerulus ORNs only at rate r, everything else 0 Hz): L only (153 left ORNs), R only (145 right ORNs), bilateral symmetric (both sides at r), no input (all 0).
- **Seeds, fixed now:** 3 discovery seeds **201, 202, 203**; 5 validation seeds **301, 302, 303, 304, 305**. Discovery and validation sets are disjoint and none was used before. 4 conditions × 8 seeds = 32 runs.
- **Recorded in every run:** spike counts of **all** 1,299 DNs (per cell, window 250–1000 ms = steps 10–39; also whole-second counts).
- **Rates:** DN type rate per side = sum of the per-cell Hz of the type's cells on that side. DNa02 has one cell per side in the model, so the type total equals the single cell (stated, not hidden). L and R refer to the side of the DN soma (annotation `side`); ipsilateral = same side as the driven antenna.
- **Primary hypothesis (set before data, not from the scan):** DNa02, with one-sided drive the DN on the **same side** has the higher rate than the opposite one (Rayshubskiy et al. 2025, walking fly; there is no evidence for flight). **Secondary:** DNae001 (= hemibrain DNa01; FlyWire `DNa01` reported separately). Neither is corrected for multiplicity; only DNa02 is the confirmatory test.
- **Criteria, on the 5 validation seeds:**
  - (i) L-only drive: L > R, and R-only drive: R > L, in **5/5** seeds (strict inequality; a seed with both sides at 0 Hz is "silent" = fail);
  - (ii) symmetric drive: |L−R|/(L+R) < 0.2 in **5/5** seeds (both 0 Hz = "silent" = fail);
  - (iii) no-input condition: no difference, defined as |L−R| < 0.1 Hz in 5/5 seeds. Both at 0 Hz is a PASS here (no input, nothing to compare), unlike in (i) and (ii).
  - The hypothesis is "supported" for a DN type only if (i), (ii) and (iii) all hold; otherwise "not supported", reported with the per-seed numbers. Effect size is recorded: (L−R)/(L+R) for each condition and seed.
- **Limitation (written in advance).** In the model the resting rate of a DN is 0 Hz (no spontaneous input), so suppression on the contralateral side cannot be seen; only the excitation side is tested. A DN type that is silent in both sides cannot show a difference.
- **Exploratory sweep (secondary, labelled "exploratory").** On the 3 discovery seeds only: every DN type (cell_type, both sides summed per side) is ranked by (1) sign consistency of L−R across the 3 seeds in the L-only and R-only conditions (sign of (L−R) must be + for L-only and − for R-only in all 3), then (2) mean effect size |L−R|/(L+R). The ranking is descriptive. A type found this way is a **new hypothesis** and is not counted as confirmed; it would need new seeds. The text of this sweep definition in the task message was cut off after "etki büyüklüğüne göre"; the ranking above is the interpretation recorded here before any data exist.

#### Reporting rules for this part
- How much of any behaviour comes from the connectome and how much from a hand-made control term is reported without exaggeration; O1/O2 are open loop and say nothing about flight behaviour.
- Failures are written as they are. Nothing is deleted, nothing is pushed or merged.

**§3.4a O1 results (2026-10-05; criteria above were committed in 5b82f84 before any simulation and were not changed).** Script `scripts/diag/so_o1.py`, output `logs/smell/o1/` (not tracked), 40/40 runs, exit 0, seeds 101–105.
- **No rate passes: 0/5 seeds at every one of the 8 rates (10.0 … 200.0 Hz).** In W1 (100–200 ms after the cut) AL is 118.7–120.2 Hz and the not-driven network 3.38–3.45 Hz in every run; W2 (400–500 ms) is the same (AL 119.3–119.8 Hz, not-driven 3.40–3.42 Hz). Nothing decays.
- Lock-up onset: already at the lowest rate tested (10 Hz, 298 food ORNs, no other input); there is no rate below the lock-up.
- PN response to the drive is monotone in the seed mean (0 inversions) but almost flat: ALPN mean 84.7 → 88.0 Hz and uniglomerular PN 127.3 → 130.6 Hz over a 20-fold range of drive. The circuit goes to the same saturated state at any drive in this range; the driven state is all-or-none rather than graded.
- Decision by the pre-registered stopping rule: **odour stays off, O2 is not run.** No parameter, gain, NT sign, rate or seed was changed. Two things were not tested and are not claimed: rates below 10 Hz, and a drive shorter than 1 s.
- Anatomy (step 0) and O1 together: the model has a first-synapse ipsilateral excess (+35.8 % for food ORNs → ALPN), but the AL state is independent of drive strength, so no odour information in the rate code could be tested downstream. This is an open-loop result about the model, not about flight behaviour.

### 3.4b Smell circuit, part 2/4: do neurotransmitter-sign variants remove the lock-up? (pre-registration, 2026-10-06, written BEFORE any simulation of this part)
**Scope.** Branch `sensory-inputs`; no push, no merge, nothing deleted. Open loop only: **no closed-loop run in this part.** The published model (Shiu et al. LIF parameters, connectome, signs of `Connectivity_783`) is **unchanged**, and every result in this repository belongs to it. This part adds two clearly labelled **MODEL VARIANTS** behind separate flags, each labelled "MODEL VARIANT, not the published model" in code, logs and reports. Whole brain, no pruning, no region-specific setting (nothing is tuned for the antennal lobe, AL). LIF parameters, dt = 0.1 ms and the 25 ms decision step are unchanged.
Motivation (REPORT.md §3.7, exploratory post-hoc diagnostic): the persistent state of O1 is sustained by AL local neurons (LNs); the ten LN types that supply most excitatory events are 100 % excitatory in the model, and for several of them Codex has no transmitter prediction (NaN), which the model reads as excitatory. This part tests that candidate by intervention. It is a test of a hypothesis, not evidence for any parameter choice.

#### Step 0: audit (no simulation; `scripts/diag/nt_audit.py`, table builder `scripts/make_nt_impute.py`; tables are reproduced by the report script from the repository files)
- **Empty neurons** (no Codex v783 `nt_type`, score 0): **19,042 of 138,639 (13.7 %)**; only 301 neurons lack an annotation `top_nt` (293 of them also empty in Codex `nt_type`), so annotation `top_nt` and Codex `nt_type` are not the same table. The model's signs do not come directly from either (473 of the 119,597 predicted cells with output synapses have a model sign that differs from the sign of their predicted transmitter; e.g. the four GABA-predicted `lLN2P_b` cells, prediction score 0.35–0.39, are excitatory in the model).
- **Sign the published model gives them** (`Excitatory` of `Connectivity_783`): **12,686 excitatory, 5,722 inhibitory, 634 with no output synapses.** The premise "the model treats empty as excitatory" holds for the LN types of interest (e.g. `lLN1_bc`, `il3LN6`, `lLN2T_b`), not for the empty set as a whole.
- **Share of output synapses**: 3,074,064 of 54,492,922 (5.6 %); 1,149,962 of them (37.4 %) excitatory in the model.
- **Where they are**: sensory 7,533 (46.1 % of the class), optic 8,261 (10.7 %), central 1,605 (5.0 %), descending 321 (24.7 %), ascending + sensory ascending 543, motor 81 (73.6 %), endocrine 72 (94.7 %); by dominant neuropil ME 7,333, WED 4,468 (92.9 % of WED neurons), LA 2,111, GNG 995, LO 681, LOP 608, **AL 515 (17.3 %)**.
- **AL local neurons (ALLN)**: 429 cells, 95 types (one cell has no type), **150 cells empty**; 758,902 output synapses, **65.2 % excitatory in the model**. 48 of 95 LN types are inconsistent between their cells (annotation `top_nt` differs, or some cells are empty and others not, or the model sign differs). The full table per LN type (cells, model sign, `top_nt`, `top_nt_conf`, `known_nt`, output synapses) is produced by `nt_audit.py`.

#### Variants (rules fixed before any run; applied to the whole brain)
- **N1, "NT imputation"** (`--nt-impute`, `FlightBrain(nt_impute=True)`, table `data/nt_impute_783.csv`). **Only empty neurons change.** An empty neuron takes the sign of the **synapse-weighted majority of the non-empty cells of the same annotation `cell_type`**: each non-empty peer votes with the sign of its **predicted transmitter** under the model's own NT → sign mapping (ACh, DA, 5-HT, OA → +1; GABA, Glu → −1; the published model treats every transmitter other than GABA/Glu as excitatory), weighted by its number of output synapses; sum > 0 → +1, sum < 0 → −1, and the empty neuron's outgoing synapses get `w = |w| · sign` (same synapse list and counts, only the sign). A neuron with no `cell_type`, no non-empty peer with outputs, a zero sum, or no output synapses keeps its published sign. Peers vote with the prediction, not with the sign the published model happens to give them; the alternative (peers vote with their model sign) was not used, and was not run. No other neuron changes.
- **N2** (`--nt-impute --nt-literature`): N1 plus the existing `--nt-literature` rule (§3.2c, `data/nt_literature_783.csv`, `known_nt` of the annotations), unchanged. The literature rule is applied **after** N1, so where both apply (54 neurons) the literature sign wins.
- **What the variants change** (computed from the rule, before any run; `nt_audit.py`): 
  - **N1: 17,134 neurons have a rule, 3,599 change sign (1,964 excitatory → inhibitory, 1,635 inhibitory → excitatory); 126,921 of 15,091,983 edges, 408,867 of 54,492,922 synapses (0.8 %).**
  - **N2: 23,301 neurons have a rule, 3,613 change sign (1,976 / 1,637); 140,219 edges, 467,658 synapses (0.9 %).**
  - Most changed neurons are in the optic lobe (photoreceptors R7 730, R1-6 547, Dm3p, Dm3q, L4, …), because that is where Codex has most empty cells. Inside the AL, **N1 changes 26 LN cells in 17 types (7.4 % of the ALLN output synapses: `lLN2P_b` 8 cells, `lLN2F_a` 2, `lLN2X04` 2, …); N2 changes 34 cells in 19 types (12.4 %), adding `lLN2P_b` (all 12), `il3LN6`, `v2LN36`.** `lLN1_bc` (112,184 output synapses, 29 of 30 cells empty, one predicted peer with a serotonin prediction → +) is **not** changed by either variant, nor are the all-empty types without peers (`lLN2T_b`, `il3LN6` under N1). This expectation is written before the run; whether such a change can matter for the lock-up is what the test decides, and no further variant will be tried if it does not.
- No third variant, no gain, no threshold, no single-type correction and no AL-specific setting is tried in this part.

#### O1 under the variants (protocol of §3.4a, unchanged)
- Same 8 drive rates (10.0, 15.3, 23.5, 36.1, 55.4, 85.0, 130.3, 200.0 Hz), same seeds **101–105**, same 1 s drive of the 298 food-glomerulus ORNs and 1 s of no input, same definitions (driven set, AL, not-driven network), same criterion: **a rate passes iff, in each of the 5 seeds, the AL mean rate and the not-driven network mean rate are < 0.1 Hz 100–200 ms after the cut.**
- Run separately for N1 and N2: 8 × 5 × 2 = **80 runs**, one process at a time (`scripts/diag/so_o1.py --variant N1|N2`, output `logs/smell/o1_N1`, `logs/smell/o1_N2`). The script writes its start time (`START_O1`, log line `start …`).
- Recorded as in §3.4a (PN response, lock-up onset, W2, time courses, all DN counts). Reported next to the published model's result (0/8, §3.4a), each labelled.

#### Decision rule (mechanical)
1. If **N1** passes in 5/5 seeds at ≥ 1 rate: O2 is run with **N1** at the **highest passing rate**.
2. Else, if **N2** passes in 5/5 seeds at ≥ 1 rate: O2 is run with **N2** at its highest passing rate.
3. Else: **O2 is not run**, odour stays off, and this is written as the result.
4. If both pass, N1 is used (it changes fewer neurons). No third variant, gain, or single-type correction is tried.

#### O2 under the selected variant
- Criteria, conditions, seeds (discovery 201, 202, 203; validation 301–305), DN recording (all 1,299 DNs), DNa02 primary and DNae001 secondary hypothesis, the validation criteria (i)–(iii), the limitation and the exploratory sweep: **exactly as written in §3.4a**, with the selected variant in place of the published model. Only DNa02 is confirmatory.
- **"A reading passes"** := a confirmatory DN type (DNa02 or DNae001) that is "supported" under (i), (ii) and (iii) on the 5 validation seeds. Exploratory types are new hypotheses and do not trigger the null control.
- **Null control (defined now; run only if a reading passes).** 5 degree-preserving shuffled connectomes of the selected variant: the `Postsynaptic_Index` column of the edge list is randomly permuted over all edges (permutation seeds **401–405**), so every edge keeps its presynaptic neuron, weight and sign (and therefore each neuron's out-degree and out-synapse count, and the in-degree distribution), and only *which* neuron is contacted is destroyed. Inputs, DN list and driven groups stay the same neurons. On each shuffled network the 4 O2 conditions are run once at the O2 rate (simulation seed = the permutation seed): 5 × 4 = 20 runs. A shuffle **reproduces** the reading if criteria (i)–(iii) hold for the same DN type in that single run (same strict rules, "silent" = fail in (i), (ii)). Reported: the number of shuffles (0–5) that reproduce it. ≥ 1 of 5 → "not distinguishable from random wiring with the same degrees in this test"; 0 of 5 → "not reproduced by 5 shuffles", which does not by itself show that the reading is connectome-specific.

#### Robustness records (recorded, **not criteria**)
Made on the selected variant (if no variant is selected, on both N1 and N2; the published model is run as a reference in the same way). Seeds 501–503, never used before.
- (i) **No input**: fresh state, **all inputs 0 Hz** for 1 s (40 steps), `olfaction_full` brain as in O1; recorded: whole-network mean rate in the last 200 ms and over the whole second; "silent" iff < 0.1 Hz in the last 200 ms. Note: from the fresh state with zero input this is expected to be trivially silent (nothing drives any neuron); it is recorded because it was asked for, and it says nothing about stability under input.
- (ii) **Sugar GRN → MN9, open loop** (existing test, `scripts/diag/a1_mn9.py` condition `sugar_only`): final configuration brain (`olfaction=False`), labellar sugar GRNs 100 Hz, all other inputs 0 Hz, 1 s from the fresh state, MN9 mean rate (L, R) in 250–1000 ms against `MN9_THRESHOLD_HZ` = 10 Hz.
- **Not claimed.** Closed-loop results are **not** claimed under a variant. Every closed-loop result (flight, walking) belongs to the published model; under a variant they need re-validation (DNp15 calibration, S1/S2, body criteria), which is not done in this part. N1 and N2 change thousands of neurons of the visual system, so the closed-loop behaviour may differ.

#### Limitation (written in advance)
N1 and N2 fill missing data with a rule; their biological accuracy needs independent evidence (transmitter identity of the cells in question). A pass would support the hypothesis that the lock-up is caused by missing or wrong signs; it would not prove it (the interventions also change other parts of the network, and the rule is a guess). A fail would say that these two rules do not remove the lock-up; it would not exclude other sign assignments, other causes, or drive rates below 10 Hz.

#### Reporting rules for this part
- The published-model result (0/8) and each variant's result are shown side by side with explicit labels; "MODEL VARIANT, not the published model" appears wherever a variant number appears.
- How much behaviour comes from the connectome versus hand-made control is not part of this open-loop test and is not claimed.
- Failures are written as they are. Nothing is deleted, pushed or merged.

**§3.4b results (2026-10-06; rules and criteria above were committed in `ef6c3ff` before any simulation and were not changed).** Scripts `scripts/diag/run_o1_nt.sh`, `so_o1.py --variant`, `so_nt_robust.py`; tables `scripts/diag/nt_report.py`; details REPORT.md §3.7.
- **Audit:** 19,042 neurons (13.7 %) have no Codex `nt_type`; the published model gives 12,686 of them an excitatory and 5,722 an inhibitory sign (634 have no outputs); they carry 5.6 % of all output synapses. 65.2 % of the AL-LN output synapses are excitatory in the model. N1 changes 3,599 neurons (26 AL LN cells), N2 3,613 (34 AL LN cells).
- **O1 under the variants: N1 0 of 8 rates, N2 0 of 8 rates pass in 5/5 seeds (80 runs).** After the cut the AL is at about 103 Hz (N1) and 86 Hz (N2) against about 120 Hz in the published model; the state is independent of the drive and is still present 400–500 ms after the cut.
- **Decision rule (item 3): O2 and the null control were not run; odour stays off.** No third variant, gain or single-type correction was tried.
- **Robustness records (not criteria):** (i) no input: silent in all models (trivial from rest); (ii) sugar 100 Hz → MN9: 53–62 Hz in N1 and N2, 56–61 Hz in the published model, all above the 10 Hz threshold. Closed-loop behaviour under a variant was not tested.

### 3.4c Smell circuit, comparison check: does the upstream NeuroFly-style olfactory drive pass our decay criterion? (pre-registration, 2026-10-06, written BEFORE any simulation of this check)
**Scope.** Branch `sensory-inputs`; no push, no merge, nothing deleted. Open loop, **published model only** (no variant, no parameter change), no closed-loop run. This is a comparison control: it measures the difference between two drives; it is not a critique of the upstream script. Its result does **not** change the odour decision of §3.4a/§3.4b (odour stays off); it is for comparison only (written in advance). `fly_brain_body_simulation.py` (upstream walking script, kept in this repository) is read, not modified or run.

#### Step 0: what the upstream walking script does (read from `fly_brain_body_simulation.py`, no simulation; line numbers refer to that file)
Counts below were computed from `brain_model/flywire_annotations.tsv` and `Completeness_783.csv` with the script's own regex (`scripts/diag/nf_report.py` reproduces them).

| question | upstream walking script | our O1 (§3.4a) |
|---|---|---|
| (a) neurons selected as "olfactory" | `_find_ids(r"olfactory\|olfactori\|\born\b\|projection.neuron")` over `cell_class`, `cell_type`, `super_class` (L292–303). All matches come from `cell_class == "olfactory"` (2,282 annotation rows, 2,279 in the model); `cell_type` and `super_class` give 0 matches. **2,275 are ORNs of the 53 `ORN_<glomerulus>` types**, **4 are `olfactory`-class cells without a cell type**. **The regex selects no projection neurons** (ALPN have `cell_class` "ALPN"; the comment at L302 mentions PNs, the selection does not contain them). Side (annotation): 1,116 L / 1,133 R / 30 unknown. Food-glomerulus ORNs (the 298 of §3.4a) are inside the set, together with 47 other glomeruli. | 298 food-glomerulus ORNs (153 L / 145 R) |
| (a') further neurons on the same drive | SEZ/gustatory set (L307; `cell_class` gustatory, 408 neurons) is added to the same list: `circuit_stim_idx` = 2,279 + 408 = **2,687** (L387; the two sets do not overlap) | none |
| (b) drive form | `poi(neu, [], circuit_stim_idx, params)` (L412) → one `PoissonInput` per neuron, N = 1, rate `r_poi2` = `CIRCUIT_STIM_RATE` = **80 Hz** (L383, L394; `brain_model/model.py` L95–102), weight `w_syn·f_poi` = 0.275 mV × 250 = **68.75 mV** per event, refractory period of the target set to 0 (model.py L103). Same rate for left and right. The same mechanism and weight as our Poisson groups (`flight/brain.py` L301–319). | Poisson at rate r, weight 68.75 mV, refractory 0 (same mechanism) |
| (b') rates reached | **One value: 80 Hz, constant** for every driven neuron, every step. There is no low, typical or high rate: the olfactory neurons are not given an odour-dependent rate anywhere in the script (the `PoissonInput` objects are never touched after construction; the step loop at L660+ only updates the rates of the ascending and visual `PoissonGroup`s, L678 and L690–692). | 10 … 200 Hz (8 rates) |
| (b'') what the odour value does | The odour field (Dijkstra path distance, `peak / max(d,1)²`, peak 500, L207–245) is sampled at two antenna positions (L744–751). Computed from the function: spawn (0,0) 0.570, food position 500.0 (maximum), smallest non-zero value 0.385. These values go only into the turn command (L829) and the video/plot recording (L852, L1192); **none of them reaches a neuron rate**. | the odour level is the Poisson rate itself |
| (c) cut / baseline | **The drive is never cut and there is no odour-free condition**: 80 Hz is on for the whole 10 s run (L115, L383) whether or not odour is present at the antennae. So the script's brain run does not contain a decay test: the olfactory drive that "turns off" does not exist in it. | 1 s drive, then all inputs 0 Hz for 1 s |
| (d) route to the turn command | `ctrl = [clip(0.75 + turn_bias, 0.1, 1), clip(0.75 − turn_bias, 0.1, 1)]` (L833–836), `turn_bias = odor_turn + dn_bias + _loom_persist` (L832). **`odor_turn = tanh(20·asym)·2.5`** (L829, `ODOR_TURN_K` L125) is computed **directly from the hand-made odour field**, `asym = (R−L)/(R+L)`, with no brain in the path. `dn_bias = 0.15·lr_diff_t` (L831), `lr_diff_t` = (L−R)/(L+R) of the **spike counts of all 1,299 DNs** (645 L / 646 R / 8 centre; side from `descending_neurons.csv`) in the 25 ms step (L721–726); `_loom_persist` is a T5-asymmetry bias from a separate network (flyvis) clamped to ±0.15 (L166). The brain's DN output enters, but (1) with a coefficient 0.15 against 2.5 for the odour-field term, (2) the brain input it depends on does not carry the odour (constant 80 Hz, same on both sides), (3) the sum is clipped to [0.1, 1] so any |odor_turn| ≳ 0.5 saturates the command. | not applicable (open loop) |
| (e) other drives on at the same time | ascending neurons 150 Hz × (0.15 … 1) proprioceptive factor (L121, L382, L677), LA>ME lamina 20–150 Hz by luminance (L158–159, L687–692) | none (O1: every other input 0 Hz) |

**Reading, as written before any run.** In the walking script the left/right odour difference reaches the legs through the hand-made field term; the brain's DN left/right difference contributes at most ±0.15 to `turn_bias`. Whether the olfactory neuron drive could carry odour information is not answered by the script, because its rate does not depend on the odour. This is stated as read from the code; no claim is made about how the upstream authors intended it.

#### Pre-registration: NeuroFly drive in our open-loop set-up (published model, `so_o1.py` infrastructure)
- **Neuron set and drive: exactly as upstream.** The 2,279 neurons selected by the upstream regex (2,275 ORNs of all 53 glomeruli, both sides and side-unknown, plus the 4 untyped `olfactory`-class cells; the 4 are added as one extra `PoissonGroup` + synapse group of the same weight and refractory setting, built before `net.store`, no other change to the network) at **80 Hz each**, left = right, 68.75 mV per event, refractory 0. **Only these are driven** (the SEZ/gustatory, ascending and visual drives of the upstream script are 0 Hz here, as in O1: the check isolates the olfactory drive; the SEZ set is not part of the question).
- **Levels.** The task asked for three levels (low, typical, highest rate seen upstream). The script contains **one** rate (80 Hz, constant; see (b')), so the three levels coincide. Pre-registered: **one level, 80 Hz, 5 seeds = 5 runs** (not 15). No level is invented; drive levels outside the upstream value are exactly the O1 range already measured (§3.4a, 298 ORNs, 10–200 Hz).
- **Protocol (as O1):** fresh state per run (`net.restore` + `brian2.seed`), 25 ms steps, steps 0–39 (1 s) driven, steps 40–79 (1 s) all inputs 0 Hz. Seeds **701, 702, 703, 704, 705** (not used before in this repository).
- **Definitions.** Driven set = the 2,279 neurons above. AL = neurons whose dominant neuropil is AL, minus the driven set. Not-driven network = all neurons outside the driven set. Windows W1 = 100–200 ms after the cut (steps 44–47), W2 = 400–500 ms (steps 56–59).
- **Criterion (as O1):** PASS iff AL mean rate < 0.1 Hz **and** not-driven network mean rate < 0.1 Hz in W1; the level passes iff 5/5 seeds pass. Reported pass or fail, with the per-seed values. **No setting is adjusted.**
- **Recorded (not criteria):** ALPN and uniglomerular-PN mean rate and AL mean rate during the drive (steps 10–39) next to the O1 values at 85.0 Hz (§3.4a; different neuron set, so not the same condition); because there is one level, whether the rates change across levels cannot be answered by this run and is stated as such; AL and not-driven rates in W2; the fraction of driven neurons that spike at least once in W1, and in the 400–500 ms window; the driven-set mean rate in W1.
- **Not tested, not claimed:** other levels, a shorter drive, the SEZ/ascending/visual drives together, anything about the upstream closed-loop behaviour. The result is open loop and about this drive in our model.
- **Pre-written interpretation rule.** If the level fails, the sentence is "under our criterion this drive does not decay; the upstream demonstration does not test decay". If it passes, it is reported as a pass and the O1 failure is not reinterpreted from it. Either way the odour decision (off) is unchanged.

**§3.4c results (2026-10-06; rules and criteria above were committed in `cde230e` (wording fix `4f70813`) before any run and were not changed).** Scripts `scripts/diag/so_o1_nf.py`, `scripts/diag/run_o1_nf.sh`; output `logs/smell/o1_nf/` (not tracked), 5/5 runs, exit 0, seeds 701–705, started 2026-10-06 09:54:17; tables `scripts/diag/nf_report.py`; details REPORT.md §3.7.
- **0 of 5 seeds pass.** 100–200 ms after the cut the AL is at 119.3–120.3 Hz and the not-driven network at 3.40–3.44 Hz (criterion < 0.1 Hz); the state is the same 400–500 ms after the cut and the same as in O1. About 15 % of the driven neurons still spike after the cut.
- One level only (the upstream script has one olfactory rate), so the drive-level dependence of the AL/PN rates could not be tested here; the PN means during the drive are recorded in REPORT.md.
- The odour decision is unchanged (odour stays off). Under our criterion this drive does not decay; the upstream demonstration does not test decay.

### 3.5 Vision screen, part 3/3 (open loop): which descending-neuron clusters separate which visual stimulus? (pre-registration, 2026-10-06, written BEFORE any simulation, rendering or smoke run of this part)
**Scope.** Branch `sensory-inputs`; no push, no merge, nothing deleted, no history rewrite. **Published model only**: LIF parameters, connectome, signs unchanged; no variant (`nt_impute`, `nt_literature` off); no neuron or synapse pruning; full brain. Open loop only: the flight controller is **not** changed and no closed-loop run is made; the n1/n2 flights stay as they are whatever this screen finds. Body fixed, no physics. Visual input goes through the existing path (FlyGym eye geometry → `Retina` → FlyVis `flow/0000/000` → 32-type FlyWire boundary layer, 34,121 neurons, `flight/vision_boundary.py`); every other input is 0 Hz. Literature expectations in this section are marked *expectation from literature, source not re-verified in this turn*; they are secondary notes and are **not** part of any pass criterion. No new source is cited in this turn.

#### Step 0 (read only, no simulation)
**(a) Existing open-loop visual path.**
- Stimulus rendering → boundary-layer rates: `scripts/diag/a0_visual.py --vision-boundary` (arena scenes, kinematic body) and `scripts/diag/a2_visual.py --vision-boundary --no-platform` (synthetic gratings), both through `BoundaryEyes` (`flight/vision_boundary.py`), output `*_visual_rates_vb.npz` with keys `<cond>__vbnd_L/_R` (per-neuron Poisson rates, Hz, 40 steps). Rates → brain: `scripts/diag/a2_openloop.py --vision-boundary` (`FlightBrain(vision_boundary=True, olfaction=False)`, `b.silence_inputs()` then `b.set_rates(vbnd_L=…, vbnd_R=…, sugar=0.0)`, one 25 ms step per rate row).
- Frame rate: decision step 25 ms, `VIS_SUBFRAMES = 2` FlyGym renders per step → FlyVis dt 12.5 ms. Eyes: 721 ommatidia per eye; raw camera image 512 × 450 px, pinhole, `fovy` = 157° (vertical; horizontal ≈ 154°). Read from the MuJoCo model (pose query only, no stepping): left-eye optical axis at azimuth +62.5°, right eye −63.6° (+ = left, elevation ≈ −0.5°); the left raw image spans azimuth +140° (left image edge, posterior) to −13.8° (right image edge, anterior), the right-eye image −140° … +13.9°; the two eyes overlap only at −14° … +14°. A frontal stimulus (0°) therefore falls on the anterior edge of both eyes.
- What exists: the yaw gratings of `a2_visual.py` (period 64 px ≈ 20° near the image centre, 2 Hz, contrast 0.8, same raw image in both eyes), arena looms (`loom_L/R`: tower face approached at 55 mm/s, not a disc with a given l/v), forward flight at 100 mm/s (`progressive`, textured arena). **What does not exist:** gratings with an angular wavelength of 30°, discs with l/v = 40 ms, a receding disc, a frontal loom, a stimulus defined in body-frame angles. The existing path is used from the raw-image stage on (raw 512 × 450 uint8 RGB image → `Retina.raw_image_to_hex_pxls` → `BoundaryEyes.step/rates`, exactly as `grating_frames`); only the generator of the raw image is new (see "Stimuli: deviations").
- Brain runner with all DN spike counts: `a2_openloop.py` records only the 15 readout types, so a new runner `scripts/diag/vd_run.py` (same `FlightBrain` calls, the pattern of `so_o1.py`) records the per-step spike counts of **all 1,299 DNs**. Null connectome: `FlightBrain(shuffle_seed=…)` / `flight.brain.shuffled_connectome` (postsynaptic column permuted over all edges; presynaptic neuron, weight, sign, out-degree preserved), as in `so_o2.py`; the driven boundary-layer neurons and their Poisson synapses are not affected by the permutation.

**(b) DN clusters in v783** (`brain_model/descending_neurons.csv`, 1,299 DNs, 472 types; identical to the annotation counts; all in `Completeness_783.csv`; side as annotated; type = exact `cell_type` string):

| cluster | left | right | note |
|---|---|---|---|
| DNg02 (8 subtypes a–h pooled as one population) | 13 | 12 | 25 neurons |
| DNa04 | 1 | 1 | |
| DNa05 | 1 | 1 | |
| DNp15 | 1 | 1 | |
| DNb01 | 1 | 1 | |
| DNp03 | 1 | 1 | |
| DNp01 | 1 | 1 | |
| DNp02 | 1 | 1 | |
| DNp04 | 1 | 1 | |
| DNp06 | 1 | 1 | |
| DNp11 | 1 | 1 | |
| DNp07 | 1 | 1 | |
| DNp10 (exact type; DNp101…DNp104 are other types, not included) | 1 | 1 | |

No cluster is absent. (8 DNs of the model have side "center"; they have no L/R and appear only in rate-based measures of the exploratory screen.) All side-pairs of the a-priori clusters are single neurons except DNg02, so for those clusters "firing rate" is a single-neuron rate per side; this makes per-seed values noisy and is a limit of the screen.

**(c) Time estimate for one run** (no new run; from `logs/smell/o1/*.npz` file times, `logs/smell/o1.log`, `logs/smell/o1_nf.log`): O1 = 80 steps in 20–21 s (≈ 0.26 s per 25 ms step, full brain, 298–2,279 Poisson-driven neurons), brain build 3 s. One run here = 60 steps ≈ 16 s; with 34,121 driven neurons per step (rate vectors) allow ≤ 25 s. One brain per seed (build + `store`) and one `restore` per condition. Stimulus rendering (once for all seeds, the stimuli are deterministic): 10 conditions × (1 s grey settling + 0.5 s grey + 1.0 s stimulus = 200 FlyVis frames of batch 2); not measured before, allowed ≤ 3 min per condition. Shuffled connectome build (read parquet, permute, write, build): not measured before, allowed ≤ 3 min per seed.
Total estimate: render ≤ 30 min; main 80 runs × ≤ 25 s ≈ 33 min + 8 builds; null 45 runs × ≤ 25 s ≈ 19 min + 5 shuffled builds ≤ 15 min. **Total ≈ 1.5 h (upper bound ≈ 2 h), below the 6 h limit, so all 9 null conditions are run and no condition is dropped.**

#### Stimuli (all parameters are single values; fixed here)
Each run = 0.5 s uniform grey (20 steps) + 1.0 s stimulus (40 steps), body fixed. Before each condition FlyVis is reset (1 s grey, as in `FlyVisEyes.reset`). Grey = luminance 0.5, contrast 0.8 (`GRATING_CONTRAST`), encoded as in `grating_frames` (uint8 raw image). Stimuli are defined in **body-frame angles**: for every raw pixel the camera ray (pinhole, 157° vertical, 512 × 450) is rotated into the body frame with the MuJoCo camera and root-body orientation of `FlightBody` (pose query only); azimuth az (+ = left), elevation el. Time t = time since stimulus onset at the end of each of the 2 sub-frames of a step.

| # | condition | definition |
|---|---|---|
| 1 | yaw-CW grating | L = 0.5 + 0.4 sin(2π(az/30° + 2 Hz·t)): vertical stripes (function of azimuth only), wavelength 30°, 2 Hz (60°/s), pattern rotating clockwise seen from above (az decreasing; the pattern moves to the right) — the optic flow of a fly turning left; full field |
| 2 | yaw-CCW grating | the same with sin(2π(az/30° − 2 Hz·t)): pattern moves to the left (az increasing) — the flow of a fly turning right |
| 3 | static grating (control) | the same grating, t = 0 for all frames |
| 4 | loom-left | dark disc (luminance 0.1) on grey, centre az = +60°, el = 0°, full angular size Θ(t) = 2·atan(τ/(t_c − t)) with τ = l/v = 40 ms, Θ(0) = 5° and Θ = 90° at t = 0.876 s (t_c = 0.916 s); then Θ stays 90° until the end of the 1.0 s (disc not removed) |
| 5 | loom-right | as 4, centre az = −60° |
| 6 | loom-front | as 4, centre az = 0° |
| 7 | receding-left | the time reversal of condition 4 over the whole 1.0 s (Θ = 90° for the first 0.124 s, then 90° → 5°) |
| 8 | receding-right | the time reversal of condition 5 |
| 9 | expanding flow (both sides) | forward translation at v = 50 mm/s inside an infinitely long cylinder of radius 50 mm centred on the body axis, wall texture of stripes perpendicular to the axis: L = 0.5 + 0.4 sin(2π(x_hit + v·t)/25 mm), x_hit = axial coordinate of the ray–wall intersection relative to the fly (rays with radial component < 10⁻³ are clamped); gives front-to-back flow in both eyes, angular speed ≈ 57°/s and angular wavelength ≈ 29° at az = ±90° |
| 10 | grey (baseline) | luminance 0.5 for the whole 1.5 s |

**Stimuli: deviations from the requested defaults, with reasons (all before any run).**
- Grating wavelength 30° as requested; 2 Hz as requested; full field as requested. The existing generator cannot make a body-frame angular wavelength (its period is in raw-image pixels, ≈ 20° only near the image centre), so the new generator defines it in azimuth. The grating is a function of azimuth only (vertical bars; no elevation dependence).
- Loom: l/v = 40 ms, 5° → 90°, ±60° side, 0° front, as requested. Added choices the request left open: the disc is dark on grey (luminance 0.1), Θ is full angular size, the disc is held at 90° for the last 124 ms rather than removed (so that the measurement window ends with the disc at its largest size). Consequence stated in advance: with l/v = 40 ms most of the expansion happens in the last ~150 ms (Θ ≈ 14° at 0.6 s, 38° at 0.8 s), so a 200–1000 ms window average dilutes the loom response; the window is as requested and is not changed.
- Receding: exact time reversal of the loom, as requested ("loom reversed in time").
- Expanding flow: the request names no parameters. v = 50 mm/s, cylinder radius 50 mm, stripe period 25 mm were chosen so that the lateral angular speed and angular wavelength match the grating of condition 1/2 (≈ 57°/s, ≈ 29°); this is a choice for comparability, not tuned on any response.
- Frontal stimuli (3 and 9 aside, condition 6) fall on the anterior edge of both eyes (overlap −14° … +14°); this is a property of the model's eyes, noted as a limit of the loom-front and flow tests.
- **Stimulus geometry unit test** (`tests/flight/test_vis_stim.py`, **no neural data**): before rendering, (i) the left-eye optical axis has azimuth in (+30°, +90°) and the right eye in (−90°, −30°); (ii) the grating luminance returned for a ray equals the formula at the ray's azimuth; (iii) Θ(t) of the loom equals 5° at t = 0, 90° at t = 0.876 s, is monotone, and the receding disc is its exact time reversal; (iv) disc centres are at az = +60°, −60°, 0°. If this test fails the generator is fixed before rendering; after rendering nothing is changed.

#### Seeds, windows, definitions
- Seeds: discovery 501, 502, 503; validation 601–605; null (shuffled connectome, permutation seed = simulation seed) 801–805. Per (seed, condition): fresh state (`net.restore`) and `brian2.seed(seed)`, so within one seed the conditions share the random stream (common random numbers); seeds are the unit of replication. Resumable per (seed, condition) file; `DONE` marker; one run at a time.
- Window: 200–1000 ms after stimulus onset = steps 28–59 (onset = step 20, 800 ms, 32 steps). Recorded: all 60 steps of all 1,299 DNs.
- Cluster rate r(c, cond): spikes in the window of all neurons of cluster c (both sides) / (n neurons × 0.8 s), Hz per neuron; side rates r_L, r_R likewise (so unequal L/R counts, DNg02 13/12, do not bias the measure).
- Asymmetry A = (r_L − r_R)/(r_L + r_R + 1 Hz).
- Silent: a cluster is **SILENT (not testable; not a failure)** if its mean r over the 3 discovery seeds is < 1 Hz in every one of the 10 conditions. It is then not tested further.

#### Input check (before any DN result is interpreted)
Rendered rates (deterministic; computed from the rendered `vbnd` rate arrays, window as above): input asymmetry A_in(cond) = (mean rate of the left-eye boundary neurons − right-eye)/(sum + 1 Hz).
- Yaw: computed on the T4a + T5a neurons of the boundary layer (front-to-back-preferring subtypes, `visual_input` module doc), because the all-subtype mean is expected to cancel for opposite directions. Requirement: A_in(1) and A_in(2) have **opposite signs**, each |A_in| ≥ 0.05.
- Loom: computed on all boundary-layer neurons. Requirement: A_in(4) and A_in(5) have **opposite signs**, each |A_in| ≥ 0.05.
- Recorded, not criteria: the expected signs (condition 2 > 0 and 1 < 0; condition 4 > 0 and 5 < 0), A_in of all other conditions, mean boundary-layer rate per condition.
- **If either requirement fails: "input check failed" is written, no brain run is launched, DN results are not interpreted** (the stimulus parameters are not changed afterwards).

#### A-priori hypotheses (direction is fixed on the discovery seeds, tested on validation)
Effects (all per seed; "mean" = mean over the seeds of the set):
- **H1** (yaw), cluster DNg02: D = A(1) − A(2).
- **H2** (yaw), each of DNa04, DNa05, DNp15, DNb01 separately: the same D.
- **H3** (loom), each of DNp03, DNp01, DNp02, DNp04, DNp06, DNp11 separately: (i) response R = ½[r(4) + r(5)] − ½[r(7) + r(8)] (Hz); (ii) side selectivity S = A(4) − A(5).
- **H4** (landing), each of DNp07, DNp10: Δ_front = r(6) − r(3) and Δ_flow = r(9) − r(3) (Hz).

Direction: sign of the 3-seed discovery mean of the effect (exactly 0 → no direction → FAIL). Committed separately (`direction-fixing` commit) **before any validation run**.

**Pass criteria (all together, per cluster and measure):**
1. not SILENT (rule above);
2. the sign of the effect equals the fixed direction in **5/5** validation seeds;
3. magnitude: |validation mean| ≥ 0.10 for D and S (asymmetry differences), ≥ 1 Hz for R, Δ_front, Δ_flow;
4. control: for D and S, |mean A(3)| (static grating, validation seeds) < |validation mean effect|; for the rate measures, |mean r(3) − mean r(10)| (static grating vs grey, validation seeds) < |validation mean effect|;
5. null: the same measure on the shuffled connectome (seeds 801–805, same conditions, grey excluded) — |real validation mean effect| > |effect| of **each** of the 5 null seeds.
Result categories: **PASS**, **FAIL**, **SILENT**. A cluster whose measure needs the grey condition for the control (rate measures) uses the real-connectome grey runs only; the null needs no grey run.

**Number of a-priori tests: 21** (H1 1 + H2 4 + H3 6 × 2 = 12 + H4 2 × 2 = 4). None is removed afterwards, no correction is applied; for orientation only, if an effect were pure noise the 5/5 sign requirement alone is passed with probability 2⁻⁵ ≈ 3 % per test (about 0.7 expected false sign-passes in 21 tests before criteria 3–5).

*Expectations from literature, source not re-verified in this turn (secondary notes, not criteria):* DNg02 populations are associated with the contralateral/ipsilateral bias of yaw optic flow; DNp01 (giant fibre) and DNp02/DNp03/DNp04/DNp06/DNp11 with looming escape; DNp07/DNp10 with landing; DNa04/DNa05/DNp15/DNb01 with steering/yaw. The sign of any left/right effect is **not** taken from the literature but fixed on the discovery seeds.

#### Exploratory screen (label: EXPLORATORY)
All DN types of the model (472; types with both sides for the asymmetry measures D and S, all types for R, Δ_front, Δ_flow), the same five measures, computed on the discovery seeds only; types SILENT by the rule above are dropped; the a-priori (cluster, measure) pairs above are excluded from the list (they are tested above); each remaining (type, measure) pair gets score = |discovery mean effect| / threshold (0.10 or 1 Hz); the **10 highest-scoring pairs** (ties: alphabetical by type) are the candidates; their direction is the sign of the discovery mean; they are then tested on validation and null **with exactly the same criteria 2–5**. Reported always together as: number of (type, measure) pairs screened, number of candidates (10), number that pass. The sweep is not repeated or widened after the result. DNg02 subtypes are separate types here (472 types), the pooled DNg02 population stays an a-priori cluster.

#### Reporting rules for this part
- Results are reported as they are; a negative result is written as negative. Anything computed after seeing the results (other windows, other contrasts, per-subtype looks, per-neuron looks, time courses) is labelled **post-hoc / exploratory** and is not a pass.
- Criteria, window, thresholds, stimulus parameters and cluster definitions are not changed after any result is seen; deviations (if any) are listed as deviations in the report.
- A cluster that passes is labelled "BRAIN readout candidate (open loop, not yet used for control)"; if none passes, that is stated.
- Limits written in advance: open loop only; no VNC; FlyVis is a trained model, not the fly's circuit; the boundary-layer rates are a Poisson stand-in for graded signals; the path from DN to wing is not modelled; most clusters are single neurons per side; the eyes cover the front only at their edges; the real effect is compared to 5 null seeds only (a minimal null, not a p-value).
- The hand-made part (stimulus generator, rate transduction constants `R_MAX`, `R_CLIP`, boundary-layer selection) and the part from the connectome are named separately in the report; the screen does not say how much of any behaviour comes from either.
- Order: (1) this section committed; (2) scripts + log row #13 committed; (3) geometry unit test, render, input check; (4) discovery runs (seeds 501–503); (5) direction-fixing commit; (6) validation runs (601–605); (7) null runs (801–805); (8) report script, REPORT §3.8, README, provenance, verify. If a session is cut, runs resume from the `DONE` markers/files and finished runs are not repeated.

### 3.5b Vision screen, follow-up: loom response in a window locked to the collision phase (pre-registration, 2026-10-06, written BEFORE any simulation, rendering, input check or smoke run of this follow-up)
**Status label (used everywhere this test is mentioned): "follow-up designed after the §3.8 results were known; new window, new seeds".** This test was designed *after* the first results of §3.5 / REPORT §3.8 were seen, including the post-hoc looks listed in Step 0(a). It is therefore not an independent pre-registration of a hypothesis; what is pre-registered is the window, the measures, the thresholds, the seeds and the pass rule, all fixed here before any run of this follow-up. The §3.5 results, numbers and tables (REPORT §3.8) are **not** changed by this follow-up; this test is reported next to them, never in place of them.

**Scope.** Branch `sensory-inputs`; no push, no merge, nothing deleted, no history rewrite. Published model only (LIF parameters, connectome, signs unchanged; no variant; no pruning; full brain). Open loop only: the flight controller is not changed, no closed-loop run. Body fixed. Same path as §3.5 (FlyGym eye geometry → `Retina` → FlyVis → 32-type boundary layer → Poisson rates; every other input 0 Hz). No new source is cited.

#### Step 0 (read only, no simulation)
**(a) What the §3.5 post-hoc looks showed about the loom (REPORT §3.8, "Post-hoc / exploratory looks", written there after the results were known); these full sentences are the record that this test was designed with the result in view:**
1. In the pre-registered window 200–1000 ms the loom drove the boundary layer only weakly: the mean rate of the driven eye was 0.43 Hz for loom-left (and 0.44 Hz for loom-right) against 0.10 Hz for grey, because with l/v = 40 ms most of the expansion happens in the last 150 ms of that window; so the "no loom response" of §3.8 means "not testable in this window", not "no response".
2. In the post-hoc window 800–1000 ms the mean boundary-layer rate of the driven eye was 1.33 Hz for loom-left and 1.34 Hz for loom-right (grey 0.10 Hz), and 5.18 / 5.67 Hz (left / right eye) for loom-front; for the receding discs it stayed at about 0.1 Hz.
3. In that same last 200 ms (800–1000 ms; validation-seed means) the lateral looms drove none of the loom clusters DNp01, DNp02, DNp03, DNp04, DNp06, DNp11, DNp07 or DNp10 (0.00 Hz each), whereas the frontal loom drove DNp04 at 24.5 Hz and, weakly, DNp02 at 1.0 Hz and DNp10 at 2.5 Hz.
4. The note on DNp04 in REPORT §3.8 reads: "DNp04's frontal response was not among the pre-registered contrasts (R and S use the lateral looms) and is not a pass." The frontal DNp04 response is therefore a post-hoc observation that motivated including the frontal loom (Rfront) here; it was not tested before.
5. Across all 472 DN types, 3 (loom-left), 1 (loom-right) and 23 (loom-front) reached ≥ 1 Hz in 200–1000 ms (validation means), against 0 for grey; and DNp01 was driven by the static grating (about 55 Hz) but not by any loom, which is why its loom contrast failed the static control in §3.8.

**(b) Loom timing in `flight/vis_stim.py` (verified by calculation from the constants, no simulation).** `LOOM_TAU = 0.040` s (l/v), `LOOM_START_DEG, LOOM_END_DEG = 5, 90`; `LOOM_TC = τ/tan(2.5°) = 0.91615 s`; `LOOM_T90 = TC − τ = 0.87615 s` (the size is 90° at 876 ms, then held; "≈ 876 ms" confirmed). Full angular size Θ(t) = 2·atan(τ/(TC − t)): 5° at 0 ms, 5.8° at 124 ms, 7.4° at 300 ms, 21.0° at 700 ms, 38.0° at 800 ms, 89.8° at 876 ms (90° at 876.15 ms), held at 90° until 1000 ms. The receding disc is the exact time reversal over the whole 1.0 s: Θ_rec(t) = Θ_loom(1.0 s − t), i.e. 90° for 0–124 ms, 90° → 21° over 124–300 ms, 21° → 5° over 300–1000 ms. The 90° disc is therefore present from the first frame of the receding stimulus (abrupt appearance on grey).

#### Stimuli (same generator, same parameters as §3.5; 0.5 s grey + 1.0 s stimulus, 60 steps of 25 ms, onset = step 20)
Seven conditions: **loom-left** (§3.5 cond. 4), **loom-right** (5), **loom-front** (6), **receding-left** (7), **receding-right** (8), **receding-front** (NEW, cond. 11: the time reversal of loom-front over the whole 1.0 s, disc centre az = 0°), **grey** (10). No parameter of the generator is changed; only condition 11 is added to `flight/vis_stim.py` (a new test file checks it; the existing test file is not touched).
Rendered rates are deterministic (FlyVis is reset before each condition, no randomness), so the already rendered boundary-layer rates of conditions 4, 5, 6, 7, 8, 10 of §3.5 (`logs/vis_dn/vd_rates.npz`, sha256 `99eb98c0289374b99f6fb24dd22456209d652f381de51b885e6f1b1cd4aadc39`, generator last changed in commit `b3479d5`) are **reused unchanged**; only receding-front is rendered, with the same render procedure. The 7 conditions are collected in a new file `logs/vis_loom/vl_rates.npz`; `vd_rates.npz` is not modified.

#### Windows (relative to stimulus onset; 25 ms steps, so every boundary falls exactly on a step boundary and **no rounding is needed**)
Step k (0-based, onset = step 20) covers stimulus time (k − 20)·25 ms … (k − 19)·25 ms.
- **W_loom = 700–900 ms = steps 48–55** (8 steps, slice `[48:56]`): the loom disc grows from 21° to 90° (reached at 876 ms, held for the last 24 ms of the window).
- **W_rec = 100–300 ms = steps 24–31** (slice `[24:32]`): the receding disc; because receding is the exact time reversal, the frames of W_rec are exactly the frames of W_loom in reverse order (90° held for the first 24 ms, then 90° → 21°). The size range is the same, the direction of change is opposite.
- **W_on = 0–200 ms = steps 20–27** (slice `[20:28]`), receding conditions only: the abrupt appearance of the 90° disc (held 0–124 ms, then shrinking to 38° at 200 ms). This window is an *onset-transient* control, it is not a pure onset window: it contains 76 ms of shrinkage.
Rate r(cluster, cond, window) = spikes of all neurons of the cluster (both sides) in the window / (n neurons × window length 0.2 s) = Hz per neuron; side rates r_L, r_R likewise. Asymmetry A = (r_L − r_R)/(r_L + r_R + 1 Hz). **Resolution note:** a single-neuron cluster has a rate resolution of 5 Hz in a 0.2 s window (one spike = 5 Hz); a two-neuron cluster 2.5 Hz; the 1 Hz thresholds below therefore mean "at least one spike in the window" for these clusters.

#### Seeds
Discovery 511, 512, 513; validation 611–615; null (degree-preserving shuffled connectome, permutation seed = simulation seed) 811–815. All new; none of 501–503, 601–605, 801–805 is reused. Per (seed, condition): fresh state (`net.restore`) and `brian2.seed(seed)` (common random numbers across the conditions of one seed; seeds are the unit of replication). Runs: discovery 3 × 7 = 21, validation 5 × 7 = 35, null 5 × 6 = 30 (grey excluded) = 86 runs.

#### Input check (from the rendered rates, BEFORE any brain run; computed from `vl_rates.npz` after receding-front is rendered, using conditions 4, 5, 10)
Boundary-layer mean rate over all neurons of one eye in W_loom (steps 48–55); "driven eye" = left eye for loom-left, right eye for loom-right (as in §3.8: loom-left drives the left-eye boundary neurons). Both requirements must hold:
1. For loom-left (left eye) **and** loom-right (right eye): mean rate in W_loom ≥ **3 ×** the grey mean rate of the same eye in the same window.
2. A_in(loom-left, W_loom) and A_in(loom-right, W_loom) have **opposite signs** and each |A_in| ≥ **0.05**, with A_in = (mean rate of left-eye boundary neurons − right-eye)/(sum + 1 Hz) over all boundary-layer neurons.
Recorded, not criteria: the same numbers for loom-front, the receding conditions in W_rec and W_on, the expected signs (loom-left > 0, loom-right < 0).
**If either requirement fails, no brain run is made, the result is written as "input too weak, not testable" and nothing is changed or re-rendered to rescue it.**

#### Clusters and measures (all fixed here)
Loom clusters DNp01, DNp02, DNp03, DNp04, DNp06, DNp11 (6) and landing clusters DNp07, DNp10 (2); neuron lists as in §3.5 Step 0(b) (all single neurons per side, 1 left + 1 right; DNp10 = exact type).
- **R** = ½[r(loom-L, W_loom) + r(loom-R, W_loom)] − ½[r(recede-L, W_rec) + r(recede-R, W_rec)] (Hz); the 6 loom clusters.
- **S** = A(loom-L, W_loom) − A(loom-R, W_loom); the 6 loom clusters.
- **Rfront** = r(loom-front, W_loom) − r(recede-front, W_rec) (Hz); the 8 clusters.
**Number of a-priori tests: 20** (6 R + 6 S + 8 Rfront). None is removed afterwards. **No multiple-comparison correction is applied.** For orientation only: pure noise passes the 5/5 sign requirement with probability 2⁻⁵ ≈ 3 % per test (≈ 0.6 expected false sign-passes in 20 tests before criteria 3–5). The 8 loom/landing clusters are the same clusters as in §3.5 H3/H4, so the tests are not independent of the §3.8 tests on the same neurons.

#### Direction and pass criteria
Direction of each (cluster, measure) = sign of the 3-seed discovery mean (exactly 0 → no direction → FAIL), committed in a separate `direction-fixing` commit before any validation run.
All of the following must hold:
1. **Not SILENT:** the discovery mean r is ≥ 1 Hz in at least one of the (condition, window) pairs the measure uses — R: loom-L and loom-R in W_loom, recede-L and recede-R in W_rec; S: loom-L and loom-R in W_loom; Rfront: loom-front in W_loom, recede-front in W_rec. Otherwise **SILENT** (not testable, not a failure; not tested further).
2. **Sign:** the sign of the effect equals the fixed direction in **5/5** validation seeds.
3. **Magnitude:** |validation mean| ≥ 1 Hz for R and Rfront; ≥ 0.10 for S.
4. **Onset-transient control (R and Rfront only):** validation mean r(loom, W_loom) > validation mean r(receding, W_on) (R: lateral conditions averaged, ½[loom-L + loom-R] > ½[recede-L + recede-R]; Rfront: loom-front > recede-front), strictly. The response must exceed the "a dark disc appeared" response. S has no onset control.
5. **Null:** the same measure on the shuffled connectome (seeds 811–815, the same conditions, grey excluded): |real validation mean effect| > |effect| of **each** of the 5 null seeds.
Categories: **PASS / FAIL / SILENT**. The SILENT rule is evaluated first, then the direction rule, then 2–5.
**Labels.** If S passes, its label is **"lateral position of the disc"**; it is **not** a claim of loom specificity (S compares left with right, not loom with a non-loom). Loom specificity is written only for an R or Rfront pass. Because the sign is fixed on the discovery seeds, an R or Rfront pass with a negative direction (receding larger than loom) is labelled "receding-preferring, not a loom response".

#### Exploratory screen (label: EXPLORATORY)
All DN types of the model (472; the 8 neurons with side "center" included; DNg02 subtypes separate), measures **R** (lateral conditions, as above) and **Rfront**, computed on the **discovery seeds only**; types SILENT by criterion 1 are dropped; the 20 a-priori (cluster, measure) pairs are excluded; each remaining pair gets score = |discovery mean effect| / 1 Hz; the **10 highest-scoring pairs** (ties: alphabetical by type, then R before Rfront) are the candidates; their direction is the sign of the discovery mean; they are then tested on validation and null with exactly criteria 2–5 (including the onset control 4). Always reported together as: number of pairs screened, number of candidates (10), number that pass. The screen is not repeated or widened after the result.

#### Reporting rules
- Every statement about this test carries the label "follow-up designed after the §3.8 results were known; new window, new seeds". Results are reported as they are; a negative or untestable result is written as such. Anything computed after seeing the results of this follow-up (other windows, other contrasts, per-subtype or per-neuron looks, time courses) is labelled **post-hoc / exploratory** and is not a pass.
- Windows, thresholds, parameters, clusters and seeds are not changed after any result of this follow-up is seen; deviations, if any, are listed as deviations.
- A passing cluster is labelled "BRAIN readout candidate (open loop, not yet used for control)"; if none passes, that is stated.
- Limits written in advance: open loop only; no VNC; FlyVis is a trained model, not the fly's circuit; boundary-layer rates are a Poisson stand-in for graded signals; the loom and receding windows are mirror images in stimulus content but not in history (W_loom follows 700 ms of a small disc; W_rec follows a 100 ms-old abrupt appearance of a 90° disc), so R also contains onset-transient and adaptation differences, which tends to make R **smaller** (the onset transient raises r(receding, W_rec)); most clusters are single neurons per side, so rates are coarse (5 Hz steps); the frontal stimulus falls on the anterior edge of both eyes (overlap −14° … +14°); the null is 5 shuffled seeds (a minimal null, not a p-value); the hand-made part (stimulus generator, rate transduction constants `R_MAX`, `R_CLIP`, boundary-layer selection) and the connectome part are named separately in the report, and the screen does not say how much of any behaviour comes from either.
- Order: (1) this section committed; (2) scripts + `tests/` addition for condition 11 + PREREGISTRATION_LOG row committed; (3) geometry test, input check from the existing rates, render of receding-front; (4) discovery runs (511–513); (5) direction-fixing commit; (6) validation (611–615); (7) null (811–815); (8) report script, REPORT section (new, §3.8 untouched), README, provenance. One run at a time, detached, `DONE` markers; if a session is cut, runs resume from the files.

### 3.6 Training ladder, step 1 (all three rounds): a TRAINED linear readout from the 1,299 descending neurons replaces the hand-made route commands (pre-registration, 2026-10-06, written BEFORE any run, recording or smoke run of this step)
**Label for the new arm (used everywhere): "TRAINED READOUT (brain unchanged)".** Branch `sensory-inputs`; no push, no merge, nothing deleted, no history rewrite. Published model only (LIF parameters, connectome, signs, dt 0.1 ms, 25 ms decision step unchanged; no variant; no pruning; full brain). The n1/n2 flights and all earlier results are unchanged. No reinforcement learning, no policy gradient, no backpropagation: the only fitted object is one ridge regression (imitation of the hand-made teacher). No new source is cited.

**Arms so far:** n2 (brain only; did not land), n1 (hand-made route + brain feeding decision; landed). **New arm T1:** brain and connectome unchanged; the four hand-made *route* commands of n1 are replaced by the output of a trained linear readout of the DN activity. Three versions of T1 (same readout method, different input): T1-real (published brain), T1-shuffled (degree-preserving shuffled connectome, permutation seed 901), T1-bypass (no brain; fixed random projection of the boundary-layer rates). This round (1/3) only does Step 0 to Step 3 below (pre-registration, log, recording code, teacher flights). Training, closed-loop trials and the exam are later rounds under the rules written here.

#### Step 0 (read only, no simulation; `fly_flight_brain_body_simulation.py` = MAIN, `flight/hybrid.py` = HYB)
**(a) Command channels of the n1 flight (config `--hybrid --vision-boundary --no-olfaction --dn-reference data/dn_lr_reference_sB.json --no-brain-steer --head-reflex --postures`, §3.3d).**

| channel | source | value range (n1 seed 3 record) | where |
|---|---|---|---|
| turn, odor term `turn_hand` = 2·tanh(20·I_asym), take-off/cruise only (0 in approach/descend) | HAND-MADE (reads the odor field at the head) | −0.44 … +0.50 (cap ±2 before the sum) | HYB `turn_hand` L94; MAIN L453 |
| turn, FlyVis term `turn_flyvis` = b_loom (FlyVis T5 L/R, low-passed) | FLYVIS (FlyVis network, not FlyWire; walking constants) | −0.047 … +0.028 (cap ±0.15) | `sensors.LoomBias` L56; MAIN L311, L453 |
| turn, brain term `turn_brain` (DNp15) | BRAIN, **exactly 0** under `--no-brain-steer` | 0 | MAIN L449 |
| turn_total = clip(turn_brain + turn_hand + turn_flyvis, ±2.5) = wing yaw command | combination | −0.46 … +0.50 | HYB `combine_turn` L190; MAIN L454 |
| collective `thrust_hand` (lift fraction − 1): odor vertical gradient + climb-only floor (take-off/cruise), altitude target platform top + 8 mm (approach), sink 30 mm/s (descend), + take-off boost 0.10 | HAND-MADE (odor gradient, geometry of the platform) | −0.42 … +0.50 (lift 0.58 … 1.50; limits 0.3 … 1.8) | HYB `thrust_hand` L70; MAIN L457; `wing_command` L179 |
| body nose-down tilt `pitch_hand` (rad): fixed 12° in cruise; approach/descend: world-frame position controller towards the platform centre | HAND-MADE (reads the platform position) | −0.017 … +0.211 (limit ±20° = ±0.349) | HYB `tilt_hand` L109; MAIN L461 |
| body bank `roll_hand` (rad), same controller | HAND-MADE | −0.007 … +0.009 (limit ±0.349) | HYB `tilt_hand`; MAIN L461 |
| phase machine: take-off timer (10 steps) → cruise → approach when the horizontal distance to the platform centre < 100 mm → descend (d < 4 mm, speed < 40 mm/s, above the platform) → touchdown (≥ 2 tarsi on the platform on 2 consecutive steps) → landed | HAND-MADE (reads the simulator position and contact) | n1 seed 3: 9 take-off, 52 cruise, 39 approach, 20 descend, touchdown at step 120, the rest landed | HYB `HybridPhases` L134; MAIN L422 |
| wings on/off, leg extension in approach/descend, leg tuck at take-off, touchdown legs | HAND-MADE, driven by the phase | discrete | MAIN L424–L440 |
| haltere attitude PD and yaw damping (acts every physics sub-step) | REFLEX (HAND) | torque | `body.py` L361–L369 |
| head (gaze) stabilisation | REFLEX (HAND), `--head-reflex` | neck angles ≤ 15° | `body.py` L386; `head_reflex.py` |
| flight / feeding leg postures | HAND; the feeding posture follows the brain's MN9 decision | discrete | MAIN L443 |
| feeding decision = MN9 (CB0701) > 10 Hz | **BRAIN** | 0 … 93 Hz | `vnc_bridge.proboscis` L98; MAIN L418 |

**(b) Which of these are route commands** (produced to reach the target from position information): `turn_hand`, `thrust_hand`, `pitch_hand`, `roll_hand` (all read the odor field or the platform position through the simulator) and the phase transitions (distance < 100 mm, descend condition). **The readout replaces exactly the four continuous commands `turn_hand`, `thrust_hand`, `pitch_hand`, `roll_hand`** (the "route commands"). Unchanged as in n1: balance (haltere PD), head reflex, postures, FlyVis `turn_flyvis` (it is a FlyVis term, neither route nor brain), the wing-command mapping, and the feeding decision (MN9 in the brain). **Interpretation fixed here, because the pre-registration text left it open: the phase machine, including its position-reading transitions (approach, descend, touchdown) and its take-off timer, stays HAND-MADE in all T1 arms.** Reason: a fixed linear readout of DN activity has no way to output a discrete state change, S1 needs a touchdown that the phase machine detects from contact, and the hand-made phase is the same scaffold for the teacher and the readout. Consequence, written in advance: the readout does not decide *when* to land; the simulator tells the controller when the platform is within 100 mm and when to descend; a T1 pass is therefore a pass of the continuous route commands only, not of the whole landing sequence.

**(c) Can the teacher compute its command in any body state?** Yes. The four commands are pure functions of (phase, position, velocity, heading, odor sampled at the head position in the gaze frame): `H.turn_hand(I_asym, phase)`, `H.thrust_hand(phase, z, v_z, I_grad)`, `H.tilt_hand(phase, pos, vel, heading)`. The odor field is a static table (`build_arena_odor_field`, depends on the pedestal position, rebuilt per start). The only state is the phase (HybridPhases: t_in, touch_run), which is advanced by the same machine during the readout's own flight; the teacher label of a visited state is computed with that phase. So labelling the states visited by a learner is possible; this is implemented in a later round.

**(d) Can the boundary-layer rates of one flight be replayed open loop into another brain?** Yes, for every step up to touchdown, and verified on the existing records. In n1 the brain does not influence the body before touchdown: `--no-brain-steer` makes `turn_brain` exactly 0, the odor/altitude/tilt terms and the phase machine read only the simulator, `turn_flyvis` comes from FlyVis, and the only brain output used, MN9, switches the feeding posture only while landed (MAIN L443). Boundary-layer rates are a function of the body trajectory (deterministic FlyVis, deterministic render). Check on records: the six n1 flights with different brain seeds (3, 10–14; `simulations/flight_v44/46/48/50/52/54_*_data.h5`) have `max |pos − pos_seed3| = 0` and `max |vbnd_type_rate − …| = 0` over **all 300 steps** (the feeding decision happened at the same step 120 in all six, so even the post-touchdown posture was identical). Limits of this statement: (i) after touchdown the feeding posture follows the brain's MN9 decision, so with a different brain (shuffled) the post-touchdown body and rates could differ; training samples therefore use only wings-on steps (take-off … descend), which are before touchdown, where replay is exact; (ii) the replay must also supply the platform-contact sugar input (a function of the body, recorded as `sugar_rate_in`) and reproduce the perch calibration (10 steps) and input-cut (8 steps) stages of the flight script, so these steps are recorded too. Replay and closed-loop trials with the shuffled brain are **not** part of this round.

**(e) Wall time of one n1 flight** (`logs/starts/run_starts.out`, 8 flights, same configuration, 300 steps): 6 min 19 s … 6 min 35 s per flight including setup (odor field, brain build, FlyVis); loop ≈ 280 s of it (0.93 s per 25 ms step, of which the brain 0.39 s); peak RSS 3.6 GB. 16 teacher flights in sequence ≈ 1 h 45 min. Upper bound of the whole step (all rounds, all arms, every trial run to its allowed maximum) in flights: teacher 16 + exam teacher 6; per arm 3 correction rounds × 12 + up to 4 trials × 4 validation = 52; 3 arms = 156; exam 3 × 6 = 18; total ≤ 196 flights ≈ 21 h of flight time (T1-bypass runs no brain and is faster). A later round may not start if its estimate is unaffordable; then it is reported as not run, not shortened.

#### The 22 start conditions (fixed here; drawn once)
Ranges are those of §3.3f: pedestal offset DX, DY ∈ [−40, +40] mm, initial heading ∈ [−60°, +60°] (§3.3f used ±40 mm and ±30°/±60° one at a time; here offset and heading are drawn **jointly**, which §3.3f did not test). Draw: `numpy.random.default_rng(20261006)`; for i = 1..22 in order: `DX = uniform(−40, 40)`, `DY = uniform(−40, 40)`, `YAW = uniform(−60, 60)`; rounded to 0.1 mm / 0.1°. All lie inside the odor grid and clear of the towers (the flag checks this). Split by order: 1–12 training, 13–16 validation, 17–22 exam.

| id | role | DX (mm) | DY (mm) | YAW (deg) |
|---|---|---|---|---|
| 1 | train | +24.9 | −14.2 | +59.3 |
| 2 | train | −22.1 | +3.9 | −34.7 |
| 3 | train | +7.2 | −18.3 | +46.6 |
| 4 | train | +32.8 | −26.8 | −23.4 |
| 5 | train | +31.7 | +25.7 | +7.8 |
| 6 | train | +39.6 | −37.8 | +47.6 |
| 7 | train | +7.7 | −14.0 | +5.8 |
| 8 | train | −15.5 | −21.5 | +12.3 |
| 9 | train | +9.7 | +22.9 | +40.0 |
| 10 | train | +28.9 | +28.6 | +42.8 |
| 11 | train | −17.6 | −0.1 | −11.6 |
| 12 | train | −8.2 | −38.3 | −56.4 |
| 13 | validation | −8.1 | −23.1 | +43.1 |
| 14 | validation | −29.7 | −35.9 | +10.7 |
| 15 | validation | +39.9 | −4.7 | −58.2 |
| 16 | validation | −35.9 | +28.2 | +46.2 |
| 17 | exam | +34.6 | +15.0 | +19.9 |
| 18 | exam | −17.3 | −39.2 | +57.3 |
| 19 | exam | −24.4 | −26.5 | +28.7 |
| 20 | exam | +13.2 | +2.0 | +13.6 |
| 21 | exam | −33.3 | −4.0 | −33.2 |
| 22 | exam | +7.8 | −37.0 | +45.5 |

**The exam starts 17–22 are not used in any run, smoke run, recording test or figure before the exam day** (the table above is the only place they appear). Flights: `--start-offset DX DY --start-yaw YAW`, all other flags and the 300 steps exactly as n1 (§3.3d / §3.3f). Brain seed of the flight with start id i: `100 + i` for training and validation starts (the flight path does not depend on it, §3.3e and Step 0(d)); exam flights of every arm and of the teacher use brain seeds `7000 + (i − 16)`, i.e. 7001–7006.

#### Recording (new option `--record-readout DIR`; no other behaviour changes; default off, default runs unchanged)
Per flight, one sidecar HDF5 `DIR/<run name>_readout.h5` (raw records live under `logs/`, **outside git**; the usual `simulations/*.h5` is written as before). Per 25 ms step, for the perch calibration steps (−18 … −9), the input-cut steps (−8 … −1) and the 300 closed-loop steps (0 … 299), step index as in `/spikes/step_idx`:
- `dn_counts` int16 (steps × 1,299): spike count of each of the 1,299 descending neurons (rows of `brain_model/descending_neurons.csv` present in the model, csv order), and `dn_neuron_idx` (global row of `Completeness_783.csv`);
- `teacher_cmd` float64 (steps × 4): `turn_hand`, `thrust_hand` (total), `pitch_hand`, `roll_hand` as commanded in that step (0 where undefined, i.e. the calibration / cut steps); `phase`, `wings_on`;
- body state: `pos`, `vel`, `quat`, `omega`, `heading`, `platform_contact`, `tower_contact`, `tower_penetration`, `is_feeding`, `mn9_rate` (the flight's own behaviour record is also in the normal HDF5);
- `vbnd_L`, `vbnd_R` float32 (steps × 17,185 and × 16,936): the boundary-layer Poisson rates **as sensed** in that step (also in the calibration and input-cut steps, where the brain does not use them); `sugar_rate_in` (the applied platform-contact sugar rate); `applied_inputs` flag (0 in the input-cut steps), so that the flight's brain input sequence can be re-created exactly. Rates are stored as float32 (the live rates are float64 until `set_rates`; replay and the bypass projection use the float32 values, so all three arms see the same numbers);
- metadata: start offset/yaw, seed, git hash, flags.
(`CALIB_STEPS` = 10 and `PERSIST_CUT_STEPS` = 8, so the pre-take-off steps are −18 … −9 and −8 … −1.)
A unit test (`tests/flight/test_readout_record.py`, no neural simulation, synthetic recorder input) checks array shapes, dtype, step indexing and that the DN counts equal the counts of the global `spikes/count` entries for the same neurons.

#### Readout method (the same for the three arms)
- **Samples:** every closed-loop step with `wings_on = 1` (take-off, cruise, approach, descend). Landed steps carry no command and are not used.
- **Input features:** the DN spike count of each of the 1,299 DNs per step → rate r_k = count/0.025 s (Hz) → **causal exponential filter** f_k = a·f_{k−1} + (1−a)·r_k with a = exp(−25 ms / 100 ms) (τ = 100 ms), f = 0 before the first recorded step (step −18), run through the whole recording including the calibration and cut steps (so a deployed readout can run from the first brain step) → standardised per feature with the mean and standard deviation over the **training samples**; a feature with standard deviation < 10⁻⁹ is set to 0.
  - T1-real: the DNs of the published brain; T1-shuffled: the same 1,299 DN indices of the shuffled connectome (`FlightBrain(shuffle_seed=901)`; the driven boundary-layer neurons and their Poisson synapses are not permuted); T1-bypass: the brain is ignored; the input is the vector of boundary-layer rates (L then R, 34,121 values, Hz) multiplied by a fixed random matrix P (1,299 × 34,121, entries N(0, 1/34,121), `numpy.random.default_rng(902)`), then the same filter and standardisation.
- **Model:** ridge regression, one output per route command (4 outputs, fitted independently), minimising Σ(y − ȳ − x·w)² + λ‖w‖² on standardised features with the intercept ȳ (unpenalised), float64.
- **λ** ∈ {0.1, 1, 10, 100, 1000}, chosen per output by **leave-one-flight-out cross-validation over the training flights only** (every flight, teacher or correction, is one group): the λ with the smallest summed squared held-out error; ties → the larger λ. After the choice the model is refitted on all training flights. Validation and exam flights never enter λ or any fit.
- **Output clipping** to the command range: `turn_hand` ∈ [−2.5, +2.5] (`TURN_BIAS_MAX`; the sum with `turn_flyvis` is clipped by the existing `combine_turn`), `thrust_hand` ∈ [−0.7, +0.8] (`LIFT_FRAC_RANGE` − 1), `pitch_hand` and `roll_hand` ∈ [−0.3491, +0.3491] rad (`TILT_MAX_DEG` = 20°).
- **In closed loop (later round):** the four readout outputs replace `turn_hand`, `thrust_hand["total"]`, `pitch_hand`, `roll_hand`, in the wings-on phases only; everything else as in n1. The readout at step k uses the DN counts of step k (the brain step comes first, as in n1).
- No hyper-parameter, feature set, filter constant, grid, clipping range or sample rule is changed after any result.

#### Trials, champion, exam
- **Trial 1** = fit on the 12 teacher flights only. **Trials 2–4** (at most 3 correction rounds): the current readout flies closed loop from the 12 training starts (β = 0, the learner alone drives); the states it visits are labelled with the teacher command computed in that state (Step 0(c)); the 12 new flights are added to the data (DAgger aggregation: teacher flights and all correction flights so far); the readout is refitted (λ re-selected by the same leave-one-flight-out rule). At most 4 trials per arm; every arm has the same allowance (4). An arm that has its champion stops there; **every trial that was run is counted and reported** (trial table: arm, trial, λ per output, validation S1 count, landings).
- **Validation after every trial:** the arm's readout flies the 4 validation starts (13–16), brain seed `100 + id`. Score = number of flights with S1. **Champion = the first trial with S1 in ≥ 3 of 4**; if no trial reaches 3/4, the trial with the highest score (ties: the earlier trial) and the sentence "no champion met the validation bar" is written.
- **Exam (once):** the champion of each of the three arms flies each exam start 17–22 once; the teacher (n1 configuration) flies the same 6 starts once as reference. No second exam flight, no repeat, no change of champion afterwards.
- **S1** = touchdown reached **and** no tower-contact step and no step-internal tower penetration before touchdown (as §3.3c / `verify_report_final.metrics`). **S2** = at least one step with `is_feeding` = 1 at or after touchdown (reported for T1-real and the teacher only).
- **Primary measure:** number of exam flights with S1, per arm and for the teacher. **Pass:** T1-real ≥ 5/6 **and** T1-real exceeds the better of T1-shuffled and T1-bypass by at least 3 flights. The result is written "k of 6 / pass or fail" whatever it is.
- **Reading of the outcome, written in advance:** if a control arm also lands (T1-real is not at least 3 flights above the best control, or a control reaches ≥ 5/6), the sentence is "the trained readout is sufficient; the connectome brain is not shown to contribute". A pass over both controls is written as "TRAINED READOUT (brain unchanged): passes the exam and the controls", **not** as proof that the connectome computes the route: the phase machine, the platform-distance triggers and the teacher labels are hand-made.
- Hand-made versus trained versus connectome parts are named separately in the report: hand-made = teacher (route commands), phase machine, reflexes, postures, stimulus-to-rate transduction; trained = the ridge weights; connectome = DN activity as a function of the boundary-layer input (T1-real only).

#### Round 1 (this turn) — what is done, in this order
(1) this section committed; (2) `docs/PREREGISTRATION_LOG.md` row #15 committed; (3) recording option + unit test + `pytest tests/` committed; (4) the 16 teacher flights (starts 1–16, sequential, detached, `DONE` markers, `logs/ladder/`), with S1/S2 per flight; no exam start, no shuffled replay, no fit, no closed-loop readout flight in this round; (5) FILE_PROVENANCE, verify, report. A teacher flight that fails S1 or S2 stays in the record and is reported as it is (it is not removed or repeated). A technical crash (exit ≠ 0, no HDF5) is rerun once with the same command and is reported; a behavioural result is never rerun.

#### Limits (written in advance)
The teacher reads the position and the odor field from the simulator; the readout is a trained piece standing in for the missing nerve cord (no VNC is modelled) and for the whole route-computing part of the fly; the method is imitation of a hand-made policy (behaviour cloning with DAgger aggregation), not reward learning; the phase machine and its position-reading triggers (approach at 100 mm, descend, touchdown) stay hand-made, so the readout does not decide when to land; one arena, one target, one geometry; the 22 starts are drawn from the §3.3f ranges and jointly (offset and heading together), which the teacher has not been tested on; 6 exam flights per arm (a pass of 5/6 vs a control at 2/6 is a coarse comparison, not a significance test); features are 1,299 neurons and the training set has about 12 × 120 wings-on samples per round, so the regression is data-poor; the DN activity of T1-real is not independent of the teacher's flight (same eyes, same body).

#### Round 2 (trial 1): clarifications before the run (2026-10-06, written after the code and tests of round 2 and BEFORE any replay, fit or readout flight; none of them changes a criterion, a method, a start, a seed or a clipping range of §3.6)
1. **Replay protocol.** Each teacher flight is replayed in a freshly built brain, one process per flight: the 10 perch-calibration steps (recorded boundary rates as sensed, sugar 0), the 8 input-cut steps (`silence_inputs`) and the 300 closed-loop steps (recorded boundary rates, recorded `sugar_rate_in`), in the recorded order (`applied_inputs`), with the float32 rates of the record. The Brian seed of the replay of flight id is the seed of that flight (100 + id); the brain is built as in the n1 flight script (no olfaction, vision boundary, nothing else). Audit = flight 2 into the published brain: the 1,299 DN counts of all 318 rows must be identical to the recording (the spike counts of all neurons are compared too). A difference stops the round and is reported.
2. **Shuffled replay.** Permutation seed 901 for all 16 flights (one shuffled connectome); Brian seed 100 + id per flight (same as the flight's own seed, so the only difference to the real brain is the connectome).
3. **Cross-validation details left open in §3.6.** The held-out error used to choose λ is that of the unclipped ridge prediction (clipping is applied at deployment only). Inside each leave-one-flight-out fold the standardisation (mean, standard deviation, constant-feature rule) is recomputed from that fold's training flights; the final refit standardises over all 12 training flights. The descriptive R² per command is 1 − (summed held-out squared error at the chosen λ) / (summed squared deviation of all training labels from their mean), pooled over the 12 held-out flights. The R² table is descriptive and does not enter any decision.
4. **Closed-loop readout mode (flag `--readout-model`).** The filter of the readout runs on every brain step from the first perch step (T1-bypass: on the float32 boundary rates of that step); the command of step k uses the brain step k. In the wings-on phases (take-off, cruise, approach, descend) the four route commands are the clipped readout output; in the landed phases the teacher's (zero) commands apply. The teacher command of the same state is computed from the same phase and recorded as the label; it is a pure function and does not touch the flight. T1-real flies the published brain; T1-shuffled flies the shuffled connectome (seed 901, Brian seed 100 + id); **T1-bypass still runs the published brain** (the feeding decision MN9 and the recorded DN activity need it) but the readout does not read it; S2 is reported for T1-real and the teacher only, as in §3.6.
5. **Validation flights of trial 1.** Starts 13–16, Brian seed 100 + id, in the order start 13, 14, 15, 16 for arm real, then shuffled, then bypass (12 flights, one at a time); `--record-readout` on, so the visited states, DN counts and teacher labels exist for a later correction round. Mean deviation of the readout commands from the teacher label = mean over the wings-on steps of |applied − label| per command, in the command's own unit (turn: wing-yaw command units; thrust: lift fraction; pitch and roll: rad).
6. **Records of this round.** Readout files `logs/ladder/readouts/trial1_<arm>.npz` (weights, mean, inverse standard deviation, λ per command, metadata; outside git); summary with SHA-256 in `docs/ladder/trial1_readouts.json` (in git); trial ledger `docs/ladder_trials.md`.
7. **Champion rule** is applied per arm exactly as §3.6 (first trial with S1 in ≥ 3 of 4 validation flights). A technical crash (exit ≠ 0, no HDF5) is rerun once with the same command and reported; a behavioural result is never rerun.

#### Note of 2026-10-07: step 1 stopped after trial 1 (deviation from the pre-registration; the text of §3.6 above is unchanged)
Stopped after trial 1 (decision of 2026-10-07, after the trial-1 results were known). This is a deviation from the pre-registration: stopping for futility was not a pre-registered rule. §3.6 allowed the correction rounds (trials 2–4) and prescribes the exam; neither is run.

Reason, as given at the decision: in the cross-validation on the training flights no arm predicts turn or roll better than the training mean (the cross-validated R² of turn and roll is negative in all three arms); correction rounds remove the state shift (covariate shift), they do not create information that is missing from the input; the work that was left was at most 144 flights, about 15–16 hours.

Verdict (the same sentence everywhere it is quoted): **T1 not completed: no champion in trial 1 (S1 0/4 in all three arms); trials 2–4 and the exam were not run.** Nothing that was not tested is claimed. The exam starts 17–22 were not used and will not be used for this step.

Interpretation, not tested: the teacher's turn command comes from the odour field of the simulator, while in these arms the brain receives visual input only (its olfactory input is off). The readout may therefore have been asked to extract from the DN activity a piece of information that the brain does not receive. That the turn R² of T1-bypass is about 0 is compatible with this reading; it is not evidence for it.

---
## Correction note (2026-10-07; the text above is unchanged)
Sources named above whose content could not be verified: (1) §3.3d, `G_roll = G_pitch = 0.5` "~50 % of thorax roll (Hengstenberg 1988)": the paper could not be opened; the constants are hand-set and Hengstenberg (1988) is related literature, not their source (REPORT.md, THIRD_PARTY.md §6). (2) Fishilevich & Vosshall 2005 and Couto et al. 2005 as the source of DoOR's receptor → glomerulus mapping: the bibliographic records are confirmed on Crossref, the statement about DoOR was not confirmed. (3) Huang et al. 2010 for lLN1_bc: bibliographic record only, content not verified. No constant, code or result changed.
