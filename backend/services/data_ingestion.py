"""
Data Ingestion Layer — Excel Source
────────────────────────────────────
Reads company data from Excel file maintained by user.

Zero API calls, no rate limiting, instant responses!

What this version does:
- Reads from Excel file (user maintains)
- 15-min in-memory cache
- 100% reliable (no API dependencies)
- Supports stress testing with price overrides
- Compatible with portfolio_snapshot.py
"""

import time
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from services.excel_source import get_excel_source

logger = logging.getLogger(__name__)

# ─── TTL cache ────────────────────────────────────────────────────────────────
_cache: dict[str, tuple[datetime, dict]] = {}
_CACHE_TTL_MINUTES = 15


def _get_cached(key: str) -> Optional[dict]:
    """Get cached data if still fresh."""
    if key in _cache:
        cached_at, data = _cache[key]
        if datetime.utcnow() - cached_at < timedelta(minutes=_CACHE_TTL_MINUTES):
            return data
    return None


def _set_cache(key: str, data: dict):
    """Cache data with timestamp."""
    _cache[key] = (datetime.utcnow(), data)


# ─── Main fetch function ──────────────────────────────────────────────────────
def fetch_ticker_data(
    ticker: str,
    closing_prices_override: Optional[list[float]] = None,
) -> dict:
    """
    Fetch all data needed for the Merton model from Excel.

    Args:
        ticker: Stock ticker (e.g., 'AAPL')
        closing_prices_override: Override prices for stress testing

    Returns:
        dict with keys:
            company_name: str
            sector: str
            market_cap: float (USD)
            total_debt: float (USD)
            closing_prices: list[float]  (1 year of daily closes, oldest first)
            equity_volatility: float     (annualized)
    """
    ticker_upper = ticker.strip().upper()

    # Check in-memory cache first (15 min TTL)
    cached = _get_cached(ticker_upper)
    if cached:
        logger.debug("Cache hit for %s", ticker_upper)
        if closing_prices_override is not None:
            cached = cached.copy()
            cached['closing_prices'] = closing_prices_override
            # Recalculate volatility with override prices
            arr = np.array(closing_prices_override)
            log_ret = np.diff(np.log(arr))
            cached['equity_volatility'] = float(np.std(log_ret, ddof=1) * np.sqrt(252))
        return cached

    try:
        # Read from Excel
        logger.info("Reading %s from Excel", ticker_upper)
        excel = get_excel_source()
        data = excel.get_ticker_data(ticker_upper)

        # Apply override if provided (for stress testing)
        if closing_prices_override is not None:
            data['closing_prices'] = closing_prices_override
            # Recalculate volatility with override prices
            arr = np.array(closing_prices_override)
            log_ret = np.diff(np.log(arr))
            data['equity_volatility'] = float(np.std(log_ret, ddof=1) * np.sqrt(252))

        # Cache in memory for 15 minutes
        _set_cache(ticker_upper, data)
        return data

    except ValueError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        raise RuntimeError(f"Error reading {ticker} from Excel: {e}")


# ─── Bulk fetch for portfolio_snapshot.py ────────────────────────────────────
def fetch_bulk_price_histories(tickers: list[str]) -> dict[str, list[float]]:
    """
    Fetch price histories for multiple tickers from Excel.
    Skips failures silently.
    """
    result = {}
    for ticker in tickers:
        try:
            data = fetch_ticker_data(ticker)
            result[ticker.strip().upper()] = data['closing_prices']
            # Gentle pacing
            time.sleep(0.5)
        except Exception as e:
            logger.warning("Bulk fetch skipped %s: %s", ticker.upper(), e)
    return result


# ─── Preset portfolios ────────────────────────────────────────────────────────
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
