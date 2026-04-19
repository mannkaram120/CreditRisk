"""
Router: /stress/run
────────────────────
POST /stress/run

Runs two Monte Carlo scenarios side-by-side:
  1. Base case (current rho, current PDs)
  2. Stressed case (higher rho, PDs multiplied by pd_multiplier)

Returns a comparison table showing deltas for EL, Credit VaR, ES,
and optionally per-tranche losses.

PRD reference: Section 5.5
"""

from fastapi import APIRouter, HTTPException
from services.portfolio_snapshot import build_company, get_portfolio_snapshot
from services.vasicek import (
    Company, run_vasicek_simulation,
    compute_tranche_losses,
)
from models.schemas import (
    StressRequest, StressResponse, StressScenario, TrancheResult
)
import numpy as np
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

_TRANCHE_LABELS = ["Equity", "Mezzanine", "Senior"]


@router.post("/run", response_model=StressResponse)
async def run_stress_test(req: StressRequest):
    """
    Run base vs. stressed scenario comparison.

    Stress shocks:
    - **Correlation shock**: rho increases to stressed_rho
    - **PD shock**: all implied PDs multiplied by pd_multiplier (capped at 0.99)
    """
    try:
        snapshots = get_portfolio_snapshot(req.companies)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    base_companies: list[Company] = [
        build_company(snapshot, request_company.notional)
        for request_company, snapshot in zip(req.companies, snapshots)
    ]

    # Stressed companies: shock PD, clamp at 0.99
    stressed_companies = [
        Company(
            ticker=c.ticker,
            pd=min(c.pd * req.pd_multiplier, 0.99),
            lgd=c.lgd,
            notional=c.notional,
        )
        for c in base_companies
    ]

    # Run both scenarios
    base_sim = run_vasicek_simulation(
        companies=base_companies,
        rho=req.base_rho,
        n_sim=req.n_sim,
        confidence=req.confidence,
    )

    stressed_sim = run_vasicek_simulation(
        companies=stressed_companies,
        rho=req.stressed_rho,
        n_sim=req.n_sim,
        confidence=req.confidence,
    )

    # Optionally compute tranche losses for both scenarios
    def _tranche_results(sim, companies_list) -> list[TrancheResult] | None:
        if not req.tranches:
            return None
        specs = [
            (t.attachment, t.detachment, _TRANCHE_LABELS[i] if i < 3 else f"Tranche {i+1}")
            for i, t in enumerate(req.tranches)
        ]
        raw = compute_tranche_losses(sim.losses, sim.total_notional, specs)
        return [
            TrancheResult(
                label=t.label,
                attachment=t.attachment,
                detachment=t.detachment,
                expected_loss_usd=t.expected_loss_usd,
                expected_loss_pct=t.expected_loss_pct,
                tranche_notional=t.tranche_notional,
            )
            for t in raw
        ]

    base_tranches     = _tranche_results(base_sim,     base_companies)
    stressed_tranches = _tranche_results(stressed_sim, stressed_companies)

    # Compute deltas (avoid div-by-zero)
    def _pct_change(base: float, stressed: float) -> float:
        if abs(base) < 1e-6:
            return 0.0
        return (stressed - base) / abs(base) * 100

    return StressResponse(
        base=StressScenario(
            label="Base",
            rho=req.base_rho,
            expected_loss=base_sim.expected_loss,
            unexpected_loss=base_sim.unexpected_loss,
            credit_var=base_sim.credit_var,
            expected_shortfall=base_sim.expected_shortfall,
            tranche_results=base_tranches,
        ),
        stressed=StressScenario(
            label="Stressed",
            rho=req.stressed_rho,
            expected_loss=stressed_sim.expected_loss,
            unexpected_loss=stressed_sim.unexpected_loss,
            credit_var=stressed_sim.credit_var,
            expected_shortfall=stressed_sim.expected_shortfall,
            tranche_results=stressed_tranches,
        ),
        el_delta_pct=_pct_change(base_sim.expected_loss, stressed_sim.expected_loss),
        var_delta_pct=_pct_change(base_sim.credit_var, stressed_sim.credit_var),
        es_delta_pct=_pct_change(base_sim.expected_shortfall, stressed_sim.expected_shortfall),
    )
