"""
Sıfır Atık YZ - Çoklu Nesne Senkronizasyon ve Çoklu Valf Kuyruğu (Multi-Valve Scheduler)
Bant üzerinde aynı anda akan birden fazla farklı atığı eş zamanlı takip eder.
Her atığın kendi türüne ait valfe olan fiziksel mesafesini ve varış süresini hesaplar,
zamanı geldiğinde hassas darbe ile ilgili valfi patlatır.
"""

import time
import heapq
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, List
from actuator_controller import ActuatorController


@dataclass(order=True)
class ScheduledValveEvent:
    trigger_time: float
    waste_id: int = field(compare=False)
    waste_type: str = field(compare=False)
    valve_number: int = field(compare=False)
    pulse_ms: int = field(compare=False)


class MultiValveScheduler:
    """
    Konveyör bant üzerinde peş peşe veya yan yana gelen çoklu atıkları
    birbirine karıştırmadan ilgili valflere zamanlayan asenkron kuyruk yöneticisi.
    """
    # Kamera ile her bir valf arasındaki fiziksel mesafeler (metre cinsinden)
    VALVE_DISTANCES_M = {
        "PET": 0.40,     # Valf 1
        "HDPE": 0.65,    # Valf 2
        "Naylon": 0.90,  # Valf 3
        "PUR": 1.15,     # Valf 4
        "Metal": 1.40    # Valf 5
    }

    def __init__(
        self,
        actuator: ActuatorController,
        conveyor_speed_m_s: float = 0.35,
        default_pulse_ms: int = 120,
        custom_distances: Optional[Dict[str, float]] = None
    ):
        self.actuator = actuator
        self.speed = max(conveyor_speed_m_s, 0.05)
        self.pulse_ms = default_pulse_ms
        self.distances = custom_distances or self.VALVE_DISTANCES_M

        self.event_queue: List[ScheduledValveEvent] = []
        self._lock = threading.Lock()
        self._running = True
        self.scheduled_waste_ids = set()

        # Arka plan kuyruk işleyici iş parçacığı
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def update_speed(self, new_speed: float):
        if new_speed > 0:
            with self._lock:
                self.speed = new_speed
                print(f"[MultiValveScheduler] Bant hızı güncellendi: {self.speed} m/s")

    def schedule_item(self, track_id: int, waste_type: str, detection_time: Optional[float] = None) -> bool:
        """
        Yeni bir atığı kendi valfine zamanlar.
        Aynı atık ID'si için mükerrer tetiklemeyi önler (De-bouncing).
        """
        if waste_type == "Reject" or waste_type not in self.distances:
            # Reject atıklar bant sonuna kadar gider
            return False

        with self._lock:
            if track_id in self.scheduled_waste_ids:
                return False  # Zaten zamanlandı

            self.scheduled_waste_ids.add(track_id)
            t0 = detection_time or time.time()
            dist = self.distances[waste_type]
            delay_sec = dist / self.speed
            target_time = t0 + delay_sec

            event = ScheduledValveEvent(
                trigger_time=target_time,
                waste_id=track_id,
                waste_type=waste_type,
                valve_number=list(self.distances.keys()).index(waste_type) + 1,
                pulse_ms=self.pulse_ms
            )
            heapq.heappush(self.event_queue, event)
            print(f"[MultiValveScheduler] Atık #{track_id} ({waste_type}) Valf {event.valve_number}'e zamanlandı. (Gecikme: {delay_sec:.3f} sn)")
            return True

    def _process_queue(self):
        """Kuyruktaki zamanı gelmiş valf patlatma olaylarını sırayla ateşler."""
        while self._running:
            now = time.time()
            to_fire = []

            with self._lock:
                while self.event_queue and self.event_queue[0].trigger_time <= now:
                    to_fire.append(heapq.heappop(self.event_queue))

            for ev in to_fire:
                print(f"[MultiValveScheduler] 🔥 ZAMAN DOLDU: Atık #{ev.waste_id} -> Valf {ev.valve_number} ({ev.waste_type}) ATEŞLENİYOR!")
                self.actuator.trigger_valve(ev.waste_type, pulse_duration_ms=ev.pulse_ms)

            time.sleep(0.005)  # 5 ms hassasiyetli polling

    def stop(self):
        self._running = False
        with self._lock:
            self.event_queue.clear()
            self.scheduled_waste_ids.clear()
