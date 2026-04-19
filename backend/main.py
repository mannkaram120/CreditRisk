"""
Credit Risk Engine - FastAPI Backend
Implements: Merton Structural Model, Vasicek One-Factor Model, Gaussian Copula
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import merton, portfolio, tranche, stress

app = FastAPI(
    title="Credit Risk Engine API",
    description="Merton, Vasicek, and Gaussian Copula credit risk models",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to karamfrm.com in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(merton.router, prefix="/merton", tags=["Merton Model"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
app.include_router(tranche.router, prefix="/tranche", tags=["Tranche Pricing"])
app.include_router(stress.router, prefix="/stress", tags=["Stress Testing"])


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
