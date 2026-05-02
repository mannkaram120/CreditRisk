"""
Excel Data Source - Read company data from Excel file.

User maintains an Excel file with company data.
Backend reads from it - zero API calls needed!
"""

import pandas as pd
import numpy as np
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class ExcelDataSource:
    """Read company data from Excel file."""
    
    def __init__(self, filepath: str = 'data/company_data.xlsx'):
        self.filepath = filepath
        self.df = None
        self.load_file()
    
    def load_file(self):
        """Load Excel file into memory."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(
                f"Excel file not found: {self.filepath}\n"
                f"Please create it at: {self.filepath}\n"
                f"Required columns: Ticker, Company Name, Sector, Market Cap (USD), "
                f"Total Debt (USD), Current Price, [Daily prices...]"
            )
        
        try:
            self.df = pd.read_excel(self.filepath, sheet_name='Companies')
            logger.info(f"Loaded Excel file with {len(self.df)} companies")
            self._validate_columns()
        except Exception as e:
            raise RuntimeError(f"Error loading Excel file: {e}")
    
    def _validate_columns(self):
        """Validate Excel has required columns."""
        required = ['Ticker', 'Company Name', 'Sector', 'Market Cap (USD)', 'Total Debt (USD)']
        missing = [col for col in required if col not in self.df.columns]
        if missing:
            raise ValueError(f"Excel missing required columns: {missing}")
    
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
        
        # Get closing prices from columns after the fixed ones
        # Columns: Ticker(0), Company Name(1), Sector(2), Market Cap(3), Total Debt(4), Price(5), ...prices...
        closing_prices = []
        
        # Start from column 6 (column index 6 = column G in Excel)
        for col_idx in range(6, len(self.df.columns)):
            try:
                price = float(row.iloc[col_idx])
                if not np.isnan(price) and price > 0:
                    closing_prices.append(price)
            except (ValueError, TypeError):
                continue
        
        # Validate we have enough data
        if len(closing_prices) < 20:
            raise ValueError(
                f"Insufficient price data for {ticker_upper}. "
                f"Need at least 20 daily prices, got {len(closing_prices)}.\n"
                f"Please add more price columns to Excel starting from column G."
            )
        
        # Calculate equity volatility
        arr = np.array(closing_prices)
        log_ret = np.diff(np.log(arr))
        equity_volatility = float(np.std(log_ret, ddof=1) * np.sqrt(252))
        
        logger.info(
            f"Loaded {ticker_upper}: {len(closing_prices)} prices, "
            f"vol={equity_volatility:.2%}, market_cap=${float(row['Market Cap (USD)']):,.0f}"
        )
        
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
        """Reload Excel file (call if file was updated externally)."""
        self.load_file()
        logger.info("Excel file reloaded")


# Global instance
_excel_source: Optional[ExcelDataSource] = None


def get_excel_source(filepath: str = 'data/company_data.xlsx') -> ExcelDataSource:
    """Get or create Excel data source instance."""
    global _excel_source
    if _excel_source is None:
        _excel_source = ExcelDataSource(filepath)
    return _excel_source


def reload_excel_source():
    """Reload Excel data source (useful after updating file)."""
    global _excel_source
    if _excel_source:
        _excel_source.reload()
