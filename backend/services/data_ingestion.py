"""
Data Ingestion Layer — GitHub CSV Cache
────────────────────────────────────────
Reads market data from a pre-built CSV hosted on GitHub.
Updated daily by GitHub Actions (scripts/update_data.py).

Zero Yahoo Finance dependency at request time.
"""

import logging
import httpx
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

CSV_URL = "https://raw.githubusercontent.com/mannkaram120/CreditRisk/main/market_data.csv"
CACHE_TTL_HOURS = 1
REQUEST_TIMEOUT = 15

_csv_cache: Optional[pd.DataFrame] = None
_csv_cached_at: Optional[datetime] = None
_ticker_cache: dict[str, tuple[datetime, dict]] = {}
_TICKER_TTL = 15


def _get_ticker_cached(key: str) -> Optional[dict]:
    if key in _ticker_cache:
        cached_at, data = _ticker_cache[key]
        if datetime.utcnow() - cached_at < timedelta(minutes=_TICKER_TTL):
            return data
    return None


def _set_ticker_cache(key: str, data: dict):
    _ticker_cache[key] = (datetime.utcnow(), data)


def _load_csv() -> pd.DataFrame:
    global _csv_cache, _csv_cached_at
    now = datetime.utcnow()
    if (
        _csv_cache is not None
        and _csv_cached_at is not None
        and now - _csv_cached_at < timedelta(hours=CACHE_TTL_HOURS)
    ):
        return _csv_cache

    logger.info("Loading market data CSV from GitHub...")
    try:
        response = httpx.get(CSV_URL, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        df["ticker"] = df["ticker"].str.strip().str.upper()
        df = df.set_index("ticker")
        _csv_cache = df
        _csv_cached_at = now
        logger.info("CSV loaded: %d tickers", len(df))
        return df
    except httpx.HTTPError as e:
        logger.error("Failed to fetch CSV: %s", e)
        if _csv_cache is not None:
            logger.warning("Using stale CSV cache as fallback")
            return _csv_cache
        raise RuntimeError(f"Could not load market data CSV from GitHub: {e}") from e


def fetch_ticker_data(
    ticker: str,
    closing_prices_override: list[float] | None = None,
) -> dict:
    ticker_upper = ticker.strip().upper()
    cached = _get_ticker_cached(ticker_upper)
    if cached:
        return cached

    df = _load_csv()

    if ticker_upper not in df.index:
        raise RuntimeError(
            f"Ticker '{ticker_upper}' not found in market_data.csv. "
            f"Add it to scripts/update_data.py TICKERS list and re-run the GitHub Action."
        )

    row = df.loc[ticker_upper]
    company_name      = str(row.get("company_name", ticker_upper))
    sector            = str(row.get("sector", "Unknown"))
    market_cap        = float(row.get("market_cap", 0))
    total_debt        = float(row.get("total_debt", 0))
    equity_volatility = float(row.get("equity_volatility", 0.25))

    if market_cap <= 0:
        raise RuntimeError(
            f"Market cap is zero for '{ticker_upper}' in the CSV. "
            "The last GitHub Actions run may have failed for this ticker."
        )

    closing_prices = closing_prices_override if closing_prices_override is not None else []

    result = {
        "company_name":      company_name,
        "sector":            sector,
        "market_cap":        market_cap,
        "total_debt":        total_debt,
        "closing_prices":    closing_prices,
        "equity_volatility": equity_volatility,
    }
    _set_ticker_cache(ticker_upper, result)
    return result


def fetch_bulk_price_histories(tickers: list[str]) -> dict[str, list[float]]:
    """Compatibility stub — volatility is pre-computed in CSV."""
    return {}


def get_available_tickers() -> list[str]:
    return _load_csv().index.tolist()


PRESETS: dict[str, list[dict]] = {
    "ig": [
        {"ticker": "AAPL", "notional": 10_000_000},
        {"ticker": "MSFT", "notional": 10_000_000},
        {"ticker": "JPM",  "notional": 10_000_000},
        {"ticker": "JNJ",  "notional": 10_000_000},
        {"ticker": "PG",   "notional": 10_000_000},
    ],
    "hy": [
        {"ticker": "F",   "notional": 10_000_000},
        {"ticker": "M",   "notional": 10_000_000},
        {"ticker": "CCL", "notional": 10_000_000},
        {"ticker": "AAL", "notional": 10_000_000},
        {"ticker": "AMC", "notional":  5_000_000},
    ],
    "mixed": [
        {"ticker": "AAPL", "notional": 15_000_000},
        {"ticker": "MSFT", "notional": 15_000_000},
        {"ticker": "JPM",  "notional": 10_000_000},
        {"ticker": "F",    "notional":  7_000_000},
        {"ticker": "CCL",  "notional":  7_000_000},
        {"ticker": "AAL",  "notional":  6_000_000},
    ],
    "crisis": [
        {"ticker": "C",   "notional": 10_000_000},
        {"ticker": "BAC", "notional": 10_000_000},
        {"ticker": "GS",  "notional": 10_000_000},
        {"ticker": "MS",  "notional": 10_000_000},
        {"ticker": "WFC", "notional": 10_000_000},
    ],
}
