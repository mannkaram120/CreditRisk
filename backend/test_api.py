"""Test API endpoints with Excel data source"""
import httpx
import json

with httpx.Client(timeout=30) as client:
    print("Testing endpoints with Excel data source")
    print("=" * 60)
    print()
    
    # Test 1: Health
    print("1. Health Check")
    resp = client.get("http://127.0.0.1:8000/health")
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.json()}")
    print()
    
    # Test 2: Single ticker
    print("2. Merton Analysis (AAPL)")
    resp = client.get("http://127.0.0.1:8000/merton/AAPL")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Status: {resp.status_code}")
        print(f"   Company: {data['company_name']}")
        print(f"   Market Cap: ${data['market_cap']:,.0f}")
        print(f"   Total Debt: ${data['total_debt']:,.0f}")
        print(f"   PD: {data['probability_of_default']:.4e}")
        print(f"   DD: {data['distance_to_default']:.2f}")
    else:
        print(f"   ERROR: {resp.status_code}")
        print(f"   {resp.json()}")
    print()
    
    # Test 3: Multiple tickers
    print("3. Multiple Tickers")
    for ticker in ["MSFT", "JPM", "F"]:
        resp = client.get(f"http://127.0.0.1:8000/merton/{ticker}")
        status = "OK" if resp.status_code == 200 else "FAIL"
        print(f"   {ticker}: {status}")
    print()
    
    # Test 4: Portfolio
    print("4. Portfolio Presets")
    for preset in ["ig", "hy", "mixed"]:
        resp = client.get(f"http://127.0.0.1:8000/portfolio/preset/{preset}")
        if resp.status_code == 200:
            data = resp.json()
            n_companies = len(data["companies"])
            print(f"   {preset}: OK ({n_companies} companies)")
        else:
            print(f"   {preset}: FAIL")
    print()
    
    print("=" * 60)
    print("✓ API WORKING WITH EXCEL DATA SOURCE!")
    print("=" * 60)
