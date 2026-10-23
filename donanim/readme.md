# Donanım ve Mekanik Tasarımlar

Bu dizin, sıfır atık yapay zeka sisteminin fiziksel, mekanik ve elektronik mimarisini barındırır.

---

## 📁 Dizin İçeriği

```text
donanim/
├── mekanik/
│   ├── servo_flap_braketi.scad      # 2020 Sigma Profil ve MG996R servo yönlendirici flap montaj braketi
│   └── kamera_montaj_aparati.scad   # Konveyör bant üzeri ayarlanabilir WebCam/PiCamera montaj ayağı
└── elektronik/
    ├── baglanti_semasi.md           # Pinout, röle kartı, 12V solenoid ve koruma diyotu rehberi
    └── devre_semasi.svg             # Vektörel elektriksel bağlantı blok şeması
```

---

## 🛠️ 1. Mekanik Tasarımlar (3D Baskı)

* **servo_flap_braketi.scad**: MG996R metal dişli servo motoru 2020 alüminyum profile sabitlemek için parametrik modeldir. OpenSCAD üzerinden doğrudan `.stl` formatında ihraç edilebilir.
  * **Önerilen Baskı Ayarları:** %40 Infill (Dolgu), 4 Kat Duvar (Perimeter), PETG veya PLA+ Filament.
* **kamera_montaj_aparati.scad**: PiCamera V2 / V3 veya standart USB web kameraları konveyör bandın tam dik tepe açısına (top-down view) sabitlemek için kullanılır.

---

## ⚡ 2. Elektronik ve Devre Mimarisi

* Detaylı bağlantı tablosu ve güvenlik önlemleri için [baglanti_semasi.md](elektronik/baglanti_semasi.md) dosyasını inceleyin.
* Blok şemasını yüksek çözünürlükte görüntülemek için [devre_semasi.svg](elektronik/devre_semasi.svg) dosyasını tarayıcınızda açabilirsiniz.
