"""Test Excel file"""
from services.excel_source import get_excel_source

print("Loading Excel file...")
excel = get_excel_source('data/company_data.xlsx')

print("✓ File loaded successfully")
print()
print("Tickers:", excel.get_all_tickers())
print()
print("Testing 4 companies:")
print()

for ticker in ['AAPL', 'JPM', 'F', 'C']:
    try:
        data = excel.get_ticker_data(ticker)
        print(f"{ticker}:")
        print(f"  Company: {data['company_name']}")
        print(f"  Sector: {data['sector']}")
        print(f"  Market Cap: ${data['market_cap']:,.0f}")
        print(f"  Total Debt: ${data['total_debt']:,.0f}")
        print(f"  Prices: {len(data['closing_prices'])} days")
        print(f"  Volatility: {data['equity_volatility']:.2%}")
        print()
    except Exception as e:
        print(f"{ticker}: ERROR - {e}")
