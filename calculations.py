import pandas as pd
import numpy as np
import numba


def calculate_sharpe(series: pd.Series, risk_free_rate=0.0):
    returns = series.pct_change().dropna()
    excess_returns = returns - risk_free_rate / 252  # daily risk-free
    mean_ret = excess_returns.mean()
    std_ret = excess_returns.std()

    if std_ret == 0:
        return 0.0

    sharpe_ratio = mean_ret / std_ret * np.sqrt(252)
    return sharpe_ratio


def run_grid_search(
    df: pd.DataFrame,
    rebalance_ratios=np.linspace(0.01, 0.05, 101),
    t1_ratios=np.linspace(0.5, 1.0, 101),
    ticker1: str = "SPY",
    ticker2: str = "GLD",
    starting_cash: float = 10_000,
):
    results = []

    for rebalance_rate in rebalance_ratios:
        for t1_ratio in t1_ratios:
            result = run_strategy(
                df, ticker1=ticker1, ticker2=ticker2, t1_ratio=t1_ratio, rebalance_rate=rebalance_rate, starting_cash=starting_cash
            )

            total_cash = result["total_cash_value"].values

            sharpe = calculate_sharpe(result["total_cash_value"])
            number_of_rebalances = np.sum(result["rebalance"] != 0)
            max_drawdown = result["total_cash_value"].pct_change().min()

            start_value = total_cash[0]
            end_value = total_cash[-1]
            n_years = (df.index[-1] - df.index[0]).days / 365.25
            cagr = (end_value / start_value) ** (1 / n_years) - 1

            results.append(
                {
                    "rebalance_rate": rebalance_rate,
                    "t1_ratio": t1_ratio,
                    "sharpe": sharpe,
                    "num_rebalances": number_of_rebalances,
                    "max_drawdown": max_drawdown,
                    "cagr": cagr,
                }
            )

    return pd.DataFrame(results)


@numba.njit
def run_strategy_numba(
    t1_prices: np.ndarray,
    t2_prices: np.ndarray,
    t1_ratio: float,
    rebalance_rate: float,
    starting_cash: float,
):
    n = len(t1_prices)
    # assert t1_ratio + rebalance_rate < 1
    # assert t1_ratio - rebalance_rate > 0

    t1_cash = np.zeros(n, dtype=np.float64)
    t2_cash = np.zeros(n, dtype=np.float64)
    rebalance = np.zeros(n, dtype=np.float64)

    t1_cash[0] = starting_cash * t1_ratio
    t2_cash[0] = starting_cash * (1 - t1_ratio)

    for i in range(1, n):
        t1_ret = (t1_prices[i] - t1_prices[i - 1]) / t1_prices[i - 1] if t1_prices[i - 1] != 0 else 0.0
        t2_ret = (t2_prices[i] - t2_prices[i - 1]) / t2_prices[i - 1] if t2_prices[i - 1] != 0 else 0.0

        t1_cash[i] = t1_cash[i - 1] * (1 + t1_ret)
        t2_cash[i] = t2_cash[i - 1] * (1 + t2_ret)

        total_cash = t1_cash[i] + t2_cash[i]
        t1_percentage = t1_cash[i] / total_cash if total_cash != 0 else 0.0

        if t1_percentage > t1_ratio + rebalance_rate:
            t1_delta = t1_percentage / t1_ratio
            t1_sell_amount = t1_cash[i] - (t1_cash[i] / t1_delta)
            t1_cash[i] -= t1_sell_amount
            t2_cash[i] += t1_sell_amount
            rebalance[i] = t1_sell_amount

        elif t1_percentage < t1_ratio - rebalance_rate:
            t2_delta = (1 - t1_percentage) / (1 - t1_ratio)
            t2_sell_amount = t2_cash[i] - (t2_cash[i] / t2_delta)
            t1_cash[i] += t2_sell_amount
            t2_cash[i] -= t2_sell_amount
            rebalance[i] = -t2_sell_amount

    total_cash = t1_cash + t2_cash
    out = np.empty((n, 4))
    out[:, 0] = t1_cash
    out[:, 1] = t2_cash
    out[:, 2] = total_cash
    out[:, 3] = rebalance

    return out


def run_strategy(
    df: pd.DataFrame,
    ticker1: str = "SPY",
    ticker2: str = "GLD",
    t1_ratio: float = 0.5,
    rebalance_rate: float = 0.05,
    starting_cash: float = 10_000,
):
    t1_prices = df[ticker1].values
    t2_prices = df[ticker2].values

    out = run_strategy_numba(t1_prices, t2_prices, t1_ratio, rebalance_rate, starting_cash)

    df = df.copy()
    df[ticker1 + "_cash_value"] = out[:, 0]
    df[ticker2 + "_cash_value"] = out[:, 1]
    df["total_cash_value"] = out[:, 2]
    df["rebalance"] = out[:, 3]

    return df
