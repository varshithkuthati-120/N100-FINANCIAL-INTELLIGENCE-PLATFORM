from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_sector_companies():
    response = client.get("/api/v1/sectors/IT/companies")
    if response.status_code == 200:
        assert isinstance(response.json(), list)
    else:
        assert response.status_code == 404
