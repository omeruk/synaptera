# 03 — BANC (Brain And Nerve Cord) beyni için yapılabilecekler ve olası sonuçlar

Tarih: 2026-10-12. Kaynaklar belgenin sonunda. Sayılar BANC makalesi/README'si ve BANC'i kullanan projelerin kendi
belgelerinden alınmıştır; bu ortamda BANC verisi **indirilmedi** (Harvard Dataverse bu ortamın ağ politikasında kapalı),
dolayısıyla BANC üzerinde bağımsız hesap yapılmadı. FlyWire v783 üzerindeki hesaplar `02_MODEL_FIZIK_TEST_ANALIZI.md`'de.

## 1. BANC nedir, Synaptera için neden önemli?

| özellik | FlyWire v783 (şu an kullanılan) | BANC v888 |
|---|---|---|
| kapsam | yalnız beyin (+ optik loblar, SEZ) | beyin + SEZ + boyun bağlantısı (cervical connective) + **tüm VNC** |
| birey | yetişkin dişi | yetişkin dişi (cinsiyet aynı → hücre tipi eşlemesi kolay) |
| nöron | 138.639 (Shiu modeli) | ~188.000 (Uploading Lab modelinde 188.508) |
| sinaps | 54,5 M (Shiu model dosyası; kenar başına medyan 2 sinaps) | ~199 M tahmini sinaps; Uploading Lab modelinde 42,3 M tutulan sinaps, 13,6 M kenar |
| DN / AN / efektör | 1.299 DN; AN'ler kesik akson | **1.316 DN, 1.849 AN, 1.031 efektör nöron** (MN + endokrin + visseral) |
| kanat/haltere/bacak MN | **yok** | **var** (VNC'de) |
| lisans | CC BY-NC 4.0 (ticari olmayan) | **CC BY 4.0** (Dataverse beyanı; daha serbest) |

Synaptera'nın en büyük yapısal eksikliği — **DN → kanat yolunun el yapımı bir köprü olması** (REPORT §5) — BANC ile
connectome'un kendisine devredilebilir. Ayrıca bacak tat nöronlarının (tarsal GRN) VNC'ye girip yükselen nöronlarla SEZ'e
ulaşan doğal yolu BANC'de tam olarak bulunur; FlyWire'da bu nöronların yalnız beyne yükselen akson parçaları var
(`sensory_ascending`, 581 nöron).

BANC makalesinin ana bulguları (Bates ve ark. 2026): efektörler en çok **aynı vücut parçasının** duyusal nöronlarından
etkilenir (yerel duyu-motor döngüler); DN/AN'ler davranış-merkezli kümeler halinde (uçuş, yürüme, baş yönlendirme,
temizlenme, beslenme, üreme, postür, iç durum) bu döngüleri koordine eder; mantar cisim ve merkez kompleks bu kümeleri
"denetleyici" olarak etkiler (dağıtık kontrol). Bu, Synaptera'nın "beyin = tek merkezi kontrolcü" varsayımının
neden zorlandığını da açıklar: uçuş stabilizasyonunun büyük kısmı VNC'deki yerel döngülerde.

## 2. Veri sürümleri ve tuzaklar (BANC'i kullanan projelerin deneyimi)

- **Snapshot 626** (Dataverse doi:10.7910/DVN/8TFGGB): 114.456 nöron, ~1,4–2,7 M kenar, FlyWire/MaleCNS'e göre **~3× düşük
  ortalama derece**; tiplendirme seyrek (%69). BioReservoir bu sürümle **yanal-taraf doğrulamasında başarısız**: dar bir
  duyusal girdi (Johnston organı) her denemede "hep sağ" DN yanıtı verdi; olası neden **sağda %45 daha fazla proofread
  nöron** olması. Dengelenmiş alt graf da düzeltmedi.
- **Materialization 888** (Dataverse doi:10.7910/DVN/7WTH1N, makale sürümü v3.0): `banc_888_edgelist_simple_v3.feather`,
  `banc_888_meta.feather`, NT tahminleri, influence parquet'leri, NBLAST çapraz-veri eşleşmeleri, mesh/SWC.
  **Kullanılması gereken sürüm budur.** Uploading Lab da 888 kullanıyor.
- **MN9 adı BANC'de yok** (BioReservoir'ın 626 snapshot taraması: "MN9 0"). Synaptera'nın tek BRAIN kararı MN9'a
  dayanıyor → BANC'e geçişte ilk iş, FlyWire CB0701 (MN9) karşılığını **çapraz-veri eşleşmesiyle** (NBLAST /
  `cell_type` eşlemeleri / bağlantı profili) bulmak.
- **L/R asimetrisi**: FlyWire'da bile (bkz. analiz §1.4) DN çiftlerinin %25'inde giriş sinapsı farkı >1,41×. BANC'de
  proofreading asimetrisi daha büyük olabilir → **her lateral okuma için simetri kapısı** zorunlu olmalı.
- Canlı BANC (CAVE) kısıtlı anahtar ister; statik Dataverse dağıtımı yeterli.
- Python istemcisi: `banc` (PyPI 0.6.1, `jasper-tms/the-BANC-fly-connectome`); R: `bancr`; influence hesabı:
  `ConnectomeInfluenceCalculator`.

## 3. BANC ile yapılabilecek çalışmalar (öncelik sırasıyla)

Her madde: **yapılacak iş → beklenen/olası sonuç → başarısızlık durumunda ne öğrenilir.**

### B0. Veri hattı ve köprü tabloları (ön koşul)
- BANC 888 → Synaptera ortak şeması (nöron: id, tip, sınıf, taraf, bölge [beyin/SEZ/VNC], NT + güven; kenar: pre, post,
  sinaps, işaret). FlyWire v783 ↔ BANC tip eşleme tablosu (DN'ler, MN9, LB3 şeker GRN'leri, HS/VS, LC4/LPLC2, T4/T5, haltere
  afferentleri, kanat MN'leri).
- Kalite kapıları: L/R simetri raporu (tip başına giriş sinapsı oranı), proofreading durumu, derece dağılımı, sıfır-girdi
  nöron sayısı.
- **Olası sonuç:** DN tiplerinin büyük kısmı eşleşir (Stürner ve ark. 2025 DN'leri FlyWire/MANC/BANC arasında
  eşledi); MN9 için belirsizlik kalabilir.

### B1. Açık döngü yeniden üretimler (BANC'te model doğrulama)
1. Labellar şeker GRN → MN9 eşdeğeri (Shiu protokolü, 100 Hz, 1 s).
2. Bacak (tarsal) şeker GRN → VNC → AN → SEZ → MN9 (FlyWire'da çalışmayan "doğal" yol).
3. Looming (LC4/LPLC2) → DNp01 (dev lif) → **TTM motor nöronu** (sıçrama/kalkış).
4. Haltere afferentleri → kanat direksiyon MN'leri (b1, b2, i1, iii3, hg…) — uçuş refleks yayı.
5. Görsel yatay hareket (HS/H2) → DNa/DNb/DNp15 → kanat direksiyon MN'leri.
- **Olası sonuçlar:** (1) ve (3) yüksek olasılıkla çalışır (Shiu ve Uploading Lab bulgularıyla uyumlu). (2) orta olasılık;
  çalışırsa Synaptera'nın "HAND-MADE tetik" etiketi **BRAIN/VNC**'ye dönüşür — en değerli tekil kazanım. (4) fly-cartpole'un
  MaleCNS uçuş devresi sonucu olumlu işaret; (5) yanal asimetri riski yüksek.

### B2. DN → kanat köprüsünün connectome ile değiştirilmesi
- Kanat MN'leri: **güç kasları** (DLM/DVM; dolaylı uçuş kasları, kanat vuruş frekansı/genliği) ve **direksiyon kasları**
  (b1, b2, b3, i1, i2, iii1, iii3, hg1–4, tp…; genlik/vuruş sapması). MN ateşleme hızı → strok genliği/frekansı/asimetri
  eşlemesi küçük, açıkça etiketli bir "kas modeli" (ör. b1 hızı ↔ genlik; literatür eğrileriyle ayarlanmış, davranışla değil).
- DNg02 (kolektif güç) → güç/direksiyon MN'lerine yolun yapısal analizi, sonra simülasyon.
- **Olası sonuçlar:** Yapısal olarak yol büyük olasılıkla mevcut (DNg02 MANC'de kanat premotor devrelerine giriyor).
  Dinamik olarak DNg02 FlyWire modelinde **net inhibitör girdi** aldığı ve AN'ler sürülmediği için sessizdi; BANC'de AN'ler
  ve VNC geri bildirimi devreye girince bu değişebilir — değişmezse "dinlenme aktivitesi/tonik sürüş eksikliği" ana
  darboğaz olarak kanıtlanmış olur.

### B3. Haltere/kanat mekanosensörlerinden kapalı döngü tutum stabilizasyonu
- Bedenden (MuJoCo) açısal hız → haltere campaniform afferentlerine Poisson/rate kodlama; kanat direksiyon MN'leri →
  rol/yunuslama/sapma torku. El yapımı haltere PD'si **kontrol kolu** olarak kalır.
- **Olası sonuç:** "REFLEX (el yapımı)" etiketli tutum kontrolünün ilk kez connectome'dan gelmesi. Gecikme/kazanç
  ayarı gerekebilir; ayar yalnız açık-döngü fizyoloji verisine (ör. haltere refleks gecikmesi ~5–10 ms, Beatus 2015
  düzeltme süresi ~30 ms) göre yapılmalı.

### B4. Kalkış ve iniş
- Kalkış: GF/DNp01 → TTM (bacak itme) + kanat açma; Uploading Lab "native GF/TTM jump" gösterdi.
- İniş: DNp07/DNp10 + bacak uzatma MN'leri; FlyWire'da DNp10 sol/sağ girdisi 4,1× asimetrik idi (analiz §1.4) → BANC'de
  simetri kapısıyla tekrar değerlendirilmeli.
- **Olası sonuç:** Kalkış tetiğinin beyne geçmesi yüksek olasılık; iniş kararı orta-düşük.

### B5. Eğitilebilir connectome (TRAINED etiketiyle)
- flyhard/fly-self-driving tarifi BANC'e uygulanır: topoloji sabit, kenar kazancı + nöron sızıntısı öğrenilir, rate
  modeli, durum taşınır, BC + DAgger, kontroller (presinaptik permütasyon, lineer, MLP), ≥3 tohum.
- Görev: hover + yalpa bozulması → optomotor yaw → engelden kaçınma → iniş.
- **Olası sonuçlar:** Görev başarısı yüksek olasılıkla (sürüş projeleri öyle gösterdi); "topoloji avantajı" görev
  bağımlı ve küçük olabilir (fly-self-driving'de ilk görevde rewired graf eşit/üstün). Bilimsel değer kontrollerin
  dürüst raporlanmasında.

### B6. Yürüme (yan proje)
- Pugliese ve ark. VNC CPG devresi + NeuroMechFly; Uploading Lab BANC ile nöral motor çıktıdan yürüme bildirdi.
- **Olası sonuç:** Platforma inişten sonra besine yürüme gibi davranışlar beyin/VNC'den gelebilir.

## 4. Senaryo tablosu (beklenen sonuçlar)

| senaryo | ne olur | olasılık (kanaat) |
|---|---|---|
| İyimser | B1 (1,2,3,4) geçer; haltere refleksi kapalı döngüde hover'ı stabilize eder; kalkış GF'den; iniş el yapımı; rota TRAINED okumayla | düşük–orta |
| Gerçekçi | B1-1, B1-3 geçer; B1-2 kısmen; refleks açık döngüde doğru işaret ama kapalı döngüde ayar ister; uçuş gücü (DNg02) sessiz kalır; TRAINED kollar görev başarır ama topoloji avantajı belirsiz | orta–yüksek |
| Kötümser | 888'de de yanal asimetri; MN9 eşleşmesi belirsiz; VNC yolları sessiz (dinlenme aktivitesi yok); yalnız yapısal bulgular raporlanır | orta |

Her senaryoda **raporlanabilir** sonuç vardır; Synaptera'nın negatif sonuç disiplini korunursa kötümser senaryo bile
yayınlanabilir bir "BANC'te neyin çalışmadığı ve neden" haritası verir.

## 5. Önerilen ilk adımlar (somut)

1. Dataverse 7WTH1N'den `banc_888_edgelist_simple_v3.feather` + `banc_888_meta.feather` + NT tahminleri; SHA-256 sabitle.
2. `scripts/analysis/connectome_structure.py`'yi (bu analizde yazıldı) BANC şemasına uyarlayıp aynı tabloları üret:
   L/R simetri, DNg02/DNp15/MN9-eşdeğeri girdileri, AL özdeğeri, sensör→MN hop mesafeleri.
3. B1-1 ve B1-3'ü Shiu-LIF ile koş (CPU, Brian2; BANC ~188k nöron → 1 s için tahminen ~20–40 s duvar süresi).
4. Kapı: B1-1 geçmezse BANC'te MN9 eşlemesini/NT işaretlerini incele, uçuşa geçme.

## Kaynaklar
- [Bates ve ark. 2026, *Nature* 656:957–970](https://www.nature.com/articles/s41586-026-10735-w); [BANC-project deposu](https://github.com/htem/BANC-project); Dataverse [10.7910/DVN/7WTH1N](https://doi.org/10.7910/DVN/7WTH1N)
- [Stürner ve ark. 2025, *Nature* 643:158–172](https://www.nature.com/articles/s41586-025-08925-z) (DN/AN çapraz-veri eşleme)
- [BioReservoir MODEL.md / DATA.md](https://github.com/igdigitallab/bioreservoir) (BANC 626 başarısızlığı, MN9 yokluğu, 888 notu)
- [The-Uploading-Lab/fly-behavior-experiments MODELS.md](https://github.com/The-Uploading-Lab/fly-behavior-experiments) (BANC 888 modeli)
- [Curt-Park/fly-cartpole](https://github.com/Curt-Park/fly-cartpole) (MaleCNS uçuş stabilizasyon devresi)
- [Pugliese ve ark. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/) (VNC CPG)
- [Cheong ve ark., eLife 96084](https://elifesciences.org/reviewed-preprints/96084) (MANC premotor devreleri); Namiki ve ark. (DNg02, uçuş motoru)
- [banc (PyPI)](https://pypi.org/project/banc/)
