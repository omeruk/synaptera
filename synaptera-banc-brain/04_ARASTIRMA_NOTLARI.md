# 04 — Araştırma notları: "The Driving Fly" ve benzeri connectome–beden çalışmaları nasıl yapıldı?

Tarih: 2026-10-12. Bu belge, kullanıcının işaret ettiği `thedrivingfly.com/media` ve `theuploadinglab.ai/fly`, `/fly/diary`
sayfalarındaki çalışmaların **nasıl yapıldığını** ve aynı dönemdeki benzer projeleri kaydeder.

## 0. Kaynaklara erişim notu (dürüstlük için)

- `thedrivingfly.com` ve `theuploadinglab.ai` bu çalışma ortamının ağ politikası tarafından engellendi (HTTP 403 / DNS);
  sayfalar **doğrudan açılamadı**. Bu yüzden:
  - The Driving Fly için projenin **kendi GitHub deposu** (`MarkUnthank/flyhard`: README, pilot raporu, CARLA video raporu,
    `src/flyhard/connectome.py`) okundu. Arama sonuçları sitenin ve basın sayfasının (`/press`) bu depoyu yaptığını
    (yazar: Mark Unthank, "Really Nice" bünyesinde bağımsız deney) gösteriyor.
  - The Uploading Lab için ekibin açık deposu `The-Uploading-Lab/fly-behavior-experiments` (README, `MODELS.md`,
    `THIRD_PARTY.md`) okundu. `/fly/diary` günlük girdileri **okunamadı**; buradaki Uploading Lab bilgileri bu depodan ve
    Synaptera `REPORT.md` "Related work" bölümündeki (2026-10-07'de açılmış) ledger/layers notlarından gelir.
- Okunan her depo README'si bu ortamda indirildi; aşağıdaki sayılar o belgelerin **kendi beyanlarıdır** (bağımsız
  doğrulanmadı). Hakemli makaleler ayrıca işaretlendi.
- Siteleri açmak isterseniz: ortam ayarlarında (oturum başlığındaki bulut ortamı menüsü → Edit → Network access)
  `thedrivingfly.com` ve `theuploadinglab.ai` alan adlarını "Allowed domains" listesine ekleyebilirsiniz.

---

## 1. The Driving Fly (flyhard) — Mark Unthank

**Ne:** MaleCNS (erkek *Drosophila* tam MSS: beyin + optik loblar + boyun + VNC) connectome'undan kurulan bir modelin,
simüle bir sineğin **bacağıyla fiziksel olarak direksiyon çevirip** CARLA sürüş simülatöründe bir arabayı (şimdilik stok
yeşil Mini Cooper; hedef "Flyat" = eski yeşil Fiat Panda) yönlendirmesi.

### 1.1 Nasıl yapıldı (yöntem zinciri)

```
istenen direksiyon açısı + ölçülen direksiyon açısı + 7 eklem açısı
  → SABİT (eğitilmeyen) rastgele eşleme → 6.365 "vnc_sensory" nöron
  → connectome rate modeli (165.122 nöron, 25.563.197 kenar; 4 graf güncellemesi / karar)
  → 708 "vnc_motor" nöron → SABİT eşleme → 7 ön bacak eklem hedefi
  → MuJoCo/NeuroMechFly eklem servoları → "nokta tutuş" kısıtı (ayak ↔ direksiyon) → pasif direksiyon
  → ölçülen direksiyon açısı → CARLA steering (25 Hz) → (gelecekte) kamera → yeni girdi
```

- **Connectome:** MaleCNS v1.0, `status == "Traced"` nöronlar ve aralarındaki tüm bağlantılar, ek eşik yok:
  165.122 nöron, 25.563.197 nöron-çifti kenarı, 124.025.046 toplam sinaps.
- **Nöron modeli (`connectome.py`, okundu):** işaretli skaler **rate** durumu;
  `s ← (1−λ)s + λ·tanh(W s + drive)`, `W = (sinaps sayısı / postsinaptik toplam girdi) × (0,05 + 0,90·σ(g_edge))`,
  `λ = 0,05 + 0,90·σ(g_leak)`. Yani **topoloji sabit**, öğrenilen şey **kenar başına bir kazanç + nöron başına bir sızıntı**
  (25.728.319 parametre). Pilotta nörotransmitter işaretleri **kullanılmıyor** (işaretsiz, girdi-normalize ağırlık).
- **Eğitim:** 40 hedef açı için ters kinematik + eklem servolarıyla 1.200 gösterim (öğretmen); ardından denetimli
  öğrenme (geri yayılım) ile 600 optimizer adımı, 186 s, tek A6000 GPU, ~3 GB bellek. PyTorch'un seyrek CSR geri
  yayılımı 101,57 GiB yoğun ara bellek istediği için **kenar başına türev parça parça (chunked)** hesaplanan özel bir
  `autograd.Function` yazılmış.
- **Sonuç (kendi beyanı):** 100 saklı hedef açıda eğitim öncesi 0/100, sonrası **100/100** (eşik 7,45°; en kötü 4,85°).
  Tutuş kısıtı kaldırılınca direksiyon yanıtı %99,98 kayboluyor (nedensellik müdahalesi).
- **CARLA'ya bağlama:** nöral karar 20 Hz, eklem komutu 200 Hz, fizik 20 kHz, CARLA 25 Hz; tek saat; 24 s'lik
  "talimatlı" sürüş (hız ve dönüş istekleri **senaryolu**). Sürüş görüntüsü, kokpit görüntüsü ve nöron aktivitesi aynı
  kayıttan; aktivite "spike değil, hesaplanmış rate durumu" olarak etiketli.
- **Dürüst sınırlar (kendi yazdıkları):** görsel sürüş yok, pedal + direksiyon birlikte yok, tek eğitim tohumu, karışık
  (shuffled) graf kontrolü yok; "sineğin zihnini yeniden kurma iddiası değildir".
- **Maliyet:** pilot oturumu $0,67 (Runpod A6000, ~$0,56/saat).

### 1.2 Bu çalışmadan türeyen "fly-self-driving" (suanmiao, Kylon ajanları)

flyhard tarifini görsel sürüşe genişletmiş:
- Aynı graf + aynı öğrenilen parametreler (kenar kazancı + sızıntı); **sabit rastgele** piksel eşlemesi
  (64×32 kamera → 4.114 optik lob duyusal nöronu) ve sabit rastgele motor okuma (708 VNC motor nöronu → direksiyon).
- **Kritik bulgu 1:** Nöral durumu kararlar arasında **sıfırlamamak** (state carried) ilk görevde 3/20 → 17/20.
- **Kritik bulgu 2:** Sadece davranış klonlama (BC) 12/20; **DAgger ×3** ile 20·19·19/20 (trafikli sokak, 3 bağımsız set).
- **Kontroller:** lineer harita 12/20, MLP-40 18/20, **rastgele yeniden kablolanmış graf (presinaptik indeks
  permütasyonu, giriş derecesi korunur) 16/20**; hız + yaya görevinde rewired 5/20 vs gerçek 18·19·16/20.
- Uyarılar: tek tohum; ilk düz yol görevinde rewired graf gerçek graf kadar iyi ya da daha iyi; fren öğrenilmedi.
- Maliyet: <$25 GPU, ~35 dk H100.

### 1.3 "flydrive" (ORI-Muchim) — iki yaklaşım yan yana

- **El yapımı görsel yol** (R1–R6 → L1/L2/L3 → Mi/Tm → T4/T5 Hassenstein–Reichardt → HS/VS → EPG halka çekici →
  PFL3 → DNa01/DNa02 benzeri → direksiyon/gaz), 83.182 parametre, **PPO** ile ağırlık öğrenimi.
- **Tüm MaleCNS connectome politika olarak:** 162.432 nöron, 24,4 M kenar; işaretler NT tahmininden (ACh +, GABA/Glu/His −);
  ışık 5.708 nörona (fotoreseptör + L1/L2/L3) giriyor; **1.311 DN'in hızları tek lineer katmanla** okunuyor; öğrenilen:
  nöron başına zaman sabiti/kazanç/eşik, hücre tipi başına sinaptik kazanç, giriş-çıkış eşlemeleri (674.129 parametre).
- Pratik dersler: ham sinaps sayıları ıraksar (ortalama giriş derecesi ~150) → **her nöronun toplam girdisini 1'e
  normalize** et; geri yayılım için transpoz CSR'ı önceden sakla; DN özelliklerini nöron başına **merkezle**
  (dondurulmuş beyinden lineer prob şerit konumunu R² 0,83 ile verir).
- Sonuç: dondurulmuş connectome + lineer DN okuma 0,74 M adımda kazasız şerit takibi (el yapımı 1,11 M);
  ama şehir görevinde (ışıklar, dönüşler) ridge okuma ile %54 bitiriş, kırmızı ışık geçme 1,25/epizod.
- Dönüş komutu **PFL3'e (merkez kompleksin hedef-yön nöronları)** enjekte edilince yanlış dönüş %70 → %4.
- Görsel tasarım dersi: fotoreseptör adaptasyonu + T4/T5 yalnız hareket algıladığı için **duran sahnede görsel girdi
  sıfırlanıyor**; çözüm L3 (sürekli, parlaklık kodlayan lamina hücresi) yolu.

### 1.4 "flybrain-drive" (mingdianliu) — eğitilmemiş, tarayıcıda

Seçilmiş alt graf (8.000 nöron), basit LIF, mühendislik algılama/planlama + nüfus oranı okuma; **sürüşü öğrenmemiş**,
kendi deyişiyle hangi davranışın nöral, hangisinin programlı olduğunu ayıran bir gösteri.

---

## 2. The Uploading Lab — BANC tabanlı "lo-fi whole-brain emulation"

Synaptera `REPORT.md`'nin 2026-10-07 notu: ledger sayfası 188.508 nöron, 13,6 M sinaps ile "lo-fi whole-brain emulation";
paylaşılan fizyolojik parametreler (kazanç, zaman sabiti) ayarlanıyor, **sinapslar asla eklenmiyor/çıkarılmıyor/tek tek
yeniden ağırlıklandırılmıyor**, ölçülmemiş değerler "aranıyor" ve tahmin olarak etiketleniyor.

Açık depo `fly-behavior-experiments/MODELS.md` (okundu) modeli şöyle tarif ediyor:
- **BANC v888** nöron kimlikleri ve bağlantıları: **188.508 nöron, 13.620.865 yönlü kenar, 42.316.236 tutulan sinaps**.
- **Nöron modeli:** iletkenlik tabanlı integrate-and-fire + **adaptasyon** (`dw/dt = (a(V−V_rest) − w)/τ_w`, spike'ta `+b`),
  sinaptik gecikmeler, seçilmiş **graded-release** (spike'sız) hücreler ve **açık elektriksel bağlantılar (gap junction)**.
  Bu parametreler ve bağlantı-gücü eşlemeleri "model varsayımı" olarak işaretli.
- **Beden:** tek nöral ağ **iki bedene** bağlı: iç "yürüme bedeni" duyusal geri bildirimi verir; nöral motor çıktısı
  eklem-hedefi aktarımıyla görüntülenen kanatlı bedeni sürer (FlyGym/FlyBody geometrisi, MuJoCo).
- **Yerli (native) davranışlar:** yürüme nöral motor çıktısından; **dev lif (giant fibre, DNp01) / TTM olayları
  sıçramayı başlatıyor**. Kanat gücü, kanat çırpma deseni (FlySuite `wing_pattern_fmech.npy`), tutum desteği, bacak
  katlama ve iniş **programlı** → "kalkış tamamen nöral bir uçuş kontrolcüsü demek değildir".
- **Deneyler (hackathon, TimeFlies ekibi):** 25 ıslak-laboratuvar kaydıyla yürüme/kaçış karşılaştırması; "ibuprofen"
  (tüm nöronlarda adaptasyon parametreleri), "kalori kısıtlaması" (LC4/LPLC2 → DNp01 girdisi ×0,5) ve "yaşlanma"
  (tüm işaretli ağırlıklar `2^(−d/45)` ile ölçeklenir; 45 günlük yarı ömür **varsayım**).
- **Dürüst sınırlar:** tüm vakalar geliştirme tohumu 0; seçilmiş vakalar bağımsız hayvan değil; tedavi kinetiği yok.

---

## 3. Diğer önemli referans projeler (kısa)

| proje | connectome | nasıl | ne gösterdi / sınır |
|---|---|---|---|
| **Eon Systems** "Virtual Embodied Fly" (Mart 2026) | FlyWire merkezi beyin, LIF (Shiu) | birkaç DN yüksek seviye komut ("dön, yürü, temizlen") olarak okunur → önceden eğitilmiş NeuroMechFly denetleyicileri | Beyin→beden eşlemesi elle seçilmiş; VNC yok (kendi beyanı). Bir eleştiri yazısı (Preserving Hope Substack): VNC'deki ~15.000 nöron simüle edilmediği için "yükleme" iddiası abartılı |
| **Fly.exe** (Ibtisam-Mohammad) | MaleCNS 165.122 nöron | GeNN/CUDA, tek GPU'da 12 sinek; retinotopik lamina kodlayıcı; **2 DN nüfus oranı** okunur; yürüme yayınlanmış desen üreteci | Her parametreye köken sınıfı (M ölçülmüş, P popülasyon önceli, F uydurulmuş, E mühendislik, I kurtarılamaz); "beden bir aralık geride" nedensel kuyruk |
| **fly-cartpole** (Curt-Park) | MaleCNS **uçuş stabilizasyon devresi** (5.459 nöron: haltere, ocelli, HS → kanat direksiyon MN b1/b2) | lineer rate birimleri, topoloji sabit, yalnız 5 duyu kazancı ayarlanır | Ayarsız devre 275,6 adım; ayarlı 499,9; karıştırılmış kablolama 165,9. **Uçuş tutum refleksinin connectome'dan elde edilebileceğine dair güçlü ipucu** |
| **FlyGM** (Jin ve ark., arXiv 2602.17997) | FlyWire 139.246 nöron (19.262 afferent, 1.488 efferent) | connectome'u yönlü mesaj-geçiren graf olarak kullanır; flybody'yi taklit + RL ile kontrol | Rewired ve Erdős–Rényi graf ile MLP'den daha iyi örnek verimliliği (kendi beyanı) |
| **flybody** (Vaxenburg ve ark., *Nature* 2025) | — (beden) | MuJoCo tam beden, akışkan + yapışma modelleri; uçuşta MLP + sabit **kanat çırpma desen üreteci (WPG)**; 216 gerçek uçuş yörüngesini taklit | Uçuş için fiziksel olarak en zengin açık beden |
| **Pugliese ve ark. 2025** (bioRxiv) | MANC/BANC **VNC** | LIF simülasyon | Yürüme için küçük bir ritim üreten devre (CPG) |
| **BioReservoir** (IG Digital Lab) | MaleCNS + BANC | Shiu-LIF, rezervuar | **BANC (Dataverse snapshot 626) yanal-taraf doğrulamasında başarısız:** 114k nöron, ~3× düşük ortalama derece, sağda %45 daha fazla proofread nöron → her denemede "hep sağ" yanıt; MaleCNS geçti. 888 sürümü henüz denenmemiş |
| **flybrain-drive**, **Doodle Fly**, **Fly-NAF**, **FLYT3** vb. | FlyWire/MaleCNS | çoğunlukla el yapımı okuma + oyun | Eğlence/gösteri; çoğu kendi kontrolünü raporluyor |

---

## 4. Ortak desen: bu çalışmalar "connectome ile sürme/uçma"yı nasıl başardı?

1. **Topoloji sabit, dinamik parametreler öğrenilir.** Hiçbiri ham connectome'u "olduğu gibi" çalıştırıp karmaşık
   görevi çözmedi. Başarılı olanlar (flyhard, fly-self-driving, FlyGM, flydrive) ya kenar kazançlarını + sızıntıları
   (rate modeli, geri yayılım) ya da yalnız okuma katmanını (ridge/lineer) eğitti.
2. **Rate modeli + girdi normalizasyonu.** Ham sinaps sayılarıyla ağ ıraksıyor; her nöronun toplam girdisini 1'e
   normalize etmek ve doyuran bir aktivasyon (tanh/sigmoid) kullanmak kararlılığı sağlıyor. Spike'lı Shiu-LIF modeli
   ise sabit parametrelerle **dinlenme aktivitesi olmadan** çalışıyor ve geniş bölgeleri sessiz bırakıyor
   (Synaptera'da 1.299 DN'in 986'sı eğitim uçuşlarında sabit/sessiz).
3. **Durum taşınması (state carry-over)** kritik; karar aralıklarında sıfırlama performansı çökertiyor.
4. **Taklit + DAgger** saf taklitten çok daha iyi (12/20 → 20/20). Synaptera'nın eğitim merdiveni tam bu noktada
   (DAgger turlarından önce) durduruldu.
5. **Sabit/rastgele arayüzler**: "Mühendislik ürünü hiçbir parça sinyali tek başına taşıyamaz" ilkesi; okuma ve
   kodlama katmanları ya sabit rastgele ya da çok küçük.
6. **Kontroller:** presinaptik permütasyonlu (rewired) graf, lineer/MLP, çoklu tohum. Bazı görevlerde rewired graf
   gerçeği kadar iyi — topoloji avantajı **görev bağımlı**.
7. **VNC'nin önemi:** Gerçek motor çıkışları (bacak/kanat MN'leri) VNC'de. MaleCNS/BANC ile VNC dahil modeller DN→MN
   yolunu el yapımı köprü olmadan kurabiliyor (flyhard: vnc_motor; Uploading Lab: yürüme; fly-cartpole: b1/b2).
8. **Uçuşta durum:** Hiçbir açık projede uçuş tamamen nöral değil. Uploading Lab'de kanat gücü/deseni programlı;
   flybody'de MLP + WPG; fly-cartpole yalnız refleksi gösterdi.

## 5. Synaptera için çıkarımlar (kısa)

- Synaptera'nın metodolojik disiplini (ön-kayıt, kaynak etiketleri, negatif sonuçların raporlanması, doğrulama betiği)
  bu projelerin çoğundan güçlü — korunmalı.
- Eksik olan: (a) VNC (BANC/MaleCNS ile çözülebilir), (b) eğitilebilir dinamik parametreler veya en azından dinlenme
  aktivitesi, (c) DAgger, (d) L/R simetri kontrolleri (bkz. `02_MODEL_FIZIK_TEST_ANALIZI.md` §1.4), (e) bilgi uyumu
  (öğretmen sinyali beyne verilmeyen bir duyudan geliyordu).
- Ayrıntılı plan: `05_MIMARI_PLAN.md`.

## Kaynaklar

Okunan birincil depolar (README ve belgeler bu ortamda indirildi):
- [MarkUnthank/flyhard](https://github.com/MarkUnthank/flyhard) — README, `docs/pilot-2026-09-09.md`, `docs/carla-video-2026-09-09.md`, `src/flyhard/connectome.py`
- [suanmiao/fly-self-driving](https://github.com/suanmiao/fly-self-driving) — README, `docs/method.md`, `docs/results.md`
- [ORI-Muchim/flydrive](https://github.com/ORI-Muchim/flydrive) — README
- [The-Uploading-Lab/fly-behavior-experiments](https://github.com/The-Uploading-Lab/fly-behavior-experiments) — README, `MODELS.md`, `THIRD_PARTY.md`
- [Ibtisam-Mohammad/Fly.exe](https://github.com/Ibtisam-Mohammad/Fly.exe) — README
- [Curt-Park/fly-cartpole](https://github.com/Curt-Park/fly-cartpole) — README
- [igdigitallab/bioreservoir](https://github.com/igdigitallab/bioreservoir) — README, `docs/MODEL.md`, `docs/DATA.md`
- [mingdianliu/flybrain-drive](https://github.com/mingdianliu/flybrain-drive), [eonsystemspbc/fly-brain](https://github.com/eonsystemspbc/fly-brain), [cobanov/awesome-fly](https://github.com/cobanov/awesome-fly) — README
- [htem/BANC-project](https://github.com/htem/BANC-project) — README

Arama sonuçlarından (sayfaların kendisi bu ortamda açılamadı):
- [The Driving Fly](https://thedrivingfly.com/), [Press kit](https://thedrivingfly.com/press)
- [The Uploading Lab](https://theuploadinglab.ai/)
- [Eon Systems — How the Eon Team Produced a Virtual Embodied Fly](https://eon.systems/updates/embodied-brain-emulation)
- [No, we haven't uploaded a fly yet (Preserving Hope)](https://preservinghope.substack.com/p/no-we-havent-uploaded-a-fly-yet)
- [Jin ve ark., arXiv:2602.17997 (FlyGM)](https://arxiv.org/abs/2602.17997)
- [Vaxenburg ve ark. 2025, *Nature* — Whole-body physics simulation of fruit fly locomotion](https://www.nature.com/articles/s41586-025-09029-4)
- [Bates ve ark. 2026, *Nature* — Distributed control circuits across a brain-and-cord connectome](https://www.nature.com/articles/s41586-026-10735-w)
- [Stürner ve ark. 2025, *Nature* — Comparative connectomics of Drosophila descending and ascending neurons](https://www.nature.com/articles/s41586-025-08925-z)
- [Pugliese ve ark. 2025 — Connectome simulations identify a central pattern generator circuit for fly walking](https://pmc.ncbi.nlm.nih.gov/articles/PMC13142387/)
- [Cheong ve ark. — MANC premotor devreleri (eLife reviewed preprint 96084)](https://elifesciences.org/reviewed-preprints/96084)
