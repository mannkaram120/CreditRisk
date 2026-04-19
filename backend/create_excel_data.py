"""
Generate Excel file with company data for Credit Risk Engine.

This script creates backend/data/company_data.xlsx with sample company data
including prices for the last 365 days.

Run: python create_excel_data.py
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Company data (Ticker, Name, Sector, Market Cap, Total Debt)
companies = [
    # Investment Grade
    ('AAPL', 'Apple Inc.', 'Technology', 3_828_515_864_576, 90_509_000_000),
    ('MSFT', 'Microsoft Corporation', 'Technology', 2_995_234_567_890, 62_150_000_000),
    ('JPM', 'JPMorgan Chase Co.', 'Finance', 614_821_345_678, 156_892_000_000),
    ('JNJ', 'Johnson & Johnson', 'Healthcare', 373_621_456_789, 28_456_000_000),
    ('PG', 'Procter & Gamble', 'Consumer', 387_123_456_789, 31_234_000_000),
    
    # High Yield
    ('F', 'Ford Motor Company', 'Automotive', 48_234_567_890, 156_234_000_000),
    ('M', 'Macy\'s Inc.', 'Retail', 6_234_567_890, 9_234_000_000),
    ('CCL', 'Carnival Corporation', 'Travel', 12_456_789_012, 28_123_000_000),
    ('AAL', 'American Airlines', 'Aviation', 10_234_567_890, 24_567_000_000),
    ('AMC', 'AMC Entertainment', 'Entertainment', 1_234_567_890, 12_345_000_000),
    
    # Crisis Portfolio
    ('C', 'Citigroup Inc.', 'Finance', 145_678_901_234, 198_456_000_000),
    ('BAC', 'Bank of America', 'Finance', 312_345_678_901, 245_678_000_000),
    ('GS', 'Goldman Sachs', 'Finance', 128_456_789_012, 178_234_000_000),
    ('MS', 'Morgan Stanley', 'Finance', 174_123_456_789, 156_789_000_000),
    ('WFC', 'Wells Fargo', 'Finance', 188_456_789_012, 198_123_000_000),
]

# Generate 365 days of price data (going back 1 year)
def generate_price_history(start_price, volatility=0.02):
    """Generate realistic price history with random walk."""
    prices = [start_price]
    current_price = start_price
    
    for _ in range(364):  # 365 days total
        # Random daily return
        daily_return = np.random.normal(0.0005, volatility)  # Slight upward drift
        current_price = current_price * (1 + daily_return)
        prices.append(current_price)
    
    return prices

# Price starting points (approximate current prices as of 2025)
price_map = {
    'AAPL': (189.95, 0.235),   # price, volatility
    'MSFT': (423.04, 0.198),
    'JPM': (165.42, 0.312),
    'JNJ': (154.23, 0.178),
    'PG': (167.89, 0.156),
    'F': (11.45, 0.456),
    'M': (18.67, 0.578),
    'CCL': (14.23, 0.876),
    'AAL': (19.34, 0.645),
    'AMC': (2.89, 1.234),
    'C': (67.45, 0.524),
    'BAC': (35.67, 0.389),
    'GS': (89.12, 0.412),
    'MS': (112.34, 0.378),
    'WFC': (78.56, 0.445),
}

# Build data
data = []
for ticker, name, sector, market_cap, debt in companies:
    start_price, vol = price_map.get(ticker, (100, 0.25))
    prices = generate_price_history(start_price, vol)
    
    row = {
        'Ticker': ticker,
        'Company Name': name,
        'Sector': sector,
        'Market Cap (USD)': market_cap,
        'Total Debt (USD)': debt,
        'Current Price': prices[-1],  # Most recent price
    }
    
    # Add 365 daily prices (oldest first)
    for i, price in enumerate(prices):
        row[f'Day_{i+1}'] = round(price, 2)
    
    data.append(row)

# Create DataFrame
df = pd.DataFrame(data)

# Write to Excel
output_file = 'data/company_data.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Companies', index=False)

print(f"✓ Created: {output_file}")
print(f"✓ Companies: {len(data)}")
print(f"✓ Tickers: {', '.join([row['Ticker'] for row in data])}")
print()
print("File ready to use!")
print(f"  Backend can now read from: backend/data/company_data.xlsx")
print()
print("Next steps:")
print("  1. cd backend")
print("  2. uvicorn main:app --port 8000")
print("  3. curl http://127.0.0.1:8000/merton/AAPL")
