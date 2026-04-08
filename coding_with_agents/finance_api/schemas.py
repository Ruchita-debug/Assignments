from pydantic import BaseModel
from typing import Optional
from datetime import date


class CompanyInfoRequest(BaseModel):
    company_symbol: str


class CompanyInfoResponse(BaseModel):
    company_name: str
    business_summary: str
    industry: str
    sector: str
    key_officers: list[str]


class StockMarketDataResponse(BaseModel):
    market_state: str
    current_price: Optional[float]
    previous_close: Optional[float]
    price_change: Optional[float]
    percentage_change: Optional[float]
    currency: str
    day_high: Optional[float]
    day_low: Optional[float]
    volume: Optional[int]
    exchange: str


class HistoricalMarketDataRequest(BaseModel):
    company_symbol: str
    start_date: date
    end_date: date
    interval: str = "1d"


class HistoricalDataPoint(BaseModel):
    date: str
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]


class HistoricalMarketDataResponse(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    interval: str
    data: list[HistoricalDataPoint]


class AnalyticalInsightsRequest(BaseModel):
    company_symbol: str
    start_date: date
    end_date: date
    interval: str = "1d"


class AnalyticalPeriodInfo(BaseModel):
    start_date: str
    end_date: str
    interval: str


class AnalyticalMetricsInfo(BaseModel):
    total_return_percent: Optional[float]
    average_daily_return_percent: Optional[float]
    volatility_percent: Optional[float]
    latest_close: Optional[float]
    latest_volume: Optional[int]
    highest_close: Optional[float]
    highest_close_date: Optional[str]
    lowest_close: Optional[float]
    lowest_close_date: Optional[str]
    trend_direction: str


class AnalyticalInsightsResponse(BaseModel):
    symbol: str
    period: AnalyticalPeriodInfo
    metrics: AnalyticalMetricsInfo
    insights: list[str]
    risk_label: str
