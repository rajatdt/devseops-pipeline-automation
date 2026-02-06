from __future__ import annotations

import time
from io import StringIO
from typing import Dict, List, Optional

import httpx
import pandas as pd

from app.config import settings

# Country code to name mapping for IRS dataset
COUNTRY_NAMES = {
    "DE": "Germany", "FR": "France", "IT": "Italy", "ES": "Spain",
    "NL": "Netherlands", "BE": "Belgium", "AT": "Austria", "PT": "Portugal",
    "GR": "Greece", "IE": "Ireland", "FI": "Finland", "HR": "Croatia",
    "SK": "Slovakia", "SI": "Slovenia", "LV": "Latvia", "LT": "Lithuania",
    "LU": "Luxembourg", "CY": "Cyprus", "MT": "Malta", "EE": "Estonia",
    "BG": "Bulgaria", "CZ": "Czech Republic", "DK": "Denmark",
    "HU": "Hungary", "PL": "Poland", "RO": "Romania", "SE": "Sweden",
}

# Country code to currency mapping for non-EUR countries
COUNTRY_CURRENCIES = {
    "BG": "BGN", "CZ": "CZK", "DK": "DKK",
    "HU": "HUF", "PL": "PLN", "RO": "RON", "SE": "SEK",
}

# Benchmark bond series in FM dataset
BENCHMARK_SERIES = {
    "U2_10Y": ("U2", "Euro Area", "EUR", "10Y"),
    "U2_7Y": ("U2", "Euro Area", "EUR", "7Y"),
    "U2_5Y": ("U2", "Euro Area", "EUR", "5Y"),
    "U2_3Y": ("U2", "Euro Area", "EUR", "3Y"),
    "U2_2Y": ("U2", "Euro Area", "EUR", "2Y"),
}

# Yield curve maturities
YC_MATURITIES = [
    "SR_3M", "SR_6M", "SR_1Y", "SR_2Y", "SR_3Y",
    "SR_5Y", "SR_7Y", "SR_10Y", "SR_15Y", "SR_20Y", "SR_30Y",
]


class CacheEntry:
    def __init__(self, data, ttl: int):
        self.data = data
        self.expires_at = time.time() + ttl

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class ECBClient:
    def __init__(self):
        self.base_url = settings.ecb_base_url
        self.cache_ttl = settings.cache_ttl_seconds
        self._cache: dict[str, CacheEntry] = {}

    def _get_cached(self, key: str):
        entry = self._cache.get(key)
        if entry and not entry.is_expired:
            return entry.data
        return None

    def _set_cached(self, key: str, data):
        self._cache[key] = CacheEntry(data, self.cache_ttl)

    def _fetch_csv(self, dataset: str, series_key: str, params: dict | None = None) -> pd.DataFrame:
        url = f"{self.base_url}/{dataset}/{series_key}"
        query_params = {"format": "csvdata"}
        if params:
            query_params.update(params)

        response = httpx.get(url, params=query_params, timeout=30.0)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))

    def get_country_yields(self, country_codes: list[str] | None = None) -> list[dict]:
        """Fetch 10-year government bond yields from the IRS dataset."""
        if country_codes is None:
            country_codes = list(COUNTRY_NAMES.keys())

        cache_key = f"irs:{'_'.join(sorted(country_codes))}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        # Build series keys grouped by currency
        eur_countries = [c for c in country_codes if c not in COUNTRY_CURRENCIES]
        non_eur_countries = [c for c in country_codes if c in COUNTRY_CURRENCIES]

        results = []

        if eur_countries:
            key = f"M.{'+'.join(eur_countries)}.L.L40.CI.0000.EUR.N.Z"
            df = self._fetch_csv("IRS", key, {"lastNObservations": "1"})
            for _, row in df.iterrows():
                ref_area = row["REF_AREA"]
                results.append({
                    "country_code": ref_area,
                    "country_name": COUNTRY_NAMES.get(ref_area, ref_area),
                    "currency": "EUR",
                    "maturity": "10Y",
                    "yield_percent": round(float(row["OBS_VALUE"]), 4),
                    "date": str(row["TIME_PERIOD"]),
                })

        for cc in non_eur_countries:
            currency = COUNTRY_CURRENCIES[cc]
            key = f"M.{cc}.L.L40.CI.0000.{currency}.N.Z"
            try:
                df = self._fetch_csv("IRS", key, {"lastNObservations": "1"})
                for _, row in df.iterrows():
                    results.append({
                        "country_code": cc,
                        "country_name": COUNTRY_NAMES.get(cc, cc),
                        "currency": currency,
                        "maturity": "10Y",
                        "yield_percent": round(float(row["OBS_VALUE"]), 4),
                        "date": str(row["TIME_PERIOD"]),
                    })
            except httpx.HTTPStatusError:
                continue

        self._set_cached(cache_key, results)
        return results

    def get_benchmark_yields(self) -> list[dict]:
        """Fetch euro area benchmark bond yields at multiple maturities from the FM dataset."""
        cache_key = "fm:benchmarks"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        series_ids = "+".join(BENCHMARK_SERIES.keys())
        key = f"M.U2.EUR.4F.BB.{series_ids}.YLD"
        df = self._fetch_csv("FM", key, {"lastNObservations": "1"})

        results = []
        for _, row in df.iterrows():
            provider_id = row["PROVIDER_FM_ID"]
            if provider_id in BENCHMARK_SERIES:
                area, area_name, currency, maturity = BENCHMARK_SERIES[provider_id]
                results.append({
                    "area": area,
                    "area_name": area_name,
                    "currency": currency,
                    "maturity": maturity,
                    "yield_percent": round(float(row["OBS_VALUE"]), 4),
                    "date": str(row["TIME_PERIOD"]),
                })

        self._set_cached(cache_key, results)
        return results

    def get_yield_curve(self, rating: str = "G_N_A") -> list[dict]:
        """Fetch the euro area yield curve from the YC dataset.

        Args:
            rating: G_N_A for AAA-rated bonds, G_N_C for all ratings.
        """
        cache_key = f"yc:{rating}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        maturities_key = "+".join(YC_MATURITIES)
        key = f"B.U2.EUR.4F.{rating}.SV_C_YM.{maturities_key}"
        df = self._fetch_csv("YC", key, {"lastNObservations": "1"})

        results = []
        for _, row in df.iterrows():
            maturity_raw = row["DATA_TYPE_FM"]
            maturity = maturity_raw.replace("SR_", "")
            results.append({
                "maturity": maturity,
                "spot_rate": round(float(row["OBS_VALUE"]), 4),
                "date": str(row["TIME_PERIOD"]),
                "rating": "AAA" if rating == "G_N_A" else "All",
            })

        results.sort(key=lambda x: _maturity_sort_key(x["maturity"]))
        self._set_cached(cache_key, results)
        return results


def _maturity_sort_key(maturity: str) -> float:
    """Convert maturity string like '3M', '1Y', '10Y' to a numeric value for sorting."""
    if maturity.endswith("M"):
        return float(maturity[:-1]) / 12
    if maturity.endswith("Y"):
        return float(maturity[:-1])
    return 0.0


ecb_client = ECBClient()
