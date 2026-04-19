# Excel-Based Data Cache Architecture

## Brilliant Idea! 💡

You're essentially creating a **local data cache** that updates daily.

### Benefits:
✅ **Zero API calls** during normal operation (just read Excel)
✅ **30 API calls/day max** (one batch update at 3 AM)
✅ **99.9% reduction in requests**
✅ **No rate limiting issues**
✅ **Offline-capable** (works without internet)
✅ **Deterministic** (same data = same results)
✅ **Testable** (use test data in Excel)
✅ **Historical audit trail** (old versions saved)

### How It Works:

```
Architecture:
───────────────────────────────────────────

1. Daily Scheduler (3 AM every day)
   └─ Runs: "python update_data.py"
      ├─ Fetches from Finnhub (30 requests)
      └─ Writes to portfolio_data.xlsx

2. Backend (REST API)
   └─ Reads from portfolio_data.xlsx
      ├─ Zero API calls
      └─ Instant response

3. User
   └─ Uses backend normally
      ├─ All data cached in Excel
      └─ No rate limits, fast responses
```

---

## Architecture Overview

### **File Structure**

```
backend/
├── data/
│   ├── portfolio_data.xlsx         ← Main cache file
│   ├── portfolio_data_backup.xlsx  ← Backup (auto-rotate daily)
│   └── portfolio_data_archive/
│       ├── 2025-01-08.xlsx
│       ├── 2025-01-09.xlsx
│       └── 2025-01-10.xlsx         ← Historical versions
│
├── update_data.py                  ← Daily update script
├── services/
│   ├── data_ingestion.py           ← Updated to read Excel
│   └── excel_cache.py              ← New: Excel operations
│
└── scheduler_config.json           ← Windows Task Scheduler config
```

### **Excel Structure**

```
portfolio_data.xlsx
├─ Sheet: "Companies"
│  ├─ A: Ticker (AAPL, MSFT, JPM, ...)
│  ├─ B: Company Name
│  ├─ C: Sector
│  ├─ D: Market Cap (USD)
│  ├─ E: Total Debt (USD)
│  ├─ F: Stock Price
│  ├─ G-AG: Daily Prices (Last 365 days)
│  ├─ AH: Equity Volatility
│  └─ AI: Last Updated
│
├─ Sheet: "Price History"
│  └─ Date vs Ticker prices (wide format)
│
└─ Sheet: "Metadata"
   ├─ Last Update Time
   ├─ Data Quality
   └─ API Call Count
```

### **Sample Excel Data**

```
Ticker    | Company Name       | Sector      | Market Cap      | Total Debt     | Current Price | Volatility | Last Updated
----------|-------------------|-------------|-----------------|----------------|---------------|------------|------------------
AAPL      | Apple Inc.        | Technology  | 3,828,515,864,576 | 90,509,000,000 | 189.95       | 0.237      | 2025-01-10 03:00
MSFT      | Microsoft Corp.   | Technology  | 2,995,234,567,890 | 62,150,000,000 | 423.04       | 0.198      | 2025-01-10 03:00
JPM       | JPMorgan Chase    | Finance     | 614,821,345,678   | 156,892,000,000| 165.42       | 0.312      | 2025-01-10 03:00
...
```

---

## Implementation Plan

### **Phase 1: Excel Operations (1 hour)**

Create `services/excel_cache.py`:

```python
import openpyxl
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta
import pandas as pd

class ExcelDataCache:
    def __init__(self, filepath='data/portfolio_data.xlsx'):
        self.filepath = filepath
    
    def read_ticker_data(self, ticker: str) -> dict:
        """Read single ticker from Excel."""
        df = pd.read_excel(self.filepath, sheet_name='Companies')
        row = df[df['Ticker'] == ticker.upper()]
        
        if row.empty:
            raise ValueError(f"Ticker {ticker} not in Excel cache")
        
        return {
            'company_name': row['Company Name'].values[0],
            'sector': row['Sector'].values[0],
            'market_cap': float(row['Market Cap'].values[0]),
            'total_debt': float(row['Total Debt'].values[0]),
            'closing_prices': self._get_price_history(ticker),
            'equity_volatility': float(row['Equity Volatility'].values[0]),
        }
    
    def read_all_tickers(self) -> list[str]:
        """Get all tickers in cache."""
        df = pd.read_excel(self.filepath, sheet_name='Companies')
        return df['Ticker'].tolist()
    
    def write_ticker_data(self, ticker: str, data: dict):
        """Update single ticker in Excel."""
        df = pd.read_excel(self.filepath, sheet_name='Companies')
        idx = df[df['Ticker'] == ticker.upper()].index[0]
        
        df.at[idx, 'Company Name'] = data['company_name']
        df.at[idx, 'Sector'] = data['sector']
        df.at[idx, 'Market Cap'] = data['market_cap']
        df.at[idx, 'Total Debt'] = data['total_debt']
        df.at[idx, 'Equity Volatility'] = data['equity_volatility']
        df.at[idx, 'Last Updated'] = datetime.utcnow()
        
        # Write back
        with pd.ExcelWriter(self.filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Companies', index=False)
    
    def backup(self):
        """Create daily backup."""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d')
        backup_path = f'data/portfolio_data_backup_{timestamp}.xlsx'
        shutil.copy(self.filepath, backup_path)
```

### **Phase 2: Daily Update Script (30 min)**

Create `update_data.py`:

```python
import os
from dotenv import load_dotenv
import requests
from services.excel_cache import ExcelDataCache
from datetime import datetime

load_dotenv()
FINNHUB_KEY = os.getenv('FINNHUB_API_KEY')
BASE_URL = 'https://finnhub.io/api/v1'

def fetch_from_finnhub(ticker: str) -> dict:
    """Fetch current data from Finnhub."""
    
    # Profile
    profile = requests.get(f'{BASE_URL}/stock/profile2', 
        params={'symbol': ticker, 'token': FINNHUB_KEY}).json()
    
    # Quote
    quote = requests.get(f'{BASE_URL}/quote',
        params={'symbol': ticker, 'token': FINNHUB_KEY}).json()
    
    # Financials
    financials = requests.get(f'{BASE_URL}/stock/financials-reported',
        params={'symbol': ticker, 'token': FINNHUB_KEY}).json()
    
    # Candlestick (prices)
    candles = requests.get(f'{BASE_URL}/stock/candle',
        params={'symbol': ticker, 'resolution': 'D', 
                'count': 365, 'token': FINNHUB_KEY}).json()
    
    return {
        'company_name': profile.get('name', ticker),
        'sector': profile.get('finnhubIndustry', 'Unknown'),
        'market_cap': quote.get('pc', 0) * profile.get('shareOutstanding', 0),
        'total_debt': extract_debt(financials),
        'closing_prices': candles.get('c', []),
        'equity_volatility': calculate_volatility(candles.get('c', [])),
    }

def main():
    cache = ExcelDataCache()
    tickers = cache.read_all_tickers()
    
    print(f"[{datetime.utcnow()}] Starting daily update for {len(tickers)} tickers...")
    
    for i, ticker in enumerate(tickers, 1):
        try:
            print(f"  [{i}/{len(tickers)}] Fetching {ticker}...")
            data = fetch_from_finnhub(ticker)
            cache.write_ticker_data(ticker, data)
            print(f"    ✓ {ticker} updated")
        except Exception as e:
            print(f"    ✗ {ticker} failed: {e}")
    
    cache.backup()
    print(f"[{datetime.utcnow()}] Daily update complete!")

if __name__ == '__main__':
    main()
```

### **Phase 3: Update data_ingestion.py (30 min)**

Modify to read from Excel:

```python
# services/data_ingestion.py

from services.excel_cache import ExcelDataCache

# Initialize cache
_excel_cache = ExcelDataCache('data/portfolio_data.xlsx')

def fetch_ticker_data(ticker: str, closing_prices_override: list = None) -> dict:
    """
    Fetch ticker data from Excel cache.
    
    If closing_prices_override provided, use that instead of cached prices
    (useful for stress testing).
    """
    ticker_upper = ticker.strip().upper()
    
    # Check in-memory cache first (15 min TTL)
    cached = _get_cached(ticker_upper)
    if cached:
        logger.debug("Memory cache hit for %s", ticker_upper)
        return cached
    
    try:
        # Read from Excel
        logger.info("Reading %s from Excel cache", ticker_upper)
        data = _excel_cache.read_ticker_data(ticker_upper)
        
        # Apply override if provided
        if closing_prices_override is not None:
            data['closing_prices'] = closing_prices_override
        
        # Cache in memory for 15 minutes
        _set_cache(ticker_upper, data)
        return data
        
    except ValueError:
        raise RuntimeError(
            f"Ticker '{ticker_upper}' not found in Excel cache. "
            "Run 'python update_data.py' to refresh data."
        )

def fetch_bulk_price_histories(tickers: list) -> dict:
    """Fetch prices for multiple tickers from Excel."""
    result = {}
    for ticker in tickers:
        try:
            data = fetch_ticker_data(ticker)
            result[ticker.upper()] = data['closing_prices']
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", ticker, e)
    return result
```

### **Phase 4: Windows Scheduler (15 min)**

Schedule daily updates at 3 AM:

Create `scheduler_config.bat`:

```batch
@echo off
REM Run daily at 3 AM to update Excel cache

REM Navigate to backend directory
cd "D:\Projects (Finance)\Credit Risk Engine\backend"

REM Activate virtual environment if using one
REM call venv\Scripts\activate.bat

REM Run update script
python update_data.py

REM Log the result
echo Update completed at %date% %time% >> data/update_log.txt
```

Then register with Windows Task Scheduler:

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "C:\batch\update_excel.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 3:00AM
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM"
Register-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -TaskName "CreditRiskEngineUpdate" -Description "Update Excel data cache daily"
```

---

## Benefits Comparison

### **Before (API-Based)**
```
Daily requests: 10 tickers × 3 requests × 100 calls = 3,000 requests
Rate limit: Finnhub 60/min = 86,400 req/day
Utilization: 3.5% of limit (but many repeated calls)
Cost: Free tier works but laggy
Issues: Rate limiting on peak usage
```

### **After (Excel-Based)**
```
Daily requests: 30 (one batch update at 3 AM)
Rate limit: 86,400 req/day
Utilization: 0.03% of limit
Cost: Free tier easily sufficient
Issues: None - no rate limiting at all
```

### **Reduction: 99% fewer API calls**

---

## File Structure After Implementation

```
backend/
├── data/
│   ├── portfolio_data.xlsx          ← Main cache (10 KB)
│   ├── portfolio_data_backup.xlsx   ← Today's backup
│   ├── update_log.txt               ← Update history
│   └── archives/
│       ├── 2025-01-08.xlsx
│       ├── 2025-01-09.xlsx
│       └── 2025-01-10.xlsx
│
├── update_data.py                   ← NEW: Daily update script
├── services/
│   ├── data_ingestion.py            ← UPDATED: Read Excel
│   └── excel_cache.py               ← NEW: Excel operations
│
└── scheduler_config.bat             ← NEW: Windows scheduler
```

---

## Daily Workflow

```
3:00 AM - Windows Scheduler triggers
  ↓
update_data.py runs
  ├─ Fetches AAPL from Finnhub ✓
  ├─ Fetches MSFT from Finnhub ✓
  ├─ Fetches JPM from Finnhub ✓
  ├─ ... (30 requests total)
  └─ Writes all to portfolio_data.xlsx
  ↓
Backup created: portfolio_data_backup_2025-01-10.xlsx
  ↓
Update log written: "2025-01-10 03:05 - Update completed successfully"
  ↓
User: Makes API calls all day ← ZERO API requests
  ├─ /merton/AAPL → reads Excel (instant)
  ├─ /portfolio/preset/ig → reads Excel (instant)
  └─ /merton/MSFT → reads Excel (instant)
  ↓
3:00 AM next day - Process repeats
```

---

## Advantages Over Pure API

| Aspect | API | Excel Cache |
|--------|-----|-------------|
| **Rate Limiting** | ❌ Issues at scale | ✅ None ever |
| **Speed** | ⏱️ 5-40 sec | ✅ <100ms |
| **Requests/day** | 3,000+ | 30 |
| **Cost** | Free tier | Free tier |
| **Reliability** | 🔴 Depends on Yahoo/Finnhub | 🟢 Always works |
| **Offline** | ❌ Needs internet | ✅ Works offline |
| **Testing** | Hard (need mocks) | ✅ Easy (use test Excel) |
| **Historical Data** | ❌ Lost | ✅ Archived daily |

---

## Implementation Timeline

| Phase | Task | Time | Cumulative |
|-------|------|------|-----------|
| 1 | Create excel_cache.py | 1 hour | 1h |
| 2 | Create update_data.py | 30 min | 1.5h |
| 3 | Update data_ingestion.py | 30 min | 2h |
| 4 | Setup Windows Scheduler | 15 min | 2.25h |
| 5 | Testing & Debugging | 30 min | 2.75h |

**Total: ~3 hours to full implementation**

---

## Next Steps

**Would you like me to:**

1. ✅ Create `services/excel_cache.py` - Excel read/write operations
2. ✅ Create `update_data.py` - Daily Finnhub fetch & update
3. ✅ Update `data_ingestion.py` - Switch to Excel source
4. ✅ Create scheduler config - Windows Task Scheduler setup
5. ✅ Generate sample `portfolio_data.xlsx` - With test data

I can have this ready in 2-3 hours! This is WAY better than fighting with APIs. 🚀
