import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="SPY vs GLD Analysis")

from data_downloader import get_two_series
from plotter import plot_2d_heatmap, plot_all_columns
from calculations import run_grid_search, run_strategy, calculate_metrics
import numpy as np

st.title("SPY vs GLD Portfolio Analysis")

st.markdown("""
Explore optimal rebalancing strategies for a two-asset portfolio. 
Adjust your strategy parameters and compare against grid search results.
""")

# Load data and run grid search (cached for performance)
@st.cache_data
def load_data_and_search():
    data = get_two_series()
    grid_results = run_grid_search(data)
    return data, grid_results

data, grid_search_data = load_data_and_search()

# Find optimal strategies
best_sharpe = grid_search_data.nlargest(1, "sharpe").iloc[0]
best_cagr = grid_search_data.nlargest(1, "cagr").iloc[0]

# Initialize session state
if "t1_ratio" not in st.session_state:
    st.session_state.t1_ratio = 0.5
if "rebalance_rate" not in st.session_state:
    st.session_state.rebalance_rate = 0.0

# Strategy configuration
col1, col2, col3, col4 = st.columns(4)

with col1:
    strategy_t1_ratio = st.slider(
        "SPY Allocation",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.t1_ratio,
        step=0.01,
        format="%.2f",
        key="t1_slider"
    )
    st.session_state.t1_ratio = strategy_t1_ratio

with col2:
    strategy_rebalance = st.slider(
        "Rebalance Threshold",
        min_value=0.0,
        max_value=0.10,
        value=st.session_state.rebalance_rate,
        step=0.01,
        format="%.2f",
        help="Rebalance when allocation drifts by this amount",
        key="rebalance_slider"
    )
    st.session_state.rebalance_rate = strategy_rebalance

with col3:
    if st.button("🎯 Optimal Sharpe", use_container_width=True):
        st.session_state.t1_ratio = float(best_sharpe["t1_ratio"])
        st.session_state.rebalance_rate = float(best_sharpe["rebalance_rate"])
        st.rerun()

with col4:
    if st.button("📈 Optimal CAGR", use_container_width=True):
        st.session_state.t1_ratio = float(best_cagr["t1_ratio"])
        st.session_state.rebalance_rate = float(best_cagr["rebalance_rate"])
        st.rerun()

# Relative metrics toggle
use_relative = st.toggle("Show Relative Metrics", value=False)

# Run strategy
strategy_result = run_strategy(
    data,
    ticker1="SPY",
    ticker2="GLD",
    t1_ratio=strategy_t1_ratio,
    rebalance_rate=strategy_rebalance,
    starting_cash=10_000,
)

strategy_metrics = calculate_metrics(
    strategy_result["total_cash_value"].values,
    data.index[0],
    data.index[-1],
    int(np.sum(strategy_result["rebalance"] != 0))
)

# Calculate SPY and GLD metrics
spy_metrics = calculate_metrics(
    data["SPY"].values,
    data.index[0],
    data.index[-1],
    0
)

gld_metrics = calculate_metrics(
    data["GLD"].values,
    data.index[0],
    data.index[-1],
    0
)

# Combined performance chart
st.subheader("Performance Comparison")

normalized_data = data.copy()
normalized_data["Your Strategy"] = (
    strategy_result["total_cash_value"] / 10_000 * data["SPY"].iloc[0]
)
plot_all_columns(normalized_data, title="", height=800)

# Metrics comparison table
st.subheader("Performance Metrics")

metrics_df = pd.DataFrame({
    "Strategy": ["Your Strategy", "SPY Only", "GLD Only"],
    "Sharpe": [strategy_metrics["sharpe"], spy_metrics["sharpe"], gld_metrics["sharpe"]],
    "CAGR": [strategy_metrics["cagr"], spy_metrics["cagr"], gld_metrics["cagr"]],
    "Max Drawdown": [strategy_metrics["max_drawdown"], spy_metrics["max_drawdown"], gld_metrics["max_drawdown"]],
    "Rebalances": [strategy_metrics["num_rebalances"], spy_metrics["num_rebalances"], gld_metrics["num_rebalances"]],
})

st.dataframe(
    metrics_df.style.format({
        "Sharpe": "{:.4f}",
        "CAGR": "{:.2%}",
        "Max Drawdown": "{:.2%}",
        "Rebalances": "{:.0f}",
    }),
    use_container_width=True,
    hide_index=True,
)

# Plot heatmaps in 2x2 grid
st.subheader("Grid Search Results")

metrics = ["sharpe", "cagr", "max_drawdown", "num_rebalances"]

# First row
col1, col2 = st.columns(2)
with col1:
    plot_2d_heatmap(
        grid_search_data,
        "rebalance_rate",
        "t1_ratio",
        metrics[0],
        baseline_value=strategy_metrics[metrics[0]],
        use_relative=use_relative,
    )

with col2:
    plot_2d_heatmap(
        grid_search_data,
        "rebalance_rate",
        "t1_ratio",
        metrics[1],
        baseline_value=strategy_metrics[metrics[1]],
        use_relative=use_relative,
    )

# Second row
col1, col2 = st.columns(2)
with col1:
    plot_2d_heatmap(
        grid_search_data,
        "rebalance_rate",
        "t1_ratio",
        metrics[2],
        baseline_value=strategy_metrics[metrics[2]],
        use_relative=use_relative,
    )

with col2:
    plot_2d_heatmap(
        grid_search_data,
        "rebalance_rate",
        "t1_ratio",
        metrics[3],
        baseline_value=strategy_metrics[metrics[3]],
        use_relative=use_relative,
    )