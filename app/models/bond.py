from pydantic import BaseModel


class BondYield(BaseModel):
    country_code: str
    country_name: str
    currency: str
    maturity: str
    yield_percent: float
    date: str


class BenchmarkYield(BaseModel):
    area: str
    area_name: str
    currency: str
    maturity: str
    yield_percent: float
    date: str


class YieldCurvePoint(BaseModel):
    maturity: str
    spot_rate: float
    date: str
    rating: str
