> **Lab notebook, in Turkish.** Working record of this project, kept as written during the work (moved here from the repository root for the public snapshot). The English consolidated report is [REPORT.md](../../REPORT.md); the English summary is the [README](../../README.md).

# NeuroFly Flight — SPEC_FLIGHT

> Aşama 0 planı; kullanıcı tarafından 2026-09-29'da onaylandı. Kaynak istem: docs/UCUS_PROMPTU.md.

## Context
Yürüyüş sistemi (FlyWire v783: 138,639 LIF nöron, 15,091,983 recurrent sinaps + FlyGym MuJoCo gövde) aynı beyinle 3D serbest uçuşa taşınacak: kalkış → iki kuleyi aşma → besin platformuna konma → SEZ beslenme fazı. Repo'daki önceki uçuş denemelerinin hiçbiri gerçek kapalı döngü değil (MuJoCo yalnız kukla, `mj_step` yok, kulelerin içinden geçiliyor, yollar scriptli). **Kullanıcı kararı:** uçuş sıfırdan, temiz mimariyle yazılacak. Beyin kurulumunda yalnızca `brain_model/model.py`'nin parquet→Synapses mantığı referans alınacak. Eski denemeler silinmeyecek, `archive/`'a taşınacak. RL yok, budama yok; LIF parametreleri, 0.1 ms dt ve 25 ms karar adımı sabit.

## Kullanıcı kararları (AskUserQuestion)
0. Onay sonrası ekler:
   - `archive/flight_attempts/` içindeki `.py` dosyaları commit edilir. `archive/scratch/` ve arşivdeki medya dosyaları (png/mp4/gif/h5) `.gitignore`'a eklenir.
   - **Aşama 0.5, 2 ve 3 sonunda durulur:** test çıktısı ve kısa özet gösterilir, kullanıcı onayı beklenir.
   - Aşama 1'de ölçülen I_asym zayıf çıkarsa ℓ_eff kararı verilmeden önce kullanıcıya sorulur.
1. Temel: hiçbir deneme temel alınmaz; sıfırdan yazılır. Beyin için model.py referans + testle kanıt.
2. Zaman ölçeği: **arena ×20, gerçek hız**. Hız fizikten çıkar: seyir ~200–400 mm/s, platforma yaklaşırken landing response ile <50 mm/s. Kameralar: yakın takip + tüm arena geniş. ~80 karar adımı hedef; artış gerekirse gerekçeli.
3. Temas: yürüyüşle aynı. CLAUDE.md solimp/solref yalnız kule/platform geom'larında; sinek–arena pair'lerinde FlyGym varsayılanı. CLAUDE.md satırı buna göre düzeltilir ve gerekçe notu eklenir.
4. Temizlik: `tests/conftest.py`; yürüyüşe `import gc`; model.py/utils.py diff'i önce `archive/uncommitted_model_utils.patch`'e yedeklenir, sonra HEAD'e döndürülür; eski denemeler `archive/flight_attempts/`'a, `scratch_*` dosyaları `archive/scratch/`'a taşınır (hiçbiri git'te izlenmiyor → düz `mv`). Hiçbir şey silinmez.
5. Swap: 8 GB /swapfile aktif (doğrulandı). Not: ölçüm anında başka süreçler ~7.7 GB RAM kullanıyordu (boşta ~7.5 GB).

## 0. Keşif bulguları (doğrulandı)
**Ortam.** `$HOME/miniforge3/envs/neurofly/bin/python` (py3.10; brian2 2.9.0, flygym 1.2.1, mujoco 3.2.7, dm_control 1.0.27, flybody d015e9b, flyvis 1.2.0, torch, h5py 3.14, mpl 3.10.8, psutil 7.2.2, pytest 9.1.1). base env (py3.13) kullanılmaz. **Kabuk profili ROS Jazzy `PYTHONPATH`'ini (py3.12 site-packages) enjekte ediyor** → pytest `launch_testing` eklentisiyle çöküyor ve py3.10 env'inde paket gölgeleme riski var. Tüm proje komutları `env -u PYTHONPATH ...` ile çalıştırılır; `run_flight_detached.sh` bunu kendisi yapar. aarch64, 8 çekirdek, GPU yok. Brian2 Cython cache dolu.

**Veri.**
- Completeness 138,639 satır; parquet 15,091,983 satır.
- "Excitatory x Connectivity": Σ = 10,496,512, Σ|·| = 54,492,922.
- Gruplar (root_id → Completeness satırı eşlemesiyle; yürüyüşteki seçicilerle):

| Grup | Sayı | Not |
|---|---|---|
| ascending | 1736 | |
| olfactory | 2279 | aslında ORN |
| SEZ | 408 | aslında gustatory reseptör nöronları |
| DN | 1299 | 645 L / 646 R / 8 center |
| LA>ME | 8025 | 4189 L / 3836 R |

- Literatürdeki DN'ler annotations'ta mevcut:
  - **DNg02_a..h: 25 nöron** (Namiki et al. 2022: kanat vuruş genliğini/gücünü düzenler).
  - DNa01, DNa02, DNp01 (giant fiber, von Reyn 2014): her biri 1+1.
  - DNb01, DNa03, DNg03 (10) ve diğerleri.
- FlyWire yalnız beyin içeriyor: kanat motor nöronu yok, haltere refleksleri VNC'de.

**Taslaktaki 7 hatanın kodda doğrulanması.** Hepsi taslakta mevcut. Ayrıca:
1. Uncommitted `model.py:376-433`'te recurrent sinaps yok; `PoissonGroup` import edilmemiş; `neu[:1736]` ve `range(408)` dilimleri var.
2. `flight_dn_mapping.py` `'bilateral'` arıyor ama CSV'de `'center'` var → liste hep boş; pitch = tanh((0−50)/30) ≈ −0.93 sabit. Veride `neu[:1736]` dilimi yalnız 44 gerçek ascending nöron içeriyor; `neu[:408]` 3 gustatory; CSV satır numarası DN'lerden yalnız 19'u gerçek DN.
3. MuJoCo yalnız kukla olarak kullanılıyor.
4. Birimler nN; itki besine uzaklıkla ölçekleniyor (sineğin sahip olmadığı bilgi); ω = τ/(m·0.5) doğrudan atanıyor; pitch/roll kuvvete girmiyor.
5. Spike sayımında `np.asarray(spk_mon.i)` tüm geçmişi kopyalıyor. Ölçüm: dilim ~0.03 ms sabit, tam kopya 6M spike'ta 1.7 ms.
6. Video yalnız metin karesi. Güncel deneme kamera karelerini listede biriktiriyor (~2.2 GB).
7. "DN" = tüm 1299 DN'in L−R farkı. Connectome'un kendi ~%4'lük R>L bias'ı sineği arenadan 130 mm dışarı döndürdü.

**Taslak ↔ repo ek tutarsızlıklar.**
- `SpikeMonitor(neu[idx])` brian2 2.9'da IndexError veriyor.
- Poisson sürüşü `g += 0.275 mV`; yürüyüşteki `v += 68.75 mV`'nin ~1/250'si → pratikte hiç spike yok.
- LIF formu model.py'den farklı (`exact` yöntemi, farklı reset).
- float32 Dijkstra 6 dakikadan uzun sürüyor (float64 ile 0.6 s).
- Yaw işareti yürüyüşe göre ters.
- İrtifa kontrolü besinin z koordinatını "kehanet" olarak kullanıyor.
- İtki hep doygun.
- Izgara 51×41×25 (taslakta 50×30×24 yazıyor).
- Besinin altında kule yok.
- Terminal hız ~667 mm/s; kule 1'in içinden geçiyor ve sinek arenadan 3.5 m uzaklaşıyor.
- "13 grafik" deniyor ama 4 var.
- "Yürüyüşü arşivle" talimatı CLAUDE.md ile çelişiyor.
- Görsel girdi sahte: kulelere uzaklık kullanılıyor.
- `odor_field_3d` ızgara dışında kenar değerine kıstırıyor.
- `generate_flight_plots.py` kapalı HDF5'ten okuyor.
- `run_detached.sh` artık var olmayan bir dizine işaret ediyor.

**Yürüyüş hakkında.**
- Olfactory ve SEZ sabit 80 Hz ile sürülüyor; koku ve beslenme beyne nedensel olarak girmiyor.
- DN katkısı ±0.005, koku terimi ±2.5 → yön fiilen el yapımı.
- Uncommitted yürüyüş diff'i: `gc` import edilmemiş → satır 1040'ta NameError.
- Adım maliyeti 23 s'den 38 s'ye çıkıyor; tam kopya bunu açıklamıyor, sebep ayrıca loglanacak.

**tests/.** 25 dosyanın hiçbiri pytest testi değil. Modül seviyesinde tam simülasyon koşturuyorlar, bu yüzden `pytest tests/` saatlerce sürer.

**Fizik prototipleri** (dosya yazmadan, FlyGym, dt 1e-4):
- `xfrc` ile yalnız F = mg: takla atıyor. COM düzeltme torku + tutum PD ile: 1 s'de |Δz| < 0.001 mm.
- Arena geom'ları yalnız `floor_collisions` ("legs") ile temas kuruyor → gövde kulenin içinden geçiyor.
- `floor_collisions="all"` + FlyGym pair varsayılanı: 300 mm/s'de penetrasyon 81 µm, BADQACC yok. Maliyet ~5.5 ms/fizik adımı.
- Pair'lere CLAUDE.md değerleri verilince: 1.8 mm penetrasyon veya kuleden geçip gitme.

## 1. Fizik yaklaşımı
| Kriter | (A) flybody kanat + aero | (B) FlyGym + xfrc stroke-averaged | (C) nokta-kütle/6-DOF |
|---|---|---|---|
| Gerçekçilik | En yüksek: kanat kinematiği + fluid | Gövde, göz, temas ve adhezyon gerçek; aero quasi-steady (Sane & Dickinson; Fry 2003) + flapping counter-force/torque (Hedrick 2009) | Düşük |
| dt / maliyet | 5e-5 s (500 adım/karar), cm birimleri | 1e-4 s (250 adım/karar), ~1.4 s/karar ≪ beyin ~25 s | İhmal edilebilir |
| Kule çarpışması / iniş | MuJoCo var, ama FlyGym retina ve adhezyon yok | Gerçek MuJoCo teması (prototipte doğrulandı) + tarsus sensörleri | Elle yazılmalı |
| RL'siz kontrol | Stabil uçuş RL politikasıyla elde edilmiş | Φ_L/Φ_R/f → kuvvet/tork; haltere PD (prototipte stabil) | Kolay ama anlamsız |
| Risk | Çok yüksek | Orta | Kabul kriterini karşılamaz |

**Öneri: (B).** Kanatlar yalnız görsel olarak çırpılır (render sırasında wing `body_quat` değiştirilir, dinamiğe girmez). Raporda açıkça yazılır.

## 2. Zaman ölçeği (×20 arena)
**Geometri** (spec × SCALE=20; tek `flight_config.py`):

| Öğe | Konum (mm) |
|---|---|
| Kule1 | x∈[160,200], y∈[−100,160], z∈[0,200] |
| Kule2 | x∈[280,320], y∈[60,300], z∈[0,200] |
| Kalkış kaidesi | (0,0), üst yüzey z≈19.5 → thorax ~(0,0,20) |
| Besin platformu | silindir (440,80), r=10, üst yüzey z=169.5 |
| Besin damlası | r=0.5, merkez (440,80,170); görsel, contype 0 |

- Sineğin kendisi ölçeklenmez (~2.5 mm).
- 400 mm/s'de karar başına 10 mm yol alınır; kule kalınlığı 40 mm → uyumlu. Fizik 300–400 mm/s'de temas testini geçiyor.
- **Süre gerekçesi.** 3D yol ~500–600 mm (kulelerin üstünden ya da çevresinden). Tırmanma dahil ortalama ~250 mm/s → ~2.2 s ≈ 90 adım. Ek süreler:
  - kalkış 0.25 s (10 adım)
  - yaklaşma yavaşlaması + iniş ~0.5 s (20 adım)
  - SEZ fazının görünmesi için beslenme 1 s (40 adım)
  - pay
- **Öneri: 160 adım (4 s).** ~80 adım yalnız uçuşa yeter; iniş ve beslenme için artış gerekiyor.
- Maliyet: ~25 s/adım → ~70 dk beyin + ~4 dk fizik + kurulum ~5 dk, toplam **~1.5 saat**. Video + grafikler ayrıca ~20–30 dk. `--n-steps` ile değiştirilebilir.

## 3. Mimari (yeni dosyalar)
```
flight/                          # yeni paket (__init__.py)
  config.py                      # SCALE, geometri, LIF'e dokunmayan uçuş sabitleri, faz kodları
  brain.py                       # create_model() çağrısı + gruplar + Poisson girdileri + artımlı sayım + dev-subnet
  groups.py                      # annotations → root_id → indeks; DN seçimi (literatür/VARSAYIM etiketli)
  odor_field_3d.py               # (simulation_data/odor_field_3d.py olarak da re-export) 3D Dijkstra + trilineer
  quasi_steady.py                # stroke-averaged kuvvet/tork + counter-force sönümü (saf numpy, test edilebilir)
  body.py                        # FlyGym Fly/arena kurulumu, xfrc uygulama, haltere refleksi, poz, temas okuma
  sensors.py                     # koku örnekleme, göz parlaklığı, FlyVis T5/looming, genişleme oranı (landing)
  controller.py                  # turn/pitch/collective/forward eşlemesi, fazlar (saf fonksiyonlar)
  recorder.py                    # ön-ayrılmış diziler + spike parçaları → HDF5
fly_flight_brain_body_simulation.py   # CLI + kapalı döngü (ince orkestratör)
render_flight_video.py                # HDF5 → 1920×1280 video (qpos replay)
generate_flight_plots.py              # HDF5 → 13 grafik
run_flight_detached.sh
tests/conftest.py, tests/flight/test_*.py
```
Aşama 1'in istediği `simulation_data/odor_field_3d.py` yolu korunur: gerçek kod bu dosyada olur, `flight/` ondan import eder.

### Beyin (`flight/brain.py`)
- `sys.path` ile `brain_model/model.py`'den `create_model, default_params` import edilir; model.py'ye dokunulmaz. LIF ve 0.1 ms dt aynen kalır.
- **Girdiler.** Hepsi PoissonGroup → Synapses `v += w_syn·f_poi` (68.75 mV), gecikme 1.8 ms, hedef nöronda rfc = 0. Oranlar `.rates` atamasıyla güncellenir, yeniden derleme olmaz.
  - **ascending 1736:** `r_asc = 150·(0.15+0.85·clip(|ω|/15,0,1))`. ω = MuJoCo gövde açısal hızı (rad/s).
  - **olfactory L/R:** antendeki normalize koku → 20–150 Hz (yürüyüşteki sabit 80 Hz yerine koku sürüşlü).
  - **LA>ME L/R:** göz parlaklığı → 20–150 Hz (yürüyüşle aynı).
  - **gustatory/SEZ 408:** uçuşta 10 Hz taban. Besin teması (iniş + proboscis) sırasında 150 Hz → SEZ fazı; çıkış olarak SEZ bölge ateşleme oranı ölçülür.
- **DN okuma** (karar başına spike sayısı):
  - `dng02_L/R` (25) → kolektif güç [Namiki 2022].
  - `steer_L/R` = DNa01 + DNa02 → **VARSAYIM** (yürüyüşte yön DN'leri).
  - `all_dn_L/R` (1299): yürüyüşle karşılaştırma için.
  - `dnp01`: yalnız kayıt.
  - Taban çıkarımı: kalkış öncesi 0.25 s kalibrasyon ortalaması (connectome'un kendi R>L bias'ını sıfırlar). Bu bir el yapımı normalizasyondur ve öyle etiketlenir.
- **Artımlı sayım.** `n0 = spk_mon.num_spikes; net.run(25 ms); new_i = spk_mon.i[n0:]; new_t = spk_mon.t_[n0:]` → `np.bincount(new_i, minlength=N)` (nöron başına), grup sayıları indeks listeleri üzerinden toplanır. Gruplar örtüştüğü için (DNg02 ⊂ dn_L/R) etiket dizisi yerine bu yol seçildi (Aşama 2). Yeni spike'lar int32/float32 parçalar halinde listeye eklenir (yalnız yeni kısım). SpikeMonitor tam kaydı: ~4 s × ~10 Hz × 138k ≈ 5.5M spike ≈ 70 MB.
- **`--dev-subnet`:** annotations gruplarının birleşimi ∪ 1-hop partnerleri. Parquet bu kümeye filtrelenip yeniden indekslenir (geçici dizine yazılır, aynı `create_model()` ile kurulur). Spike'lar global indeksle saklanır. Dosya adında `DEV`, meta'da `dev_subnet=True`. Sonuç olarak raporlanmaz.
  - Ölçüm (Aşama 2): 13,747 çekirdek nöron → 1-hop ile 98,157 nöron, 8,818,102 sinaps (tam ağın %58'i).
  - **Kullanıcı kararı (Aşama 2 onayı):** `--dev-subnet` varsayılanı yalnız ≥10 sinapslı partnerleri alır (`DEV_MIN_SYN`): 52,579 nöron, 3,439,313 sinaps (%23). Tam 1-hop sürümü `--dev-subnet-full` bayrağıyla kalır.
- **Uygulama notları (Aşama 2).**
  - Olfactory 2279 = 1116 L / 1133 R / 30 tarafı bilinmeyen (`olf_C`, L/R ortalamasıyla sürülür).
  - Girdi grupları (ascending, olfactory, SEZ, LA>ME) ayrık; kurulumda kontrol edilir.
  - DN okumaları `descending_neurons.csv`'den (cell_type + side): DNg02 13 L / 12 R, DNa01+DNa02 2 L / 2 R, DNp01 1+1.
- **Bench (Aşama 2, tam beyin, seed 0).**
  - Kurulum 1.3 s (Cython cache dolu), adım 0.27 s / 25 ms, tepe RSS 2.8 GB. SPEC'teki ~25 s/adım varsayımı beyin için geçersiz; yürüyüşteki adım maliyeti beyinden gelmiyor.
  - Kalkış öncesi (asc 22.5, olf 20, vis 20, sez 10 Hz), 40 adım, 25 ms başına ortalama spike: dng02_L/R 0 / 0 (25 nöronun hiçbiri ateşlemiyor); steer_L 2.08, steer_R 0.12 (adımların %88'i 0); all_dn_L/R 75.4 / 82.0; dnp01 0. Ağ ortalaması 5.65 Hz, nöronların %18.7'si en az bir kez ateşliyor.
  - Hücre tipi bazında, 1 s: DNa02 perch L 1.85 / R 0.08; girdiler 150 Hz'e çıkınca L 3.3 / R 2.25. Bu değerler sağ koku ya da sağ göz asimetrisiyle değişmiyor. DNa01 yükselen girdide susuyor. DNg02, DNp01, DNa03–06, DNb01, DNg01, DNg03, DNp03 ve DNp15 tüm koşullarda ≈ 0. DNg13 aktif (2–3.3) ama lateral tepkisi yok. all_dn: sağ göz sürüşünde R−L farkı +11'den +22'ye çıkıyor.
  - Sonuç: bu girdi düzeyinde `steer` ve `dng02` okumaları sensör asimetrisini taşımıyor; ΔDN terimleri pratikte ~0 ya da sabit bias olur. 
- **Kullanıcı kararı (Aşama 3 onayı, DN seçimi).**
  - Ana yön sinyali `all_dn_L/R` (1299 DN): yürüyüşteki `(L−R)/(L+R)` oranı, kalkış öncesi kalibrasyonun aynı oranı çıkarılarak (`ΔDN`). Kazanç yürüyüşle aynı: `turn_dn = 0.15·ΔDN`.
  - `steer` (DNa01/02) ve `dng02` yalnız kayıt için HDF5'e yazılır; kontrole girmez.
  - Veriye dayalı DN seçimi yapılmaz (döngüsel olur).
- **DNg02 yeniden testi (Aşama 4, tam beyin, seed 0, 8 adım yerleşme + 40 adım = 1 s/koşul).**
  - Taban (asc 22.5, vis 20, olf 20, sez 10 Hz): 25 DNg02 nöronunun toplam spike'ı 0.
  - LA>ME L+R ve ascending 300 Hz: ağ ortalaması 32.8 Hz, nöronların %33.7'si aktif, all_dn L/R 422 / 453 spike/adım, **DNg02 toplam 0** (a..h alt tiplerinin hepsi 0).
  - Aynı + olfactory 150 Hz: ağ 35.7 Hz, **DNg02 yine 0**.
  - Olası neden (yalnız gözlem): DNg02'ye gelen sinapsların net işareti inhibitör. 1138 presinaptik partnerden 3100 bağlantı; Σ(eks.) = +6101, Σ(inh.) = −7228; nöron başına net medyan −9, ortalama −45. Girdi gruplarından doğrudan gelen yalnız 169 bağlantı var.
  - **Sonuç:** Kod değiştirilmedi. Bu modelde **kolektif güce (kanat genliği) konnektom katkısı 0'dır**; kolektif tamamen el yapımı terimlerden gelir (koku gradyanı eşlemesi, dikey hız sönümü, ventral refleks, kalkış artışı). Raporda açıkça yazılır.

### Gövde ve fizik (`flight/body.py`, `flight/quasi_steady.py`)
- **Kurulum.**
  - `Fly(enable_vision, enable_adhesion, tarsus contact sensors, floor_collisions=<gövde+bacak collision geom listesi>)`. Pair'ler FlyGym varsayılanında; kule/platform geom'larında CLAUDE.md solimp/solref.
  - `SingleFlySimulation`, dt 1e-4, karar başına 250 adım.
  - Arena: ≥ 700×600 mm FlatTerrain.
- **Kuvvet.**
  - Kanat başına `F_w = (W/2)·(Φ_w/Φ0)²·(f/f0)²`; Φ0 = 140°, f0 = 218 Hz; W = m·g ≈ 10.07 µN (g·mm/s²).
  - Kuvvet gövde-sabit strok düzlemi normali boyunca uygulanır. Gövde pitch'i kuvveti öne yatırır → ileri hız **fizikten çıkar**.
  - Sönüm: FCF ≈ −c_F·(f·Φ̄)·v, FCT ≈ −c_T·(f·Φ̄)·ω (Hedrick 2009). c_F, pitch eğimi ~10–15°'de terminal hız 200–400 mm/s olacak şekilde tek sefer kalibre edilir; testte ölçülür.
  - Kuvvet ve tork subtree COM'a göre düzeltilir ve Thorax'a `xfrc_applied` ile uygulanır.
- **Torklar.**
  - Yaw ∝ (Φ_L − Φ_R).
  - Roll = (F_L − F_R)·yan kol → roll fiziksel olarak yaw'a bağlıdır. Taslaktaki "roll = −0.4·yaw" sabit atanmaz; ölçülen oran raporlanır.
  - Pitch = strok düzlemi / ileri–geri kayma torku.
- **Haltere refleksi (EL YAPIMI, VNC temsili).** Fizik hızında açısal hız PD'si (pitch/roll/yaw). Konnektomda karşılığı yok.
- **Temas.** Tarsus sensörleri + `data.contact` taranarak platform/kule temasları ve min. kule mesafesi okunur.
- **Bacaklar.** Uçuşta tuck pozu, inişte açık poz. Joint isimleri `fly.actuated_joints` üzerinden doğrulanır; iniş sonrası adhezyon açılır.
- **Uygulama notları ve ölçümler (Aşama 3).**
  - Model: kütle 1.027 mg, W = 10.07 µN. Birimler mm, s, g → kuvvet µN, tork µN·mm.
  - **Basitleştirme:** strok düzlemi normali = gövde +z. Hover düz gövdeyle yapılır; gerçek sinekte gövde ~45° burun yukarıdadır. İleri itki gövdenin burun-aşağı eğilmesinden gelir.
  - Katsayılar (`quasi_steady.make_params`, config'ten türetilir):
    - c_F: 12° eğimde terminal hız 300 mm/s olacak şekilde seçildi (7.06e-3 µN·s/mm; öteleme sönüm zaman sabiti m/c_F ≈ 0.15 s). Terminal hız testi bu kalibrasyonu doğrular; bağımsız bir tahmin değildir.
    - c_T: I_zz / 50 ms.
    - Haltere refleksi (EL YAPIMI): roll/pitch tutum PD'si (ω_n = 60 rad/s, ζ = 1) + yaw hızı sönümü (toplam τ = 20 ms).
    - Yaw kazancı: turn_bias = 1 → ΔΦ = 10° → kalıcı yaw hızı 5 rad/s.
  - Kuvvet ve tork her fizik adımında hesaplanır, tüm sineğin COM'una (subtree_com) göre Thorax `xfrc_applied` ile uygulanır. Beyin adımı başına `fly.pre_step` bir kez çağrılır, ardından 250 × `physics.step()`.
  - Çarpışma: sinek geom'larının hepsi arena ile pair kurar; anten (Pedicel/Funiculus/Arista) ve Haltere hariç. Toplam 2477 pair (self-collision dahil). Arena geom'larında contype = conaffinity = 0; yalnız explicit pair'ler çarpışır. `viz_*` geom'larının pair'leri silinir.
  - Tuck pozu: yürüyüş duruş pozundan ofsetler (femur −40°, tibia +55–75°, coxa_roll −25°), render ile göz kontrolü yapıldı. Kozmetiktir; uçuş dinamiğine etkisi yalnız COM ve inertia üzerinden.
  - Maliyet: 4.2 ms / fizik adımı → 1.04 s / karar. Beyin 0.27 s / karar olduğundan fizik baskın. 160 adım ≈ 3.5 dk + kurulum (§2'deki ~1.5 saat tahmini geçersiz; video/grafik süresi ayrı).
  - Ölçümler (seed yok, deterministik):
    - hover 1 s: |Δz| ≈ 1e-6 mm.
    - 400 mm/s kule 1 çarpması: max penetrasyon 19.7 µm, BADQACC 0, sekme ~−50 mm/s.
    - Platforma 1.5 mm'den bırakma: 6/6 tarsus teması.
    - 12° eğim: 1 s'de 299.6 mm/s.
    - turn_bias 0.5: 0.25 s'de −32.9°, yaw hızı −2.5 rad/s, sağa yatış 0.34°. Roll/yaw bağlantısı zayıf, çünkü haltere tutum PD'si roll'u tutuyor.
    - Kaideden kalkış (1.05× hover genliği, bacaklar tuck): 0.25 s'de +23 mm, BADQACC 0.
  - **Düzeltme (Aşama 4): kök gövde sahte kütlesi.** FlyGym'in serbest kök gövdesi `"<ad>/"` 1e-6 g'lık sahte bir inertial taşıyor. Bunun `ipos`'u spawn konumuna eşit, yani sinekten |spawn| mm uzakta (xipos = 2·spawn).
    - Etkisi: yalnız `inertia_body()` hesabını değil, MuJoCo dinamiğini de bozuyordu. Açık hava spawn'ında (|spawn| = 175 mm) roll eylemsizliği ~60× büyüktü (Ixx 0.0295'e karşı gerçek 1.2e-4 g·mm²). `subtree_com` da |spawn|'ın ~%0.1'i kadar kayıyordu.
    - Kaide spawn'ında (|spawn| ≈ 20 mm) Ixx/Iyy yaklaşık 2–4× büyüktü.
    - Düzeltme: `body.py`'de `m.body_ipos[root] = 0`. Sahte kütle sineğin içine taşındı; kütle değişmedi. Gerçek bileşik eylemsizlik (tuck): diag ≈ (1.2e-4, 5.1e-4, 5.1e-4) g·mm².
    - Sonuç: yukarıdaki Aşama 3 ölçümleri şişik eylemsizlikle yapılmıştı. Gerçek eylemsizlikte, ω_n = 60 rad/s ile haltere refleksi çok yumuşak kaldı: turn −0.2'de 30° yatış ve 0.25 s'de 500 mm/s yanal kayma. Aşama 3'teki kararlılık fiilen ~17 kat aşırı sönümlü, çok sert bir döngüden geliyordu.
  - **Haltere ω_n = 200 rad/s** (EL YAPIMI, `HALTERE_OMEGA_N`). Gerekçe: sinekler roll bozulmalarını ~30 ms içinde düzeltiyor (Beatus et al. 2015). Kritik sönümlü 5.8/ω_n ≈ 30 ms. ζ = 1 ve yaw τ = 20 ms aynı kaldı.
  - **Yeniden ölçüm (düzeltilmiş gövde, ω_n = 200).** Aşama 3 testlerinin hepsi yine geçiyor.
    - 12° eğim: 1 s'de 299.7 mm/s.
    - turn_bias 0.5: 0.25 s'de −33.2°, yaw hızı −2.52 rad/s, sağa yatış 6.8°. Roll/yaw bağlantısı birim turn başına ~13.5° yatış; 300 mm/s ve 5 rad/s'lik koordineli dönüşün yatışı (~9°) ile aynı mertebede. Hover/kalkışta bu yatış yana kayma üretir: turn −0.2'de 0.25 s'de ~40 mm/s.
    - Haltere darbe testi (`test_haltere_recovers_gust_within_200ms`): 50 ms'lik gövde ekseni tork darbesi (kp·0.35 rad; roll 4.55, pitch 21.2 µN·mm). Darbe sonunda eğim roll 20.3°, pitch 20.4°. <1°'ye dönüş roll'da darbeden 33 ms, pitch'te 26 ms sonra; 0.2 s sonra 0.000°, BADQACC 0.
    - Kontrol: refleks kapalıyken aynı darbe sineği takla attırıyor (tepe 176°, 0.2 s sonra 107°). Toparlanmayı yapan el yapımı refleks.

### Kontrol (`flight/controller.py`, her 25 ms)
- **`turn_bias = tanh(20·I_asym)·2 + 0.15·ΔDN + b_loom` → ΔΦ.** ΔDN = all_dn `(L−R)/(L+R)` − kalibrasyon oranı (kullanıcı kararı, Aşama 3 onayı; `steer` yalnız kayıt).
  - İşaret yürüyüşle aynı: koku sağdaysa sağa döner. Birim testle sabitlenir.
  - `I_asym` = sol/sağ anten (±ℓ yanal) koku farkı / toplamı.
  - **ℓ_eff kararı (Aşama 1, kullanıcı onaylı).** Ölçüm: gerçek ℓ = 0.5 mm ile ×20 arenada |I_asym| kalkışta ≤ 0.0009, kuleler arasında ≤ 0.005, besine ~60 mm'de ≤ 0.013 (gradyan 90° yandayken). Dönüş terimi 2·tanh(20·I) bu durumda ≤ 0.04–0.5 / 2 kalıyor. Yürüyüşte (ℓ = 0.5, d ≈ 20 mm) I ≈ 0.05.
    - Yön için **ℓ_eff = 10 mm** kullanılır (`ANTENNA_HALF_SEP_EFF`). **EL YAPIMI.** Uçuşta zamansal-mekânsal koku örneklemesinin (casting, hareket boyunca ardışık örnekleme) temsilidir ve ℓ/d oranını yürüyüş seviyesinde tutar. I_grad (üst/alt) için de aynı ℓ kullanılır.
    - Gerçek ℓ = 0.5 mm ile hesaplanan I_asym ve I_grad her adımda ayrı sütun olarak HDF5'e yazılır. `--antenna-real` bayrağı yönü bunlarla sürer (ablasyon koşusu).
- **`pitch_bias = 0.8·tanh(10·I_grad) + b_alt_hold` → kolektif genlik.**
  - `I_grad` = anten üstü/altı ±ℓ farkı.
  - `b_alt_hold = −k·v_z` (dikey hız sönümü). **Hedef irtifa yok** (önceki denemelerin z-kehanetinin tersine).
  - Ek: zemin/kule üstü ventral refleksi (EL YAPIMI).
- **DNg02 terimi: YOK** (kullanıcı kararı). DNg02 yalnız kaydedilir; bu modelde sessiz (Aşama 4 yeniden testi). Kolektife konnektom katkısı 0.
- **İleri hız:** gövde pitch hedefi θ_cruise (~12°, EL YAPIMI). Hız kendisi fizikten çıkar.
- **Landing response.** Platformun görüntü genişleme oranı `ṙ/r` (geometrik; FlyVis looming sinyali de kaydedilir) eşiği aştığında pitch-up → yavaşlama; ardından bacak açma. Tetik EL YAPIMI (van Breugel & Dickinson 2012; Card & Dickinson 2008). Hedef: temasta hız < 50 mm/s.
- **`b_loom`:** FlyVis T5 L/R asimetrisi (yürüyüşteki yöntem, yeni kod).
- Her terim HDF5'e ayrı ayrı yazılır.
- **Fazlar:** perch → takeoff → cruise → approach → touchdown → feed_extend → feed_eat → feed_retract. İniş = tarsus–platform MuJoCo teması (≥2 bacak, 50 ms). Sonra kanat kuvveti 0 olur ve SEZ girdisi yükselir.
- **Ablasyon bayrakları:** `--ablate-dn` (turn_dn = 0), `--ablate-odor` (I_asym = I_grad = 0), `--antenna-real` (yön gerçek ℓ = 0.5 mm ile).

### Döngü (`fly_flight_brain_body_simulation.py`)
- CLI: `--n-steps 160 --dev-subnet --dev-subnet-full --ablate-dn --ablate-odor --antenna-real --seed --tag --no-video`.
- **Adım sırası:** sensörler → oranlar → `net.run(25 ms)` → artımlı sayım → kontrol → 250 fizik adımı (her adımda xfrc + haltere) → kayıt.
- Video karesi anlarında (play_speed 0.25, 30 fps → her 8.33 ms'de bir, karar başına 3) yalnız `qpos` kaydedilir; kamera render'ı yapılmaz.
- **Döngü bitince önce HDF5 yazılır** (spike'lar dahil), `del` + `gc.collect()`, sonra `render_flight_video.py` çağrılır (`--no-video` ise atlanır).
- Adım başına süre ve RSS (psutil, VmHWM) loglanır.

### HDF5 (`simulations/flight_v{N}[_DEV][_ablDN|_ablOdor|_antReal]_data.h5`)
- **`/meta` attrs:** n_steps, decision_interval, brain_dt, physics_dt, scale, play_speed, fps, flags, seed, git_hash, timestamp, geometry (json), lif_params (json), group_counts (json), peak_rss_gb, step_time_mean.
- **`/behavior` (N):**
  - Durum: t, pos(N,3), vel(N,3), speed, quat(N,4), omega(N,3), dist_to_food, phase(int8, attrs kod tablosu).
  - Koku: odor_L/R/U/D, I_asym, I_grad (yönde kullanılan ℓ ile); I_asym_real, I_grad_real (her zaman ℓ = 0.5 mm).
  - Yaw bileşenleri: turn_bias, turn_odor, turn_dn, turn_loom.
  - Pitch/güç bileşenleri: pitch_bias, pitch_odor, pitch_alt, pitch_ventral, pitch_takeoff, lift_frac, pitch_down (coll_dng02 yok: kullanıcı kararı).
  - Motor: stroke_amp_L/R, stroke_freq, force(N,3), torque(N,3).
  - Girdi oranları: asc_rate, vis_rate_L/R, olf_rate_L/R, sez_rate_in.
  - Görsel: loom_L/R, expansion_rate.
  - DN sayıları: dng02_L/R, steer_L/R, all_dn_L/R, dnp01.
  - Çıktı/temas: sez_out_rate, platform_contact, tower_contact, min_tower_clearance, is_feeding.
  - Aşama 4 ekleri: heading, dn_lr_delta, height_above, brain_mn (sayım), step_time, brain_time, rss_gb, tower_penetration. `sez_out_rate` = brain_mn spike'ı / (105 · 25 ms).
  - v7 teşhisi ekleri: ell_LR, ell_UD (kullanılan anten yarı-aralığı), v_fwd (gövde yönünde yatay hız).
- **`/spikes`:** `all/{t float32 s, i int32 global}` (gzip); `groups/<ad>` = global indeks listeleri.
- **`/positions`:** `{x, z, idx}` (beyin paneli soma/pos birleşimi).
- **`/odor_field_3d`:** `{conc, blocked}` + attrs origin, res, food.
- **`/render`:** `{t, qpos(F,nq)}`.

### Video (`render_flight_video.py`)
- 1920×1280, 30 fps, libx264.
- Üst panel 1920×640: beyin. Frontal soma projeksiyonu, glow τ = 80 ms artımlı hesaplanır; frame×nöron dizisi tutulmaz, spike'lar numpy ile sıralanır.
- Alt panel 2×960×640:
  - (1) **yakın takip:** sineğin ~8 mm arkası/üstü; pos + yaw + z takip edilir.
  - (2) **geniş arena:** sabit, tüm kuleler/platform görünür. Sinek görünür kalsın diye render-only işaretçi (contype 0) + iz çizgisi.
- `qpos` MuJoCo'ya geri oynatılır. Her kare `writer.append_data`, `plt.close(fig)`, `buffer_rgba`.

### 13 grafik (`generate_flight_plots.py` → `plots/flight/v{N}/`)
1. circuit_timeline
2. raster_circuits
3. dn_steer_turn_coupling
4. dng02_collective_coupling
5. population_heatmap
6. firing_rate_distribution
7. odor_olfactory_response
8. visual_lamina_loom
9. trajectory_3d (kuleler + platform)
10. altitude_speed_profile (landing yavaşlaması dahil)
11. turn_pitch_decomposition (el yapımı / DN / loom payları)
12. odor_field_3d_slices + yörünge
13. distance_to_food (+ ablasyon eğrileri üst üste)

## 4. Bellek planı (15 GB RAM + 8 GB swap; hedef tepe RSS < 13 GB)
**Tahmini tepe RSS.** Diğer süreçler ~7.7 GB tuttuğunda bu sistemde swap devreye girebilir; hedef, bizim süreç için ≤ 8 GB.

| Kalem | Tahmin |
|---|---|
| Parquet yükleme (15M × 7 int64) | geçici ~0.85 GB |
| Brian Synapses (i, j, w, delay) | ~0.6–1.2 GB |
| Kurulum geçici tepe | ~3–4 GB |
| FlyVis + torch | ~1 GB |
| MuJoCo | < 0.3 GB |
| SpikeMonitor | ~0.1 GB |

**Kurallar.**
- `create_model` sonrası `df_con` referansları bırakılır ve `gc.collect()` çağrılır.
- Kamera kareleri döngüde hiç üretilmez.
- Video replay'de glow vektörü tek (138k float32).
- Spike sıralaması numpy ile yapılır (Python tuple listesi yok).
- HDF5 videodan önce yazılır.
- Her adımda RSS loglanır; RSS 12 GB'ı aşarsa uyarı basılır.
- `run_flight_detached.sh` `/usr/bin/time -v` ile tepe RSS'i log'a yazar.
- Swap bir güvenlik payıdır, bütçeye dahil edilmez.

## 5. Uygulama aşamaları (her aşama sonunda: pytest çıktısı + smoke + commit)
**0.5 — Hazırlık.** (sonunda DUR, onay bekle)
- `SPEC_FLIGHT.md` yazılır.
- `archive/uncommitted_model_utils.patch` (git diff) oluşturulur → `git checkout brain_model/model.py brain_model/utils.py`.
- Arşive taşınacaklar (untracked → `mv`): `.bak`, `fly_flight_brain_body_simulation.py` (eski), `fly_flight_40s_perfected.py`, `fly_flight_biological_40s.py`, `render_*_40s*_video.py`, `flight_controllers/`, `brain_model/flight_dn_mapping.py`, `generate_flight_plots.py` (eski), `simulation_data/odor_field_3d.py` (eski), `run_detached.sh` → `archive/flight_attempts/`; `scratch_*` → `archive/scratch/`.
- `fly_brain_body_simulation.py`'ye tek satır `import gc`.
- `tests/conftest.py`: 25 eski betik `collect_ignore`'a alınır, `slow` marker tanımlanır.
- CLAUDE.md temas satırı düzeltilir (geom'larda CLAUDE.md değerleri, pair'lerde FlyGym varsayılanı + penetrasyon test gerekçesi).
- Commit.

**1 — Koku alanı.** `tests/flight/test_odor_field_3d.py`:
- kule/platform vokselleri 0;
- maksimum besin vokselinde;
- kule arkasındaki nokta, eşit Öklid mesafeli açık noktadan daha düşük;
- ızgara noktalarında trilineer lookup tam değer;
- ızgara dışı 0;
- ×20 ölçekte kalkış noktasındaki I_asym büyüklüğü raporlanır; zayıfsa ℓ_eff kararı için kullanıcıya sorulur. → **Yapıldı:** zayıf çıktı, ℓ_eff = 10 mm seçildi (bkz. Kontrol).
- Uygulanan koku modeli: 5 mm ızgara (113×105×61), 26-komşulu Dijkstra (scipy csgraph, ~0.4 s), besin için Öklid mesafeli sanal kaynak düğümü, `C = 1/(1+(d/20 mm)²)`. Trilineer lookup'ta bloklu köşeler dışlanır ve ağırlıklar yeniden normalize edilir (duvar dibinde sahte gradyan yok).

**2 — Beyin.** (sonunda DUR, onay bekle) `tests/flight/test_brain.py`:
- slow: tam ağda `len(syn) == 15,091,983` ve Σw == 10,496,512·w_syn;
- grup sayıları 1736 / 408 / 1299 / 2279 / 8025;
- DN root_id → indeks eşlemesi Completeness satırıyla birebir; DNg02 == 25;
- dilimle alt grup seçimi yok (grup indeksleri ardışık 0..N−1 değil);
- artımlı sayım == tam geçmişten sayım (oyuncak ağ);
- dev-subnet çıktı adında "DEV".

**3 — Gövde.** (sonunda DUR, onay bekle) `tests/flight/test_body.py`:
- beyin girdisi olmadan 1 s hover: |Δz| < 0.5 mm;
- 400 mm/s kule çarpması: max penetrasyon < 0.1 mm, BADQACC yok;
- platforma bırakılınca tarsus–platform teması algılanır;
- sabit pitch eğiminde terminal hız 200–400 mm/s aralığında;
- turn_bias > 0 → sağa yaw.

**4 — Kapalı döngü.** Smoke:
- `--n-steps 20 --dev-subnet --no-video` (hızlı);
- `--n-steps 20 --no-video` (tam beyin, cache'li);
- `tests/flight/test_smoke_hdf5.py` şema ve şekilleri doğrular.

- **Uygulama notları (Aşama 4).**
  - Yeni dosyalar: `flight/sensors.py`, `flight/controller.py`, `flight/recorder.py` (BehaviorRecorder + write_h5), `fly_flight_brain_body_simulation.py`, `tests/flight/test_controller.py`, `tests/flight/test_smoke_hdf5.py`. `body.py`'ye eklenenler: `ext_torque`, `snap_at` (qpos), `update_vision()`.
  - **Perch = kalibrasyon.** 10 adım (0.25 s): kanatlar kapalı, sinek kaidede, sensörler ve beyin çalışır. Bu adımlar `/behavior`'a yazılmaz; taban `meta/dn_baseline`'da. `/behavior` takeoff'tan başlar (t = 0.025 s, kalkış anına göre).
  - **Girdiler.**
    - Koku `log10(C/1e-3)/3` → 20–150 Hz (EL YAPIMI normalizasyon); anten örneklemesi Head gövdesinden.
    - Göz: FlyGym ommatidia ortalaması → 20–150 Hz. Her karar adımında `_update_vision` zorlanır.
    - FlyVis T5 yürüyüşteki sabitlerle. `b_loom` FlyVis ağından gelir, FlyWire'dan değil.
  - **SEZ çıkışı.** `brain_mn`: cell_class `brain_motor_neuron` (105; çoğu SEZ proboscis/farenks/anten motor nöronu), root_id eşlemesiyle. Bu grup `--dev-subnet` çekirdeğine de girdiği için DEV alt ağı büyüdü: ≥10 sinaps 52,798; tam 1-hop 98,266 (test güncellendi).
  - **Kolektif.** `lift = clip(1 + pitch_bias, 0.3, 1.8)`, genlik `Φ_hover(tilt)·√lift`.
    - `pitch_alt = −v_z/400 mm/s`. 25 ms ZOH'ta kararlı: τ ≈ 32 ms.
    - Ventral refleks: yalnız cruise'da, altındaki yüzeye < 8 mm. Kalkışta +0.10 lift.
  - **İniş.** Tetik: platformun geometrik açısal yarıçapının genişleme oranı > 5 /s. 300 mm/s'de ~60 mm'ye karşılık gelir. Approach'ta bacaklar açılır; hız fazlasıyla orantılı burun-yukarı frenleme, en fazla 20°. Touchdown için ≥2 tarsus–platform teması 2 ardışık adım sürmeli; ardından kanatlar kapanır, adhezyon açılır ve SEZ 150 Hz'e çıkar.
  - **Maliyet (tam beyin).** Kurulum 9.6 s: beyin + FlyGym görüsü + FlyVis. Adım ~0.96 s: beyin 0.37 s, geri kalanı fizik + render. Tepe RSS 3.46 GB. 160 adım ≈ 2.6 dk.
- **Smoke (Aşama 4, tam beyin, `--n-steps 20 --no-video --tag smoke`, seed 0; düzeltilmiş gövde) → `simulations/flight_v6_smoke_data.h5`.**
  - **Yol.** (−0.4, 0.1, 22.1) → (37.9, 33.3, 66.2) mm, 0.5 s. Yol uzunluğu 77 mm, besine mesafe 471 → 418 mm. Son hız 285 mm/s, v_z +99 mm/s; baş +24.7° (sola).
  - **Gradyanla karşılaştırma.** Koku gradyanının yönü azimut 19–37°, yükselim 23–62°. Gradyan rotası y ≈ 80'de kule 1'in üstünden (z ≈ 200) geçiyor. Sinek azimutu izliyor, ama gradyan rotasından daha yavaş tırmanıyor.
  - **turn_bias paylar (ort. |·| / varyans).**
    - odor %90.3 / %98.3
    - DN %5.3 / %1.2
    - loom %4.4 / %0.4
  - **Birikmiş yaw komutu.** odor +27.3°, DN +0.15°, loom −1.2°; gerçek baş değişimi +24.7°.
  - **ΔDN.** Ortalama −0.007, std 0.087. turn_dn ile turn_odor arasındaki korelasyon −0.31 (20 örnek).
  - **pitch_bias paylar (ort. |·| / varyans).**
    - odor %49 / %15
    - alt %42 / %53
    - takeoff %9 / %31
    - ventral 0
  - **DN ve SEZ okumaları.** DNg02 0/0. steer L/R 2.3 / 0.0 spike/adım. DNp01 0. brain_mn 6.0 Hz.
- **DEV tanı koşusu (80 adım, yalnız tanı, sonuç değil).**
  - Sinek ~1.0 s'de kule 1'in batı yüzüne varıyor (x ≈ 157, z ≈ 118).
  - Koku terimi ±2'de doygunlaşıyor. Bunun nedeni muhtemelen duvar dibinde trilineer lookup'ın bloklu köşeleri dışlaması (gözlem, doğrulanmadı). Sinek yüz boyunca güneye zikzak çizerek tırmanıyor ve 1.9 s'de kulenin güney ucundan (y ≈ −85) üstüne çıkıyor.
  - Temas penetrasyonu en fazla 0.053 mm; besine mesafe 2 s'de 303 mm.

- **Tam koşu v7 (kullanıcı, 160 adım, tam beyin, `simulations/flight_v7_data.h5`).**
  - Sinek kule 1'i güneyden aşıyor, besine 29 mm'ye kadar geliyor. Approach fazında z ≈ 170'te 15–44 mm/s ile asılı kalıyor; touchdown yok. Son adımda turn_odor +1.98.
  - Max kule penetrasyonu 0.033 mm.
- **Kullanıcı kararları (v7 sonrası).** Haltere ω_n = 200 onaylandı. Önce teşhis yapılacak, kazançlara dokunulmayacak; yalnız artefakt ve mantık hataları düzeltilecek. Sineği besine ulaştırmak için ayar yapılmayacak.
- **Teşhis (a): koku örneklemesi.**
  1. **ARTEFAKT: duvar içine düşen anten noktası.** Kule 1 batı yüzündeki zikzağın nedeni bu.
     - Kuleye < 3 mm yaklaşınca ℓ_eff = 10 mm'lik sol örnek noktası kulenin içine düşüyor. Lookup katı içinde 0 döndürdüğü için I_asym = +1.000 ve turn_odor +2 oluyor (v7 adım 39–42 ve 61–63).
     - Sinek duvardan sert sağa kaçıyor, gerçek gradyan onu geri çeviriyor, döngü tekrar ediyor.
     - Aşama 4'teki "bloklu köşe renormalizasyonu" şüphesi yanlıştı. Renormalizasyon katı dışındaki noktalarda doğru çalışıyor; sorun noktanın katının içinde olması.
     - **Düzeltme:** `OdorField3D` kesin geometriyi tutar (`solids`, `inside_solid`, `free_extent`). `antenna_odor` her çift (L/R, U/D) için ℓ = min(ℓ_eff, iki yöndeki serbest mesafe) kullanır; iki taraf aynı ℓ ile örneklenir. Kullanılan ℓ, `ell_LR`/`ell_UD` olarak HDF5'e yazılır.
     - Test: `test_antenna_never_samples_inside_solids`. Batı yüzüne 0.3–9 mm mesafede, 24 yönde max |I_asym| 1.000'den 0.023'e düştü. `test_platform_does_not_zero_the_lower_antenna` aynı hatanın platform silindiri için olanını kapsıyor (D noktası platformun içinde → I_grad = +1).
  2. **ARTEFAKT: gövde-sabit örnekleme ekseni.**
     - U/D ekseni gövdeyle birlikte eğiliyordu, böylece I_grad'a sin(pitch)·(ileri gradyan) karışıyordu. Aynı şekilde yatış da I_asym'e dikey gradyan karıştırıyordu.
     - v7'de seyirde (12° burun-aşağı) gerçek aşağı gradyanı siliyordu: 120. adımda gövde −0.002, yatay çerçeve −0.048. Sinek besin yüksekliğinin ~6 mm üstünde uçtu.
     - 20° burun-yukarı frende işaret dönüyordu (125. adımda −0.188'e karşı −0.075). Approach başındaki 15 mm'lik dalış (v_z −233 mm/s, z 159.7'ye) buradan geliyor.
     - **Düzeltme:** `sensors.gaze_frame`. Örnekleme çerçevesi yalnız gövde yönünü (heading) alır; roll ve pitch çıkarılır. **EL YAPIMI.** Baş/bakış stabilizasyonunun temsilidir (Hengstenberg 1988). Test: `test_gaze_frame_removes_pitch_and_roll_from_odor_sampling`.
  3. **ARTEFAKT DEĞİL: besin yakınındaki turn_odor doygunluğu.**
     - Izgara ile analitik alan `1/(1+(d/20)²)` karşılaştırıldı (d = 29 mm, ℓ = 10). Baş hatası 0–10° için I_asym farkı ≤ 0.007, dönüş terimi farkı ≤ 0.2. Konsantrasyonun 40 mm içindeki göreli hatası medyan −%11: 5 mm ızgara, 26-komşu metrik.
     - Doygunluğun nedeni kontrolcünün kendi kazancı. I_asym ≈ ℓ·|∂lnC/∂d|·sin δ ≈ 0.47·sin δ (d = 29 mm). 2·tanh(20·I) ile bu ~0.25 dönüş/derece demek ve ±7°'de doyuyor.
     - Yaw hızı 5 rad/s/dönüş olduğundan döngü kazancı ~86 /s. 25 ms ZOH ile adım başına ~2.1 → ayrık döngü kararsız; tanh sınırlı bir limit çevrimi var. d küçüldükçe kötüleşir. Yürüyüşteki eşleme aynı; **davranış olduğu gibi bırakıldı.**
     - Gerçek ℓ = 0.5 mm'lik kayıt sütunu (I_asym_real) hücre içi ızgara hatası taşıyor: besin yakınında yön başına sapma ~0.007, gerçek sinyalle aynı mertebede. Yalnız kayıt ve `--antenna-real` ablasyonu için geçerli.
- **Teşhis (b): landing response.**
  - **MANTIK HATASI: tek yönlü fren.** Eski `body_pitch_target("approach")` = −20°·clip((v−40)/100, 0, 1). v < 40 mm/s'de eğim 0 oluyordu: ileri itki yok, sürükleme hızı 0'a indiriyor. v7'de 130. adımdan sonra sinek 29 mm'de asılı kaldı.
  - **Düzeltme:** approach eğimi = ileri besleme θ_ff + aynı fren eğimi (20°/100 mm/s) iki yönde, [−20°, +12°] ile kırpılır.
    - θ_ff = 12°·40/300 = 1.6°, lineer sürüklemeden (seyir kalibrasyonu).
    - Hız, gövde yönündeki yatay bileşen `v_fwd` (HDF5'e yazılır).
    - Yeni kazanç yok. Test: `test_body_pitch_target`.
  - Bacak açma mantığı zaten vardı: approach tetiğinde `stand` pozu.
- **DEV tanı koşusu (160 adım, `flight_v8_DEV_diag`, yalnız tanı, sonuç değil).**
  - Fren sonrası 37–49 mm/s ile ileri yaklaşıyor. Duvar yakınında (41 adım clearance < 10 mm) max |I_asym| 0.11 (v7: 1.000); ℓ_LR en az 0.25 mm. Max penetrasyon 0.032 mm.
  - **Touchdown yine yok.** Sinek r = 10.7 mm'de platformun **yan yüzüne** varıyor ve orada sıkışıyor (kafa, sol kanat, sol orta femur temasta; v = 0; lift 1.72 W).
  - Sebep: koku I_grad'ı thorax'ı damla yüksekliğine (z = 170) götürüyor, açık bacakların tarsusları thorax'ın 1.5–3 mm altında (z 167–168.7), platform üstü 169.5. Hiçbir terim "bacakları kenarın üstüne taşı" demiyor. Ek olarak (3)'teki yan salınım (±50–100 mm/s) sineği kenara yandan sokuyor.
  - Bu bir artefakt ya da mantık hatası değil, **eksik davranış**. Kullanıcı kararı gereği yeni kural eklenmedi. Olası EL YAPIMI ek: approach'ta görsel kenar/yüzey tabanlı "yüzeyin üstünde kal" terimi. Kullanıcıya soruldu.
- **Konnektom katkısı (açıkça).** Dönüşte ~%5 (gürültü), kolektifte %0.
  - v7 tam koşu: turn_dn ort. |·| payı %1.6, varyans payı %0.0, birikmiş yaw komutu −0.6° (koku −149°, loom −19.5°). ΔDN ort. −0.004, std 0.071. turn_odor ile korelasyon −0.07. 20 adımlık smoke'ta pay %5.3.
  - Yön pratikte tamamen el yapımı koku eşlemesinden geliyor.
  - Kolektif: DNg02 v7'de toplam 0 spike. pitch payları koku %57, dikey hız sönümü %41, kalkış %1.5; konnektom %0.
- Sonrası (tam beyin, `--n-steps 20 --no-video --tag smoke` → `flight_v9_smoke_data.h5`): 0.5 s'de (34.1, 40.6, 59.9), 282 mm/s; `pytest tests/` 45 passed, 2 skipped.

**5 — Çıktılar.** Smoke HDF5'ten `render_flight_video.py --max-frames 30` → 1920×1280 kare boyutu doğrulanır; `generate_flight_plots.py` → 13 PNG.

- **Uygulama notları (Aşama 5).**
  - **`render_flight_video.py <h5> [--max-frames N] [--start-frame K] [--out]`** → `simulations/<stem>_video.mp4`, 1920×1280, 30 fps, libx264.
    - Beyin paneli numpy ile rasterize edilir: her nöron 2×2 px; glow tek float32 vektör, τ = 80 ms, `bincount` ile artımlı güncellenir. Renkler: olfactory, LA>ME, ascending, DN, SEZ/brain_mn, diğer.
    - Spike zamanı beyin saatinde; video zamanı = beyin zamanı − 0.25 s kalibrasyon.
    - Alt paneller `mujoco.Renderer` + serbest kamera. Takip kamerası: 8 mm, −18°, yaw alçak geçiren filtreyle. Arena kamerası: güneyden, kuleler uçtan görünür, böylece platform gizlenmez. Sinek işaretçisi ve iz scene geom'dur (yalnız render, fizik yok).
    - Kanatların modelde eklemi yok; kanat gövdelerinin `body_quat`'ı kayıtlı stroke genliğiyle ±Φ/2 döndürülür (**görsel**; görünen frekans 218 Hz değil). Bu, videoda yazılıdır.
    - Her kare `append_data` → `plt.close(fig)`; kare listesi tutulmaz.
    - Maliyet: v7 (480 kare) 49 s, tepe RSS 1.1 GB.
  - **`generate_flight_plots.py <h5> [--ablation h5 ...] [--out]`** → `plots/flight/<stem>/01..13_*.png`.
    - Açık tema kategorik palet sabit sırayla; çift eksen yok. Faz gölgesi: kum = approach, nane = iniş/beslenme.
    - 13. grafik `--ablation` koşularını üst üste çizer.
    - Grafik 4 ve 11 başlıklarında konnektomun kolektife katkısının 0 olduğu yazılıdır.
  - Testler (`test_smoke_hdf5.py`): 6 kare × 1920×1280, HDF5 mtime < mp4 mtime, 13 PNG.
  - Üretilenler: `flight_v9_smoke` ve kullanıcının `flight_v7` koşusu için video + 13 grafik. v7 düzeltmelerden önceki kodla koşuldu; `v_fwd`/`ell_*` sütunları onda yok.

**6 — Betik.** `run_flight_detached.sh`: setsid/nohup, `MUJOCO_GL=egl`, env python, log + `/usr/bin/time -v`. Ablasyon komutları: `--ablate-dn` / `--ablate-odor` / `--antenna-real` ile 160 adım.

**7 — Gözden geçirme.** Subagent diff'i SPEC'e karşı inceler; ardından dosya listesi, komutlar, sınırlamalar teslim edilir.

## 6. Doğrulama / kabul
- **Kullanıcının başlatacağı tam koşu:**
  - dist_to_food genel olarak azalır;
  - tower penetrasyonu < 0.1 mm;
  - platform_contact → feed fazı ve SEZ çıkış oranında artış;
  - HDF5 mtime < mp4 mtime;
  - log'da tepe RSS < 13 GB;
  - 3 panelli video + 13 grafik mevcut.
- **Dürüstlük:**
  - turn/pitch bileşenlerinin ortalama |·| ve varyans payları;
  - ablasyon mesafe–zaman eğrileri (ablate-dn, ablate-odor, antenna-real) tek grafikte;
  - haltere refleksi, landing tetiği, seyir pitch'i ve taban çıkarımı "el yapımı" olarak listelenir.
  - Beklenti baştan yazılır: navigasyonun büyük kısmı koku terimi + el yapımı reflekslerden gelir; DN katkısının küçük olması muhtemel ve öyle raporlanır.
- **Bilinen sınırlamalar:**
  - aero stroke-ortalamalı;
  - kanat görsel;
  - VNC yok;
  - olfactory/SEZ grupları reseptör nöronları;
  - DNa01/DNa02'nin uçuş rolü VARSAYIM;
  - ×20 arena ve ℓ_eff = 10 mm (EL YAPIMI; gerçek ℓ ile karşılaştırma `--antenna-real` koşusunda).
  - Koku alanı statik ve geometrik (adveksiyon/türbülans/plume yok). Formül yürüyüşten farklı: yürüyüşte `500/max(d,1)²`, uçuşta `C = 1/(1+(d/20 mm)²)`. Uzak alanda ikisi de ∝ 1/d²; uçuş formülü tekil maksimum verir ve ×20 ölçeğe uyarlanmıştır.
  - 26-komşulu Dijkstra metriği Öklid mesafesini yöne göre ~%8'e kadar fazla ölçer ve eş-konsantrasyon yüzeylerini çokyüzlüleştirir. Bu yüzden gradyan yönü gerçek yönden ~10–12°'ye kadar sapabilir (ör. kuleler arasında gerçek −6°, ölçülen −17.6°).

---
## Correction note (2026-10-07; the text above is unchanged)
The mention of Hengstenberg (1988) for head/gaze stabilisation (`sensors.gaze_frame`) is related literature only; the paper could not be opened and no constant is taken from it (REPORT.md, THIRD_PARTY.md §6). No code or result changed.
