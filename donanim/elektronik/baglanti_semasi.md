# Sıfır Atık YZ - Elektronik Bağlantı ve Pinout Şeması

Bu döküman; Raspberry Pi / Jetson Nano, optik sensörler, endüktif sensör, röle kartı, pnömatik solenoid valfler ve servo motorların elektriksel bağlantılarını detaylandırır.

---

## ⚡ 1. Raspberry Pi 4 / 5 GPIO Pin Dağılımı (BCM)

| Pin No (Fiziksel) | BCM Adı | Bağlanan Donanım Bileşeni | Sinyal Tipi | Voltaj |
| :---: | :---: | :--- | :---: | :---: |
| **Pin 2** | 5V Power | 5V Röle Kartı VCC / IR Sensör VCC | Güç | +5V |
| **Pin 6** | GND | Ortak Şase (Ground) | Şase | 0V |
| **Pin 7** | GPIO 4 | TCRT5000 IR Engel / Bant Tetik Sensörü | Giriş (INPUT) | 3.3V / 5V Toleranslı |
| **Pin 8** | GPIO 14 | LJ12A3 Endüktif Metal Sensörü (Optokuplörlü) | Giriş (INPUT) | 3.3V |
| **Pin 11** | GPIO 17 | Valf 1 (PET Solenoid Röle Girişi IN1) | Çıkış (OUTPUT) | 3.3V Sinyal |
| **Pin 12** | GPIO 18 | Alternatif MG996R Servo PWM Sinyali | PWM Çıkış | 3.3V / 5V |
| **Pin 13** | GPIO 27 | Valf 2 (HDPE Solenoid Röle Girişi IN2) | Çıkış (OUTPUT) | 3.3V Sinyal |
| **Pin 15** | GPIO 22 | Valf 3 (Naylon Solenoid Röle Girişi IN3) | Çıkış (OUTPUT) | 3.3V Sinyal |
| **Pin 16** | GPIO 23 | Valf 4 (PUR Solenoid Röle Girişi IN4) | Çıkış (OUTPUT) | 3.3V Sinyal |
| **Pin 18** | GPIO 24 | Valf 5 (Metal Solenoid Röle Girişi IN5) | Çıkış (OUTPUT) | 3.3V Sinyal |
| **Pin 22** | GPIO 25 | Konveyör Bant Motoru E-Stop Rölesi | Çıkış (OUTPUT) | 3.3V Sinyal |

---

## 🔌 2. Güç Mimarisi ve Kritik Koruma Önlemleri

> [!CAUTION]
> **İndüktif Ters Gerilim (Back-EMF) Koruması:**
> 12V Solenoid hava valfleri ani kapanma anlarında yüksek ters voltaj (Back-EMF) üretir. Mikrodenetleyicinizin veya röle kartınızın hasar görmesini engellemek için **her solenoid bobinine paralel olarak ters yönde (Katot +12V'a, Anot GND'ye) 1N4007 flyback diyot** lehimlenmelidir.

1. **İki Ayrı Güç Hattı Kullanımı:**
   - **Hat 1 (Lojik):** Raspberry Pi için 5V 3A Type-C regüleli adaptör.
   - **Hat 2 (Güç & Valfler):** Solenoid valfler, hava kompresörü ve servo motorlar için harici **12V 5A DC SMPS Güç Kaynağı**.
2. **Ortak GND (Common Ground):**
   - Harici 12V güç kaynağının GND pini ile Raspberry Pi'ın GND pini birleştirilmelidir (Referans sinyal voltajı için).
3. **Optik İzolasyon (Optocoupler):**
   - Kullanılan röle modülünün optokuplörlü (JD-VCC jumper'lı) olması tercih edilmelidir. JD-VCC harici güçten, VCC Pi'dan beslenerek %100 galvanik izolasyon sağlanır.

---

## 🛠️ 3. Mekanik Valf ve Kompresör Pnömatik Hattı

```text
[ Hava Kompresörü (6-8 Bar) ]
          │
  [ Şartlandırıcı (Filtre + Basınç Regülatörü: 4 Bar) ]
          │
  [ 5'li Pnömatik Dağıtıcı Manifold ]
    ├── 12V Solenoid Valf 1 (PET Nozulu)
    ├── 12V Solenoid Valf 2 (HDPE Nozulu)
    ├── 12V Solenoid Valf 3 (Naylon Nozulu)
    ├── 12V Solenoid Valf 4 (PUR Nozulu)
    └── 12V Solenoid Valf 5 (Metal Nozulu)
```
