"""Data downloading and processing utilities."""

import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime


# Fixed end date for all data
FIXED_END_DATE = "2025-12-31"

# Available periods with their years back from end date
AVAILABLE_PERIODS = {
    "1yr": 1,
    "3yr": 3,
    "5yr": 5,
    "10yr": 10,
    "15yr": 15,
    "20yr": 20,
}


@st.cache_data()
def get_daily_data(ticker_symbol: str, start_date: str, end_date: str = FIXED_END_DATE):
    """Get daily close prices for a ticker symbol with fixed date range."""
    ticker = yf.Ticker(ticker_symbol)
    close_series = ticker.history(start=start_date, end=end_date)["Close"]
    close_series.name = ticker_symbol
    return close_series


def calculate_start_date(period: str) -> str:
    """Calculate start date based on period and fixed end date."""
    if period not in AVAILABLE_PERIODS:
        raise ValueError(f"Period must be one of {list(AVAILABLE_PERIODS.keys())}")
    
    years_back = AVAILABLE_PERIODS[period]
    end_date = datetime.strptime(FIXED_END_DATE, "%Y-%m-%d")
    start_year = end_date.year - years_back
    start_date = end_date.replace(year=start_year)
    return start_date.strftime("%Y-%m-%d")


@st.cache_data()
def get_two_series(ticker1: str = "SPY", ticker2: str = "GLD", period: str = "10yr"):
    """Get normalized price series for two tickers with data length checking."""
    start_date = calculate_start_date(period)
    
    s1 = get_daily_data(ticker1, start_date)
    s2 = get_daily_data(ticker2, start_date)
    
    # Check if we have any data
    if len(s1) == 0 or len(s2) == 0:
        st.error(f"Error: No data available for {ticker1 if len(s1) == 0 else ticker2} in the period {period}")
        st.stop()
    
    # Check if we have sufficient data
    min_required_days = AVAILABLE_PERIODS[period] * 252  # Approximate trading days per year
    if len(s1) < min_required_days * 0.8 or len(s2) < min_required_days * 0.8:
        st.warning(f"Warning: Insufficient data for {period} period. Using available data from {s1.index[0].strftime('%Y-%m-%d')} to {FIXED_END_DATE}")

    # normalise
    s1 = s1 / s1.values[0]
    s2 = s2 / s2.values[0]

    joined = pd.concat([s1, s2], axis=1).dropna()
    return joined
