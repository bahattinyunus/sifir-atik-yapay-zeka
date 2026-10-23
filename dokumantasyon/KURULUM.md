# Sıfır Atık YZ - Uçtan Uca Kurulum ve Dağıtım Rehveri

Bu kılavuz, sistemi sıfırdan bir **Raspberry Pi 4 / 5**, **NVIDIA Jetson Nano** veya standart bir Linux/Windows sunucu üzerine kurmak için gerekli tüm adımları içerir.

---

## 📋 1. Sistem Gereksinimleri

* **İşletim Sistemi:** Raspberry Pi OS (64-bit Debian Bookworm/Bullseye) veya Ubuntu 22.04 LTS / Windows 10/11
* **Python:** Python 3.9, 3.10, 3.11 veya 3.12
* **Kamera:** USB WebCam (UVC uyumlu) veya Raspberry Pi Camera V2/V3 (CSI)
* **Ağ:** Lokal Wi-Fi veya Ethernet (Edge cihazı ile Dashboard arasındaki WebSocket iletişimi için)

---

## 🚀 2. Hızlı Kurulum Adımları

### Adım 1: Depoyu Klonlama ve Sanal Ortam (venv)
```bash
git clone https://github.com/bahattinyunus/sifir-atik-yapay-zeka.git
cd sifir-atik-yapay-zeka

# Sanal ortam oluşturma ve etkinleştirme
python3 -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate
```

### Adım 2: Bağımlılıkların Yüklenmesi
```bash
pip install --upgrade pip
pip install -r arayuz/backend/requirements.txt
```

*(Opsiyonel)* Eğer PyTorch modelini lokalde eğitmek veya test etmek isterseniz:
```bash
pip install torch numpy
```

---

## 🖥️ 3. Servisleri Çalıştırma

### A. Web Arayüzü ve Backend API'yi Başlatma
```bash
cd arayuz/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
* Tarayıcınızdan `http://localhost:8000/docs` adresine giderek Swagger API dokümantasyonunu görebilirsiniz.
* `arayuz/index.html` dosyasını tarayıcınızda açarak canlı kontrol panelini izleyebilirsiniz.

### B. Uçta Çıkarım (Edge Inference) Motorunu Başlatma
Ayrı bir terminalde:
```bash
cd gomulu-yazilim
python edge_inference.py
```

---

## ⚙️ 4. Otonom Başlatma (Linux systemd Servisleri)

Fabrika veya atölye ortamında cihaz prize takıldığında monitör veya klavyeye ihtiyaç duymadan otomatik başlaması için `systemd` servisleri:

### 1. Backend API Servisi: `/etc/systemd/system/sifir-atik-backend.service`
```ini
[Unit]
Description=Sifir Atik YZ FastAPI Backend Servisi
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/sifir-atik-yapay-zeka/arayuz/backend
ExecStart=/home/pi/sifir-atik-yapay-zeka/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 2. Edge Inference Servisi: `/etc/systemd/system/sifir-atik-edge.service`
```ini
[Unit]
Description=Sifir Atik YZ Edge AI ve Valf Kontrol Servisi
After=sifir-atik-backend.service

[Service]
User=pi
WorkingDirectory=/home/pi/sifir-atik-yapay-zeka/gomulu-yazilim
ExecStart=/home/pi/sifir-atik-yapay-zeka/venv/bin/python edge_inference.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Servisleri aktif etmek için:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sifir-atik-backend sifir-atik-edge
sudo systemctl start sifir-atik-backend sifir-atik-edge
```
