# Endüstriyel Otomasyon: Raspberry Pi, Arduino ve PLC Entegrasyonu

Geri dönüşüm tesislerinde Raspberry Pi yüksek seviyeli görüntü işleme ve yapay zeka çıkarımı yaparken; milisaniyelik valf darbeleri ve motor hız kontrolü için mikrodenetleyiciler (Arduino Nano, STM32 BluePill, ESP32) veya endüstriyel PLC'ler (Siemens S7-1200 / Delta) ile köprü kurulabilir.

---

## 🔌 1. Donanımsal Haberleşme Mimarisi

```text
  [ USB Kamera / CSI ]
          │
  [ Raspberry Pi 4/5 ] (Edge-AI: PolymerEdgeNet / MultiObjectDetector)
          │
  [ USB-Seri / UART / RS485 ] (115200 Baud / Modbus RTU)
          │
  [ Arduino Nano / STM32 / PLC ] (Gerçek Zamanlı Donanım Sürücüsü)
          ├── MOSFET Sürücü Kartı (IRLZ44N / Optokuplör) ──> 12V Solenoid Valfler
          └── Frekans İnvertörü (VFD) ────────────────────────> Konveyör AC Motoru
```

---

## 📡 2. Seri İletişim Protokolü (SerialBridge ASCII Standardı)

Raspberry Pi ile mikrodenetleyici arasındaki mesajlaşma `gomulu-yazilim/serial_bridge.py` kütüphanesi tarafından yönetilir:

| Komut Formatı | Açıklama | Örnek Komut | Beklenen Cevap |
| :--- | :--- | :--- | :--- |
| `FIRE:<VALVE_NO>:<PULSE_MS>\n` | Belirtilen valfi milisaniye süreyle aç | `FIRE:1:120\n` | `ACK:FIRE:1\n` |
| `STOP\n` | Tüm valfleri ve bandı acil durdur | `STOP\n` | `ACK:STOPPED\n` |
| `SPEED:<M_S>\n` | Bant hızını ayarla (PWM / VFD) | `SPEED:0.40\n` | `ACK:SPEED\n` |
| `PING\n` | Bağlantı sağlık kontrolü | `PING\n` | `PONG\n` |

---

## ⚡ 3. Endüstriyel PLC 24V Seviye Dönüşümü

Endüstriyel PLC girişleri genellikle **24V PNP/NPN** lojik ile çalışır:
* Raspberry Pi'nin 3.3V GPIO çıkışlarını doğrudan PLC'ye bağlamayınız.
* 3.3V -> 24V seviye dönüştürücü optokuplör modülleri (PC817 veya DST-1R4P-N) kullanılmalıdır.
* Alternatif olarak USB-RS485 dönüştürücü takılarak standart **Modbus RTU** protokolü üzerinden PLC registerlarına yazılabilir.
