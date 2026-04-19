# ✅ Excel Source Setup - Your Data, Zero API Calls

## **Quick Setup (5 minutes)**

### Step 1: Create Folder
```bash
mkdir backend/data
```

### Step 2: Create Excel File

**File:** `backend/data/company_data.xlsx`

**Sheet Name:** `Companies` (important!)

**Columns:**

| A | B | C | D | E | F | G | H | I | ... |
|---|---|---|---|---|---|---|---|---|-----|
| Ticker | Company Name | Sector | Market Cap (USD) | Total Debt (USD) | Current Price | Day1 Price | Day2 Price | Day3 Price | ... |
| AAPL | Apple Inc. | Technology | 3.83E+12 | 90509000000 | 189.95 | 197.29 | 201.64 | 201.26 | ... |
| MSFT | Microsoft | Technology | 2.99E+12 | 62150000000 | 423.04 | 420.15 | 421.03 | 419.87 | ... |
| JPM | JPMorgan Chase | Finance | 6.15E+11 | 156892000000 | 165.42 | 167.24 | 166.89 | 168.15 | ... |

### Step 3: Add Your Companies

- **Ticker**: Stock symbol (AAPL, MSFT, JPM, etc.)
- **Company Name**: Full name (Apple Inc., Microsoft Corp., etc.)
- **Sector**: Industry (Technology, Finance, Healthcare, etc.)
- **Market Cap (USD)**: Total market capitalization in USD
- **Total Debt (USD)**: Total debt from balance sheet
- **Current Price**: Today's stock price (optional - for reference)
- **Day1 Price onwards**: Historical daily closing prices (oldest first!)
  - Need at least 20 prices (20 days minimum)
  - 365 prices ideal (1 year of data)

### Step 4: Test It

```bash
cd backend
python -c "
from services.excel_source import get_excel_source

excel = get_excel_source('data/company_data.xlsx')
print('Tickers in Excel:', excel.get_all_tickers())
data = excel.get_ticker_data('AAPL')
print('AAPL:', data['company_name'])
print('Volatility:', f\"{data['equity_volatility']:.2%}\")
"
```

### Step 5: Start Backend

```bash
uvicorn main:app --port 8000
```

### Step 6: Test API

```bash
curl http://127.0.0.1:8000/merton/AAPL
```

Should return Merton analysis with data from your Excel file!

---

## **Excel Format Tips**

### Price Data Format

- **Column G:** Day 1 (oldest price, typically ~365 days ago)
- **Column H:** Day 2 (365-1 days ago)
- ...
- **Column AQ:** Day 365 (most recent price, today)

Or whatever number of days you have (minimum 20).

### Numbers Format

```excel
Market Cap: Use scientific notation for billions
  Example: 3,828,515,864,576 or 3.83E+12 (both OK)

Total Debt: Regular number (billions or exact)
  Example: 90,509,000,000

Prices: Decimal numbers
  Example: 189.95
```

### Example Data

```
TICKER | Company | Sector | Market_Cap | Debt | Price | Price_Day1 | Price_Day2 | ... | Price_Day365
AAPL   | Apple   | Tech   | 3.83E+12   | 9E10 | 189.95 | 197.29    | 201.64     | ... | 195.36
MSFT   | Microsoft| Tech  | 2.99E+12   | 6E10 | 423.04 | 420.15    | 421.03     | ... | 418.27
```

---

## **How It Works**

```
1. You maintain Excel file with company data
   backend/data/company_data.xlsx

2. Backend reads from Excel
   (zero API calls!)

3. Data is cached in memory for 15 minutes
   (ultra-fast responses)

4. Endpoints return Merton analysis
   /merton/AAPL → Uses your Excel data
```

---

## **Example Excel File (Minimal)**

Let's say you want 3 companies with 20 days of price data:

```
| A    | B            | C         | D        | E       | F    | G    | H    | ...  | Z    |
|------|--------------|-----------|----------|---------|------|------|------|------|------|
| AAPL | Apple Inc.   | Tech      | 3.83E+12 | 9.05E10 | 190  | 197  | 202  | ...  | 195  |
| MSFT | Microsoft    | Tech      | 2.99E+12 | 6.2E10  | 423  | 420  | 421  | ...  | 418  |
| JPM  | JPMorgan     | Finance   | 6.15E+11 | 1.57E11 | 165  | 167  | 167  | ...  | 164  |
```

That's it! 3 companies, 20 price points each = 60 rows + header.

---

## **Common Issues & Fixes**

### "Excel file not found"

**Fix:** Create file at `backend/data/company_data.xlsx`

### "Sheet 'Companies' not found"

**Fix:** Make sure sheet is named exactly `Companies` (capitalization matters)

### "Insufficient price data"

**Fix:** Need at least 20 prices per ticker. Add more columns with daily prices.

### "TypeError: unable to parse"

**Fix:** Check column names are exact:
- `Ticker`
- `Company Name`
- `Sector`
- `Market Cap (USD)`
- `Total Debt (USD)`

(Capitalization and spaces matter!)

---

## **Advantages**

✅ **Zero API calls** - You control all data
✅ **No rate limiting** - Ever
✅ **Instant responses** - <100ms cached
✅ **Offline capable** - No internet needed
✅ **Full data control** - You verify accuracy
✅ **Easy testing** - Use test data in Excel

---

## **Next Steps**

1. Create `backend/data/company_data.xlsx`
2. Add sheet named `Companies`
3. Fill in your companies with data
4. Save file
5. Test: `python -c "from services.excel_source import get_excel_source; print(get_excel_source().get_all_tickers())"`
6. Start backend: `uvicorn main:app --port 8000`
7. Call API: `curl http://127.0.0.1:8000/merton/AAPL`

Done! 🚀
