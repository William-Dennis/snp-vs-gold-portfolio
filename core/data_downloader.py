import yfinance as yf
import pandas as pd
import streamlit as st


@st.cache_data()
def get_daily_data(ticker_symbol: str, period="10y"):
    ticker = yf.Ticker(ticker_symbol)
    close_series = ticker.history(period=period)["Close"]
    close_series.name = ticker_symbol
    return close_series


def get_two_series(ticker1: str = "SPY", ticker2: str = "GLD", period="10y"):
    s1 = get_daily_data(ticker1, period)
    s2 = get_daily_data(ticker2, period)

    # normalise
    s1 = s1 / s1.values[0]
    s2 = s2 / s2.values[0]

    joined = pd.concat([s1, s2], axis=1).dropna()
    return joined
