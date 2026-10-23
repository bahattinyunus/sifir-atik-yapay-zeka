import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gomulu-yazilim"))
from actuator_controller import ActuatorController
from conveyor_tracker import ConveyorTracker
from sensor_reader import SensorManager

def test_actuator_mock_mode():
    controller = ActuatorController(mock_mode=True)
    assert controller.mock_mode is True
    assert controller.e_stop_active is False

    # Valf tetikleme testi
    result = controller.trigger_valve("PET", pulse_duration_ms=50)
    assert result is True

    # Tanımsız valf (Reject)
    reject_res = controller.trigger_valve("Reject")
    assert reject_res is False

    # E-Stop testi
    controller.set_emergency_stop(True)
    assert controller.e_stop_active is True
    assert controller.trigger_valve("HDPE") is False

    controller.set_emergency_stop(False)
    assert controller.e_stop_active is False
    controller.cleanup()

def test_conveyor_tracker():
    controller = ActuatorController(mock_mode=True)
    tracker = ConveyorTracker(actuator=controller, conveyor_speed_m_s=0.4, camera_to_valve_distance_m=0.8)
    
    delay = tracker.calculate_delay_seconds()
    # 0.8 / 0.4 = 2.0 saniye
    assert round(delay, 2) == 2.0

    tracker.update_parameters(speed_m_s=0.5)
    delay2 = tracker.calculate_delay_seconds()
    assert round(delay2, 2) == 1.6

    tracker.cancel_all()

def test_sensor_manager_mock():
    sensors = SensorManager(mock_mode=True)
    assert sensors.mock_mode is True
    _ = sensors.is_waste_present()
    _ = sensors.is_metal_detected()
    spec = sensors.read_nir_spectrometer()
    assert len(spec) == 18
