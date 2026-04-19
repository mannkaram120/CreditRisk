"""
Router: /merton/{ticker}
"""

from fastapi import APIRouter, HTTPException
from services.merton import solve_merton, get_lgd, dd_to_label
from services.data_ingestion import fetch_ticker_data
from models.schemas import MertonResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{ticker}", response_model=MertonResponse)
async def get_merton_analysis(ticker: str):
    ticker = ticker.strip().upper()

    try:
        data = fetch_ticker_data(ticker)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    market_cap        = data["market_cap"]
    equity_volatility = data["equity_volatility"]
    total_debt        = data["total_debt"]
    company_name      = data["company_name"]
    sector            = data["sector"]

    if market_cap <= 0:
        raise HTTPException(
            status_code=422,
            detail=f"Could not retrieve market cap for {ticker}. "
                   "Ensure this is an equity ticker with traded shares.",
        )

    try:
        merton = solve_merton(
            equity_value=market_cap,
            equity_volatility=equity_volatility,
            total_debt=total_debt,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"Merton solver error: {exc}")

    lgd = get_lgd(sector)
    dd  = merton["distance_to_default"]

    return MertonResponse(
        ticker=ticker,
        company_name=company_name,
        market_cap=market_cap,
        total_debt=total_debt,
        equity_volatility=equity_volatility,
        asset_value=merton["asset_value"],
        asset_volatility=merton["asset_volatility"],
        distance_to_default=dd,
        probability_of_default=merton["probability_of_default"],
        risk_label=dd_to_label(dd),
        lgd=lgd,
        sector=sector,
    )
