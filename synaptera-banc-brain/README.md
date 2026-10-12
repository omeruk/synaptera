# Synaptera: BANC Brain — bağımsız analiz ve sonraki çalışma planı (2026-10-12)

Bu klasör ("Synaptera: BANC Brain"), Synaptera v1.0.0 anlık görüntüsünün kod, model, fizik ve test incelemesini; bağlantı yapısı (connectome)
üzerindeki yeni analizleri; BANC olanaklarını; benzer çalışmalara ("The Driving Fly", The Uploading Lab vb.) dair
araştırma notlarını ve bir sonraki çalışma için mimari planı içerir. Dil: Türkçe (lab defteri `docs/tr/` ile tutarlı).
Bu dosyalar anlık görüntüden **sonra** eklendi; `docs/SNAPSHOT_MANIFEST.md` listesinde yoktur.

| belge | içerik |
|---|---|
| [01_KOD_INCELEMESI.md](01_KOD_INCELEMESI.md) | Hatalar ve eksiklikler; yüksek/orta/düşük önem; öncelikli düzeltme listesi |
| [02_MODEL_FIZIK_TEST_ANALIZI.md](02_MODEL_FIZIK_TEST_ANALIZI.md) | Bağlantı yapısı analizi, beyin modellemesi, fizik motoru, beyin testleri ve sonuçlarının değerlendirmesi; bu oturumdaki test/simülasyon sonuçları |
| [03_BANC_OLANAKLARI.md](03_BANC_OLANAKLARI.md) | BANC beyni + sinir kordonu ile yapılabilecekler ve olası sonuçlar |
| [04_ARASTIRMA_NOTLARI.md](04_ARASTIRMA_NOTLARI.md) | The Driving Fly (flyhard), fly-self-driving, flydrive, The Uploading Lab, Eon, Fly.exe, fly-cartpole… nasıl yapıldı |
| [05_MIMARI_PLAN.md](05_MIMARI_PLAN.md) | Synaptera-2 için katmanlı mimari, fazlı yol haritası, risk kaydı |
| [06_YENI_PROJE_KURULUMU.md](06_YENI_PROJE_KURULUMU.md) | Yeni projenin (`omeruk/synaptera-banc-brain`) kurulumu: `yeni_proje/kur.sh`, taşıma listesi, `CLAUDE.md`, terminalde ilk istek |
| `veri/` | Bu analizin sayısal çıktıları (FlyWire v783'ten türetilmiş → CC BY-NC 4.0, repo politikası gibi) |

Analiz betikleri: `synaptera-banc-brain/scripts/connectome_structure.py`, `synaptera-banc-brain/scripts/dn_lr_asymmetry.py`,
`synaptera-banc-brain/scripts/grn_mn9_check.py` (veri: `scripts/fetch_data.py` ile indirilir).

## Repo düzeni (işlerin karışmaması için)

| ne | nerede | not |
|---|---|---|
| Yayımlanmış Synaptera v1.0.0 (kod, raporlar, şekiller) | bu repo, kök dizin | **Değiştirilmez.** `docs/SNAPSHOT_MANIFEST.md` dosya listesi ve SHA-256'ları geçerli kalır |
| Bu analiz ("Synaptera: BANC Brain") | bu repo, `synaptera-banc-brain/` | Yalnız bu klasöre yazılır; kök dosyalara dokunulmaz |
| Mevcut koddaki hata düzeltmeleri (plan F0: komut kuyruğu, simetri kapısı, üzerine yazma koruması, Φ kırpma…) | bu repo, ayrı dal → PR | Birleşince **v1.1** olarak etiketlenir; v1.0.0 sonuçları yeniden üretilip karşılaştırılır |
| Asıl BANC çalışması (plan F1–F6: veri hattı, VNC, refleks, eğitim) | **yeni repo** (öneri: `omeruk/synaptera-banc-brain`) | Farklı mimari ve veri lisansı (BANC CC BY 4.0 / FlyWire CC BY-NC); bu klasördeki plana bağlantı verir |

Dal adları: `omeruk/<konu>` (ör. `omeruk/v1.1-duzeltmeler`). `main`'e yalnız PR ile girilir.

## Yönetici özeti

**Kod:** Raporlanan sonuçları geçersiz kılan bir kod hatası bulunmadı. Test paketi: **123 geçti, 51 atlandı, 0 başarısız**
(atlamaların çoğu giriş gerektiren Codex verisi yüzünden). Türetilebilir 4 veri dosyası geliştirici kopyasıyla SHA-256 düzeyinde
aynı. Yüksek önemli bulgular:
1. **Beyin–beden adım içi akausalite:** beden, aynı 25 ms aralıkta "gelecekte" üretilen spike'larla sürülüyor (komut kuyruğu gerekli).
2. **Sol/sağ asimetri kontrolü yok:** DNp15'in sağ girdisi solun 1,66 katı (383 DN içinde 65. en asimetrik), DNp10'unki 0,24 katı
   (8.) → raporlanan iki lateral okuma başarısızlığı connectome'dan öngörülebilirdi.
3. **Eğitim merdiveninde bilgi uyumsuzluğu:** öğretmenin dönüş komutu koku alanından, beyin yalnız görsel girdi alıyor; DAgger turları yapılmadan durduruldu.
4. **Görsel örnekleme 80 Hz:** kuleye 4,4 mm'de ~49°/kare kayma → hareket algısı örtüşmeli.
5. **Kanat strok genliği sınırsız:** ~206°'ye çıkabiliyor.

**Bağlantı yapısı (yeni bulgular):**
- Bacak şeker GRN'lerinden MN9'a işaretli doğrusal etki **negatif**, labellar GRN'lerden **pozitif** → bacak GRN → MN9 başarısızlığı yapısal;
  bu oturumda değiştirilmemiş Shiu modeliyle bağımsız olarak da doğrulandı (12 bacak GRN @100 Hz → MN9 0/0 Hz; labellar 36 GRN → 54–55 / 48 Hz; iki tohum).
- DNg02 girdisinin %54'ü inhibitör ve bir kısmı hiç sürülmeyen yükselen nöronlardan → sessizlik erişilebilirlikten değil, net inhibisyon + tonik sürüş yokluğundan.
- Antenal lobta LN+PN iç sinapslarının %77'si uyarıcı (Shiu işaret kuralı aminleri uyarıcı sayıyor); baskın özdeğer ~2.184 sinaps → kendini sürdüren kilitlenme yapısal olarak beklenir.
- Modelde kanat/haltere/bacak motor nöronu yok; 1.736 yükselen nöron hiç sürülmüyor.

**BANC:** VNC'yi ve gerçek kanat/haltere/bacak motor nöronlarını getiriyor, CC BY 4.0. En değerli olası kazanımlar: DN → kanat
köprüsünün connectome'a devri, haltere refleksinin connectome'dan gelmesi, bacak tat → MN9 doğal tetiği, GF ile kalkış.
Riskler: proofreading kaynaklı L/R asimetrisi (güncel Codex dışa aktarımında optik lob sağ/sol 1,56×), seyreklik (FlyWire'dan ~2,6× az sinaps/nöron), dinlenme aktivitesi yokluğu. Güncel Codex BANC dışa aktarımında MN9, 62 kanat MN'si, 25 haltere MN'si ve TTMn mevcut (`03_BANC_OLANAKLARI.md` ek A).

**Benzer çalışmalar:** "Sürüş" projelerinin hepsi topolojiyi sabit tutup **dinamik parametreleri veya okuma katmanını eğitiyor**
(rate modeli + girdi normalizasyonu + durumun taşınması + taklit + DAgger); hiçbirinde uçuş tamamen nöral değil.

**Plan:** F0 mevcut repo düzeltmeleri → F1 BANC veri hattı + QA → F2 açık döngü yeniden üretimler → F3 VNC motor arayüzü ve
haltere refleksi → F4 kalkış/iniş/beslenme tetiği → F5 eğitilebilir connectome kolu → F6 tam görev. Ayrıntı: `05_MIMARI_PLAN.md`.

## Erişim notu
`thedrivingfly.com` ve `theuploadinglab.ai` (ve Harvard Dataverse, arXiv, Nature) bu çalışma ortamının ağ politikasınca
engelliydi; araştırma notları projelerin GitHub depolarındaki belgelere ve arama sonuçlarına dayanır (`04_ARASTIRMA_NOTLARI.md` §0).
