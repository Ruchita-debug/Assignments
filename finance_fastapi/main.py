from fastapi import FastAPI, HTTPException
from datetime import timedelta
from .schemas import (
    CompanyInfoRequest,
    CompanyInfoResponse,
    StockMarketDataResponse,
    HistoricalMarketDataRequest,
    HistoricalMarketDataResponse,
    AnalyticalInsightsRequest,
    AnalyticalInsightsResponse,
)
import yfinance as yf


app = FastAPI()


def _is_invalid_company_info(company_info: dict) -> bool:
    required_profile_fields = (
        "displayName",
        "longName",
        "shortName",
        "longBusinessSummary",
        "industry",
        "sector",
    )
    return not any(company_info.get(field) for field in required_profile_fields)


def _is_invalid_stock_info(company_info: dict) -> bool:
    required_market_fields = (
        "currentPrice",
        "regularMarketPrice",
        "previousClose",
        "marketState",
    )
    return not any(company_info.get(field) is not None for field in required_market_fields)


def _to_optional_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_optional_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _get_index_date_text(index_value) -> str:
    isoformat_fn = getattr(index_value, "isoformat", None)
    if callable(isoformat_fn):
        date_value = isoformat_fn()
    else:
        date_value = str(index_value)
    return str(date_value).split("T")[0]


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/company_info", response_model=CompanyInfoResponse)
def get_company_info(request: CompanyInfoRequest):
    company_symbol = request.company_symbol.strip().upper()
    if not company_symbol:
        raise HTTPException(
            status_code=400, detail="company_symbol cannot be empty")

    try:
        company_ticker_obj = yf.Ticker(company_symbol)
        company_info = company_ticker_obj.info
    except Exception:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch company data for symbol '{company_symbol}'",
        )

    if not company_info:
        raise HTTPException(
            status_code=404,
            detail=f"No company data found for symbol '{company_symbol}'",
        )

    if _is_invalid_company_info(company_info):
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch company data for symbol '{company_symbol}'",
        )

    officers = company_info.get("companyOfficers") or []

    return {
        "company_name": company_info.get("displayName", "N/A"),
        "business_summary": company_info.get("longBusinessSummary", "N/A"),
        "industry": company_info.get("industry", "N/A"),
        "sector": company_info.get("sector", "N/A"),
        "key_officers": [
            f'{officer.get("name", "Unknown")} - {officer.get("title", "Unknown")}'
            for officer in officers
        ],
    }


@app.post("/stock_market", response_model=StockMarketDataResponse)
def get_stock_market_data(request: CompanyInfoRequest):
    company_symbol = request.company_symbol.strip().upper()

    if not company_symbol:
        raise HTTPException(
            status_code=400, detail="Company symbol cannot be empty.")

    try:
        company_ticker_obj = yf.Ticker(company_symbol)
        company_info = company_ticker_obj.info
    except Exception:
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch company data for {company_symbol}"
        )
    if not company_info:
        raise HTTPException(
            status_code=404,
            detail=f"No stock data found for symbol '{company_symbol}'",
        )

    if _is_invalid_stock_info(company_info):
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch company data for symbol '{company_symbol}'",
        )

    current_price = company_info.get("currentPrice", None)
    previous_close = company_info.get("previousClose", None)

    if current_price is None or previous_close is None:
        price_change = None
        percentage_change = None
    else:
        price_change = current_price - previous_close
        if previous_close == 0:
            percentage_change = None
        else:
            percentage_change = price_change / previous_close * 100

    return {
        "market_state": company_info.get("marketState", "N/A"),
        "current_price": current_price,
        "previous_close": previous_close,
        "price_change": price_change,
        "percentage_change": percentage_change,
        "currency": company_info.get("currency", "N/A"),
        "day_high": company_info.get("dayHigh"),
        "day_low": company_info.get("dayLow"),
        "volume": company_info.get("volume"),
        "exchange": company_info.get("exchange", "N/A")
    }


@app.post("/historical_market_data", response_model=HistoricalMarketDataResponse)
def get_historical_market_data(request: HistoricalMarketDataRequest):
    company_symbol = request.company_symbol.strip().upper()

    if not company_symbol:
        raise HTTPException(status_code=400, detail="Company symbol cannot be empty.")

    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be less than or equal to end_date.",
        )

    # yfinance uses an exclusive end date; add one day so the user's end_date is included.
    history_end_date = request.end_date + timedelta(days=1)

    try:
        company_ticker_obj = yf.Ticker(company_symbol)
        historical_df = company_ticker_obj.history(
            start=request.start_date.isoformat(),
            end=history_end_date.isoformat(),
            interval=request.interval,
            auto_adjust=False,
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch historical data for symbol '{company_symbol}'",
        )

    if historical_df is None or historical_df.empty:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch historical data for symbol '{company_symbol}'",
        )

    historical_data = []
    for idx, row in historical_df.iterrows():
        date_text = _get_index_date_text(idx)

        historical_data.append(
            {
                "date": date_text,
                "open": _to_optional_float(row.get("Open")),
                "high": _to_optional_float(row.get("High")),
                "low": _to_optional_float(row.get("Low")),
                "close": _to_optional_float(row.get("Close")),
                "volume": _to_optional_int(row.get("Volume")),
            }
        )

    return {
        "symbol": company_symbol,
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "interval": request.interval,
        "data": historical_data,
    }


@app.post("/analytical_insights", response_model=AnalyticalInsightsResponse)
def get_analytical_insights(request: AnalyticalInsightsRequest):
    company_symbol = request.company_symbol.strip().upper()

    if not company_symbol:
        raise HTTPException(status_code=400, detail="Company symbol cannot be empty.")

    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be less than or equal to end_date.",
        )

    history_end_date = request.end_date + timedelta(days=1)

    try:
        company_ticker_obj = yf.Ticker(company_symbol)
        historical_df = company_ticker_obj.history(
            start=request.start_date.isoformat(),
            end=history_end_date.isoformat(),
            interval=request.interval,
            auto_adjust=False,
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch historical data for symbol '{company_symbol}'",
        )

    if historical_df is None or historical_df.empty:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch historical data for symbol '{company_symbol}'",
        )

    close_series = historical_df["Close"].dropna()
    if close_series.empty:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch usable close-price data for symbol '{company_symbol}'",
        )

    volume_series = historical_df["Volume"].dropna() if "Volume" in historical_df.columns else None

    first_close = _to_optional_float(close_series.iloc[0])
    latest_close = _to_optional_float(close_series.iloc[-1])

    total_return_percent = None
    if first_close not in (None, 0) and latest_close is not None:
        total_return_percent = round(((latest_close - first_close) / first_close) * 100, 2)

    daily_returns = close_series.pct_change().dropna()

    average_daily_return_percent = None
    volatility_percent = None
    if not daily_returns.empty:
        average_daily_return_percent = round(float(daily_returns.mean()) * 100, 4)
        volatility_percent = round(float(daily_returns.std()) * 100, 4)

    highest_close = _to_optional_float(close_series.max())
    lowest_close = _to_optional_float(close_series.min())

    highest_close_date = None
    lowest_close_date = None
    try:
        highest_close_date = _get_index_date_text(close_series.idxmax())
    except Exception:
        pass
    try:
        lowest_close_date = _get_index_date_text(close_series.idxmin())
    except Exception:
        pass

    latest_volume = None
    if volume_series is not None and not volume_series.empty:
        latest_volume = _to_optional_int(volume_series.iloc[-1])

    trend_direction = "Sideways"
    if len(close_series) >= 50:
        ma_20 = float(close_series.tail(20).mean())
        ma_50 = float(close_series.tail(50).mean())
        if ma_20 > ma_50:
            trend_direction = "Uptrend"
        elif ma_20 < ma_50:
            trend_direction = "Downtrend"
    elif total_return_percent is not None:
        if total_return_percent > 1:
            trend_direction = "Uptrend"
        elif total_return_percent < -1:
            trend_direction = "Downtrend"

    risk_label = "Medium"
    if volatility_percent is not None:
        if volatility_percent < 1:
            risk_label = "Low"
        elif volatility_percent > 2.5:
            risk_label = "High"

    insights = []
    if total_return_percent is not None:
        if total_return_percent >= 0:
            insights.append(f"Stock gained {total_return_percent}% over the selected period.")
        else:
            insights.append(
                f"Stock declined {abs(total_return_percent)}% over the selected period."
            )

    insights.append(f"Trend appears to be {trend_direction.lower()} based on recent price behavior.")

    if volatility_percent is not None:
        if volatility_percent < 1:
            insights.append("Volatility is low, indicating relatively stable price movement.")
        elif volatility_percent <= 2.5:
            insights.append("Volatility is moderate, suggesting balanced risk and movement.")
        else:
            insights.append("Volatility is high, indicating elevated risk and larger price swings.")

    return {
        "symbol": company_symbol,
        "period": {
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "interval": request.interval,
        },
        "metrics": {
            "total_return_percent": total_return_percent,
            "average_daily_return_percent": average_daily_return_percent,
            "volatility_percent": volatility_percent,
            "latest_close": latest_close,
            "latest_volume": latest_volume,
            "highest_close": highest_close,
            "highest_close_date": highest_close_date,
            "lowest_close": lowest_close,
            "lowest_close_date": lowest_close_date,
            "trend_direction": trend_direction,
        },
        "insights": insights,
        "risk_label": risk_label,
    }
