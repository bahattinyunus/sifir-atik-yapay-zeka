import sys
import os
import numpy as np
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "yapay-zeka", "modeller"))
from yolo_detector import MultiObjectPolymerDetector

def test_multi_object_detector_tracking():
    detector = MultiObjectPolymerDetector(min_area=500)

    # Sahte bir kamera karesi (480x640)
    frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
    # Bant üzerine beyaz bir plastik şişe çiz
    frame1[150:220, 200:260] = 255

    results1 = detector.detect_and_track(frame1)
    assert len(results1) >= 1
    first_track_id = results1[0]["track_id"]
    assert first_track_id > 0
    assert "bbox" in results1[0]
    assert "class_name" in results1[0]

    # İkinci karede atık biraz ilerledi
    frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
    frame2[150:220, 215:275] = 255

    results2 = detector.detect_and_track(frame2)
    assert len(results2) >= 1
    # Aynı nesne aynı ID ile takip edilmeli
    assert results2[0]["track_id"] == first_track_id
