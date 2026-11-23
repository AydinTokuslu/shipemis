# Excel çalışma kitaplarının denetimi (Türkçe)

Bu belge, doktora tezinde (Tokuşlu, 2019) kullanılan Excel dosyalarının Python'a
aktarılması sırasında bulunan sorunları ve bunların 2015 yılı sonuçlarına etkisini
özetler. Bulgular doğrudan dosyalardaki formüllerden ve kayıtlı değerlerden
okunmuştur.

`shipemis` paketindeki `replicate_thesis_*` fonksiyonları incelenen **38 dosyanın
tamamını sıfır farkla** yeniden üretir. Dosyalar: 12 aylık ENTEC transit, 12 aylık
Trozzi transit ve 7 firmanın iki yöntemle hazırlanmış 14 yerel trafik dosyası;
toplam ~87.000 satır. Yani aşağıdaki sorunlar Python'un değil, Excel'in
davranışıdır. Ayrıntılı sayılar `results/` klasöründeki CSV dosyalarındadır.

## 1. Özet: 2015 transit geçişleri (43.544 geçiş)

| CO₂ (t/yıl) | Tez | Düzeltilmiş (Python) |
|---|---:|---:|
| Trozzi & Vaccaro | 937.017 | **134.102** |
| Entec UK Limited | 1.086.585 | **157.711** |

| Diğer kirleticiler (t/yıl) | NOx | SOx | PM | VOC | CO |
|---|---:|---:|---:|---:|---:|
| Trozzi – tez | 18.324 | 5.294 | 692 | 693 | 2.138 |
| Trozzi – düzeltilmiş | 2.493 | 562 | 69 | 97 | 299 |
| Entec – tez | 19.987 | 9.150 | 1.143 | 747 | – |
| Entec – düzeltilmiş | 3.497 | 2.661 | 335 | 130 | – |

Düzeltilmiş hâlleriyle iki bağımsız yöntem CO₂'de %18 içinde birbirini tutuyor.
Tezin Tablo 28 ve giriş bölümünde aktarılan Kesgin & Vardar (2001) transit
sonucu (1998 için 173.362 t CO₂, 4.344 t NOx) da aynı büyüklükte. Bu, düzeltilmiş
değerlerin makul olduğunu destekliyor.

Tezdeki değerler düzeltilmiş değerlerin CO₂'de yaklaşık **7 katı**, NOx'te
**5–7 katı**.

## 2. Entec dosyaları

| # | Sorun | Nerede | Etki |
|---|---|---|---|
| E1 | Yük faktörleri yüzde olarak (80, 30…) girilmiş, formülde 100'e bölünmemiş. Bölenler seyirde 10⁶, manevra/limanda 10⁷. | Tüm dosyalar | Seyir **100×**, manevra ve liman **10×** büyük |
| E2 | Seyir formüllerinde yöntemde olmayan sabit çarpanlar: NOx ×5, CO₂ ×6, VOC ×5, PM ×3, SOx ×3 | 12 transit dosyasının tamamı | Transit seyir ek olarak 3–6× büyük (toplam 300–600×) |
| E3 | VOC formüllerinde ×4 çarpanı | 7 yerel dosyanın tamamı | VOC ek olarak 4× büyük |
| E4 | Toplam satırı `=SUM(…3:…43)` yalnızca ilk 41 gemiyi topluyor | 12 transit dosyasının tamamı ve Turyol yerel | Bkz. aşağı |
| E5 | Tezde emisyon faktörlerinin birimi "kg kirlilik/ton yakıt" yazıyor; doğrusu g/kWh (CO₂/SFC ≈ 3,18) | Tez tablo 16–18 | Metin düzeltmesi |
| E6 | Veri satırlarının altında `#REF!` içeren eski şablon formülleri var | Yerel dosyalar | Sonuca etkisi yok |

**E4'ün tezdeki karşılığı:** "AY AY EMİSYON ANALİZİ İSTATİSTİĞİ" dosyasındaki
aylık değerlerin 12'si de, ilgili ayın dosyasındaki ilk 41 geminin toplamıyla
birebir aynı. Örneğin Ağustos'ta 83.075 t CO₂ yazıyor; bu, 3.564 geçişten ilk 41'inin
toplamı. Tezdeki yıllık 1.086.585 t bu 12 kısmi toplamın toplamıdır. E1 ve E2
hataları değerleri yaklaşık 600 kat büyüttüğünden, yalnızca ~%1'lik satırın
toplanması sonucu tesadüfen gerçeğe yakın bir büyüklüğe çekmiş. Tüm satırlar
toplansaydı Excel yılda 94,6 milyon t CO₂ verirdi.

## 3. Trozzi & Vaccaro dosyaları

| # | Sorun | Nerede | Etki |
|---|---|---|---|
| T1 | General Cargo yakıt katsayısı 9,8197 yerine **98,197** girilmiş | FORMUL!B5 (tüm dosyalar) | General Cargo yakıtı ~10× büyük. Transitte tezdeki CO₂'nin %76–79'u bu tipten geliyor |
| T2 | Günlük tüketim (t/gün) saate çevrilirken 24 yerine 10'a bölünüyor | Transit | Transit tüm sonuçlar **2,4×** büyük |
| T3 | Yakıt `C(GT)/10` olarak hesaplanıyor; ayrıca NOx ve VOC için ek /10, CO ve SOx için /2 bölenleri var | Yerel | Kirleticiler arasında tutarsız ölçek |
| T4 | Mod emisyon faktörü sayfalarında CO₂ = 3,2 (t/t), jeneratör sütununda 3200 (kg/t) | Yerel | Mod katkıları CO₂'de 1000× küçük; CO₂'yi jeneratör terimi belirliyor |
| T5 | Jeneratör emisyon faktörü, kendi yakıtı ve süresi olmadan liman EF'sine ekleniyor | Yerel | Yöntemle uyumsuz |
| T6 | Jeneratör NOx regresyonunda işaret hatası: kaynakta **−2,47·P**, Excel'de **+2,47·P** | Yerel, M sütunu | P=70 kW için 343,9 kg/t (tablo değeri ~25–30 kg/t) |
| T7 | CO₂ jeneratör faktörü aşağı sürüklenince artmış: 3200, 3201 … | Turyol (…3231), Dentur (…3220), Mavi Marmara (…3208), Şehir Hatları (…3207) | Küçük (%1'e kadar), ama veri hatası |
| T8 | Transit dosyalarında VBA makroları kaydedilmemiş; yalnızca değerler var. Formül değerlerden geri çözülmüştür ve 12 ayın tüm satırlarında tutuyor (fark < 10⁻¹⁵) | Transit .xls | Yeniden üretilebilirlik |

Trozzi transitte toplama hatası yok: tezdeki yıllık değer (937.017 t CO₂),
12 aylık dosyanın tüm satırlarının toplamına eşit (937.018 t).

## 4. Yerel trafik

**Tezdeki toplamların kaynağı:** Tablo 27'deki değerler, EK 7–18'deki firma
toplamlarının toplamıdır (Beyden için EK tablosu yok, dosya değeri eklenince tutuyor):

* Trozzi: EK toplamları + Beyden = 315.308 t CO₂ (tezde 315.310 t)
* Entec: EK toplamları + Beyden = 321.269 t CO₂ (tezde 321.269 t)

**Yüklenen dosyaların bir kısmı EK'lerdekiyle aynı sürüm değil:**

| Firma | Trozzi dosya / EK (t CO₂) | Entec dosya / EK (t CO₂) |
|---|---|---|
| İDO | 68.058 / 68.058 ✓ | 6.872 / 6.872 ✓ |
| Turyol | 106.741 / 106.741 ✓ | 92.746 (ilk 41 gemi; tümü 117.630) / 124.216 |
| Şehir Hatları | 58.509 / 33.258 | 114.216 / 153.103 |
| Dentur | 84.046 / 47.963 | 10.406 / 10.406 ✓ |
| Boğaziçi | 40.933 / 23.359 | 4.257 / 4.257 ✓ |
| Mavi Marmara | 59.375 / 33.884 | 15.813 / 15.813 ✓ |
| Beyden | 2.047 / – | 6.602 / – |

Python yüklenen dosyaları birebir üretir. Farklı sürümler bulunursa onlar da
aynı şekilde kontrol edilebilir.

**Eski Excel girdileri:** Yerel trafik dosyalarında formül hatalarına ek olarak
girdiler de genel değerlerden oluşuyordu. Trozzi dosyalarında her gemiye seyir,
manevra ve limanda 1'er gün girilip ×365 yapılmış. Entec dosyalarında 192 geminin
tamamına 1500 kW / 530 kW verilmiş.

### 4.1 Yeni gemi bazlı girdi tablosu

`scripts/build_local_fleet.py`, firmaların emisyon envanteri dosyalarından ve tezin
EK 1–6 listelerinden 221 gemilik bir girdi tablosu (`data/local_fleet_2015.csv`)
oluşturur. Her değerin kaynağı tabloda ayrı bir sütunda yazılıdır.

| Girdi | Kaynak |
|---|---|
| Yıllık mesafe, tonaj, makine tipi | Firma envanter dosyaları |
| Ana makine gücü | Envanter (Şehir Hatları, Mavi Marmara, Turyol); EK 2, 4, 5 (İDO, Dentur, Boğaziçi); İDO'nun EK'de olmayan gemileri için üretici değerleri veya EK'deki kardeş gemi |
| Yardımcı makine gücü | Envanter (Şehir Hatları'nın bir kısmı); diğerleri EK (265 kW × 2; İDO deniz otobüsleri 280 kW × 4) |
| Hız | Envanter (Şehir Hatları, İDO); EK 1, 3, 6 |
| Varsayılan | Beyden için makine gücü (2 × 750 kW) ve Dentur, Boğaziçi, Beyden için hız (14 kn) |

### 4.2 Düzeltilmiş sonuçlar (yalnızca seyir fazı)

Firmalardan manevra ve liman süresi verisi alınamadığı için yalnızca seyir fazı
hesaplanmıştır; sonuçlar bu nedenle **alt sınırdır**.

| t/yıl | CO₂ | NOx | SOx | PM | Yakıt |
|---|---:|---:|---:|---:|---:|
| Entec, düzeltilmiş | **178.310** | 3.049 | 2.988 | 206 | 55.953 |
| Trozzi, düzeltilmiş | 391.011 | 7.260 | 1.688 | 197 | 122.191 |
| Entec, tez | 321.269 | 5.582 | 4.711 | 348 | – |
| Trozzi, tez | 315.310 | 4.101 | 3.566 | 330 | – |

Firma bazında: Şehir Hatları 61.851 t, Turyol 40.415 t, Mavi Marmara 33.168 t,
İDO 30.373 t, Beyden 4.267 t, Boğaziçi 4.141 t, Dentur 4.094 t CO₂ (Entec).
Ayrıntılar `results/local_2015_firms_corrected.csv` ve
`results/local_2015_ships_corrected.csv` dosyalarında.

**Yorum:**

* Yerel trafik için **Entec sonucu önerilir**. Gemi bazında gerçek makine gücü
  kullanıyor. Trozzi'nin tonaja dayalı yakıt regresyonu büyük gemilerden
  türetildiği için küçük feribotlarda tüketimi ~2,2 kat yüksek veriyor.
* Düzeltilmiş Entec değeri (178 bin t CO₂, alt sınır) tezin Tablo 28'indeki
  önceki çalışmalarla aynı büyüklükte: 1998 için 170.491 t, 2008 için 253.705 t.
* Tezdeki yerel toplamların düzeltilmiş değere yakın çıkması tesadüftür. Excel'in
  hatalı formülleri ve genel girdileri birbirinin etkisini kısmen dengelemiş.
* **Bazı mesafeler şüpheli:** Dentur gemi başına yılda 1.476 mil (~105 saat
  seyir), Boğaziçi 3.060 mil (~219 saat), İDO 4.320 mil (~244 saat; Osman Gazi
  gibi günlük Bursa seferi yapan feribotlar için çok düşük). Bu üç firmanın
  sonuçları büyük olasılıkla eksik tahmin. Diğer firmalar gemi başına
  1.000–2.000 saat/yıl ile makul.
* SOx, Entec'in 2015 faktörleriyle (yaklaşık %2,7 kükürt varsayımı) hesaplandı.
  Feribotların daha düşük kükürtlü yakıt kullandığı biliniyorsa SOx ve PM daha
  düşük çıkar.

## 5. Öneriler

1. Tezdeki sayısal sonuçları ve aynı çalışma kitaplarını kullanan yayınları bu
   bulgular ışığında yeniden kontrol et. Gerekirse ilgili dergilere düzeltme
   (corrigendum) başvurusu yapmayı değerlendir.
2. Kodu GitHub'da paylaşırken README'deki "Known issues in the original
   workbooks" bölümünü koru. Şeffaflık, iş ve postdoc başvurularında güçlü bir
   artı olur.
3. Transit (134–158 bin t CO₂) ve yerel trafik (Entec, ≥178 bin t CO₂) için
   düzeltilmiş sonuçlar literatürle uyumlu. Bunun yeni bir kısa makale veya
   düzeltme notu için sağlam bir temel olduğunu düşünüyorum.
4. Dentur, Boğaziçi ve İDO mesafelerini mümkünse yeniden kontrol et; manevra ve
   liman süreleri için tipik sefer başı değerler (ör. 10 dk manevra, 15 dk iskele)
   ile bir duyarlılık analizi eklenebilir.
