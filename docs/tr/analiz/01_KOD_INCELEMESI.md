# 01 — Kod incelemesi: hatalar, eksiklikler ve yüksek önemli bulgular

Tarih: 2026-10-12. Kapsam: `fly_flight_brain_body_simulation.py`, `flight/` (19 modül), `simulation_data/odor_field_3d.py`,
`scripts/` (veri, analiz, rapor, şekil betikleri), `tests/` (19 test dosyası), çalıştırma betikleri (`run_*.sh`),
Shiu ve ark. `brain_model/model.py` (indirildi, SHA-256 doğrulandı).

Yöntem: tüm çekirdek kod satır satır okundu; `ruff` (pyflakes + bugbear) statik analizi; test paketi Python 3.10 +
pinlenmiş paket sürümleriyle (x86_64, 4 çekirdek) çalıştırıldı; veri türetme betikleri yeniden koşturulup SHA-256'lar
geliştirici kopyasıyla karşılaştırıldı; FlyWire v783 üzerinde bağımsız yapısal analiz ve Shiu-LIF açık döngü
simülasyonu yapıldı (`02_MODEL_FIZIK_TEST_ANALIZI.md`).

**Genel değerlendirme:** Kod tabanı bilimsel yazılım için alışılmadık derecede disiplinli: her motor terimi ayrı
kaydediliyor ve etiketleniyor, sabitlerin kaynağı yorumlarda, HDF5 şeması belgelenmiş, rapor sayıları betikle
doğrulanıyor, veri hash'lerle sabitlenmiş. Aşağıdaki bulguların çoğu **tasarım/metodoloji** düzeyinde; raporlanmış
sonuçları geçersiz kılan bir kod hatası bulunmadı. Önem dereceleri: **Y** (yüksek), **O** (orta), **D** (düşük).

---

## A. Yüksek önemli bulgular (Y)

### Y1 — Beyin–beden ortak simülasyonunda adım içi nedensellik ihlali (lockstep)
`fly_flight_brain_body_simulation.py:451` → `:526`: her karar adımında önce `brain.step()` beyni [t, t+25 ms]
aralığında koşturuyor, sonra bu aralıkta üretilen spike'lardan türeyen komut **aynı** [t, t+25 ms] fizik aralığına
uygulanıyor. Beden, fiziksel zamanda henüz oluşmamış (25 ms'ye kadar "gelecekteki") spike'larla sürülüyor; buna karşın
görsel girdi bir önceki adımda render edilmiş kareler. Sonuç: duyu→motor gecikmesi 0–25 ms arasında ve adım içinde
akausal; gerçek sinekte görsel-motor gecikme onlarca milisaniye mertebesindedir ve sıfır olamaz.
- **Etki:** n1/n2'de beyin direksiyon terimi 0 olduğu için raporlanan uçuşlar etkilenmez; ama DNp15 kapalı döngü
  doğrulaması (b1–b3) ve gelecekteki tüm beyin-kontrollü uçuşlarda döngü kazancı/kararlılığı yanlış tahmin edilir.
- **Öneri:** komutu bir adım geciktiren kuyruk (adım k'nin beyin çıktısı adım k+1'de uygulanır; Fly.exe'nin "beden bir
  aralık geride" tasarımı) veya daha ince eşleme (ör. 5 ms beyin / 5 ms beden alt adımları). Gecikme açık bir parametre
  olarak kaydedilmeli.

### Y2 — Okuma seçiminde sol/sağ yeniden yapılandırma asimetrisi kontrol edilmiyor
Bu oturumdaki bağımsız analiz (`scripts/analysis/dn_lr_asymmetry.py`): FlyWire v783'te tek-nöron-çifti olan 383 DN
tipinin girdi sinapslarında medyan sağ/sol oranı 1,17×; %24,8'inde fark >1,41×, %11,5'inde >2×. **DNp15 sağ/sol =
1,66× (383 içinde en asimetrik 65.)**, uyarıcı girdi 1.126 / 636 (1,77×). **DNp10 = 0,24× (8. en asimetrik).**
Bu, raporlanan iki negatif bulguyu (DNp15'in "sağ-baskın taban hızı", perch L 0 / R 52 Hz; DNp10'un "tek taraflı"
olması) **yapısal olarak** açıklıyor. Ön-kayıtlı birincil okuma DNa02 ise simetrik (1,07×).
- **Öneri:** Her lateral okuma için önceden kayda alınmış bir **simetri kapısı** (ör. |log2(R/L)| < 0,5 hem toplam
  hem uyarıcı girdi için) ve/veya ayna-simetrikleştirilmiş connectome kontrol kolu.

### Y3 — Eğitim merdiveninde bilgi uyumsuzluğu
`flight/readout_model.py` + `--readout-model`: öğretmenin dönüş komutu (`turn_hand`) simülatörün **koku alanından**
geliyor; T1 kollarında beynin koku girdisi kapalı (`--no-olfaction`), yalnız görsel girdi var. Okuma, beyne hiç
verilmeyen bir bilgiyi DN aktivitesinden çıkarmaya zorlanıyor (raporun kendi yorumu da bu yönde; R² dönüş < 0 tüm
kollarda). Ayrıca 1.299 DN özelliğinin **986'sı** eğitim uçuşlarında sabit (sessiz).
- **Öneri:** öğretmen sinyali ile beynin duyu girdisi aynı bilgiyi taşımalı (ör. görsel hedefli görev ya da çalışan
  bir koku girdisi); DAgger turları; λ ızgarası sınırda seçildi (1000, `readout_model.py:20`) → ızgara genişletilmeli.

### Y4 — Görsel örnekleme hızı uçuş hızına göre yetersiz (hareket örtüşmesi / aliasing)
`flight/visual_input.py`: karar başına 2 render (80 Hz, `VIS_SUBFRAMES = 2`, FlyVis dt 12,5 ms). 300 mm/s seyirde
kuleye 4,4 mm mesafede açısal hız ~3.900°/s → kare başına ~49° kayma; 10 mm'de ~21°/kare; 50 mm'de ~4,3°/kare.
Ommatidyum açıklığı ~5° olduğundan engel yakınında T4/T5 hareket sinyali örtüşmeli/güvenilmez.
- **Etki:** görsel engelden kaçınma veya optik akış tabanlı iniş için beyin girdisi fiziksel olarak bozuk olabilir;
  açık döngü taramalarında (yavaş uyaranlar) sorun yok.
- **Öneri:** yakın-engel fazlarında alt kare sayısını artırma (ör. 8–10/adım), ya da FlyVis'i daha küçük dt ile koşma;
  render maliyeti ölçülmeli.

### Y5 — Kanat strok genliği fiziksel sınırsız
`flight/quasi_steady.py:68` (`wing_lift ∝ Φ²`), `controller.py:64`, `hybrid.py:180`: genlik üst sınırı yok.
`LIFT_FRAC_RANGE` üst ucu 1,8 ve 20° eğimde kolektif genlik 193,8°, dönüş farkıyla 206,3°'ye çıkabiliyor
(geometrik üst sınır ~180°; Drosophila manevralarda bu sınıra yaklaşır). Kuasi-statik `Φ²` ölçeklemesi bu bölgede ekstrapolasyon.
- **Öneri:** Φ ≤ ~180° (veya literatürle seçilecek daha düşük bir değer) kırpma + kırpma olaylarının kaydı; doyma durumunda kalan itkinin frekansla karşılanması.

---

## B. Orta önemli bulgular (O)

| kod | bulgu | yer | öneri |
|---|---|---|---|
| O1 | **Sessizce üzerine yazma:** `--version` açıkça verilip aynı bayraklarla tekrar koşulursa `DisplayWriter` (`"w"`) ve `write_h5` (`mode="w"`) mevcut sonuç HDF5'ini uyarısız siler | `flight/vision_boundary.py:470`, `flight/recorder.py:280` | var olan dosyada dur (veya `--overwrite` bayrağı) |
| O2 | **Codex verisine zorunlu bağımlılık:** `build_groups` her durumda `column_assignment.csv.gz` (Codex, giriş gerektirir) okur; görme kullanmayan deneyler bile beyni kuramaz | `flight/groups.py:151` | T4/T5 gruplarını yalnız görme açıkken kur |
| O3 | **Karışık (shuffled) null kontrolü aktivite-eşli değil:** posta-sinaptik permütasyon aynı (pre,post) çiftlerini çoğaltabilir; karışık beyin aynı girdilerde 2,5× DN spike'ı üretiyor (REPORT §3.9b) → "bağlantının katkısı" ile "aktivite düzeyi" karışıyor | `flight/brain.py:203` | aktivite-eşli normalizasyon, hücre sınıfı/nöropil içi karıştırma, ikinci null (Erdős–Rényi aynı derece) |
| O4 | **Poisson girdi yolu modelden sapıyor:** Synaptera `PoissonGroup → Synapses(delay=1,8 ms)` kullanıyor; Shiu `PoissonInput` gecikmesiz. Ayrıca 68,75 mV'luk tekme (eşik farkı 7 mV) her girdi spike'ını zorunlu çıkış spike'ına çeviriyor; refrakter kapalı → 34.121 sınır nöronu saf spike üreteci olur, kendi tekrarlayan girdileri anlamsızlaşır | `flight/brain.py:315` | "değiştirilmemiş model" ifadesine dipnot; graded hücreler için akım enjeksiyonu varyantı |
| O5 | **Tohumlar bağımsız değil:** `--seed` yalnız Brian2'yi tohumlar; fizik deterministik → direksiyon 0 iken rota bit-bit aynı (rapor bunu doğru belirtiyor) | ana betik | fiziksel gürültü (rüzgâr, sensör gürültüsü) ile tohumlanan bir varyant |
| O6 | **Özel (private) FlyGym API'si:** `_update_vision`, `_last_vision_update_time`, `_curr_visual_input`, `_floor_contacts`; `sim.step()` atlanıp `physics.step()` doğrudan çağrılıyor | `flight/body.py:145-150, 387, 433-435` | sürüm sabit kalmalı; FlyGym yükseltmesinde regresyon testi |
| O7 | **Tekrarlanabilirlik hash'leri platforma duyarlı:** bu oturumda `data/t45_transduction.json` yeniden üretildi, SHA-256 farklı çıktı (x86_64 + torch 2.14.1 vs aarch64 + 2.14.0). JSON içindeki kayan nokta farkları bit-düzeyi karşılaştırmayı bozuyor | `scripts/fetch_data.py` (EXPECTED) | sayısal tolerans karşılaştırması (ör. rtol 1e-6) ekle |
| O8 | **Yaw doğrulama tabanı:** DNp15 normalizasyonu taraf başına referans çıkarıp ortak ölçeğe böler; referans tek uyarıcıdan (sym_prog) — Y2 asimetrisi nedeniyle statik sahnede bile büyük `s_hat` | `flight/vnc_bridge.py` | Y2'deki kapı |
| O9 | **Kuasi-statik model ayrıntıları:** kaldırma gövde z'si boyunca (strok düzlemi açısı yok); karşı-kuvvet izotropik; dönüş komutu toplam kaldırmayı `d²` kadar artırıyor (~%0,8); rol–yaw eşleşmesi sabit | `flight/quasi_steady.py` | flybody kanat modeli veya strok düzlemi + anizotrop sönüm |
| O10 | **Ridge ızgarası sınırda:** tüm komut/kollarda λ = 1000 (ızgara maksimumu) seçildi; 1.412 örnek / 1.299 özellik | `flight/readout_model.py:20` | ızgarayı genişlet, sessiz özellikleri baştan ele |

---

## C. Düşük önemli bulgular (D)

- **D1** `FlyVisEyes.step` / `BoundaryEyes.step`: loom terimi alt karelerin ortalaması yerine **son karenin** aktivitesinden
  (`visual_input.py:257`, `vision_boundary.py:446`); boş `frames` listesinde sıfıra bölme/tanımsız değişken.
- **D2** `Bridge.update`: ablasyon açıkken `set_baseline` çağrılmadan kullanılırsa `None` indeksleme hatası
  (`vnc_bridge.py:90`); ana döngüde sıralama doğru, betiklerde risk.
- **D3** Ana betiğin sonunda `del brain, body, eyes, ...` (`:759`) kapanış (closure) değişkenlerini siliyor; statik analiz
  9 adet "tanımsız isim" (F821) raporluyor. Çalışma anında sorun yok ama kırılgan.
- **D4** Sabit kodlanmış yollar: `PATH_CODEX_TYPES = ~/Downloads/...` (`vision_boundary.py:52`), çalıştırma
  betiklerinde `PY=$HOME/miniforge3/envs/neurofly/bin/python` (ortam değişkeniyle aşılabiliyor).
- **D5** `tests/conftest.py:23`: anlık görüntüde bulunmayan 25 yürüme betiği `collect_ignore` listesinde (zararsız, bayat).
- **D6** `FlightBrain(dev_subnet=True, shuffle_seed=...)`: karışık kontrol DEV alt ağında sessizce yok sayılıyor.
- **D7** Çökme durumunda `/flyvis`'i içeren ama `meta`'sı olmayan yarım HDF5 dosyası sonuç adıyla kalabilir.
- **D8** `ruff` (F + B kuralları): 117 bulgu; çoğu kullanılmayan import/değişken ve `zip(strict=)` stili.
  `B023` (döngü değişkeni kapanışı) uyarılarının hepsi incelendi: lambdalar aynı iterasyonda çağrılıyor → **gerçek hata değil**.
- **D9** `SpikeMonitor` tüm koşu boyunca bütün spike'ları bellekte tutuyor (7,5 s'de ~3,5 GB); daha uzun uçuşlar için
  akışlı (streaming) kayıt gerekir.

---

## D. Eksiklikler (özellik/kapsam)

1. **VNC yok:** DN → kanat yolu el yapımı köprü; yükselen nöronlar (1.736) hiç sürülmüyor (REPORT §5).
2. **Dinlenme aktivitesi yok:** girdisiz ağ sessiz; DN'lerin çoğu sessiz kalıyor (986/1.299 sabit özellik).
3. **Nöron modeli:** tekdüze LIF; gap junction, adaptasyon, graded (spike'sız) nöron, nöromodülasyon yok.
4. **Koku devresi kilitleniyor** (yapısal neden: `02_MODEL_FIZIK_TEST_ANALIZI.md` §1.6).
5. **Hortum eklemi yok**; MN9 kararı yalnız görsel işaretçi.
6. **Seyir rotası, irtifa, iniş, refleksler el yapımı**; beyin yalnız beslenme kararını veriyor.
7. **Harici ön-kayıt yok** (OSF vb.); commit zaman damgaları bağımsız kanıt değil (repo bunu açıkça yazıyor).
8. **Test kapsamı:** tam-beyin testleri `slow` işaretli ve Codex verisi olmadan çalışmıyor; açık anlık görüntüde
   bağımsız kullanıcı yalnız saf-fonksiyon ve fizik testlerini koşabiliyor.
9. **Veri paketi ve videolar henüz yayımlanmamış** (DOI "eklenecek"); `verify_report_final.py` paket olmadan çalışmıyor.

---

## E. Bu oturumda yapılan doğrulamalar

| kontrol | sonuç |
|---|---|
| Shiu model dosyaları + FlyWire ek açıklamaları (5 dosya) | SHA-256 **birebir** (fetch_data.py sabitleriyle) |
| Türetilen `descending_neurons.csv`, `sugar_grn_783.csv`, `leg_sugar_grn_783.csv`, `orn_spontaneous_783.csv` | 4/4 **birebir** (geliştirici kopyasıyla) |
| `t45_transduction.json` (FlyVis ağırlıkları indirildi) | üretildi; SHA-256 **farklı** (platform/torch farkı; bkz. O7) |
| Codex gerektiren 8 dosya | giriş gerektirdiği için üretilemedi |
| `pytest tests/` | bkz. `02_MODEL_FIZIK_TEST_ANALIZI.md` §5 |
| Statik analiz (ruff F,B) | 117 bulgu; gerçek hata değil (D8) |
| Bağımsız Shiu-LIF açık döngü (GRN → MN9) | bkz. `02_MODEL_FIZIK_TEST_ANALIZI.md` §5 |

## F. Öncelikli düzeltme listesi (mevcut repo için)

1. (Y1) Komut kuyruğu ile nedensel eşleme + gecikme parametresi.
2. (Y2) L/R simetri raporu ve okuma kapısı (`scripts/analysis/dn_lr_asymmetry.py` temel alınabilir).
3. (O1) Sonuç dosyasının üzerine yazmayı engelle.
4. (O2) T4/T5 sütun dosyasını yalnız görme açıkken iste.
5. (Y5) Strok genliği kırpma + kayıt.
6. (O7) Hash karşılaştırmasına sayısal tolerans.
7. (Y4) Yakın engel fazında görsel alt kare sayısı.
8. (D1–D3) küçük temizlikler.
