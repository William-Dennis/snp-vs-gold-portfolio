"""Performance metrics calculations."""

from typing import Dict

import numpy as np
import pandas as pd


def calculate_sharpe(series: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Calculate annualized Sharpe ratio from a price series."""
    returns = series.pct_change().dropna()
    excess_returns = returns - risk_free_rate / 252

    std_ret = excess_returns.std()
    if std_ret == 0:
        return 0.0

    sharpe_ratio = (excess_returns.mean() / std_ret) * np.sqrt(252)
    return sharpe_ratio


def calculate_max_drawdown(series: pd.Series) -> float:
    """Calculate maximum drawdown from a price series (peak-to-trough decline)."""
    cumulative_max = series.cummax()
    drawdown = (series - cumulative_max) / cumulative_max
    return drawdown.min()


def calculate_max_weekly_drawdown(series: pd.Series) -> float:
    """Calculate maximum weekly drawdown."""
    # Resample to weekly frequency, taking the last value of each week
    weekly_series = series.resample('W').last()
    return calculate_max_drawdown(weekly_series)


def calculate_max_monthly_drawdown(series: pd.Series) -> float:
    """Calculate maximum monthly drawdown."""
    # Resample to monthly frequency, taking the last value of each month
    monthly_series = series.resample('ME').last()
    return calculate_max_drawdown(monthly_series)


def calculate_metrics(
    total_cash: np.ndarray,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    rebalance_count: int,
) -> Dict:
    """Calculate strategy performance metrics."""
    # Create a proper time-indexed series for time-based resampling
    date_range = pd.date_range(start=start_date, end=end_date, periods=len(total_cash))
    series = pd.Series(total_cash, index=date_range)
    n_years = (end_date - start_date).days / 365.25
    cagr = (total_cash[-1] / total_cash[0]) ** (1 / n_years) - 1

    return {
        "sharpe": calculate_sharpe(series),
        "num_rebalances": rebalance_count,
        "max_drawdown": calculate_max_drawdown(series),
        "max_weekly_drawdown": calculate_max_weekly_drawdown(series),
        "max_monthly_drawdown": calculate_max_monthly_drawdown(series),
        "cagr": cagr,
    }
