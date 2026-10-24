"""
Sıfır Atık YZ - Mikrodenetleyici (Arduino / STM32 / ESP32 / PLC) Seri Haberleşme Köprüsü
Raspberry Pi üzerindeki Edge-AI kararlarını USB-Seri veya UART üzerinden
harici mikrodenetleyici kartına ASCII/G-Code benzeri komutlarla iletir.
Protokol:
  "FIRE:<VALVE_NUM>:<PULSE_MS>\n" -> Örn: "FIRE:1:120\n"
  "STOP\n"                         -> Acil Durdurma
  "SPEED:<M_S>\n"                  -> Konveyör hız bilgisi
"""

import time
import threading
from typing import Optional

class SerialBridge:
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200, mock_mode: Optional[bool] = None):
        self.port = port
        self.baudrate = baudrate
        self.mock_mode = mock_mode
        self.serial_conn = None
        self._lock = threading.Lock()
        self._connect()

    def _connect(self):
        try:
            import serial
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1.0)
            self.mock_mode = False
            print(f"[SerialBridge] Seri port açıldı: {self.port} ({self.baudrate} baud)")
        except Exception:
            self.mock_mode = True
            print("[SerialBridge] Fiziksel seri port bulunamadı, Sanal Seri Köprü devrede.")

    def send_valve_command(self, valve_num: int, pulse_ms: int = 120) -> bool:
        """Mikrodenetleyiciye valf ateşleme komutu yollar."""
        cmd = f"FIRE:{valve_num}:{pulse_ms}\n"
        return self._send_raw(cmd)

    def send_emergency_stop(self) -> bool:
        """Tüm donanımı derhal durdurma komutu."""
        return self._send_raw("STOP\n")

    def _send_raw(self, cmd: str) -> bool:
        with self._lock:
            if not self.mock_mode and self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.write(cmd.encode('utf-8'))
                    return True
                except Exception as e:
                    print(f"[SerialBridge] Seri yazma hatası: {e}")
                    return False
            else:
                # Mock simülasyon
                # print(f"[SerialBridge:MOCK] Komut iletildi: {cmd.strip()}")
                return True

    def close(self):
        if self.serial_conn and not self.mock_mode:
            try:
                self.serial_conn.close()
            except Exception:
                pass
        print("[SerialBridge] Seri bağlantı kapatıldı.")
