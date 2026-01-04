"""SPY vs GLD Portfolio Analysis - Streamlit App."""

import streamlit as st


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
    render_settings,
)
from core.data_downloader import AVAILABLE_PERIODS, validate_ticker

st.set_page_config(layout="wide", page_title="SPY vs GLD Analysis")

# Render settings in sidebar (must be done early to get ticker inputs)
render_settings()

# Get tickers from session state (defaults set in render_settings)
ticker1 = st.session_state.get("ticker1", "SPY")
ticker2 = st.session_state.get("ticker2", "GLD")

# Validate tickers
for ticker in [ticker1, ticker2]:
    if not validate_ticker(ticker):
        st.error(f"❌ Invalid ticker symbol: {ticker}. Please enter a valid ticker.")
        st.stop()

if ticker1 == ticker2:
    st.error(f"❌ Ticker 1 and Ticker 2 must be different. Both are set to {ticker1}.")
    st.stop()

st.title(f"{ticker1} vs {ticker2} Portfolio Analysis")

st.markdown("""
Explore optimal rebalancing strategies for a two-asset portfolio.
Adjust your strategy parameters and compare against grid search results.
""")

# Date range selection dropdown
period_options = list(AVAILABLE_PERIODS.keys())
selected_period = st.selectbox(
    "Select Historical Period (ending 2025-12-31)",
    options=period_options,
    index=period_options.index("10yr"),  # Default to 10yr
    help="Choose the historical period for analysis. All periods end on December 31, 2025.",
)

# Load data and run grid search
data, grid_search_data = load_data_and_search(
    ticker1=ticker1, ticker2=ticker2, period=selected_period
)

# Find optimal strategies
best_strategies = get_best_strategies(grid_search_data)
best_sharpe = best_strategies["sharpe"]
best_cagr = best_strategies["cagr"]
best_drawdown = best_strategies["drawdown"]

# Render strategy controls and get selected parameters
strategy_t1_ratio, strategy_rebalance = render_strategy_controls(
    best_sharpe, best_cagr, best_drawdown, ticker1
)

# Relative metrics toggle
use_relative = st.toggle("Show Relative Metrics", value=False)

# Run strategy with selected parameters
strategy_result, strategy_metrics = run_strategy_with_metrics(
    data, ticker1, ticker2, strategy_t1_ratio, strategy_rebalance, 10_000
)

# Calculate baseline metrics
ticker1_metrics = calculate_metrics(
    data[ticker1].values, data.index[0], data.index[-1], 0
)
ticker2_metrics = calculate_metrics(
    data[ticker2].values, data.index[0], data.index[-1], 0
)

# Render UI components
render_performance_chart(data, strategy_result)

render_metrics_table(
    strategy_t1_ratio,
    strategy_rebalance,
    strategy_metrics,
    best_sharpe,
    best_cagr,
    best_drawdown,
    ticker1_metrics,
    ticker2_metrics,
    ticker1,
    ticker2,
)

render_heatmaps(
    grid_search_data,
    strategy_metrics,
    use_relative,
    strategy_t1_ratio,
    strategy_rebalance,
    best_sharpe,
    best_cagr,
    best_drawdown,
    ticker1,
)
