"""
Sıfır Atık YZ - Donanım Soyutlama Katmanı (HAL) ve Aktüatör Kontrolcüsü
Solenoid pnömatik valfleri, röleleri ve servo motorları güvenli ve thread-safe olarak yönetir.
Gerçek Raspberry Pi/Jetson ortamında fiziksel GPIO kullanır, PC/Windows ortamında simülasyon moduna geçer.
"""

import time
import threading
from typing import Dict, Optional

# GPIO Kütüphanesini Dinamik Olarak İçe Aktar (Mock Fallback Desteği)
try:
    import RPi.GPIO as GPIO
    IS_HARDWARE_AVAILABLE = True
except (ImportError, RuntimeError):
    IS_HARDWARE_AVAILABLE = False


class VirtualGPIO:
    """Raspberry Pi veya Jetson harici ortamlarda geliştirme ve test için sanal GPIO."""
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    HIGH = 1
    LOW = 0

    @classmethod
    def setmode(cls, mode):
        pass

    @classmethod
    def setwarnings(cls, flag):
        pass

    @classmethod
    def setup(cls, pin, mode):
        pass

    @classmethod
    def output(cls, pin, state):
        pass

    @classmethod
    def cleanup(cls):
        pass


gpio_driver = GPIO if IS_HARDWARE_AVAILABLE else VirtualGPIO


class ActuatorController:
    """
    Pnömatik Solenoid Valfler ve Servo Motorlar için Birleşik Aktüatör Yöneticisi.
    """

    # Varsayılan BCM Pin Eşleşmeleri
    DEFAULT_PINS = {
        "VALVE_PET": 17,     # 1. Pnömatik Solenoid Valf (PET)
        "VALVE_HDPE": 27,    # 2. Pnömatik Solenoid Valf (HDPE)
        "VALVE_NYLON": 22,   # 3. Pnömatik Solenoid Valf (Naylon)
        "VALVE_PUR": 23,     # 4. Pnömatik Solenoid Valf (PUR)
        "VALVE_METAL": 24,   # 5. Pnömatik Solenoid Valf (Metal)
        "SERVO_FLAP": 18,    # Alternatif Mekanik Yönlendirici Flap
        "CONVEYOR_RELAY": 25 # Konveyör Bant Motor Rölesi
    }

    def __init__(self, pin_config: Optional[Dict[str, int]] = None, mock_mode: Optional[bool] = None):
        self.pins = pin_config or self.DEFAULT_PINS
        self.mock_mode = (not IS_HARDWARE_AVAILABLE) if mock_mode is None else mock_mode
        self.e_stop_active = False
        self._lock = threading.Lock()
        self._init_hardware()

    def _init_hardware(self):
        print(f"[ActuatorController] Donanım Başlatılıyor (Mock Modu: {self.mock_mode})...")
        if not self.mock_mode:
            gpio_driver.setmode(gpio_driver.BCM)
            gpio_driver.setwarnings(False)
            for name, pin in self.pins.items():
                gpio_driver.setup(pin, gpio_driver.OUT)
                gpio_driver.output(pin, gpio_driver.LOW)
            print("[ActuatorController] Fiziksel GPIO Pinleri başarıyla kuruldu.")
        else:
            print("[ActuatorController] Sanal GPIO sürücüsü aktif.")

    def trigger_valve(self, waste_type: str, pulse_duration_ms: int = 120):
        """
        Belirtilen atık türü için ilgili pnömatik valfi milisaniye bazında açıp kapatır.
        """
        if self.e_stop_active:
            print(f"[ActuatorController] [UYARI] E-STOP aktif! {waste_type} valfi açılamaz.")
            return False

        pin_key = f"VALVE_{waste_type.upper()}"
        if pin_key not in self.pins:
            print(f"[ActuatorController] '{waste_type}' için tanımlı valf pini bulunamadı (Reject/Bant Sonu).")
            return False

        pin = self.pins[pin_key]

        def _fire():
            with self._lock:
                if self.e_stop_active:
                    return
                print(f"[VALF ATEŞLENDİ] >>> {waste_type} (Pin: {pin}, Süre: {pulse_duration_ms} ms)")
                if not self.mock_mode:
                    gpio_driver.output(pin, gpio_driver.HIGH)
                time.sleep(pulse_duration_ms / 1000.0)
                if not self.mock_mode:
                    gpio_driver.output(pin, gpio_driver.LOW)
                print(f"[VALF KAPANDI] <<< {waste_type} (Pin: {pin})")

        # Valf darbesini arka plan thread'inde çalıştır (ana döngüyü bloklamaz)
        t = threading.Thread(target=_fire, daemon=True)
        t.start()
        return True

    def set_emergency_stop(self, active: bool = True):
        """Acil durdurma durumunu günceller ve tüm çıkışları kapatır."""
        self.e_stop_active = active
        if active:
            print("[ActuatorController] 🛑 ACİL DURDURMA DEVREYE GİRDİ! Tüm valfler kapatılıyor.")
            self.all_valves_off()
        else:
            print("[ActuatorController] ✅ Acil durdurma sıfırlandı.")

    def all_valves_off(self):
        """Tüm valfleri ve aktüatörleri derhal LOW konumuna çeker."""
        with self._lock:
            if not self.mock_mode:
                for pin in self.pins.values():
                    gpio_driver.output(pin, gpio_driver.LOW)
            print("[ActuatorController] Tüm valfler ve röleler güvenli konuma (OFF) çekildi.")

    def cleanup(self):
        """Uygulama sonlanırken pinleri temizler."""
        self.all_valves_off()
        if not self.mock_mode:
            gpio_driver.cleanup()
        print("[ActuatorController] GPIO kaynakları temizlendi.")
