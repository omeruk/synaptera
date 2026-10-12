# CLAUDE.md — synaptera-banc-brain

Bu dosya, bu repoda çalışan Claude Code oturumları için kalıcı talimattır. Yeni projenin köküne kopyalanır.

## Proje

Synaptera v1.0.0'ın (FlyWire v783 tam-beyin LIF modeli + FlyGym/MuJoCo gövdesi, kapalı döngü *Drosophila* uçuşu)
devamı. Hedef: BANC (beyin + sinir kordonu) connectome'u ile el yapımı DN → kanat köprüsünü, refleksleri ve tetikleri
connectome'a devretmek; bunu ölçülebilir, ön-kayıtlı ve kontrollü deneylerle göstermek.
- Mimari ve yol haritası: `docs/05_MIMARI_PLAN.md` (fazlar F1–F6, kapılar, risk kaydı).
- Önceki çalışmanın incelemesi: `docs/01_KOD_INCELEMESI.md` … `docs/04_ARASTIRMA_NOTLARI.md`.
- Taşınan kodun kökeni: `docs/06_YENI_PROJE_KURULUMU.md` ve `vendor/synaptera_v1/MANIFEST.md`.
- Synaptera v1.0.0 (github.com/omeruk/synaptera) **donmuş arşivdir**; ona kod yazılmaz.

## Ortam ve komutlar

- Python ortamı: conda `neurofly` (Python 3.10; Brian2 2.9.0, MuJoCo 3.2.7, FlyGym 1.2.1, FlyVis 1.2.0, numpy 2.0.2).
- Her komut `env -u PYTHONPATH ...` ile çalıştırılır (kabuk profilindeki başka bir PYTHONPATH paketleri gölgeleyebilir).
- Başsız render: `export MUJOCO_GL=egl` (sistemde `libegl1`, gerekirse `libosmesa6`).
- Testler: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 env -u PYTHONPATH python -m pytest tests/` (tam-beyin testleri `--runslow`).
- Veri: `env -u PYTHONPATH python scripts/fetch_data.py` (SHA-256 sabitli indirme; Codex dosyaları giriş gerektirir:
  `--codex-dir ~/Downloads`). Veri dosyaları (`brain_model/`, `data/`, `banc/`, `runs/`) **asla commit edilmez**.
- Bir tam-beyin koşusu ~3,5 GB RAM (FlyWire); BANC ~188k nöron daha fazlasını ister. Uzun koşular `nohup` ile ve
  `runs/<ad>/` altında; ilerleme logdan izlenir.

## Değişmez kurallar

1. **Kaynak etiketi:** her motor ve duyu terimi tek etiket taşır — `BRAIN`, `VNC`, `HAND`, `REFLEX`, `TRAINED`,
   `FLYVIS` — ve kayıtta ayrı tutulur. Etiketi belirsiz bir terim eklenmez.
2. **Parametre kökeni:** her sabit `configs/assumptions.json`'da köken sınıfıyla kayıtlı: `M` ölçülmüş, `P` popülasyon
   önceli, `F` uydurulmuş (neye uydurulduğu yazılı), `E` mühendislik iskelesi, `I` kurtarılamaz.
3. **Davranışa göre ayar yok:** sabitler davranışsal başarıya bakılarak ayarlanmaz; yalnız açık döngü fizyoloji/
   anatomi ölçütleriyle ve bu ölçütler önceden yazılarak.
4. **Nedensel zamanlama:** beden, nöral motorun çıktısını **bir eşleme aralığı gecikmeli** alır (komut kuyruğu);
   gecikme konfigürasyonda ve kayıtta açık. Aynı aralıkta üretilen spike'la aynı aralıktaki bedeni sürmek yasak
   (Synaptera v1 hatası Y1).
5. **Simetri kapısı:** sol/sağ okuma veya yol, giriş sinapsı oranı |log2(R/L)| < 0,5 kapısından geçmeden deneyde
   kullanılmaz (`scripts/analysis/dn_lr_asymmetry.py` genellemesi). Kapı sonucu raporlanır.
6. **Ön-kayıt:** kriterler ve karar kuralları koşulardan **önce** commit edilir (ve mümkünse OSF'ye kaydedilir);
   sonradan değiştirilmez. Sonradan eklenen her şey "post-hoc" etiketlidir.
7. **Kontroller:** her deneyde aktivite-eşli karıştırılmış graf, aynı dereceli rastgele graf ve ablasyon; eğitimde
   ek olarak lineer + MLP. Tohumlar fiziksel gürültüyü de değiştirir; en az 5 tohum.
8. **Referans kol değiştirilmez:** spiking referans kolu Shiu ve ark. parametreleriyle çalışır; her sapma (işaret
   kuralı, nöron modeli, girdi yolu) bayrakla açılan, adı konmuş bir **model varyantı**dır.
9. **Bilgi uyumu:** eğitimde öğretmen sinyali beynin aldığı duyulardan çıkarılabilir olmalı; önce beyinsiz "bypass"
   kolunda çapraz-doğrulamalı R² > 0 gösterilir (Synaptera v1 hatası Y3).
10. **Negatif sonuçlar** eşit ağırlıkla raporlanır. `DEV` alt ağ koşuları asla sonuç değildir.
11. **Sayılar elle yazılmaz:** raporlardaki her sayı kayıtlardan bir betikle yeniden hesaplanır ve
    `scripts/verify_report.py` ile metne karşı denetlenir.
12. **Lisans:** NeuroFly'dan uyarlanmış kod (Synaptera `docs/ADAPTED_CODE.md`) taşınmaz. BANC verisi CC BY 4.0,
    FlyWire verisi CC BY-NC 4.0; türev dosyalar kaynağının lisansını taşır.
13. **Sonuç dosyaları korunur:** var olan bir koşu çıktısının üzerine yazılmaz (yeni sürüm veya açık `--overwrite`).

## Git

- Dallar: `omeruk/<konu>`; `main`'e yalnız PR ile.
- Kod, commit mesajları ve kod yorumları İngilizce; lab defteri ve planlar Türkçe (`docs/`).
- Her PR: ilgili testler + (varsa) doğrulama betiği çıktısı.
