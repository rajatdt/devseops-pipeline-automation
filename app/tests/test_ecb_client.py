from unittest.mock import MagicMock, patch

import pytest

from app.services.ecb_client import ECBClient

SAMPLE_IRS_CSV = """KEY,FREQ,REF_AREA,IR_TYPE,TR_TYPE,MATURITY_CAT,BS_COUNT_SECTOR,CURRENCY_TRANS,IR_BUS_COV,IR_FV_TYPE,TIME_PERIOD,OBS_VALUE
IRS.M.DE.L.L40.CI.0000.EUR.N.Z,M,DE,L,L40,CI,0000,EUR,N,Z,2024-12,2.3456
IRS.M.FR.L.L40.CI.0000.EUR.N.Z,M,FR,L,L40,CI,0000,EUR,N,Z,2024-12,3.1234
"""

SAMPLE_FM_CSV = """KEY,FREQ,REF_AREA,CURRENCY,PROVIDER_FM,INSTRUMENT_FM,PROVIDER_FM_ID,DATA_TYPE_FM,TIME_PERIOD,OBS_VALUE
FM.M.U2.EUR.4F.BB.U2_10Y.YLD,M,U2,EUR,4F,BB,U2_10Y,YLD,2024-12,2.8100
FM.M.U2.EUR.4F.BB.U2_5Y.YLD,M,U2,EUR,4F,BB,U2_5Y,YLD,2024-12,2.5400
"""

SAMPLE_YC_CSV = """KEY,FREQ,REF_AREA,CURRENCY,PROVIDER_FM,INSTRUMENT_FM,PROVIDER_FM_ID,DATA_TYPE_FM,TIME_PERIOD,OBS_VALUE
YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_1Y,B,U2,EUR,4F,G_N_A,SV_C_YM,SR_1Y,2024-12-20,2.5000
YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y,B,U2,EUR,4F,G_N_A,SV_C_YM,SR_10Y,2024-12-20,2.9000
"""


@pytest.fixture
def client():
    c = ECBClient()
    c._cache.clear()
    return c


def _mock_response(csv_text: str):
    mock = MagicMock()
    mock.text = csv_text
    mock.raise_for_status = MagicMock()
    return mock


class TestGetCountryYields:
    @patch("app.services.ecb_client.httpx.get")
    def test_returns_yields_for_eur_countries(self, mock_get, client):
        mock_get.return_value = _mock_response(SAMPLE_IRS_CSV)

        results = client.get_country_yields(country_codes=["DE", "FR"])

        assert len(results) == 2
        de = next(r for r in results if r["country_code"] == "DE")
        assert de["country_name"] == "Germany"
        assert de["currency"] == "EUR"
        assert de["maturity"] == "10Y"
        assert de["yield_percent"] == 2.3456
        assert de["date"] == "2024-12"

    @patch("app.services.ecb_client.httpx.get")
    def test_caches_results(self, mock_get, client):
        mock_get.return_value = _mock_response(SAMPLE_IRS_CSV)

        client.get_country_yields(country_codes=["DE", "FR"])
        client.get_country_yields(country_codes=["DE", "FR"])

        assert mock_get.call_count == 1


class TestGetBenchmarkYields:
    @patch("app.services.ecb_client.httpx.get")
    def test_returns_benchmark_yields(self, mock_get, client):
        mock_get.return_value = _mock_response(SAMPLE_FM_CSV)

        results = client.get_benchmark_yields()

        assert len(results) == 2
        ten_y = next(r for r in results if r["maturity"] == "10Y")
        assert ten_y["area"] == "U2"
        assert ten_y["area_name"] == "Euro Area"
        assert ten_y["yield_percent"] == 2.81


class TestGetYieldCurve:
    @patch("app.services.ecb_client.httpx.get")
    def test_returns_sorted_yield_curve(self, mock_get, client):
        mock_get.return_value = _mock_response(SAMPLE_YC_CSV)

        results = client.get_yield_curve()

        assert len(results) == 2
        assert results[0]["maturity"] == "1Y"
        assert results[1]["maturity"] == "10Y"
        assert results[0]["rating"] == "AAA"
