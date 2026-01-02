import streamlit as st
import pandas as pd

# st.set_page_config(layout="wide", page_title="SPY vs GLD Analysis")

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

# Strategy configuration
col1, col2, col3 = st.columns(3)

with col1:
    strategy_t1_ratio = st.slider(
        "SPY Allocation",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        format="%.2f"
    )

with col2:
    strategy_rebalance = st.slider(
        "Rebalance Threshold",
        min_value=0.0,
        max_value=0.10,
        value=0.0,
        step=0.005,
        format="%.3f",
        help="Rebalance when allocation drifts by this amount"
    )

with col3:
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
plot_all_columns(normalized_data, title="", height=400)

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

# Plot heatmaps
st.subheader("Grid Search Results")

for metric in ["sharpe", "cagr", "max_drawdown", "num_rebalances"]:
    plot_2d_heatmap(
        grid_search_data,
        "rebalance_rate",
        "t1_ratio",
        metric,
        baseline_value=strategy_metrics[metric],
        use_relative=use_relative,
    )