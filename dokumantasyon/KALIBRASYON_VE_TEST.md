# Konveyör Bant ve Valf Zamanlama Kalibrasyon Rehberi

Optik ayıklama sistemlerinde en sık karşılaşılan problem, yapay zekanın polimeri doğru tanımasına rağmen valfin atığı kaçırmasıdır. Bu durum zamanlama (timing) kalibrasyonunun eksikliğinden kaynaklanır.

---

## 📐 1. Temel Zamanlama Formülü

Atığın kamera optik merkezinden geçip ilgili pnömatik valfin nozul hizasına gelmesi için gereken gecikme süresi ($t_{gecikme}$):

$$t_{\text{gecikme}} = \frac{d}{v_{\text{bant}}} - t_{\text{inference}} - t_{\text{valf\_acilis}}$$

* $d$: Kamera optik merkezi ile valf nozulu arasındaki net fiziksel mesafe (Metre).
* $v_{\text{bant}}$: Konveyör bandın lineer hızı (Metre / Saniye).
* $t_{\text{inference}}$: Modelin görüntüyü işleme süresi (Ortalama ~0.015 sn / 15 ms).
* $t_{\text{valf\_acilis}}$: Solenoid valfin bobininin enerjilenip mekanik contayı açma süresi (~0.010 - 0.020 sn).

---

## ⏱️ 2. Adım Adım Kalibrasyon Prosedürü

### Adım 1: Konveyör Bant Hızının Ölçülmesi
1. Bant üzerine belirgin bir beyaz işaret bandı yapıştırın.
2. Bant üzerine 1.00 metrelik bir mesafe ölçüp işaretleyin.
3. Kronometre ile bandın bu 1 metreyi kaç saniyede tamamladığını ölçün ($t_{\text{olcum}}$).
4. $v_{\text{bant}} = \frac{1.0}{t_{\text{olcum}}}$ (Örnek: 2.85 saniyede geçtiyse $v = 0.35$ m/s).

### Adım 2: Valf Mesafesinin Ölçülmesi
* Kamera lensi merkezinden 1. Valf (PET) nozuluna olan mesafeyi cetvelle ölçün (Örn: 45 cm = 0.45 m).
* Teorik Gecikme: $0.45 / 0.35 \approx 1.285$ saniye (1285 ms).

### Adım 3: Valf Püskürtme Süresi (Pulse Width) Ayarı
* Çok kısa süre (örn. <50ms): Ağır şişeleri banttan fırlatmaya yetecek hava debisi oluşmaz.
* Çok uzun süre (örn. >250ms): Kompresör hava tankı hızla boşalır ve arkadan gelen diğer atıklar için basınç düşer.
* **Önerilen Başlangıç Değeri:** **100 ms - 140 ms**.

### Adım 4: Hava Basıncı Ayarı
* Pnömatik şartlandırıcı regülatörünü **4.0 - 5.5 Bar** arasına ayarlayın.
* Şişeler çok hafif olduğu için aşırı yüksek basınç (>7 Bar) atığın hazne dışına sekmesine sebep olabilir.
