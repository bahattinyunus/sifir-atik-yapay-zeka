import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "arayuz", "backend"))
from main import app
from database import init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_api_environmental_impact(client):
    response = client.get("/api/environmental-impact")
    assert response.status_code == 200
    data = response.json()
    assert "total_mass_kg" in data
    assert "total_co2_saved_kg" in data
    assert "total_energy_saved_kwh" in data
    assert "total_water_saved_liters" in data
    assert "equivalent_trees_saved" in data
    assert "by_polymer" in data
    assert "PET" in data["by_polymer"]

def test_api_logs(client):
    response = client.get("/api/logs?limit=15")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
