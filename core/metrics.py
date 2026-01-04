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


def calculate_metrics(
    total_cash: np.ndarray,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    rebalance_count: int,
    risk_free_rate: float = 0.0,
) -> Dict:
    """Calculate strategy performance metrics."""
    series = pd.Series(total_cash)
    n_years = (end_date - start_date).days / 365.25
    cagr = (total_cash[-1] / total_cash[0]) ** (1 / n_years) - 1

    return {
        "sharpe": calculate_sharpe(series, risk_free_rate),
        "num_rebalances": rebalance_count,
        "max_drawdown": series.pct_change().min(),
        "cagr": cagr,
    }
