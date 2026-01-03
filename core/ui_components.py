"""UI components for the Streamlit app."""

import streamlit as st
import pandas as pd

from .app_helpers import run_strategy_with_metrics
from .plotter import plot_2d_heatmap, plot_all_columns


def render_strategy_controls(best_sharpe, best_cagr, best_drawdown):
    """Render strategy configuration controls."""
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

    return strategy_t1_ratio, strategy_rebalance


def render_performance_chart(data, strategy_result):
    """Render the combined performance comparison chart."""
    st.subheader("Performance Comparison")

    normalized_data = data.copy()
    normalized_data["Your Strategy"] = (
        strategy_result["total_cash_value"] / 10_000 * data["SPY"].iloc[0]
    )
    plot_all_columns(normalized_data, title="", height=800)


def render_metrics_table(
    strategy_t1_ratio,
    strategy_rebalance,
    strategy_metrics,
    best_sharpe,
    best_cagr,
    best_drawdown,
    best_sharpe_metrics,
    best_cagr_metrics,
    best_drawdown_metrics,
    spy_metrics,
    gld_metrics,
):
    """Render the metrics comparison table."""
    st.subheader("Performance Metrics")

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
                1.0,
                0.0,
            ],
            "Rebalance Threshold": [
                strategy_rebalance,
                float(best_sharpe["rebalance_rate"]),
                float(best_cagr["rebalance_rate"]),
                float(best_drawdown["rebalance_rate"]),
                0.0,
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


def render_heatmaps(grid_search_data, strategy_metrics, use_relative):
    """Render the grid search heatmaps."""
    st.subheader("Grid Search Results")

    metrics = ["sharpe", "cagr", "max_drawdown", "num_rebalances"]

    for i in range(0, len(metrics), 2):
        col1, col2 = st.columns(2)
        with col1:
            plot_2d_heatmap(
                grid_search_data,
                "rebalance_rate",
                "t1_ratio",
                metrics[i],
                baseline_value=strategy_metrics[metrics[i]],
                use_relative=use_relative,
            )
        if i + 1 < len(metrics):
            with col2:
                plot_2d_heatmap(
                    grid_search_data,
                    "rebalance_rate",
                    "t1_ratio",
                    metrics[i + 1],
                    baseline_value=strategy_metrics[metrics[i + 1]],
                    use_relative=use_relative,
                )
