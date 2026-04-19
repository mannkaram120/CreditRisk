"""
Pydantic schemas for request validation and response serialization.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum


# ─────────────────────────────────────────────
# Merton Model
# ─────────────────────────────────────────────

class MertonResponse(BaseModel):
    ticker: str
    company_name: str
    market_cap: float          # USD
    total_debt: float          # USD
    equity_volatility: float   # annualized, e.g. 0.25 = 25%
    asset_value: float         # implied V from Merton solver
    asset_volatility: float    # implied sigma_V from Merton solver
    distance_to_default: float # DD = (ln(V/D) + (r - 0.5*sigma_V^2)*T) / (sigma_V*sqrt(T))
    probability_of_default: float  # PD = N(-DD), as a fraction
    risk_label: str            # "Safe", "Watch", or "Distressed"
    lgd: float                 # Loss Given Default, sector-based lookup
    sector: str


# ─────────────────────────────────────────────
# Portfolio Analysis
# ─────────────────────────────────────────────

class PortfolioName(BaseModel):
    ticker: str
    notional: float = Field(gt=0, description="Notional exposure in USD")


class PortfolioRequest(BaseModel):
    companies: List[PortfolioName] = Field(min_length=1, max_length=20)
    rho: float = Field(default=0.2, ge=0.0, le=1.0, description="Asset correlation")
    confidence: float = Field(default=0.99, description="VaR confidence level")
    n_sim: int = Field(default=50_000, ge=10_000, le=200_000)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        allowed = {0.90, 0.95, 0.99, 0.999}
        if v not in allowed:
            raise ValueError(f"confidence must be one of {sorted(allowed)}")
        return v


class CompanyResult(BaseModel):
    ticker: str
    company_name: str
    pd: float
    dd: float
    asset_volatility: float
    market_cap: float
    total_debt: float
    lgd: float
    notional: float
    risk_label: str
    sector: str


class PortfolioResponse(BaseModel):
    companies: List[CompanyResult]
    expected_loss: float          # EL = mean of loss distribution
    unexpected_loss: float        # UL = std of loss distribution
    credit_var: float             # CVaR at requested confidence level
    expected_shortfall: float     # ES = mean of tail beyond VaR threshold
    total_notional: float
    rho: float
    confidence: float
    n_sim: int
    loss_distribution: List[float]   # histogram-ready array (sampled to 1000 pts)


# ─────────────────────────────────────────────
# Tranche Pricing
# ─────────────────────────────────────────────

class TranchePoint(BaseModel):
    attachment: float = Field(ge=0.0, lt=1.0)
    detachment: float = Field(gt=0.0, le=1.0)

    @field_validator("detachment")
    @classmethod
    def detach_gt_attach(cls, v, info):
        if "attachment" in info.data and v <= info.data["attachment"]:
            raise ValueError("detachment must be greater than attachment")
        return v


class TrancheRequest(BaseModel):
    companies: List[PortfolioName]
    rho: float = Field(default=0.2, ge=0.0, le=1.0)
    n_sim: int = Field(default=50_000, ge=10_000, le=200_000)
    tranches: List[TranchePoint] = Field(
        default=[
            TranchePoint(attachment=0.0, detachment=0.03),  # Equity
            TranchePoint(attachment=0.03, detachment=0.07), # Mezzanine
            TranchePoint(attachment=0.07, detachment=1.0),  # Senior
        ]
    )


class TrancheResult(BaseModel):
    label: str                     # "Equity", "Mezzanine", "Senior"
    attachment: float
    detachment: float
    expected_loss_usd: float
    expected_loss_pct: float       # as % of tranche notional
    tranche_notional: float


class TrancheResponse(BaseModel):
    tranches: List[TrancheResult]
    total_notional: float
    loss_distribution: List[float]


# ─────────────────────────────────────────────
# Stress Testing
# ─────────────────────────────────────────────

class StressRequest(BaseModel):
    companies: List[PortfolioName]
    base_rho: float = Field(default=0.2, ge=0.0, le=1.0)
    stressed_rho: float = Field(default=0.5, ge=0.0, le=1.0)
    pd_multiplier: float = Field(default=2.0, ge=1.0, le=5.0)
    confidence: float = Field(default=0.99)
    n_sim: int = Field(default=50_000, ge=10_000, le=200_000)
    tranches: Optional[List[TranchePoint]] = None


class StressScenario(BaseModel):
    label: str                     # "Base" or "Stressed"
    rho: float
    expected_loss: float
    unexpected_loss: float
    credit_var: float
    expected_shortfall: float
    tranche_results: Optional[List[TrancheResult]] = None


class StressResponse(BaseModel):
    base: StressScenario
    stressed: StressScenario
    el_delta_pct: float
    var_delta_pct: float
    es_delta_pct: float


# ─────────────────────────────────────────────
# Preset portfolios
# ─────────────────────────────────────────────

class PresetName(str, Enum):
    ig = "ig"
    hy = "hy"
    mixed = "mixed"
    crisis = "crisis"
