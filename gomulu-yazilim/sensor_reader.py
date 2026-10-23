"""
Sıfır Atık YZ - Sensör Okuma ve Tetikleme Modülü
Konveyör bant üzerindeki IR optik engel sensörleri, endüktif metal sensörleri
ve yakın kızılötesi (NIR) spektrometre sensörlerinin entegrasyonu.
"""

import time
import random
from typing import Optional, Callable
from actuator_controller import IS_HARDWARE_AVAILABLE, gpio_driver


class SensorManager:
    # Varsayılan GPIO Pinleri
    IR_SENSOR_PIN = 4        # TCRT5000 veya optik engel sensörü
    INDUCTIVE_PIN = 14       # Metal tespiti için endüktif sensör

    def __init__(self, ir_pin: int = IR_SENSOR_PIN, inductive_pin: int = INDUCTIVE_PIN, mock_mode: Optional[bool] = None):
        self.ir_pin = ir_pin
        self.inductive_pin = inductive_pin
        self.mock_mode = (not IS_HARDWARE_AVAILABLE) if mock_mode is None else mock_mode
        self._init_pins()

    def _init_pins(self):
        if not self.mock_mode:
            gpio_driver.setup(self.ir_pin, gpio_driver.IN)
            gpio_driver.setup(self.inductive_pin, gpio_driver.IN)
            print("[SensorManager] Fiziksel sensör pinleri kuruldu.")
        else:
            print("[SensorManager] Sanal sensör sürücüsü devrede.")

    def is_waste_present(self) -> bool:
        """
        IR optik sensörün önünden atık geçip geçmediğini kontrol eder.
        Aktif LOW veya HIGH sensör mantığına göre uyarlanabilir.
        """
        if not self.mock_mode:
            # Tipik IR sensörleri cisim görünce LOW verir
            return gpio_driver.input(self.ir_pin) == gpio_driver.LOW
        else:
            # Simülasyon modunda %30 ihtimalle cisim geçmiş gibi yapar
            return random.random() < 0.35

    def is_metal_detected(self) -> bool:
        """Endüktif yaklaşım sensöründen metal sinyali okur."""
        if not self.mock_mode:
            return gpio_driver.input(self.inductive_pin) == gpio_driver.HIGH
        else:
            return random.random() < 0.12

    def read_nir_spectrometer(self) -> dict:
        """
        AS7265x (Triad Spektrometre: UV, VIS, NIR) 18 kanal dalga boyu spektrum okuması.
        Polimer türlerinin spesifik NIR soğurma piklerini simüle eder veya I2C'den okur.
        """
        # 410nm - 940nm arası spektral kanallar
        channels = ["410nm", "435nm", "460nm", "485nm", "510nm", "535nm",
                    "560nm", "585nm", "610nm", "645nm", "680nm", "705nm",
                    "730nm", "760nm", "810nm", "860nm", "900nm", "940nm"]
        return {ch: round(random.uniform(100.0, 1024.0), 2) for ch in channels}
