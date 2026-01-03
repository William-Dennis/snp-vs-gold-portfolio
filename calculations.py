"""Portfolio rebalancing strategy with grid search and result caching."""

import hashlib
import json
import sqlite3
from typing import Dict, Optional, Tuple

import numba
import numpy as np
import pandas as pd

STEPS = 201

# ============================================================================
# PERFORMANCE METRICS
# ============================================================================


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
) -> Dict:
    """Calculate strategy performance metrics."""
    series = pd.Series(total_cash)
    n_years = (end_date - start_date).days / 365.25
    cagr = (total_cash[-1] / total_cash[0]) ** (1 / n_years) - 1

    return {
        "sharpe": calculate_sharpe(series),
        "num_rebalances": rebalance_count,
        "max_drawdown": series.pct_change().min(),
        "cagr": cagr,
    }


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================


def get_db_connection(db_path: str = "results_cache.db") -> sqlite3.Connection:
    """Create database connection and initialize schema."""
    conn = sqlite3.connect(db_path)
    _create_results_table(conn)
    return conn


def _create_results_table(conn: sqlite3.Connection) -> None:
    """Create results table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS strategy_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE,
            start_date TEXT,
            end_date TEXT,
            ticker1 TEXT,
            ticker2 TEXT,
            t1_ratio REAL,
            rebalance_rate REAL,
            starting_cash REAL,
            sharpe REAL,
            num_rebalances INTEGER,
            max_drawdown REAL,
            cagr REAL
        )
    """)
    conn.commit()


def make_param_hash(
    start_date: str,
    end_date: str,
    ticker1: str,
    ticker2: str,
    t1_ratio: float,
    rebalance_rate: float,
    starting_cash: float,
) -> str:
    """Generate unique hash for parameter combination."""
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "ticker1": ticker1,
        "ticker2": ticker2,
        "t1_ratio": t1_ratio,
        "rebalance_rate": rebalance_rate,
        "starting_cash": starting_cash,
    }
    param_str = json.dumps(params, sort_keys=True)
    return hashlib.sha256(param_str.encode()).hexdigest()


def get_cached_result(conn: sqlite3.Connection, hash_key: str) -> Optional[Dict]:
    """Retrieve cached results for given parameter hash."""
    cur = conn.execute(
        "SELECT sharpe, num_rebalances, max_drawdown, cagr "
        "FROM strategy_results WHERE hash = ?",
        (hash_key,),
    )
    row = cur.fetchone()

    if row:
        return {
            "sharpe": float(row[0]),
            "num_rebalances": int(row[1]),
            "max_drawdown": float(row[2]),
            "cagr": float(row[3]),
        }
    return None


def save_results_batch(conn: sqlite3.Connection, results: list) -> None:
    """Save multiple results to database in batch."""
    if not results:
        return

    conn.executemany(
        """
        INSERT OR IGNORE INTO strategy_results
        (hash, start_date, end_date, ticker1, ticker2, t1_ratio, 
         rebalance_rate, starting_cash, sharpe, num_rebalances, 
         max_drawdown, cagr)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        results,
    )
    conn.commit()


# ============================================================================
# STRATEGY EXECUTION
# ============================================================================


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


# ============================================================================
# GRID SEARCH
# ============================================================================


def run_grid_search(
    df: pd.DataFrame,
    rebalance_ratios: np.ndarray = np.linspace(0.01, 0.11, STEPS),
    t1_ratios: np.ndarray = np.linspace(0, 1.0, STEPS),
    ticker1: str = "SPY",
    ticker2: str = "GLD",
    starting_cash: float = 10_000,
    db_path: str = "results_cache.db",
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
):
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
            )

            results.append(result_dict)
            if insert_tuple:
                to_insert.append(insert_tuple)

    return results, to_insert


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
):
    """Process single parameter combination."""
    hash_key = make_param_hash(
        start_date, end_date, ticker1, ticker2, t1_ratio, rebalance_rate, starting_cash
    )

    cached = get_cached_result(conn, hash_key)
    if cached:
        result_dict = {"rebalance_rate": rebalance_rate, "t1_ratio": t1_ratio, **cached}
        return result_dict, None

    result = run_strategy(df, ticker1, ticker2, t1_ratio, rebalance_rate, starting_cash)
    metrics = calculate_metrics(
        result["total_cash_value"].values,
        df.index[0],
        df.index[-1],
        int(np.sum(result["rebalance"] != 0)),
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
        *metrics.values(),
    )

    return result_dict, insert_tuple
