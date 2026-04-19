"""
Merton Structural Model (1974)
─────────────────────────────
Solves the two-equation system to extract:
  - Implied firm asset value (V)
  - Implied asset volatility (sigma_V)
  - Distance to Default (DD)
  - Probability of Default (PD = N(-DD))

Math reference:  PRD Section 3.1
"""

import numpy as np
from scipy.optimize import fsolve
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)

# Risk-free rate (US 10Y proxy, update periodically)
RISK_FREE_RATE = 0.045
TIME_HORIZON = 1.0  # 1 year

# ─── LGD lookup by GICS sector ───────────────────────────────────────────────
# Source: industry convention / PRD Section 4.3
SECTOR_LGD: dict[str, float] = {
    "Financial Services": 0.55,
    "Financials":         0.55,
    "Banks":              0.55,
    "Energy":             0.45,
    "Industrials":        0.40,
    "Consumer Cyclical":  0.40,
    "Consumer Defensive": 0.35,
    "Technology":         0.35,
    "Healthcare":         0.35,
    "Communication Services": 0.40,
    "Utilities":          0.40,
    "Real Estate":        0.50,
    "Basic Materials":    0.45,
    "default":            0.40,
}

# ─── Risk labels by Distance to Default ──────────────────────────────────────
def dd_to_label(dd: float) -> str:
    if dd > 3:
        return "Safe"
    elif dd > 1:
        return "Watch"
    else:
        return "Distressed"


# ─── Merton equation system ───────────────────────────────────────────────────

def _merton_equations(
    params: tuple[float, float],
    E: float,
    sigma_E: float,
    D: float,
    r: float,
    T: float,
) -> list[float]:
    """
    Residuals of the two Merton equations:
      1. E = V*N(d1) - D*exp(-rT)*N(d2)         [equity as call option]
      2. sigma_E * E = N(d1) * sigma_V * V       [Ito leverage relation]

    Returns [eq1_residual, eq2_residual] — fsolve drives these to 0.
    """
    V, sigma_V = params

    # Guard against degenerate values that break log/sqrt
    if V <= 0 or sigma_V <= 1e-6:
        return [1e10, 1e10]

    d1 = (np.log(V / D) + (r + 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))
    d2 = d1 - sigma_V * np.sqrt(T)

    eq1 = V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2) - E
    eq2 = norm.cdf(d1) * sigma_V * V - sigma_E * E

    return [eq1, eq2]


def solve_merton(
    equity_value: float,
    equity_volatility: float,
    total_debt: float,
    r: float = RISK_FREE_RATE,
    T: float = TIME_HORIZON,
) -> dict:
    """
    Solve the Merton system numerically via scipy fsolve.

    Parameters
    ----------
    equity_value       : Market cap in USD
    equity_volatility  : Annualized equity vol (e.g. 0.30)
    total_debt         : Face value of total debt in USD
    r                  : Risk-free rate (default: RISK_FREE_RATE)
    T                  : Time horizon in years (default: 1.0)

    Returns
    -------
    dict with keys:
        asset_value        (V)
        asset_volatility   (sigma_V)
        distance_to_default (DD)
        probability_of_default (PD)
    """
    if total_debt <= 0:
        # No debt → zero default probability
        return {
            "asset_value": equity_value,
            "asset_volatility": equity_volatility,
            "distance_to_default": 10.0,
            "probability_of_default": 0.0,
        }

    # Initial guesses: asset value ≈ equity + debt; asset vol ≈ equity vol * leverage
    leverage = equity_value / (equity_value + total_debt)
    V0 = equity_value + total_debt
    sigma_V0 = equity_volatility * leverage

    try:
        solution, info, ier, msg = fsolve(
            _merton_equations,
            x0=[V0, sigma_V0],
            args=(equity_value, equity_volatility, total_debt, r, T),
            full_output=True,
            xtol=1e-8,
            maxfev=2000,
        )

        if ier != 1:
            logger.warning("fsolve did not fully converge: %s — using best guess", msg)

        V, sigma_V = solution
        sigma_V = max(sigma_V, 1e-6)  # floor to prevent division by zero

        # Distance to Default
        dd = (np.log(V / total_debt) + (r - 0.5 * sigma_V**2) * T) / (
            sigma_V * np.sqrt(T)
        )

        # Implied Probability of Default  PD = N(-DD)
        pd = float(norm.cdf(-dd))
        pd = max(0.0, min(pd, 1.0))  # clamp [0, 1]

        return {
            "asset_value": float(V),
            "asset_volatility": float(sigma_V),
            "distance_to_default": float(dd),
            "probability_of_default": pd,
        }

    except Exception as exc:
        logger.error("Merton solver error: %s", exc)
        raise RuntimeError(f"Merton solver failed: {exc}") from exc


# ─── Annualised equity volatility from price series ──────────────────────────

def compute_equity_volatility(prices: list[float]) -> float:
    """
    Compute annualised equity volatility from a series of daily closing prices.
    Uses log returns * sqrt(252) convention.

    Parameters
    ----------
    prices : list of daily closing prices, most recent last

    Returns
    -------
    Annualized volatility as a fraction (e.g. 0.28 for 28%)
    """
    if len(prices) < 20:
        raise ValueError("Need at least 20 price observations to estimate volatility")

    prices_arr = np.array(prices, dtype=float)
    log_returns = np.diff(np.log(prices_arr))
    daily_vol = np.std(log_returns, ddof=1)
    annual_vol = daily_vol * np.sqrt(252)
    return float(annual_vol)


def get_lgd(sector: str) -> float:
    """Return Loss Given Default for a GICS sector, with fallback."""
    for key in SECTOR_LGD:
        if key.lower() in sector.lower() or sector.lower() in key.lower():
            return SECTOR_LGD[key]
    return SECTOR_LGD["default"]
