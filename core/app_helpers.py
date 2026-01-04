"""UI components and helper functions for the Streamlit app."""

import streamlit as st
import pandas as pd
import numpy as np

from .data_downloader import get_two_series
from .grid_search import run_grid_search
from .strategy import run_strategy
from .metrics import calculate_metrics


def run_strategy_with_metrics(
    data: pd.DataFrame,
    ticker1: str,
    ticker2: str,
    t1_ratio: float,
    rebalance_rate: float,
    starting_cash: float,
    trade_cost: float = 0.0,
    risk_free_rate: float = 0.0,
) -> tuple[pd.DataFrame, dict]:
    """Run strategy and calculate metrics in one call."""
    result = run_strategy(
        data, ticker1, ticker2, t1_ratio, rebalance_rate, starting_cash, trade_cost
    )
    metrics = calculate_metrics(
        result["total_cash_value"].values,
        data.index[0],
        data.index[-1],
        int(np.sum(result["rebalance"] != 0)),
        risk_free_rate,
    )
    return result, metrics


@st.cache_data
def load_data_and_search(
    period: str = "10yr",
    final_year: int = 2025,
    trade_cost: float = 0.0,
    risk_free_rate: float = 0.0,
):
    """Load data and run grid search (cached for performance)."""
    data = get_two_series(period=period, final_year=final_year)
    grid_results = run_grid_search(
        data, trade_cost=trade_cost, risk_free_rate=risk_free_rate
    )
    return data, grid_results


def get_best_strategies(grid_search_data: pd.DataFrame) -> dict:
    """Extract best strategies from grid search results."""
    return {
        "sharpe": grid_search_data.nlargest(1, "sharpe").iloc[0],
        "cagr": grid_search_data.nlargest(1, "cagr").iloc[0],
        "drawdown": grid_search_data.nlargest(1, "max_drawdown").iloc[0],
    }
