> **Lab notebook, in Turkish.** Working record of this project, kept as written during the work (moved here from the repository root for the public snapshot). The English consolidated report is [REPORT.md](../../REPORT.md); the English summary is the [README](../../README.md).

# NeuroFly uçuş — "dürüst hibrit final" raporu (final-v1-hibrit)

FlyWire v783 konnektomu (138.639 nöron, Brian2 LIF, tam beyin, DEV değil) + NeuroMechFly/FlyGym MuJoCo gövdesi, kapalı döngü,
25 ms karar adımı. Üç koşu: seed 3, 300 adım (7.5 s), `--no-olfaction`. Ön kayıt: `SPEC_BRAIN_CONTROL.md`
("Dürüst hibrit final"). Bu rapordaki her sayı `scripts/verify_report_final.py` ile HDF5'ten yeniden hesaplanıp
kontrol edilir.

| koşu | ayar | HDF5 |
|---|---|---|
| final_a | `--hybrid` | `simulations/flight_v11_hybrid_noOlf_final_a_data.h5` |
| final_b | `--hybrid --ablate-dn DNp15` (DNp15 okuması perch tabanına sabit) | `simulations/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b_data.h5` |
| final_c | yalnız beyin (HAND navigasyon yok; v10 brainonly160 ayarları) | `simulations/flight_v13_ablOdor_noOlf_final_c_data.h5` |

## Özet

- **final_a (hibrit): ön-kayıtlı ölçüte göre BAŞARISIZ.** S1 ✗, S2 ✓.
  - Platforma iniş var (touchdown 2.87 s) ve beslenme var (MN9 ilk kez > 10 Hz: 2.90 s; 4.62 s beslenme).
  - Ancak adım 52'de (t ≈ 1.3 s) kule 2'nin üstüne adım içinde 6.3 µm dokundu. Adım sonu temas bayrağı 0, fakat ön kayıt adım-içi dokunuşu da temas sayıyor.
- **final_b (DNp15 ablasyonu): S1 ✓, S2 ✓.**
  - Beyin dönüş terimi sabit +0.102 (perch tabanı). Bu koşu, beynin dönüş terimi sabitken ön-kayıtlı ölçütü geçti.
  - Ön kayıt gereği bundan "beyin gereksiz" ya da "beyin zararlı" sonucu çıkarılmaz: tek koşu, tek seed. Kule dokunuşu 6.3 µm'lik bir sınır olayı.
- **final_c (yalnız beyin): başarısız.** İniş yok, besine en yakın 318.7 mm. Kulelere adım içinde 18 adımda dokundu; 3 adımda adım sonu kule teması var.
- final_a ile final_b'nin besine uzaklık eğrileri neredeyse aynı (`plots/flight/*/13_distance_to_food.png`). Rota fiilen HAND katmanından geliyor; DNp15 terimi rotayı belirgin değiştirmiyor.

## Ne beyinden (BRAIN), ne el yapımından (HAND)?

| davranış bileşeni | kaynak (hibrit, final_a/b) |
|---|---|
| navigasyon (koku gradyanına dönüş) | **HAND**: el yapımı koku haritası `turn_hand`; koku alanını doğrudan okuyan el yapımı sensör. Beynin koku girdisi KAPALI |
| irtifa, kolektif (itki) | **HAND**: tırmanma tabanı, yaklaşma irtifa hedefi (platform + 8 mm), alçalma 30 mm/s. DNg02 sessiz (0 spike), VNC uçuş programının irtifa hedefi yok |
| ileri hız, gövde eğimi | **HAND**: sabit seyir eğimi 12°; yaklaşmada dünya çerçevesinde konum kontrolcüsü |
| kalkış, yaklaşma, iniş, bacak açma | **HAND**: zamanlayıcı, yaklaşma yarıçapı, dikey iniş |
| yaw (dönüş) | toplam = BRAIN + HAND + FLYVIS (±2.5 kırpma) |
| — BRAIN | DNp15 L/R farkı → `turn_brain` (VNC köprüsü; okuma **post-hoc** seçildi) |
| — FLYVIS | FlyVis ağının T5 L/R looming terimi (FlyWire değil; yürüyüş sabitleri) |
| — REFLEX | haltere PD, her fizik alt adımında; `turn_reflex` olarak kaydedilir, komuta **eklenmez** |
| beslenme kararı | **BRAIN**: MN9 okuması > 10 Hz (temas + landed) |
| görsel girdi | FlyGym gözleri → FlyVis → FlyWire T4/T5 Poisson sürüşü |

final_c'de HAND navigasyon yok. Dönüş yalnız beyin (DNp15), ancak el yapımı kalanlar var: haltere refleksi, iniş
tetiği, seyir eğimi, koku→kolektif haritası (koku ablasyonlu), dikey hız sönümü, ventral refleks, kalkış artışı.

## Ön-kayıtlı ölçütler ve karşılaştırma

- S1: touchdown'a kadar kule teması yok. Hem adım sonu bayrağı hem adım-içi penetrasyon 0 olmalı.
- S2: touchdown'dan sonra en az bir adımda `is_feeding` = 1.
- Başarı = S1 ∧ S2.

| ölçü | final_a | final_b | final_c |
|---|---|---|---|
| touchdown | 2.87 s (adım 114) | 3.07 s (adım 122) | yok |
| temas hızı | 6.3 mm/s | 5.8 mm/s | — |
| kule teması | 0 | 0 | 3 |
| adım-içi kule | 1 (adım 52) | 0 | 18 (ilki adım 38) |
| en büyük penetrasyon | 6.3 µm | 0.0 µm | 43.4 µm |
| S1 | ✗ | ✓ | ✗ |
| S2 | ✓ | ✓ | ✗ |
| MN9 ilk | 2.90 s | 3.07 s | — |
| beslenme adımı | 185 (4.62 s) | 178 (4.45 s) | 0 |
| beslenmede ort. MN9 | 57.0 Hz | 55.7 Hz | — |
| besine en yakın | 2.0 mm | 1.9 mm | 318.7 mm |
| son uzaklık | 2.0 mm | 1.9 mm | 330.2 mm |
| kanatlar açık | 114 adım | 122 adım | 300 adım |
| pay BRAIN | 0.43 | 0.43 | 0.60 |
| pay HAND | 0.28 | 0.31 | 0.00 |
| pay REFLEX | 0.26 | 0.20 | 0.40 |
| pay FLYVIS | 0.03 | 0.06 | 0.00 |
| oran BRAIN/toplam | 0.97 | 1.22 | 1.00 |
| tepe RSS | 3.49 GB | 3.49 GB | 3.49 GB |

Tablo notları:
- "kule teması": adım sonu `tower_contact` bayrağının açık olduğu adım sayısı, tüm koşu boyunca.
- "adım-içi kule": touchdown'dan önce (final_c'de tüm koşuda) `tower_penetration` > 0 olan adım sayısı.
- "pay …": kanatların açık olduğu adımlarda dört terimin Σ|·| payı (ön-kayıtlı ikincil ölçü).
- "oran BRAIN/toplam": ön-kayıtlı birincil ölçü Σ|BRAIN| / Σ|toplam|.
  - Terimler kısmen birbirini götürdüğü için bu oran **pay değildir** ve 1'i geçebilir (final_b: 1.22).
  - final_a'daki 0.97 "dönüşün %97'si beyinden" anlamına gelmez.
- final_b'de BRAIN terimi 300 adımın hepsinde aynı sabit değer (+0.102, perch tabanı). Oradaki "pay BRAIN" sabit bir sapmanın payıdır.
- Kolektif, irtifa, gövde eğimi ve iniş için beyin payı tanım gereği 0.

## Beynin katkısı — dürüst okuma

- **Beslenme kararı beyinden geliyor.** Platform temasıyla şeker GRN sürüşü başlıyor. MN9 okuması final_a'da touchdown'dan 1 adım (25 ms) sonra eşiği geçiyor ve beslenme boyunca ortalama 57.0 Hz. Temassız uçuşta MN9 0.
  - Şeker GRN'lerine temas girdisi el yapımı bir bağlantı (tarsus–platform teması → 100 Hz Poisson).
  - GRN → SEZ → MN9 yolu ise konnektomdan.
- **Dönüşe katkı küçük ve belirleyici değil.** DNp15 terimi final_a'da yaw komutuna eklenen en büyük terim (pay 0.43). Ancak sabitlendiğinde (final_b) rota neredeyse değişmiyor ve koşu yine iniyor. DNp15 okuması post-hoc seçildi (Adım 2 kararları).
- **Yalnız beyin (final_c) besine ulaşmıyor.** Navigasyonu taşıyan HAND katmanı olmadan konnektom okuması hedefe yönelmiyor. Beynin koku girdisi de kapalı.

## Sınırlamalar

- **Aerodinamik stroke-ortalamalı (quasi-steady).** Kanatların modelde eklemi ve dinamiği yok. Videolardaki kanat çırpması ve stroke zarfı görseldir; zarf kaydedilen genliği gösterir. 218 Hz çırpma 30 fps'te gösterilemez.
- **Hortumun modelde eklemi yok.** Rostrum/Haustellum gövdeleri var, eklemleri yok. Videolarda MN9 > 10 Hz iken kafadan besine turuncu bir **görsel işaret** çiziliyor; fizik yok.
- **Uniform LIF:** tüm nöronlar aynı parametrelerle (Shiu et al. modeli), 1.8 ms gecikme, w_syn 0.275 mV. Modülatör NT'ler hızlı uyarıcı/inhibitör sayılıyor.
- **DNg02 sessiz** (3 koşuda 0 spike). Kolektif ve irtifa beyinden okunamadı; tamamı HAND.
- **Beynin koku girdisi kapalı** (`--no-olfaction`). Hibritte koku navigasyonu el yapımı.
- **DNp15 yön okuması post-hoc seçildi.** Ön-kayıtlı doğrulama (Adım 2 kararları) kısmen başarısızdı: (a) geçti, (b) ve (c) geçmedi.
- **Tek seed (3).** Genelleme iddiası yok; final_a / final_b farkı betimseldir.
- FlyVis terimi yürüyüş sabitleriyle çalışıyor. FlyVis ağı FlyWire değil.
- Başarı, davranışın HAND katmanından geldiğini değiştirmez.

## Çıktılar

- Videolar (değişim modu; `render_flight_video_v2.py`, HDF5 qpos tekrarı):
  - `simulations/flight_v11_hybrid_noOlf_final_a_v2_change.mp4` (ana)
  - `simulations/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b_v2_change.mp4`
  - `simulations/flight_v13_ablOdor_noOlf_final_c_v2_change.mp4`
  - yan yana karşılaştırma: `simulations/compare_final_a_vs_final_c.mp4` (`render_flight_compare.py`)
- Grafikler: `plots/flight/<koşu>/01–15_*.png` (`generate_flight_plots.py --ablation … --extra`).
  - 13: üç koşunun besine uzaklık eğrisi
  - 14: dönüş bileşenleri yığını
  - 15: MN9 + temas anı
- Anahtar kareler: `plots/flight/v2_keyframes/`.

Render notu: platform, simülasyondaki gibi düz koyu (`platform="dark"`) çiziliyor. v2'nin ilk anahtar karelerinde ve
eski `render_flight_video.py` videolarında platform dokulu (neutral) görünüyordu. O görüntü FlyVis'in gördüğüyle aynı
değildi; simülasyonun kendisi etkilenmedi.

Video görselleri (yalnız render, HDF5'ler aynı): değişim modunun tabanı sabit (her nöronun kapalı döngünün ilk
0.5 s'sindeki, yani koşu t ∈ [0, 0.5) s ortalama hızı; kalkış 0.025 s'de başladığı için bu pencere kalkışı ve seyir
başını içerir). Beslenme başlangıcından 1.0 s sonrası ×1.0 gerçek zamanla (her 4. kare) oynatılır, ekranda yazar;
öncesi ×0.25. Besin damlası (`viz_food_drop`) yalnız kamera görüntülerinde sarı çizilir; göz paneli ve FlyVis girdisi
simülasyondaki koyu rengi görür. Karşılaştırma videosunda sağ (final_c) arena kamerası iki yörüngenin ortak sınır
kutusuna göre ortalanıp uzaklaştırılır.

## Atıflar

- Dorkenwald, S. et al. (2024). Neuronal wiring diagram of an adult brain. *Nature* 634, 124–138. doi:10.1038/s41586-024-07558-y
- Schlegel, P. et al. (2024). Whole-brain annotation and multi-connectome cell typing of *Drosophila*. *Nature* 634, 139–152. doi:10.1038/s41586-024-07686-5
- Shiu, P. K. et al. (2024). A *Drosophila* computational brain model reveals sensorimotor processing. *Nature* 634. doi:10.1038/s41586-024-07763-9
- Wang-Chen, S. et al. (2024). NeuroMechFly v2: simulating embodied sensorimotor control in adult *Drosophila*. *Nature Methods*. doi:10.1038/s41592-024-02497-y
- Lappalainen, J. K. et al. (2024). Connectome-constrained networks predict neural activity across the fly visual system. *Nature* 634. doi:10.1038/s41586-024-07939-3
- FlyWire verisi: **ticari olmayan kullanım** (CC BY-NC 4.0).

DOI'ler proje sahibinden alındı; başlıklar ve Dorkenwald/Schlegel sayfa aralıkları bellekten yazıldı, yayından önce
DOI üzerinden doğrulanmalı.
