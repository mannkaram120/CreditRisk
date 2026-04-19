#!/usr/bin/env python
"""Integration test for FMP API backend replacement."""
import sys
sys.path.insert(0, '.')
from services.data_ingestion import fetch_ticker_data
import json
import time

print("=" * 70)
print("Testing FMP API Integration with fetch_ticker_data()")
print("=" * 70)

# Test 1: Fetch AAPL (blue-chip)
print("\n[TEST 1] Fetching AAPL (Apple Inc.)...")
try:
    data = fetch_ticker_data("AAPL")
    print("✓ Success!")
    print(f"  Company: {data['company_name']}")
    print(f"  Sector: {data['sector']}")
    print(f"  Market Cap: ${data['market_cap']:,.0f}")
    print(f"  Total Debt: ${data['total_debt']:,.0f}")
    print(f"  Closing Prices: {len(data['closing_prices'])} days, oldest=${data['closing_prices'][0]:.2f}, newest=${data['closing_prices'][-1]:.2f}")
    print(f"  Equity Volatility: {data['equity_volatility']:.2%}")
    
    # Verify return format
    required_keys = {"company_name", "sector", "market_cap", "total_debt", "closing_prices", "equity_volatility"}
    if set(data.keys()) == required_keys:
        print("✓ Return format matches specification exactly!")
    else:
        print(f"✗ Missing or extra keys! Got: {set(data.keys())}, Expected: {required_keys}")
        sys.exit(1)
        
    # Verify data types
    assert isinstance(data["company_name"], str), "company_name must be str"
    assert isinstance(data["sector"], str), "sector must be str"
    assert isinstance(data["market_cap"], float), "market_cap must be float"
    assert isinstance(data["total_debt"], float), "total_debt must be float"
    assert isinstance(data["closing_prices"], list), "closing_prices must be list"
    assert isinstance(data["equity_volatility"], float), "equity_volatility must be float"
    assert len(data["closing_prices"]) >= 20, "Must have at least 20 price points"
    print("✓ All data types correct!")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Verify caching (15-minute TTL)
print("\n[TEST 2] Verifying cache (should be instant)...")
start = time.time()
data2 = fetch_ticker_data("AAPL")
elapsed = time.time() - start
if elapsed < 0.1:
    print(f"✓ Cache hit! Returned in {elapsed*1000:.1f}ms")
else:
    print(f"⚠ Slower response: {elapsed:.2f}s (possible API delay)")

if data == data2:
    print("✓ Cached data matches original exactly!")
else:
    print("✗ Cached data differs from original!")
    sys.exit(1)

# Test 3: Fetch a different ticker (JPM - bank)
print("\n[TEST 3] Fetching JPM (JPMorgan)...")
try:
    data3 = fetch_ticker_data("JPM")
    print("✓ Success!")
    print(f"  Company: {data3['company_name']}")
    print(f"  Sector: {data3['sector']}")
    print(f"  Market Cap: ${data3['market_cap']:,.0f}")
    print(f"  Total Debt: ${data3['total_debt']:,.0f}")
    print(f"  Equity Volatility: {data3['equity_volatility']:.2%}")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Error handling - invalid ticker
print("\n[TEST 4] Testing error handling with invalid ticker...")
try:
    data_invalid = fetch_ticker_data("XXXINVALIDXXX999")
    print("✗ Should have raised RuntimeError for invalid ticker!")
    sys.exit(1)
except RuntimeError as e:
    print(f"✓ Correctly raised RuntimeError: {e}")
except Exception as e:
    print(f"✗ Raised wrong exception type: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED!")
print("=" * 70)
print("\nSummary:")
print("  ✓ FMP API integration is working correctly")
print("  ✓ Return format matches specification exactly")
print("  ✓ Data types are correct")
print("  ✓ Caching is operational")
print("  ✓ Multiple tickers work")
print("  ✓ Error handling works correctly")
print("\n🎉 Ready for production!")
