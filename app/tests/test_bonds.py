from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_YIELDS = [
    {
        "country_code": "DE",
        "country_name": "Germany",
        "currency": "EUR",
        "maturity": "10Y",
        "yield_percent": 2.35,
        "date": "2024-12",
    },
]

MOCK_BENCHMARKS = [
    {
        "area": "U2",
        "area_name": "Euro Area",
        "currency": "EUR",
        "maturity": "10Y",
        "yield_percent": 2.81,
        "date": "2024-12",
    },
]

MOCK_YIELD_CURVE = [
    {
        "maturity": "1Y",
        "spot_rate": 2.50,
        "date": "2024-12-20",
        "rating": "AAA",
    },
    {
        "maturity": "10Y",
        "spot_rate": 2.90,
        "date": "2024-12-20",
        "rating": "AAA",
    },
]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "app" in response.json()


class TestYieldsEndpoint:
    @patch("app.routers.bonds.ecb_client.get_country_yields")
    def test_get_all_yields(self, mock_yields):
        mock_yields.return_value = MOCK_YIELDS
        response = client.get("/api/v1/bonds/yields")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["country_code"] == "DE"

    @patch("app.routers.bonds.ecb_client.get_country_yields")
    def test_get_yield_by_country(self, mock_yields):
        mock_yields.return_value = MOCK_YIELDS
        response = client.get("/api/v1/bonds/yields/DE")
        assert response.status_code == 200
        assert response.json()[0]["country_name"] == "Germany"

    def test_get_yield_invalid_country(self):
        response = client.get("/api/v1/bonds/yields/XX")
        assert response.status_code == 404

    @patch("app.routers.bonds.ecb_client.get_country_yields")
    def test_country_code_case_insensitive(self, mock_yields):
        mock_yields.return_value = MOCK_YIELDS
        response = client.get("/api/v1/bonds/yields/de")
        assert response.status_code == 200


class TestBenchmarksEndpoint:
    @patch("app.routers.bonds.ecb_client.get_benchmark_yields")
    def test_get_benchmarks(self, mock_benchmarks):
        mock_benchmarks.return_value = MOCK_BENCHMARKS
        response = client.get("/api/v1/bonds/benchmarks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["maturity"] == "10Y"


class TestYieldCurveEndpoint:
    @patch("app.routers.bonds.ecb_client.get_yield_curve")
    def test_get_yield_curve_default(self, mock_yc):
        mock_yc.return_value = MOCK_YIELD_CURVE
        response = client.get("/api/v1/bonds/yield-curve")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch("app.routers.bonds.ecb_client.get_yield_curve")
    def test_get_yield_curve_all_ratings(self, mock_yc):
        mock_yc.return_value = MOCK_YIELD_CURVE
        response = client.get("/api/v1/bonds/yield-curve?rating=All")
        assert response.status_code == 200
        mock_yc.assert_called_with(rating="G_N_C")
