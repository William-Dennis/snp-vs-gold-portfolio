"""SPY vs GLD Portfolio Analysis - Streamlit App."""

import streamlit as st

st.set_page_config(layout="wide", page_title="SPY vs GLD Analysis")

from core.app_helpers import (
    load_data_and_search,
    run_strategy_with_metrics,
    get_best_strategies,
)
from core.metrics import calculate_metrics
from core.ui_components import (
    render_strategy_controls,
    render_performance_chart,
    render_metrics_table,
    render_heatmaps,
)

st.title("SPY vs GLD Portfolio Analysis")

st.markdown("""
Explore optimal rebalancing strategies for a two-asset portfolio.
Adjust your strategy parameters and compare against grid search results.
""")

# Load data and run grid search
data, grid_search_data = load_data_and_search()

# Find optimal strategies
best_strategies = get_best_strategies(grid_search_data)
best_sharpe = best_strategies["sharpe"]
best_cagr = best_strategies["cagr"]
best_drawdown = best_strategies["drawdown"]
best_weekly_drawdown = best_strategies["weekly_drawdown"]
best_monthly_drawdown = best_strategies["monthly_drawdown"]

# Render strategy controls and get selected parameters
strategy_t1_ratio, strategy_rebalance = render_strategy_controls(
    best_sharpe, best_cagr, best_drawdown, best_weekly_drawdown, best_monthly_drawdown
)

# Relative metrics toggle
use_relative = st.toggle("Show Relative Metrics", value=False)

# Run strategy with selected parameters
strategy_result, strategy_metrics = run_strategy_with_metrics(
    data, "SPY", "GLD", strategy_t1_ratio, strategy_rebalance, 10_000
)

# Calculate baseline metrics
spy_metrics = calculate_metrics(data["SPY"].values, data.index[0], data.index[-1], 0)
gld_metrics = calculate_metrics(data["GLD"].values, data.index[0], data.index[-1], 0)

# Render UI components
render_performance_chart(data, strategy_result)

render_metrics_table(
    strategy_t1_ratio,
    strategy_rebalance,
    strategy_metrics,
    best_sharpe,
    best_cagr,
    best_drawdown,
    best_weekly_drawdown,
    best_monthly_drawdown,
    spy_metrics,
    gld_metrics,
)

render_heatmaps(grid_search_data, strategy_metrics, use_relative)
