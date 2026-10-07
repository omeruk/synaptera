> **Lab notebook, in Turkish.** Working record of this project, kept as written during the work (moved here from the repository root for the public snapshot). The English consolidated report is [REPORT.md](../../REPORT.md); the English summary is the [README](../../README.md).

# REPORT_SENSORY_B — Aşama B (görme sınır katmanı), tek tam koşu

Komut: `fly_flight_brain_body_simulation.py --seed 3 --n-steps 300 --hybrid --vision-boundary --ablate-dn DNp15 --no-olfaction --no-video --tag final_sB`
→ `simulations/flight_v16_hybrid_sB_ablDN-DNp15_noOlf_final_sB_data.h5`. Referans final_b (`flight_v12_..._final_b`), aynı seed ve spawn.
Ölçütler koşudan önce SPEC_SENSORY_INPUTS §3.3b'ye yazıldı. Kazanç ayarı yapılmadı. DNp15 yeniden kalibrasyonu yok: yön terimi ablasyonla perch tabanında, sabit +0.102.
Rota, irtifa, yaklaşma ve iniş final_b'de olduğu gibi HAND. Beyinden gelen tek karar beslenme (MN9).
Aşağıdaki tablolar `scripts/diag/sb_report.py` çıktısıdır.

## Okuma notları
- **Davranış final_b ile aynı:** touchdown adım 122, beslenme 178 adım, kule teması 0. Beklenen sonuç, çünkü rota HAND ve yön terimi sabit. Yeni görsel girdi davranışa yalnız MN9 ve FLYVIS b_loom üzerinden ulaşabilir. `turn_brain` payının 1.2 çıkması ablasyon sabitinin (+0.102) toplam komuttan büyük olmasından kaynaklanıyor; bu bir beyin kararı değil.
- **Aktivite yayıldı:** sürülmeyen nöronlarda aktif oran %1.38'den %10.8'e çıktı, ortalama hız 0.13'ten 2.2 Hz'e. final_b'nin 1-hop kabuğunda aktif oran %3.1'den %45.5'e çıktı. Artışın çoğu optik lobta (ME, LO) ve AVLP/PVLP/SPS/LAL/VES'te. AL, LH, MB ve FB fiilen sessiz kalıyor (`--no-olfaction`).
- **DNp07 / DNp10 iniş adayı değil:** DNp07 artık her pencerede 60–80 Hz, perch'te de 72/76 Hz. Tonik çalışıyor, yaklaşma ya da iniş seçiciliği yok. DNp10 L final_b'deki gibi ~10–16 Hz, R 0. DNp01 de tonik (perch 28/52, iniş sonrası düşüyor). DNg02 her pencerede 0. Boyun MN'leri ≤ 1.5 Hz. MDN yalnız touchdown öncesi 4 adımda 10/15 Hz; bu, 4 nöronda toplam ~5 spike demek ve çözünürlük düşük.
- **Çift sayım düşük:** gerçekleşen/hedef oranının tip medyanları 0.98–1.15, ortalama oranlar ≤ 1.34. En yüksekleri Lawf2 ve T4a. Hiçbir tip 1.5'i aşmıyor. T4/T5 hızı FlyVis hedefine göre %0–18 şişiyor (T4a 1.18, T4c 1.15); final_b'de bu oran 0.99–1.00'dı.
- **Tm4 fiilen sürülmüyor** (a_ref < 1e-3 kuralı, 0 Hz). Kolonsuz nöronlarda kolon kuralı SPEC'ten sapıyor (partner ortalaması); ayrıntı SPEC §3.3b'de.


## Aktif nöronlar (kapalı döngü, ≥1 spike)

| | B n | B % | final_b n | final_b % |
|---|---|---|---|---|
| Toplam | 40,527 / 138,639 | 29.23 | 11,162 / 138,639 | 8.05 |
| Sürülen girdi nöronları | 29,242 / 34,157 | 85.61 | 9,418 / 11,858 | 79.42 |
| Sürülmeyen nöronlar | 11,285 / 104,482 | 10.80 | 1,744 / 126,781 | 1.38 |
| Ağ ortalaması Hz | 7.51 |  | 0.98 |
| Sürülmeyen ort. Hz | 2.235 |  | 0.130 |

## Baskın nöropile göre (L/R birleşik; ort. Hz = tüm nöronlar, aktif Hz = yalnız aktifler)

| nöropil | n | B aktif | B % | B ort. Hz | B aktif Hz | final_b aktif | final_b % | final_b ort. Hz |
|---|---|---|---|---|---|---|---|---|
| ME | 58,598 | 23,657 | 40.4 | 11.77 | 29.2 | 2,578 | 4.4 | 0.47 |
| LO | 16,751 | 7,549 | 45.1 | 11.57 | 25.7 | 2,931 | 17.5 | 2.23 |
| LOP | 8,027 | 5,570 | 69.4 | 8.56 | 12.3 | 4,797 | 59.8 | 7.52 |
| LA | 6,668 | 488 | 7.3 | 3.18 | 43.4 | 0 | 0.0 | 0.00 |
| GNG | 5,222 | 507 | 9.7 | 1.67 | 17.2 | 392 | 7.5 | 1.39 |
| (yok) | 4,458 | 333 | 7.5 | 2.44 | 32.7 | 7 | 0.2 | 0.03 |
| MB_CA | 3,862 | 0 | 0.0 | 0.00 | – | 0 | 0.0 | 0.00 |
| AVLP | 3,803 | 622 | 16.4 | 8.13 | 49.7 | 46 | 1.2 | 0.01 |
| SMP | 3,556 | 121 | 3.4 | 0.05 | 1.6 | 2 | 0.1 | 0.00 |
| SLP | 3,039 | 26 | 0.9 | 0.05 | 5.5 | 2 | 0.1 | 0.00 |
| AL | 2,977 | 11 | 0.4 | 0.02 | 4.4 | 0 | 0.0 | 0.00 |
| LH | 2,383 | 20 | 0.8 | 0.03 | 3.7 | 0 | 0.0 | 0.00 |
| PLP | 2,233 | 181 | 8.1 | 1.03 | 12.8 | 32 | 1.4 | 0.10 |
| FB | 1,837 | 7 | 0.4 | 0.00 | 0.6 | 0 | 0.0 | 0.00 |
| PVLP | 1,728 | 281 | 16.3 | 2.76 | 17.0 | 53 | 3.1 | 0.03 |
| IPS | 1,558 | 175 | 11.2 | 1.14 | 10.2 | 119 | 7.6 | 0.55 |
| SPS | 1,418 | 257 | 18.1 | 2.16 | 11.9 | 50 | 3.5 | 0.19 |
| MB_ML | 1,123 | 1 | 0.1 | 0.00 | 0.5 | 0 | 0.0 | 0.00 |
| AOTU | 1,076 | 22 | 2.0 | 0.13 | 6.2 | 0 | 0.0 | 0.00 |
| LAL | 990 | 259 | 26.2 | 1.29 | 4.9 | 71 | 7.2 | 0.62 |
| SAD | 982 | 30 | 3.1 | 0.28 | 9.3 | 10 | 1.0 | 0.04 |
| ICL | 925 | 46 | 5.0 | 0.59 | 12.0 | 5 | 0.5 | 0.00 |
| CRE | 732 | 99 | 13.5 | 0.13 | 1.0 | 0 | 0.0 | 0.00 |
| PRW | 556 | 37 | 6.7 | 0.73 | 11.0 | 37 | 6.7 | 0.85 |
| AMMC | 509 | 6 | 1.2 | 0.05 | 4.4 | 0 | 0.0 | 0.00 |
| VES | 450 | 120 | 26.7 | 1.78 | 6.7 | 17 | 3.8 | 0.06 |
| NO | 405 | 10 | 2.5 | 0.16 | 6.3 | 6 | 1.5 | 0.23 |
| EB | 403 | 9 | 2.2 | 0.02 | 1.1 | 1 | 0.2 | 0.00 |
| SIP | 372 | 9 | 2.4 | 0.02 | 0.7 | 0 | 0.0 | 0.00 |
| SCL | 362 | 13 | 3.6 | 0.45 | 12.6 | 0 | 0.0 | 0.00 |
| WED | 354 | 19 | 5.4 | 1.07 | 20.0 | 3 | 0.8 | 0.01 |
| FLA | 328 | 3 | 0.9 | 0.11 | 11.9 | 2 | 0.6 | 0.02 |
| OCG | 272 | 0 | 0.0 | 0.00 | – | 0 | 0.0 | 0.00 |
| IB | 205 | 7 | 3.4 | 0.13 | 3.9 | 0 | 0.0 | 0.00 |
| MB_VL | 149 | 1 | 0.7 | 0.04 | 5.9 | 0 | 0.0 | 0.00 |
| PB | 100 | 2 | 2.0 | 0.11 | 5.4 | 1 | 1.0 | 0.01 |
| <100 nöronlu 9 nöropil | 228 | 29 | | 1.35 | | 0 | | 0.00 |

## Girdi nöronlarından uzaklık (yönlü en kısa yol, tüm kenarlar; kaynak = o koşunun sürülen girdileri)

| hop | B n | B aktif | B % | B ort. Hz | final_b n | final_b aktif | final_b % | final_b ort. Hz |
|---|---|---|---|---|---|---|---|---|
| 0 (girdi) | 34,157 | 29,242 | 85.6 | 23.64 | 11,858 | 9,418 | 79.4 | 10.02 |
| 1 | 50,850 | 7,327 | 14.4 | 2.50 | 27,274 | 847 | 3.1 | 0.25 |
| 2 | 35,489 | 3,029 | 8.5 | 2.11 | 67,369 | 688 | 1.0 | 0.09 |
| 3 | 15,289 | 833 | 5.4 | 1.80 | 27,079 | 166 | 0.6 | 0.12 |
| 4+ | 999 | 96 | 9.6 | 3.50 | 3,130 | 43 | 1.4 | 0.11 |
| ulaşılamaz | 1,855 | 0 | 0.0 | 0.00 | 1,929 | 0 | 0.0 | 0.00 |

Aynı kabuklar (final_b'nin T4/T5+şeker kaynağına göre), B koşusunda:

| hop (final_b kaynağı) | n | B aktif % | B ort. Hz | final_b aktif % | final_b ort. Hz |
|---|---|---|---|---|---|
| 0 | 11,858 | 87.8 | 10.73 | 79.4 | 10.02 |
| 1 | 27,274 | 45.5 | 13.91 | 3.1 | 0.25 |
| 2 | 67,369 | 23.1 | 6.62 | 1.0 | 0.09 |
| 3 | 27,079 | 6.0 | 2.63 | 0.6 | 0.12 |
| 4+ | 3,130 | 16.0 | 4.64 | 1.4 | 0.11 |
| ulaşılamaz | 1,929 | 3.0 | 1.45 | 0.0 | 0.00 |

## DN / MN hızları (Hz/nöron, L / R) pencerelere göre

**B** (touchdown adım 122; pencere adım sayıları: perch 10, takeoff 4, cruise 52, approach 41, descend 20, td -4..-1 4, td 0..+3 4, landed 177)

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

**final_b** (touchdown adım 122; pencere adım sayıları: perch 10, takeoff 4, cruise 52, approach 41, descend 20, td -4..-1 4, td 0..+3 4, landed 177)

| | n L/R | perch | takeoff | cruise | approach | descend | td -4..-1 | td 0..+3 | landed |
|---|---|---|---|---|---|---|---|---|---|
| DNp07 | 1/1 | 4.0 / 8.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNp10 | 1/1 | 16.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNp15 | 1/1 | 4.0 / 56.0 | 0.0 / 50.0 | 5.4 / 58.5 | 1.0 / 53.7 | 0.0 / 44.0 | 0.0 / 40.0 | 0.0 / 40.0 | 0.0 / 28.5 |
| DNp01 | 1/1 | 0.0 / 4.0 | 0.0 / 0.0 | 0.8 / 2.3 | 1.0 / 1.0 | 0.0 / 2.0 | 0.0 / 10.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNa02 | 1/1 | 36.0 / 0.0 | 30.0 / 0.0 | 53.8 / 16.9 | 42.9 / 9.8 | 52.0 / 10.0 | 60.0 / 10.0 | 20.0 / 0.0 | 19.4 / 1.8 |
| MN9 | 1/1 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 50.0 / 60.0 | 49.3 / 62.6 |
| MDN | 2/2 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| neck MN | 13/13 | 0.0 / 0.0 | 0.0 / 0.0 | 0.1 / 0.0 | 0.1 / 0.1 | 0.0 / 0.3 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| DNg02 | 13/12 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |

## Davranış

| | B | final_b |
|---|---|---|
| touchdown adımı (t s) | 122 (3.075) | 122 (3.075) |
| touchdown hızı mm/s | 6.7 | 5.8 |
| besine min / son uzaklık mm | 1.9 / 1.9 | 1.9 / 1.9 |
| beslenme adımı (ilk) | 178 (122) | 178 (122) |
| kule temas adımı | 0 | 0 |
| maks. kule penetrasyonu mm | 0.0000 | 0.0000 |
| turn_brain (ablasyon tabanı) ort. | +0.102 | +0.102 |
| turn_brain payı (sum|brain|/sum|total|) | 1.202 | 1.217 |
| ort. adım s / beyin s | 0.941 / 0.393 | 0.900 / 0.327 |
| tepe RSS GB | 3.52 | 3.49 |

## Ölçütler (SPEC §3.3b)

- **B-K1 kaçak uyarılma: GEÇTİ** — sürülmeyen ort. 2.235 Hz (< 5); son/ilk %25 = 2.235/2.120 = 1.05 (≤ 1.5); en yüksek nöropil ort. UNASGD 36.87 Hz (≤ 50).
- B-K2 (tam koşu, 8 adım kesme): adım başına 0.846 0.000 0.000 0.000 0.000 0.000 0.000 0.000 Hz; 100–200 ms ort. 0.000 Hz (< 0.1, geçti).
- **B-K2 (smoke, 1 s kesme): GEÇTİ** — son 200 ms ort. 0.0000 Hz; ilk < 0.1 Hz adım 1 (50 ms); 100–200 ms ort. 0.0000 Hz; perch ağ ort. 7.84 Hz.
- **B-K3 adım süresi / RAM: GEÇTİ** — adım 0.941 s vs final_b 0.900 s (+4.6 %); beyin 0.393 vs 0.327 s (+20.1 %); tepe RSS 3.52 GB.
- **B-K4 temassız MN9: GEÇTİ** — 0.00 Hz (119 temassız adım); perch 0.00 Hz; temaslı adımlar 53.7 Hz.
  - final_b: temassız 0.00 Hz, perch 0.00 Hz, temaslı 55.4 Hz.

### B-K6 çift sayım (gerçekleşen / FlyVis hedef hızı, kapalı döngü ortalamaları)

| tip | n | hedef ort. Hz | gerçekleşen ort. Hz | oran (ort.) | medyan oran (hedef ≥ 1 Hz) | n (≥1 Hz) | not |
|---|---|---|---|---|---|---|---|
| T4a | 1,457 | 5.58 | 6.60 | 1.18 | 1.03 | 1,043 |  |
| T4b | 1,507 | 4.35 | 4.81 | 1.11 | 1.02 | 1,061 |  |
| T4c | 1,710 | 8.06 | 9.25 | 1.15 | 1.01 | 984 |  |
| T4d | 1,569 | 14.71 | 15.32 | 1.04 | 1.00 | 967 |  |
| T5a | 1,483 | 19.40 | 19.27 | 0.99 | 0.99 | 1,365 |  |
| T5b | 1,514 | 9.83 | 9.72 | 0.99 | 0.99 | 1,159 |  |
| T5c | 1,536 | 11.85 | 11.77 | 0.99 | 0.99 | 1,050 |  |
| T5d | 1,469 | 7.62 | 7.59 | 1.00 | 1.00 | 927 |  |
| Lawf2 | 346 | 46.82 | 62.58 | 1.34 | 1.15 | 278 |  |
| Mi1 | 1,581 | 44.17 | 43.69 | 0.99 | 0.99 | 1,581 |  |
| Mi10 | 406 | 45.73 | 45.24 | 0.99 | 0.98 | 404 |  |
| Mi14 | 252 | 20.34 | 20.50 | 1.01 | 0.99 | 152 |  |
| Mi15 | 972 | 27.17 | 26.96 | 0.99 | 0.99 | 967 |  |
| R7 | 1,332 | 43.49 | 42.94 | 0.99 | 0.99 | 1,328 |  |
| T2 | 1,466 | 35.68 | 35.44 | 0.99 | 0.99 | 1,443 |  |
| T2a | 1,774 | 45.01 | 44.68 | 0.99 | 0.99 | 1,713 |  |
| T3 | 1,676 | 48.01 | 47.63 | 0.99 | 0.99 | 1,618 |  |
| Tm1 | 1,554 | 21.91 | 21.71 | 0.99 | 0.99 | 975 |  |
| Tm16 | 344 | 20.22 | 20.17 | 1.00 | 0.99 | 198 |  |
| Tm20 | 1,494 | 20.99 | 20.90 | 1.00 | 1.00 | 1,414 |  |
| Tm3 | 1,756 | 43.13 | 43.30 | 1.00 | 1.00 | 1,727 |  |
| Tm4 | 1,490 | 0.00 | 0.00 | – | – | 0 |  |
| Tm5a | 452 | 19.39 | 19.29 | 0.99 | 1.00 | 254 |  |
| Tm5b | 458 | 16.85 | 16.86 | 1.00 | 1.00 | 241 |  |
| Tm5c | 622 | 36.75 | 36.67 | 1.00 | 1.00 | 622 |  |
| TmY10 | 448 | 21.05 | 20.86 | 0.99 | 0.99 | 265 |  |
| TmY14 | 371 | 10.11 | 10.10 | 1.00 | 0.99 | 154 |  |
| TmY3 | 735 | 24.29 | 24.68 | 1.02 | 1.01 | 469 |  |
| TmY4 | 432 | 6.47 | 6.43 | 0.99 | 0.99 | 234 |  |
| TmY5a | 1,180 | 12.98 | 14.64 | 1.13 | 1.03 | 848 |  |
| TmY9q | 358 | 36.85 | 37.43 | 1.02 | 1.01 | 330 |  |
| TmY9q__perp | 377 | 39.50 | 40.65 | 1.03 | 1.02 | 347 |  |

T4/T5 tip başına ortalama oranı, final_b ile:

| tip | B hedef | B gerçek | B oran | final_b hedef | final_b gerçek | final_b oran |
|---|---|---|---|---|---|---|
| T4a | 5.58 | 6.60 | 1.18 | 5.46 | 5.40 | 0.99 |
| T4b | 4.35 | 4.81 | 1.11 | 4.52 | 4.50 | 0.99 |
| T4c | 8.06 | 9.25 | 1.15 | 8.53 | 8.51 | 1.00 |
| T4d | 14.71 | 15.32 | 1.04 | 14.84 | 14.71 | 0.99 |
| T5a | 19.40 | 19.27 | 0.99 | 16.59 | 16.54 | 1.00 |
| T5b | 9.83 | 9.72 | 0.99 | 10.59 | 10.51 | 0.99 |
| T5c | 11.85 | 11.77 | 0.99 | 11.04 | 10.97 | 0.99 |
| T5d | 7.62 | 7.59 | 1.00 | 7.73 | 7.72 | 1.00 |
