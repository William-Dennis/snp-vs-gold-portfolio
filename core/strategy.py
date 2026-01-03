"""Portfolio rebalancing strategy execution."""

from typing import Tuple

import numba
import numpy as np
import pandas as pd


@numba.njit
def run_strategy_numba(
    t1_prices: np.ndarray,
    t2_prices: np.ndarray,
    t1_ratio: float,
    rebalance_rate: float,
    starting_cash: float,
) -> np.ndarray:
    """Execute rebalancing strategy (numba-optimized)."""
    n = len(t1_prices)
    t1_cash = np.zeros(n)
    t2_cash = np.zeros(n)
    rebalance = np.zeros(n)

    t1_cash[0] = starting_cash * t1_ratio
    t2_cash[0] = starting_cash * (1 - t1_ratio)

    for i in range(1, n):
        t1_cash[i], t2_cash[i], rebalance[i] = _process_timestep(
            t1_prices[i - 1 : i + 1],
            t2_prices[i - 1 : i + 1],
            t1_cash[i - 1],
            t2_cash[i - 1],
            t1_ratio,
            rebalance_rate,
        )

    total_cash = t1_cash + t2_cash
    return np.column_stack((t1_cash, t2_cash, total_cash, rebalance))


@numba.njit
def _process_timestep(
    t1_prices: np.ndarray,
    t2_prices: np.ndarray,
    t1_prev: float,
    t2_prev: float,
    t1_ratio: float,
    rebalance_rate: float,
) -> Tuple:
    """Process single timestep: returns, rebalancing."""
    t1_ret = (t1_prices[1] - t1_prices[0]) / t1_prices[0] if t1_prices[0] != 0 else 0.0
    t2_ret = (t2_prices[1] - t2_prices[0]) / t2_prices[0] if t2_prices[0] != 0 else 0.0

    t1_cash = t1_prev * (1 + t1_ret)
    t2_cash = t2_prev * (1 + t2_ret)

    total = t1_cash + t2_cash
    t1_pct = t1_cash / total if total != 0 else 0.0

    rebal = 0.0
    if rebalance_rate > 0:
        if t1_pct > t1_ratio + rebalance_rate:
            rebal, t1_cash, t2_cash = _rebalance_sell_t1(
                t1_cash, t2_cash, t1_pct, t1_ratio
            )
        elif t1_pct < t1_ratio - rebalance_rate:
            rebal, t1_cash, t2_cash = _rebalance_sell_t2(
                t1_cash, t2_cash, t1_pct, t1_ratio
            )

    return t1_cash, t2_cash, rebal


@numba.njit
def _rebalance_sell_t1(
    t1_cash: float, t2_cash: float, t1_pct: float, t1_ratio: float
) -> Tuple:
    """Rebalance by selling asset 1."""
    delta = t1_pct / t1_ratio
    sell_amount = t1_cash - (t1_cash / delta)
    return sell_amount, t1_cash - sell_amount, t2_cash + sell_amount


@numba.njit
def _rebalance_sell_t2(
    t1_cash: float, t2_cash: float, t1_pct: float, t1_ratio: float
) -> Tuple:
    """Rebalance by selling asset 2."""
    delta = (1 - t1_pct) / (1 - t1_ratio)
    sell_amount = t2_cash - (t2_cash / delta)
    return -sell_amount, t1_cash + sell_amount, t2_cash - sell_amount


def run_strategy(
    df: pd.DataFrame,
    ticker1: str = "SPY",
    ticker2: str = "GLD",
    t1_ratio: float = 0.5,
    rebalance_rate: float = 0.05,
    starting_cash: float = 10_000,
) -> pd.DataFrame:
    """Run rebalancing strategy on price data."""
    result = run_strategy_numba(
        df[ticker1].values, df[ticker2].values, t1_ratio, rebalance_rate, starting_cash
    )

    output_df = df.copy()
    output_df[f"{ticker1}_cash_value"] = result[:, 0]
    output_df[f"{ticker2}_cash_value"] = result[:, 1]
    output_df["total_cash_value"] = result[:, 2]
    output_df["rebalance"] = result[:, 3]

    return output_df
