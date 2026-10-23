"""
Sıfır Atık YZ - Konveyör Bant Takipçisi ve Zamanlama Yöneticisi
Kameradan geçen atık ile pnömatik valf arasındaki mesafeyi ve konveyör hızını
kullanarak valfin tam atık hizasına geldiği anda tetiklenmesini sağlar.
Formül: t_delay = Mesafe (metre) / Bant Hızı (m/s)
"""

import time
import threading
from typing import Callable, Optional
from actuator_controller import ActuatorController


class ConveyorTracker:
    def __init__(
        self,
        actuator: ActuatorController,
        conveyor_speed_m_s: float = 0.35,
        camera_to_valve_distance_m: float = 0.45,
        default_pulse_ms: int = 120
    ):
        self.actuator = actuator
        self.speed = max(conveyor_speed_m_s, 0.05)
        self.distance = camera_to_valve_distance_m
        self.pulse_ms = default_pulse_ms
        self._scheduled_timers = []
        self._lock = threading.Lock()

    def update_parameters(self, speed_m_s: Optional[float] = None, distance_m: Optional[float] = None, pulse_ms: Optional[int] = None):
        """Çalışma anında bant hızı ve valf parametrelerini günceller."""
        if speed_m_s is not None and speed_m_s > 0:
            self.speed = speed_m_s
        if distance_m is not None and distance_m > 0:
            self.distance = distance_m
        if pulse_ms is not None and pulse_ms > 0:
            self.pulse_ms = pulse_ms
        print(f"[ConveyorTracker] Parametreler Güncellendi: Hız={self.speed} m/s, Mesafe={self.distance} m, Darbe={self.pulse_ms} ms")

    def calculate_delay_seconds(self, custom_distance_m: Optional[float] = None) -> float:
        """Kamera algılama anı ile valf aktivasyonu arasındaki gecikmeyi hesaplar."""
        d = custom_distance_m if custom_distance_m is not None else self.distance
        return round(d / self.speed, 3)

    def schedule_actuation(self, waste_type: str, callback: Optional[Callable] = None):
        """
        Atık tespit edildiğinde valf tetiklemesini geleceğe zamanlar.
        """
        if waste_type == "Reject":
            print(f"[ConveyorTracker] {waste_type} atığı için valf tetiklenmeyecek (Reject haznesine akacak).")
            return

        delay = self.calculate_delay_seconds()
        print(f"[ConveyorTracker] {waste_type} algılandı. {delay:.3f} saniye sonra valf tetiklenecek.")

        def _execute():
            self.actuator.trigger_valve(waste_type, pulse_duration_ms=self.pulse_ms)
            if callback:
                try:
                    callback(waste_type)
                except Exception as e:
                    print(f"[ConveyorTracker] Geri çağırma hatası: {e}")

        timer = threading.Timer(delay, _execute)
        with self._lock:
            self._scheduled_timers.append(timer)
        timer.start()

    def cancel_all(self):
        """Tüm bekleyen zamanlanmış valf tetiklemelerini iptal eder."""
        with self._lock:
            for t in self._scheduled_timers:
                t.cancel()
            self._scheduled_timers.clear()
        print("[ConveyorTracker] Bekleyen tüm valf görevleri iptal edildi.")
