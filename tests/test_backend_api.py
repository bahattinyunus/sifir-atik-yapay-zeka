import sys
import os
import pytest
from fastapi.testclient import TestClient

# Backend dizinini yola ekle
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "arayuz", "backend"))
from main import app
from database import init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_api_stats(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "total_count" in data["summary"]
    assert "counts" in data["summary"]

def test_api_detect_and_history(client):
    payload = {
        "type": "PET",
        "confidence": 97.5,
        "timestamp": "12:00:00",
        "inference_ms": 15.2,
        "actuated": True,
        "source": "unit-test"
    }
    response = client.post("/api/detect", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "id" in res_data

    # History'de görebilmeliyiz
    hist_resp = client.get("/api/history?limit=10")
    assert hist_resp.status_code == 200
    items = hist_resp.json()
    assert len(items) > 0
    assert items[0]["waste_type"] == "PET"

def test_api_config(client):
    # Ayarları al
    cfg_resp = client.get("/api/config")
    assert cfg_resp.status_code == 200
    cfg = cfg_resp.json()
    assert "conveyor_speed_m_s" in cfg

    # Ayarları güncelle
    upd_resp = client.post("/api/config", json={"conveyor_speed_m_s": "0.45", "confidence_threshold": "80.0"})
    assert upd_resp.status_code == 200
    assert upd_resp.json()["status"] == "success"

def test_api_system_status(client):
    resp = client.get("/api/system-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "cpu_usage_pct" in data
    assert "ram_usage_pct" in data

def test_api_simulate(client):
    resp = client.post("/api/simulate", json={"count": 2, "force_type": "HDPE"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["generated"] == 2
    assert data["items"][0]["type"] == "HDPE"

def test_api_estop(client):
    resp = client.post("/api/e-stop")
    assert resp.status_code == 200
    assert resp.json()["status"] == "emergency_stop_activated"

    resp_reset = client.post("/api/e-stop/reset")
    assert resp_reset.status_code == 200
    assert resp_reset.json()["status"] == "system_resumed"

def test_api_export_csv(client):
    resp = client.get("/api/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "Atık Türü" in resp.text or "waste_type" in resp.text or "ID" in resp.text
