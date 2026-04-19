"""
Unit tests for Credit Risk Engine backend.

Run with: pytest tests/ -v

Tests:
  1. Merton solver — known analytical check
  2. Vasicek simulation — EL convergence to analytical value
  3. Tranche loss — attachment/detachment logic
  4. Basel II IRB — formula validation
"""

import numpy as np
import pytest
from scipy.stats import norm

from services.merton import solve_merton, compute_equity_volatility, get_lgd, dd_to_label
from services.vasicek import (
    Company, run_vasicek_simulation,
    compute_tranche_losses, basel_irb_capital,
    validate_simulation_vs_irb,
)


# ─── Merton tests ─────────────────────────────────────────────────────────────

class TestMertonSolver:

    def test_zero_debt_returns_zero_pd(self):
        result = solve_merton(
            equity_value=1_000_000_000,
            equity_volatility=0.25,
            total_debt=0,
        )
        assert result["probability_of_default"] == 0.0
        assert result["distance_to_default"] == 10.0

    def test_high_leverage_yields_high_pd(self):
        """Firm with debt >> equity should have high PD."""
        result = solve_merton(
            equity_value=100_000_000,   # $100M market cap
            equity_volatility=0.80,     # high vol distressed firm
            total_debt=900_000_000,     # $900M debt
        )
        assert result["probability_of_default"] > 0.10  # >10% PD
        assert result["distance_to_default"] < 2.0

    def test_large_safe_firm_has_low_pd(self):
        """Apple-like firm: huge market cap, moderate debt, low vol."""
        result = solve_merton(
            equity_value=3_000_000_000_000,  # $3T market cap
            equity_volatility=0.22,
            total_debt=120_000_000_000,      # $120B debt
        )
        assert result["probability_of_default"] < 0.01  # < 1% PD
        assert result["distance_to_default"] > 3.0

    def test_pd_is_bounded(self):
        result = solve_merton(
            equity_value=500_000_000,
            equity_volatility=0.35,
            total_debt=200_000_000,
        )
        assert 0.0 <= result["probability_of_default"] <= 1.0

    def test_equity_volatility_from_prices(self):
        # Simulate flat prices — vol should be 0
        prices = [100.0] * 252
        vol = compute_equity_volatility(prices)
        assert vol == pytest.approx(0.0, abs=1e-10)

    def test_equity_volatility_insufficient_data(self):
        with pytest.raises(ValueError):
            compute_equity_volatility([100.0] * 10)

    def test_lgd_sector_lookup(self):
        assert get_lgd("Technology") == pytest.approx(0.35)
        assert get_lgd("Energy") == pytest.approx(0.45)
        assert get_lgd("Financials") == pytest.approx(0.55)
        assert get_lgd("Unknown Sector XYZ") == pytest.approx(0.40)  # default

    def test_dd_labels(self):
        assert dd_to_label(4.0) == "Safe"
        assert dd_to_label(2.0) == "Watch"
        assert dd_to_label(0.5) == "Distressed"


# ─── Vasicek simulation tests ─────────────────────────────────────────────────

class TestVasicekSimulation:

    def _simple_portfolio(self, pd=0.02, n=5):
        return [
            Company(ticker=f"CO{i}", pd=pd, lgd=0.40, notional=10_000_000)
            for i in range(n)
        ]

    def test_el_close_to_analytical(self):
        """
        Analytical EL = sum(PD_i * LGD_i * Notional_i).
        Monte Carlo EL should converge within 5% at 50k sims.
        """
        companies = self._simple_portfolio(pd=0.05, n=5)
        analytical_el = sum(c.pd * c.lgd * c.notional for c in companies)

        sim = run_vasicek_simulation(
            companies=companies, rho=0.2, n_sim=50_000, confidence=0.99, seed=42
        )
        error_pct = abs(sim.expected_loss - analytical_el) / analytical_el * 100
        assert error_pct < 5.0, f"EL error {error_pct:.2f}% exceeds 5% tolerance"

    def test_higher_rho_increases_var(self):
        """Higher correlation should widen the tail — Credit VaR increases."""
        companies = self._simple_portfolio()

        low_rho = run_vasicek_simulation(companies, rho=0.05, n_sim=30_000, confidence=0.99, seed=0)
        high_rho = run_vasicek_simulation(companies, rho=0.60, n_sim=30_000, confidence=0.99, seed=0)

        assert high_rho.credit_var >= low_rho.credit_var

    def test_zero_pd_yields_zero_losses(self):
        companies = [Company("A", pd=0.0, lgd=0.40, notional=10_000_000)]
        sim = run_vasicek_simulation(companies, rho=0.2, n_sim=10_000, confidence=0.99, seed=1)
        assert sim.expected_loss == pytest.approx(0.0, abs=1.0)

    def test_loss_shape(self):
        companies = self._simple_portfolio()
        sim = run_vasicek_simulation(companies, rho=0.2, n_sim=10_000, confidence=0.99, seed=2)
        assert len(sim.losses) == 10_000
        assert np.all(sim.losses >= 0)

    def test_es_geq_var(self):
        """Expected Shortfall must be >= Credit VaR by definition."""
        companies = self._simple_portfolio(pd=0.10)
        sim = run_vasicek_simulation(companies, rho=0.3, n_sim=20_000, confidence=0.99, seed=3)
        assert sim.expected_shortfall >= sim.credit_var - 1  # small tolerance


# ─── Tranche tests ────────────────────────────────────────────────────────────

class TestTrancheLoss:

    def test_equity_fully_absorbs_small_losses(self):
        """
        If all losses < equity detachment, equity tranche takes all loss,
        mezzanine and senior take 0.
        """
        total_notional = 100_000_000
        # 100 scenarios all with $1M loss (< $3M equity tranche)
        losses = np.full(100, 1_000_000.0)

        tranches = [
            (0.00, 0.03, "Equity"),
            (0.03, 0.07, "Mezzanine"),
            (0.07, 1.00, "Senior"),
        ]
        results = compute_tranche_losses(losses, total_notional, tranches)

        equity = results[0]
        mezz   = results[1]
        senior = results[2]

        assert equity.expected_loss_usd == pytest.approx(1_000_000.0, rel=1e-6)
        assert mezz.expected_loss_usd   == pytest.approx(0.0, abs=1.0)
        assert senior.expected_loss_usd == pytest.approx(0.0, abs=1.0)

    def test_tranche_loss_example_from_prd(self):
        """
        PRD Section 3.3.5 worked example:
        100M notional, single scenario with 5M loss.
        Equity (0-3%): fully wiped = 3M
        Mezz  (3-7%): partially hit = 2M
        Senior(7-100%): untouched = 0
        """
        total_notional = 100_000_000
        losses = np.array([5_000_000.0])

        tranches = [
            (0.00, 0.03, "Equity"),
            (0.03, 0.07, "Mezzanine"),
            (0.07, 1.00, "Senior"),
        ]
        results = compute_tranche_losses(losses, total_notional, tranches)

        assert results[0].expected_loss_usd == pytest.approx(3_000_000.0)
        assert results[1].expected_loss_usd == pytest.approx(2_000_000.0)
        assert results[2].expected_loss_usd == pytest.approx(0.0, abs=1.0)


# ─── Basel II IRB validation ──────────────────────────────────────────────────

class TestBaselIRB:

    def test_irb_formula_investment_grade(self):
        """Basel IRB at PD=0.5%, LGD=40%, rho=0.20 should give ~2-5% capital."""
        K = basel_irb_capital(pd=0.005, lgd=0.40, rho=0.20)
        assert 0.01 < K < 0.08, f"Expected K in [1%, 8%], got {K:.4f}"

    def test_irb_increases_with_pd(self):
        """Higher PD → more capital required."""
        K_low  = basel_irb_capital(pd=0.01, lgd=0.40, rho=0.20)
        K_high = basel_irb_capital(pd=0.10, lgd=0.40, rho=0.20)
        assert K_high > K_low

    def test_irb_vs_simulation_convergence(self):
        """
        Basel IRB is an asymptotic single-factor formula, so validate it on a
        reasonably granular homogeneous portfolio rather than a single binary
        obligor loss.
        """
        companies = [
            Company(f"TEST{i}", pd=0.02, lgd=0.40, notional=1_000_000)
            for i in range(100)
        ]
        sim = run_vasicek_simulation(companies, rho=0.20, n_sim=50_000, confidence=0.999, seed=99)
        validation = validate_simulation_vs_irb(companies, sim, rho=0.20)
        assert validation["error_pct"] < 25.0, (
            f"Simulation vs IRB error {validation['error_pct']:.1f}% too large"
        )
