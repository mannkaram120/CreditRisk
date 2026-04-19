# Credit Risk Engine — Backend

A production-grade credit risk computation server implementing:

- **Merton Structural Model (1974)** — implied PD from live equity data
- **Vasicek One-Factor Model** — portfolio loss distribution via Monte Carlo
- **Gaussian Copula** — CDO tranche pricing (equity / mezzanine / senior)

> Targets credit risk professionals and recruiters.  
> Mathematical reference: `CreditRiskEngine_PRD.docx`

---

## Stack

| Layer | Technology |
|---|---|
| API Framework | Python 3.11 + FastAPI |
| Math Engine | NumPy + SciPy |
| Data | yfinance (equity + balance sheet) |
| Deployment | Existing backend host (Vercel BE) |

---

## Project Structure

```
backend/
├── main.py                    # FastAPI app, CORS, router registration
├── requirements.txt
├── models/
│   └── schemas.py             # Pydantic request/response models
├── services/
│   ├── merton.py              # Merton solver, volatility, LGD lookup
│   ├── vasicek.py             # Monte Carlo simulation, tranche, IRB
│   └── data_ingestion.py      # yfinance fetcher + TTL cache + presets
├── routers/
│   ├── merton.py              # GET /merton/{ticker}
│   ├── portfolio.py           # POST /portfolio/analyze, GET /portfolio/preset/{name}
│   ├── tranche.py             # POST /tranche/price
│   └── stress.py              # POST /stress/run
└── tests/
    └── test_engine.py         # Unit tests (pytest)
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/merton/{ticker}` | GET | Merton PD, DD, asset value for a single ticker |
| `/portfolio/analyze` | POST | Vasicek Monte Carlo for custom portfolio |
| `/portfolio/preset/{name}` | GET | Pre-built portfolio (ig / hy / mixed / crisis) |
| `/tranche/price` | POST | CDO tranche expected losses |
| `/stress/run` | POST | Base vs stressed scenario comparison |
| `/health` | GET | Health check |

---

## Running Locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Swagger docs: http://localhost:8000/docs  
ReDoc: http://localhost:8000/redoc

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

Tests validate:
- Merton solver numerical accuracy
- Vasicek EL convergence to analytical value
- Tranche loss attachment/detachment logic (PRD Section 3.3.5 example)
- Basel II IRB vs Monte Carlo convergence

---

## Model Limitations (Per PRD Section 10)

- **Debt Structure**: Merton assumes single-class zero-coupon debt. We use total debt as proxy.
- **Constant Correlation**: Single rho for entire portfolio; real correlation is sector-varying.
- **Data Freshness**: yfinance balance sheet data is quarterly; may lag up to 3 months.
- **Tail Dependence**: Gaussian copula understates crisis-era default clustering. Student-t copula would improve this.
- **Hazard Rate**: Constant hazard assumed; real credit spreads have term structure.

---

## Step 1 Status (Days 1–7 of 20-day plan)

- [x] Merton solver (`services/merton.py`)
- [x] yfinance data ingestion + TTL cache (`services/data_ingestion.py`)
- [x] Vasicek Monte Carlo + vectorized simulation (`services/vasicek.py`)
- [x] Tranche loss calculation
- [x] Basel II IRB validation formula
- [x] Stress test comparison engine
- [x] All 5 FastAPI endpoints wired
- [x] Pydantic schemas for all requests/responses
- [x] Unit tests covering core math
- [ ] Frontend (Days 8–18)
- [ ] Deploy (Day 20)
