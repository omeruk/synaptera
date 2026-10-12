# 05 — Bir sonraki çalışma için mimari plan

**Çalışma adı (öneri):** *Synaptera-2 — BANC tabanlı, sinir kordonlu (VNC), nedensel ve öğrenebilir uçuş*
Tarih: 2026-10-12. Dayanak: `01_KOD_INCELEMESI.md` (hatalar), `02_MODEL_FIZIK_TEST_ANALIZI.md` (yapısal analiz),
`03_BANC_OLANAKLARI.md`, `04_ARASTIRMA_NOTLARI.md`.

---

## 1. Araştırma soruları ve başarı tanımı

| RQ | soru | "sonuç" sayılacak çıktı |
|---|---|---|
| RQ1 | BANC'in VNC yolları el yapımı DN → kanat köprüsünün yerini alabilir mi? | Açık döngüde DN uyarımı → doğru kanat MN gruplarında doğru işaretli yanıt; kapalı döngüde hover'ın köprüsüz sürdürülmesi |
| RQ2 | Uçuş tutum refleksi (haltere/ocelli/HS → kanat direksiyon MN) connectome'dan kapalı döngüde stabil mi? | ±30° yalpa/rol bozulmasında el yapımı PD'ye göre ön-kayıtlı kriterler (Synaptera b1–b3 benzeri) |
| RQ3 | Beslenme kararının tetiği doğal yoldan (tarsal GRN → VNC → AN → SEZ → MN9 eşdeğeri) gelebilir mi? | "HAND-MADE tetik" etiketinin kaldırılması |
| RQ4 | Topolojisi sabit, dinamik parametreleri eğitilen connectome uçuş görevlerini öğrenir mi, gerçek topoloji kontrol graflarından iyi mi? | TRAINED kolunda görev başarısı + rewired/rastgele/MLP kontrolleriyle ≥3 tohumda fark |
| RQ5 | Kalkış kararı (looming → DNp01 → TTM) ve iniş beyinden gelebilir mi? | Kalkış/iniş fazlarının en az birinin HAND → BRAIN/VNC etiketine geçmesi |

Her RQ ayrı ön-kayıtlı; biri başarısız olursa diğerleri sürer (negatif sonuç da çıktıdır).

## 2. Korunacak ve yeni ilkeler

**Synaptera'dan korunacak:** her motor/duyu terimine tek kaynak etiketi ve ayrı kayıt; ön-kayıt + doğrulama betiği;
negatif sonuçların eşit ağırlıkta raporu; veri hash'leri; DEV alt ağların asla sonuç sayılmaması.

**Yeni:**
1. **Etiket kümesi genişler:** `BRAIN` (beyin), `VNC` (sinir kordonu connectome'u), `HAND`, `REFLEX` (el yapımı),
   `TRAINED`, `FLYVIS`. Ek olarak **parametre köken sınıfı** (Fly.exe'den): `M` ölçülmüş, `P` popülasyon önceli,
   `F` uydurulmuş (neye uydurulduğu yazılı), `E` mühendislik iskelesi, `I` kurtarılamaz.
2. **Nedensel zamanlama:** beden her zaman nöral motorun bir eşleme aralığı gerisinde (komut kuyruğu); gecikme
   konfigürasyonda ve HDF5'te açık.
3. **Kalite kapıları (ön-kayıtlı):** L/R simetri (|log2 R/L| < 0,5), proofreading durumu, girdi/çıktı derecesi,
   yol (hop) varlığı — bir okuma ya da yol kapıdan geçmeden deneyde kullanılmaz.
4. **Harici ön-kayıt:** OSF (veya eşdeğeri) + repo içi kayıt.
5. **Tohumlar anlamlı:** fiziksel gürültü (rüzgâr darbesi, sensör gürültüsü, başlangıç pozu) tohumla değişir; ≥5 tohum.
6. **Kontroller her deneyde:** aktivite-eşli karıştırılmış graf, aynı dereceli rastgele graf, ablasyon, (eğitimde) lineer + MLP.

## 3. Katmanlı mimari

```
┌──────────────────────── 6. Deney / görev katmanı (tasks/, prereg/) ─────────────────────────┐
│ görev merdiveni T0..T6, kriterler, tohum + fiziksel gürültü, değerlendirme, rapor/verify     │
└───────────────▲───────────────────────────────────────────────────────────┬────────────────┘
                │ ölçüm/kayıt                                                │ konfig (YAML + hash)
┌───────────────┴──────┐  durum   ┌───────────────────────────┐            │
│ 1. Beden / fizik     │────────▶ │ 3. Duyu arayüzleri        │            │
│ MuJoCo: flybody veya │          │ vision: FlyVis + L3 parl. │            │
│ NeuroMechFly;        │          │ haltere/kanat CS, JO,     │            │
│ kanat modeli         │          │ tarsal GRN, (koku)        │            │
└──────────▲───────────┘          └─────────────┬─────────────┘            │
           │ kuvvet/tork, eklem               hız/akım (etiketli)          │
┌──────────┴───────────┐                        ▼                          │
│ 4. Motor arayüzleri  │ MN aktivitesi ┌──────────────────────────────────┐ │
│ kanat güç/direksiyon │◀───────────── │ 2. Nöral motor (engine/)         │◀┘
│ MN → strok; haltere, │   (kuyruk:    │  graf: BANC 888 (+FlyWire783,    │
│ bacak, boyun, MN9    │   1 aralık    │   MaleCNS adaptörleri)           │
└──────────────────────┘   gecikme)    │  (a) Shiu-LIF spiking — "değiş-  │
                                        │      tirilmemiş model" kolu      │
                                        │  (b) rate + eğitilebilir kazanç/ │
                                        │      sızıntı (PyTorch, GPU)      │
                                        │  (c) iletkenlik+adaptasyon+gap   │
                                        └──────────────▲───────────────────┘
                                                       │
                                        ┌──────────────┴───────────────────┐
                                        │ 0. Connectome veri katmanı       │
                                        │ ortak şema, tip eşleme, QA       │
                                        └──────────────────────────────────┘
```

### 3.0 Connectome veri katmanı (`connectome/`)
- **Adaptörler:** `banc888.py` (Dataverse 7WTH1N: `banc_888_edgelist_simple_v3.feather`, `banc_888_meta.feather`,
  NT tahminleri), `flywire783.py` (mevcut Shiu dosyaları), `malecns.py` (isteğe bağlı karşılaştırma).
- **Ortak şema:** `neurons(id, cell_type, cell_class, super_class, side, region∈{brain,SEZ,neck,VNC}, nt, nt_conf, soma_xyz, status)`,
  `edges(pre, post, n_syn, sign)`. İşaret kuralı konfigürasyonda (Shiu kuralı varsayılan; varyantlar etiketli).
- **Tip eşleme tablosu** (`crosswalk.csv`): FlyWire ↔ BANC (DN'ler, MN9 adayı, LB3 şeker GRN, HS/VS/H2, LC4/LPLC2, T4/T5,
  haltere afferentleri, kanat MN'leri); kaynak sütunu (NBLAST, isim, bağlantı profili).
- **QA raporu** (her veri sürümü için otomatik): L/R simetri tablosu (bu çalışmadaki `dn_lr_asymmetry.py` genelleştirilmiş),
  derece dağılımları, sıfır-girdi nöronlar, uyarıcı/inhibitör oranları, kritik yolların hop mesafeleri ve işaretli etki
  (`connectome_structure.py` genelleştirilmiş).

### 3.1 Nöral motor (`engine/`)
Ortak arayüz (öneri):
```python
class NeuralEngine(Protocol):
    def reset(self, seed: int) -> None: ...
    def set_inputs(self, drive: dict[str, np.ndarray]) -> None:     # grup adı -> hız (Hz) veya akım
    def advance(self, dt_ms: float) -> None:                        # bir eşleme aralığı
    def rates(self, groups: list[str], window_ms: float) -> dict[str, np.ndarray]
    def state_dict(self) -> dict: ...                               # tekrar oynatma / denetim
```
- **(a) Spiking (referans kolu):** Shiu parametreleri değişmeden; Brian2 (CPU) veya GeNN/Brian2CUDA (GPU). "Değiştirilmemiş
  model" iddiaları yalnız bu koldan. Poisson girdisi Shiu'daki gibi gecikmesiz `PoissonInput`; graded hücreler için akım
  enjeksiyonu varyantı etiketli.
- **(b) Rate + eğitilebilir (TRAINED kolu):** flyhard tarifi — `s ← (1−λ)s + λ·tanh(Ŵs + u)`, `Ŵ` = işaretli, girdi-normalize
  sinaps sayısı × (kenar kazancı); öğrenilen: kenar kazancı + nöron sızıntısı (+ isteğe bağlı hücre tipi başına kazanç).
  **Durum taşınır** (sıfırlama yok). Özel seyrek geri yayılım (parçalı kenar türevi + önceden saklanmış transpoz).
- **(c) Biyofiziksel varyant:** iletkenlik tabanlı IF + adaptasyon + gap junction (Uploading Lab yaklaşımı); dinlenme
  aktivitesi sorununu (DN'lerin %76'sı sessiz) test etmek için.
- **Denklik testi:** (a) ile (b) arasında açık döngü yanıt korelasyonu (ör. sugar→MN9, looming→DNp01) raporlanır.

### 3.2 Duyu arayüzleri (`sense/`)
| duyu | kaynak | hedef nöronlar (BANC) | not |
|---|---|---|---|
| görme | FlyGym gözleri → FlyVis | sınır katmanı (mevcut kural) + **L3 parlaklık yolu** | yakın-engel fazında alt kare ↑ (Y4) |
| haltere | gövde açısal hızı (Coriolis) | haltere campaniform afferentleri (VNC) | refleks yayı için kritik; ~ms ölçeği |
| kanat mekanosensör | strok parametreleri | kanat CS afferentleri | kas geri bildirimi |
| anten (JO) | hava akımı, rüzgâr | JO-A/B/C/E | hız/rüzgâr algısı |
| bacak tat (tarsal GRN) | tarsus–besin teması | tarsal şeker GRN'leri (VNC) | RQ3; HAND kısayolun yerine |
| bacak propriosepsiyon | eklem açıları/temas | bacak CS/kordotonal | iniş ve yürüme |
| koku | 3B koku alanı | ORN (antenal lob) | AL kilitlenmesi çözülmeden kapalı (bkz. §6) |

Her eşleme bir `Transduction` nesnesi: girdi büyüklüğü → hız; parametreleri köken sınıflı (`M/P/F/E/I`).

### 3.3 Motor arayüzleri (`motor/`)
- **Kanat:** güç kası MN'leri (DLM/DVM; strok frekansı/genliği) + direksiyon MN'leri (b1–b3, i1–i2, iii1–iii3, hg, tp; genlik
  asimetrisi, strok sapması). `MuscleModel`: MN hızı → aktivasyon (1. derece filtre) → strok parametresi değişimi;
  parametreler **yalnız literatür fizyolojisinden** (açık döngü), davranışa göre ayarlanmaz; fiziksel sınırlar (Φ ≤ ~180°).
- **Haltere MN, boyun MN** (baş refleksi el yapımı olmaktan çıkabilir), **bacak MN** (TTM kalkış, iniş uzatması),
  **MN9 eşdeğeri** (hortum; MuJoCo'ya hortum eklemi eklenirse fiziksel etki).
- **Köprü kolu:** mevcut el yapımı DN → strok köprüsü bir **kontrol kolu** olarak kalır (karşılaştırma için).

### 3.4 Beden/fizik (`body/`)
- **Seçenek A (önerilen başlangıç):** mevcut FlyGym/NeuroMechFly + iyileştirilmiş strok-ortalamalı model (genlik sınırı,
  strok düzlemi açısı, anizotrop sönüm). Hızlı, mevcut kodla uyumlu.
- **Seçenek B (sonraki):** flybody (Vaxenburg 2025) kanat eklemli akışkan modeli + desen üreteci; MN → desen üreteci
  modülasyonu. Daha gerçekçi ama zaman adımı küçük ve pahalı.
- Fizik dt 0,05–0,1 ms; **eşleme aralığı 5 ms** (refleksler için 25 ms çok kaba); görme 100–200 Hz.
- Fiziksel gürültü üreteci (tohumlu): rüzgâr darbeleri, sensör gürültüsü.

### 3.5 Eşleme ve zamanlama
```
her 5 ms aralık k:
    duyu_k   = sense(body_state_k)                # nöral motora girdi
    engine.advance(5 ms)                          # nöral durum k → k+1
    mn_k     = engine.rates(motor_groups)         # bu aralığın MN çıktısı
    body.step(motor(mn_{k-1}), 5 ms)              # beden BİR ARALIK GERİDE (nedensel)
    kayıt(k)
```
Brian2'de 5 ms'lik `run()` çağrı yükü yüksek → `network_operation` ile tek `run()` içinde eşleme veya GeNN/PyTorch.

### 3.6 Kayıt, tekrar oynatma, doğrulama
- Mevcut HDF5 şeması genişletilir: her terim + etiket + köken sınıfı; MN hızları; gecikme parametresi; QA raporu hash'i.
- **Tekrar oynatma denetimi** (Synaptera'da zaten var, "replay exact"): kaydedilen girdilerle nöral motor bit-bit aynı.
- `verify_report.py`: rapor sayılarını kayıtlardan yeniden hesaplar (mevcut yaklaşım).
- Sayısal tolerans karşılaştırması (platformlar arası).

## 4. Görev merdiveni ve fazlar (kapılı yol haritası)

| faz | iş | çıktı | geçiş kapısı |
|---|---|---|---|
| **F0** | Mevcut repo düzeltmeleri: Y1 (kuyruk), Y2 (simetri kapısı), O1, O2, Y5, O7 | düzeltilmiş Synaptera + n1 yeniden koşu (aynı sonuç beklenir) | n1 kriterleri değişmeden geçer |
| **F1** | BANC 888 veri hattı + crosswalk + QA raporu | QA tabloları; MN9/DN eşleşmeleri | kritik tipler (DNp01, DNg02, DNa02, MN9 adayı, haltere afferentleri, kanat MN) eşleşti; simetri raporu yayınlandı |
| **F2** | Açık döngü yeniden üretimler (spiking kol): sugar→MN9, tarsal GRN→MN9, looming→DNp01→TTM, haltere→direksiyon MN, HS→DN | 5 ön-kayıtlı test | ≥3/5 geçer; geçmeyenler negatif bulgu olarak raporlanır |
| **F3** | Kanat motor arayüzü + kas modeli; hover'da haltere refleksi kapalı döngü (RQ1, RQ2) | REFLEX → VNC etiketi dönüşümü (veya negatif) | ±30° bozulma kriterleri (b1–b3 benzeri), ≥5 tohum |
| **F4** | Kalkış (GF/TTM), iniş, beslenme doğal tetiği (RQ3, RQ5) | faz bazında etiket tablosu | her faz ayrı kriter |
| **F5** | TRAINED kol: rate motoru, BC + DAgger, görevler: hover → optomotor → engel → iniş (RQ4) | öğrenme eğrileri, kontrol kolları | ≥3 tohum; kontrollerle karşılaştırma ön-kayıtlı |
| **F6** | Tam görev: kalkış → kuleler → iniş → beslenme; video; makale | final raporu | — |

Görev merdiveni (her biri ön-kayıtlı kriterle):
T0 açık döngü yanıtları → T1 hover + bozulma → T2 optomotor yaw takibi → T3 GF kalkışı → T4 platforma iniş →
T5 hedefe yönelim (görsel hedef: koyu platform; koku ancak AL sorunu çözülürse) → T6 tam görev.

**Bilgi uyumu kuralı (Y3'ten ders):** TRAINED kolda öğretmen sinyali, beynin aldığı duyulardan çıkarılabilir olmalı
(ör. görsel hedefli rota). Bunun ön testi: "bypass" kolunda (beyinsiz rastgele projeksiyon) çapraz-doğrulamalı R² > 0.

## 5. Önerilen dizin yapısı

```
synaptera2/
  connectome/   adapters (banc888, flywire783, malecns), schema.py, crosswalk.csv, qa.py
  engine/       lif_brian2.py, lif_genn.py, rate_torch.py (+ sparse autograd), cond_adapt.py, protocol.py
  sense/        vision_flyvis.py, l3_luminance.py, haltere.py, wing_cs.py, jo.py, tarsal_grn.py, olfaction.py
  motor/        wing_muscle.py, haltere_mn.py, leg_mn.py, neck_mn.py, proboscis.py, legacy_bridge.py
  body/         flygym_body.py, flybody_body.py, quasi_steady.py, noise.py
  coupling/     scheduler.py (nedensel kuyruk), recorder.py (HDF5/Zarr), replay.py
  tasks/        t0_openloop.py ... t6_full.py, criteria.py
  train/        bc.py, dagger.py, controls.py (rewired/random/linear/MLP)
  prereg/       OSF bağlantıları, kriter dosyaları (değiştirilemez)
  scripts/      fetch_data.py, verify_report.py, figures/
  configs/      *.yaml (+ parametre köken kaydı assumptions.json)
  tests/        birim + entegrasyon + "golden" açık döngü testleri
```

## 6. Koku devresi için ayrı alt plan (isteğe bağlı)

Yapısal analiz, AL'deki kalıcı durumun **işaret kuralından** kaynaklandığını gösteriyor (LN+PN iç sinapslarının %77'si
uyarıcı; 54 aminerjik LN uyarıcı sayılıyor; baskın özdeğer ~2.184 sinaps → ~2,3 Hz üzerinde kendini sürdüren mod).
Seçenekler (her biri **model varyantı** olarak etiketli): (i) aminerjik nöronları hızlı yoldan çıkar (mevcut
`--nt-modulatory-silent narrow`), (ii) LN'ler için literatür işaretleri (mevcut `--nt-literature`, 24 nöron yetersiz kaldı),
(iii) adaptasyonlu nöron modeli (c), (iv) rate modelinde girdi normalizasyonu. Kapı: O1 kriteri (kesimden 100–200 ms
sonra < 0,1 Hz).

## 7. Hesaplama planı

| iş | kaynak | tahmini maliyet |
|---|---|---|
| Spiking kol, BANC ~188k nöron, CPU Brian2 | 1 süreç/çekirdek; 1 s sim ≈ 20–40 s duvar (BioReservoir ölçümlerinden ölçekleme; doğrulanmalı) | 7,5 s uçuş ≈ 3–5 dk; 5 tohum × 10 koşul ≈ birkaç saat |
| Spiking kol, GPU (GeNN/Brian2CUDA) | tek GPU | gerçek zamana yakın (FastFly/Eon benchmark'ları) |
| Rate kol eğitimi | A6000/A40 sınıfı GPU (~$0,5/saat) | flyhard pilotu: 600 adım 186 s, ~3 GB; görev başına saatler mertebesi |
| FlyVis + render | CPU/GPU | alt kare artışı maliyeti ölçülmeli |

## 8. Risk kaydı

| risk | olasılık | etki | azaltma |
|---|---|---|---|
| BANC'te MN9 eşdeğeri belirsiz | orta | RQ3, beslenme | bağlantı profili + NBLAST; birden çok aday; belirsizse FlyWire kolu kalır |
| BANC L/R proofreading asimetrisi | orta–yüksek | lateral okumalar | simetri kapısı; ayna-simetrik kontrol; nüfus düzeyi okumalar |
| VNC yolları sessiz (dinlenme aktivitesi yok) | yüksek | RQ1–RQ2 | (c) varyantı; tonik sürüş (etiketli); rate kolu |
| Kas modeli parametreleri belirsiz | yüksek | RQ1 | yalnız açık döngü literatür; duyarlılık analizi; köken sınıfı `P/F` |
| Hesaplama maliyeti (5 ms eşleme) | orta | takvim | GeNN/PyTorch; DEV alt ağ yalnız geliştirme |
| Eğitim "topoloji avantajı" göstermez | orta | RQ4 | sonuç yine raporlanır; görev seçimi ön-kayıtlı |
| Lisans | düşük | yayın | BANC CC BY 4.0; FlyWire CC BY-NC; türev dosyalar ayrı paket |

## 9. İlk iki haftalık somut iş listesi (öneri)

1. F0: `fly_flight_brain_body_simulation.py`'ye komut kuyruğu (`--motor-latency-steps 1`, varsayılan eski davranış
   kayıtlı), üzerine yazma koruması, T4/T5 sütun dosyasının koşullu yüklenmesi, Φ kırpma; testler.
2. F0: `scripts/analysis/dn_lr_asymmetry.py`'yi okuma kapısı aracına çevir; DNa02/DNp15 için raporu yayınla.
3. F1: BANC 888 indir (Dataverse erişimi gerekir), hash'le; ortak şema adaptörü; QA raporu.
4. F1: crosswalk ilk sürümü: DNp01, DNg02 (a–h), DNa01/02, DNp15, DNp07/10, MN9 adayı, LB3, haltere afferentleri, kanat MN'leri.
5. F2 ön-kaydı: 5 açık döngü testinin kriterleri (OSF + repo).

## 10. Bu planın Synaptera sonuçlarıyla bağı (neden bu sıra?)

- DNg02 sessizliği: girdisinin %54'ü inhibitör, %8'i hiç sürülmeyen yükselen nöronlardan → VNC + AN geri bildirimi ve
  dinlenme aktivitesi olmadan güç okuması mümkün görünmüyor → **F1–F3 önce**.
- DNp15/DNp10 başarısızlıkları: yapısal L/R asimetriyle uyumlu → **simetri kapısı F0'da**.
- Bacak GRN → MN9 başarısızlığı: FlyWire'da işaretli etki negatif; VNC'siz veri eksik → **BANC'te F2**.
- Eğitim merdiveni: bilgi uyumsuzluğu + DAgger'sız durdurma → **F5'te bilgi uyumu kuralı ve DAgger zorunlu**.
- Koku kilitlenmesi: işaret kuralı kaynaklı pozitif geri besleme → **ayrı alt plan (§6)**, uçuş yolunun kritik yolunda değil.
