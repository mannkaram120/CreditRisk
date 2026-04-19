# 🚀 Credit Risk Engine - Local Setup Guide

## Quick Start (5 minutes)

### Step 1: Navigate to Backend Directory
```bash
cd "D:\Projects (Finance)\Credit Risk Engine\backend"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Start the Server
```bash
uvicorn main:app --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Step 4: Test It Works
Open a new terminal and run:
```bash
python -c "
import httpx
resp = httpx.get('http://127.0.0.1:8000/health')
print(f'Status: {resp.status_code}')
print(f'Response: {resp.json()}')
"
```

Expected output:
```
Status: 200
Response: {'status': 'ok', 'version': '1.0.0'}
```

---

## Detailed Setup Instructions

### Prerequisites
- Python 3.9+ installed
- pip package manager
- Internet connection (for downloading dependencies and live market data)

### Installation Steps

#### 1. Clone or Navigate to Project
```bash
cd "D:\Projects (Finance)\Credit Risk Engine"
```

#### 2. Navigate to Backend
```bash
cd backend
```

#### 3. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

#### 4. Install Requirements
```bash
pip install -r requirements.txt
```

This installs:
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **numpy** - Numerical computing
- **scipy** - Scientific computing
- **pandas** - Data analysis
- **yfinance** - Live market data
- **httpx** - HTTP client
- **python-dotenv** - Environment variables

#### 5. (Optional) Configure Environment
If you have API keys for additional data providers, create a `.env` file:
```bash
cp .env.example .env
# Edit .env if needed
```

---

## Running the Server

### Basic Start
```bash
uvicorn main:app --port 8000
```

### With Auto-Reload (Development)
```bash
uvicorn main:app --reload --port 8000
```

### On Specific Host
```bash
uvicorn main:app --host 0.0.0.0 --port 8000  # Listen on all interfaces
```

### Full Options
```bash
uvicorn main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload \
  --log-level info
```

---

## Testing the API

### Health Check
```bash
curl http://127.0.0.1:8000/health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### Merton Analysis (Single Ticker)
```bash
curl http://127.0.0.1:8000/merton/AAPL
```

Response (example):
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "market_cap": 3828515864576.0,
  "total_debt": 90509000000.0,
  "equity_volatility": 0.237,
  "asset_value": 3918865000000.0,
  "asset_volatility": 0.022,
  "distance_to_default": 16.33,
  "probability_of_default": 3.1193e-60,
  "risk_label": "Investment Grade (AAA)",
  "lgd": 0.45,
  "sector": "Technology"
}
```

### Portfolio Preset
```bash
curl http://127.0.0.1:8000/portfolio/preset/ig
```

Available presets:
- **ig** - Investment Grade (AAPL, MSFT, JPM, JNJ, PG)
- **hy** - High Yield (F, M, CCL, AAL, AMC)
- **mixed** - Mixed Portfolio (6 companies)
- **crisis** - Financial Crisis (C, BAC, GS, MS, WFC)

---

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Class
```bash
pytest tests/test_engine.py::TestMertonSolver -v
```

### Run with Coverage
```bash
pytest tests/ --cov=services --cov=models
```

Expected: **18 tests passing**

---

## API Endpoints Reference

### Merton Model
```
GET /merton/{ticker}
```
Returns: Merton structural model analysis with PD and DD

### Portfolio Presets
```
GET /portfolio/preset/{name}
```
Returns: Preset portfolio definition

### Portfolio Analysis
```
POST /portfolio/analyze
Request body:
{
  "companies": [
    {"ticker": "AAPL", "notional": 10000000},
    {"ticker": "MSFT", "notional": 10000000}
  ],
  "rho": 0.5,
  "n_sim": 10000
}
```
Returns: Vasicek portfolio analysis with loss distribution

### Tranche Pricing
```
POST /tranche/price
```
Returns: Securitization tranche pricing

### Stress Testing
```
POST /stress/shock
```
Returns: Portfolio stress test results

---

## Common Issues & Solutions

### Port Already in Use
**Error**: `[Errno 10048] only one usage of each socket address`

**Solution**:
```bash
# Kill all Python processes
Get-Process python | Stop-Process -Force

# Wait 2 seconds
Start-Sleep -Seconds 2

# Restart server
uvicorn main:app --port 8000
```

Or use a different port:
```bash
uvicorn main:app --port 8001
```

### yfinance Session Error
**Error**: `"Yahoo API requires curl_cffi session not <class 'requests.sessions.Session'>"`

**Solution**:
```bash
# 1. Clear Python cache
Remove-Item -Recurse __pycache__* .pytest_cache* -Force

# 2. Kill all Python processes
Get-Process python | ForEach-Object { Stop-Process -Id $_.Id -Force }

# 3. Restart server
uvicorn main:app --port 8000
```

### Slow Initial Request
**Note**: First request to an endpoint may take 5-8 seconds because it's fetching live market data from yfinance. Subsequent requests are cached for 15 minutes.

### Import Errors
**Solution**: Make sure you're in the correct directory and requirements are installed:
```bash
cd backend
pip install -r requirements.txt
```

---

## Directory Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── .env                    # Configuration (local)
├── .env.example           # Configuration template
│
├── models/
│   └── schemas.py         # Pydantic models
│
├── services/
│   ├── data_ingestion.py  # Market data fetching (yfinance)
│   ├── merton.py          # Merton structural model
│   ├── vasicek.py         # Vasicek simulation
│   └── portfolio_snapshot.py  # Portfolio caching
│
├── routers/
│   ├── merton.py          # /merton endpoint
│   ├── portfolio.py        # /portfolio endpoints
│   ├── tranche.py         # /tranche endpoint
│   └── stress.py          # /stress endpoint
│
└── tests/
    └── test_engine.py     # Unit tests (18 tests)
```

---

## Performance Tips

### 1. Use Caching
- First request to a ticker: 5-8 seconds (live fetch)
- Cached requests: <100ms
- Cache duration: 15 minutes

### 2. Batch Multiple Tickers
Portfolio endpoints fetch multiple tickers in parallel, which is faster than individual calls.

### 3. Run Tests First
Tests validate all models without network calls and complete in <1 second:
```bash
pytest tests/test_engine.py -v
```

---

## Frontend Integration

If you have a frontend (React, Vue, Angular):

1. **Enable CORS** - Already configured in `main.py`
2. **Base URL** - `http://127.0.0.1:8000`
3. **Example Fetch**:
```javascript
const response = await fetch('http://127.0.0.1:8000/merton/AAPL');
const data = await response.json();
console.log(data);
```

---

## Development Workflow

### 1. Start Server with Auto-Reload
```bash
uvicorn main:app --reload --port 8000
```

### 2. Make Code Changes
Edit files in `services/`, `models/`, or `routers/`

### 3. Server Automatically Restarts
Watch for messages like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Uvicorn reloaded
```

### 4. Test Changes
```bash
curl http://127.0.0.1:8000/merton/AAPL
```

### 5. Run Tests
```bash
pytest tests/ -v
```

---

## Useful Commands Cheat Sheet

```bash
# Navigate to backend
cd "D:\Projects (Finance)\Credit Risk Engine\backend"

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --port 8000

# Start with auto-reload (development)
uvicorn main:app --reload --port 8000

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_engine.py::TestMertonSolver::test_zero_debt_returns_zero_pd -v

# Check API health
curl http://127.0.0.1:8000/health

# Test a ticker
curl http://127.0.0.1:8000/merton/AAPL

# Test portfolio preset
curl http://127.0.0.1:8000/portfolio/preset/ig

# Clear Python cache
Remove-Item -Recurse __pycache__* .pytest_cache* -Force

# Kill all Python processes
Get-Process python | ForEach-Object { Stop-Process -Id $_.Id -Force }
```

---

## Next Steps

1. ✅ Start the server: `uvicorn main:app --port 8000`
2. ✅ Test endpoints: `curl http://127.0.0.1:8000/health`
3. ✅ Run tests: `pytest tests/test_engine.py -v`
4. ✅ Integrate with frontend
5. ✅ Deploy to production

---

**Need Help?**
- Check server logs for error messages
- Run `pytest tests/ -v` to verify all models work
- Ensure internet connection for yfinance data
- Clear cache if you encounter issues: `Remove-Item -Recurse __pycache__* -Force`

**Happy coding! 🎉**
