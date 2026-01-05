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


def calculate_max_rolling_drawdown(series: pd.Series, window: int) -> float:
    """Calculate maximum drawdown over a rolling window."""
    rolling_returns = series.pct_change(window).dropna()
    return rolling_returns.min() if len(rolling_returns) > 0 else 0.0


def calculate_metrics(
    total_cash: np.ndarray,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    rebalance_count: int,
) -> Dict:
    """Calculate strategy performance metrics."""
    series = pd.Series(total_cash)
    n_years = (end_date - start_date).days / 365.25
    cagr = (total_cash[-1] / total_cash[0]) ** (1 / n_years) - 1

    return {
        "sharpe": calculate_sharpe(series),
        "num_rebalances": rebalance_count,
        "max_drawdown": series.pct_change().min(),
        "max_weekly_drawdown": calculate_max_rolling_drawdown(series, 5), # TODO: Use a constant e.g. WEEKLY_WINDOW
        "max_monthly_drawdown": calculate_max_rolling_drawdown(series, 21), # TODO: Use a constant e.g. MONTHLY_WINDOW
        "cagr": cagr,
    }
