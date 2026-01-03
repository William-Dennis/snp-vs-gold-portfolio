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
best_drawdown = grid_search_data.nlargest(1, "max_drawdown").iloc[0]

# Initialize session state
if "t1_slider" not in st.session_state:
    st.session_state.t1_slider = 0.5
if "rebalance_slider" not in st.session_state:
    st.session_state.rebalance_slider = 0.0

# Strategy configuration
col1, col2, col3, col4, col5 = st.columns(5)

with col3:
    if st.button("Max Sharpe Strategy", use_container_width=True):
        st.session_state.t1_slider = float(best_sharpe["t1_ratio"])
        st.session_state.rebalance_slider = float(best_sharpe["rebalance_rate"])
        st.rerun()

with col4:
    if st.button("Max CAGR Strategy", use_container_width=True):
        st.session_state.t1_slider = float(best_cagr["t1_ratio"])
        st.session_state.rebalance_slider = float(best_cagr["rebalance_rate"])
        st.rerun()

with col5:
    if st.button("Min Drawdown Strategy", use_container_width=True):
        st.session_state.t1_slider = float(best_drawdown["t1_ratio"])
        st.session_state.rebalance_slider = float(best_drawdown["rebalance_rate"])
        st.rerun()

with col1:
    strategy_t1_ratio = st.slider(
        "SPY Allocation",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.t1_slider,
        step=0.01,
        format="%.3f",
        key="t1_slider",
    )

with col2:
    strategy_rebalance = st.slider(
        "Rebalance Threshold",
        min_value=0.0,
        max_value=0.10,
        value=st.session_state.rebalance_slider,
        step=0.001,
        format="%.4f",
        help="Rebalance when allocation drifts by this amount",
        key="rebalance_slider",
    )

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
    int(np.sum(strategy_result["rebalance"] != 0)),
)

# Calculate SPY and GLD metrics
spy_metrics = calculate_metrics(data["SPY"].values, data.index[0], data.index[-1], 0)

gld_metrics = calculate_metrics(data["GLD"].values, data.index[0], data.index[-1], 0)

# Combined performance chart
st.subheader("Performance Comparison")

normalized_data = data.copy()
normalized_data["Your Strategy"] = (
    strategy_result["total_cash_value"] / 10_000 * data["SPY"].iloc[0]
)
plot_all_columns(normalized_data, title="", height=800)

# Metrics comparison table
st.subheader("Performance Metrics")

# Calculate metrics for the 3 best strategies from grid search
best_sharpe_result = run_strategy(
    data,
    ticker1="SPY",
    ticker2="GLD",
    t1_ratio=float(best_sharpe["t1_ratio"]),
    rebalance_rate=float(best_sharpe["rebalance_rate"]),
    starting_cash=10_000,
)
best_sharpe_metrics = calculate_metrics(
    best_sharpe_result["total_cash_value"].values,
    data.index[0],
    data.index[-1],
    int(np.sum(best_sharpe_result["rebalance"] != 0)),
)

best_cagr_result = run_strategy(
    data,
    ticker1="SPY",
    ticker2="GLD",
    t1_ratio=float(best_cagr["t1_ratio"]),
    rebalance_rate=float(best_cagr["rebalance_rate"]),
    starting_cash=10_000,
)
best_cagr_metrics = calculate_metrics(
    best_cagr_result["total_cash_value"].values,
    data.index[0],
    data.index[-1],
    int(np.sum(best_cagr_result["rebalance"] != 0)),
)

best_drawdown_result = run_strategy(
    data,
    ticker1="SPY",
    ticker2="GLD",
    t1_ratio=float(best_drawdown["t1_ratio"]),
    rebalance_rate=float(best_drawdown["rebalance_rate"]),
    starting_cash=10_000,
)
best_drawdown_metrics = calculate_metrics(
    best_drawdown_result["total_cash_value"].values,
    data.index[0],
    data.index[-1],
    int(np.sum(best_drawdown_result["rebalance"] != 0)),
)

# Updated metrics DataFrame including the 3 strategies
metrics_df = pd.DataFrame(
    {
        "Strategy": [
            "Your Strategy",
            "Max Sharpe Strategy",
            "Max CAGR Strategy",
            "Min Drawdown Strategy",
            "SPY Only",
            "GLD Only",
        ],
        "SPY Allocation": [
            strategy_t1_ratio,
            float(best_sharpe["t1_ratio"]),
            float(best_cagr["t1_ratio"]),
            float(best_drawdown["t1_ratio"]),
            1.0,  # SPY only fully allocated to SPY
            0.0,  # GLD only no SPY allocation
        ],
        "Rebalance Threshold": [
            strategy_rebalance,
            float(best_sharpe["rebalance_rate"]),
            float(best_cagr["rebalance_rate"]),
            float(best_drawdown["rebalance_rate"]),
            0.0,  # no rebalancing for single assets
            0.0,
        ],
        "Sharpe": [
            strategy_metrics["sharpe"],
            best_sharpe_metrics["sharpe"],
            best_cagr_metrics["sharpe"],
            best_drawdown_metrics["sharpe"],
            spy_metrics["sharpe"],
            gld_metrics["sharpe"],
        ],
        "CAGR": [
            strategy_metrics["cagr"],
            best_sharpe_metrics["cagr"],
            best_cagr_metrics["cagr"],
            best_drawdown_metrics["cagr"],
            spy_metrics["cagr"],
            gld_metrics["cagr"],
        ],
        "Max Drawdown": [
            strategy_metrics["max_drawdown"],
            best_sharpe_metrics["max_drawdown"],
            best_cagr_metrics["max_drawdown"],
            best_drawdown_metrics["max_drawdown"],
            spy_metrics["max_drawdown"],
            gld_metrics["max_drawdown"],
        ],
        "Rebalances": [
            strategy_metrics["num_rebalances"],
            best_sharpe_metrics["num_rebalances"],
            best_cagr_metrics["num_rebalances"],
            best_drawdown_metrics["num_rebalances"],
            spy_metrics["num_rebalances"],
            gld_metrics["num_rebalances"],
        ],
    }
)
st.dataframe(
    metrics_df.style.format(
        {
            "Sharpe": "{:.4f}",
            "CAGR": "{:.2%}",
            "Max Drawdown": "{:.2%}",
            "Rebalances": "{:.0f}",
            "SPY Allocation": "{:.2f}",
            "Rebalance Threshold": "{:.3f}",
        }
    ),
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
