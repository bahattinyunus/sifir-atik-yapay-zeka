import sys
import os
import time
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gomulu-yazilim"))
from actuator_controller import ActuatorController
from multi_object_tracker import MultiValveScheduler

def test_multi_valve_scheduler_queue():
    controller = ActuatorController(mock_mode=True)
    scheduler = MultiValveScheduler(actuator=controller, conveyor_speed_m_s=0.5, default_pulse_ms=100)

    # PET atığı zamanla (0.40m / 0.5m/s = 0.8s)
    res_pet = scheduler.schedule_item(track_id=101, waste_type="PET")
    assert res_pet is True
    assert 101 in scheduler.scheduled_waste_ids

    # Aynı ID ile ikinci kez çağrıldığında mükerrer kayıt engellenmeli
    res_duplicate = scheduler.schedule_item(track_id=101, waste_type="PET")
    assert res_duplicate is False

    # HDPE atığı zamanla
    res_hdpe = scheduler.schedule_item(track_id=102, waste_type="HDPE")
    assert res_hdpe is True

    # Reject atığı valfe zamanlanmamalı
    res_reject = scheduler.schedule_item(track_id=103, waste_type="Reject")
    assert res_reject is False

    # Hız güncelleme
    scheduler.update_speed(0.6)
    assert scheduler.speed == 0.6

    scheduler.stop()
