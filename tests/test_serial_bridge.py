import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gomulu-yazilim"))
from serial_bridge import SerialBridge

def test_serial_bridge_mock():
    bridge = SerialBridge(port="COM99", mock_mode=True)
    assert bridge.mock_mode is True

    assert bridge.send_valve_command(valve_num=1, pulse_ms=100) is True
    assert bridge.send_emergency_stop() is True
    bridge.close()
