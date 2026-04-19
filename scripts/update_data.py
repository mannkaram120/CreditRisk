"""
scripts/update_data.py
──────────────────────
Fetches live market data for 100+ tickers and writes market_data.csv.

Run manually:
    python scripts/update_data.py

Or automatically via GitHub Actions (.github/workflows/update_market_data.yml)
which runs every weekday at 06:00 UTC.

What it fetches per ticker:
    - company_name, sector       from yfinance info
    - market_cap                 from yfinance info
    - total_debt                 from quarterly/annual balance sheet
    - equity_volatility          annualised from 1y daily log returns
    - lgd                        sector-based lookup table

Output:
    market_data.csv — one row per ticker
    Backend reads this via GitHub raw URL — zero Yahoo dependency at runtime.
"""

import time
import logging
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Output path ──────────────────────────────────────────────────────────────
OUTPUT_PATH = Path(__file__).parent.parent / "market_data.csv"

# ─── Ticker universe (117 tickers) ───────────────────────────────────────────
# Add any ticker here — update_data.py fetches it automatically next run.

TICKERS = [
    # ── PRESET: Investment Grade (IG) ────────────────────────────────────────
    "AAPL", "MSFT", "JPM", "JNJ", "PG",

    # ── PRESET: High Yield (HY) ──────────────────────────────────────────────
    "F", "M", "CCL", "AAL", "AMC",

    # ── PRESET: Crisis / Financials ──────────────────────────────────────────
    "C", "BAC", "GS", "MS", "WFC",

    # ── LARGE CAP TECH ───────────────────────────────────────────────────────
    "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    "ORCL", "CRM", "ADBE", "INTC", "AMD",
    "QCOM", "TXN", "CSCO", "IBM", "NOW",

    # ── FINANCIALS / BANKS ───────────────────────────────────────────────────
    "BRK-B", "V", "MA", "AXP", "BLK",
    "SCHW", "USB", "PNC", "TFC", "COF",
    "DFS", "SYF", "AIG", "MET", "PRU",

    # ── HEALTHCARE ───────────────────────────────────────────────────────────
    "UNH", "LLY", "ABBV", "MRK", "PFE",
    "TMO", "ABT", "DHR", "BMY", "AMGN",
    "GILD", "ISRG", "SYK", "BSX", "HCA",

    # ── CONSUMER & RETAIL ────────────────────────────────────────────────────
    "WMT", "COST", "HD", "LOW", "TGT",
    "MCD", "SBUX", "NKE", "TJX",

    # ── ENERGY ───────────────────────────────────────────────────────────────
    "XOM", "CVX", "COP", "SLB", "EOG",
    "MPC", "PSX", "VLO", "OXY", "HAL",

    # ── INDUSTRIALS ──────────────────────────────────────────────────────────
    "BA", "CAT", "GE", "HON", "RTX",
    "LMT", "UPS", "FDX", "DE", "MMM",

    # ── UTILITIES ────────────────────────────────────────────────────────────
    "NEE", "DUK", "SO", "D", "AEP",

    # ── REAL ESTATE (REITs) ──────────────────────────────────────────────────
    "PLD", "AMT", "EQIX", "SPG", "O",

    # ── DISTRESSED / HIGH YIELD WATCH ────────────────────────────────────────
    "UAL", "DAL", "ALK", "HA", "NCLH",
    "RCL", "HLT", "MAR", "H", "MGM",

    # ── TELECOM ──────────────────────────────────────────────────────────────
    "T", "VZ", "TMUS",

    # ── MEDIA & ENTERTAINMENT ────────────────────────────────────────────────
    "DIS", "NFLX", "PARA", "WBD", "FOX",
]

# Deduplicate while preserving order
seen = set()
TICKERS = [t for t in TICKERS if not (t in seen or seen.add(t))]

# ─── LGD by sector ───────────────────────────────────────────────────────────
SECTOR_LGD: dict[str, float] = {
    "Financial Services": 0.55, "Financials": 0.55, "Banks": 0.55,
    "Energy": 0.45, "Industrials": 0.40, "Consumer Cyclical": 0.40,
    "Consumer Defensive": 0.35, "Technology": 0.35, "Healthcare": 0.35,
    "Communication Services": 0.40, "Utilities": 0.40,
    "Real Estate": 0.50, "Basic Materials": 0.45, "default": 0.40,
}

def get_lgd(sector: str) -> float:
    for key, val in SECTOR_LGD.items():
        if key.lower() in sector.lower() or sector.lower() in key.lower():
            return val
    return SECTOR_LGD["default"]

# ─── Debt extraction ──────────────────────────────────────────────────────────
SHORT_KEYS = [
    "Current Debt", "Short Term Debt", "CurrentDebt",
    "Short Long Term Debt", "ShortTermDebt",
    "Current Debt And Capital Lease Obligation",
]
LONG_KEYS = [
    "Long Term Debt", "LongTermDebt",
    "Long Term Debt And Capital Lease Obligation", "Long-Term Debt",
]

def _from_sheet(sheet) -> float:
    if sheet is None or sheet.empty:
        return 0.0
    short, long_ = 0.0, 0.0
    for idx in sheet.index:
        idx_str = str(idx).strip()
        try:
            val = float(sheet.loc[idx].iloc[0])
            if np.isnan(val):
                continue
        except (TypeError, ValueError):
            continue
        if any(k.lower() in idx_str.lower() for k in SHORT_KEYS):
            short = max(short, val)
        if any(k.lower() in idx_str.lower() for k in LONG_KEYS):
            long_ = max(long_, val)
    return short + long_

def get_total_debt(t: yf.Ticker, info: dict) -> float:
    for fn in [lambda: t.quarterly_balance_sheet, lambda: t.balance_sheet]:
        try:
            debt = _from_sheet(fn())
            if debt > 0:
                return debt
        except Exception:
            pass
    return float(info.get("totalDebt") or 0)

# ─── Fetch one ticker ─────────────────────────────────────────────────────────
def fetch_one(ticker: str) -> dict | None:
    logger.info("Fetching %-6s ...", ticker)
    for attempt in range(1, 4):
        try:
            t    = yf.Ticker(ticker)
            info = t.info or {}

            if not info.get("marketCap"):
                logger.warning("  %s: empty info (attempt %d)", ticker, attempt)
                time.sleep(attempt * 5)
                continue

            company_name = info.get("longName") or info.get("shortName") or ticker
            sector       = info.get("sector") or "Unknown"
            market_cap   = float(info.get("marketCap") or 0)
            total_debt   = get_total_debt(t, info)

            hist = t.history(period="1y", auto_adjust=True)
            if hist.empty or len(hist) < 20:
                logger.warning("  %s: insufficient price history (%d rows)", ticker, len(hist))
                time.sleep(attempt * 5)
                continue

            closes     = hist["Close"].dropna().values
            log_ret    = np.diff(np.log(closes))
            equity_vol = float(np.std(log_ret, ddof=1) * np.sqrt(252))
            lgd        = get_lgd(sector)
            today      = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            logger.info(
                "  %-6s  cap=$%7.1fB  debt=$%6.1fB  vol=%5.1f%%  %s",
                ticker, market_cap/1e9, total_debt/1e9, equity_vol*100, sector,
            )
            return {
                "ticker":            ticker,
                "company_name":      company_name,
                "sector":            sector,
                "market_cap":        market_cap,
                "total_debt":        total_debt,
                "equity_volatility": round(equity_vol, 6),
                "lgd":               lgd,
                "last_updated":      today,
                "data_source":       "yfinance",
            }

        except Exception as e:
            logger.warning("  %s attempt %d error: %s", ticker, attempt, e)
            time.sleep(attempt * 5)

    logger.error("  FAILED: %s", ticker)
    return None

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 60)
    logger.info("Credit Risk Engine — Market Data Update")
    logger.info("Tickers: %d  |  Output: %s", len(TICKERS), OUTPUT_PATH)
    logger.info("Estimated time: ~%d minutes", (len(TICKERS) * 4) // 60)
    logger.info("=" * 60)

    # Load existing CSV as fallback for failed tickers
    existing: dict[str, dict] = {}
    if OUTPUT_PATH.exists():
        try:
            df_old = pd.read_csv(OUTPUT_PATH)
            for _, row in df_old.iterrows():
                existing[row["ticker"]] = row.to_dict()
            logger.info("Loaded %d existing rows as fallback", len(existing))
        except Exception as e:
            logger.warning("Could not load existing CSV: %s", e)

    rows, failed = [], []

    for i, ticker in enumerate(TICKERS, 1):
        logger.info("[%3d/%d]", i, len(TICKERS))
        result = fetch_one(ticker)

        if result:
            rows.append(result)
        elif ticker in existing:
            old = existing[ticker].copy()
            old["data_source"] = f"cached — fetch failed {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
            rows.append(old)
            logger.info("  %s: using cached data", ticker)
        else:
            failed.append(ticker)

        time.sleep(3)  # gentle pacing between tickers

    # Write CSV
    df   = pd.DataFrame(rows)
    cols = [
        "ticker", "company_name", "sector",
        "market_cap", "total_debt", "equity_volatility",
        "lgd", "last_updated", "data_source",
    ]
    df = df[[c for c in cols if c in df.columns]]
    df.to_csv(OUTPUT_PATH, index=False)

    logger.info("=" * 60)
    logger.info("Complete: %d rows written to %s", len(df), OUTPUT_PATH)
    if failed:
        logger.warning("Failed tickers (no fallback data): %s", failed)
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
