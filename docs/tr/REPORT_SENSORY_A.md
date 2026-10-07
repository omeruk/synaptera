> **Lab notebook, in Turkish.** Working record of this project, kept as written during the work (moved here from the repository root for the public snapshot). The English consolidated report is [REPORT.md](../../REPORT.md); the English summary is the [README](../../README.md).

# REPORT_SENSORY_A — Aşama A (koku, tam) + bacak tat GRN'leri

Plan ve önceden kayıtlı ölçütler: SPEC_SENSORY_INPUTS §2.2, §2.4, §3.2b. Ölçütler koşulardan önce yazıldı (commit `773b8ae`) ve sonra değiştirilmedi. Kazanç, hız ya da eşik ayarlanmadı. DNp15 kalibrasyonu ve doğrulaması bu turda yok.
Hibrit koşularda rota, irtifa, yaklaşma ve iniş **EL YAPIMI**. Beyinden gelen tek davranış kararı beslenme (MN9). Yön terimi `--ablate-dn DNp15` ile perch tabanında sabit.

## Özet
1. **Spontan hızlar:** 53 glomerülün 23'ü Hallem & Carlson 2006'dan geliyor (DoOR'daki `SFR` satırı, 24 reseptör). Kalan 30 glomerül 5 Hz (VARSAYIM). Tablo: `data/orn_spontaneous_783.csv`, §1. Yeni bağımlılık gerekmedi; DoOR.data csv olarak okundu.
2. **`--olfaction-full`** (varsayılan kapalı) eklendi. 2,275 ORN glomerül başına spontan hızda sürülüyor; besin kokusu yalnız 6 besin glomerülünü artırıyor.
3. **APL varyantları: önceden kayıtlı kurala göre ikisi de geçmedi.**
   - Tüm ORN'lerin spontan girdisi, AL→LH→MB'de kendini sürdüren bir durum kuruyor. Tüm girdiler 1 s sıfırlandıktan sonra ağ spiking APL'de 3.4 Hz, graded APL'de 1.9 Hz'de kalıyor (B-K2 kaldı).
   - Spiking APL ayrıca KC seyrekliğinde (%68) ve B-K1'de kaldı.
   - Graded APL, kullanıcının saydığı (i)–(iii) ve kaçak uyarılma ölçütlerinin hepsini geçti. Yalnız karar kuralına benim eklediğim B-K2'de kaldı (§3).
   - Kural gereği tam koşu `--olfaction-full` olmadan yapıldı: koku yalnız 6 besin glomerülüyle, spiking APL.
4. **Tam koşu (v19, final_sA):** koku girdisi yalnız 298 ORN olsa da aynı kalıcı durum oluştu.
   - AL'nin ORN dışı nöronları ort. 122 Hz; LH ve MB_CA ~48 Hz; KC'lerin %65–67'si her pencerede aktif.
   - B-K1 kaldı (sürülmeyen ort. 6.9 Hz) ve B-K2 kaldı (kesmeden sonra 3.4 Hz).
   - Davranış final_sB'ye çok yakın (touchdown 121 / 122, kule teması 0), çünkü rota el yapımı.
   - Beslenme 178 adımdan 127 adıma düştü: MN9 iniş sonrası 21/24 Hz, final_sB'de 50/59 Hz.
5. **DN'ler:**
   - DNp07 tonik (60–76 Hz), yaklaşma ya da iniş seçiciliği yok.
   - DNp10 yalnız solda (12–40 Hz); touchdown çevresinde 30–40 Hz'e çıkıyor. Bu, tek nöronun 4 adımlık penceresi; çözünürlük düşük.
   - DNp01 final_sB'deki tonik ateşlemeden (28/52) ~0'a indi.
   - DNp15 L 0 / R 27–56 Hz.
   - Koku yönüyle DN sol−sağ farkı arasında ilişki yok (tüm |r| ≤ 0.11). Ancak kapalı döngüdeki besin ORN asimetrisi küçük (−5.8…+0.5 Hz), yani test zayıf.
6. **Bacak GRN'leri:** bağlantıyla 74 nörondan 12'si seçildi (hepsi SA_VTV_2). Kısa testte yalnız bacak GRN'leri 100 Hz iken **MN9 0.0 Hz** (3/3 seed). Yani 10 Hz'i geçmiyor. `--leg-grn` tam koşu komutunda olmadığı için tam koşuda yok.

## 1. Glomerül başına spontan hız (`data/orn_spontaneous_783.csv`)
- **Kaynak:** Hallem & Carlson 2006, *Cell* 125:143–160 (doi 10.1016/j.cell.2006.01.050). Değerler, reseptörün boş nöronda (Δhalo ab3A) ölçülen spontan hızı.
- **Erişim:** DoOR veritabanı (Münch & Galizia 2016, *Sci Rep* 6:21841), `github.com/ropensci/DoOR.data` (eski adı Dahaniel/DoOR.data), commit `db323a4`.
  - Her reseptör dosyasında (`data/<reseptör>.csv`) `InChIKey == "SFR"` satırı, `Hallem.2006.EN` sütunu kullanıldı.
  - Reseptör→glomerül eşlemesi DoOR'un `door_mappings.csv` dosyasından. DoOR bu eşlemeyi Couto et al. 2005 ve Fishilevich & Vosshall 2005'ten kurar.
  - Betik: `scripts/make_orn_spontaneous.py`. Dosyaları sabit commit'ten indirir ya da `--door-dir` ile yerel kopyayı okur.
- **Kurallar** (sonuçtan önce sabit):
  - DM3 (Or47a + Or33b) ve DM5 (Or85a + Or33b) iki H&C reseptörünü birlikte ifade ediyor; bunlara iki değerin ortalaması verildi (VARSAYIM).
  - H&C 2006'da reseptörü olmayan 30 glomerüle 5 Hz verildi (VARSAYIM).
  - Diğer DoOR veri setlerinin SFR değerleri yalnız bilgi olarak `door_other_sfr` sütununda; kullanılmadı.
- **Sonuç:** ORN başına ağırlıklı ortalama 10.7 Hz.
- **Besin glomerülleri** (koku yalnız bunları artırır): DM1 5 (VARSAYIM), DM2 4, DM4 2, VA2 5 (VARSAYIM), VM2 2, DP1m 5 (VARSAYIM). Eski `orn_food` girdisi bu glomerüllerin hepsine 8 Hz veriyordu.

| glomerül | ORN L/R/na | H&C 2006 reseptör (Hz) | spontan Hz | kaynak | besin |
|---|---|---|---|---|---|
| D | 16/15/0 | – | 5 | VARSAYIM 5 Hz |  |
| DA1 | 60/66/0 | – | 5 | VARSAYIM 5 Hz |  |
| DA2 | 16/22/1 | – | 5 | VARSAYIM 5 Hz |  |
| DA3 | 14/16/0 | Or23a=9 | 9 | H&C 2006 |  |
| DA4l | 19/18/3 | Or43a=21 | 21 | H&C 2006 |  |
| DA4m | 20/19/1 | Or2a=8 | 8 | H&C 2006 |  |
| DC1 | 21/18/0 | Or19a=29 | 29 | H&C 2006 |  |
| DC2 | 8/12/0 | – | 5 | VARSAYIM 5 Hz |  |
| DC3 | 15/18/0 | – | 5 | VARSAYIM 5 Hz |  |
| DC4 | 11/11/0 | – | 5 | VARSAYIM 5 Hz |  |
| DL1 | 34/34/1 | Or10a=14 | 14 | H&C 2006 |  |
| DL2d | 7/7/0 | – | 5 | VARSAYIM 5 Hz |  |
| DL2v | 8/10/0 | – | 5 | VARSAYIM 5 Hz |  |
| DL3 | 36/42/1 | Or65a=18 | 18 | H&C 2006 |  |
| DL4 | 27/25/0 | Or85f=7 | 7 | H&C 2006 |  |
| DL5 | 18/24/0 | Or7a=17 | 17 | H&C 2006 |  |
| DM1 | 35/33/0 | – | 5 | VARSAYIM 5 Hz | ✓ |
| DM2 | 29/25/0 | Or22a=4 | 4 | H&C 2006 | ✓ |
| DM3 | 32/29/0 | Or33b=25 Or47a=1 | 13 | H&C 2006 (ortalama, VARSAYIM) |  |
| DM4 | 20/20/0 | Or59b=2 | 2 | H&C 2006 | ✓ |
| DM5 | 21/21/0 | Or85a=14 Or33b=25 | 19.5 | H&C 2006 (ortalama, VARSAYIM) |  |
| DM6 | 27/25/0 | Or67a=11 | 11 | H&C 2006 |  |
| DP1l | 12/12/0 | – | 5 | VARSAYIM 5 Hz |  |
| DP1m | 16/16/0 | – | 5 | VARSAYIM 5 Hz | ✓ |
| V | 34/33/0 | – | 5 | VARSAYIM 5 Hz |  |
| VA1d | 48/45/4 | Or88a=26 | 26 | H&C 2006 |  |
| VA1v | 46/38/10 | Or47b=47 | 47 | H&C 2006 |  |
| VA2 | 34/33/0 | – | 5 | VARSAYIM 5 Hz | ✓ |
| VA3 | 13/13/3 | – | 5 | VARSAYIM 5 Hz |  |
| VA4 | 15/15/1 | – | 5 | VARSAYIM 5 Hz |  |
| VA5 | 6/5/1 | Or49b=8 | 8 | H&C 2006 |  |
| VA6 | 32/28/0 | Or82a=16 | 16 | H&C 2006 |  |
| VA7l | 8/8/0 | – | 5 | VARSAYIM 5 Hz |  |
| VA7m | 10/12/0 | – | 5 | VARSAYIM 5 Hz |  |
| VC1 | 13/13/0 | – | 5 | VARSAYIM 5 Hz |  |
| VC2 | 14/15/0 | – | 5 | VARSAYIM 5 Hz |  |
| VC3 | 14/17/0 | Or35a=17 | 17 | H&C 2006 |  |
| VC4 | 9/14/0 | Or67c=6 | 6 | H&C 2006 |  |
| VC5 | 13/12/0 | – | 5 | VARSAYIM 5 Hz |  |
| VL1 | 39/39/0 | – | 5 | VARSAYIM 5 Hz |  |
| VL2a | 33/38/0 | – | 5 | VARSAYIM 5 Hz |  |
| VL2p | 13/13/1 | – | 5 | VARSAYIM 5 Hz |  |
| VM1 | 12/13/0 | – | 5 | VARSAYIM 5 Hz |  |
| VM2 | 19/18/0 | Or43b=2 | 2 | H&C 2006 | ✓ |
| VM3 | 18/17/2 | Or9a=3 | 3 | H&C 2006 |  |
| VM4 | 35/40/0 | – | 5 | VARSAYIM 5 Hz |  |
| VM5d | 36/31/0 | Or85b=13 | 13 | H&C 2006 |  |
| VM5v | 9/14/0 | Or98a=12 | 12 | H&C 2006 |  |
| VM6l | 10/11/0 | – | 5 | VARSAYIM 5 Hz |  |
| VM6m | 17/16/0 | – | 5 | VARSAYIM 5 Hz |  |
| VM6v | 13/13/0 | – | 5 | VARSAYIM 5 Hz |  |
| VM7d | 16/17/0 | – | 5 | VARSAYIM 5 Hz |  |
| VM7v | 13/13/0 | – | 5 | VARSAYIM 5 Hz |  |

## 2. `--olfaction-full` (varsayılan KAPALI)
- **Uygulama:** `flight/olfaction_full.py`.
  - Gruplar `orn_all_L/R/C`: 2,275 tipli ORN (L 1,114 / R 1,132 / tarafı `na` 29), root_id → Completeness satırı ile. `orn_food_*`'ın yerine geçer.
  - Hız: r = r_spont,g + besin_g · (150 − r_spont,g) · f. f = ipsilateral antenin `odor_norm`'u (C: iki antenin ortalaması). Besin dışı 47 glomerül her zaman spontan hızda.
- **Kayıt:**
  - HDF5 `olfaction_full/{idx,spont_hz,food,glomerulus}_{L,R,C}` ve `meta/olfaction_full`.
  - `olf_rate_L/R` = besin glomerülü ORN'lerinin ortalama hızı.
  - Dosya adında `_sA`.
- `--no-olfaction` ile birlikte kullanılamaz.
- El yapımı koku navigasyonu (`turn_hand`, `thrust_hand`) hibritte aynen kalır; beyin girdisinden bağımsız.
- **Testler:** `tests/flight/test_olfaction_full.py`. Tablo, root_id grupları, hız kuralı, isim/CLI ve DEV alt-ağında Poisson grupları test ediliyor (DEV yalnız test içindir, sonuç değildir).

## 3. İki APL varyantı (hiçbir kazanç ayarlanmadı; graded g = 2.0 Adım 0'dan)
### 3.1 Açık döngü (`scripts/diag/sa_criteria.py`; tam beyin, yalnız `orn_all` girdisi; seed 0/1/2)
Protokol:
- S: 1 s spontan;
- O: 1 s besin kokusu (f = 1, iki anten);
- P: 1.5 s spontan;
- X: 1 s tüm girdiler 0.

| ölçüt (SPEC §3.2b) | spiking APL s0 / s1 / s2 | graded APL s0 / s1 / s2 |
|---|---|---|
| (i) AL (ORN hariç): taban → kesmeden 1.0–1.5 s sonra, Hz | 121.1→121.2 / 121.0→121.0 / 121.3→121.2 ✓✓✓ | 116.3→116.3 / 116.4→116.6 / 116.4→116.5 ✓✓✓ |
| (i) KC: taban → 1.0–1.5 s, Hz | 33.2→33.4 / 33.3→33.1 / 33.3→33.3 ✓✓✓ | 1.88→1.89 / 1.89→1.87 / 1.88→1.89 ✓✓✓ |
| (ii) KC ≥1 spike, koku 250–1000 ms (%5–15) | 68.2 / 67.9 / 68.1 % ✗✗✗ | 8.5 / 8.6 / 8.6 % ✓✓✓ |
| (iii) MN9 adım 0–139 (< 10 Hz) | 0.14 / 0.29 / 0.14 ✓✓✓ | 0.00 ✓✓✓ |
| K1 sürülmeyen ort. (< 5 Hz) · son/ilk · en yüksek nöropil | 3.55 · 1.03 · AL 48.4 ✓✓✓ | 1.95 · 1.02 · AL 47.1 ✓✓✓ |
| kayıt: X, tüm girdiler 0, 100–200 ms ağ | 3.48 / 3.44 / 3.44 Hz | 1.95 / 1.95 / 1.94 Hz |
| kayıt: X 500–1000 ms, AL / KC / LH Hz | 119.8 / 32.0 / 45.9 (s0) | 114.9 / 1.84 / 40.7 (s0) |

- **(i) geçiyor ama tabana dönüşü göstermiyor.** Taban da kesme sonrası da aynı kalıcı durumda; koku bu durumu yalnız ~%3 oynatıyor (AL 121 → 124.5 Hz).
- **Kalıcılığın kanıtı X penceresi.** Tüm girdiler sıfırken 1 s boyunca AL ~115–120 Hz, LH ~41–46 Hz. Ağ ortalaması hiç düşmüyor.
- **Bu durum yeni değil:**
  - SPEC_BRAIN_CONTROL'de (Adım 0) yalnız 6 besin glomerülü 8 Hz'de de oluşmuştu.
  - Taşıyıcının AL/LH döngüsü olduğu, en büyük kaynağın modelde uyarıcı işaretli lLN1_bc olduğu orada ölçülmüştü.
  - Spontan girdi 2,275 ORN'e yayılınca durum, kokudan önce, spontan fazda kuruluyor.
- **Graded APL KC'leri ayırıyor ama kalıcılığı kırmıyor.** KC hızı 33 Hz'den 1.9 Hz'e düşüyor ve KC seyrekliği aralığa giriyor. Ama AL/LH çekirdeği APL'den bağımsız ateşlemeye devam ediyor.
- **DN'ler (açık döngü):** DNa02 L 42–62 / R 0–2; DNp10 L 24–36 / R 0; DNp07 L 4–16 / R 0–8; DNp15 0/0; DNp01 0/0 Hz. Kokuyla belirgin değişim yok.

### 3.2 Smoke (kapalı döngü, tam beyin; `--n-steps 20 --persist-steps 40 --hybrid --vision-boundary --olfaction-full --ablate-dn DNp15 --seed 3 --no-video`)

| ölçüt | spiking (v17) | graded (v18) |
|---|---|---|
| B-K1 sürülmeyen ort. < 5 Hz · son/ilk · en yüksek nöropil | **6.60 ✗** · 1.01 · LH 46.9 | 4.46 ✓ · 1.01 · AL 43.5 |
| B-K2 1 s kesme, son 200 ms < 0.1 Hz | **3.46 ✗** (hiç 0.1 altına inmedi) | **1.95 ✗** (hiç 0.1 altına inmedi) |
| B-K3 adım / RSS | 1.00 s / 3.50 GB ✓ | 1.03 s / 3.50 GB ✓ |
| B-K4 temassız MN9 | 0.00 Hz ✓ | 0.00 Hz ✓ |
| perch ağ ort. | 11.21 Hz | 9.82 Hz |

### 3.3 Karar (mekanik, §3.2b)
- **Spiking:** (ii), B-K1 ve B-K2'de kaldı.
- **Graded:** B-K2'de kaldı.
- **İkisi de geçmedi.** Tam koşu `--olfaction-full` olmadan yapıldı: koku yalnız besin glomerülleriyle (`orn_food`, 8 Hz spontan), spiking APL. Başka ayar denenmedi.
- **Açık not:**
  - Kullanıcının saydığı ölçütler (i), (ii), (iii) ve Aşama B kaçak uyarılmasıydı (B-K1). Yalnız bunlara bakılsaydı graded varyant geçerdi.
  - B-K2'yi (ve B-K3/K4'ü) karar kuralına ben ekledim. Ekleme koşulardan önce SPEC'e yazıldı ve commit'lendi; sonuç görüldükten sonra kural değiştirilmedi.
  - B-K2'nin ölçtüğü şey, (i)'nin başlığındaki "kalıcı durum yok" hedefinin kendisi. (i)'nin işlemsel tanımı bunu yakalayamadı, çünkü taban da kalıcı durumun içindeydi.
  - `--apl-graded --olfaction-full` ile tam koşu yapılıp yapılmayacağı kullanıcı kararı.

## 4. Bacak tat GRN'leri (`--leg-grn`, varsayılan KAPALI)
- **Seçim** (`flight.groups.select_leg_sugar_grns`, `scripts/make_leg_sugar_grn.py` → `data/leg_sugar_grn_783.csv`). Davranıştan önce, yalnız bağlantıyla yapıldı (VARSAYIM):
  - Özellikler `select_sugar_homologs` ile aynı: partner tipi × giriş/çıkış × ipsi/kontra, L2-normalize, kosinüs.
  - Havuz: labellar sugar/water 129 + bitter 65. Kural: k = 5, çoğunluk.
  - Havuz içinde birini dışarıda bırakma: sugar/water 129/129 doğru, bitter 0/65 yanlış pozitif.
  - **Seçilen: 12/74, hepsi SA_VTV_2** (6 L, 6 R; `knn_frac` 1.0). Diğer 62 nöronun `knn_frac` değeri ≤ 0.2; ayrım net.
- **Kapalı döngü:** herhangi bir tarsus besin platformuna değdiğinde 100 Hz. Tarsus–GRN eşlemesi yok. Labellar 36 şeker GRN'inin sürüşü değişmedi.
- **Kısa test** (`scripts/diag/sa_leg_grn.py`; açık döngü, tam beyin, seed 0/1/2; yalnız bacak GRN'leri 100 Hz, 1 s):

| koşul | MN9 L/R Hz, 0–1000 ms (s0; s1; s2) | 3 seed ort. | > 10 Hz? |
|---|---|---|---|
| yalnız bacak GRN'leri (gerçekleşen 96–103 Hz) | 0/0; 0/0; 0/0 | **0.0** | **hayır** |
| referans: yalnız labellar şeker GRN'leri | 47/62; 52/59; 42/59 | 53.5 | evet |

- **Anatomi (yalnız açıklama):**
  - Bacak GRN'lerinden MN9'a en kısa yol 2 (L) / 3 (R) hop; labellar şeker GRN'lerinden 2 / 2 hop.
  - Bacak GRN'lerinin 3,975 çıkış sinapsı var. En büyük hedefleri AN_GNG_PRW_2 (1,242), CB1898, SLP237 ve DNg103.
  - Labellar setin 9,632 sinapsı var. En büyük hedefleri LB3 ve CB0248/CB0192 gibi SEZ ara nöronları.
  - Mevcut ağırlıklarla bacak yolu MN9'u eşiğe getirmiyor.

## 5. Tam koşu: v19 `final_sA` (food glomerülleri, spiking APL) ile final_sB yan yana
Komut (§3.3 kararıyla; kullanıcının komutundan tek fark `--olfaction-full` yok):
`fly_flight_brain_body_simulation.py --seed 3 --n-steps 300 --hybrid --vision-boundary --ablate-dn DNp15 --no-video --version 19 --tag final_sA`
→ `simulations/flight_v19_hybrid_sB_ablDN-DNp15_final_sA_data.h5` (döngü 291 s). Referans final_sB: `flight_v16_hybrid_sB_ablDN-DNp15_noOlf_final_sB` (aynı seed ve spawn, `--no-olfaction`). İki koşu arasındaki tek girdi farkı: beyne besin ORN girdisi (298 nöron).
Aşağıdaki tablolar `scripts/diag/sa_report.py` çıktısıdır.

**Okuma:**
- **Kalıcı durum tam koşuda da var.**
  - Perch kalibrasyonunda ağ ort. 10.95 Hz (final_sB'de 7.84). 8 adımlık kesmede 3.4 Hz'de kalıyor.
  - Sürülmeyen nöronların ortalaması 6.9 Hz (final_sB'de 2.2); B-K1 kaldı.
  - Sürülmeyen aktif nöron oranı %10.8'den %18.0'e çıktı. Artışın çoğu AL, LH, MB_CA ve MB lobları, SMP/SLP/CRE/SIP'te. Optik lob (ME/LO/LOP/LA) final_sB ile aynı. Görsel-motor nöropillerde aktif oran benzer, ama ortalama hız arttı: LAL 1.3 → 5.7, VES 1.8 → 7.4, PLP 1.0 → 4.8, SPS 2.2 → 3.7 Hz.
- **KC'ler seyrek değil:** her pencerede %64–67'si ≥1 spike atıyor, ort. ~33–35 Hz. Bu, spiking APL'nin açık döngüdeki %68'iyle tutarlı.
- **MN9 ve beslenme:**
  - İniş sonrası MN9 21/24 Hz (final_sB 50/59). Beslenme 127 adım (final_sB 178).
  - Adım 0'da da kalıcı durumun MN9'u bastırdığı ölçülmüştü (SPEC_BRAIN_CONTROL). Kapalı döngüde aynı etki burada da görünüyor.
  - Temassız MN9 0 Hz; B-K4 geçti.
- **Yön terimi işaret değiştirdi:**
  - Ablasyon sabiti `turn_brain` = −0.102 (final_sB +0.102).
  - Neden: perch'te DNp15 R tabanı 44 Hz (final_sB 52 Hz); 10 adımda tek nöron 11'e karşı 13 spike. DNp15 referansı (R 63.2, L 15.2 Hz) çıkarılınca normalize fark işaret değiştiriyor.
  - Bu bir beyin kararı değil. Ablasyon sabitinin perch tabanına bağlı olmasının yan etkisi. DNp15 yeniden kalibrasyonu (§3.3) sonraki tur.
  - Rota el yapımı olduğu için iniş etkilenmedi.
- **DN'ler:**
  - DNp07 tonik, seçicilik yok.
  - DNp10 yalnız solda; inişe yakın 30–40 Hz'e çıkıyor (final_sB'de 10–15). Tek nöron ve 4 adımlık pencere olduğu için seçicilik iddia edilmez.
  - DNp01, final_sB'deki tonik 28/52 Hz'den ~0'a indi. Kalıcı durum muhtemelen bu yolu bastırıyor; bu ölçülmedi.
  - DNa02 sağda tamamen sessiz (L 56–90 / R 0).
- **Koku yönü ve DN L−R:**
  - Kanatlar açıkken hiçbir DN'nin L−R farkı koku asimetrisiyle anlamlı ilişkili değil (|r| ≤ 0.11; final_sB'de koku girdisi olmadan "tüm DN" r = −0.19/+0.22).
  - Kapalı döngüde iki anten de doymaya yakın; besin ORN L−R farkı yalnız −5.8…+0.5 Hz. Bu yüzden test zayıf ve sonuç "ilişki yok", "yön kodlanmıyor" değil.


### Aktif nöronlar (kapalı döngü, ≥1 spike)

| | A n | A % | final_sB n | final_sB % |
|---|---|---|---|---|
| Toplam | 48,391 / 138,639 | 34.90 | 40,527 / 138,639 | 29.23 |
| Sürülen girdi nöronları | 29,607 / 34,455 | 85.93 | 29,242 / 34,157 | 85.61 |
| Sürülmeyen nöronlar | 18,784 / 104,184 | 18.03 | 11,285 / 104,482 | 10.80 |
| Ağ ortalaması Hz | 11.20 |  | 7.51 |
| Sürülmeyen ort. Hz | 6.939 |  | 2.235 |

### Baskın nöropile göre (L/R birleşik; ort. Hz = tüm nöronlar, aktif Hz = yalnız aktifler)

| nöropil | n | A aktif | A % | A ort. Hz | A aktif Hz | final_sB aktif | final_sB % | final_sB ort. Hz |
|---|---|---|---|---|---|---|---|---|
| ME | 58,598 | 23,842 | 40.7 | 11.62 | 28.6 | 23,657 | 40.4 | 11.77 |
| LO | 16,751 | 7,566 | 45.2 | 11.21 | 24.8 | 7,549 | 45.1 | 11.57 |
| LOP | 8,027 | 5,579 | 69.5 | 8.55 | 12.3 | 5,570 | 69.4 | 8.56 |
| LA | 6,668 | 494 | 7.4 | 3.26 | 44.1 | 488 | 7.3 | 3.18 |
| GNG | 5,222 | 523 | 10.0 | 2.04 | 20.4 | 507 | 9.7 | 1.67 |
| (yok) | 4,458 | 336 | 7.5 | 2.39 | 31.7 | 333 | 7.5 | 2.44 |
| MB_CA | 3,862 | 3,505 | 90.8 | 48.25 | 53.2 | 0 | 0.0 | 0.00 |
| AVLP | 3,803 | 617 | 16.2 | 8.35 | 51.4 | 622 | 16.4 | 8.13 |
| SMP | 3,556 | 384 | 10.8 | 4.99 | 46.2 | 121 | 3.4 | 0.05 |
| SLP | 3,039 | 349 | 11.5 | 4.20 | 36.5 | 26 | 0.9 | 0.05 |
| AL | 2,977 | 1,355 | 45.5 | 48.91 | 107.5 | 11 | 0.4 | 0.02 |
| LH | 2,383 | 1,653 | 69.4 | 47.35 | 68.3 | 20 | 0.8 | 0.03 |
| PLP | 2,233 | 368 | 16.5 | 4.83 | 29.3 | 181 | 8.1 | 1.03 |
| FB | 1,837 | 70 | 3.8 | 0.70 | 18.4 | 7 | 0.4 | 0.00 |
| PVLP | 1,728 | 282 | 16.3 | 2.81 | 17.2 | 281 | 16.3 | 2.76 |
| IPS | 1,558 | 139 | 8.9 | 1.31 | 14.7 | 175 | 11.2 | 1.14 |
| SPS | 1,418 | 275 | 19.4 | 3.73 | 19.3 | 257 | 18.1 | 2.16 |
| MB_ML | 1,123 | 126 | 11.2 | 8.67 | 77.3 | 1 | 0.1 | 0.00 |
| AOTU | 1,076 | 35 | 3.3 | 0.42 | 13.0 | 22 | 2.0 | 0.13 |
| LAL | 990 | 204 | 20.6 | 5.74 | 27.8 | 259 | 26.2 | 1.29 |
| SAD | 982 | 22 | 2.2 | 0.65 | 29.2 | 30 | 3.1 | 0.28 |
| ICL | 925 | 46 | 5.0 | 0.63 | 12.6 | 46 | 5.0 | 0.59 |
| CRE | 732 | 231 | 31.6 | 15.18 | 48.1 | 99 | 13.5 | 0.13 |
| PRW | 556 | 47 | 8.5 | 1.14 | 13.5 | 37 | 6.7 | 0.73 |
| AMMC | 509 | 2 | 0.4 | 0.08 | 19.9 | 6 | 1.2 | 0.05 |
| VES | 450 | 117 | 26.0 | 7.39 | 28.4 | 120 | 26.7 | 1.78 |
| NO | 405 | 7 | 1.7 | 0.03 | 1.7 | 10 | 2.5 | 0.16 |
| EB | 403 | 5 | 1.2 | 0.00 | 0.3 | 9 | 2.2 | 0.02 |
| SIP | 372 | 60 | 16.1 | 4.90 | 30.4 | 9 | 2.4 | 0.02 |
| SCL | 362 | 37 | 10.2 | 3.02 | 29.5 | 13 | 3.6 | 0.45 |
| WED | 354 | 19 | 5.4 | 1.77 | 33.0 | 19 | 5.4 | 1.07 |
| FLA | 328 | 3 | 0.9 | 0.21 | 23.3 | 3 | 0.9 | 0.11 |
| OCG | 272 | 0 | 0.0 | 0.00 | – | 0 | 0.0 | 0.00 |
| IB | 205 | 17 | 8.3 | 1.24 | 15.0 | 7 | 3.4 | 0.13 |
| MB_VL | 149 | 23 | 15.4 | 13.09 | 84.8 | 1 | 0.7 | 0.04 |
| PB | 100 | 2 | 2.0 | 0.04 | 2.1 | 2 | 2.0 | 0.11 |
| <100 nöronlu 9 nöropil | 228 | 51 | | 10.44 | | 29 | | 1.35 |

AL, ORN'ler hariç (808 nöron; PN/LN vb.): A ort. 122.39 Hz, aktif 86.8 %; final_sB ort. 0.06 Hz. Tüm ORN'ler (2,275): A ort. 20.57 Hz; sürülen ORN'ler (298): 117.81 Hz.

### KC seyrekliği (5,177 KC; pencere içinde ≥1 spike atan oran ve ort. hız)

| pencere | A KC ≥1 spike % | A KC ort. Hz | final_sB KC ≥1 spike % | final_sB KC ort. Hz |
|---|---|---|---|---|
| perch (10 adım) | 64.7 | 28.93 | 0.1 | 0.01 |
| takeoff (4 adım) | 64.4 | 32.47 | 0.0 | 0.00 |
| cruise (52 adım) | 66.2 | 33.11 | 0.0 | 0.00 |
| approach (42 adım) | 66.9 | 34.95 | 0.0 | 0.01 |
| descend (18 adım) | 66.8 | 35.23 | 0.0 | 0.00 |
| td -4..-1 (4 adım) | 66.3 | 35.12 | 0.0 | 0.00 |
| td 0..+3 (4 adım) | 66.5 | 35.45 | 0.0 | 0.00 |
| landed (178 adım) | 67.3 | 35.30 | 0.0 | 0.00 |

### DN / MN hızları (Hz/nöron, L / R) pencerelere göre

**A** (touchdown adım 121; pencere adım sayıları: perch 10, takeoff 4, cruise 52, approach 42, descend 18, td -4..-1 4, td 0..+3 4, landed 178)

| | n L/R | perch | takeoff | cruise | approach | descend | td -4..-1 | td 0..+3 | landed |
|---|---|---|---|---|---|---|---|---|---|
| DNp07 | 1/1 | 76.0 / 76.0 | 60.0 / 60.0 | 75.4 / 58.5 | 73.3 / 72.4 | 71.1 / 62.2 | 70.0 / 70.0 | 70.0 / 70.0 | 64.5 / 59.6 |
| DNp10 | 1/1 | 12.0 / 0.0 | 10.0 / 0.0 | 19.2 / 0.0 | 21.9 / 0.0 | 17.8 / 0.0 | 30.0 / 0.0 | 40.0 / 0.0 | 30.6 / 0.0 |
| DNp15 | 1/1 | 0.0 / 44.0 | 0.0 / 30.0 | 3.1 / 53.1 | 0.0 / 56.2 | 0.0 / 48.9 | 0.0 / 50.0 | 0.0 / 30.0 | 0.0 / 26.7 |
| DNp01 | 1/1 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.8 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.4 |
| DNa02 | 1/1 | 56.0 / 0.0 | 80.0 / 0.0 | 76.2 / 0.0 | 70.5 / 0.0 | 73.3 / 0.0 | 80.0 / 0.0 | 90.0 / 0.0 | 78.2 / 0.0 |
| MN9 | 1/1 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 10.0 / 10.0 | 20.9 / 24.0 |
| MDN | 2/2 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| neck MN | 13/13 | 0.9 / 0.0 | 1.5 / 0.0 | 1.0 / 0.1 | 1.3 / 0.0 | 1.2 / 0.0 | 0.8 / 0.0 | 1.5 / 0.0 | 1.2 / 0.0 |
| DNg02 | 13/12 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |

**final_sB** (touchdown adım 122; pencere adım sayıları: perch 10, takeoff 4, cruise 52, approach 41, descend 20, td -4..-1 4, td 0..+3 4, landed 177)

| | n L/R | perch | takeoff | cruise | approach | descend | td -4..-1 | td 0..+3 | landed |
|---|---|---|---|---|---|---|---|---|---|
| DNp07 | 1/1 | 72.0 / 76.0 | 60.0 / 50.0 | 81.5 / 66.2 | 81.0 / 71.2 | 80.0 / 68.0 | 70.0 / 60.0 | 60.0 / 60.0 | 73.7 / 66.9 |
| DNp10 | 1/1 | 16.0 / 0.0 | 0.0 / 0.0 | 13.1 / 0.0 | 16.6 / 0.0 | 8.0 / 0.0 | 10.0 / 0.0 | 10.0 / 0.0 | 15.1 / 0.0 |
| DNp15 | 1/1 | 0.0 / 52.0 | 0.0 / 40.0 | 9.2 / 62.3 | 3.9 / 61.5 | 8.0 / 56.0 | 10.0 / 50.0 | 0.0 / 40.0 | 4.5 / 41.4 |
| DNp01 | 1/1 | 28.0 / 52.0 | 40.0 / 40.0 | 27.7 / 61.5 | 28.3 / 62.4 | 28.0 / 64.0 | 30.0 / 40.0 | 10.0 / 20.0 | 14.7 / 32.1 |
| DNa02 | 1/1 | 44.0 / 8.0 | 40.0 / 20.0 | 48.5 / 17.7 | 41.0 / 5.9 | 50.0 / 0.0 | 60.0 / 0.0 | 30.0 / 0.0 | 34.8 / 3.6 |
| MN9 | 1/1 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 50.0 / 50.0 | 49.7 / 59.2 |
| MDN | 2/2 | 0.0 / 0.0 | 0.0 / 0.0 | 0.4 / 0.8 | 0.5 / 1.0 | 3.0 / 3.0 | 10.0 / 15.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| neck MN | 13/13 | 0.0 / 0.6 | 0.8 / 1.5 | 0.4 / 1.5 | 0.2 / 0.9 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.1 |
| DNg02 | 13/12 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |

### DN sol−sağ farkı ve koku yönü (tanımlayıcı; yön terimi ablasyonla sabit)

**A** (kanatlar açık 121 adım; Pearson r, sol − sağ sayım; |r| < 0.18 ≈ p > 0.05)

| DN L−R | I_asym | odor_L−R | ORN besin L−R Hz |
|---|---|---|---|
| DNa02 | -0.01 | +0.01 | +0.01 |
| DNp15 | +0.00 | -0.04 | -0.00 |
| DNp07 | -0.11 | +0.09 | +0.11 |
| DNp10 | -0.05 | +0.03 | +0.05 |
| DNp01 | +0.08 | -0.07 | -0.08 |
| tüm DN | -0.06 | +0.10 | +0.06 |

Koku asimetrisi aralığı: I_asym -0.011…+0.140; ORN besin L−R -5.8…+0.5 Hz.

**final_sB** (kanatlar açık 122 adım; Pearson r, sol − sağ sayım; |r| < 0.18 ≈ p > 0.05)

| DN L−R | I_asym | odor_L−R | ORN besin L−R Hz |
|---|---|---|---|
| DNa02 | -0.10 | +0.10 | – |
| DNp15 | +0.00 | +0.07 | – |
| DNp07 | +0.00 | -0.00 | – |
| DNp10 | +0.06 | -0.10 | – |
| DNp01 | +0.02 | -0.03 | – |
| tüm DN | -0.19 | +0.22 | – |

Koku asimetrisi aralığı: I_asym -0.107…+0.009; ORN besin L−R +0.0…+0.0 Hz.

### Davranış

| | A | final_sB |
|---|---|---|
| touchdown adımı (t s) | 121 (3.050) | 122 (3.075) |
| touchdown hızı mm/s | 7.5 | 6.7 |
| besine min / son uzaklık mm | 2.0 / 2.0 | 1.9 / 1.9 |
| beslenme adımı (ilk) | 127 (123) | 178 (122) |
| kule temas adımı | 0 | 0 |
| maks. kule penetrasyonu mm | 0.0000 | 0.0000 |
| turn_brain (ablasyon tabanı) ort. | -0.102 | +0.102 |
| turn_brain payı (sum|brain|/sum|total|) | 0.883 | 1.202 |
| ort. adım s / beyin s | 0.971 / 0.416 | 0.941 / 0.393 |
| tepe RSS GB | 3.51 | 3.52 |
| perch ağ ort. Hz | 10.95 | 7.84 |

### Ölçütler (SPEC §3.2b / §3.3b)

- **B-K1 kaçak uyarılma (tam koşu A): KALDI** — sürülmeyen ort. 6.939 Hz (< 5); son/ilk %25 = 6.982/6.720 = 1.04 (≤ 1.5); en yüksek nöropil ort. AL 48.91 Hz (≤ 50).
- B-K2 (tam koşu A, 8 adım kesme): adım başına 4.209 3.393 3.413 3.336 3.421 3.422 3.424 3.437 Hz; 100–200 ms ort. 3.426 Hz (≥ 0.1, KALDI).
- **B-K3 (tam koşu A): GEÇTİ** — ort. adım 0.971 s, beyin 0.416 s, tepe RSS 3.51 GB.
- **B-K4 temassız MN9 (tam koşu A): GEÇTİ** — 0.00 Hz (119 temassız adım); perch 0.00 Hz; temaslı 22.1 Hz.
- **B-K1 kaçak uyarılma (final_sB): GEÇTİ** — sürülmeyen ort. 2.235 Hz (< 5); son/ilk %25 = 2.235/2.120 = 1.05 (≤ 1.5); en yüksek nöropil ort. UNASGD 36.87 Hz (≤ 50).
- B-K2 (final_sB, 8 adım kesme): adım başına 0.846 0.000 0.000 0.000 0.000 0.000 0.000 0.000 Hz; 100–200 ms ort. 0.000 Hz (< 0.1, geçti).
- **B-K3 (final_sB): GEÇTİ** — ort. adım 0.941 s, beyin 0.393 s, tepe RSS 3.52 GB.
- **B-K4 temassız MN9 (final_sB): GEÇTİ** — 0.00 Hz (119 temassız adım); perch 0.00 Hz; temaslı 53.7 Hz.
- **B-K1 kaçak uyarılma (smoke flight_v17_hybrid_sA_sB_ablDN-DNp15_smoke_sA_data.h5): KALDI** — sürülmeyen ort. 6.603 Hz (< 5); son/ilk %25 = 6.550/6.466 = 1.01 (≤ 1.5); en yüksek nöropil ort. LH 46.90 Hz (≤ 50).
- **B-K2 (smoke flight_v17_hybrid_sA_sB_ablDN-DNp15_smoke_sA_data.h5, 1 s kesme): KALDI** — son 200 ms ort. 3.4572 Hz; ilk < 0.1 Hz adım None; 100–200 ms ort. 3.4476 Hz; perch ağ ort. 11.21 Hz; kesme seyri: 4.23 3.47 3.45 3.42 3.42 3.41 3.44 3.43 Hz (her 5. adım).
- **B-K3 (smoke flight_v17_hybrid_sA_sB_ablDN-DNp15_smoke_sA_data.h5): GEÇTİ** — ort. adım 1.000 s, beyin 0.427 s, tepe RSS 3.50 GB.
- **B-K4 temassız MN9 (smoke flight_v17_hybrid_sA_sB_ablDN-DNp15_smoke_sA_data.h5): GEÇTİ** — 0.00 Hz (20 temassız adım); perch 0.00 Hz; temaslı nan Hz.
- **B-K1 kaçak uyarılma (smoke flight_v18_hybrid_sA_sB_ablDN-DNp15_aplG_smoke_sA_data.h5): GEÇTİ** — sürülmeyen ort. 4.463 Hz (< 5); son/ilk %25 = 4.406/4.346 = 1.01 (≤ 1.5); en yüksek nöropil ort. AL 43.54 Hz (≤ 50).
- **B-K2 (smoke flight_v18_hybrid_sA_sB_ablDN-DNp15_aplG_smoke_sA_data.h5, 1 s kesme): KALDI** — son 200 ms ort. 1.9500 Hz; ilk < 0.1 Hz adım None; 100–200 ms ort. 1.9628 Hz; perch ağ ort. 9.82 Hz; kesme seyri: 2.81 1.97 2.00 1.95 1.97 1.98 1.98 1.99 Hz (her 5. adım).
- **B-K3 (smoke flight_v18_hybrid_sA_sB_ablDN-DNp15_aplG_smoke_sA_data.h5): GEÇTİ** — ort. adım 1.031 s, beyin 0.456 s, tepe RSS 3.50 GB.
- **B-K4 temassız MN9 (smoke flight_v18_hybrid_sA_sB_ablDN-DNp15_aplG_smoke_sA_data.h5): GEÇTİ** — 0.00 Hz (20 temassız adım); perch 0.00 Hz; temaslı nan Hz.

## 6. El yapımı / konnektom ayrımı (bu turda değişmedi)
- **EL YAPIMI:** kalkış zamanlayıcısı, koku→dönüş ve koku→güç haritaları, irtifa, yaklaşma, iniş ve bacak açılması, seyir eğimi, haltere refleksi (REFLEX).
- **BEYİN (konnektom):** beslenme (MN9 > 10 Hz). DNp15 yön terimi bu koşularda ablasyonla sabit; beyinden gelmiyor.
- **FLYVIS:** b_loom dönüş terimi.
- **Bu turun eklemeleri:** yalnız beyne giden duyu girdileri (ORN spontan hızları, bacak GRN'leri). Davranışa etkisi yalnız MN9 üzerinden.
- **VARSAYIM'lar:**
  - 30 glomerül 5 Hz;
  - ortak ifade ortalaması (DM3, DM5);
  - koku yalnız 6 besin glomerülünü artırır;
  - bacak GRN'leri bağlantı benzerliğiyle seçildi ve tarsus eşlemesi yok;
  - graded APL mekanizması ve g = 2.0.

## 7. Dosyalar ve yeniden üretim
- **Veri:** `data/orn_spontaneous_783.csv` (`scripts/make_orn_spontaneous.py`), `data/leg_sugar_grn_783.csv` (`scripts/make_leg_sugar_grn.py`).
- **Kod:** `flight/olfaction_full.py`. `flight/brain.py`, `flight/groups.py`, `flight/recorder.py` ve `fly_flight_brain_body_simulation.py` güncellendi (`--olfaction-full`, `--leg-grn`).
- **Testler:** `tests/flight/test_olfaction_full.py`, `tests/flight/test_leg_grn.py`. `pytest tests/`: 109 passed, 10 skipped. `--runslow` ile iki seçim tekrar üretim testi geçti.
- **Koşular:** smoke v17 (spiking) ve v18 (graded): `flight_v1{7,8}_hybrid_sA_sB_ablDN-DNp15[_aplG]_smoke_sA`. Tam koşu v19.
- **Betikler:**
  - `scripts/diag/sa_criteria.py --variant spiking|graded`, ardından `--report sa_criteria_*.npz`;
  - `scripts/diag/sa_leg_grn.py`;
  - `scripts/diag/sa_report.py NEW REF --smoke ...`.
