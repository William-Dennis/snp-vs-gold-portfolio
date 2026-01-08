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
) -> tuple[pd.DataFrame, dict]:
    """Run strategy and calculate metrics in one call."""
    result = run_strategy(
        data, ticker1, ticker2, t1_ratio, rebalance_rate, starting_cash
    )
    metrics = calculate_metrics(
        result["total_cash_value"].values,
        data.index[0],
        data.index[-1],
        int(np.sum(result["rebalance"] != 0)),
    )
    return result, metrics


@st.cache_data
def load_data(period: str = "10yr"):
    """Load price data (cached for performance)."""
    return get_two_series(period=period)


@st.cache_data
def load_grid_search_cached(period: str = "10yr"):
    """Run and cache grid search for a period."""
    data = get_two_series(period=period)
    return run_grid_search(data)


def load_data_and_search(period: str = "10yr", fast_mode: bool = False):
    """Load data and conditionally run grid search based on fast mode."""
    data = load_data(period=period)

    if fast_mode:
        # In fast mode, return empty grid results to skip expensive computation
        # Create empty dataframe with expected columns
        grid_results = pd.DataFrame(
            columns=[
                "rebalance_rate",
                "t1_ratio",
                "sharpe",
                "cagr",
                "max_drawdown",
                "num_rebalances",
            ]
        )
    else:
        # Normal mode: run grid search (will use cache if available)
        grid_results = load_grid_search_cached(period=period)

    return data, grid_results


def get_best_strategies(grid_search_data: pd.DataFrame) -> dict:
    """Extract best strategies from grid search results."""
    if grid_search_data.empty:
        # Return placeholder values when grid search is empty (fast mode)
        placeholder = {
            "t1_ratio": 0.5,
            "rebalance_rate": 0.06,
            "sharpe": 0.0,
            "cagr": 0.0,
            "max_drawdown": 0.0,
            "num_rebalances": 0,
        }
        return {
            "sharpe": placeholder,
            "cagr": placeholder,
            "drawdown": placeholder,
        }

    return {
        "sharpe": grid_search_data.nlargest(1, "sharpe").iloc[0],
        "cagr": grid_search_data.nlargest(1, "cagr").iloc[0],
        "drawdown": grid_search_data.nlargest(1, "max_drawdown").iloc[0],
    }
