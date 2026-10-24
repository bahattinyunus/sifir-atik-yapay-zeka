# Çevresel Etki (ESG) ve Karbon Tasarrufu Hesaplama Metodolojisi

Bu doküman, Sıfır Atık Yapay Zeka sisteminin dashboard'unda gerçek zamanlı olarak sunulan **Önlenen Karbon Emisyonu ($CO_2$)**, **Enerji Tasarrufu** ve **Kurtarılan Ağaç Dengi** metriklerinin bilimsel arka planını açıklar.

---

## 🔬 1. Referans Alınan Modeller ve Standartlar

Hesaplamalarımızda aşağıdaki uluslararası otoritelerin Yaşam Döngüsü Analizi (LCA - Life Cycle Assessment) verileri baz alınmıştır:
1. **US EPA WARM (Waste Reduction Model):** Plastik ve metal atıkların geri dönüşümüyle önlenen sera gazı emisyon faktörleri.
2. **PlasticsEurope Eco-profiles:** Virgin (orijinal fosil yakıt kaynaklı) polimer üretimi ile geri dönüştürülmüş polimer (rPET, rHDPE) üretiminin beşik-kapı (cradle-to-gate) karbon ayak izi karşılaştırması.
3. **Avrupa Alüminyum Birliği (European Aluminium):** İkincil (geri dönüştürülmüş) alüminyum üretiminde birincil üretime göre sağlanan %95 enerji tasarrufu.

---

## 📊 2. Polimer Bazında Katsayı Matrisi

| Malzeme / Polimer | Birim Parça Ağırlığı (Ort.) | Önlenen $CO_2$ Emisyonu ($kg CO_2e / kg$) | Enerji Tasarrufu ($kWh / kg$) | Su Tasarrufu ($Litre / kg$) |
| :--- | :---: | :---: | :---: | :---: |
| **PET (Polietilen Tereftalat)** | 30 g (0.030 kg) | **1.50** | **6.00** | 25.0 |
| **HDPE (Yüksek Yoğunluklu PE)**| 45 g (0.045 kg) | **1.80** | **7.50** | 25.0 |
| **Naylon (Poliamid PA6/66)**  | 25 g (0.025 kg) | **2.30** | **10.00** | 30.0 |
| **PUR (Poliüretan Köpük)**    | 15 g (0.015 kg) | **1.20** | **4.00** | 20.0 |
| **Alüminyum / Metal Kutu**     | 15 g (0.015 kg) | **9.00** | **14.00** | 40.0 |

---

## 🧮 3. Temel Hesaplama Formülleri

### A. Toplam Kurtarılan Kütle ($M_{\text{toplam}}$)
$$M_{\text{toplam}} = \sum_{i \in \text{Polimerler}} N_i \times W_i$$
* $N_i$: Ayrıştırılan $i$ polimerinin toplam parça adedi.
* $W_i$: İlgili polimerin ortalama parça kütlesi ($kg$).

### B. Önlenen Karbon Salınımı ($E_{\text{CO}_2}$)
$$E_{\text{CO}_2} = \sum_{i \in \text{Polimerler}} (N_i \times W_i) \times C_i$$
* $C_i$: $i$ polimerinin $kg$ başına engellediği sera gazı emisyon katsayısı ($kg CO_2e / kg$).

### C. Eşdeğer Yetişkin Ağaç Sayısı
Bir yetişkin çam/meşe ağacı yılda ortalama **21.77 kg $CO_2$** soğurur (US Forestry Service verisi):
$$\text{Ağaç Dengi} = \frac{E_{\text{CO}_2}}{21.77}$$
