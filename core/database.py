"""Database operations for caching strategy results."""

import hashlib
import json
import sqlite3
from typing import Dict, Optional


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
            max_weekly_drawdown REAL,
            max_monthly_drawdown REAL,
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
        "SELECT sharpe, num_rebalances, max_drawdown, max_weekly_drawdown, max_monthly_drawdown, cagr "
        "FROM strategy_results WHERE hash = ?",
        (hash_key,),
    )
    row = cur.fetchone()

    if row:
        return {
            "sharpe": float(row[0]),
            "num_rebalances": int(row[1]),
            "max_drawdown": float(row[2]),
            "max_weekly_drawdown": float(row[3]),
            "max_monthly_drawdown": float(row[4]),
            "cagr": float(row[5]),
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
         max_drawdown, max_weekly_drawdown, max_monthly_drawdown, cagr)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        results,
    )
    conn.commit()
