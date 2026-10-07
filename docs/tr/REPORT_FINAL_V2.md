> **Lab notebook, in Turkish.** Working record of this project, kept as written during the work (moved here from the repository root for the public snapshot). The English consolidated report is [REPORT.md](../../REPORT.md); the English summary is the [README](../../README.md).

# NeuroFly uçuş — final-v2 raporu (sB girdi seti)

FlyWire v783 konnektomu (138.639 nöron, Brian2 LIF, tam beyin, DEV değil) + NeuroMechFly/FlyGym MuJoCo gövdesi, kapalı döngü, 25 ms karar adımı.
Ön kayıt: `SPEC_SENSORY_INPUTS.md` §3.3c (doğrulama koşularından önce yazıldı, commit 5aefc83). Sonuçlar SPEC'e de işlendi (commit 79a6499).
Tablolar `scripts/diag/fv2_report.py` çıktısıdır (davranış tanımları `scripts/verify_report_final.py` ile aynı).

**Final yapılandırma (sB):** `--hybrid --vision-boundary --no-olfaction` + bacak PD rampaları (varsayılan, b075aa9).
- Görme: FlyVis → 32 sınır katmanı tipi (34.121 nöron) → FlyWire (Aşama B).
- Beynin koku girdisi **kapalı**. `--olfaction-full`, `--leg-grn`, `--nt-literature` kapalı.
- DNp15 referansı yeniden ölçüldü: `data/dn_lr_reference_sB.json`.

| koşu | ayar | HDF5 |
|---|---|---|
| final_v2a | sB, `--hybrid --ablate-dn DNp15` | `simulations/flight_v42_hybrid_sB_ablDN-DNp15_noOlf_final_v2a_data.h5` |
| final_v2b | — | **atlandı**: final_v2a zaten ablasyonlu (ön kayıt) |
| final_v2c | sB, yalnız beyin, `--ablate-dn DNp15` | `simulations/flight_v43_sB_ablDN-DNp15_ablOdor_noOlf_final_v2c_data.h5` |
| final_a (v1) | T4/T5, `--hybrid`, DNp15 aktif | `simulations/flight_v11_hybrid_noOlf_final_a_data.h5` |
| final_b (v1) | T4/T5, `--hybrid --ablate-dn DNp15` | `simulations/flight_v12_hybrid_ablDN-DNp15_noOlf_final_b_data.h5` |
| final_c (v1) | T4/T5, yalnız beyin, DNp15 aktif | `simulations/flight_v13_ablOdor_noOlf_final_c_data.h5` |

Hepsi seed 3, 300 adım (7.5 s), `--no-olfaction`, `--no-video`. Final-v1 koşuları bacak rampasından önce yapıldı; final-v2'de rampa açık.
Video bu turda render edilmedi (n1/n2 videoları: §6.6).

## Özet
1. **DNp15 doğrulaması (sB, seed 6/7/8): GEÇMEDİ.**
   - (a) açık döngü optomotor işareti: **12/12 geçti**.
   - (b) hover + ±30° yaw bozulması: **kaldı** (b1 6/6, b2 3/6, b3 3/6).
   - (c) statik sahnelerde |turn| < 0.3: **kaldı, 0/9**.
   - Kural gereği DNp15 terimi bütün final koşularda ablasyonla perch tabanında tutuldu. Başka okuma, kazanç ya da normalizasyon denenmedi.
2. **final_v2a (hibrit): ön-kayıtlı ölçüte göre BAŞARISIZ.** S1 ✗, S2 ✓.
   - Platforma indi (touchdown 3.47 s) ve besledi (162 adım, MN9 ort. 52.2 Hz).
   - Ancak adım 51'de (t = 1.30 s) kule 2'nin üst kenarına adım içinde **130.9 µm** girdi. Adım sonu temas bayrağı 0.
   - Bu, final_a'daki (6.3 µm, adım 52, aynı kulenin üst kenarı) olayla aynı türden ama 20 kat derin.
3. **final_v2c (yalnız beyin): başarısız.** İniş yok; besine en yakın 413.6 mm. Sabit yön terimiyle (+0.244) toplam −532° döndü (daire). Kule teması yok.
4. **Ağ aktivitesi:** aktif nöron oranı final-v1'deki %8–11'den **%29.7 (v2a) / %30.4 (v2c)**'e çıktı. Sürülmeyen nöronlarda %1.4–2.3 → %10.6–11.1.
5. **Beyinden gelen tek davranış kararı yine beslenme (MN9).** Yön terimi sabit. Rota, irtifa, yaklaşma ve iniş HAND.
6. **Ek kontrol (post-hoc, §6):** DNp15 terimi tam 0 + baş refleksi + duruşlarla hibrit n1 **S1 ✓ S2 ✓**; yalnız beyin n2 kuleye çarptı. Bu, ön-kayıtlı final_v2a sonucunu (S1 ✗) değiştirmez.
7. **Çok seed'li tekrar (§6.7, seed 10–14):** n1 5/5 S1 ∧ S2, n2 0/5. Yön terimi 0 olduğu için rota seed'den bağımsız ve beş koşuda aynı; bu bağımsız bir iniş doğrulaması değil. Seed'e bağlı tek sonuç beslenme kararı: temas adımında MN9 5/5 eşiğin üstünde (en düşük 15.7 Hz).
8. **Kalkış konumu / yönü testi (§6.8, ön kayıt §3.3f):** 8 koşulun 8'inde S1 ∧ S2. Rota farklı başlangıçlardan aynı koku hattına yakınsıyor ve kule 2'nin üst kenarını 2.8–5.5 mm marjla geçiyor; yön terimi 0 olduğu için bu el yapımı rotanın dayanıklılığıdır, beynin değil.

## Ne beyinden (BRAIN), ne el yapımından (HAND)?

| davranış bileşeni | final_v2a (hibrit) | final_v2c (yalnız beyin) |
|---|---|---|
| navigasyon | **HAND** koku haritası (`turn_hand`); beynin koku girdisi kapalı | yok |
| yaw | HAND + FLYVIS + **sabit** BRAIN terimi (+0.244, DNp15 ablasyonu) | yalnız **sabit** BRAIN terimi (+0.244) |
| irtifa, kolektif, ileri hız, kalkış, yaklaşma, iniş, bacak açma | **HAND** | VNC programı (el yapımı), irtifa hedefi yok |
| bacak toplama / açma hareketi | HAND PD rampası (75 / 150 ms, VARSAYIM) | aynı |
| haltere refleksi | REFLEX (kaydedilir, komuta eklenmez) | aynı |
| beslenme kararı | **BRAIN**: MN9 > 10 Hz | (temas yok) |
| görsel girdi | FlyVis → 32 sınır tipi → FlyWire (Poisson) | aynı |

- "Sabit BRAIN terimi" bir beyin kararı değildir. Değeri perch'teki DNp15 hızı eksi sB referansıdır: [(0 − 22.1) − (52 − 63.6)] / 42.9 = −0.244 → turn +0.244.
- final_b/final_sB'deki sabit +0.102, eski referansla aynı perch hızlarından geliyordu. Yani v2a ile final_sB arasındaki tek davranışsal fark bu sabitin büyüklüğü: **referans değişince ablasyon sabiti 2.4 katına çıktı.**

## 1. DNp15 yeniden kalibrasyonu (Adım 1)
`scripts/make_dn_reference.py --vision-boundary`: aynı sym_prog uyaranı, 2 s, 250–2000 ms, seed 0/1/2, sınır katmanı üzerinden.

| | eski (T4/T5) L / R Hz | sB L / R Hz |
|---|---|---|
| DNp15 | 15.2 / 63.2 | **22.1 / 63.6** |
| DNa02 (yalnız kayıt) | 31.4 / 2.5 | 17.9 / 16.2 |

Seedler arası fark ≤ 4 Hz. Taban farkı −41.5 Hz, ortak ölçek 42.9 Hz.

## 2. Doğrulama (Adım 2; seed 6/7/8; ölçütler Adım 2 kararlarıyla aynen)

**(a) Açık döngü optomotor işareti: GEÇTİ, 12/12.** turn_bias (+ = sağ), 250–1000 ms:

| koşul | beklenen | s6 / s7 / s8 | ham DNp15 L−R (Hz) |
|---|---|---|---|
| sentetik yaw, dünya CCW | SOL | −2.42 / −2.46 / −2.45 | +72.9 |
| sentetik yaw, dünya CW | SAĞ | +1.71 / +1.61 / +1.69 | −113.2 |
| arena yaw_R | SOL | −0.44 / −0.33 / −0.42 | −24.4 |
| arena yaw_L | SAĞ | +0.87 / +0.88 / +0.93 | −79.8 |

Kayıt: loom_R yanlış yönde (+0.51…+0.61); sym_prog ~0 (referans uyaranı).

**(c) Sabit sapma: KALDI, 0/9.**

| statik sahne | s6 / s7 / s8 | ham DNp15 L−R (Hz) |
|---|---|---|
| perch | +0.40 / +0.46 / +0.33 | −58.5 |
| air_static | +0.37 / +0.40 / +0.34 | −57.5 |
| sym_static | −0.92 / −0.92 / −0.87 | −2.8 |

- Arena statik sahnelerinde DNp15 L ~0, R ~58 Hz. sB referansında L 22 Hz olduğu için bu, eşiğin üstünde sağa sapma olarak okunuyor. T4/T5'le (Adım 2 kararları) perch/hover +0.09…+0.26 idi.
- sym_static'te iki taraf da sessiz; taban çıkarımı bunu sola komut olarak okuyor. Formülün bilinen sorunu.

**(b) Hover + 30° yaw bozulması: KALDI (b1 6/6, b2 3/6, b3 3/6).** `simulations/flight_v30…v41_*_v2val_data.h5`.

| seed | bozulma | Δturn | Δψ normal (°) | Δψ ablasyon (°) |
|---|---|---|---|---|
| 6 / 7 / 8 | +30 (sola) | +0.29 / +0.11 / +0.31 ✓ | +8.8 / −1.5 / −18.6 ✓ | +30.0 |
| 6 / 7 / 8 | −30 (sağa) | +0.20 / +0.03 / +0.29 ✗ | −35.8 / −48.7 / −74.0 ✗ | −30.0 |

- Beyin her iki bozulmada da sağa dönüyor. Sola bozulmayı düzeltiyor, sağa bozulmayı **büyütüyor**. Tek yönlü stabilizasyon; Adım 2 kararlarında (seed 3/4/5) da aynı desen vardı.
- b1 ablasyonda da 6/6 (pasif sönüm).

**Okuma:** DNp15 optomotor işaretini yeni girdide de taşıyor. Ama sağ-baskın tabanı (perch L 0 / R 52 Hz) nedeniyle kapalı döngüde simetrik bir yön kontrolü vermiyor.

## 3. Final koşular: ön-kayıtlı ölçütler ve final-v1 ile yan yana
S1: touchdown'a kadar kule teması yok (adım sonu bayrağı ve adım-içi penetrasyon 0). S2: touchdown'dan sonra en az bir adımda `is_feeding` = 1. Başarı = S1 ∧ S2.

| ölçü | final_v2a | final_v2c | final_a | final_b | final_c | final_sB |
|---|---|---|---|---|---|---|
| touchdown | 3.47 s (adım 138) | yok | 2.87 s (114) | 3.07 s (122) | yok | 3.07 s (122) |
| temas hızı | 5.8 mm/s | — | 6.3 mm/s | 5.8 mm/s | — | 6.7 mm/s |
| kule teması (adım sonu) | 0 | 0 | 0 | 0 | 3 | 0 |
| adım-içi kule (touchdown öncesi) | 1 (adım 51) | 0 | 1 (adım 52) | 0 | 18 | 0 |
| en büyük penetrasyon | 130.9 µm | 0.0 µm | 6.3 µm | 0.0 µm | 43.4 µm | 0.0 µm |
| **S1** | **✗** | ✗ (iniş yok) | ✗ | ✓ | ✗ | ✓ |
| **S2** | **✓** | ✗ | ✓ | ✓ | ✗ | ✓ |
| MN9 ilk > 10 Hz | 3.47 s | — | 2.90 s | 3.07 s | — | 3.07 s |
| beslenme adımı | 162 | 0 | 185 | 178 | 0 | 178 |
| beslenmede ort. MN9 | 52.2 Hz | — | 57.0 Hz | 55.7 Hz | — | 54.4 Hz |
| besine en yakın / son | 3.4 / 3.4 mm | 413.6 / 772.4 mm | 2.0 / 2.0 mm | 1.9 / 1.9 mm | 318.7 / 330.2 mm | 1.9 / 1.9 mm |
| kanatlar açık | 138 | 300 | 114 | 122 | 300 | 122 |
| pay BRAIN | 0.42 | 0.63 | 0.43 | 0.43 | 0.60 | 0.43 |
| pay HAND | 0.32 | 0.00 | 0.28 | 0.31 | 0.00 | 0.31 |
| pay REFLEX | 0.24 | 0.37 | 0.26 | 0.20 | 0.40 | 0.20 |
| pay FLYVIS | 0.03 | 0.00 | 0.03 | 0.06 | 0.00 | 0.06 |
| oran BRAIN/toplam | 1.08 | 1.00 | 0.97 | 1.22 | 1.00 | 1.20 |
| turn_brain | sabit +0.244 | sabit +0.244 | değişken | sabit +0.102 | değişken | sabit +0.102 |
| ort. adım / beyin s | 0.903 / 0.378 | 0.983 / 0.380 | 0.887 / 0.319 | 0.900 / 0.327 | 1.084 / 0.324 | 0.941 / 0.393 |
| tepe RSS | 3.51 GB | 3.51 GB | 3.49 GB | 3.49 GB | 3.49 GB | 3.52 GB |

Notlar:
- final_v2a'nın adım-içi teması kule 2'nin üst kenarında: konum (278.4, 66.6, 200.2) mm, kule 2 x 280–320, y 60–300, üst z 200. final_a'nın teması da aynı kulenin üst kenarındaydı (adım 52). BADQACC yok.
- final_v2a, final_sB'den yalnız ablasyon sabitiyle (+0.244 vs +0.102) ayrılıyor; sB'nin rotası kuleyi ıskalıyordu. Sağa daha büyük sabit sapma rotayı kaydırıp kule kenarına getirdi. Toplam yön değişimi −120° (sB −38°). HAND terimi bunu kısmen karşıladı (turn_hand ort. −0.064, sB −0.019).
- final_v2c'de yön terimi sabit olduğu için sinek daire çiziyor (toplam −532°). final_c'de (DNp15 aktif) −357° ve iki kule temas kümesi vardı. İrtifa 21–29 mm; VNC programında irtifa hedefi yok.
- "pay BRAIN" sabit bir sapmanın payıdır; "oran BRAIN/toplam" pay değildir ve 1'i geçebilir (REPORT_FINAL ile aynı tanım).

### Aktif nöronlar (kapalı döngü, ≥ 1 spike)

| | final_v2a | final_v2c | final_a | final_b | final_c | final_sB |
|---|---|---|---|---|---|---|
| Toplam | 41,148 (%29.68) | 42,200 (%30.44) | 13,140 (%9.48) | 11,162 (%8.05) | 14,769 (%10.65) | 40,527 (%29.23) |
| Sürülen girdi | 29,530 / 34,157 (%86.45) | 31,144 / 34,157 (%91.18) | 10,786 / 11,858 (%90.96) | 9,418 / 11,858 (%79.42) | 11,816 / 11,858 (%99.65) | 29,242 / 34,157 (%85.61) |
| Sürülmeyen | 11,618 / 104,482 (%11.12) | 11,056 / 104,482 (%10.58) | 2,354 / 126,781 (%1.86) | 1,744 / 126,781 (%1.38) | 2,953 / 126,781 (%2.33) | 11,285 / 104,482 (%10.80) |
| Ağ ort. Hz | 7.35 | 7.61 | 1.04 | 0.98 | 1.63 | 7.51 |
| Sürülmeyen ort. Hz | 2.188 | 2.216 | 0.139 | 0.130 | 0.183 | 2.235 |

Artışın çoğu optik lob (ME %40.8 / LO %46.0 aktif, v2a) ve görsel→motor nöropillerinde (ayrıntı REPORT_SENSORY_B). AL (%0.2, 0.02 Hz), LH (%1.0) ve MB_CA (%0) koku girdisi kapalı olduğu için fiilen sessiz.

### Ek kayıt ölçütleri (SPEC §3.3b tanımları)
- **final_v2a:** B-K1 geçti (sürülmeyen 2.188 Hz; son/ilk %25 1.02; en yüksek nöropil UNASGD 38.27 Hz). B-K3 geçti (0.903 s, 3.51 GB). B-K4 geçti (temassız MN9 0.00 Hz, 136 adım). Kesme 100–200 ms 0.000 Hz.
- **final_v2c:** B-K1 geçti (2.216 Hz; 1.03; UNASGD 34.63 Hz). B-K3 geçti (0.983 s, 3.51 GB). B-K4 geçti (0.00 Hz, 300 adım). Kesme 0.000 Hz.

### DN / MN hızları (Hz/nöron, L / R)
- **İniş adayı yok:** DNp07 sB girdisinde her pencerede tonik 60–82 Hz (perch dahil). final-v1'de inişte 0'dı. Her iki durumda da yaklaşma/iniş seçiciliği yok.
  - *Düzeltme notu (2026-10-05):* "60–82 Hz" aralığı eksik. final_v2a'nın tüm pencerelerinde doğru aralık **50.0–82.2 Hz** (iki taraf; en küçük takeoff R 50.0, en büyük approach L 82.2; aşağıdaki pencere tablosu), REPORT.md §4 ile aynı. Nitel sonuç (tonik, iniş seçiciliği yok) değişmiyor.
- **DNp15:** sağ baskın taban sürüyor (perch L 0 / R 52 Hz). Yön terimi ablasyonla sabit olduğu için kayıt.
- **DNp01:** sB'de tonik (perch 28/52 Hz); kalkış zamanlı, DNp01 kararı değil.
- **DNg02:** her koşuda 0. Kolektif ve irtifa beyinden okunamıyor.
- **MN9:** temassız 0; temas sonrası 40–58 Hz.
- **MDN, boyun MN'leri:** ≤ 1.5 Hz.

<details><summary>Pencere tabloları</summary>

**final_v2a** (touchdown adım 138; pencere adım sayıları: perch 10, takeoff 4, cruise 56, approach 55, descend 18, td −4..−1 4, td 0..+3 4, landed 161)

| | perch | takeoff | cruise | approach | descend | td −4..−1 | td 0..+3 | landed |
|---|---|---|---|---|---|---|---|---|
| DNp07 | 72.0 / 76.0 | 60.0 / 50.0 | 77.9 / 69.3 | 82.2 / 81.5 | 80.0 / 66.7 | 80.0 / 60.0 | 60.0 / 60.0 | 74.8 / 65.8 |
| DNp10 | 16.0 / 0.0 | 0.0 / 0.0 | 15.7 / 0.0 | 9.5 / 0.0 | 20.0 / 0.0 | 20.0 / 0.0 | 20.0 / 0.0 | 16.1 / 0.0 |
| DNp15 | 0.0 / 52.0 | 0.0 / 40.0 | 8.6 / 65.0 | 13.8 / 46.5 | 8.9 / 44.4 | 0.0 / 60.0 | 10.0 / 50.0 | 2.5 / 50.2 |
| DNp01 | 28.0 / 52.0 | 30.0 / 30.0 | 25.0 / 58.6 | 21.1 / 57.5 | 17.8 / 46.7 | 30.0 / 60.0 | 10.0 / 60.0 | 15.7 / 32.5 |
| DNa02 | 44.0 / 8.0 | 40.0 / 20.0 | 47.1 / 17.9 | 38.5 / 10.9 | 37.8 / 11.1 | 50.0 / 30.0 | 40.0 / 0.0 | 33.3 / 3.0 |
| MN9 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 40.0 / 40.0 | 47.5 / 58.4 |
| MDN | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| neck MN | 0.0 / 0.6 | 0.8 / 1.5 | 0.4 / 1.3 | 0.2 / 1.0 | 0.5 / 0.5 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.1 |
| DNg02 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |

**final_v2c** (iniş yok; perch 10, takeoff 4, cruise 291)

| | perch | takeoff | cruise |
|---|---|---|---|
| DNp07 | 72.0 / 76.0 | 60.0 / 50.0 | 82.1 / 75.9 |
| DNp10 | 16.0 / 0.0 | 0.0 / 0.0 | 15.1 / 0.0 |
| DNp15 | 0.0 / 52.0 | 0.0 / 40.0 | 10.3 / 70.2 |
| DNp01 | 28.0 / 52.0 | 40.0 / 40.0 | 26.9 / 55.1 |
| DNa02 | 44.0 / 8.0 | 40.0 / 10.0 | 54.2 / 17.0 |
| MN9 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| MDN | 0.0 / 0.0 | 0.0 / 0.0 | 0.6 / 1.2 |
| neck MN | 0.0 / 0.6 | 0.0 / 0.0 | 0.5 / 1.1 |
| DNg02 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |

**final_a** (touchdown adım 114; perch 10, takeoff 4, cruise 52, approach 39, descend 14, td −4..−1 4, td 0..+3 4, landed 185)

| | perch | takeoff | cruise | approach | descend | td −4..−1 | td 0..+3 | landed |
|---|---|---|---|---|---|---|---|---|
| DNp07 | 4.0 / 8.0 | 0.0 / 0.0 | 0.8 / 1.5 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNp10 | 16.0 / 0.0 | 0.0 / 0.0 | 3.8 / 0.0 | 1.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNp15 | 4.0 / 56.0 | 0.0 / 50.0 | 4.6 / 60.8 | 8.2 / 60.5 | 0.0 / 51.4 | 0.0 / 50.0 | 0.0 / 50.0 | 0.0 / 35.9 |
| DNp01 | 0.0 / 4.0 | 0.0 / 0.0 | 1.5 / 2.3 | 2.1 / 6.2 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 10.0 | 0.0 / 0.0 |
| DNa02 | 36.0 / 0.0 | 30.0 / 0.0 | 45.4 / 20.0 | 52.3 / 11.3 | 40.0 / 11.4 | 20.0 / 10.0 | 20.0 / 10.0 | 15.4 / 3.0 |
| MN9 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 30.0 / 30.0 | 50.8 / 64.0 |
| MDN | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| neck MN | 0.0 / 0.0 | 0.0 / 0.0 | 0.2 / 0.8 | 0.6 / 0.9 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNg02 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |

**final_b** (touchdown adım 122; perch 10, takeoff 4, cruise 52, approach 41, descend 20, td −4..−1 4, td 0..+3 4, landed 177)

| | perch | takeoff | cruise | approach | descend | td −4..−1 | td 0..+3 | landed |
|---|---|---|---|---|---|---|---|---|
| DNp07 | 4.0 / 8.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNp10 | 16.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNp15 | 4.0 / 56.0 | 0.0 / 50.0 | 5.4 / 58.5 | 1.0 / 53.7 | 0.0 / 44.0 | 0.0 / 40.0 | 0.0 / 40.0 | 0.0 / 28.5 |
| DNp01 | 0.0 / 4.0 | 0.0 / 0.0 | 0.8 / 2.3 | 1.0 / 1.0 | 0.0 / 2.0 | 0.0 / 10.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNa02 | 36.0 / 0.0 | 30.0 / 0.0 | 53.8 / 16.9 | 42.9 / 9.8 | 52.0 / 10.0 | 60.0 / 10.0 | 20.0 / 0.0 | 19.4 / 1.8 |
| MN9 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 50.0 / 60.0 | 49.3 / 62.6 |
| MDN | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| neck MN | 0.0 / 0.0 | 0.0 / 0.0 | 0.1 / 0.0 | 0.1 / 0.1 | 0.0 / 0.3 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNg02 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |

**final_c** (iniş yok; perch 10, takeoff 4, cruise 291)

| | perch | takeoff | cruise |
|---|---|---|---|
| DNp07 | 4.0 / 8.0 | 0.0 / 0.0 | 3.7 / 8.8 |
| DNp10 | 16.0 / 0.0 | 0.0 / 0.0 | 6.9 / 0.0 |
| DNp15 | 4.0 / 56.0 | 0.0 / 50.0 | 10.2 / 64.2 |
| DNp01 | 0.0 / 4.0 | 0.0 / 0.0 | 4.5 / 8.4 |
| DNa02 | 36.0 / 0.0 | 40.0 / 0.0 | 43.2 / 15.0 |
| MN9 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| MDN | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| neck MN | 0.0 / 0.0 | 0.0 / 0.0 | 0.2 / 0.5 |
| DNg02 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |

final_sB tablosu: REPORT_SENSORY_B.md.
</details>

## 4. Ön-kayıtlı ölçütler: geçti / kaldı

| ölçüt (ön kayıt) | sonuç |
|---|---|
| DNp15 doğrulama (a) optomotor işaret 12/12 | **geçti** (12/12) |
| DNp15 doğrulama (b) b1 ∧ b2 ∧ b3, 6/6 | **kaldı** (6/6, 3/6, 3/6) |
| DNp15 doğrulama (c) statik \|turn\| < 0.3, 9/9 | **kaldı** (0/9) |
| → DNp15 final'de aktif mi? | **hayır**, ablasyonla tabanda (kural) |
| final_v2a S1 (kule teması yok) | **kaldı** (adım-içi 130.9 µm, adım 51) |
| final_v2a S2 (touchdown sonrası beslenme) | **geçti** |
| final_v2c S1 / S2 | **kaldı** (iniş yok) |
| B-K1 / B-K3 / B-K4 (v2a, v2c; kayıt) | geçti |

## 5. Aşama A / A2 olumsuz bulgusu: koku (ayrı bölüm)
Bu bölüm final koşularına girmez; koku girdisi final'de kapalı. Ayrıntı: REPORT_SENSORY_A.md, REPORT_SENSORY_A2.md, SPEC §3.2b–§3.2c, §6.
- **Kalıcı durum:** 53 glomerülün spontan ORN girdisi (Hallem & Carlson 2006) AL'nin LN/PN döngüsünü kendini sürdüren bir duruma sokuyor. Tüm girdiler kesildiğinde ağ sönmüyor: spiking APL'de 3.45 Hz, graded APL'de 1.95 Hz (ölçüt < 0.1 Hz). Yalnız 6 besin glomerülüyle de oluşuyor.
- **Teşhis:** döngü çıkışının %60–73'ü AL LN/PN çekirdeğinde. %27–38'i Codex NT tahmini olmayan ya da düşük güvenli, modelde uyarıcı sayılan nöronlardan. En büyük tek katkıcı lLN1_bc; literatürde kolinerjik, yani modeldeki işaret doğru.
- **`--nt-literature`** (yalnız literatür işaretleri, 24 nöron değişti) kalıcı durumu küçülttü (3.45 → 2.45 Hz; 1.95 → 1.54 Hz) ama kaldırmadı. Dört yapılandırmanın dördü de B-K2'de kaldı. Karar: koku final'de kapalı.
- **Olası eksik mekanizmalar** (hipotez, test edilmedi; SPEC §6 gelecek iş): LN gap junction'ları, ORN/PN/LN adaptasyonu, literatür NT'si olmayan lLN2 / v2LN tipleri.
- **Bacak GRN → MN9 yolu çalışmıyor:** bağlantıyla seçilen 12 SA_VTV_2 nöronu 100 Hz'de MN9'u 0.0 Hz'de bırakıyor (3/3 seed). `--leg-grn` kapalı; gelecek iş.

## 6. Doğallık ve ek kontrol (post-hoc; SPEC §3.3d)
Bu bölüm final_v2a'nın sonucu görüldükten **sonra** eklendi. Ön-kayıtlı sonuç (§3–4: final_v2a S1 ✗, S2 ✓) aynen geçerli. Ölçütler (S1/S2, B-K1/K3/K4, baş refleksi B-H1…H3) koşulardan önce SPEC §3.3d'ye yazıldı (commit 65f05bd).

**Koşular** (seed 3, 300 adım, `--no-video`, tam beyin; `run_natural.sh`; ortak: `--vision-boundary --no-olfaction --dn-reference data/dn_lr_reference_sB.json --no-brain-steer --head-reflex --postures`):

| koşu | ayar | HDF5 |
|---|---|---|
| n1 | `--hybrid` + ortak | `simulations/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_data.h5` |
| n2 | yalnız beyin + ortak | `simulations/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_data.h5` |

Üç değişiklik birlikte açık:
- **`--no-brain-steer`** (ek kontrol): DNp15 dönüş terimi **tam 0**; ablasyonun perch tabanı sabiti (+0.244) de yok. DNp15 okuması kaydediliyor, komuta girmiyor.
- **`--head-reflex`** (HAND refleks, VARSAYIM): boyun eklemleri gövde açısal hızına karşı döner; kazanç yaw 0.6, roll/pitch 0.5; sınır ±15°; yaw'da 9°'de reset sakkadı; izleme 5 ms. Sabitler literatürden (Cellini et al. 2022; Hengstenberg 1988), koşudan önce yazıldı. Gözler başa bağlı, yani FlyVis girdisi baş ile döner. *(Düzeltme notu, 2026-10-05: G_yaw 0.6, ±15° ve 9° sakkad elle seçildi (hand-set; motivated by the fly gaze-stabilisation literature; not traced to a specific source); Cellini et al. 2022 ve Davis & Mongeau 2023 yalnız ilgili literatür. Ayrıntı: SPEC_SENSORY_INPUTS §3.3d düzeltme notu.)*
- **`--postures`** (HAND, VARSAYIM): uçuşta ön bacaklar önde katlı, orta/arka bacaklar geride (eski toplu tuck pozu yerine). Platformda MN9 beslenme kararı açıkken 0.3 s rampayla öne eğik beslenme duruşu.

### 6.1 Davranış: n1, final_v2a, final_sB yan yana (+ yalnız beyin)

| ölçü | **n1** | final_v2a | final_sB | **n2** | final_v2c |
|---|---|---|---|---|---|
| yön terimi (BRAIN) | **0** | sabit +0.244 | sabit +0.102 | **0** | sabit +0.244 |
| touchdown | 3.02 s (adım 120) | 3.47 s (138) | 3.07 s (122) | yok | yok |
| temas hızı | 6.1 mm/s | 5.8 mm/s | 6.7 mm/s | — | — |
| kule teması (adım sonu) | 0 | 0 | 0 | **264** | 0 |
| adım-içi kule (touchdown öncesi) | 0 | 1 | 0 | 264 | 0 |
| en büyük penetrasyon | 0.0 µm | 130.9 µm | 0.0 µm | 35.3 µm | 0.0 µm |
| **S1** | **✓** | ✗ | ✓ | ✗ | ✗ |
| **S2** | **✓** | ✓ | ✓ | ✗ | ✗ |
| MN9 ilk > 10 Hz | 3.02 s | 3.47 s | 3.07 s | — | — |
| beslenme adımı | 180 | 162 | 178 | 0 | 0 |
| beslenmede ort. MN9 | 52.3 Hz | 52.2 Hz | 54.4 Hz | — | — |
| besine en yakın | 0.5 mm | 3.4 mm | 1.9 mm | 324.4 mm | 413.6 mm |
| toplam yön değişimi (kanatlar açık) | +1.7° | −119.9° | −38° | +1.3° | −532° |
| pay HAND / REFLEX / FLYVIS / BRAIN | 0.54 / 0.35 / 0.11 / 0.00 | 0.32 / 0.24 / 0.03 / 0.42 | 0.31 / 0.20 / 0.06 / 0.43 | 0 / 1.00 / 0 / 0 | 0 / 0.37 / 0 / 0.63 |
| aktif nöron (toplam) | %29.02 | %29.68 | %29.23 | %28.12 | %30.44 |
| sürülmeyen aktif / ort. Hz | %10.75 / 2.224 | %11.12 / 2.188 | %10.80 / 2.235 | %8.10 / 1.287 | %10.58 / 2.216 |
| ağ ort. Hz | 7.42 | 7.35 | 7.51 | 4.10 | 7.61 |
| ort. adım / beyin s | 0.894 / 0.376 | 0.903 / 0.378 | 0.941 / 0.393 | 1.454 / 0.366 | 0.983 / 0.380 |
| tepe RSS | 3.51 GB | 3.51 GB | 3.52 GB | 3.52 GB | 3.51 GB |

- **n1 başarılı (S1 ∧ S2).** Rota neredeyse düz (+1.7°); HAND koku haritası ortalamada ~0 dönüş verdi. Kule 2'nin kenarına yaklaşmadı. İnişten hemen sonra MN9 eşiği geçti (3.02 s, touchdown ile aynı adım) ve sinek besine 0.5 mm'de 180 adım besledi.
- **Okuma:** final_v2a'nın S1 başarısızlığı, ablasyonun sabit +0.244 sağ dönüşünün rotayı kule kenarına kaydırmasıyla tutarlı (final_v2a −120°, n1 +1.7°). Ancak n1 üç şeyle birden değişti (yön terimi, baş, duruş), tek seed. Bu yüzden nedeni yalnız yön terimine bağlamak bir **hipotez**, kanıt değil.
- **n1'de beyinden gelen tek davranış kararı beslenme (MN9).** Yön terimi 0. Rota, irtifa, yaklaşma, iniş HAND. Baş ve duruş HAND refleks/duruş. Beslenme duruşunun tetikleyicisi beyin kararı (MN9), duruşun kendisi HAND.
- **n2 (yalnız beyin) başarısız.** Yön komutu 0 ve VNC programında irtifa hedefi yok. Sinek 21–29 mm irtifada düz uçtu, adım 36'da (t ≈ 0.9 s) kule 1'in ön yüzüne çarptı (x = 158.7 mm, yüz x = 160) ve koşu sonuna kadar 264 adım yüze dayalı kaldı (hız 0, penetrasyon ≤ 35 µm, BADQACC yok).
  - Kule yüzüne yakın statik görüntü sınır katmanının hedef hızını yarıya indirdi (§6.3). Ağ 4.10 Hz'e düştü.
  - Temas çözümü adımı 1.45 s'ye uzattı (B-K3 sınırı 2.0 s içinde).
  - final_v2c sabit sağ dönüşle daire çiziyordu ve kuleye değmiyordu. n2'de bu sabitin kalkması kuleye çarpmayı açığa çıkardı. Yalnız-beyin kolunda yön/irtifa kontrolü yok.

### 6.2 Ön-kayıtlı ölçütler (SPEC §3.3d)

| ölçüt | n1 | n2 |
|---|---|---|
| S1 (touchdown'a kadar kule teması yok) | **geçti** | kaldı (iniş yok, 264 temas adımı) |
| S2 (touchdown sonrası beslenme) | **geçti** | kaldı |
| B-K1 (sürülmeyen < 5 Hz; son/ilk ≤ 1.5; nöropil ≤ 50 Hz) | geçti (2.224 Hz; 1.04; UNASGD 23.07 Hz) | geçti (1.287 Hz; 0.72; UNASGD 38.87 Hz) |
| B-K3 (adım ≤ 2.0 s, RSS ≤ 8 GB) | geçti (0.894 s, 3.51 GB) | geçti (1.454 s, 3.52 GB) |
| B-K4 (temassız MN9 < 10 Hz) | geçti (0.00 Hz, 118 adım) | geçti (0.00 Hz, 300 adım) |
| B-H1 (BADQACC yok) | geçti (0) | geçti (0) |
| B-H2 (\|θ_baş\| ≤ 15°) | geçti (en büyük yaw/pitch/roll 7.3 / 4.5 / 2.3°) | geçti (2.9 / 4.7 / 1.5°) |
| B-H3 (dönüş alt adımlarının > %50'sinde \|bakış yaw\| < \|gövde yaw\|) | geçti (3,240 / 3,247 = %99.8) | geçti (553 / 575 = %96.2) |

Kesme penceresi (100–200 ms) her iki koşuda 0.000 Hz.

### 6.3 Baş refleksi: görsel girdiye ve DN'lere etkisi
**Baş hareketi (n1, kanatlar açık 120 adım):**
- Yaw medyan |θ| 0.3°, %95'lik 5.9°, en büyük 7.3°.
- Yaw reset sakkadı hiç olmadı (9° eşiğine ulaşılmadı): rota neredeyse düz, dönüşler kısa.
- Ortalama |bakış yaw hızı| 0.224 rad/s, |gövde yaw hızı| 0.283 rad/s. Dönüş alt adımlarında bakış neredeyse her zaman gövdeden yavaş (%99.8).
- n2'de baş fiilen hareketsiz (yaw %95'lik 0.1°), çünkü yön komutu 0. Temas sırasındaki kısa dönüşlerde %96.2.

**Görsel girdi** (sınır katmanı FlyVis hedef hızı, kanatlar açık adımların ortalaması, Hz):

| | n1 | final_v2a | final_sB | n2 | final_v2c |
|---|---|---|---|---|---|
| ort. L / R | 23.02 / 22.60 | 23.95 / 21.10 | 23.69 / 22.11 | 11.63 / 12.61 | 22.55 / 22.90 |
| tip başına ort. \|L−R\| | 2.99 | 4.66 | 3.59 | 1.84 | 4.46 |
| T4/T5 L / R | 10.32 / 9.90 | 10.56 / 9.77 | 10.58 / 10.06 | 8.27 / 9.48 | 13.40 / 14.09 |

- n1'de iki göz arası fark en düşük (2.99 Hz; v2a 4.66, sB 3.59). Bu, baş stabilizasyonunun yaw optik akışını azaltmasıyla **tutarlı**.
- Ama n1'in rotası da çok daha düz (+1.7° vs −120° / −38°). Daha az gövde dönüşü de aynı farkı üretir. **İki etki bu koşulardan ayrıştırılamaz** (SPEC §3.3d'de önceden yazıldı). Yalnız baş refleksini açıp kapatan eşleşmiş bir kontrol yapılmadı.
- n2'deki düşük girdi (11.6 / 12.6 Hz) baştan değil, kule yüzüne dayalı statik görüntüden.

**DN'ler** (Hz/nöron, L / R; tam tablolar `scripts/diag/nat_report.py`):

| | n1 seyir | final_v2a seyir | n1 yaklaşma | final_v2a yaklaşma | n1 alçalma | final_v2a alçalma |
|---|---|---|---|---|---|---|
| DNp15 | 8.5 / 62.3 | 8.6 / 65.0 | 3.1 / 69.7 | 13.8 / 46.5 | 8.0 / 64.0 | 8.9 / 44.4 |
| DNa02 | 47.7 / 17.7 | 47.1 / 17.9 | 43.1 / 9.2 | 38.5 / 10.9 | 46.0 / 10.0 | 37.8 / 11.1 |
| DNp01 | 26.2 / 50.8 | 25.0 / 58.6 | 30.8 / 61.5 | 21.1 / 57.5 | 36.0 / 66.0 | 17.8 / 46.7 |
| DNp07 | 82.3 / 71.5 | 77.9 / 69.3 | 82.1 / 75.9 | 82.2 / 81.5 | 76.0 / 76.0 | 80.0 / 66.7 |
| boyun MN | 0.5 / 1.5 | 0.4 / 1.3 | 0.1 / 0.3 | 0.2 / 1.0 | 0.2 / 0.8 | 0.5 / 0.5 |

- **Nitel tablo değişmedi.** DNp15 sağ-baskın tonik (perch L 0 / R 52 Hz, n1 ve v2a'da aynı, çünkü perch'te baş hareketsiz). DNp07 tonik 60–82 Hz, iniş seçiciliği yok. DNg02 0. MDN ≤ 1 Hz.
  - *Düzeltme notu (2026-10-05):* DNp07 için doğru aralık **50.0–82.2 Hz** (final_v2a, tüm pencereler; §3 pencere tablosu), REPORT.md §4 ile aynı. Bu tablodaki n1 değerleri de 82 Hz civarında (en büyük n1 seyir L 82.3 Hz). Nitel sonuç değişmiyor.
- Boyun MN'leri n1'de de ≤ 1.5 Hz (n2 seyirde R 3.2 Hz). Baş refleksi HAND; beynin boyun MN'lerine bağlanmadı. Beyin bu refleksi "üretmiyor".
- Yaklaşma/alçalmada DNp01 n1'de daha yüksek (30.8/61.5, 36.0/66.0 vs 21.1/57.5, 17.8/46.7), DNp15 L yaklaşmada daha düşük. Rota, baş ve süre farkı birlikte değiştiği için nedensel yorum yapılmıyor. Kayıt.

### 6.4 Duruşlar
- **n1:** 60 adım uçuş duruşu, 60 adım stand (kalkıştan önceki ilk adım + yaklaşma/alçalmadaki açılma), 180 adım beslenme duruşu.
  - Platformda MN9 touchdown adımında eşiği geçti. Bu yüzden bacaklar stand'da beklemeden 0.3 s rampayla beslenme duruşuna geçti ve koşu sonuna kadar orada kaldı (poz değişimi 0, beslenme kesintisiz).
  - Beslenmede gövde pitch'i ort. **+6.9°** burun aşağı (kaide üzerinde önceden ölçülen +5.7°).
  - "İniş sonrası doğal durma duruşu": açılma rampası FlyGym'in durma duruşuna gidiyor, touchdown'da poz atlaması yok. Ancak bu koşuda platformda beslenmesiz bekleme olmadığı için stand duruşu platformda gözlenmedi.
- **n2:** 299 adım uçuş duruşu; kule yüzüne dayalıyken de kanatlar açık, bacaklar uçuş duruşunda.
- Duruşlar yalnız görünüm/temas geometrisini değiştiriyor; aerodinamik model bacak pozundan bağımsız.

### 6.5 Sınırlamalar (bu bölüm)
- **Post-hoc:** `--no-brain-steer` final_v2a görüldükten sonra eklendi. n1'in başarısı ön-kayıtlı final ölçütünün yerine geçmez.
- **Tek seed (3).** n1 ile final_v2a üç değişiklikle ayrılıyor; baş refleksinin ve duruşların davranışa katkısı ayrıştırılmadı.
- **Baş refleksi tamamen HAND.** Kazanç, sınır ve reset eşiği literatürden; τ_rc ve pitch kazancı VARSAYIM. Pasif boyun yayı nedeniyle DC izleme 0.95.
- **Uçuş duruşu nitel bir tarif.** Drosophila uçuşunda bacak açısı ölçümü bulunamadı. Beslenme eğimi ve rampa süresi VARSAYIM.
- Videolar bu koşulardan sonra yalnız render ile üretildi (§6.6); simülasyon yeniden koşulmadı.

Yeniden üretim: `nohup bash run_natural.sh > logs/natural/nohup.out 2>&1 &` (n1 6.3 dk, n2 9.1 dk, kurulum dahil); tablolar `env -u PYTHONPATH python scripts/diag/nat_report.py`.

### 6.6 Videolar (yalnız render)
`render_flight_video_v2.py` n1/n2 için güncellendi; başlatma `run_videos_natural.sh` (üç video paralel, `logs/video_v2n/DONE_video_*`). Son render (yumuşak nokta beyin paneli, ekran yazıları İngilizce): `run_videos_vis.sh` (`logs/video_vis/DONE_video_*`); dosyaları tablonun son üç satırı. Kodlama: H.264, yuv420p, sabit 1 s anahtar kare aralığı (`-g 30`, sahne kesmesinde ek anahtar kare yok), `+faststart` (moov dosyanın başında). Sayılar ffprobe ile ölçüldü.

| video | dosya | süre | kare | fps | anahtar kare aralığı | çözünürlük | piksel |
|---|---|---|---|---|---|---|---|
| n1 | `simulations/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change.mp4` | 33.60 s | 1008 | 30 | 30 kare (1 s) | 1920×1080 | yuv420p |
| n2 | `simulations/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change.mp4` | 44.00 s | 1320 | 30 | 30 kare (1 s) | 1920×1080 | yuv420p |
| n1 \| n2 | `simulations/flight_n1_vs_n2_v2_compare.mp4` | 33.60 s | 1008 | 30 | 30 kare (1 s) | 1920×1080 | yuv420p |
| n1 (yumuşak nokta) | `simulations/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_v2_change_en_vis.mp4` | 33.60 s | 1008 | 30 | 30 kare (1 s) | 1920×1080 | yuv420p |
| n2 (yumuşak nokta) | `simulations/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2_v2_change_en_vis.mp4` | 44.00 s | 1320 | 30 | 30 kare (1 s) | 1920×1080 | yuv420p |
| n1 \| n2 (yumuşak nokta) | `simulations/flight_n1_vs_n2_v2_compare_en_vis.mp4` | 33.60 s | 1008 | 30 | 30 kare (1 s) | 1920×1080 | yuv420p |

- Kartlar: başlık 6 s, bitiş 8 s (render turu 7e593fc; ilk sürüm 3 s / 4 s). Oynatma ×0.25. n1'de beslenme başladıktan 1 s sonra her 4. kare gösteriliyor (×1.0, ekranda etiketli). n2'nin tamamı ×0.25. Karşılaştırma videosu n1'in zamanlamasını iki tarafa da uyguluyor; iki koşunun render saatleri aynı.
- **Beyin panelleri:** simüle edilen spike katmanı sınıf renkleriyle, değişim modunda çiziliyor (τ = 80 ms). Çizim ve parlaklık bir **görüntü ayarıdır, ölçüm değildir.**
  - **Yumuşak nokta çizimi** (`run_videos_vis.sh`, `*_en_vis.mp4`): her nöron, tüm sınıflarda **aynı boyutta** tek yumuşak nokta (Gauss, σ 0.7 px; panel 2× çözünürlükte çizilip küçültülüyor; konum = sinaps ağırlık merkezi). Noktalar toplamalı birikiyor; en parlak kanalda ton eşleme (1 − e^−x)^γ, γ 0.6, renk tonu korunuyor; çok parlak çekirdekler hafifçe beyaza kayıyor; hafif ışıma (bulanıklık σ 5 px, ağırlık 0.22). Sessiz nöronlar sönük gri-mavi taban bulutu olarak her karede görünüyor (kameradan uzak olanlar daha sönük).
  - **Sınıf başına sabit kazanç** (koşu başına bir kez, koşu boyunca sabit): kalabalık sınıflarda 40 karedeki yalnız-sınıf pozlamasının %99.5'lik değeri bir düzeye eşleniyor (visual %80, other %70). Küçük sınıflarda (taste, DN, motor, olfactory) kazanç 3 / (aktif nöronlarının medyan yoğunluğu): tipik ateşleyen nöron tam parlaklığa yakın. Böylece kalabalık görsel sınıf küçük devreleri bastırmıyor. Ekranda: "display gain per class (fixed); dot size equal for all neurons".
  - Önceki çizim (tablodaki `run_videos_natural.sh` videoları ve `*_en.mp4`): tek ortak kazanç, 40 karedeki pozlamanın %99.5'lik değeri beyaza doğru %70'e; noktasız yumuşak parlama. Eski sabit ölçek, %29 aktif nöronla optik lobları doyuruyordu.
  - **FlyVis katmanı ayrı:** `/flyvis` aktivitesi, eşlenen FlyWire nöronlarının konumlarında limon yeşiliyle ve alfa karışımıyla çiziliyor. Spike katmanına eklenmiyor. Kapsam: 34 sürülmeyen FlyVis tipi, 19.156 FlyWire nöronu; |a−a0| / koşu p99. Lejantta "FlyVis (gösterim, sürülmez)" yazıyor. Simülasyona girdi değil.
- **Devre şeridi:** göz (FlyVis hedef hızı, sınır nöronları ortalaması) → sınır katmanı (32 tip, 34.121 nöron; simüle spike ort. Hz) → LO/LOP/ME (sürülmeyen) → DNp15 L/R.
  - DNp15 kesikli kutuda "kayıt, komuta girmez". VNC köprüsü sönük, "yön terimi 0".
  - Şeker GRN → SEZ → MN9 → beslenme. Koku zinciri sönük, "beyin koku girdisi KAPALI".
  - HAND kutuları: baş yaw açısı (`head_q`) ve bacak duruşu (`leg_pose`).
- **Kalıcı etiket** HDF5 bayraklarından:
  - n1: "Yön bulma, irtifa, iniş, baş, duruş: EL YAPIMI · Beyin: beslenme kararı (MN9)".
  - n2: "Yön bulma: YOK (yön terimi 0) · Uçuş programı (irtifa hedefi yok), baş, duruş: EL YAPIMI · Beyin: beslenme kararı (MN9)".
- **Baş ve duruş replay'de:** `render/qpos` boyun eklemlerini içeriyor. n1 replay'inde en büyük |yaw| 7.30°, kayıtlı `head_q` ile aynı.
  - Baş hareketi küçük (yaw %95'lik 5.9°). Bu yüzden takip kamerasında gözle zor seçiliyor; açı devre şeridinde sayı olarak gösteriliyor.
  - Uçuş ve beslenme duruşları kamerada görünüyor. Takip kamerasının açısı faza göre değişiyor (7e593fc): seyirde arka-yan üç çeyrek, yaklaşma/alçalmada yandan, temas ve beslenmede önden-yan yakın plan; geçişler 0.5 s rampa. Beslenmede öne eğilme ve turuncu hortum işareti (yalnız görsel) bu açıdan görünüyor.
- Kanat bulanıklığı ve ×4 beslenme hızlandırması değişmedi. Yalnız kamera render'ında: besin damlası yarı saydam sarı, besin platformu orta gri (simülasyonda ve gözlerin/FlyVis'in gördüğü renk koyu).
- Karşılaştırma videosu (7e593fc): her yarıda büyük takip kamerası, arena + 3D iz, büyük puntolu faz / besine uzaklık / MN9 satırları ve küçük önden beyin paneli.
- **Bitiş kartı (n1):**
  - n1 sonuçları.
  - Karşılaştırma satırları: ön-kayıtlı final_v2a (S1 ✗) ve n2.
  - "DNp15 yön okuması doğrulamayı geçmedi (a 12/12, b ✗, c ✗)" ve "koku: AL kalıcı durumu, final'de kapalı".
  - DOI'li atıflar ve FlyWire CC BY-NC 4.0 notu.
  - Baş refleksi sabitlerinin künyeleri DOI'siz (SPEC §3.3d'deki gibi).

**Kareler:**
- Anahtar kareler (n1): `plots/flight/v2_keyframes/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1_change_{kalkis_t0.13,kule_t1.45,inis_t3.02,beslenme_t3.52}.png`, kartlar `..._n1_{title,end}_card.png`.
- Video kareleri (her videodan 3): `plots/flight/v2_video_frames/<video>_at{8,15.5,24}s.png` (n1, karşılaştırma) ve `_at{8,20,35}s.png` (n2). Anahtar kareler ve bu video kareleri ilk render turundan; 7e593fc'deki kamera/düzen değişikliğinden sonra yeniden üretilmedi.
- Grafikler (`generate_flight_plots.py --extra`, 15'er): `plots/flight/flight_v44_hybrid_sB_noBrSteer_head_pose_noOlf_n1/`, `plots/flight/flight_v45_sB_noBrSteer_head_pose_ablOdor_noOlf_n2/`.

**Kayıt (hata):** n1/n2 HDF5'lerinde `/flyvis/step_idx` yok.
- Neden: simülasyonda `display.close()` yanlış girintideydi ve yalnız `--olfaction-full` açıkken çağrılıyordu. Kod düzeltildi; mevcut HDF5'ler değiştirilmedi.
- Render satır → adım eşlemesini `satır = adım + 18` olarak kuruyor (10 kalibrasyon + 8 girdi kesme adımı; spike `step_idx` en küçüğü −18). Satır sayısı 318 = 300 + 18; render bunu assert ile denetliyor.

Yeniden üretim: `nohup bash run_videos_natural.sh > logs/video_v2n/nohup.out 2>&1 &`; anahtar kareler `render_flight_video_v2.py <n1 h5> --keyframes auto --cards`.

### 6.7 Çok seed'li tekrar (SPEC §3.3e)
Ön kayıt: SPEC §3.3e, koşulardan önce yazıldı (commit 1b48395). n1 ve n2 yapılandırmaları **aynen**; yalnız `--seed` (10–14) ve `--tag` değişti (`run_seeds.sh`, `logs/seeds/DONE_*`). Tablo `scripts/diag/seeds_report.py` çıktısıdır; seed 3 satırları §6.1'deki koşulardır.

| koşu | seed | S1 | S2 | touchdown adımı | MN9 temas adımında (Hz) | ilk beslenme adımı | beslenme adımı | beslenmede MN9 ort. / en düşük (Hz) | kule teması (adım sonu) | adım-içi kule (td öncesi) | BADQACC |
|---|---|---|---|---|---|---|---|---|---|---|---|
| n1 | 3 (§3.3d) | ✓ | ✓ | 120 | 15.7 | 120 | 180 | 52.3 / 15.7 | 0 | 0 | 0 |
| n1 | 10 | ✓ | ✓ | 120 | 47.2 | 120 | 180 | 51.6 / 18.1 | 0 | 0 | 0 |
| n1 | 11 | ✓ | ✓ | 120 | 15.7 | 120 | 180 | 52.8 / 15.7 | 0 | 0 | 0 |
| n1 | 12 | ✓ | ✓ | 120 | 31.5 | 120 | 180 | 52.2 / 21.6 | 0 | 0 | 0 |
| n1 | 13 | ✓ | ✓ | 120 | 31.5 | 120 | 180 | 51.9 / 19.2 | 0 | 0 | 0 |
| n1 | 14 | ✓ | ✓ | 120 | 15.7 | 120 | 180 | 51.8 / 15.3 | 0 | 0 | 0 |
| n2 | 3 (§3.3d) | ✗ | ✗ | yok | — | — | 0 | — / — | 264 | 264 | 0 |
| n2 | 10 | ✗ | ✗ | yok | — | — | 0 | — / — | 264 | 264 | 0 |
| n2 | 11 | ✗ | ✗ | yok | — | — | 0 | — / — | 264 | 264 | 0 |
| n2 | 12 | ✗ | ✗ | yok | — | — | 0 | — / — | 264 | 264 | 0 |
| n2 | 13 | ✗ | ✗ | yok | — | — | 0 | — / — | 264 | 264 | 0 |
| n2 | 14 | ✗ | ✗ | yok | — | — | 0 | — / — | 264 | 264 | 0 |

- **n1** (seed 10–14): S1 ∧ S2 5/5; temas adımında MN9 > 10 Hz: 5/5, en düşük 15.7 Hz, en yüksek 47.2 Hz.
- **n2** (seed 10–14): S1 ∧ S2 0/5; touchdown yok (MN9 temas ölçüsü uygulanamaz).

**Belirlenimcilik** (seed 10–14 vs seed 3, aynı kol, tüm adımlar; en büyük |fark|):
- **n1**: pos 0, heading 0, turn_total 0, phase 0, is_feeding 0, tower_contact 0, leg_pose 0
- **n2**: pos 0, heading 0, turn_total 0, phase 0, is_feeding 0, tower_contact 0, leg_pose 0

B-K1 / B-K3 / B-K4 (kayıt; tanımlar §3.3b):
- **n1**: B-K1 ∧ B-K3 ∧ B-K4 5/5; sürülmeyen 2.225–2.227 Hz, adım 0.912–0.925 s, temassız MN9 0.00–0.00 Hz.
- **n2**: B-K1 ∧ B-K3 ∧ B-K4 5/5; sürülmeyen 1.289–1.292 Hz, adım 1.473–1.493 s, temassız MN9 0.00–0.00 Hz.

**Okuma (dürüst sayım):**
- **Rota seed'den bağımsız ve deterministik.** `--no-brain-steer` ile yön terimi 0. Gövdeye beyinden giden tek yol MN9 beslenme kararı; bu karar da yalnız touchdown'dan sonra devreye giriyor. Rota, irtifa, iniş HAND + fizik. Bu yüzden n1'in beş koşusunda konum, touchdown adımı (120) ve kule değerleri (0) bit düzeyinde aynı; n2'nin beş koşusunda da kule 1'e çarpma (264 temas adımı) aynı.
- **Dolayısıyla iniş ve kule sonucu (S1) 5 bağımsız doğrulama DEĞİL.** Aynı el yapımı rotanın beş kez tekrarıdır. "S1 5/5" seed sağlamlığı göstermez; rota sağlamlığı ayrı bir testle (§3.3f kalkış konumu/yönü) ölçülüyor.
- **Seed'e bağlı tek sonuç beslenme kararı (MN9).** Beyindeki Poisson girdisi seed'le değişiyor; MN9 değerleri koşudan koşuya farklı. Temas adımında (120) MN9 beş seed'in **beşinde** 10 Hz eşiğini geçti; en düşük **15.7 Hz** (seed 11 ve 14; seed 3'te de 15.7 Hz), en yüksek 47.2 Hz (seed 10). Beslenme boyunca MN9 hiç eşiğin altına inmedi (en düşük 15.3 Hz, seed 14), bu yüzden beslenme adım sayısı (180) ve duruş dizisi de her seed'de aynı.
- MN9 değerlerinin kademeli olması (15.7 / 31.5 / 47.2 Hz) okumanın az sayıda nöronda 50 ms penceresinde spike saymasından. En düşük değer eşiğin 1.6 katı; eşiğe yakın bir seed görülmedi, ama 5 seed bu kararın hata oranı için küçük bir örneklem.
- n2'de (yalnız beyin) temas olmadığı için MN9 temas ölçüsü uygulanamaz; S2 0/5 rotadan kaynaklanıyor.

### 6.8 Kalkış konumu / yönü testi (SPEC §3.3f)
Ön kayıt: SPEC §3.3f, koşulardan önce yazıldı (commit 256d072; bayraklar 976812a). n1 yapılandırması **aynen** (seed 3, `--hybrid`, §3.3d ortak bayrakları); yalnız `--start-offset` / `--start-yaw` ve `--tag` değişti (`run_starts.sh`, `logs/starts/DONE_*`; 8 koşu, her biri 6.3–6.6 dk, hepsi exit 0, teknik tekrar yok). Kalkış kaidesi sinekle birlikte taşındı (koku alanı engeli dahil). Tablo `scripts/diag/starts_report.py` çıktısıdır; n1 satırı §6.1'deki koşudur. "İlk beslenme adımı", "kuleye en yakın" ve yakınsama satırları kayıttır, ölçüt değil.

| koşul | bayrak | S1 | S2 | touchdown (adım / s) | MN9 temas adımında (Hz) | ilk beslenme adımı | beslenme adımı | besine en yakın | toplam yön değişimi | kuleye en yakın (td öncesi) | kule teması (adım sonu) | adım-içi kule (td öncesi) | en büyük penetrasyon | BADQACC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n1 | — (§3.3d n1) | ✓ | ✓ | 120 / 3.02 s | 15.7 | 120 | 180 | 0.5 mm | +1.7° | 4.4 mm | 0 | 0 | 0.0 µm | 0 |
| st_xp40 | `--start-offset 40 0` | ✓ | ✓ | 115 / 2.90 s | 0.0 | 116 | 184 | 0.5 mm | +1.6° | 4.7 mm | 0 | 0 | 0.0 µm | 0 |
| st_xm40 | `--start-offset -40 0` | ✓ | ✓ | 125 / 3.15 s | 23.6 | 125 | 175 | 0.5 mm | +1.9° | 4.1 mm | 0 | 0 | 0.0 µm | 0 |
| st_yp40 | `--start-offset 0 40` | ✓ | ✓ | 119 / 3.00 s | 0.0 | 120 | 180 | 0.4 mm | +1.7° | 4.0 mm | 0 | 0 | 0.0 µm | 0 |
| st_ym40 | `--start-offset 0 -40` | ✓ | ✓ | 121 / 3.05 s | 15.7 | 121 | 179 | 0.5 mm | +1.6° | 4.6 mm | 0 | 0 | 0.0 µm | 0 |
| st_yawp30 | `--start-yaw 30` | ✓ | ✓ | 120 / 3.02 s | 31.5 | 120 | 180 | 0.5 mm | -25.8° | 5.4 mm | 0 | 0 | 0.0 µm | 0 |
| st_yawm30 | `--start-yaw -30` | ✓ | ✓ | 118 / 2.97 s | 15.7 | 118 | 182 | 0.5 mm | +30.8° | 5.5 mm | 0 | 0 | 0.0 µm | 0 |
| st_yawp60 | `--start-yaw 60` | ✓ | ✓ | 116 / 2.92 s | 23.6 | 116 | 184 | 0.5 mm | -57.0° | 3.3 mm | 0 | 0 | 0.0 µm | 0 |
| st_yawm60 | `--start-yaw -60` | ✓ | ✓ | 114 / 2.87 s | 0.0 | 115 | 185 | 0.3 mm | +62.2° | 2.8 mm | 0 | 0 | 0.0 µm | 0 |

- **S1 ∧ S2: 8/8 koşulda geçti**.
- S1 8/8, S2 8/8; touchdown 8/8; temas adımında MN9 > 10 Hz: 5/8 (en düşük 0.0 Hz).
- touchdown → ilk beslenme: 0–1 adım; kuleye en yakın (td öncesi): 2.8–5.5 mm (n1 4.4 mm).
- rota yakınsaması (kayıt): yön, n1'in 5° içine t = 1.02–1.42 s'de giriyor ve adım 60'a kadar kalıyor; t = 1.32 s'de n1 rotasından |Δy| 0.2–5.2 mm.

**Başlangıç** (adım 0, kayıt; girdi kesme adımlarından sonra):
- n1: (-0.2, 0.1) mm, +1.6°
- st_xp40: (39.8, 0.1) mm, +1.8°
- st_xm40: (-40.2, 0.1) mm, +1.6°
- st_yp40: (-0.2, 40.1) mm, +1.8°
- st_ym40: (-0.2, -39.9) mm, +1.5°
- st_yawp30: (-0.2, -0.1) mm, +29.4°
- st_yawm30: (-0.1, 0.3) mm, -27.0°
- st_yawp60: (-0.1, -0.2) mm, +60.1°
- st_yawm60: (0.1, 0.3) mm, -58.8°

**Kuleye en yakın nokta** (touchdown öncesi, gövde merkezi; kayıt):
- n1: 4.4 mm, kule 2, t = 1.45 s, (322.2, 80.2, 203.8) mm
- st_xp40: 4.7 mm, kule 2, t = 1.32 s, (322.6, 80.2, 203.9) mm
- st_xm40: 4.1 mm, kule 2, t = 1.57 s, (321.7, 80.2, 203.7) mm
- st_yp40: 4.0 mm, kule 2, t = 1.42 s, (321.6, 80.0, 203.6) mm
- st_ym40: 4.6 mm, kule 2, t = 1.32 s, (278.1, 75.2, 204.1) mm
- st_yawp30: 5.4 mm, kule 2, t = 1.30 s, (279.0, 80.0, 205.3) mm
- st_yawm30: 5.5 mm, kule 2, t = 1.37 s, (316.6, 80.0, 205.5) mm
- st_yawp60: 3.3 mm, kule 2, t = 1.37 s, (319.7, 79.7, 203.3) mm
- st_yawm60: 2.8 mm, kule 2, t = 1.27 s, (317.8, 79.8, 202.8) mm

**Kayıt ölçütleri:** B-K1 ∧ B-K3 ∧ B-K4 8/8; B-H1 ∧ B-H2 ∧ B-H3 8/8.
- **st_xp40**: B-K1 geçti (sürülmeyen 2.232 Hz, son/ilk %25 1.03, en yüksek nöropil UNASGD 22.87 Hz); B-K3 geçti (adım 0.932 s, RSS 3.51 GB); B-K4 geçti (temassız MN9 0.00 Hz, 113 adım; perch 0.00 Hz); kesme 100–200 ms 0.000 Hz; B-H1 geçti, B-H2 geçti, B-H3 geçti (4,134 / 4,134).
- **st_xm40**: B-K1 geçti (sürülmeyen 2.228 Hz, son/ilk %25 1.05, en yüksek nöropil UNASGD 23.40 Hz); B-K3 geçti (adım 0.903 s, RSS 3.51 GB); B-K4 geçti (temassız MN9 0.00 Hz, 123 adım; perch 0.00 Hz); kesme 100–200 ms 0.000 Hz; B-H1 geçti, B-H2 geçti, B-H3 geçti (3,085 / 3,112).
- **st_yp40**: B-K1 geçti (sürülmeyen 2.227 Hz, son/ilk %25 1.04, en yüksek nöropil UNASGD 23.00 Hz); B-K3 geçti (adım 0.905 s, RSS 3.52 GB); B-K4 geçti (temassız MN9 0.00 Hz, 117 adım; perch 0.00 Hz); kesme 100–200 ms 0.000 Hz; B-H1 geçti, B-H2 geçti, B-H3 geçti (3,337 / 3,337).
- **st_ym40**: B-K1 geçti (sürülmeyen 2.225 Hz, son/ilk %25 1.04, en yüksek nöropil UNASGD 23.20 Hz); B-K3 geçti (adım 0.893 s, RSS 3.51 GB); B-K4 geçti (temassız MN9 0.00 Hz, 119 adım; perch 0.00 Hz); kesme 100–200 ms 0.000 Hz; B-H1 geçti, B-H2 geçti, B-H3 geçti (2,645 / 2,645).
- **st_yawp30**: B-K1 geçti (sürülmeyen 2.224 Hz, son/ilk %25 1.05, en yüksek nöropil UNASGD 23.23 Hz); B-K3 geçti (adım 0.897 s, RSS 3.51 GB); B-K4 geçti (temassız MN9 0.00 Hz, 118 adım; perch 0.00 Hz); kesme 100–200 ms 0.000 Hz; B-H1 geçti, B-H2 geçti, B-H3 geçti (2,575 / 2,575).
- **st_yawm30**: B-K1 geçti (sürülmeyen 2.223 Hz, son/ilk %25 1.03, en yüksek nöropil UNASGD 23.00 Hz); B-K3 geçti (adım 0.904 s, RSS 3.51 GB); B-K4 geçti (temassız MN9 0.00 Hz, 116 adım; perch 0.00 Hz); kesme 100–200 ms 0.000 Hz; B-H1 geçti, B-H2 geçti, B-H3 geçti (4,656 / 4,878).
- **st_yawp60**: B-K1 geçti (sürülmeyen 2.225 Hz, son/ilk %25 1.04, en yüksek nöropil UNASGD 23.07 Hz); B-K3 geçti (adım 0.896 s, RSS 3.51 GB); B-K4 geçti (temassız MN9 0.00 Hz, 114 adım; perch 0.00 Hz); kesme 100–200 ms 0.000 Hz; B-H1 geçti, B-H2 geçti, B-H3 geçti (6,075 / 6,214).
- **st_yawm60**: B-K1 geçti (sürülmeyen 2.239 Hz, son/ilk %25 1.01, en yüksek nöropil UNASGD 22.60 Hz); B-K3 geçti (adım 0.905 s, RSS 3.51 GB); B-K4 geçti (temassız MN9 0.00 Hz, 112 adım; perch 0.00 Hz); kesme 100–200 ms 0.000 Hz; B-H1 geçti, B-H2 geçti, B-H3 geçti (6,004 / 6,447).

**Okuma (dürüst sayım):**
- **Ön-kayıtlı sonuç: S1 ∧ S2 8/8.** Hiçbir koşulda kule teması ya da adım-içi penetrasyon yok; hepsi indi ve besledi.
- **Rota yakınsıyor.** ±40 mm öteleme ve ±30°/±60° yön farkı, el yapımı koku haritası tarafından kabaca kule 2 geçişi sırasında kapatılıyor (yön t = 1.02–1.42 s'de n1'in 5° içine giriyor; kuleye en yakın an t = 1.27–1.57 s). Yön koşullarında toplam yön değişimi başlangıç açısının yaklaşık tersi (+30° → −25.8°, −60° → +62.2°).
- **Kritik nokta aynı:** sekiz koşunun hepsi kule 2'nin üstünü y ≈ 75–80 mm hattında, gövde merkezi en yakın kule yüzeyine 2.8–5.5 mm (n1 4.4 mm) olacak şekilde geçiyor. En yakın nokta altı koşuda kulenin uzak üst kenarı (x ≈ 316–323), ikisinde (st_ym40, st_yawp30) yakın üst kenarı (x ≈ 278–279). final_v2a'nın 130.9 µm'lik adım-içi teması da kule 2'nin yakın üst kenarındaydı ((278.4, 66.6, 200.2) mm, §3), final_a'nın 6.3 µm'lik teması da aynı kulenin üst kenarında. Yani marj küçük ve geçiş yeri başlangıçtan bağımsız.
- **Ne gösterir, ne göstermez:** Test, el yapımı rota/iniş zincirinin bu başlangıç aralığında ön-kayıtlı ölçütü geçtiğini gösteriyor. Yön terimi 0 olduğu için beynin rota kontrolü hakkında kanıt değil (SPEC §3.3f'de önceden yazıldı). Tek seed. Daha büyük ötelemeler ya da kule 2 hattından uzak başlangıçlar test edilmedi.
- **Beslenme kararı (BEYİN):** 8/8 koşuda touchdown sonrası beslenme başladı. Temas adımında MN9 3 koşuda 0.0 Hz'di (st_xp40, st_yp40, st_yawm60) ve beslenme bir adım sonra başladı; 5 koşuda temas adımında eşiğin üstündeydi. Gecikme 0–1 adım (≤ 25 ms).

## Sınırlamalar
- **Davranışın neredeyse tamamı HAND.** final_v2a'da rota, irtifa, yaklaşma, iniş el yapımı; yön terimi sabit. Beyinden gelen tek karar beslenme (MN9). Şeker GRN'lerine temas girdisi de el yapımı (tarsus–platform teması → 100 Hz); GRN → MN9 yolu konnektomdan.
- Ablasyon sabiti referansa bağlı. Referans yeni girdiyle ölçülünce sabit +0.102'den +0.244'e çıktı ve final_v2a'nın rotasını değiştirdi. Bu, ablasyonun "beyinsiz" bir taban olmadığını gösterir.
- DNp15 okuması post-hoc seçildi ve iki doğrulamada (seed 3/4/5 ve 6/7/8) aynı nedenle (sağ-baskın taban, sessiz-DN okuması) kaldı.
- DNg02 sessiz: kolektif/irtifa okunamıyor. DNp07 sB girdisinde tonik: iniş kararı adayı değil.
- Tek seed (3) final koşuları; genelleme iddiası yok. final_v2a ile final_sB farkı tek bir sabitin farkı.
- Final-v1 koşuları bacak rampasından önce; v1–v2 farkı yalnız görme girdisinden değil.
- Aerodinamik quasi-steady; hortum eklemi yok; uniform LIF; modülatör NT'ler hızlı uyarıcı/inhibitör sayılıyor.

## Yeniden üretim
```
# Adım 1
env -u PYTHONPATH python scripts/make_dn_reference.py --vision-boundary
# Adım 2 (logs/v2/val altında çalıştırıldı)
python scripts/diag/a0_visual.py --vision-boundary
python scripts/diag/a2_visual.py --vision-boundary --no-platform
python scripts/diag/a2_openloop.py --vision-boundary --seeds 6 7 8
python scripts/diag/a2_openloop.py --report a2_openloop_vb_s{6,7,8}.npz --dn-reference data/dn_lr_reference_sB.json
fly_flight_brain_body_simulation.py --no-olfaction --vision-boundary --dn-reference data/dn_lr_reference_sB.json \
    --spawn-air 440 -170 160 90 --hover --yaw-perturb 0.5 ±30 --n-steps 60 --seed {6,7,8} --no-video [--ablate-dn steer]
python scripts/diag/a2b_perturb.py simulations/flight_v{30..41}_*_v2val_data.h5
# Adım 3
DNP15=ablated nohup bash run_final_v2.sh > logs/final_v2/nohup.out 2>&1 &
# Adım 4
python scripts/diag/fv2_report.py
```
Koşu süreleri: final_v2a 6.4 dk, final_v2c 6.8 dk (kurulum dahil).
