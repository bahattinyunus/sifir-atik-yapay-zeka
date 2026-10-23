# Malzeme Listesi (BOM) ve Maliyet Analizi (2026 Güncel)

Bu doküman, düşük maliyetli sıfır atık yapay zeka sisteminin kurulumu için gerekli asgari ve ileri seviye bileşenleri listeler.

---

## 1. İşlemci / Uç Cihaz (Edge Device)

| Bileşen | Önerilen Model | Alternatif | Tahmini Maliyet | Not |
| :--- | :--- | :--- | :---: | :--- |
| **Geliştirme Kartı** | Raspberry Pi 4 / 5 (4GB/8GB) | NVIDIA Jetson Orin Nano / Nano 2GB | $60 - $120 | RPi 4/5 hafif MobileNet ve INT8 modeller için fazlasıyla yeterlidir. |
| **MicroSD Kart** | 64GB SanDisk Extreme A2 | 32GB Kingston Canvas | $12 | Yüksek IOPS hızlı okuma/yazma sistem kararlılığı için kritiktir. |
| **Güç Kaynağı** | 5.1V 3.5A / 27W Type-C Adaptör | - | $12 | Under-voltage (yetersiz voltaj) hatalarını önlemek için orijinal adaptör önerilir. |

---

## 2. Görüntü ve Spektroskopik Sensörler

| Bileşen | Önerilen Model | Tahmini Maliyet | Amaç / Not |
| :--- | :--- | :---: | :--- |
| **Kamera** | 1080p Geniş Açılı USB WebCam / PiCamera V2 | $20 - $35 | Minimum 30 FPS ve ayarlanabilir odaklama. |
| **Optik Engel Sensörü** | TCRT5000 / E18-D80NK Kızılötesi | $3 - $6 | Atığın kameranın altına girdiğini haber veren donanımsal tetikleyici. |
| **Endüktif Sensör** | LJ12A3-4-Z/BX NPN Yaklaşım Sensörü | $5 | Alüminyum ve metal kutuları ayrıştırmak için optik sisteme destek sensör. |
| **NIR Spektrometre (Opsiyonel)** | SparkFun AS7265x Triad Spektrometre | $65 | Naylon ve PUR gibi zorlu polimerlerin 18 dalga boyunda spektral analizi için. |

---

## 3. Mekanik ve Pnömatik Aktüatörler

| Bileşen | Önerilen Model | Tahmini Maliyet | Amaç / Not |
| :--- | :--- | :---: | :--- |
| **Pnömatik Solenoid Valf** | 12V 2/2 Normalde Kapalı Hızlı Valf (x5 Adet) | $45 - $60 | Her polimer sınıfı (PET, HDPE, Naylon, PUR, Metal) için hava üfleme nozulu. |
| **Hava Kompresörü** | Sessiz Yağsız Kompresör (24L, 6-8 Bar) | $90 - $150 | Pnömatik nozullar için basınçlı hava üretimi. |
| **Röle Modülü** | 5V 8 Kanallı Optokuplör İzolasyonlu Röle | $6 | 3.3V Raspberry Pi sinyalleri ile 12V valfleri sürmek için. |
| **Flyback Diyotları** | 1N4007 Doğrultucu Diyot (10 Adet) | $1 | Solenoid bobinlerinden geri dönen yüksek voltajı sönümlemek için şarttır. |
| **Servo Motor (Alternatif)** | MG996R Metal Dişli Servo | $8 | Valf ve kompresör yerine mekanik flap ile ayırma yapmak isteyen başlangıç seviyesi için. |
| **Pnömatik Hortum ve Rakorlar** | 6mm PU Hortum + Hızlı Bağlantı Rakor Seti | $15 | Dağıtıcı manifold bağlantıları. |

---

## 4. Toplam Maliyet Özeti

* **Faz 1 (Başlangıç - Mekanik Flap & WebCam):** ~$110 - $150
* **Faz 2 (Endüstriyel Pnömatik Valfli Sistem):** ~$240 - $320 *(Kompresör hariç)*
* **Faz 3 (Tam Teşekküllü Spektrometre ve Kompresörlü Sistem):** ~$450 - $550

*(Endüstriyel TOMRA / AMP alternatiflerinin $80,000 - $250,000 bandında olduğu düşünüldüğünde, bu açık kaynak mimari KOBİ'ler ve geri dönüşüm girişimleri için %99'un üzerinde maliyet avantajı sağlamaktadır.)*
