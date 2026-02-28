import pytest
from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestPapersEndpoint:
    def test_list_papers_returns_list(self):
        response = client.get("/papers/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_nonexistent_paper_returns_404(self):
        response = client.get("/papers/nonexistent_id")
        assert response.status_code == 404

    def test_search_requires_query(self):
        response = client.get("/papers/search")
        assert response.status_code == 422

    def test_search_returns_results_structure(self):
        response = client.get("/papers/search?q=machine+learning")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
