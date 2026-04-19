# Reducing API Requests per Ticker

## Current Request Count

**Current: 3 requests per ticker**
```
1. Price history     → /stock/candle
2. Company profile   → /stock/profile2 (market cap, sector)
3. Debt/financials   → /stock/financials-reported
─────────────────────────────────
Total per ticker: 3 requests
10 tickers: 30 requests
```

---

## Optimization Strategies

### **Strategy 1: Differential Caching** ✅ EASIEST (Saves 67%)

Different data has different change rates:

```python
# Current: Cache everything for 15 minutes

# Optimized cache durations:
CACHE_TTL = {
    'price_history': 15,      # Changes daily     (15 min TTL)
    'company_profile': 7*24*60, # Changes rarely   (1 week TTL)
    'debt_data': 7*24*60,       # Changes quarterly (1 week TTL)
}
```

**Impact:**
- First call: 3 requests
- Calls within 15 min: 1 request (prices only)
- Calls within 1 week: 1 request (prices only)

**Reduction: 67-90%** depending on usage pattern

---

### **Strategy 2: Lazy-Load Debt Data** ✅ MEDIUM (Saves 33%)

Load debt only when needed:

```python
# Current: Always fetch debt
fetch_ticker_data(ticker) → requires debt

# Optimized: Debt optional
fetch_ticker_data(ticker, load_debt=False)
  → Only returns: price, market_cap, sector
  → Skips: debt request
  → Saves: 1 request per ticker
```

**When to skip debt:**
- Stress testing (uses stress profiles)
- Quick portfolio screening
- When debt rarely changes

**Reduction: 33%** (3 → 2 requests)

---

### **Strategy 3: Batch Endpoints** ✅ HIGH IMPACT (Saves 50-66%)

Use endpoints that combine data:

```python
# Instead of 3 separate calls per ticker:
Finnhub: /quote → gets price + market_cap + day change

# Instead of:
1. /stock/profile2
2. /stock/candle
3. /stock/financials-reported

# Do:
1. /stock/profile2 → once per week (cached)
2. /stock/quote → once per day (combined price + market data)
3. /stock/financials-reported → once per quarter (cached)
```

**Reduction: 66%** (3 → 1 request per day, after first week)

---

### **Strategy 4: Skip Sector Lookup** ✅ QUICK (Saves 33%)

Sector rarely changes. Get it once and cache forever:

```python
# Old: Fetch sector every time
sector = profile['sector']  # 1 request

# New: Get on first call, cache permanently
if ticker not in SECTOR_CACHE:
    sector = profile['sector']
else:
    sector = SECTOR_CACHE[ticker]  # 0 requests
```

**Reduction: 33% over time**

---

## Recommended Solution: Combination

**Implement all 4 strategies:**

```python
# New cache structure:
CACHE = {
    'AAPL': {
        'company_name': 'Apple',
        'sector': 'Technology',              # Cache: 1 year
        'market_cap': 3.8e12,                # Cache: 1 week
        'total_debt': 9.05e10,               # Cache: 3 months
        'closing_prices': [...],             # Cache: 15 min
        'equity_volatility': 0.237,          # Cache: 1 day
    }
}

# New function signature:
def fetch_ticker_data(
    ticker: str,
    load_debt: bool = True,                 # New: optional debt
    use_cache: bool = True,                 # New: allow cache bypass
    cache_ttl_override: dict = None,        # New: custom TTL
) -> dict:
    ...
```

---

## Before vs After

### **Scenario: 10-company portfolio, called twice in 1 hour**

**Current approach:**
```
Call 1: 10 tickers × 3 requests = 30 requests
Call 2: 10 tickers × 3 requests = 30 requests
Total: 60 requests
```

**With differential caching:**
```
Call 1: 10 × 3 = 30 requests (all fresh)
Call 2: 10 × 1 = 10 requests (sector/debt cached, only prices fresh)
Total: 40 requests
Savings: 33%
```

**With lazy loading (skip debt):**
```
Call 1: 10 × 2 = 20 requests
Call 2: 10 × 1 = 10 requests
Total: 30 requests
Savings: 50%
```

**With full optimization:**
```
Call 1: 10 × 3 = 30 requests (first time, all fresh)
Call 2: 10 × 1 = 10 requests (sector/debt cached 1 week)
Call 3-52: 10 × 1 = 10 requests (only prices refresh daily)
Weekly total: ~150 requests
Without optimization: 300+ requests
Savings: 50-60%
```

---

## Implementation Options

### **Option A: Smart Caching** (Easiest, 33% savings)

```python
# Update cache to track data freshness
_cache = {
    'AAPL': {
        'data': {...},
        'cached_at': datetime.utcnow(),
        'ttl_by_field': {
            'prices': 15,              # min
            'market_cap': 7*24*60,     # min
            'debt': 7*24*60,           # min
            'sector': 365*24*60,       # min
        }
    }
}

# Check what needs refreshing
def needs_refresh(ticker, field):
    cached = _cache[ticker]
    age_min = (utcnow - cached['cached_at']).total_seconds() / 60
    ttl = cached['ttl_by_field'][field]
    return age_min > ttl
```

### **Option B: Lazy Load Debt** (Medium effort, 50% savings)

```python
def fetch_ticker_data(
    ticker: str,
    load_debt: bool = True,
    ...
) -> dict:
    # ... get prices, market_cap, sector ...
    
    if load_debt:
        total_debt = _extract_debt(t, info)  # 1 request
    else:
        total_debt = 0  # or None
    
    return {
        'company_name': company_name,
        'sector': sector,
        'market_cap': market_cap,
        'total_debt': total_debt,  # May be 0 if not loaded
        'closing_prices': closing_prices,
        'equity_volatility': equity_volatility,
    }
```

### **Option C: Full Optimization** (Best long-term, 60% savings)

Implement A + B + better batch endpoints

---

## My Recommendation

**Implement Option A (Smart Caching)** - Takes 30 minutes, saves 33%

```python
# 1. Add field-level TTL to cache
# 2. Check freshness per field, not whole record
# 3. Only refetch stale fields
# 4. Profit: 33% fewer requests
```

Then after that works, optionally add:
- **Option B (Lazy Load)** - Another 17% savings
- **Better endpoints** - Another 10-15% savings

**Total possible: 60% reduction**

---

## Quick Estimate

**With smart caching alone:**

```
Current: 10 tickers × 3 requests × 10 calls/day = 300 requests/day
Optimized: 10 × 3 + (10×1)×9 = 30 + 90 = 120 requests/day
Savings: 60% (300 → 120)

With Finnhub 60/min limit:
- Current: Uses ~100% of daily quota
- Optimized: Uses ~33% of daily quota
- Result: Can run 3x more analyses
```

---

## Decision

**Which optimization do you want?**

1. **⚡ Quick Win** - Option A (Smart Caching) → 33% savings, 30 min
2. **🎯 Balanced** - Option A + B → 50% savings, 1 hour  
3. **🚀 Full Optimization** - All strategies → 60% savings, 2 hours

I recommend starting with **Option A** today, then adding B tomorrow if needed.

Want me to implement it?
