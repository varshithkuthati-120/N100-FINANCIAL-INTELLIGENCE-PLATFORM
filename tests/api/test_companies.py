from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_companies():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "ticker" in data[0]

def test_get_companies_filter_sector():
    response = client.get("/api/v1/companies?sector=IT")
    assert response.status_code == 200
    data = response.json()
    for comp in data:
        assert comp["broad_sector"] == "IT"

def test_get_company_profile():
    response = client.get("/api/v1/companies/RELIANCE")
    assert response.status_code == 200
    assert response.json()["ticker"] == "RELIANCE"

def test_get_company_not_found():
    response = client.get("/api/v1/companies/INVALID")
    assert response.status_code == 404
