"""
Router: /tranche/price
───────────────────────
POST /tranche/price

Runs Monte Carlo, then applies CDO tranche attachment/detachment
logic to compute expected loss per tranche.

PRD reference: Section 3.3.4, 3.3.5
"""

from fastapi import APIRouter, HTTPException
from services.portfolio_snapshot import build_company, get_portfolio_snapshot
from services.vasicek import (
    Company, run_vasicek_simulation,
    compute_tranche_losses, sample_loss_distribution,
)
from models.schemas import TrancheRequest, TrancheResponse, TrancheResult
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

_TRANCHE_LABELS = ["Equity", "Mezzanine", "Senior", "Super Senior",
                   "Tranche 5", "Tranche 6", "Tranche 7", "Tranche 8"]


@router.post("/price", response_model=TrancheResponse)
async def price_tranches(req: TrancheRequest):
    """
    Price CDO tranches using Gaussian Copula / Vasicek Monte Carlo.

    Computes expected loss per tranche as both USD and % of tranche notional.
    """
    try:
        snapshots = get_portfolio_snapshot(req.companies)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    companies: list[Company] = [
        build_company(snapshot, request_company.notional)
        for request_company, snapshot in zip(req.companies, snapshots)
    ]

    # Run simulation
    sim = run_vasicek_simulation(
        companies=companies,
        rho=req.rho,
        n_sim=req.n_sim,
        confidence=0.99,
    )

    # Build tranche spec with auto-labels
    tranche_specs = [
        (t.attachment, t.detachment, _TRANCHE_LABELS[i] if i < len(_TRANCHE_LABELS) else f"Tranche {i+1}")
        for i, t in enumerate(req.tranches)
    ]

    tranche_losses = compute_tranche_losses(
        losses=sim.losses,
        total_notional=sim.total_notional,
        tranches=tranche_specs,
    )

    return TrancheResponse(
        tranches=[
            TrancheResult(
                label=t.label,
                attachment=t.attachment,
                detachment=t.detachment,
                expected_loss_usd=t.expected_loss_usd,
                expected_loss_pct=t.expected_loss_pct,
                tranche_notional=t.tranche_notional,
            )
            for t in tranche_losses
        ],
        total_notional=sim.total_notional,
        loss_distribution=sample_loss_distribution(sim.losses, n_points=1000),
    )
