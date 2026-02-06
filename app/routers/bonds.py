from fastapi import APIRouter, HTTPException, Query

from app.models.bond import BenchmarkYield, BondYield, YieldCurvePoint
from app.services.ecb_client import COUNTRY_NAMES, ecb_client

router = APIRouter(prefix="/api/v1/bonds", tags=["bonds"])


@router.get("/yields", response_model=list[BondYield])
def get_all_yields():
    """Get the latest 10-year government bond yields for all tracked EU countries."""
    try:
        data = ecb_client.get_country_yields()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ECB API error: {e}")
    return [BondYield(**item) for item in data]


@router.get("/yields/{country_code}", response_model=list[BondYield])
def get_yield_by_country(country_code: str):
    """Get the latest 10-year government bond yield for a specific country."""
    cc = country_code.upper()
    if cc not in COUNTRY_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"Country code '{cc}' not found. Valid codes: {', '.join(sorted(COUNTRY_NAMES.keys()))}",
        )
    try:
        data = ecb_client.get_country_yields(country_codes=[cc])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ECB API error: {e}")
    if not data:
        raise HTTPException(status_code=404, detail=f"No yield data available for {cc}")
    return [BondYield(**item) for item in data]


@router.get("/benchmarks", response_model=list[BenchmarkYield])
def get_benchmarks():
    """Get euro area benchmark bond yields at multiple maturities (2Y, 3Y, 5Y, 7Y, 10Y)."""
    try:
        data = ecb_client.get_benchmark_yields()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ECB API error: {e}")
    return [BenchmarkYield(**item) for item in data]


@router.get("/yield-curve", response_model=list[YieldCurvePoint])
def get_yield_curve(
    rating: str = Query(
        default="AAA",
        description="Bond rating filter: 'AAA' for AAA-rated bonds, 'All' for all ratings",
    ),
):
    """Get the current euro area yield curve (spot rates at various maturities)."""
    rating_key = "G_N_A" if rating.upper() == "AAA" else "G_N_C"
    try:
        data = ecb_client.get_yield_curve(rating=rating_key)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ECB API error: {e}")
    return [YieldCurvePoint(**item) for item in data]
