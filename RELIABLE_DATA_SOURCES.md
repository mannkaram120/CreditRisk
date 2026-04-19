# Reliable Data Sources for Corporate Credit Risk Analysis

## **Summary Table**

| Source | Price Data | Market Cap | Debt | Sector | Rate Limit | Cost | Quality |
|--------|-----------|-----------|------|--------|-----------|------|---------|
| **Alpha Vantage** | ✅ | ✅ | ❌ | ✅ | 5/min free | Free | ⭐⭐⭐⭐ |
| **IEX Cloud** | ✅ | ✅ | ✅ | ✅ | 100/sec | $9/mo | ⭐⭐⭐⭐⭐ |
| **Polygon.io** | ✅ | ✅ | ✅ | ✅ | High | $29/mo | ⭐⭐⭐⭐⭐ |
| **Finnhub** | ✅ | ✅ | ✅ | ✅ | 60/min free | Free | ⭐⭐⭐⭐ |
| **Yahoo Finance** | ✅ | ✅ | ✅ | ✅ | 2-3/ticker | Free | ⭐⭐ (unreliable) |
| **FRED (Fed)** | ❌ | ❌ | ❌ | ❌ | Unlimited | Free | N/A |

---

## **BEST OPTIONS (Ranked)**

### **1️⃣ ALPHA VANTAGE** ✅ RECOMMENDED FOR TESTING

**Best for:** Learning, testing, small portfolios

**Pros:**
- Free tier: 5 requests/min, 500/day
- No rate limiting within limits
- All data we need
- Stable API
- JSON responses

**Cons:**
- 5 req/min is slow for many tickers
- Need to wait between requests

**Get API Key:**
```bash
# Free at https://www.alphavantage.co/
# Takes 2 minutes
```

**Data Available:**
- Daily stock prices ✅
- Company overview (market cap, sector) ✅
- Balance sheet data (debt) ✅

**Implementation:**
```python
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData

# Get stock data
ts = TimeSeries(key='YOUR_API_KEY', output_format='pandas')
data, meta = ts.get_daily(symbol='AAPL')

# Get company fundamentals
fd = FundamentalData(key='YOUR_API_KEY', output_format='pandas')
balance_sheet = fd.get_balance_sheet_annual('AAPL')
```

---

### **2️⃣ FINNHUB** ✅ YOU ALREADY HAVE AN API KEY!

**Best for:** Production with free tier

**Pros:**
- You have the API key already
- 60 req/min free tier
- Excellent data quality
- No rate limiting within limits
- Most reliable free option

**Cons:**
- Fewer endpoints than paid alternatives
- Need to add integration

**Your API Key:**
```
Check your .env file - you already have FINNHUB_API_KEY
```

**Data Available:**
- Daily stock prices ✅
- Company profile (market cap, sector) ✅
- Financial statements (debt) ✅

**Implementation:**
```python
import requests

API_KEY = 'YOUR_FINNHUB_KEY'
BASE_URL = 'https://finnhub.io/api/v1'

# Stock price
resp = requests.get(f'{BASE_URL}/quote', params={
    'symbol': 'AAPL',
    'token': API_KEY
})

# Company profile
resp = requests.get(f'{BASE_URL}/stock/profile2', params={
    'symbol': 'AAPL',
    'token': API_KEY
})

# Financial statements
resp = requests.get(f'{BASE_URL}/stock/financials-reported', params={
    'symbol': 'AAPL',
    'token': API_KEY
})
```

---

### **3️⃣ IEX CLOUD** ✅ BEST OVERALL (Paid)

**Best for:** Production systems

**Pros:**
- Extremely reliable
- 100 requests/second
- Unlimited daily quota
- Best documentation
- All data we need
- No rate limiting issues

**Cons:**
- $9/month minimum
- Need credit card

**Get Started:**
```bash
# Sign up at https://iexcloud.io/
# Free trial available
```

**Data Available:**
- Real-time stock prices ✅
- Company fundamentals ✅
- Balance sheet ✅
- Income statement ✅

---

### **4️⃣ POLYGON.IO** ✅ ALTERNATIVE (Paid)

**Best for:** High-volume production

**Pros:**
- Very fast
- Good documentation
- $29/month
- No rate limiting

**Cons:**
- Most expensive of these options

---

## **COMPARISON: What Each Source Has**

### Data We Need:

```
1. Stock Price History (1 year daily)
   ✅ Alpha Vantage  (up to 20 years)
   ✅ Finnhub        (unlimited)
   ✅ IEX Cloud      (unlimited)
   ✅ Polygon.io     (unlimited)
   ❌ Yahoo Finance  (unreliable)

2. Market Cap
   ✅ Alpha Vantage  (in company overview)
   ✅ Finnhub        (in profile)
   ✅ IEX Cloud      (in company stats)
   ✅ Polygon.io     (in company details)
   ⚠️ Yahoo Finance  (inconsistent)

3. Total Debt (Short-term + Long-term)
   ✅ Alpha Vantage  (balance sheet)
   ✅ Finnhub        (financial statements)
   ✅ IEX Cloud      (balance sheet)
   ✅ Polygon.io     (financial statements)
   ⚠️ Yahoo Finance  (unreliable)

4. Sector
   ✅ Alpha Vantage  (company overview)
   ✅ Finnhub        (profile)
   ✅ IEX Cloud      (company details)
   ✅ Polygon.io     (company details)
   ⚠️ Yahoo Finance  (inconsistent)
```

---

## **RATE LIMIT COMPARISON**

```
Free Tier:
  Yahoo Finance    → 2-3 requests per ticker (BLOCKS YOU)
  Alpha Vantage    → 5 requests/minute (RELIABLE)
  Finnhub          → 60 requests/minute (RELIABLE) ← YOU HAVE THIS
  IEX Cloud        → Not free tier

Paid:
  IEX Cloud        → 100 requests/second (UNLIMITED)
  Polygon.io       → High throughput (UNLIMITED)
```

---

## **MY RECOMMENDATION**

### **🥇 For Immediate Use (Today):**
Use **Finnhub** - you already have the API key!
- 60 requests/minute = fast enough
- No rate limiting within limits
- All data available
- Already in your .env

### **🥈 If Finnhub Doesn't Work:**
Use **Alpha Vantage** - free and reliable
- 5 requests/minute = slower but consistent
- Add 12-second delays between requests
- Get API key (2 minutes)

### **🥉 For Production:**
Use **IEX Cloud** - $9/month
- Unlimited requests
- Most reliable
- Best documentation

---

## **QUICK START: Use Finnhub (YOU HAVE THE KEY!)**

### Step 1: Check Your API Key
```bash
cat .env
```

You should see:
```
FINNHUB_API_KEY=your_key_here
```

### Step 2: Test It
```bash
python -c "
import os
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('FINNHUB_API_KEY')

# Test 1: Get stock price
resp = requests.get('https://finnhub.io/api/v1/quote', params={
    'symbol': 'AAPL',
    'token': key
})
print('AAPL Price:', resp.json())
"
```

### Step 3: Use in Code
Update `data_ingestion.py` to use Finnhub instead of yfinance

---

## **IMPLEMENTATION: Finnhub Version**

Replace yfinance with Finnhub in `data_ingestion.py`:

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()
FINNHUB_KEY = os.getenv('FINNHUB_API_KEY')
BASE_URL = 'https://finnhub.io/api/v1'

def fetch_ticker_data_finnhub(ticker: str) -> dict:
    """Fetch data using Finnhub instead of yfinance."""
    
    # Get company profile
    profile_resp = requests.get(
        f'{BASE_URL}/stock/profile2',
        params={'symbol': ticker, 'token': FINNHUB_KEY}
    )
    profile = profile_resp.json()
    
    # Get current price + market data
    quote_resp = requests.get(
        f'{BASE_URL}/quote',
        params={'symbol': ticker, 'token': FINNHUB_KEY}
    )
    quote = quote_resp.json()
    
    # Get financial statements for debt
    financials_resp = requests.get(
        f'{BASE_URL}/stock/financials-reported',
        params={'symbol': ticker, 'token': FINNHUB_KEY}
    )
    financials = financials_resp.json()
    
    # Get price history (candlestick)
    candle_resp = requests.get(
        f'{BASE_URL}/stock/candle',
        params={
            'symbol': ticker,
            'resolution': 'D',
            'count': 365,
            'token': FINNHUB_KEY
        }
    )
    candles = candle_resp.json()
    
    return {
        'company_name': profile.get('name', ticker),
        'sector': profile.get('finnhubIndustry', 'Unknown'),
        'market_cap': profile.get('marketCapitalization', 0) * 1_000_000,
        'total_debt': extract_debt(financials),
        'closing_prices': candles.get('c', []),
        'equity_volatility': calculate_volatility(candles.get('c', []))
    }
```

---

## **RATE LIMIT BEST PRACTICES**

### Alpha Vantage (5 req/min):
```python
import time
for ticker in ['AAPL', 'MSFT', 'JPM']:
    fetch(ticker)
    time.sleep(12)  # 12 seconds between requests
```

### Finnhub (60 req/min):
```python
import time
for ticker in ['AAPL', 'MSFT', 'JPM']:
    fetch(ticker)
    time.sleep(1)  # 1 second between requests
```

### IEX Cloud (unlimited):
```python
# No delay needed
for ticker in ['AAPL', 'MSFT', 'JPM']:
    fetch(ticker)
```

---

## **NEXT STEPS**

1. **Immediate:** Test Finnhub with your existing API key
2. **If works:** Integrate into `data_ingestion.py`
3. **If not:** Switch to Alpha Vantage (free, reliable)
4. **For production:** Use IEX Cloud ($9/mo)

---

## **Resources**

- **Alpha Vantage Docs:** https://www.alphavantage.co/documentation/
- **Finnhub Docs:** https://finnhub.io/docs/api/
- **IEX Cloud Docs:** https://iexcloud.io/docs/
- **Polygon.io Docs:** https://polygon.io/docs/

---

**My Strong Recommendation:**
👉 Use **Finnhub** - you already have the API key, it's reliable, and 60 req/min is plenty for your portfolio analysis.

Let me help you integrate it if you want!
