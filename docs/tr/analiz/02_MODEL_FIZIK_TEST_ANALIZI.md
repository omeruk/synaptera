# 02 — Bağlantı yapısı, beyin modellemesi, fizik motoru ve beyin testlerinin analizi

Tarih: 2026-10-12. Bu belgedeki **yeni** sayılar bu oturumda FlyWire v783 verisi (Shiu ve ark. model dosyaları + FlyWire
ek açıklamaları, SHA-256 doğrulandı) üzerinde koşturulan betiklerden gelir:
`scripts/analysis/connectome_structure.py` → `veri/connectome_stats.json`,
`scripts/analysis/dn_lr_asymmetry.py` → `veri/dn_lr_asymmetry.txt`,
`scripts/analysis/grn_mn9_check.py` → `veri/grn_mn9.json`.
Repo raporlarından alınan sayılar kaynağıyla (REPORT.md §…) belirtilmiştir.

---

## 1. Bağlantı yapısı (connectome)

### 1.1 Genel istatistik (Shiu modelinin yüklediği graf)

| ölçü | değer |
|---|---|
| nöron | 138.639 |
| kenar (pre→post çifti) | 15.091.983 (uyarıcı 9.059.302 / inhibitör 6.032.681) |
| sinaps | 54.492.922 (uyarıcı 32.494.717 = %59,6 / inhibitör 21.998.205) |
| nöron işareti (çıkış) | 96.672 uyarıcı, 41.333 inhibitör, 634 çıkışsız |
| girdisi olmayan nöron | 1.549 (sürülmedikçe asla spike atmaz) |
| kenar başına sinaps | medyan 2, maks 2.405 |
| giriş derecesi (kenar) | ortalama 108,9, medyan 69, maks 10.356 |
| giriş sinapsı / nöron | ortalama 393, medyan 198, %99'luk 3.477 |
| karşılıklı (reciprocal) kenar oranı | %26,6 |
| öz-döngü | 0 |

Süper sınıflar: optik 77.521, merkezi 32.380, duyusal 16.353, görsel projeksiyon 8.037, **yükselen (AN) 1.736**,
**inen (DN) 1.299**, duyusal-yükselen 581, görsel merkezkaç 524, **motor 110**, endokrin 76.
En büyük sinaps akışları: optik→optik 20,2 M; merkezi→merkezi 18,4 M; optik→VPN 4,3 M; VPN→merkezi 2,0 M;
**merkezi→DN 1,47 M**; AN→merkezi 0,87 M.

**Önemli:** Modeldeki 110 motor nöronun 105'i beyin motor nöronu (hortum/farinks/anten), 1'i boyun MN; **kanat, haltere
veya bacak MN'si yok** — bunlar VNC'de. 1.736 yükselen nöron modelde var ama **hiç sürülmüyor** (VNC yok).

### 1.2 LIF aritmetiği (Shiu parametreleriyle) — neden "çok sinaps gerekli"?
- Tek sinapsın PSP tepe değeri: **0,043 mV** (9,2 ms'de; τm 20 ms, τs 5 ms, w 0,275 mV).
- Eşiğe (−52 → −45 mV, 7 mV) ulaşmak için ~**162 eşzamanlı sinaps**, ya da ortalama depolarizasyonla
  **~5.091 sinaps·Hz** (ör. 51 sinaps × 100 Hz) gerekir.
- Poisson girdi sinapsı ise **68,75 mV** (w × 250) → her girdi spike'ı garanti çıkış spike'ı. Sürülen nöronlar
  (sınır katmanının 34.121 nöronu dahil) fiilen **spike üreteci** olur; kendi tekrarlayan girdileri etkisizleşir.
- Ağda **dinlenme/tonik aktivite yok**: girdisiz ağ tamamen sessiz (BioReservoir de 0 spike ölçtü). Sonuç: zayıf veya
  net-inhibitör girdili nöronlar (ör. DNg02) hiç ateşlemez; eğitim uçuşlarında 1.299 DN'in 986'sı sabit (REPORT §3.9b).

### 1.3 Şeker GRN → MN9 (tek BRAIN kararı) ve bacak GRN'leri neden başarısız?

| kaynak | n | MN9'a doğrudan sinaps | MN9'a uyarıcı hop | işaretli doğrusal etki (1→4 adım) |
|---|---|---|---|---|
| labellar şeker GRN (LB3, 20 Shiu + 16 sağ homolog) | 36 | 0 | **2** | 0 → +2,1e-5 → +8,2e-4 → **+1,4e-3** |
| bacak şeker benzeri GRN (SA_VTV_2, bağlantıyla seçilmiş) | 12 | 0 | 3 | 0 → −2,5e-6 → −1,6e-5 → **−5,7e-6** |
| tüm bacak GRN'leri | 74 | 0 | 2 | 0 → −1,2e-5 → −2,0e-4 → **−2,0e-4** |

(İşaretli etki: her nöronun toplam girdi sinapsına normalize edilmiş işaretli bağlantı matrisinin kuvvetleriyle
yayılım — BANC makalesindeki "influence" ölçüsünün basit, doğrusal bir benzeri.)

MN9'un kendi girdisi 11.465 sinaps, **%54'ü inhibitör** (6.218); en büyük girdiler DNge062, CB0553, CB0806…
**Yorum:** bacak GRN'lerinden MN9'a giden etki yapısal olarak **net negatif** → bağlantıyla seçilmiş bacak GRN'lerinin
MN9'u sürmemesi (lab defteri bulgusu) connectome düzeyinde beklenen bir sonuç. FlyWire'da bu nöronların yalnız beyne
yükselen akson parçaları var; doğal yol (tarsus → VNC → AN → SEZ) eksik → BANC'te test edilmeli.

### 1.4 Sol/sağ asimetri — DNp15 ve DNp10 başarısızlıklarının yapısal açıklaması

Tüm beyin: sağ yarıküre nöronları (68.914) soldan (69.499) az olduğu hâlde **%10,8 daha fazla giriş sinapsı** alıyor
(sağ/sol: optik 1,157; VPN 1,133; merkezi 1,064; DN 1,065).

Tek-nöron çifti olan **383 DN tipi**:
- |log2(sağ/sol)| medyanı 0,22 (~1,17×); **%24,8'inde fark > 1,41×, %11,5'inde > 2×**; işaretli medyan sağa kaymış (+0,10).

| DN | sol girdi | sağ girdi | sağ/sol | 383 içinde asimetri sırası | raporlanan davranış |
|---|---|---|---|---|---|
| **DNp15** (direksiyon okuması, post-hoc) | 1.255 (uyarıcı 636) | 2.085 (uyarıcı 1.126) | **1,66** | **65.** | perch tabanı L 0 / R 52 Hz; statik sahnede bile sağ-baskın; doğrulama başarısız |
| **DNp10** (iniş adayı) | 7.655 | 1.849 | **0,24** | **8.** | sol 0–20 Hz, sağ her pencerede 0 |
| DNa02 (ön-kayıtlı birincil) | 12.268 | 13.159 | 1,07 | 300. | yalnız kaydedildi |
| DNa01 | 5.857 | 6.638 | 1,13 | 222. | — |
| DNp01 (dev lif) | 4.327 | 5.147 | 1,19 | 176. | — |
| DNp07 (iniş adayı) | 4.656 | 4.061 | 0,87 | 214. | her fazda ateşliyor, seçici değil |

**Sonuç:** Raporlanan iki lateral okuma başarısızlığı, okuma seçilmeden önce connectome'dan **öngörülebilirdi**.
Bu, yeniden yapılandırma (proofreading/segmentasyon) eksikliğinden veya bireysel farktan olabilir; model açısından
fark etmez — lateral bir okuma için simetri kapısı gereklidir (bkz. `05_MIMARI_PLAN.md`).

### 1.5 DNg02 (kolektif güç) neden her koşuda sessiz?
- 25 nöron, toplam 13.329 giriş sinapsı, **%54'ü inhibitör** (7.228 vs 6.101).
- Girdi kaynakları: merkezi 11.378 (IB008, PS008, IB010, PS005, IB025, PS181…), **yükselen 1.107** (AN_multi_28, AN_multi_6;
  modelde sürülmüyor), DN 600, VPN 196.
- Görsel girişe uzaklık sorun değil: DNg02'ler VPN'lerden 1–2 hop, T4/T5'ten 2–3 hop (tüm DN'lerin 1.288/1.299'u VPN'lerden ≤2 hop).
- **Yorum:** sessizlik erişilebilirlikten değil, **net-inhibitör girdi + tonik sürüş yokluğu + AN/VNC geri bildiriminin
  eksikliğinden** kaynaklanıyor. Kanat gücü okuması VNC'li bir modelde ve/veya dinlenme aktivitesi olan bir nöron
  modelinde tekrar test edilmeli.

### 1.6 Antenal lob (AL) kalıcı durumunun yapısal nedeni
- 429 ALLN: modelde **166 uyarıcı / 263 inhibitör**. Ek açıklamalardaki baskın NT: glutamat 148, GABA 147, **ACh 80,
  serotonin 40, dopamin 12, oktopamin 2** → Shiu kuralı aminleri de **hızlı uyarıcı** sayıyor.
- 685 ALPN: 474 uyarıcı / 211 inhibitör.
- LN+PN iç sinapsları: **650.947 uyarıcı / 192.129 inhibitör (%77 uyarıcı)**.
- 1.114 LN+PN'nin **913'ü**, diğer LN/PN'ler 100 Hz'de ateşlediğinde eşiği aşacak kadar tekrarlayan uyarıcı sinaps alıyor
  (net inhibisyon düşülünce 691).
- İşaretli LN+PN alt matrisinin baskın özdeğeri **≈ 2.184 sinaps** → kaba doğrusal (ortalama depolarizasyon) tahminle kazanç ≈ 2.184 × 1,375 µV/(sinaps·Hz)
  ≈ **3,0 mV/Hz**: bu moddaki ortalama aktivite **~2,3 Hz'i** aşınca eşik farkını (7 mV) tek başına sağlar →
  kendi kendini sürdüren durum. Raporlanan AL kilitlenmesi (~120 Hz, kesimden sonra sönmüyor; REPORT §3.7) bu
  pozitif geri beslemeyle tutarlı. Literatür işaretleriyle yalnız 24 nöronun değişmesi (N2) bu geri beslemeyi kırmaya yetmedi.

---

## 2. Beyin modellemesinin değerlendirmesi

**Güçlü yanlar:** yayımlanmış modeli değiştirmeden kullanma; tam beyin (alt ağ yok); her model varyantının bayrakla ve
etiketle ayrılması (`--nt-impute`, `--nt-literature`, `--apl-graded`, `--nt-modulatory-silent`); FlyVis → FlyWire sınır
katmanı kuralının davranıştan önce sabitlenmesi; karışık-connectome null kontrolü; tekrar oynatma denetiminin "bit-bit"
geçmesi (8.025.285 spike).

**Zayıf yanlar ve etkileri:**

| sorun | etki | kanıt |
|---|---|---|
| Dinlenme aktivitesi yok, tekdüze LIF | DN'lerin çoğu sessiz → okuma bilgisi yok | 986/1.299 DN özelliği sabit (§3.9b) |
| Aminler ve tüm "diğer" NT'ler hızlı uyarıcı | AL'de kaçak pozitif geri besleme | §1.6 |
| Graded (spike'sız) hücreler Poisson spike'ı ile sürülüyor; 68,75 mV tekme | sınır katmanı saf üreteç; aşırı güçlü, dengesiz girdi | §1.2; vision_boundary belgesi |
| L/R yeniden yapılandırma asimetrisi | lateral okumalar yanlı | §1.4 |
| VNC yok, AN'ler sürülmüyor | DN → kas yolu el yapımı; DNg02 sessiz | §1.1, §1.5 |
| Karışık null aktivite-eşli değil | "bağlantı" ile "aktivite düzeyi" etkisi karışıyor | karışık beyin 2,5× DN spike (§3.9b) |
| Okumalar 25 ms + 50 ms filtre | refleks ölçeğinde (ms) kontrol mümkün değil | `vnc_bridge.READOUT_TAU` |
| Post-hoc okuma seçimi | ön-kayıt değerini düşürüyor (rapor dürüstçe belirtiyor) | REPORT §2.6 |

---

## 3. Fizik motorunun değerlendirmesi

**Altyapı:** MuJoCo 3.2.7 (FlyGym 1.2.1 / NeuroMechFly v2 gövdesi), fizik dt 0,1 ms, karar başına 250 alt adım.
Kanatlar aerodinamik olarak simüle **edilmiyor**: strok-ortalamalı (kuasi-statik) kuvvet/tork `xfrc_applied` ile tüm
sineğin kütle merkezine uygulanıyor (tork kaydırması doğru). Kaldırma `F = (W/2)(Φ/Φ0)²(f/f0)²` gövde z ekseni boyunca;
karşı-kuvvet/tork (Hedrick 2009) doğrusal; uç hız 300 mm/s @ 12° kalibrasyonu; haltere refleksi PD (ωn 200 rad/s, ζ 1;
Beatus 2015'e göre ~30 ms yerleşme); baş refleksi el yapımı; engellerde yumuşak temas (solimp/solref), yapışma (adhesion).

**İyi yapılmış:** FlyGym kök gövdesindeki sahte eylemsizlik hatasının (spawn konumunda 1e-6 g kütle → rol eylemsizliğini
~60× şişiriyordu) bulunup düzeltilmesi; BADQACC uyarılarının izlenmesi; adım içi kule penetrasyonunun ölçülmesi (S1 kriteri);
bacak geçişlerinin kosinüs rampası; kule/platform dokuları (T4/T5 için kenar dışı hareket).

**Sorunlar:**
1. **Genlik sınırsız** (≤ 206° hesaplandı; `01_KOD_INCELEMESI.md` Y5).
2. **Strok düzlemi = gövde yatay düzlemi**; ileri itki yalnız gövde eğimiyle; strok düzlemi açısı ve kanat vuruş fazı yok.
3. **İzotrop doğrusal sönüm**: gerçek çırpma karşı-kuvveti yöne bağlı.
4. **Rol–yaw sabit eşleşmesi**: rol torku (F_L − F_R)·kol; ayrı kontrol yok.
5. **Görsel örnekleme 80 Hz** → yakın engelde hareket örtüşmesi (Y4).
6. **Beyin–beden adım içi akausalite** (Y1).
7. **Deterministik fizik** → tohum tekrarları bağımsız değil.
8. **Hortum eklemi yok** → MN9 kararının fiziksel etkisi yok.
9. Kanatlar statik geometri olarak çarpışmaya dahil (görüntüde çırpıyor, fizikte çırpmıyor).

Karşılaştırma: flybody (Vaxenburg ve ark. 2025) kanat eklemli, akışkan modelli ve gerçek uçuş yörüngelerini taklit eden
bir uçuş modeli sunuyor; bir sonraki aşamada seçenek olarak değerlendirilmeli (`05_MIMARI_PLAN.md` §3.4).

---

## 4. Beyin testleri ve sonuçlarının değerlendirmesi (repo raporlarından)

| test | sonuç (REPORT.md) | bu analizin yorumu |
|---|---|---|
| Final-v1 (final_a/b/c) | a: S1 ✗ (6,3 µm), b: ✓✓, c: ✗✗ | a ve b rotaları neredeyse aynı → rota el yapımı |
| DNp15 doğrulaması (ön-kayıtlı) | (a) 12/12, (b) 6/6, 3/6, 3/6, (c) 0/9 → **başarısız** | §1.4: DNp15 girdisi sağda 1,66× → statik sahnede sağ-baskınlık yapısal; Y1 gecikme hatası kapalı döngü testini de etkiler |
| final_v2a (ön-kayıtlı) | S1 ✗ (130,9 µm), S2 ✓ | ablasyon sabiti "beyinsiz" değil (+0,244 sağ dönüş) |
| n1 / n2 (post-hoc kontrol) | n1 ✓✓, n2 ✗✗ | n1 rota el yapımı; n2 beyin-yalnız iniş yok |
| Çoklu tohum (n1 5/5) | rota bit-bit aynı | bağımsız tekrar değil (deterministik fizik, direksiyon 0) |
| Başlangıç konumu/yönü (8/8) | ✓ | el yapımı rotanın sağlamlığı; beyin kontrolü değil |
| Koku O1 (+N1/N2 varyantları, upstream sürüş) | 0/8 hız, tüm varyantlarda kilitlenme | §1.6: işaret kuralı kaynaklı pozitif geri besleme |
| Görsel DN taraması | 21 a-priori testin 1'i geçti (DNp15), 8 başarısız, 12 sessiz | DNg02 sessizliği §1.5; çoğu DN tonik sürüşsüz eşik altında |
| Loom takip (çarpışma kilitli) | 0/20 | aynı |
| Eğitim merdiveni T1 (3 kol) | 0/12 uçuş iner; dönüş R² < 0 | Y3: bilgi uyumsuzluğu; DAgger yapılmadan durduruldu; 986/1.299 sessiz özellik |
| Bacak GRN → MN9 | MN9 0,0 Hz (lab defteri, kayıtlı koşu yok) | **bu oturumda bağımsız olarak doğrulandı** (§5) ve yapısal nedeni bulundu (§1.3) |

Genel okuma (rapora katılıyorum): bu modelde beyin yalnız beslenme kararını veriyor; rota, iniş ve refleksler el yapımı.
Bu analiz buna şunu ekliyor: başarısızlıkların çoğunun **önceden kontrol edilebilir yapısal nedenleri** var
(L/R asimetri, net-inhibitör girdi, işaret kuralı kaynaklı pozitif geri besleme, eksik VNC), ve bunlar bir sonraki
çalışmanın tasarımını doğrudan belirliyor.

---

## 5. Bu oturumda koşturulan testler ve doğrulamalar

### 5.1 `pytest tests/` (Python 3.10, pinlenmiş Brian2 2.9.0 / MuJoCo 3.2.7 / FlyGym 1.2.1 / numpy 2.0.2, FlyVis 1.2.0, torch 2.14.1; x86_64, 4 çekirdek)
**123 geçti, 51 atlandı, 0 başarısız** (12 dk 23 s). Atlama nedenleri: 22 × Codex `column_assignment.csv.gz` yok
(giriş gerektirir), 9 × `slow` (tam beyin), 7 × `vision_boundary_783.csv` yok (Codex), 6 × `nt_impute_783.csv`,
4 × `nt_literature_783.csv`, 2 × DN referans dosyaları (tam-beyin koşusu gerektirir), diğerleri.
Not: ilk denemede `libEGL`/`libOSMesa` olmadığı için MuJoCo render testleri toplanamadı; kurulumdan sonra geçti
(README'deki `MUJOCO_GL=egl` notuna sistem kütüphanesi gereksinimi eklenmeli).

### 5.2 Veri türetme tekrarlanabilirliği
4/4 türetilebilir dosya geliştirici kopyasıyla **SHA-256 birebir**; `t45_transduction.json` farklı (platform/torch).

### 5.3 Bağımsız açık döngü simülasyonu (değiştirilmemiş Shiu modeli, Brian2, 1 s, Shiu `PoissonInput` protokolü)

Sonuçlar `veri/grn_mn9.json` (koşu bitince doldurulur; aşağıdaki tablo tohum 0):

| sürülen nöronlar | girdi | MN9 sol / sağ (Hz) |
|---|---|---|
| Shiu'nun 20 sol şeker GRN'i | 100 Hz | 68 / 50 |
| 36 labellar şeker GRN (raporlanan koşulardaki set) | 100 Hz | 54 / 48 |
| 12 bacak şeker GRN'i (SA_VTV_2) | 100 Hz | **0 / 0** |
| 12 bacak şeker GRN'i (SA_VTV_2) | 200 Hz | 1 / 0 |

Bu, raporun "kayıtlı koşusu olmayan" bacak GRN bulgusunu bağımsız olarak doğruluyor ve labellar yolun Shiu'nun R0
eğrisiyle (100 Hz → 59,6 / 46,8 Hz) uyumlu olduğunu gösteriyor.
