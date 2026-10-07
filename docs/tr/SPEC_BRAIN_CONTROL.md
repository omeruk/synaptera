> **Lab notebook, in Turkish.** Working record of this project, kept as written during the work (moved here from the repository root for the public snapshot). The English consolidated report is [REPORT.md](../../REPORT.md); the English summary is the [README](../../README.md).

# NeuroFly Flight — SPEC_BRAIN_CONTROL: teşhis bulguları (R0–R4) ve plan (R5)

> Plan kullanıcı tarafından 2026-09-29'da onaylandı; kararlar aşağıda ("Kullanıcı kararları"). Branch: `brain-control`.
> Teşhis: simülasyon koduna dokunulmadı. Betikler `scripts/diag/` altında (`r0_sugar.py`, `r0_all.sh`, `r1_persist.py`, `r2_anat.py`, `r2_extra.py`, `r3_open.py`, `r3_analyze.py`, `r3_dng02.py`; kullanım `scripts/diag/README.md`). Tam beyin, seed 0, `env -u PYTHONPATH`.
> Adım 0 uygulandı (2026-09-29, sonuçlar aşağıda "Adım 0 — sonuçlar"). Adım 0 kararları (APL, VNC uçuş programı, simetri kaynağı) uygulandı: "Adım 0 kararları — sonuçlar". Adım 0 kararları II (NT işareti testi broad/narrow, taraf normalizasyonu, sıra) 2026-09-30'da uygulandı: "Adım 0 kararları II". Adım 1 (beslenme, MN9) uygulandı: "Adım 1 — sonuçlar". Adım 2 (görsel yön) uygulandı, ölçütler başarısız: "Adım 2 — sonuçlar". Adım 2 kararları (NT yalnız duyarlılık testi; DNp15 yön okuması, post-hoc; yeni normalizasyon; ön-kayıtlı doğrulama seed 3/4/5): "Adım 2 kararları". Doğrulama: (a) geçti, (b) ve (c) başarısız, raporlandı. 160 adımlık koşu: besine ulaşmadı. Sonraki adım için kullanıcı kararı beklenir.

## Kullanıcı kararları (2026-09-29, plan onayı)
1. `column_assignment.csv.gz` repo'ya eklenir: `data/` altına. Kaynağı ve lisansı README'de yazılır. Kopyalama Adım 0'da yapılır.
2. Ascending girdi varsayılan olarak 0. Eski davranış (\|ω\| → 1736 AN) `--asc-legacy` bayrağıyla korunur.
3. Gerçekçi girdiyle de KC kalıcı durumu sürerse raporlanır ve devam edilir. LIF parametrelerine ve NT işaretlerine dokunulmaz.
4. Kalkış için senaryo başına bir looming uyaranı eklenir. Bu **"deney tasarımı"** olarak etiketlenir, karar olarak sayılmaz.
5. Ek, Adım 2 için; el yapımı kural EKLENMEZ:
   - Koku yönü DN'lere ulaşmıyorsa besin platformu görsel olarak belirgin yapılır (koyu, yüksek kontrast).
   - Gerekçe: sinekler koku varlığında görsel nesnelere yönelir (van Breugel & Dickinson 2014).
   - Ölçülecek soru: beynin görsel yönlendirmesi sineği platforma götürüyor mu?

## Context
Hedef: tüm davranış kararlarının FlyWire konnektomundaki DN okumalarından gelmesi. İzinli model parçaları yalnız ikisi:
1. Sabit, doğrusal, literatüre dayalı bir **VNC köprüsü** (DN → kanat genliği/frekansı),
2. **haltere refleksi**.

Mevcut sürüm `demo-v1-el-yapimi-kontrol` tag'inde duruyor. Orada yön %90+ el yapımı koku teriminden geliyor, kolektife konnektom katkısı %0. Bu turun işi: konnektomun bu işi yapıp yapamayacağını ve hangi girdi/okuma kurulumuyla yapabileceğini ölçmek.

---

## R0 — Model doğrulaması: TUTUYOR
Protokol Shiu et al. ile aynı: `model.py` `create_model` + `poi()` (PoissonInput, 68.75 mV, hedefte rfc = 0), 1 s, 5 deneme. Şeker GRN listesi `brain_model/figures.ipynb`'den alındı (21 ID; 20'si v783'te var). MN9 = `CB0701`.

| Kurulum | Şeker GRN oranı | MN9 (Hz, iki nöron) | Referans |
|---|---|---|---|
| v630, orijinal protokol | 100 Hz | 68.6±3.7 / 51.2±4.2 | repo'daki orijinal çıktı `results/example/sugarR_100Hz`: 67.0 / 48.6 |
| v630 | 200 Hz | 93.8 / 62.4 | orijinal `sugarR`: 93.3 / 61.8 |
| v783 | 100 / 200 / 50 / 20 Hz | 59.6/46.8 · 87.4/65.0 · 11.2/8.2 · 0/0 | eşik 20–50 Hz arasında |
| v783, **bizim giriş yolumuz** (PoissonGroup→Synapses, gecikme 1.8 ms) | 100 Hz | 62.4 / 48.2 | Shiu yoluyla eşdeğer |

**Sonuç:** Kurulum, LIF parametreleri ve bizim Poisson giriş mekanizması doğru.

**Yan bulgular:**
- Shiu'nun "right hemisphere" dediği şeker GRN'leri annotations'ta `side = left`. Taraf konvansiyonları farklı; ayrıntı R2 notunda.
- **Uçuştaki `sez` grubu (408 = tüm GRN sınıfları: şeker, acı, su, …) 150 Hz'de MN9'u 0.3 / 2.3 Hz'e bastırıyor.** 100 Hz'de 5 / 1 Hz. Yani mevcut beslenme girdisi hortum motor nöronunu *baskılıyor*. Sebebi acı/diğer GRN'ler.
- Uçuş arka planı (asc 22.5, olf 20, vis 20) açıkken şeker 100 Hz → MN9 20 / 20 Hz. Tek başına şekere göre ~%65 düşük.

## R1 — Girdi denetimi
**Şu an sürülenler** (hepsi aynı oranla, hücre tipi ayrımı yok):

| Grup | Nöron | Oran | Kapsam | Shiu protokolüyle fark |
|---|---|---|---|---|
| ascending (AN) | 1736 | 22.5–150 Hz ∝ \|ω\| | Tüm AN'ler, taraf ve tip ayrımı yok | Shiu küçük, tanımlı bir set sürüyor; bu eşlemenin anatomik temeli yok |
| olfactory (ORN) | 2279 | 20–150 Hz | Tüm ORN tipleri (DA1 feromon dahil); L/R antene göre | Koku kodu yok: her glomerül aynı oranda |
| LA>ME | 8025 | 20–150 Hz ∝ ortalama parlaklık | L1–L5, ON/OFF ayrımı yok, tüm kolonlar aynı | Uzamsal ya da hareket bilgisi yok |
| GRN (`sez`) | 408 | 10 / 150 Hz | Tüm GRN sınıfları | Şeker yerine karışık tat → MN9 baskılanıyor |

Toplam 12,448 nöron sürülüyor (%9).

**Hop analizi.** Uyarıcı ve ≥5 sinapslı kenarlarla, kaynaktan DN'e en kısa yol; 1299 DN'den kaçına k adımda ulaşıldığı:

| Kaynak | k=1 | k=2 | k=3 | Not |
|---|---|---|---|---|
| **ascending** | **881** | 1187 | 1217 | DN'lerin %68'ine **tek sinaps**. İşaretli etki diğer kaynaklardan 10–100× büyük |
| LPLC2 / LC4 | 12 / 10 | 290 / 179 | 821 / 663 | Dev lif (DNp01) ve DNp02/04/11'e 1 hop |
| HS/VS | 28–40 | ~200 | ~800 | DNp15, DNp20, DNa02, DNb06'ya 1 hop |
| T4/T5 | 0 | ~110 | ~680 | |
| ORN | 0–1 | 64–90 | 611–669 | |
| LA>ME | 0–1 | 34–36 | 423–439 | |
| GRN | ~20 | ~250 | ~730 | |

Gecikme payı: her hop 1.8 ms + ~5–10 ms integrasyon. Koku ve parlaklık DN'lere ≥3 hop ötede; ascending 1 hop.

**"Ortalama 5.65 Hz, %81 sessiz" beklenen mi?**
- Evet, beklenen. Modelde spontan aktivite yok: girdisiz ağ 0 Hz'dir (ölçüldü). Eşik için ~5100 sinaps·Hz net uyarı gerekiyor (7 mV / (0.275 mV · 5 ms)).
- Sorun zayıf girdi değil, **yanlış tür girdi.** Asıl bulgu bir sonraki madde.

**KRİTİK: koku girdisi kendi kendini sürdüren bir durumu ateşliyor.** Uçuş arka planı 0.5 s verilip tüm girdiler kesilince ağ ≥2 s boyunca sürüyor:
- 3.45 Hz, nöronların %5.9'u, 147 DN, ~5000 DN spike/s.
- Ateşleyici yalnız ORN 20 Hz. Ascending, LA>ME ve GRN tek başına ateşlemiyor (kesilince 0).
- Çekirdek Kenyon hücreleri: uçuş tabanında 5177 KC'nin 3506'sı aktif. KC→KC uyarıcı sinaps, sürdürülen sette KC başına ortalama 63. Tek nöronlu APL bunu bastıramıyor. Ayrıca lLN1_bc→lLN1_bc işareti pozitif; NT tahmini muhtemelen hatalı. **Değiştirilmedi.**
- Sonuç: **uçuş tabanındaki DN spike'larının ~%80'i (6445 → 5134/s) girdiye değil, bu kalıcı duruma ait.**
- Bu durum sabit bir L/R asimetrisi taşıyor: DNa02 L 71 Hz / R 3 Hz. Ayrıca girdi geçmişine bağlı bir histerezis var. SPEC_FLIGHT'taki "konnektomun R>L bias'ı" ve DNa02 perch L 1.85 / R 0.08 bunun izi.
- Yöntem notu: ilk R3 koşusu koşullar arasında yalnız v/g sıfırladığı için bu durumla kirlendi. Tekrar koşu her koşulda `net.restore('fresh')` ile yapıldı. Aşağıdaki sayılar temiz koşudan.

**Görme (parlaklık + dokusuz kuleler).**
- LA>ME 20 Hz, tek başına: DN çıkışı **0**.
- 100 Hz tek göz: sol 57, sağ 360 DN spike/s. Zayıf ve asimetrik.
- Parlaklık, L1–L5'i ON/OFF ve kolon ayrımı olmadan sürüyor. Hareket ya da looming bilgisi beyne hiç girmiyor. Mevcut `b_loom` FlyWire'dan değil FlyVis'ten geliyor ve el yapımı kazançla eşleniyor.
- Kuleler tek renk (0.55 gri); zemin düşük kontrastlı dama (0.3 / 0.4). Dokusuz yüzeylerde T4/T5 yalnız kenarlarda tepki verir. Kule yüzüne yaklaşırken optik akış neredeyse sıfır olur.

## R2 — Anatomik yol haritası ve ÖNCEDEN BELİRLENEN okuma setleri
Yöntem (`r2_anat.py`, tam tablo `r2_src_dn.csv`):
- Hop sayısı: yukarıdaki gibi.
- İşaretli ağırlık: sinaps sayısı × işaret / hedefin toplam girişi, k ≤ 4 adım toplamı.
- Lateralizasyon: sol kaynak → DN_L ile DN_R farkı.

Bulgular:
- **Koku → DN:** 3 hop, zayıf (≤ 3e-3). İpsilateral eğilim DNa02 ve DNa03'te var; ORN_L → DNa02_L 6.7e-4, DNa02_R −2.6e-5. Ama ORN_R → DNa02 L/R 2.2e-4 / 3.4e-4, yani zayıf. ORN'ler iki AL'ye de projekte eder.
- **Optik akış → DN:**
  - T4/T5 ve HS/VS'den ipsilateral: DNa02 (HS 1 hop), DNp15, DNp20, DNp22, DNb06.
  - Looming (LPLC2/LC4) ipsilateral: DNp01, DNp02, DNp04, DNp06, DNp11 (1 hop).
  - Looming kontralateral: DNa01, DNa04, DNa05, DNb01.
- **Ascending → DN:** 1 hop, baskın. **DNg02'ye net inhibitör** (−4.5e-2), hem L hem R.
- **DNg02:**
  - Uyarıcı presinaptik 656 nöron (IB025, PS181, CL216, PS109, CL336, LAL197, …).
  - İnhibitörler glutamaterjik PS/IB (IB008, PS008, PS005) ve GABAerjik AN_multi_28/6.
  - Yalnız uyarıcı yollarla en güçlü kaynak: görsel projeksiyon nöronları (2 hop, 2.4e-2) > ascending > T4/T5 > ocellar/mekanosensör. Koku ve GRN 100× daha zayıf.

**Önceden belirlenen okuma setleri.** Anatomi + literatür; davranış görülmeden sabitlenir, sonradan değiştirilmez:

| İşlev | Birincil okuma | Anatomik gerekçe | Literatür | Kayıt için ikincil |
|---|---|---|---|---|
| Yön (yaw) | **DNa02 L−R** (1+1) | Koku (ipsi, 3 hop) + optik akış (HS 1 hop, T4/T5 2 hop) buraya yakınsıyor | Yürüyüşte ipsilateral dönüş (Rayshubskiy et al.); uçuş rolü **VARSAYIM** | DNa01, DNb01, DNp15, DNp20, DNb06 |
| Kolektif güç / irtifa | **DNg02 (25) L+R** | Tek literatür okuması; görsel projeksiyon yolu | Namiki et al. 2022 | L−R farkı yalnız kayıt |
| Kalkış | **DNp01** (dev lif) + DNp02/04/11 | LPLC2/LC4 1 hop, ipsilateral | von Reyn et al. 2014 | DNp06 |
| İniş (bacak açma / yavaşlama) | **DNp07 + DNp10** | Optik akış 2–3 hop | Ache et al. 2019 (künye doğrulanacak) — **VARSAYIM** | |
| Beslenme | **MN9** (`CB0701`, 1+1; DN değil, beyin motor nöronu) | Şeker GRN → MN9 | Shiu et al. 2023 (R0'da doğrulandı) | brain_mn (105) |
| İleri hız | **Literatürde DN yok** | — | — | Aşağıda risk olarak işlendi |

`all_dn` (1299) okuması yön için bırakılır. Anatomik seçici değil, ascending ve kalıcı durum tarafından domine ediliyor.

**Taraf konvansiyonu.** Beklenen:
- annotations `side` = sineğin kendi tarafı (Schlegel et al. 2024).
- Shiu'nun v630 "right" etiketi görüntü tarafı.
- FlyGym göz L/R = sineğin tarafı.

İç tutarlılık doğrulandı: `descending_neurons.csv` ile annotations taraf etiketleri 1299/1299 aynı. Mutlak eşleme S2'de bir testle sabitlenir: sol göze yaw uyarımı → HS_L → DNp15_L.

## R3 — Açık döngü uyarım (her koşul temiz başlangıçtan, 1 s)
DN hızları Hz cinsinden, nöron başına.

| Koşul | Önemli okumalar |
|---|---|
| Uçuş tabanı (F0) | DNa02 L71 / R3, DNa01 16/0, DNg13 91/49, DNp10 L10. **DNg02 0** |
| Koku sol 150 / sağ 150 / iki taraf | DNa02 L 82/68/72, R 6/3/3. **Koku tarafı DN'de fark yaratmıyor.** all_dn L−R: −146 / −132 / −337 |
| Yalnız ORN_L / ORN_R (100 Hz) | DNa02 L 59/46, R 1/3. Her iki taraf da **aynı sol ağırlıklı deseni** veriyor; bu kalıcı durumdan geliyor |
| Yaw optik akış (T4a/T5a sol + T4b/T5b sağ, 50 Hz), yalnız | DNp15 L105/R0, DNa02 L71/R6, DNb01 34/16 |
| Ters yaw, yalnız | DNp15 L0/R132, DNp20 R95, DNb06 R84, DNa02 L9/R23. **Ayna simetrik, açık lateral kod** |
| Aynısı uçuş tabanı üstünde (F8/F9) | Yaw sağ: DNa02 L101/R0, DNp15 L98. Yaw sol: DNa02 16/17, DNp15 R123, DNp20 R93. Kod taban altında da korunuyor |
| Looming sol / sağ (LPLC2+LC4 100 Hz) | Sol: DNp01 143/102, DNp02/04/11 ipsi 118/198/121, DNa01 ve DNb01 kontra. Sağ: ayna görüntüsü |
| İleri akış (progressive, iki göz T4a/T5a) | DNp07 36/47, DNp15 32/91, DNa03 L40 |
| Ascending 100 / 150 Hz | all_dn 3× artıyor; DNa02 104/65. DNg02 0 |
| LA>ME tek göz 100 Hz | DN ≈ 0 (DNp22 23–51 hariç) |
| Şeker 100 Hz, yalnız / uçuş tabanında | MN9 55/76 / 20/20 |
| Tüm GRN 100 Hz | MN9 5/1 |

**DNg02 — hiç ateşlenmiyor.** Denenen girdiler:
- ORN, LA>ME;
- T4/T5 a/b/c/d (her biri 100 Hz);
- VS, ocellar, LPLC2/LC4, ascending, GRN;
- hepsi uçuş tabanıyla ya da tek başına.

Hepsinde 25 nöronun hepsi 0 spike.

**Ama uyarılabilir:** kendi uyarıcı presinaptiklerinden ilk 50'si 50 / 100 Hz'de sürülünce 13–15/25 nöron ateşliyor (ort. 20 / 39 Hz). 656 presinaptiğin hepsi 100 Hz'de sürülünce 18/25 nöron, 77 Hz (L 55, R 101).
**Sonuç:** Sorun DNg02'nin kendisi değil, onu besleyen ara katman (PS/IB/CL/LAL). Bu katman bizim duyusal girdilerimizle toplanmıyor. Anatomi en olası kaynak olarak görsel projeksiyon nöronlarını gösteriyor; bunlar ancak gerçek görsel girdiyle (R4) test edilebilir.

## R4 — Görme girdisi: FlyVis → FlyWire
**Fizibilite: YÜKSEK.**
- `~/Downloads/column_assignment.csv.gz` (Matsliah/Zhao 2024 kolon ataması): 31 tip, 45,528 nöron, v783 root_id'lerinin %100'ü Completeness'ta. Kolon sayısı sol 785 / sağ 796; hex koordinat (p, q).
- 30 tip FlyVis ile ortak: R7/R8, L1–L5, C2/C3, Mi1/4/9, Tm1/2/3/4/9/20, T1–T3, T4a–d, T5a–d. Kolonlu T4/T5 sayısı 11,822.
- FlyVis: 65 tip × 721 kolon (u, v ∈ [−15, 15]). LPLC2/LC4/HS gibi görsel projeksiyon nöronları FlyVis'te yok; onları FlyWire LIF kendisi hesaplar. Doğal arayüz bu.

**Yöntem.**
1. FlyWire (p, q) → FlyVis (u, v) hizalaması: merkez kolon + eksen yönü + L/R ayna. Kalan ~70 kenar kolonu en yakın komşuya atanır. Test: dikey/yatay çubuk uyarımı → doğru T4 alt tipi ve doğru kolon.
2. Her karar adımında FlyVis aktivitesi `a` → oran `r = r_max · relu(a − a0) / a_ref`, nöron başına `PoissonGroup.rates` dizisi (yeniden derleme yok).
3. Sürülen katman: **yalnız T4a–d ve T5a–d** (11,822). Tm/Mi de sürülürse T4/T5'e çift girdi olur. LA>ME parlaklık girdisi kaldırılır.
4. `a0` ve `a_ref`, gri ekran ve standart hareketli ızgara tepkisinden **bir kez** belirlenir, sonra sabitlenir. Bu bir transdüksiyon sabitidir, davranışa göre ayarlanmaz.

**Maliyet.**
- FlyVis zaten her adımda koşuyor.
- 11.8k Poisson nöronu + 11.8k sinaps: ihmal edilebilir (<%5 beyin süresi).
- Bellek: < 50 MB.

**Riskler.**
- 25 ms'de tek kare = 40 fps. 300 mm/s'de yakın yüzeylerde zamansal örtüşme (aliasing) olur. Adım başına 2–3 alt kare render gerekebilir (~+0.1 s/adım).
- FlyGym ommatidyası ~5° kabul açısında. Dokular kaba olmalı (periyot ≥ 10–15°).
- Eksen/ayna hizalama hatası yön işaretini tersine çevirir. Birim testle sabitlenir.

**Dokulu kuleler/zemin.**
- Kule ve platform malzemelerine yüksek kontrastlı MuJoCo `checker`/`gradient` doku (ör. 0.2 / 0.8, periyot ~20 mm); zemin kontrastı yükseltilir.
- Beklenen etkiler: yaklaşırken kule yüzünde genişleme (LPLC2/LC4 → kaçınma DN'leri), ileri akış (DNp07), dönüşte yaw akışı (DNp15/DNa02).
- Ölçüt: aynı yörüngenin replay'inde dokusuz ve dokulu T4/T5 toplam aktivitesi ile DN tepkisi karşılaştırılır.

---

## R5 — Plan: el yapımı terimleri tek tek DN okumalarıyla değiştirme
Genel kurallar:
- Her adımda önce `pytest tests/`, sonra smoke (`--n-steps 20`). Tam koşuyu kullanıcı başlatır.
- Her okuma için:
  - `--ablate-dn <set>`: okuma, perch tabanına sabitlenir;
  - `--swap-dn-lr <set>`: L/R değiştirilir. Nedensellik kanıtı budur: dönüş işareti tersine dönmeli.
- Ablasyonlar yalnız okumaya uygulanır. Sinaps ya da nöron silinmez.
- Başarı ölçütleri ≥3 seed'de raporlanır.
- **Başarısızlık olduğu gibi raporlanır; kazanç davranış başarısına göre ayarlanmaz.**

**VNC köprüsü (sabit, bir kez belirlenir, `flight/vnc_bridge.py`):**
- Φ_L,R = Φ_hover · (1 + k_c · ĉ) ± k_s · ŝ
  - ĉ = DNg02 hızı / r_ref
  - ŝ = (DNa02_L − DNa02_R) / r_ref
- Kazançlar ve r_ref literatür aralığından (strok genliği ~110–170°; DN max ~100–200 Hz) kalkış öncesi bir kez sabitlenir. **VARSAYIM** olarak etiketlenir.
- Frekans sabit (218 Hz).
- Taban çıkarımı (perch kalibrasyonu) köprünün sabit ofseti olarak kalırsa **EL YAPIMI** diye raporlanır.

### Adım 0 — Girdi revizyonu (tüm sonraki adımların ön koşulu)
1. **GRN:** 408 yerine yalnız şeker GRN'leri. Shiu listesindeki 20 nöron + karşı taraf LB3 homologları; homologlar bağlantı profili benzerliğiyle, anatomiden seçilir. Yalnız platform/damla temasında sürülür.
2. **Koku:** tüm ORN'ler yerine gıda kokusu glomerülleri (ör. DM1, DM2, DM4, VA2, VM2, DP1m; Semmelhack & Wang 2009, Hallem & Carlson 2006). Taraf ağırlığı ipsi > kontra. Taban oranı spontan ORN düzeyi (~5–10 Hz).
3. **Ascending:** \|ω\| → 1736 AN eşlemesinin anatomik temeli yok. **Varsayılan 0** (kullanıcı kararı 2); `--asc-legacy` bayrağıyla eski davranış korunur. Bu değişiklik yön tabanını ve DNg02 inhibisyonunu etkiler; ölçülüp raporlanır.
4. **Görme:** R4 yöntemi (FlyVis → T4/T5) + dokulu arena. LA>ME parlaklık girdisi kalkar.
5. **Kalıcı durum testi:** yeni girdilerle perch → girdi kesme → kalıcı aktivite ölçümü. LIF parametrelerine dokunulmaz.

Başarı ölçütleri:
- (a) Girdi kesilince ≤200 ms'de ağ < 0.1 Hz. Kalıcı durum yok ya da ölçülüp raporlanmış.
- (b) Simetrik uyarımda okuma setlerinin L/R tabanı |L−R|/(L+R) < 0.2.
- (c) R3 matrisi yeni girdilerle tekrarlanır.

**Risk YÜKSEK:** Gerçekçi koku girdisi de KC durumunu ateşleyebilir. Kullanıcı kararı 3: bu durumda raporlanır ve devam edilir; LIF'e dokunulmaz. Kalıcı durumun okumalara katkısı her koşuda ayrıca ölçülür: perch sonrası girdi kesme penceresi.

### Adım 0 — sonuçlar (2026-09-29, tam beyin, seed 0)
Betikler: `scripts/diag/a0_visual.py`, `a0_criteria.py` (README'de). Her koşul aynı temiz durumdan (`net.restore`), 1 s uyarım (250–1000 ms sayılır) + girdi kesme.

**Uygulanan girdiler** (`flight/groups.py`, `flight/brain.py`, `flight/visual_input.py`):
- Şeker GRN: 36 nöron. Shiu'nun 20'si (sol LB3) + 16 sağ LB3 homoloğu. Homologlar giriş+çıkış partner-tipi profilinde kNN (k=5) ile seçildi. Sol LOO: 19/20 şeker, 44 diğer LB3'ten 2 yanlış pozitif (`data/sugar_grn_783.csv`). Yalnız tarsus–besin platformu temasında 100 Hz. **VARSAYIM:** labellar GRN'ler tarsal temasın yerine kullanılıyor.
- Gıda ORN: DM1, DM2, DM4, VA2, VM2, DP1m, 298 nöron (L 153 / R 145). Oran 8 Hz spontan → 150 Hz. Her anten yalnız kendi tarafının ORN'lerini sürer (ipsi 1, kontra 0).
- Ascending: varsayılan 0; `--asc-legacy` ile eski eşleme.
- Görme: LA>ME kaldırıldı. FlyVis (flow/0000/000) → 11,822 T4a–d/T5a–d, per-nöron oran. Adım başına 2 render, FlyVis dt 12.5 ms.
  - Kolon hizalaması iki konnektomun Mi4/Mi9/Tm9 ofsetlerinden hesaplandı: 60° dönme, yansıma yok, iki hemisferde aynı; kosinüsler 0.87–1.00.
  - Göz konvansiyonu ölçüldü: FlyGym sol göz FlyVis çerçevesinde; **sağ göz yatay aynalanıyor**.
  - FlyVis kapsamı dışındaki ~%9 nöron (L 512 / R 531) en yakın kolona atandı.
  - Transdüksiyon `r = 50·relu(a−a0)/a_ref` (≤150 Hz); a0 düğüm başına gri denge aktivitesi. **VARSAYIM:** R_MAX 50 Hz.
- Dokulu arena: 0.2/0.8 dama; engellerde 20 mm, zeminde 40 mm periyot. Görsel-only mesh'lerle çizildi; çarpışma geom'ları ve temas parametreleri değişmedi. Eski görünüm `--untextured` ile.
- Her koşuda perch sonrası 200 ms girdi kesme penceresi var; sonuç HDF5 `/meta/persist_net_rate_hz`'e yazılıyor.

**FlyVis modelinin sınırı** (kayıt; değiştirilmedi). Standart ızgarada tercih edilen yön / karşı yön:
- T4a 48/18, T4b 50/18, T4c 50/21 Hz: seçici.
- **T4d seçici değil** (aşağı 52 / yukarı 49).
- T5 zayıf seçici; T5b ters eğilimli.
- Statik dokulu sahne de T4/T5'i tonik sürüyor: perch'te ort. 9 Hz, T5a ~21 Hz.

**(a) Kalıcı durum: BAŞARISIZ, raporlandı (kullanıcı kararı 3).**
- **Yalnız gıda ORN'lerini 8 Hz spontan hızda sürmek bile** KC durumunu ateşliyor. Kesmeden 100–200 ms sonra ağ 3.4 Hz; ~3350 KC aktif; ~5100 DN spike/s.
- Ateşlemeyenler: T4/T5 tek başına (perch sahnesi, yaw, simetrik ızgara), şeker 100 Hz, ascending 22.5 Hz tek başına. Bunlarda ağ ≤100 ms'de 0 oluyor.
- ORN'lü tüm koşullarda (koku yok, sol, sağ, iki taraf) kesme sonrası oran aynı: 3.40–3.53 Hz. Yani durum girdiye değil, ateşlenmiş olmasına bağlı.
- Kapalı döngü smoke'ta: perch 4.4 Hz → kesmede 3.4 Hz.

**(b) L/R simetri: BAŞARISIZ.** Değerler |L−R|/(L+R).

| Uyarım | DNa02 L/R (Hz) | Oran | Diğer |
|---|---|---|---|
| ORN iki taraf 150 Hz, yalnız | 53 / 0 | 1.00 | |
| **Ayna-simetrik T4/T5 ızgarası, KC durumu yok** | 28 / 3 | 0.83 | DNp15 16/59, DNb06 0/43, DNp22 32/87 |
| ascending 22.5 Hz, yalnız | 28 / 24 | 0.08 | geçen tek okuma |

- Yani asimetrinin iki kaynağı var: (1) KC durumu (sol ağırlıklı DNa02, R1'deki gibi); (2) görsel yolun kendisi. Simetrik T4/T5 girdisi de DN'lerde güçlü taraf farkı üretiyor. İkincisinin kaynağı (konnektom asimetrisi mi, kolon atamasındaki hemisfer farkları mı; L 5901 / R 5921 nöron) henüz ayrılmadı.
- DNg02, DNp01 ve MN9 simetrik koşullarda sessiz.

**(c) R3 matrisi, yeni girdilerle.** Tam tablo `a0_criteria.py --report` çıktısında.
- **DNg02 hâlâ her koşulda 0.** Buna gerçek T4/T5 görme girdisi (yaw, ileri akış, looming) dahil. Adım 3 riski gerçekleşiyor.
- Şeker 100 Hz tek başına MN9 49/65 Hz (homologlar dahil; R0'da tek taraf 55/76). Perch tabanıyla 17/19 Hz; kalıcı durum ~%70 bastırıyor.
- Yaw, T4/T5 üzerinden yön kodunu taşıyor, ama KC durumu üstünde zayıf. Yalnız görme: yaw sağ → DNp15 L17/R45, DNa02 61/13. Perch tabanı üstünde yaw sağ ve yaw sol arasında DNa02 L 77 → 52, DNp15 R 39 → 71.
- Looming (T4/T5 → LPLC2/LC4 yolu) DNp01'i ateşlemiyor; DNp02 yalnız sağda ~10 Hz ve koşuldan bağımsız. Kule yaklaşması bu hızda yeterli looming uyaranı değil ya da yol zayıf; Adım 3 kalkış uyaranında yeniden ölçülecek.
- Ascending 100 Hz DNa02'yi 111/61 yapıyor. Varsayılan 0 ile uçuş tabanındaki bu AN katkısı kalktı.

### Adım 0 kararları (kullanıcı, 2026-09-29) — sonuçlar
Betikler: `scripts/diag/a0_apl_gain.py`, `a0_criteria.py --apl-graded`, `a0_symmetry.py`, `a0_codex.py` (README'de). Tam beyin, seed 0.

**Karar 1 — APL biyolojik haliyle (`--apl-graded`).**
- APL gerçekte spike atmayan, dereceli global geri besleme baskılaması yapan bir nöron (Papadopoulou et al. 2011; Lin et al. 2014). Yalnız APL'nin çıkış mekanizması değişti (`flight/brain.py`):
  - APL'nin 6221 çıkış sinapsı (5194'ü KC'lere; aynı liste, aynı sayılar, aynı negatif işaret) spike yolundan çıkıp sürekli akım olarak etki ediyor: I_apl,j = g · Σ w_APL→j · a_APL / Hz.
  - a_APL: KC→APL sinaps sayısıyla ağırlıklı ortalama KC hızı (Hz), t_mbr (20 ms) ile alçak geçiren; girdisi yalnız parquet'teki 5215 KC→APL kenarı (gecikme 1.8 ms).
  - Nöron denkleminde tek yeni terim "+ I_apl" (APL hedefi olmayan nöronlarda 0). LIF parametreleri, sinaps listesi ve NT işaretleri değişmedi. Testle doğrulandı: spike + graded ağırlık toplamı = parquet toplamı.
- **Kazanç g = 2.0**, davranışa bakılmadan, yalnız KC seyrekliğiyle bir kez belirlendi. Önceden yazılan kural: gıda kokusu (6 glomerül ORN'si, iki anten 150 Hz, tek başına, 1 s), 250–1000 ms'de ≥1 spike atan KC oranı, hedef %7.5 (literatür %5–10), ızgara 2^(k/2) içinde en yakın değer.
  - Tarama: g = 0 → %94.1, 1 → %13.8, 1.41 → %11.0, **2 → %8.5**, 2.83 → %6.4, 4 → %4.9.
  - Referans: spiking APL ile aynı uyaranda KC'lerin ~%65'i aktif.
- **(a) Kalıcılık: BAŞARISIZ, ama kaynak yer değiştirdi.**

| | spiking APL | graded APL |
|---|---|---|
| Koku sırasında aktif KC (tüm ORN'lü koşullar) | ~%65 | **%8.2–8.5** |
| Kesmeden 100–200 ms sonra ağ | 3.4 Hz | 1.9 Hz |
| Kesmeden 200–500 ms sonra aktif KC | ~3340 | ~413 |
| Kesmeden sonra DN spike/s | ~5100 | ~4600 |
| Kalıcı spike'larda KC payı (X_only_orn8) | %34.5 | **%3.5** |
| Kalıcı spike'larda ALLN + ALPN + LHLN payı | %32 | %52 |

  - ORN'süz koşullar (görme, şeker, ascending tek başına) iki durumda da ≤100 ms'de 0 oluyor.
  - Kapalı döngü smoke'ta (`--apl-graded --no-olfaction`, 20 adım) kesme sonrası: 0.086 Hz → 0.
  - **Yeni çekirdek anten lobunda.** Kalıcı spike'ların giriş sinapslarının %52'si AL_L/AL_R'de (beyin ortalamasının ~15 katı), %12'si LH'de.
  - Modelde uyarıcı işaretli ALLN sayısı 166; kalıcı ALLN spike'larının %59'u bunlardan. Bu 166 nöronun Codex NT tahmini (`neurons.csv`): 90 NaN (skor 0), 24 SER, 41 ACh, 8 GABA, 2 OCT, 1 GLUT.
  - En büyük tek kaynak **lLN1_bc**: 29 nöron, 108k çıkış sinapsı. Codex nt_type NaN (DA ~0.3, SER ~0.25, GABA ~0.2, ACh ~0.2); annotations top_nt karışık (DA 12, ACh 11, SER 7); modelde uyarıcı.
  - R1'deki şüpheli lLN1_bc→lLN1_bc işareti bu. **NT işaretleri değiştirilmedi** (kural); karar kullanıcıda.
- **(b) DN L/R asimetrisi: DÜZELMEDİ.**
  - DNa02 L/R: perch 69/3, yalnız ORN 8 Hz 43/0, kesme sonrası 47/0.
  - Kalıcı durum hâlâ sol ağırlıklı DNa02 taşıyor; KC'ler çekildiğinde de sürüyor, yani taşıyıcı AL/LH döngüsü.
  - Görsel asimetri APL'den bağımsız; aşağıda karar 3.
- (c) Diğer: MN9 şeker 100 Hz tek başına 55/65, perch tabanıyla 15/23 Hz (spiking APL'de 17/19). DNg02 her koşulda 0.

**`--no-olfaction`.** Beyne hiçbir gıda-ORN girdisi yok: PoissonGroup kurulmuyor, spontan 8 Hz de yok. El yapımı koku terimleri de sıfırlanıyor (`turn_odor = pitch_odor = 0`, `--ablate-odor`'u içerir). Aksi halde kontrolcü koku alanını doğrudan okuyup yönlendirirdi. HDF5 adı `_ablOdor_noOlf`; `--apl-graded` → `_aplG`.

**Karar 2 — VNC uçuş programı (plan güncellemesi; kod Adım 1+ içinde).**
- Kolektif güç, irtifa tutma ve seyir eğimi **"VNC uçuş programı"** olarak kalır ve öyle etiketlenir: sabit hover gücü + dikey hız sönümü + sabit seyir eğimi.
- Adım 3'teki "pitch_alt kaldırılır / ĉ = DNg02 → kolektif" planının yerine geçer.
- Beynin kararları:
  - yön: DNa02 / DNp15;
  - kalkış: DNp01 / looming;
  - iniş: DNp07 / 10;
  - beslenme: MN9.
- Koku→dönüş (`turn_odor`) ve koku→irtifa (`pitch_odor`) el yapımı terimleri yine kaldırılır.
- DNg02 kayıt için kalır. Raporda **"kolektif güç konnektomdan okunamadı"** yazılır: R3 ve Adım 0'da, gerçek T4/T5 girdisi ve graded APL dahil, her koşulda 0.
- DNp15'in yön okumasına birincil olarak katılması kullanıcı kararıdır. R2 tablosunda ikincildi; anatomik gerekçe: HS/H2 1 hop, IPS.

**Karar 3 — ayna-simetrik ızgarada DN asimetrisinin kaynağı: KONNEKTOM (eşleme hatası değil).**
- Swap testi (`a0_symmetry.py`): koku yok, KC durumu yok. Değerler Hz/nöron L/R, (L−R)/(L+R).

| Okuma | normal | gözler yer değiştirmiş | eşlemesiz (alt tip başına düz oran) |
|---|---|---|---|
| DNa02 | 31/3 +0.84 | 29/3 +0.83 | 29/3 +0.83 |
| DNp15 | 12/64 −0.68 | 12/67 −0.69 | 17/61 −0.56 |
| DNb06 | 0/43 −1.00 | 0/41 −1.00 | 0/37 −1.00 |
| DNp22 | 27/88 −0.53 | 31/83 −0.46 | 32/88 −0.47 |
| DNp20 | 9/80 −0.79 | 11/80 −0.76 | 12/79 −0.74 |
| HS (LPTC) | 132/106 +0.11 | 133/109 +0.10 | 141/101 +0.17 |
| VS (LPTC) | 80/116 −0.18 | 81/115 −0.17 | 81/112 −0.16 |

- Girdi simetrik: FlyVis iki göz aktivite farkı %7 (ızgara fazı). T4/T5 toplam girdi L 155.6k / R 156.2k Hz·nöron; alt tip ortalamaları L/R ±%1.
- **Asimetri girdiyle yer değiştirmiyor ve kolon eşlemesi kaldırılınca da kalıyor.** Kaynak FlyWire tarafında; LPTC katmanında zaten görünüyor.
- Kapsam ve sayılar simetrik, eşleme sorunu yok:
  - kolon L 785 / R 796; T4/T5 L 5901 / R 5921; kolon başına 7.52 / 7.45; FlyVis kapsamı dışında L 512 / R 531;
  - alt tip sayıları column_assignment, visual_neuron_types, consolidated_cell_types ve annotations arasında ±%2. column_assignment'ta olmayan T4/T5'ler (T4c'de 157, T4d'de 71) kolonsuz oldukları için sürülmüyor;
  - HS / H2 1+1, VS 8+8.
- **Sinaps sayıları asimetrik:**
  - T4/T5 çıkış sinapsları: parquet (eşiksiz) L 718k / R 1,000k (+%39); Princeton ≥5, LOP_L 535k / LOP_R 795k.
  - T4/T5 → LPTC (parquet): VS 20.1k/33.0k, LPLC2 19.0k/31.1k, H2 10.1k/14.4k, LPC2 7.2k/19.7k; HS 16.0k/14.6k (tek ters yönlü).
  - LPTC → DN (Princeton): VS→DNp20 319/542, VS→DNb06 271/329, H2→DNp15 206(R→L)/173(L→R).
  - DN'lerin kendi toplam girdisi yaklaşık simetrik: DNa02 11.5k/12.5k, DNb06 4.8k/4.5k. İstisnalar DNp15 1.1k/1.9k ve DNp10 6.6k/1.3k.
  - Yorum: asimetri esas olarak optik lob sinaps sayılarında (sağ lobula plate'te daha çok T4/T5 çıkışı) ve eşik yakınındaki DN'lerde büyüyor (DNb06 0/43).
  - DNa02'nin L baskınlığı LPTC'den gelmiyor: HS→DNa02 sinapsları L>R ama küçük (107/70). Doğrudan girdileri (LAL/IPS) simetrik; farkın kaynağı çok-hop ve ayrılmadı.
  - Bu asimetrinin biyolojik mi, rekonstrüksiyon/proofreading farkı mı olduğu bu veriden ayrılamaz.
- **Eşleme değişmedi, düzeltme yapılmadı.** Sağ göz aynalaması ve 60° hizalama doğru; swap testi eşleme hatasını dışlıyor.
- Sonuç: (b) kriteri bu konnektomla simetrik görsel uyarımda geçmez; Adım 2'de yön okuması bu tabanla raporlanmalı. Taban çıkarımı EL YAPIMI olur.

**Veri envanteri kontrolleri** (`a0_codex.py`; FlyWire Codex v783, `data/README.md`):
- **root_id:** simülasyondaki 138,639 nöronun hepsi `neurons.csv`'de (139,255). Fazla 616 nöron: 553 sensory, 31 sensory_ascending, 14 ascending, 6 optic, 4 descending, 4 central, 4 endocrine.
- **Princeton bağlantıları:** ortak 3.67M çiftte sinaps sayısı yalnız %10.7'sinde birebir eşit (fark medyanı +2, Princeton lehine). Parquet (Shiu v783 tablosu) Princeton ≥5 tablosuyla aynı değil. Bağlantı sayıları yalnız karşılaştırma amacıyla kullanıldı; model parquet'ten gelir.
- **NT:** APL L/R GABA (0.77 / 0.76). KC 5177'nin hepsi ACh (skor medyanı 1.00). Parquet işareti ile Codex nt_type 473 presinaptik nöronda uyuşmuyor. DA/SER/OCT tahminli 1677 nöron parquet'te uyarıcı (Shiu konvansiyonu).
- **Kalıcı çekirdeğin nöropili** (spiking APL, P0_perch): AL_L/R (5.6×), MB_CA_L/R (5.3× / 4.9×), LH_L/R (4.7× / 4.3×). Taraf L 4171 / R 3889.

### Adım 0 kararları II (kullanıcı, 2026-09-30) — kurallar ölçümden ÖNCE yazıldı
**Karar 1 — NT işareti testi (`--nt-modulatory-silent`, varsayılan KAPALI).** "NT işaretlerine dokunulmaz" kuralının bilinçli, yalnız bayrakla açılan istisnası.
- Gerekçe: Shiu modeli GABA/Glu dışındaki her NT'yi hızlı uyarıcı sayıyor. Biyolojide DA/SER/OCT yavaş modülatördür. AL yerel nöronlarının çoğu GABAerjiktir (Wilson & Laurent 2005; Chou et al. 2010).
- **Kural (sabit, davranışa bakmadan):**
  - Codex v783 `neurons.csv` `nt_type` ∈ {DA, SER, OCT} olan nöronlar ya da NT tahmini olmayan nöronlar (`nt_type` NaN, `nt_type_score` = 0) seçilir.
  - Bu nöronların parquet'teki **bütün giden sinapsları** (işareti ne olursa olsun) hızlı yoldan çıkar: ağırlık 0.
  - Sinaplar Brian2 sinaps listesinde kalır. Nöronlar ağda kalır, girdi alır ve spike atar.
  - Başka hiçbir işaret değişmez. LIF parametreleri değişmez.
  - Liste `data/nt_modulatory_silent_783.csv`'dedir; `scripts/make_nt_silent.py` ile `~/Downloads/neurons.csv.gz`'den üretilir.
  - Kayıt: HDF5 `/meta/nt_silent` (sayılar) ve `/nt_silent/idx` (sessizleştirilen nöron indeksleri). Çıktı adında `_ntS` geçer.
- **Kural uygulanmadan bilinen yapısal sonuç** (davranış değil, liste kesişimi):
  - NaN NT'li nöronların çoğu duyusal ya da optik lob nöronu.
  - Kural Poisson ile sürülen girdi nöronlarının bir kısmının çıkışını da kesiyor: gıda ORN 182/298, şeker GRN 11/36, T4/T5 1154/11,822.
  - Kural olduğu gibi uygulanır, istisna eklenmez. Bu kesişim sonuçla birlikte raporlanır.
- **Ek kural (kullanıcı, 2026-09-30).** İlk broad koşusu girdileri de susturmuştu. Bu ek, o koşunun sonucu değerlendirilmeden yazıldı:
  - İki varyant var:
    - `--nt-modulatory-silent broad` (= yukarıdaki kural): DA/SER/OCT + NaN.
    - `--nt-modulatory-silent narrow`: yalnız `nt_type` DA/SER/OCT (NaN hariç).
  - **Hiçbir varyantta Poisson ile sürülen girdi nöronları susturulmaz.** Bunlar `orn_food_L/R/C`, `sugar`, `t45_L/R` (ve `--asc-legacy` ile `ascending`); `--no-olfaction`'da da aynı liste.
  - Amaç: kalıcılığın kalkmasının ne kadarının girdi zayıflamasından geldiğini ayırmak.
  - İki varyant aynı ölçütlerle yan yana raporlanır. İlk (girdileri de susturan) broad koşusu yalnız kayıt olarak üçüncü sütunda durur.
  - Çıktı adları `_ntS-broad` / `_ntS-narrow`.
- Ölçümler:
  - (a) kalıcılık kriteri, tek başına ve `--apl-graded` ile;
  - KC seyrekliği;
  - R0 regresyonu: şeker 100 Hz → MN9 > 40 Hz mi;
  - DN L/R asimetrisi;
  - etkilenen nöron ve sinaps sayıları.
- Başarısızsa olduğu gibi raporlanır. Başka işaret değiştirilmez.

**Karar 1 — sonuçlar (2026-09-30, tam beyin, seed 0; `a0_criteria.py --nt-silent broad|narrow [--apl-graded]`, 21 koşul, R3 matrisi aynı).**

| | broad (girdiler korunur) | narrow (girdiler korunur) | broad, girdiler de susturulmuş (ilk koşu, yalnız kayıt) |
|---|---|---|---|
| Susturulan nöron | 19,372 (DA 584, SER 939, OCT 72, NaN 17,777); 1,347 girdi nöronu korundu | 1,595 (DA 584, SER 939, OCT 72); 82 girdi nöronu korundu | 20,719 |
| Sıfırlanan kenar | 1,132,146 / 15.09M (%7.5) | 296,022 (%2.0) | 1,188,391 (%7.9) |
| Sıfırlanan sinaps | 1.76M uyarıcı + 1.89M inhibitör = 3.64M / 54.5M (%6.7) | 0.71M uyarıcı + 0 inhibitör (%1.3) | 1.87M + 1.92M (%7.0) |
| **(a) kalıcılık**, spiking APL (100–200 ms < 0.1 Hz) | **21/21 GEÇTİ**; 200–500 ms'de hepsi 0 | **ORN'lü 13 koşulda BAŞARISIZ**: ~2.2 Hz, kesme sonrası ~2250 KC aktif | 20/21 (V_prog 0.116 Hz) |
| (a) kalıcılık, `--apl-graded` | **21/21 GEÇTİ** | ORN'lü 13 koşulda BAŞARISIZ: ~1.5 Hz | 21/21 |
| KC seyrekliği (gıda kokusu 150 Hz tek başına, 250–1000 ms'de aktif KC) | spiking **%9.6** (hedef %5–10); graded %3.4 | spiking %49 (kalıcı durum); graded %7.2 | spiking %5.6; graded %2.4 |
| **R0** şeker 100 Hz tek başına → MN9 L/R | **53/69 Hz (>40, geçti)** | 45/57 (geçti) | 79/83 |
| Şeker + perch tabanı → MN9 | 63/68 | 24/32 | 55/60 |
| DN L/R, perch (DNa02 · DNp15) | 55/0 · 0/52 | 73/0 · 0/47 | 55/0 · 0/52 |
| DN L/R, yalnız görme perch sahnesi (DNa02) | 63/3 | 61/0 | 75/0 |
| DN L/R, ayna-simetrik ızgara (DNa02 · DNp15) | 28/11 (0.45) · 17/67 | 31/1 (0.92) · 13/69 | 27/9 · 13/68 |

Karşılaştırma: değişmemiş model (Adım 0) spiking APL 3.4 Hz kalıcı, perch'te MN9 15–17/19–23.

**Yorum** (ölçülenin ötesine geçmeden):
- **Kalıcılığı kaldıran, girdi zayıflaması değil; NT tahmini olmayan (NaN) ~17.8k girdi-dışı nöronun çıkışı.** Kanıtlar:
  - broad, girdiler korunarak da 21/21 geçiyor;
  - narrow (yalnız DA/SER/OCT, girdiler aynı) kalıcı durumu hiç kaldırmıyor.
  - lLN1_bc'nin 30 nöronu da bu NaN kümesinde. Sorumlu alt küme ayrılmadı.
- broad'da spiking APL ile KC seyrekliği kendiliğinden literatür aralığına giriyor (%9.6).
  - graded APL (g = 2.0, değişmemiş ağda kalibre) bu ağda KC'leri fazla bastırıyor (%3.4).
  - Kazanç yeniden ayarlanmadı.
- **DN L/R asimetrisi düzelmedi.** Kalıcı durum yokken de perch'te DNa02 sol baskın, DNp15 sağ baskın.
  - Bu, Karar 3'teki görsel yol asimetrisiyle tutarlı.
  - Asimetri yalnız KC/AL durumundan gelmiyordu.
- **Koku tarafı DN'de hâlâ fark yaratmıyor** (broad: O_L150 ile O_R150 arasında DNa02 ~aynı).
- DNg02 her koşulda 0.
- Bu bir işaret varsayımının testidir, biyolojik düzeltme iddiası değildir:
  - NaN NT'nin anlamı "tahmin yok"tur, "modülatör" değil.
  - broad'ın başarısı, bu nöronların hızlı uyarıcı/inhibitör sayılmasının kalıcı durumu taşıdığını gösterir; doğru işaretlerinin ne olduğunu göstermez.
- Varsayılan KAPALI kalır. Adım 1–2 bu bayrak olmadan (`--no-olfaction`) yürür. Kokunun geri eklenmesi kullanıcı kararıdır.

**Karar 2 — yön okumasında taraf normalizasyonu (VARSAYIM).**
- Asimetri konnektom kaynaklı (Karar 3). Eşlemeye dokunulmaz.
- VNC köprüsünde her tarafın DN okuması, o tarafın **önceden sabitlenmiş simetrik referans uyarana** verdiği kendi tepkisine bölünür:
  - Referans: ayna-simetrik ileri akış ızgarası (`a0_visual.py` `sym_prog` ile aynı uyaran).
  - Referans bir kez ölçülür ve `data/dn_lr_reference.json`'a yazılır.
- VARSAYIM olarak etiketlenir. Normalizasyonsuz ham okuma da HDF5'e yazılır.

**Karar 3 — sıra.** Adım 1 (beslenme) ve Adım 2 (görsel yön) `--no-olfaction` ile ilerler. Koku düzeltmesi (Karar 1) başarılı olursa koku sonradan eklenir.

### Adım 1 — Beslenme (en düşük risk)
- **Değişen:** zaman tabanlı `feed_extend/eat/retract` fazları kaldırılır.
- **Yeni kural:** proboscis uzatma = MN9 hızı > eşik; eşik R0 eğrisinden sabitlenir (20–50 Hz arası geçiş). Şeker GRN'leri yalnız temas varken sürülür.
- **Başarı:**
  - temasta MN9 > eşik, temas yokken 0;
  - uçuş tabanı altında da eşik aşılır (R0: 20 / 20 Hz → eşik buna göre);
  - `--ablate-mn9` ile uzatma hiç olmaz.
- **Risk düşük–orta:** Uçuş tabanı MN9'u 60'tan 20 Hz'e bastırıyor. Adım 0'dan sonra yeniden ölçülür.
- Kısıt: FlyGym'de hortum eklemi yok; uzatma görsel/kayıt olarak kalır.
- **Uygulama sabitleri** (`flight/vnc_bridge.py`; davranıştan önce yazıldı):
  - Eşik **10 Hz**, iki MN9'un ortalaması. R0 v783 eğrisinde GRN geçişi 20–50 Hz arasında; eşik, geçişin üst ucundaki (50 Hz GRN) MN9 ortalaması: (11.2 + 8.2)/2 = 9.7 → 10 Hz.
  - Okuma alçak geçireni τ = 50 ms (**VARSAYIM**). 10 Hz'de 25 ms'de 0.5 spike düşer; filtre olmadan karar tek spike'la titrer.
  - `--ablate-dn mn9` (= `--ablate-mn9`): okuma perch tabanına sabitlenir.
  - Zamanlı `feed_extend/eat/retract` fazları yalnız `--legacy-control` ile kalır. Yeni yolda iniş sonrası faz `landed`; `is_feeding` = landed ∧ MN9 kararı.
  - **Deney tasarımı:** `--start-on-platform`. Sinek besin platformunda ayakta başlar. Perch kalibrasyonu şekersiz yapılır; kapalı döngünün ilk adımından itibaren temas → şeker. Gerekçe: `--no-olfaction` ile sinek platformu kendisi bulmuyor.

**Adım 1 — sonuçlar** (2026-09-30, tam beyin, `--no-olfaction`, spiking APL, NT değişmemiş, seed 0/1/2). Betikler: `scripts/diag/a1_mn9.py`, `a1_closed.py`.

*Açık döngü* (1 s, 250–1000 ms). MN9 ortalaması, 3 seed ort. ± SS:

| Koşul | MN9 L/R (Hz) | ortalama | eşik 10 Hz |
|---|---|---|---|
| şeker 100 Hz tek başına | 50/61 | 55.6 ± 4.5 | geçti (3/3) |
| şeker + perch görme | 58/70 | 64.0 ± 2.0 | geçti |
| şeker + hover görme | 50/62 | 56.0 ± 2.0 | geçti |
| şeker + ileri uçuş akışı (100 mm/s) | 56/70 | 62.9 ± 4.4 | geçti |
| şeker + yaw | 54/66 | 60.2 ± 2.5 | geçti |
| şekersiz, perch / ileri uçuş | 0/0 | 0 | 0 |

- Uçuş görsel tabanı MN9'u bastırmıyor, hafif artırıyor.
- Adım 0'daki ~%70 bastırma, koku kaynaklı kalıcı durumdan geliyordu; `--no-olfaction` ile o durum yok.

*Kapalı döngü* (40 adım = 1 s; `a1_closed.py`):

| Koşul | temaslı adım | MN9 temasta (Hz) | temasta uzatma oranı | temassız uzatma | ilk uzatma gecikmesi |
|---|---|---|---|---|---|
| `--start-on-platform` s0/s1/s2 | 40/40 | 51.6 / 61.2 / 57.1 | 0.97 / 0.97 / 0.95 | – | 50 / 50 / 75 ms |
| `--start-on-platform --ablate-mn9` s0/s1/s2 | 40/40 | 0 (taban) | 0 / 0 / 0 | – | uzatma yok |
| pedestaldan kalkış (temas yok) s0/s1/s2 | 0 | – | – | 0 / 0 / 0 (MN9 0 Hz) | – |

- Başarı ölçütleri üçü de sağlandı: temasta MN9 > eşik, temassız 0; uçuş görsel tabanında da eşik aşılıyor; `--ablate-mn9` ile uzatma hiç olmuyor.
- Kalıcılık (kapalı döngü, kesme sonrası 25–50 ms): 0.004 Hz → 0 (koku yok).
- **Dürüstlük notu.** Karar zinciri: şeker GRN (temasla, sabit 100 Hz) → konnektom → MN9 → sabit eşik.
  - Temas algılama ve GRN oranı el yapımı girdi eşlemesidir.
  - MN9'a kadar olan kısım konnektomdan gelir.
  - `--no-olfaction` ile sinek platforma kendisi gitmiyor. Temas deney tasarımıyla sağlandı; "sinek besini bulup yedi" sonucu yok.

### Adım 2 — Yön
- **Kalkanlar:** `turn_odor` (tanh(20·I_asym)·2 ve ℓ_eff = 10 mm), `b_loom` (FlyVis T5 el yapımı kazanç), `all_dn` ΔDN.
- **Yerine:** ŝ = DNa02 L−R → köprü ΔΦ.
- **Başarı:**
  - (a) Açık döngü, sabit hover'da dönen desen → optomotor yönde yaw. `--swap-dn-lr` ile işaret tersine döner.
  - (b) Kule yüzüne yaklaşırken kaçınma dönüşü (looming → DNa01/DNb01 kontra, kayıt) ya da çarpma; hangisi olursa raporlanır.
  - (c) Koku yönelimi: yalnız koku kaynaklı DNa02 lateralizasyonu var mı? Ölçüt: kalkış noktasından besine başlangıç yön hatası, `--ablate-dn` ile karşılaştırmalı.
- **Risk YÜKSEK (koku yönelimi):** R3'te koku tarafı DN'de fark yaratmadı; anatomik lateralizasyon da zayıf. Beklenti: optomotor stabilizasyon ve looming kaçınması çalışır, **kokuya yönelim büyük olasılıkla çalışmaz.** Sinek besine ulaşamayabilir; bu sonuç olarak raporlanır.
- **Görsel nesneye yönelim (kullanıcı kararı 5).**
  - Kurulum:
    - Besin platformu ve damla koyu, yüksek kontrastlı yapılır; bu arena tasarımıdır.
    - Yönelim için yeni bir kontrol terimi eklenmez. Platform görüntüsü yalnız FlyVis → T4/T5 → FlyWire yolu ve aynı DNa02 okumasıyla etkiler.
  - Ölçütler:
    - (d) Platformun retinal azimutu ile DNa02 L−R arasındaki ilişki.
    - (e) Kalkıştan sonra platform yönüne dönüş, iki kontrolle karşılaştırılarak: platform görsel olarak nötr (arka planla aynı) iken, ve `--ablate-dn`.
    - (f) Platform geçici olarak görünür ve koku kapalıyken yönelim olup olmadığı. Koku ile görme arasındaki bağlam etkisi konnektomda kendiliğinden var mı, bu soruya bakar.
  - Sonuç ne çıkarsa (yönelim, kaçınma ya da ilişki yok) öyle raporlanır.
- **Uygulama (2026-09-30; sabitler ve beklenen yönler davranıştan ÖNCE yazıldı).** `flight/vnc_bridge.py`:
  - Formül: n_t = r_L/ref_L − r_R/ref_R, t ∈ {DNa02, DNp15}; ŝ = ort. n_t; turn_bias = −K_STEER·ŝ.
    - r, τ = 50 ms filtreli Hz/nöron.
    - turn_bias > 0 = sağa dönüş; ΔΦ = 10°·turn_bias.
    - ±2.5'te kırpılır.
  - **İşaret VARSAYIM:** solda daha aktif DN → sola dönüş (ipsilateral).
    - DNa02 için yürüyüşten (Rayshubskiy et al.).
    - DNp15 için: HS, gövdenin sağa dönüşündeki ipsilateral önden-arkaya akışla uyarılır; optomotor tepki geri döner, yani ipsilateral.
    - Sonuçtan sonra ters çevrilmez.
  - **K_STEER = 1** (VARSAYIM): ŝ = 1 → ΔΦ = 10°, ~5 rad/s kararlı yaw.
  - **ref:** `data/dn_lr_reference.json`. `scripts/make_dn_reference.py` ile ölçülür: sym_prog ızgarası, 2 s, 250–2000 ms, seed 0/1/2, Adım 2 beyni (`olfaction=False`, spiking APL, NT değişmemiş).
  - `--swap-dn-lr steer`: normalize edilmiş iki taraf kanalı yer değiştirir, ŝ → −ŝ.
  - `--ablate-dn steer`: okuma perch tabanına sabitlenir.
  - Yeni yolda `turn_odor`, `b_loom` ve `all_dn` terimleri yok (0 kaydedilir). Eski yol `--legacy-control` ile.
- **Arena tasarımı:** platform sütunu ve damla düz koyu (0.03). `--platform-neutral`: diğer engellerle aynı dama.
- **Deney tasarımı:** `--spawn-air X Y Z YAW`.
  - Havada hover ile başlanır; kalibrasyon ve girdi kesme hover'da yapılır (kanatlar açık, yalnız dikey hız sönümü). Sonra cruise.
  - Bu durumda ablasyon tabanı perch değil, hover tabanıdır.
- **Önceden yazılmış beklenen yönler:**
  - optomotor: dünyanın CCW dönüşünde (sineğin sağa dönmesi, `yaw_R`, `syn_yaw_ccw`) SOL; tersinde SAĞ.
  - looming: sol duvar yaklaşırken kaçınma = SAĞ.
  - platform yönelimi: platform solda (az > 0) iken SOL.
- **Ölçümler:**
  - (a) açık döngü: `a2_openloop.py`, 3 seed; normal / swap / ablasyon aynı spike sayılarından.
  - (b) kule: pedestaldan kalkış (başlangıç yönü kule 1'e dik), 60 adım × 3 seed. Normal / `--ablate-dn` / `--swap-dn-lr`.
  - (d) açık döngü azimut → dönüş, koyu ve nötr platform.
  - (e) kapalı döngü: `--spawn-air 440 -170 160 90±30` (platform 250 mm kuzeyde, ±30° azimut), 40 adım × 3 seed. Koyu / nötr / `--ablate-dn`.
  - (f) koku kapalı olduğundan bağlam etkisi test edilemez; koku eklenince yapılır.

**Adım 2 — sonuçlar** (2026-09-30, tam beyin, `--no-olfaction`, spiking APL, NT değişmemiş).

*Referans* (`data/dn_lr_reference.json`, sym_prog, 3 seed):
- DNa02 L/R **31.4 / 2.5 Hz**; DNp15 L/R 15.2 / 63.2 Hz.
- Seedler arası fark < 2 Hz.
- Sağ DNa02'nin referans tepkisi neredeyse sessiz. Normalizasyon, sağ DNa02'deki her Hz'i sol DNa02'dekinin ~12 katı ağırlıkla sayıyor.

*(a) Açık döngü* (`a2_openloop.py`, 3 seed; turn_bias > 0 = sağ; 250–1000 ms ortalaması):

| Koşul | beklenen | normal (s0/s1/s2) | n_DNa02 | n_DNp15 | ham DNa02 L/R · DNp15 L/R (Hz) |
|---|---|---|---|---|---|
| perch (sahne statik) | – | −0.18 / −0.49 / −0.18 | +1.45 | −0.90 | 57/1 · 0/57 |
| hover, statik | – | +1.22 / +1.63 / +1.52 | −2.61 | −0.89 | 53/11 · 0/56 |
| sentetik yaw, dünya CCW | SOL | −0.58 / −0.12 / −0.06 ✓ | −4.72 | **+4.96** | 15/13 · 76/0 |
| sentetik yaw, dünya CW | SAĞ | +1.77 / +1.30 / +1.77 ✓ | −2.14 | −1.70 | 0/5 · 0/108 |
| arena yaw_R (dünya CCW) | SOL | +1.84 / +1.76 / +1.84 ✗ | −6.58 | **+0.51** | 47/20 · 18/41 |
| arena yaw_L (dünya CW) | SAĞ | +2.00 / +1.97 / +2.26 ✓ | −5.40 | −1.22 | 39/16 · 0/77 |
| ileri akış (arena) | – | +2.18 / +1.93 / +2.04 | −5.73 | −0.75 | 68/20 · 4/62 |
| looming sol (kaçınma SAĞ) | SAĞ | +1.20 / +0.70 / +0.72 ✓ | −1.45 | −0.88 | 33/6 · 0/57 |
| looming sağ (kaçınma SOL) | SOL | +2.22 / +2.24 / +2.33 ✗ | −6.54 | −0.89 | 48/20 · 0/56 |

- `--swap-dn-lr steer` her koşulda işareti tam tersine çeviriyor. Bu, tanım gereği böyle; köprünün kablolamasını doğrular, konnektom hakkında bilgi vermez.
- `--ablate-dn steer` her koşulda sabit −0.19 / −0.49 / −0.15 veriyor (perch tabanı).
- **Sonuç: optomotor (a) kapalı döngü öncesinde BAŞARISIZ.**
  - Arenada hemen her görsel sahne sabit bir SAĞ dönüş (+1…+2.3) üretiyor. Yön farkı küçük: yaw_L − yaw_R = +0.26.
  - Kaynak DNa02 normalizasyonu. Ham DNa02 her koşulda SOL baskın (33–68 / 1–20 Hz). Ama sağ referans 2.5 Hz olduğu için sağdaki 6–20 Hz, n_DNa02'yi −1.5…−6.6'ya çekiyor.
  - Ham DNa02 L−R, iki yaw yönünde yön seçici değil (L 47 → 39, R 20 → 16).
- **DNp15 tek başına optomotor işaretini dört yaw koşulunun dördünde de doğru veriyor:** sentetik +4.96 / −1.70; arena +0.51 / −1.22 (+ = sol).
  - DNp15 L yalnız sineğin sağa döndüğü (dünya CCW) koşullarda ateşliyor (18–76 Hz); diğer koşullarda 0.
- Looming DN'leri: DNa01/DNb01 kontralateral kodu bu T4/T5 girdisinde zayıf. DNp01 0–5 Hz (Adım 0 ile aynı).
- *(d) Platform azimutu → dönüş* (açık döngü, 150 mm'den 60 mm/s yaklaşma):
  - İlişki yok. Koyu platform r = +0.32 (yanlış yön), nötr r = −0.13.
  - Her azimutta sabit sağa sapma (+0.6…+1.5) baskın. Koyu ile nötr platform arasındaki fark bu sapmanın altında.

*(b) Kule, kapalı döngü* (`a2_closed.py`; pedestaldan kalkış, 60 adım = 1.5 s, seed 0/1/2):

| Koşul | ort. turn_bias | toplam yön değişimi | kule teması | min. kule açıklığı (mm) |
|---|---|---|---|---|
| normal | +1.20 / +1.03 / +1.26 | −541° / −454° / −578° (sağa daire) | yok | 86 / 84 / 150 |
| `--ablate-dn` | −0.58 / +0.55 / +0.48 | +249° / −233° / −204° | yok | 159 / 153 / 140 |
| `--swap-dn-lr` | −1.64 / −0.86 / −1.28 | +742° / +380° / +358° (sola daire) | yok | 147 / 23 / 152 |

- **Kaçınma da çarpma da yok.** Sinek sabit sağa sapmayla daire çiziyor ve kuleye yaklaşmıyor.
- swap dönüş yönünü tersine çeviriyor. Bu köprü kablolamasının sonucudur; kule davranışı hakkında bir şey söylemez.
- Ablasyonda turn, seed başına sabit ama farklı (−0.58…+0.55). Kaynak: 10 adımlık perch tabanı; sağ DNa02'de tek spike normalize okumayı ~1.6 kaydırıyor.

*(e) Platform yönelimi, kapalı döngü* (`--spawn-air 440 -170 160 60|120`: platform 250 mm kuzeyde, başlangıç azimutu +30° / −30°; 40 adım = 1 s; seed 0/1/2):

| Koşul | az₀ | az @ 0.25 s | toplam yön değişimi | platforma en yakın (mm) |
|---|---|---|---|---|
| koyu, az +30 (platform solda) | +33 / +35 / +30 | +89 / +62 / +119 (sağa döndü, uzaklaştı) | −335° / −301° / −518° | 236 / 220 / 242 |
| koyu, az −30 | −30 / −26 / −29 | −48 / +53 / −33 | −392° / −546° / −422° | 181 / 212 / 175 |
| nötr, az +30 | +29 / +32 / +29 | +77 / +92 / +13 | −565° / −628° / −184° | 234 / 241 / 62 |
| nötr, az −30 | −30 / −27 / −30 | +53 / +85 / −28 | −493° / −485° / −467° | 200 / 205 / 184 |
| `--ablate-dn`, az +30 | +34 / +37 / +29 | +141 / −132 / +21 | −420° / −831° / +47° | 250 / 251 / 30 |
| `--ablate-dn`, az −30 | −31 / −23 / −28 | −55 / +173 / +29 | +74° / −795° / −221° | 217 / 240 / 192 |

- **Yönelim yok.** Koyu ve nötr platform aynı sağa daire davranışını veriyor. Platform solda olduğunda da sinek sağa dönüyor.
- Koyu platformlu 6 koşunun hiçbiri platforma başlangıçtan 75 mm'den fazla yaklaşmadı. Nötr s2 (62 mm) ve ablasyon s2 (30 mm), daire yörüngesinin rastlantısal geçişleri.
- MuJoCo: 27 koşunun hiçbirinde BADQACC ya da kule teması yok.

**Adım 2 değerlendirmesi** (ölçütler başarısız; olduğu gibi raporlanır, kazanç ve normalizasyon değiştirilmedi):
- Önceden yazılan okuma (DNa02 + DNp15, taraf başına sym_prog referansına bölünmüş) kapalı döngüde **yönü konnektomdan değil, normalizasyonun büyüttüğü sağ DNa02 aktivitesinden** alıyor. Sonuç: sabit sağa sapma, yaklaşık +1…+1.8 → 5–9 rad/s.
- Konnektomda yön bilgisi var:
  - DNp15 L/R, dört optomotor koşulun dördünde de doğru işaret veriyor.
  - Ham DNa02 L−R ise optomotor yöne duyarsız.
- Ölçülemeyenler: kule kaçınması ve platform yönelimi. Sabit sapma altında sinek hedefe hiç yaklaşmıyor.
- El yapımı olmayan kısım: T4/T5 → FlyWire → DN (konnektom). El yapımı / VARSAYIM: taraf normalizasyonu, işaret, K_STEER, τ, haltere refleksi, VNC uçuş programı.
- **Karar kullanıcıda** (uygulanmadı). Örnek seçenekler:
  - (i) okumayı DNp15 ile sınırlamak (R2 tablosunda DNp15 ikincildi; veri görüldükten sonra seçim olur);
  - (ii) normalizasyonu fark/ortak mod gibi başka bir biçimde tanımlamak;
  - (iii) normalizasyonsuz ham L−R ile sapmayı raporlamak.
  - Hepsi veriye dayalı seçim riski taşır.

### Adım 2 kararları (kullanıcı, 2026-09-30) — ölçütler koşudan ÖNCE yazıldı
**Karar 1 — NT işareti testi: yalnız duyarlılık testi.**
- `--nt-modulatory-silent` varsayılan KAPALI kalır; sonraki adımlar bu bayrak olmadan yürür.
- Kalıcı durumu kaldıran şey **"tahminsiz NT" kümesi** (Codex `nt_type` NaN, ~17.8k girdi-dışı nöron; broad geçiyor, narrow geçmiyor). "NT tahmini yok" biyolojik bir kategori değildir; bu nöronların çıkışını sıfırlamanın **biyolojik gerekçesi yoktur**.
- Bu sonuç raporda yalnız bu çekinceyle geçer: "kalıcı durum, NT tahmini olmayan nöronların hızlı uyarıcı/inhibitör sayılmasına bağlı; doğru işaretleri bilinmiyor."

**Karar 2 — yön okuması: DNp15 L−R (POST-HOC seçim).**
- Ana okuma **yalnız DNp15 L−R**. DNa02 yalnız kayıt (HDF5 `steer_raw`, `steer_norm_t`'de kalır; yön komutuna katılmaz).
- **POST-HOC etiketi:** DNp15 R2 tablosunda ikincil okuma olarak vardı, ama tek başına ana okuma olması Adım 2 verisi (DNp15'in 4/4 optomotor işareti) görüldükten sonra seçildi. SPEC'te, HDF5 meta'da ve raporda "post-hoc" diye geçer. Adım 2 seed'leri (0/1/2) bu seçimin kaynağıdır; doğrulama yalnız yeni seed'lerle (3/4/5) yapılır.
- **Normalizasyon (VARSAYIM, yeni biçim).** Taraf başına bölme kaldırılır (sağ DNa02 ref 2.5 Hz gibi sıfıra yakın paydaya bölme hatası):
  - n_t = [(r_L − ref_L) − (r_R − ref_R)] / ((ref_L + ref_R) / 2)
  - ref: aynı `data/dn_lr_reference.json` (sym_prog; değişmedi). DNp15: ref_L 15.2, ref_R 63.2 Hz → taban farkı −48.0 Hz çıkarılır, ortak ölçek 39.2 Hz.
  - ŝ = n_DNp15; turn_bias = −K_STEER · ŝ, ±2.5'te kırpılır. **K_STEER = 1 değişmedi**, işaret (ipsilateral) değişmedi, τ = 50 ms değişmedi.
  - Referans uyarana tepki yine ŝ = 0 verir. n_DNa02 de aynı formülle hesaplanıp yalnız kaydedilir.
- Adım 2 tablosundaki ham DNp15 değerleri bu formülle seed 0–2 için işaretleri zaten ima ediyor; bu yüzden o seed'ler doğrulama sayılmaz.

**Doğrulama ölçütleri (sabit; seed 3, 4, 5; tam beyin, `--no-olfaction`, spiking APL, NT değişmemiş).** Başarısızsa olduğu gibi raporlanır; başka okuma, kazanç ya da normalizasyon denenmez.
- **(a) Açık döngü işaret.** `a2_openloop.py --seeds 3 4 5` (aynı FlyVis dizileri; seed yalnız beyin Poisson girdisini değiştirir). Koşullar ve beklenen işaret: `syn_yaw_ccw` SOL (turn < 0), `syn_yaw_cw` SAĞ, arena `yaw_R` SOL, arena `yaw_L` SAĞ. Ölçüt: normal köprünün 250–1000 ms ortalama turn_bias işareti **4/4 koşul × 3/3 seed = 12/12** doğru.
- **(b) Kapalı döngü stabilizasyon (hover + ani yaw bozulması).**
  - Deney tasarımı: `--spawn-air 440 -170 160 90 --hover` (havada hover; gövde eğimi 0, ileri seyir yok; faz makinesi yalnız kanat açık tutar) + `--yaw-perturb 0.5 ±30`.
  - Bozulma: kapalı döngünün t = 0.5 s'sinde 0.1 s süren dış yaw torku (gövde z ekseni). Büyüklük, yalnız pasif sönümle (turn = 0) 30° dönüş verecek biçimde sabit: T = (I_zz / HALTERE_YAW_TAU) · ω_p, ω_p = 30° / 0.1 s = 5.24 rad/s (turn_bias eşdeğeri ≈ 1.05). + = sola (CCW).
  - 60 adım (1.5 s); yön +30 ve −30; seed 3/4/5; normal ve `--ablate-dn steer` → 12 koşu.
  - ω = kaydedilen heading'in zaman türevi. t_on = 0.5 s.
  - **b1:** normal koşuda ort. |ω| [t_on+0.4, t_on+0.5] < 0.5·ω_p (2.62 rad/s), 6/6. *Not (önceden):* HALTERE_YAW_TAU = 20 ms pasif sönüm yüzünden b1'in ablasyonda da sağlanması beklenir; b1 tek başına beyin stabilizasyonu göstermez.
  - **b2 (beyin karşı-dönüşü):** normal koşuda Δturn = ort. turn_bias [t_on, t_on+0.5] − ort. turn_bias [t_on−0.25, t_on], işareti bozulmaya zıt (sola bozulma → Δturn > 0), 6/6.
  - **b3 (ablasyonla karşılaştırma):** Δψ = ψ(t_on+0.5) − ψ(t_on) − ω̄_pre·0.5 (ω̄_pre: [t_on−0.25, t_on] ortalaması). Aynı seed ve yönde |Δψ_normal| < |Δψ_ablate|, 6/6.
  - (b) geçer ⇔ b1 ∧ b2 ∧ b3.
- **(c) Sabit sapma yok.** Açık döngü statik sahneler `perch`, `air_static` (hover, statik arena), `sym_static` (statik simetrik ızgara): 250–1000 ms ort. turn_bias |.| < 0.3, **3 koşul × 3 seed = 9/9**. Kapalı döngü hover'ın bozulma öncesi penceresi [0.25, 0.5] s yalnız kayıt olarak raporlanır.
- **(d) Kule ve platform (başarı iddiası yok).** Pedestaldan kalkış 60 adım; `--spawn-air 440 -170 160 60|120` (platform ±30°) 40 adım; seed 3/4/5; normal ve `--ablate-dn`. `a2_closed.py` ölçüleriyle kaçınma / çarpma / yönelim olduğu gibi raporlanır.

**Doğrulama — sonuçlar** (2026-09-30; seed 3/4/5; tam beyin, `--no-olfaction`, spiking APL, NT değişmemiş; okuma DNp15, post-hoc). Betikler: `a2_openloop.py --seeds 3 4 5` + `--report` (a/c özet satırı eklendi), yeni `a2b_perturb.py` (b), `a2_closed.py` (d).

*(a) Açık döngü işaret: GEÇTİ, 12/12.* turn_bias (+ = sağ), 250–1000 ms, s3/s4/s5:

| Koşul | beklenen | normal | ham DNp15 L−R (Hz) |
|---|---|---|---|
| sentetik yaw, dünya CCW | SOL | −2.50 / −2.50 / −2.50 (kırpık) | +72 |
| sentetik yaw, dünya CW | SAĞ | +1.51 / +1.33 / +1.57 | −106 |
| arena yaw_R | SOL | −0.62 / −0.66 / −0.43 | −26 |
| arena yaw_L | SAĞ | +0.77 / +0.74 / +0.67 | −77 |

- swap her koşulda işareti çeviriyor (tanım gereği). Ablasyon sabit +0.20 / +0.27 / +0.20.
- Looming (kayıt): loom_L +0.15…+0.20 (SAĞ, beklenen yön ama küçük), loom_R +0.23…+0.37 (yanlış yön).

*(c) Sabit sapma: BAŞARISIZ, 6/9.*

| Statik sahne | s3 / s4 / s5 | |.| < 0.3 |
|---|---|---|
| perch | +0.21 / +0.26 / +0.21 | 3/3 |
| air_static (hover) | +0.22 / +0.12 / +0.09 | 3/3 |
| **sym_static** | **−1.22 / −1.22 / −1.19** | **0/3** |

- Kaynak formülün kendisi: statik simetrik ızgarada DNp15 iki tarafta da ~0 Hz (ham L−R −0.6). Taban çıkarımı sessiz DN'yi referans farkına (15.2 − 63.2 = −48 Hz) göre okuyor: ŝ = +48/39.2 = +1.22 → sola dönüş. Yani yeni normalizasyon "DN sessiz" durumunu sıfır değil, güçlü bir sol komut olarak okuyor.
- Arena statik sahneleri (perch, hover) eşiğin altında ama tutarlı sağa (+0.1…+0.26).
- Kapalı döngü hover, bozulma öncesi [0.25, 0.5] s (yalnız kayıt): −0.06 / −0.06 / +0.06.

*(b) Hover + 30° yaw bozulması: BAŞARISIZ (b1 6/6, b2 4/6, b3 4/6).*

| seed | bozulma | normal: Δturn | normal Δψ (°) | ablasyon Δψ (°) | |ω| son pencere normal / abl. (rad/s) |
|---|---|---|---|---|---|
| 3 | +30 (sola) | +0.26 ✓ | −6.4 ✓ | +30.0 | 1.17 / 1.02 |
| 4 | +30 | +0.30 ✓ | −8.3 ✓ | +30.0 | 0.09 / 0.51 |
| 5 | +30 | +0.05 ✓ | +35.0 ✗ | +30.0 | 2.35 / 1.02 |
| 3 | −30 (sağa) | +0.23 ✗ | −56.7 ✗ | −30.0 | 1.98 / 1.02 |
| 4 | −30 | +0.02 ✗ | −26.0 ✓ | −30.0 | 0.95 / 0.51 |
| 5 | −30 | −0.18 ✓ | +10.8 ✓ | −30.0 | 0.72 / 1.02 |

- b1 ablasyonda da 6/6 (önceden yazıldığı gibi pasif sönüm, HALTERE_YAW_TAU = 20 ms); tek başına anlamsız.
- Sola bozulmada (+30) beyin 3/3 sağa karşı-dönüş üretiyor; 2/3'te sapmayı 30°'den 6–8°'ye indiriyor. Sağa bozulmada (−30) karşı-dönüş 1/3; s3'te dönüşü büyütüyor (−57°).
- Asimetri, (c)'deki ve açık döngüdeki tablo ile tutarlı: DNp15 tabanı sağ baskın (perch/hover L 0 / R ~56 Hz); sol DNp15 yalnız sineğin sağa döndüğü akışta ateşleniyor.
- Not: "hover" ileri tilt olmadan da yatay hıza çıkıyor (maks. 79–157 mm/s; ablasyonda 34–68); dönüş komutu–roll bağlaşımından. Ölçüt yaw üzerinden, bu hız ölçülmedi.

*(d) Kule ve platform (başarı iddiası yok).*
- **Kule** (pedestaldan kalkış, 60 adım): normal 3/3 kuleye **çarpıyor** (1.05 / 1.12 / 1.40 s; penetrasyon ≤ 50 µm, BADQACC yok). Toplam yön değişimi −93° / +82° / +72°, ort. turn +0.02…+0.16. Kaçınma yok. Ablasyonda 2/3 çarpma (s5 ıskaladı, açıklık 7.6 mm). Adım 2'deki sabit sağa daire ortadan kalktı; sinek kuleye doğru uçuyor.
- **Platform** (`--spawn-air`, 40 adım = 1 s, koyu platform):

| az₀ | normal s3/s4/s5: yön değişimi | platforma en yakın (mm) | ablasyon: en yakın (mm) |
|---|---|---|---|
| −30 (platform sağda) | −44° / −45° / −58° (sağa, platforma doğru) | **34 / 36 / 33** (1 s'nin sonunda, hâlâ yaklaşıyor) | 177 / 206 / 49 |
| +30 (platform solda) | −21° / −5° / −21° (sağa, platformdan uzak) | 114 / 122 / 146 | 89 / 127 / 127 |

- Platform sağdayken sinek platforma döndü ve 1 s içinde ~33 mm'ye (yatay; z 160, platform üstü 169.5) yaklaştı; solda iken dönmedi. Açık döngüde de aynı yarım yönelim: platform sağdayken sağa dönüş (+0.4…+0.6), solda iken ~0; koyu ve nötr platformda benzer (r = −0.92 / −0.90). Yani bu, koyu platforma özgü değil ve simetrik değil; sağ-baskın taban + sağdaki ileri akış ile açıklanabilir. **Platform yönelimi iddia edilmez.**
- Hiçbir koşuda iniş (platform teması) yok; 1 s'lik pencere buna yetmiyor.

**Değerlendirme.**
- Post-hoc okuma yeni seed'lerde optomotor işaretini koruyor (a).
- Stabilizasyon yalnız tek yönde çalışıyor (b); normalizasyon "DN sessiz" durumunda büyük sol komut üretiyor (c).
- Önceden yazılan kural gereği başka okuma ya da normalizasyon denenmedi. Adım 2 kararları doğrulaması **başarısız** (a geçti; b ve c geçmedi).

**Karar 3 — tur sonunda DUR ve soru:** "Yalnız beyin kararlarıyla (DNp15 yön, MN9 beslenme, VNC uçuş programı, koku yok) sinek kalkıştan başlayıp besine ulaşabiliyor mu?" Bir kez 160 adımlık DEV olmayan koşu (seed 3, pedestaldan kalkış, `--no-olfaction`) ve yörünge raporu.

**Karar 3 — sonuç: 160 adımlık koşu** (`simulations/flight_v10_ablOdor_noOlf_brainonly160_data.h5`; seed 3, tam beyin, DEV değil, pedestaldan kalkış, `--no-olfaction`, DNp15 okuması, MN9 beslenme; video yok). Komut: `env -u PYTHONPATH MUJOCO_GL=egl $PY fly_flight_brain_body_simulation.py --no-olfaction --no-video --n-steps 160 --seed 3 --tag brainonly160`.

| t (s) | konum (mm) | not |
|---|---|---|
| 0 | (0, 0, 22) | kalkış (zamanlı faz, 0.25 s) |
| 0.5 | (35, 29, 27) | seyir, ~300 mm/s |
| 1.0 | (157, 42, 26) | kule 1'in yüzüne 3 mm; hız 87 mm/s'ye düşüyor |
| 1.40 | (~155, −10, 26) | kule teması (1 adım, penetrasyon < 0.1 mm), yüz boyunca güneye kayma |
| 2.0 | (60, −147, 25) | kuleden uzaklaşıyor |
| 3.0 | (−172, −183, 24) | başlangıcın güneybatısı |
| 4.0 | (−240, 68, 22) | besinden 696 mm |

- **Besine ulaşmadı.** Besine en yakın 319 mm (t = 0.97 s). Platform teması 0, MN9 hep 0 Hz, hortum uzatma 0, beslenme 0. Faz hiç `approach`'a geçmedi.
- **İrtifa 21.5–28.8 mm'de kaldı; platform üstü 169.5 mm.** VNC uçuş programında irtifa hedefi yok (yalnız dikey hız sönümü), DNg02 her adımda 0. Yani yön doğru olsaydı bile sinek bu irtifada platformun üstüne çıkamazdı; platform sütununa ancak yandan çarpabilirdi.
- Yön: toplam −318° (net sağa), ort. turn +0.20, ort. |turn| 0.60; platform azimutu ort. |94°| (çoğu zaman platform yanda/arkada).
- Kalıcılık: kesme sonrası 0.083 → 0 Hz. DNp01 toplam 45 spike (kalkış kararı değil; kalkış zamanlı).
- **Cevap: hayır.** Bu kurulumda yalnız beyin kararlarıyla sinek kalkıştan besine ulaşamıyor. Veriden görülen iki bağımsız engel: (1) irtifa: konnektomdan kolektif okuması yok (DNg02 = 0) ve VNC programı platform yüksekliğine tırmanmıyor; (2) yön: DNp15 okuması optomotor işaretini taşıyor ama sağ-baskın tabanla tek yönlü stabilizasyon veriyor, besin yönü hakkında bilgi taşımıyor (koku kapalı, platform yönelimi (d)'de simetrik değil).
- Tek koşu, tek seed; genelleme iddiası yok.

### Dürüst hibrit final (kullanıcı, 2026-09-30) — ölçütler koşudan ÖNCE yazıldı
Bağlam: MN9 beslenme ✅, DNp15 optomotor işareti ✅ (12/12); stabilizasyon (b) ve statik sapma (c) ❌; DNg02 hiç ateşlemiyor; koku DN'lerde lateral sinyal vermiyor; yalnız-beyin koşusu besine ulaşmadı (v10 brainonly160). Final bu yüzden **hibrit**: her terim etiketli ve HDF5'e ayrı yazılır. Kod: `flight/hybrid.py`, bayrak `--hybrid`.

**Bileşenler** (her adımda HDF5 `/behavior`):

| etiket | terim | kaynak |
|---|---|---|
| HAND | `turn_hand` | koku yön eşlemesi 2·tanh(20·I_asym), ℓ_eff 10 mm; yalnız kalkış/seyir |
| HAND | `thrust_hand` (kolektif, lift − 1) | seyir: koku dikey gradyanı 0.8·tanh(10·I_grad) + yalnız tırmandıran taban (platform üstü + 8 mm); yaklaşma: irtifa hedefi 169.5 + 8 = 177.5 mm; iniş: 30 mm/s alçalma |
| HAND | `pitch_hand`, `roll_hand` (gövde eğimi, rad) | seyir 12°; yaklaşma/iniş: dünya çerçevesinde konum kontrolcüsü (platform merkezine, hız = min(300, 3·d) mm/s; platform geometrisini okur) |
| HAND | faz etiketi `phase` | kalkış zamanlayıcısı, yaklaşma yarıçapı 100 mm, `descend` (d < 4 mm, v < 40 mm/s), touchdown (≥ 2 tarsus × 2 adım), bacak açma |
| BRAIN | `turn_brain` | −K_STEER·ŝ(DNp15), mevcut köprü formülü, K_STEER = 1 değişmedi (POST-HOC okuma) |
| BRAIN | `proboscis_extended`, `is_feeding` | beslenme YALNIZ MN9 (CB0701) > 10 Hz; el yapımı beslenme tetiği yok |
| FLYVIS | `turn_flyvis` | b_loom, FlyVis T5 L/R (FlyVis ağı, FlyWire değil; yürüyüş sabitleri, ±0.15) |
| REFLEX | `turn_reflex` | haltere PD'nin yaw sönüm torku, aynı torku veren turn_bias cinsinden; **komuta girmez** |

- `turn_total` = clip(turn_brain + turn_hand + turn_flyvis, ±2.5) = kanat yaw komutu (`turn_bias` ile aynı).
- **İrtifa tamamen HAND.** VNC uçuş programında irtifa hedefi yok (yalnız dikey hız sönümü); DNg02 her koşuda 0 spike (Adım 3 riski gerçekleşti). Raporda böyle yazılır.
- Beyin girdisi üç koşuda da `--no-olfaction` (gıda ORN'leri kapalı). Gerekçe: DNp15 okuması yalnız bu koşulda doğrulandı; kokulu girdide Adım 0'daki kalıcı durum MN9'u ~%70 bastırıyordu; (a)/(b)/(c) aynı beyin girdisini görür. `--hybrid` ile bu bayrak `--ablate-odor` anlamına gelmez: HAND koku navigasyonu koku alanını doğrudan okur, beyin koku almaz.

**v7'de sinek besine 29 mm kala neden asılı kaldı (teşhis) ve HAND düzeltmesi.**
1. Yaklaşma tetiği (genişleme > 5/s) 300 mm/s'de d = 30 mm'de ateşlendi; tek yönlü fren 40 mm/s altında eğimi 0 yaptı, sürükleme sineği durdurdu (5cc0786'da eski yol için düzeltildi).
2. İrtifa yalnız koku I_grad'ından geliyordu: toraks damla yüksekliğinde (z 170) tutuluyor, açık bacakların tarsusları 1.5–3 mm aşağıda, platform üstünün (169.5) altında kalıyor → sinek platform sütununun yan yüzüne geliyor (v8_DEV: r = 10.7 mm'de sıkıştı).
3. Kaynak yakınında koku dönüş döngüsü kararsız (kazanç ~86/s, 25 ms ZOH): yön ±7° salınıyor; yalnız ileri eksende hız kontrolü yanal kaymayı gideremiyor.
- **Düzeltme (HAND):** yaklaşmada irtifa hedefi platform üstü + 8 mm; dünya çerçevesinde, yönden bağımsız yatay konum kontrolcüsü; yaklaşmada koku dönüşü kapalı; platform üstüne gelince dikey iniş.
- **Beyinsiz doğrulama** (`scripts/diag/hyb_landing.py`; FlyWire yok, FlyVis yok):
  - İlk tasarım (seyirde sabit irtifa hedefi 177.5 mm): kule 1'in batı yüzüne çarpıp 3 s boyunca yüz boyunca kaydı (16 adım kule teması). Koku alanı (3D Dijkstra) kule 1'in önünde "üstünden aş" yönünü veriyor; sabit hedef bununla çelişiyordu. → seyirde irtifa koku dikey gradyanına bırakıldı, hedef yalnız taban.
  - İkinci tasarım (koku dönüşü yaklaşmada açık, eski −v_z sönümü): 1 adım kule köşe teması (z 181'de), sonra platform üstünde d_xy 4–6 mm'de 5 s daire çizdi (koku dönüşü ±2'de doygun; dönüş–yatış bağlaşımı). → yaklaşmada koku dönüşü kapatıldı, seyirde tırmanışı frenleyen sönüm kaldırıldı.
  - Son tasarım: kule 1'in üstünden (z 200–213, en yakın açıklık 3.7 mm), touchdown 3.0 s, temas hızı 1 mm/s, kule teması 0.
  - v10 yalnız-beyin koşusunun kayıtlı DNp15 dönüş serisi beyin vekili olarak eklendi (ofset 0/40/80 adım): 3/3 iniş, touchdown 3.7 / 4.1 / 2.85 s; ofset 80'de bir adım içi kule dokunuşu (0.012 mm; adım sonu temas bayrağı 0).
  - HAND sabitleri bu beyinsiz koşularda belirlendi; beyinli hibrit koşular görüldükten sonra değiştirilmez.

**Koşular** (seed 3, n_steps 300, tam beyin, DEV değil, spiking APL, NT değişmemiş, pedestaldan kalkış):
- (a) `--hybrid --no-olfaction --tag final_a`
- (b) `--hybrid --no-olfaction --ablate-dn DNp15 --tag final_b` — DNp15 okuması perch tabanına sabitlenir (mevcut ablasyon anlamı): turn_brain sabit bir değer olur, 0 değil (Adım 2 (a)'da ≈ +0.2).
- (c) `--no-olfaction --tag final_c` — yalnız beyin, v10 brainonly160 ayarları (VNC programı, HAND navigasyon yok); v10 dosyası yeni spike şemasında olmadığı için yeniden koşulur.
- **n_steps = 300 (7.5 s) gerekçesi:** beyinsiz vekil koşularda touchdown 2.85–4.1 s; temastan MN9 > 10 Hz'e gecikme Adım 1'de 50–75 ms; + 2 s beslenme → ≈ 6.2 s. Gerçek beyin terimi yaklaşmayı geciktirebileceği için ~1.3 s pay → 7.5 s = 300 adım. (c) aynı n_steps.

**Başarı ölçütü (her koşu için ayrı):**
- **S1 — kuleye girmeden platform teması:** faz `touchdown`a geçer (≥ 2 tarsus × 2 ardışık adım platformda) ve touchdown'a kadar **hiçbir adımda kule teması yok**: `tower_contact` = 0 ve `tower_penetration` = 0 (adım içi dokunuş da temas sayılır; penetrasyon büyüklüğü ayrıca raporlanır).
- **S2 — beslenme:** touchdown'dan sonra en az bir adımda `is_feeding` = 1 (landed ∧ MN9 > 10 Hz).
- Başarı = S1 ∧ S2. Ayrıca raporlanır (ölçüt değil): touchdown zamanı ve hızı, beslenme adım sayısı/süresi, MN9 ortalaması, kule açıklığı.

**Beyin katkı ölçüsü (önceden tanımlı):**
- Birincil: **Σ|turn_brain| / Σ|turn_total|**, kanatların açık olduğu adımlarda (`wings_on` = 1). HDF5 `meta.turn_share.brain_over_total`.
  - Terimler zıt işaretliyse ya da kırpma olursa 1'i geçebilir; bu yüzden yanında ikincil ölçü de verilir.
- İkincil: dört bileşenin Σ|·| payları (brain / hand / flyvis / reflex; `meta.turn_share.share_*`).
- (b)'de turn_brain sabit perch tabanıdır; ölçü yine hesaplanır ve böyle etiketlenir.
- Kolektif ve gövde eğiminde beyin payı tanım gereği 0 (HAND).

**Yorum kuralları (önceden):**
- Tek seed; genelleme iddiası yok.
- (a) ile (b) arasındaki fark betimsel raporlanır. (a) başarılı, (b) başarısız olsa bile "beyin gerekli" denmez; tek koşu, ve (b)'de beyin terimi 0 değil sabit bir sapmadır.
- Başarı, davranışın HAND katmanından geldiğini değiştirmez: navigasyon, irtifa, yaklaşma ve iniş el yapımıdır; beynin payı yaw'a eklenen DNp15 terimi ve MN9 beslenme kararıdır.
- Başarısızlık olduğu gibi raporlanır; HAND sabitleri, kazançlar ve okuma değiştirilip yeniden denenmez.

**Smoke** (2026-09-30; tam beyin, seed 3, `--no-olfaction --n-steps 20 --no-video`; sonuç değil):

| mod | 0.5 s'de konum (mm) | Σ\|brain\|/Σ\|total\| | pay brain/hand/flyvis/reflex | adım (s) | duvar süresi | tepe RSS |
|---|---|---|---|---|---|---|
| (a) hibrit | (46, 3, 134) | 1.53 | 0.41 / 0.45 / 0.01 / 0.13 | ~1.0 | 47 s | 3.49 GB |
| (b) hibrit + abl. DNp15 | (43, 26, 135) | 1.01 | 0.27 / 0.53 / 0.04 / 0.16 | ~1.0 | 46 s | 3.49 GB |
| (c) yalnız beyin | (31, 23, 27) | 1.00 | 0.64 / 0 / 0 / 0.36 | ~1.0 | 46 s | 3.48 GB |

- (a)'da oran > 1: ilk 0.5 s'de beyin terimi koku terimine çoğunlukla zıt işaretli (toplam komut küçülüyor). Önceden yazıldığı gibi ikincil paylar birlikte okunur.
- (b)'de turn_brain sabit +0.10 (perch tabanı).
- Kalıcılık: kesme sonrası 0.083 → 0 Hz. DNg02 0/0. Kule teması 0, BADQACC yok.
- Tahmin: 300 adım × ~1.05 s + ~30 s kurulum/kalibrasyon ≈ 6 dk/koşu; 3 koşu ≈ 18–20 dk; + 3 video (900 kare, ~1.5–2 dk/video) → toplam ~25 dk. Başlatma: `run_final.sh`.

### Adım 3 — Güç / irtifa / ileri hız / kalkış
- **Kalkanlar:**
  - `pitch_odor` (I_grad), `pitch_alt` (−v_z sönümü), ventral refleks, kalkış artışı;
  - sabit seyir eğimi θ_cruise (12°) ve approach fren eğimi.
- **Güç:** ĉ = DNg02 → kolektif genlik (köprü).
- **İleri hız:**
  - Haltere refleksi tutum hedefi seviye (0°) olarak sabitlenir; bu refleks, karar değil.
  - Strok düzlemi gövdeye göre sabit bir morfolojik eğimle köprüde tanımlanır.
  - İtki böylece yalnız güçle (DNg02) değişir. İleri hız için ayrı DN kararı **yok**; bunu literatür boşluğu olarak raporla.
- **Kalkış:**
  - DNp01 veya DNp02/04/11 popülasyonu eşiği aşınca.
  - Senaryo başında bir looming uyaranı verilir (kullanıcı kararı 4); sinekte gönüllü kalkış için beyin tetiği bilinmiyor.
  - Uyaran: kaideye yaklaşan koyu bir disk. Render'da görünür, fizikte yok (contype 0).
  - HDF5 ve raporda **"deney tasarımı"** olarak etiketlenir.
- **Başarı:**
  - DNg02 > 0 ve irtifa değişimiyle ilişkili;
  - `--ablate-dn dng02` ile irtifa kontrolü kaybolur;
  - kalkış yalnız looming varken olur.
- **Risk ÇOK YÜKSEK:** DNg02 bugün hiçbir girdiyle ateşlenmiyor. Adım 0'daki gerçek görme girdisinden sonra da 0 kalırsa **kolektif beyinden gelemez**. O zaman köprü sabit hover gücünde kalır ve irtifa kontrolsüz olur. Bu durumda sonuç olarak "uçuş gücü konnektomdan okunamadı" raporlanır; başka bir DN'e geçilmez (veriye dayalı seçim yasağı).

### Adım 4 — İniş
- **Kalkanlar:** geometrik genişleme oranı tetiği (ṙ/r > 5 /s), hız orantılı fren, `stand` pozu tetiği.
- **Yerine:** DNp07 + DNp10 > eşik → bacak açma. Yavaşlama yalnız DNg02/DNa02 değişiminden gelebilir.
- **Başarı:**
  - platform yaklaşmasında DNp07/10 artışı (R3'te ileri akışta DNp07 36/47 Hz);
  - temasta hız < 50 mm/s;
  - `--ablate-dn landing` ile bacak açılmaz.
- **Risk YÜKSEK:** Literatür künyesi doğrulanmalı. Yavaşlama için DN yolu belirsiz. Platform yanına çarpma (v8'de görüldü) muhtemel.

### Dosyalar (onaydan sonra; yürüyüş kodu ve `tests/` bozulmaz)
**Yeni:**
- `flight/vnc_bridge.py`
- `flight/readouts.py` (önceden belirlenmiş setler; root_id → indeks)
- `flight/visual_input.py` (FlyVis → FlyWire kolon eşlemesi)
- `data/column_assignment.csv.gz` (~460 KB; `~/Downloads`'tan kopya) + `data/README.md` (kaynak: FlyWire/Codex visual columns, Matsliah et al. 2024 / Zhao et al. 2024; lisans)
- `tests/flight/test_readouts.py`, `test_visual_input.py`, `test_vnc_bridge.py`

**Değişen:**
- `flight/brain.py` (girdi grupları, per-nöron oranlar)
- `flight/groups.py` (şeker GRN, gıda ORN setleri)
- `flight/controller.py` (terimler tek tek kaldırılır; her adım ayrı commit)
- `flight/body.py` (arena dokusu, koyu/yüksek kontrastlı platform, kalkış looming uyaranı)
- `fly_flight_brain_body_simulation.py` (`--ablate-dn/--swap-dn-lr/--asc-legacy`)

**Korunan:** mevcut el yapımı yol `--legacy-control` bayrağıyla karşılaştırma için kalır.

## Doğrulama
- Her adım: `env -u PYTHONPATH .../python -m pytest tests/` ve `--n-steps 20 --no-video` smoke. Teşhis betikleri `scripts/diag/` altında ve tekrarlanabilir.
- R0 kalıcı regresyon testi: şeker 100 Hz → MN9 > 40 Hz (slow).
- Adım 0 testi: temiz başlangıçta girdi kesilince aktivite söner.
- Adım 2 testi: sol göz yaw akışı → DNp15_L > DNp15_R (taraf konvansiyonu).
- Rapor: her davranış terimi için DN payı ile köprü/refleks payı ayrı ayrı. Ablasyon ve swap eğrileri tek grafikte.
