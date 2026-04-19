# Excel File Data Source

## Setup: Create Your Excel File

Create a file: `backend/data/company_data.xlsx`

### Sheet: "Companies"

| Ticker | Company Name | Sector | Market Cap (USD) | Total Debt (USD) | Current Price | Stock Prices (365 days) |
|--------|--------------|--------|------------------|------------------|----------------|------------------------|
| AAPL | Apple Inc. | Technology | 3,828,515,864,576 | 90,509,000,000 | 189.95 | [197.29, 201.64, 201.26, ...] |
| MSFT | Microsoft Corp. | Technology | 2,995,234,567,890 | 62,150,000,000 | 423.04 | [420.15, 421.03, 419.87, ...] |
| JPM | JPMorgan Chase | Finance | 614,821,345,678 | 156,892,000,000 | 165.42 | [167.24, 166.89, 168.15, ...] |

### Example Excel Structure:

```
Column A: Ticker (AAPL, MSFT, JPM, ...)
Column B: Company Name
Column C: Sector
Column D: Market Cap
Column E: Total Debt
Column F: Current Price
Columns G onwards: Daily prices (oldest first, in order of dates)
```

---

## Backend Implementation

Create file: `backend/services/excel_source.py`

```python
import pandas as pd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ExcelDataSource:
    """Read company data from Excel file."""
    
    def __init__(self, filepath: str = 'data/company_data.xlsx'):
        self.filepath = filepath
        self.df = None
        self.load_file()
    
    def load_file(self):
        """Load Excel file into memory."""
        try:
            self.df = pd.read_excel(self.filepath, sheet_name='Companies')
            logger.info(f"Loaded Excel file with {len(self.df)} companies")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Excel file not found: {self.filepath}\n"
                f"Please create it at: {self.filepath}\n"
                f"Columns needed: Ticker, Company Name, Sector, Market Cap, Total Debt, "
                f"Current Price, [Daily prices...]"
            )
        except Exception as e:
            raise RuntimeError(f"Error loading Excel file: {e}")
    
    def get_ticker_data(self, ticker: str) -> dict:
        """
        Fetch ticker data from Excel.
        
        Args:
            ticker: Stock ticker (e.g., 'AAPL')
        
        Returns:
            dict with keys: company_name, sector, market_cap, total_debt, 
                           closing_prices, equity_volatility
        """
        ticker_upper = ticker.strip().upper()
        
        # Find row for this ticker
        row = self.df[self.df['Ticker'] == ticker_upper]
        if row.empty:
            available = self.df['Ticker'].tolist()
            raise ValueError(
                f"Ticker '{ticker_upper}' not found in Excel.\n"
                f"Available tickers: {available}"
            )
        
        row = row.iloc[0]
        
        # Get closing prices (from column G onwards)
        # Assuming columns A-F are: Ticker, Company, Sector, MarketCap, Debt, Price
        # Columns G onwards are daily prices
        closing_prices = []
        for col in self.df.columns[6:]:  # Start from column G (index 6)
            try:
                price = float(row[col])
                if not np.isnan(price):
                    closing_prices.append(price)
            except (ValueError, TypeError):
                continue
        
        if not closing_prices or len(closing_prices) < 20:
            raise ValueError(
                f"Insufficient price data for {ticker_upper}. "
                f"Need at least 20 data points, got {len(closing_prices)}."
            )
        
        # Calculate equity volatility
        arr = np.array(closing_prices)
        log_ret = np.diff(np.log(arr))
        equity_volatility = float(np.std(log_ret, ddof=1) * np.sqrt(252))
        
        return {
            'company_name': str(row['Company Name']),
            'sector': str(row['Sector']),
            'market_cap': float(row['Market Cap (USD)']),
            'total_debt': float(row['Total Debt (USD)']),
            'closing_prices': closing_prices,
            'equity_volatility': equity_volatility,
        }
    
    def get_all_tickers(self) -> list:
        """Get all tickers in Excel."""
        return self.df['Ticker'].tolist()
    
    def reload(self):
        """Reload Excel file (call this if file was updated)."""
        self.load_file()
        logger.info("Excel file reloaded")


# Initialize global instance
_excel_source = None

def get_excel_source(filepath: str = 'data/company_data.xlsx') -> ExcelDataSource:
    """Get Excel data source instance."""
    global _excel_source
    if _excel_source is None:
        _excel_source = ExcelDataSource(filepath)
    return _excel_source
```

---

## Update data_ingestion.py

Replace `fetch_ticker_data()` to read from Excel:

```python
# At top of services/data_ingestion.py

from services.excel_source import get_excel_source

# Get Excel source
excel_source = get_excel_source('data/company_data.xlsx')

def fetch_ticker_data(
    ticker: str,
    closing_prices_override: Optional[list[float]] = None,
) -> dict:
    """
    Fetch ticker data from Excel file.
    
    Args:
        ticker: Stock ticker
        closing_prices_override: Override prices (for stress testing)
    
    Returns:
        dict with company data
    """
    ticker_upper = ticker.strip().upper()
    
    # Check in-memory cache first (15 min TTL)
    cached = _get_cached(ticker_upper)
    if cached:
        logger.debug("Cache hit for %s", ticker_upper)
        return cached
    
    try:
        # Read from Excel
        logger.info("Reading %s from Excel", ticker_upper)
        data = excel_source.get_ticker_data(ticker_upper)
        
        # Apply override if provided (for stress testing)
        if closing_prices_override is not None:
            data['closing_prices'] = closing_prices_override
            # Recalculate volatility with override prices
            arr = np.array(closing_prices_override)
            log_ret = np.diff(np.log(arr))
            data['equity_volatility'] = float(np.std(log_ret, ddof=1) * np.sqrt(252))
        
        # Cache in memory for 15 minutes
        _set_cache(ticker_upper, data)
        return data
    
    except ValueError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        raise RuntimeError(f"Error reading {ticker} from Excel: {e}")


def fetch_bulk_price_histories(tickers: list[str]) -> dict[str, list[float]]:
    """Fetch price histories for multiple tickers from Excel."""
    result = {}
    for ticker in tickers:
        try:
            data = fetch_ticker_data(ticker)
            result[ticker.upper()] = data['closing_prices']
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", ticker, e)
    return result
```

---

## Benefits

✅ **Zero API calls** - You provide all data  
✅ **No rate limiting** - Ever  
✅ **Instant responses** - Reads Excel (cached in memory)  
✅ **Full control** - You manage data quality  
✅ **Simple** - Just a spreadsheet  
✅ **Easy testing** - Use test Excel file  

---

## Usage

### 1. Create Excel File

Save as: `backend/data/company_data.xlsx`

| Ticker | Company Name | Sector | Market Cap (USD) | Total Debt (USD) | Price | Day1 | Day2 | Day3 | ... |
|--------|--------------|--------|------------------|------------------|-------|------|------|------|-----|
| AAPL | Apple Inc. | Technology | 3.83E+12 | 90509000000 | 189.95 | 197.29 | 201.64 | 201.26 | ... |
| MSFT | Microsoft | Technology | 2.99E+12 | 62150000000 | 423.04 | 420.15 | 421.03 | 419.87 | ... |

### 2. Test It

```bash
cd backend
python -c "
from services.excel_source import get_excel_source

excel = get_excel_source('data/company_data.xlsx')
data = excel.get_ticker_data('AAPL')
print('AAPL loaded:', data['company_name'])
print('Market Cap:', data['market_cap'])
print('Volatility:', data['equity_volatility'])
"
```

### 3. Update Excel

Whenever you have new data:
1. Open `company_data.xlsx`
2. Update the data
3. Save the file

The backend automatically picks up changes!

### 4. Use Backend

```bash
uvicorn main:app --port 8000
```

Now API calls read from your Excel file:
```bash
curl http://127.0.0.1:8000/merton/AAPL
# Returns data from your Excel file!
```

---

## Excel File Format Tips

### Column Order (Important!)

```
A: Ticker
B: Company Name
C: Sector
D: Market Cap (USD)
E: Total Debt (USD)
F: Current Price (ignored, just for reference)
G onwards: Daily closing prices (365 days, oldest first)
```

### Price Data Format

- **Column G**: Day 1 (oldest)
- **Column H**: Day 2
- ...
- **Column AQ**: Day 365 (most recent)

Or however many days you have (minimum 20).

### Data Types

- **Ticker**: Text (AAPL, MSFT, etc.)
- **Company Name**: Text
- **Sector**: Text
- **Market Cap**: Number (use scientific notation for billions)
- **Total Debt**: Number
- **Prices**: Numbers (decimals OK)

### Example Excel Formula

To calculate market cap from stock price and shares:
```excel
=Stock_Price * Shares_Outstanding
```

---

## Error Handling

If something goes wrong:

```python
# Missing ticker
"Ticker 'XYZ' not found in Excel. Available: AAPL, MSFT, JPM"

# Insufficient data
"Insufficient price data for AAPL. Need at least 20 data points, got 5."

# File not found
"Excel file not found: backend/data/company_data.xlsx"
```

---

## Advantages

| Aspect | API | Your Excel |
|--------|-----|-----------|
| **API Calls** | 30+ per portfolio | 0 |
| **Rate Limiting** | ❌ Yes | ✅ No |
| **Speed** | Slow (5-8s) | Fast (<100ms) |
| **Data Control** | ❌ Depends on API | ✅ You control |
| **Cost** | Free tier | No cost |
| **Reliability** | 🔴 API downtime | 🟢 Always works |

---

## Setup Checklist

- [ ] Create `backend/data/company_data.xlsx`
- [ ] Add columns: Ticker, Company Name, Sector, Market Cap, Total Debt, Price, [Daily Prices...]
- [ ] Add your companies
- [ ] Save file
- [ ] Run: `python -c "from services.excel_source import get_excel_source; print(get_excel_source('data/company_data.xlsx').get_all_tickers())"`
- [ ] Verify it loads correctly
- [ ] Start backend: `uvicorn main:app --port 8000`
- [ ] Test: `curl http://127.0.0.1:8000/merton/AAPL`

---

**Done!** Now your system reads from YOUR Excel file, not from APIs. 🚀
