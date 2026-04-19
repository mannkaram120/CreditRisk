"""
Router: /portfolio
──────────────────
POST /portfolio/analyze  — run Vasicek Monte Carlo on a custom portfolio
GET  /portfolio/preset/{name} — return pre-built portfolio definition
"""

from fastapi import APIRouter, HTTPException
from services.data_ingestion import PRESETS
from services.portfolio_snapshot import (
    build_company,
    build_company_result,
    get_portfolio_snapshot,
)
from services.vasicek import (
    Company, run_vasicek_simulation, sample_loss_distribution
)
from models.schemas import (
    PortfolioRequest, PortfolioResponse, CompanyResult, PresetName
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=PortfolioResponse)
async def analyze_portfolio(req: PortfolioRequest):
    """
    Run full Vasicek Monte Carlo simulation on a custom portfolio.

    Fetches live Merton PD for each ticker, then simulates the
    portfolio loss distribution with the given correlation parameter.
    """
    company_results: list[CompanyResult] = []
    companies: list[Company] = []

    try:
        snapshots = get_portfolio_snapshot(req.companies)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    for request_company, snapshot in zip(req.companies, snapshots):
        company_results.append(build_company_result(snapshot, request_company.notional))
        companies.append(build_company(snapshot, request_company.notional))

    # Run simulation
    sim = run_vasicek_simulation(
        companies=companies,
        rho=req.rho,
        n_sim=req.n_sim,
        confidence=req.confidence,
    )

    return PortfolioResponse(
        companies=company_results,
        expected_loss=sim.expected_loss,
        unexpected_loss=sim.unexpected_loss,
        credit_var=sim.credit_var,
        expected_shortfall=sim.expected_shortfall,
        total_notional=sim.total_notional,
        rho=req.rho,
        confidence=req.confidence,
        n_sim=req.n_sim,
        loss_distribution=sample_loss_distribution(sim.losses, n_points=1000),
    )


@router.get("/preset/{name}")
async def get_preset(name: PresetName):
    """
    Return a pre-built portfolio definition by name.

    Available presets: ig, hy, mixed, crisis
    """
    preset = PRESETS.get(name.value)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found")
    return {"preset": name.value, "companies": preset}
