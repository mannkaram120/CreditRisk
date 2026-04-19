"""
Shared portfolio snapshot service.

Builds and caches analyzed company data so related endpoints can reuse a
single live market-data fetch / Merton analysis pass for the same portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import threading

from models.schemas import CompanyResult, PortfolioName
from services.data_ingestion import fetch_bulk_price_histories, fetch_ticker_data
from services.merton import dd_to_label, get_lgd, solve_merton
from services.vasicek import Company


@dataclass(frozen=True)
class AnalyzedTickerSnapshot:
    ticker: str
    company_name: str
    sector: str
    market_cap: float
    total_debt: float
    asset_volatility: float
    dd: float
    pd: float
    lgd: float
    risk_label: str


_SNAPSHOT_TTL_MINUTES = 10
_snapshot_cache: dict[tuple[str, ...], tuple[datetime, list[AnalyzedTickerSnapshot]]] = {}
_snapshot_lock = threading.Lock()
_snapshot_inflight: dict[tuple[str, ...], threading.Event] = {}


def _portfolio_key(companies: list[PortfolioName]) -> tuple[str, ...]:
    return tuple(company.ticker.strip().upper() for company in companies)


def _get_cached_snapshot(key: tuple[str, ...]) -> list[AnalyzedTickerSnapshot] | None:
    with _snapshot_lock:
        cached = _snapshot_cache.get(key)
        if cached is None:
            return None

        cached_at, snapshots = cached
        if datetime.utcnow() - cached_at < timedelta(minutes=_SNAPSHOT_TTL_MINUTES):
            return snapshots

        del _snapshot_cache[key]
        return None


def _set_cached_snapshot(key: tuple[str, ...], snapshots: list[AnalyzedTickerSnapshot]) -> None:
    with _snapshot_lock:
        _snapshot_cache[key] = (datetime.utcnow(), snapshots)


def _begin_snapshot_build(key: tuple[str, ...]) -> tuple[threading.Event, bool]:
    with _snapshot_lock:
        existing = _snapshot_inflight.get(key)
        if existing is not None:
            return existing, False

        event = threading.Event()
        _snapshot_inflight[key] = event
        return event, True


def _end_snapshot_build(key: tuple[str, ...], event: threading.Event) -> None:
    with _snapshot_lock:
        current = _snapshot_inflight.get(key)
        if current is event:
            del _snapshot_inflight[key]
    event.set()


def analyze_single_ticker(
    ticker: str,
    closing_prices_override: list[float] | None = None,
) -> AnalyzedTickerSnapshot:
    normalized_ticker = ticker.strip().upper()
    data = fetch_ticker_data(normalized_ticker, closing_prices_override=closing_prices_override)
    merton = solve_merton(
        equity_value=data["market_cap"],
        equity_volatility=data["equity_volatility"],
        total_debt=data["total_debt"],
    )

    sector = data["sector"]
    lgd = get_lgd(sector)
    dd = merton["distance_to_default"]

    return AnalyzedTickerSnapshot(
        ticker=normalized_ticker,
        company_name=data["company_name"],
        sector=sector,
        market_cap=data["market_cap"],
        total_debt=data["total_debt"],
        asset_volatility=merton["asset_volatility"],
        dd=dd,
        pd=merton["probability_of_default"],
        lgd=lgd,
        risk_label=dd_to_label(dd),
    )


def get_portfolio_snapshot(companies: list[PortfolioName]) -> list[AnalyzedTickerSnapshot]:
    """
    Return analyzed company snapshots for a portfolio, preserving request order.

    The snapshot is cached by ordered ticker tuple so multiple related API
    requests can reuse one live fetch pass.
    """
    key = _portfolio_key(companies)
    cached = _get_cached_snapshot(key)
    if cached is not None:
        return cached

    event, is_owner = _begin_snapshot_build(key)
    if not is_owner:
        event.wait(timeout=30)
        cached = _get_cached_snapshot(key)
        if cached is not None:
            return cached

    try:
        bulk_histories = fetch_bulk_price_histories([company.ticker for company in companies])
        snapshots = [
            analyze_single_ticker(
                company.ticker,
                closing_prices_override=bulk_histories.get(company.ticker.strip().upper()),
            )
            for company in companies
        ]
        _set_cached_snapshot(key, snapshots)
        return snapshots
    finally:
        _end_snapshot_build(key, event)


def build_company_result(snapshot: AnalyzedTickerSnapshot, notional: float) -> CompanyResult:
    return CompanyResult(
        ticker=snapshot.ticker,
        company_name=snapshot.company_name,
        pd=snapshot.pd,
        dd=snapshot.dd,
        asset_volatility=snapshot.asset_volatility,
        market_cap=snapshot.market_cap,
        total_debt=snapshot.total_debt,
        lgd=snapshot.lgd,
        notional=notional,
        risk_label=snapshot.risk_label,
        sector=snapshot.sector,
    )


def build_company(snapshot: AnalyzedTickerSnapshot, notional: float) -> Company:
    return Company(
        ticker=snapshot.ticker,
        pd=snapshot.pd,
        lgd=snapshot.lgd,
        notional=notional,
    )
