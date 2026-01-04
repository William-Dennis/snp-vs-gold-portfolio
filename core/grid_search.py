"""Grid search functionality for parameter optimization."""

import numpy as np
import pandas as pd

from .database import (
    get_cached_result,
    get_db_connection,
    make_param_hash,
    save_results_batch,
)
from .metrics import calculate_metrics
from .strategy import run_strategy

STEPS = 201


def run_grid_search(
    df: pd.DataFrame,
    rebalance_ratios: np.ndarray = np.linspace(0.01, 0.11, STEPS),
    t1_ratios: np.ndarray = np.linspace(0, 1.0, STEPS),
    ticker1: str = "SPY",
    ticker2: str = "GLD",
    starting_cash: float = 10_000,
    db_path: str = "results_cache.db",
    trade_cost: float = 0.0,
    risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    """Run grid search over parameter space with caching."""
    conn = get_db_connection(db_path)
    start_date = df.index[0].strftime("%Y-%m-%d")
    end_date = df.index[-1].strftime("%Y-%m-%d")

    results, to_insert = _process_grid(
        conn,
        df,
        start_date,
        end_date,
        rebalance_ratios,
        t1_ratios,
        ticker1,
        ticker2,
        starting_cash,
        trade_cost,
        risk_free_rate,
    )

    save_results_batch(conn, to_insert)
    conn.close()

    return pd.DataFrame(results)


def _process_grid(
    conn,
    df,
    start_date,
    end_date,
    rebalance_ratios,
    t1_ratios,
    ticker1,
    ticker2,
    starting_cash,
    trade_cost,
    risk_free_rate,
) -> "Tuple[list[dict], list[tuple]]":
    """Process all parameter combinations in grid."""
    results = []
    to_insert = []

    for rebalance_rate in rebalance_ratios:
        for t1_ratio in t1_ratios:
            result_dict, insert_tuple = _process_params(
                conn,
                df,
                start_date,
                end_date,
                rebalance_rate,
                t1_ratio,
                ticker1,
                ticker2,
                starting_cash,
                trade_cost,
                risk_free_rate,
            )
            results.append(result_dict)
            if insert_tuple:
                to_insert.append(insert_tuple)

    return results, to_insert


def _compute_strategy_metrics(
    df,
    ticker1,
    ticker2,
    t1_ratio,
    rebalance_rate,
    starting_cash,
    trade_cost,
    risk_free_rate,
) -> "Dict":
    """Compute strategy result and metrics."""
    result = run_strategy(
        df, ticker1, ticker2, t1_ratio, rebalance_rate, starting_cash, trade_cost
    )
    metrics = calculate_metrics(
        result["total_cash_value"].values,
        df.index[0],
        df.index[-1],
        int(np.sum(result["rebalance"] != 0)),
        risk_free_rate,
    )
    return metrics


def _process_params(
    conn,
    df,
    start_date,
    end_date,
    rebalance_rate,
    t1_ratio,
    ticker1,
    ticker2,
    starting_cash,
    trade_cost,
    risk_free_rate,
):
    """Process single parameter combination."""
    hash_key = make_param_hash(
        start_date,
        end_date,
        ticker1,
        ticker2,
        t1_ratio,
        rebalance_rate,
        starting_cash,
        trade_cost,
        risk_free_rate,
    )

    cached = get_cached_result(conn, hash_key)
    if cached:
        result_dict = {"rebalance_rate": rebalance_rate, "t1_ratio": t1_ratio, **cached}
        return result_dict, None

    metrics = _compute_strategy_metrics(
        df,
        ticker1,
        ticker2,
        t1_ratio,
        rebalance_rate,
        starting_cash,
        trade_cost,
        risk_free_rate,
    )

    result_dict = {"rebalance_rate": rebalance_rate, "t1_ratio": t1_ratio, **metrics}
    insert_tuple = (
        hash_key,
        start_date,
        end_date,
        ticker1,
        ticker2,
        t1_ratio,
        rebalance_rate,
        starting_cash,
        trade_cost,
        risk_free_rate,
        *metrics.values(),
    )

    return result_dict, insert_tuple
