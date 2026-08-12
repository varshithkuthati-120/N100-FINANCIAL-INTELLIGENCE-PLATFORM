from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_screener_min_roe():
    response = client.get("/api/v1/screener?min_roe=15.0")
    assert response.status_code == 200
    data = response.json()
    for item in data:
        assert item["roe"] >= 15.0

def test_screener_invalid_param():
    response = client.get("/api/v1/screener?min_roe=abc")
    assert response.status_code == 422
