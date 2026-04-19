"""
Vasicek One-Factor Model + Gaussian Copula Monte Carlo Engine
─────────────────────────────────────────────────────────────
Implements:
  1. Vasicek Monte Carlo loss distribution simulation (PRD Section 3.2)
  2. CDO tranche loss calculation (PRD Section 3.3.4 / 3.3.5)
  3. Credit VaR and Expected Shortfall extraction (PRD Section 3.4)
  4. Basel II IRB analytical formula for validation (PRD Section 3.4.3)

Design: fully vectorized with NumPy for speed at 50k+ simulations.
"""

import numpy as np
from scipy.stats import norm
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ─── Data containers ─────────────────────────────────────────────────────────

@dataclass
class Company:
    ticker: str
    pd: float       # Probability of Default [0, 1]
    lgd: float      # Loss Given Default [0, 1]
    notional: float # USD exposure


@dataclass
class SimulationResult:
    losses: np.ndarray          # Full loss array, shape (n_sim,)
    expected_loss: float        # Mean
    unexpected_loss: float      # Std
    credit_var: float           # Percentile(losses, alpha) - EL
    expected_shortfall: float   # Mean of tail beyond VaR
    total_notional: float


@dataclass
class TrancheResult:
    label: str
    attachment: float
    detachment: float
    expected_loss_usd: float
    expected_loss_pct: float
    tranche_notional: float


# ─── Vectorized Monte Carlo ───────────────────────────────────────────────────

def run_vasicek_simulation(
    companies: list[Company],
    rho: float,
    n_sim: int,
    confidence: float,
    seed: Optional[int] = None,
) -> SimulationResult:
    """
    Run vectorized Vasicek One-Factor Monte Carlo simulation.

    Each company's asset return:
        A_i = sqrt(rho) * Z + sqrt(1-rho) * eps_i

    Company i defaults if A_i < N^(-1)(PD_i).

    Parameters
    ----------
    companies   : list of Company objects
    rho         : asset correlation (systematic factor weight)
    n_sim       : number of Monte Carlo scenarios
    confidence  : VaR confidence level (e.g. 0.99)
    seed        : optional RNG seed for reproducibility

    Returns
    -------
    SimulationResult
    """
    rng = np.random.default_rng(seed)
    n = len(companies)

    pd_array  = np.array([c.pd       for c in companies])
    lgd_array = np.array([c.lgd      for c in companies])
    not_array = np.array([c.notional for c in companies])

    # Default thresholds: K_i = N^(-1)(PD_i)
    # Floor PD away from 0/1 to avoid ±inf thresholds
    pd_clipped = np.clip(pd_array, 1e-8, 1 - 1e-8)
    thresholds = norm.ppf(pd_clipped)  # shape (n,)

    # ── Simulate ─────────────────────────────────────────────────────────────
    # Z  shape (n_sim, 1)  — systematic economic factor
    # eps shape (n_sim, n) — idiosyncratic shocks
    Z   = rng.standard_normal((n_sim, 1))
    eps = rng.standard_normal((n_sim, n))

    # Asset returns: A shape (n_sim, n)
    A = np.sqrt(rho) * Z + np.sqrt(1 - rho) * eps

    # Default indicator: 1 if A_i < K_i
    defaults = A < thresholds  # bool (n_sim, n)

    # Loss per scenario: sum of LGD_i * Notional_i for defaulted companies
    loss_given_default = lgd_array * not_array  # (n,)
    losses = defaults @ loss_given_default       # (n_sim,)

    # ── Risk metrics ─────────────────────────────────────────────────────────
    total_notional = float(np.sum(not_array))
    el = float(np.mean(losses))
    ul = float(np.std(losses, ddof=1))

    var_threshold = float(np.percentile(losses, confidence * 100))
    credit_var = var_threshold - el

    tail_losses = losses[losses > var_threshold]
    es = float(np.mean(tail_losses)) if len(tail_losses) > 0 else var_threshold

    logger.info(
        "Simulation complete: n=%d, rho=%.2f, EL=$%.0f, CVaR=$%.0f, ES=$%.0f",
        n_sim, rho, el, credit_var, es,
    )

    return SimulationResult(
        losses=losses,
        expected_loss=el,
        unexpected_loss=ul,
        credit_var=credit_var,
        expected_shortfall=es,
        total_notional=total_notional,
    )


# ─── Tranche loss calculation ─────────────────────────────────────────────────

def compute_tranche_losses(
    losses: np.ndarray,
    total_notional: float,
    tranches: list[tuple[float, float, str]],  # (attachment%, detachment%, label)
) -> list[TrancheResult]:
    """
    Compute expected tranche losses from the Monte Carlo loss array.

    Tranche Loss per scenario =
        min(portfolio_loss, D*N) - min(portfolio_loss, A*N)

    where A, D are attachment/detachment as fractions of total notional N.

    Parameters
    ----------
    losses          : (n_sim,) array of scenario losses in USD
    total_notional  : total portfolio notional in USD
    tranches        : list of (attachment_frac, detachment_frac, label)

    Returns
    -------
    list of TrancheResult
    """
    results = []
    for attachment_frac, detachment_frac, label in tranches:
        A = attachment_frac * total_notional
        D = detachment_frac * total_notional

        tranche_loss_usd = np.minimum(losses, D) - np.minimum(losses, A)
        expected_tranche_loss = float(np.mean(tranche_loss_usd))

        tranche_notional = (detachment_frac - attachment_frac) * total_notional
        expected_tranche_loss_pct = (
            expected_tranche_loss / tranche_notional if tranche_notional > 0 else 0.0
        )

        results.append(TrancheResult(
            label=label,
            attachment=attachment_frac,
            detachment=detachment_frac,
            expected_loss_usd=expected_tranche_loss,
            expected_loss_pct=expected_tranche_loss_pct,
            tranche_notional=tranche_notional,
        ))

    return results


# ─── Basel II IRB analytical formula (validation) ────────────────────────────

def basel_irb_capital(pd: float, lgd: float, rho: float, confidence: float = 0.999) -> float:
    """
    Basel II IRB analytical formula for regulatory capital (K).
    Derived directly from the Vasicek one-factor model at infinite simulations.

    K = LGD * N[ N^(-1)(PD)/sqrt(1-R) + sqrt(R/(1-R)) * N^(-1)(0.999) ] - LGD * PD

    Parameters
    ----------
    pd         : Probability of Default [0,1]
    lgd        : Loss Given Default [0,1]
    rho        : Asset correlation (R in Basel formula)
    confidence : Regulatory confidence level (default 99.9%)

    Returns
    -------
    Capital requirement K as fraction of exposure (e.g. 0.08 = 8%)

    Reference: PRD Section 3.4.3
    """
    pd = np.clip(pd, 1e-8, 1 - 1e-8)
    z_conf = norm.ppf(confidence)

    term = (norm.ppf(pd) / np.sqrt(1 - rho)) + (np.sqrt(rho / (1 - rho)) * z_conf)
    K = lgd * norm.cdf(term) - lgd * pd

    return float(K)


def validate_simulation_vs_irb(
    companies: list[Company],
    simulation_result: SimulationResult,
    rho: float,
) -> dict:
    """
    Compare Monte Carlo Credit VaR at 99.9% to Basel II IRB formula.
    Used as a model validation check (PRD Section 9 / Interview Defence).

    Returns dict with analytical_capital, simulated_capital, error_pct.
    """
    total_notional = simulation_result.total_notional
    analytical_capital = sum(
        basel_irb_capital(c.pd, c.lgd, rho) * c.notional
        for c in companies
    )

    # Re-extract 99.9% VaR from simulation for comparison
    var_999 = float(np.percentile(simulation_result.losses, 99.9))
    simulated_capital = var_999 - simulation_result.expected_loss

    error_pct = abs(analytical_capital - simulated_capital) / max(analytical_capital, 1) * 100

    return {
        "analytical_capital_usd": analytical_capital,
        "simulated_capital_usd": simulated_capital,
        "error_pct": error_pct,
    }


# ─── Utility: thin the loss array for frontend transmission ──────────────────

def sample_loss_distribution(losses: np.ndarray, n_points: int = 1000) -> list[float]:
    """
    Uniformly sample n_points from the sorted loss distribution.
    Used to keep API payload size manageable while preserving shape.
    """
    sorted_losses = np.sort(losses)
    indices = np.linspace(0, len(sorted_losses) - 1, n_points, dtype=int)
    return sorted_losses[indices].tolist()
