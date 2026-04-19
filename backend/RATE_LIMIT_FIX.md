# Yahoo Finance Rate Limiting - Solutions

## Problem
You're seeing: `429 Client Error: Too Many Requests`

This means Yahoo Finance API is blocking requests due to rate limiting.

---

## **SOLUTION 1: Wait for Rate Limit to Reset** ✅ FASTEST

Rate limits typically reset in 10-15 minutes.

```bash
# Just wait 15 minutes, then restart the server
uvicorn main:app --port 8000
```

---

## **SOLUTION 2: Use Demo Mode** ✅ FOR TESTING

Alpha Vantage has a free "demo" mode that works without API keys:

```bash
# Update data_ingestion.py to use Alpha Vantage (see below)
```

---

## **SOLUTION 3: Get a Free Alpha Vantage API Key** ✅ RECOMMENDED

Alpha Vantage is more reliable than yfinance:

1. Go to: https://www.alphavantage.co/
2. Sign up (free tier)
3. Copy your API key
4. Add to `.env`:
```
ALPHA_VANTAGE_API_KEY=your_key_here
```

5. Use the modified data_ingestion.py (Alpha Vantage version)

---

## **SOLUTION 4: Reduce Request Frequency**

If you're testing many tickers rapidly, space them out:

```bash
# Test one ticker every 10 seconds
for ticker in AAPL MSFT JPM; do
    curl http://127.0.0.1:8000/merton/$ticker
    Start-Sleep -Seconds 10
done
```

---

## **Why Yahoo Finance is Being Rate Limited**

- Multiple HTTP 429 responses in short succession
- Yahoo blocks aggressively to prevent scraping
- Free tier has very low limits (~2-3 requests per ticker)
- Shared IP addresses get blocked together

---

## **Recommended Approach**

### Step 1: Wait 15 minutes for reset
```bash
Start-Sleep -Seconds 900
```

### Step 2: Restart Server
```bash
# Kill old server
Get-Process python | ForEach-Object { Stop-Process -Id $_.Id -Force }

# Clear cache
Remove-Item -Recurse __pycache__* .pytest_cache* -Force

# Start fresh
uvicorn main:app --port 8000
```

### Step 3: Test with 10-second delays between requests
```bash
# Test health
curl http://127.0.0.1:8000/health
Start-Sleep -Seconds 10

# Test AAPL
curl http://127.0.0.1:8000/merton/AAPL
Start-Sleep -Seconds 10

# Test another ticker
curl http://127.0.0.1:8000/merton/MSFT
```

---

## **For Production Deployment**

Consider these alternatives:
1. **Alpha Vantage** - Free tier, 5 requests/min
2. **IEX Cloud** - Paid but very reliable
3. **Finnhub** - You already have an API key!
4. **Polygon.io** - Paid but excellent uptime

---

## **Immediate Action Required**

👉 **Just wait 15 minutes and try again**

That's the fastest fix. Yahoo's rate limits reset automatically.

```bash
Write-Host "Waiting for rate limit reset..."
Start-Sleep -Seconds 900
Write-Host "Restarting server..."
uvicorn main:app --port 8000
```

---

**Status**: Rate limit expires in ~15 minutes
**Severity**: Not a bug, it's an API constraint
**Action**: Wait or use alternative data source
