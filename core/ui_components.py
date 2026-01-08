"""UI components for the Streamlit app."""

import streamlit as st
import pandas as pd

from .plotter import plot_2d_heatmap, plot_all_columns, plot_portfolio_allocation


def _render_preset_buttons(best_sharpe, best_cagr, best_drawdown):
    """Render preset strategy buttons."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col3:
        if st.button("Max Sharpe Strategy", width="stretch"):
            st.session_state.t1_slider = float(best_sharpe["t1_ratio"]) * 100.0
            st.session_state.rebalance_slider = (
                float(best_sharpe["rebalance_rate"]) * 100.0
            )
            st.rerun()

    with col4:
        if st.button("Max CAGR Strategy", width="stretch"):
            st.session_state.t1_slider = float(best_cagr["t1_ratio"]) * 100.0
            st.session_state.rebalance_slider = (
                float(best_cagr["rebalance_rate"]) * 100.0
            )
            st.rerun()

    with col5:
        if st.button("Min Drawdown Strategy", width="stretch"):
            st.session_state.t1_slider = float(best_drawdown["t1_ratio"]) * 100.0
            st.session_state.rebalance_slider = (
                float(best_drawdown["rebalance_rate"]) * 100.0
            )
            st.rerun()

    return col1, col2


def _render_sliders(col1, col2):
    """Render allocation and rebalance sliders."""
    with col1:
        strategy_t1_ratio_pct = st.slider(
            "SPY Allocation",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            value=50.0,
            format="%.1f%%",
            key="t1_slider",
        )
        strategy_t1_ratio = strategy_t1_ratio_pct / 100.0

    with col2:
        strategy_rebalance_pct = st.slider(
            "Rebalance Threshold",
            min_value=1.0,
            max_value=11.0,
            step=0.1,
            value=11.0,
            format="%.1f%%",
            help="Rebalance when allocation drifts by this amount",
            key="rebalance_slider",
        )
        strategy_rebalance = strategy_rebalance_pct / 100.0

    return strategy_t1_ratio, strategy_rebalance


def render_strategy_controls(best_sharpe, best_cagr, best_drawdown):
    """Render strategy configuration controls."""
    col1, col2 = _render_preset_buttons(best_sharpe, best_cagr, best_drawdown)
    return _render_sliders(col1, col2)


def render_settings():
    """Render settings in sidebar with advanced options."""
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.number_input(
            "Final Year",
            min_value=2005,
            max_value=2025,
            value=2025,
            step=1,
            key="final_year",
            help="End year for historical data analysis",
        )
        st.checkbox(
            "Show Rebalancing Lines",
            value=False,
            key="show_rebalance_lines",
            help="Display vertical lines on the chart indicating when rebalancing occurred",
        )
        st.checkbox(
            "Show % Allocation Chart",
            value=False,
            key="show_pct_allocation_chart",
            help="Display a chart showing portfolio allocation percentages of SPY vs GLD",
        )


def render_performance_chart(data, strategy_result):
    """Render the combined performance comparison chart."""
    st.subheader("Performance Comparison")

    normalized_data = data.copy()
    normalized_data["Your Strategy"] = (
        strategy_result["total_cash_value"] / 10_000 * data["SPY"].iloc[0]
    )

    rebalance_mask = strategy_result["rebalance"] != 0
    rebalance_dates = strategy_result.index[rebalance_mask].tolist()
    rebalance_amounts = strategy_result.loc[rebalance_mask, "rebalance"].tolist()

    # Pass rebalancing data only if toggle is enabled
    show_rebalancing = st.session_state.show_rebalance_lines

    plot_all_columns(
        normalized_data,
        title="",
        y_label="Normalised Price",
        height=800,
        rebalance_dates=rebalance_dates if show_rebalancing else None,
        rebalance_amounts=rebalance_amounts if show_rebalancing else None,
    )

    # Add percentage change chart if enabled
    if st.session_state.get("show_pct_allocation_chart", False):
        plot_portfolio_allocation(
            strategy_result,
            "SPY",
            "GLD",
            height=200,
            rebalance_dates=rebalance_dates if show_rebalancing else None,
            rebalance_amounts=rebalance_amounts if show_rebalancing else None,
        )


def _get_allocation_values(strategy_t1_ratio, best_sharpe, best_cagr, best_drawdown):
    """Get SPY allocation values for all strategies."""
    return [
        strategy_t1_ratio,
        float(best_sharpe["t1_ratio"]),
        float(best_cagr["t1_ratio"]),
        float(best_drawdown["t1_ratio"]),
        1.0,
        0.0,
    ]


def _get_rebalance_values(strategy_rebalance, best_sharpe, best_cagr, best_drawdown):
    """Get rebalance threshold values for all strategies."""
    return [
        strategy_rebalance,
        float(best_sharpe["rebalance_rate"]),
        float(best_cagr["rebalance_rate"]),
        float(best_drawdown["rebalance_rate"]),
        0.0,
        0.0,
    ]


def _get_metric_values(
    metric_key,
    strategy_metrics,
    best_sharpe,
    best_cagr,
    best_drawdown,
    spy_metrics,
    gld_metrics,
):
    """Get metric values for all strategies."""
    return [
        strategy_metrics[metric_key],
        best_sharpe[metric_key],
        best_cagr[metric_key],
        best_drawdown[metric_key],
        spy_metrics[metric_key],
        gld_metrics[metric_key],
    ]


def _create_metrics_dataframe(
    strategy_t1_ratio,
    strategy_rebalance,
    strategy_metrics,
    best_sharpe,
    best_cagr,
    best_drawdown,
    spy_metrics,
    gld_metrics,
):
    """Create metrics comparison dataframe."""
    return pd.DataFrame(
        {
            "Strategy": [
                "Your Strategy",
                "Max Sharpe Strategy",
                "Max CAGR Strategy",
                "Min Drawdown Strategy",
                "SPY Only",
                "GLD Only",
            ],
            "SPY Allocation": _get_allocation_values(
                strategy_t1_ratio, best_sharpe, best_cagr, best_drawdown
            ),
            "Rebalance Threshold": _get_rebalance_values(
                strategy_rebalance, best_sharpe, best_cagr, best_drawdown
            ),
            "Sharpe": _get_metric_values(
                "sharpe",
                strategy_metrics,
                best_sharpe,
                best_cagr,
                best_drawdown,
                spy_metrics,
                gld_metrics,
            ),
            "CAGR": _get_metric_values(
                "cagr",
                strategy_metrics,
                best_sharpe,
                best_cagr,
                best_drawdown,
                spy_metrics,
                gld_metrics,
            ),
            "Max Drawdown": _get_metric_values(
                "max_drawdown",
                strategy_metrics,
                best_sharpe,
                best_cagr,
                best_drawdown,
                spy_metrics,
                gld_metrics,
            ),
            "Rebalances": _get_metric_values(
                "num_rebalances",
                strategy_metrics,
                best_sharpe,
                best_cagr,
                best_drawdown,
                spy_metrics,
                gld_metrics,
            ),
        }
    )


def _get_format_spec():
    """Get format specification for metrics table."""
    return {
        "Sharpe": "{:.4f}",
        "CAGR": "{:.2%}",
        "Max Drawdown": "{:.2%}",
        "Rebalances": "{:.0f}",
        "SPY Allocation": "{:.1%}",
        "Rebalance Threshold": "{:.1%}",
    }


def render_metrics_table(
    strategy_t1_ratio,
    strategy_rebalance,
    strategy_metrics,
    best_sharpe,
    best_cagr,
    best_drawdown,
    spy_metrics,
    gld_metrics,
):
    """Render the metrics comparison table."""
    st.subheader("Performance Metrics")

    metrics_df = _create_metrics_dataframe(
        strategy_t1_ratio,
        strategy_rebalance,
        strategy_metrics,
        best_sharpe,
        best_cagr,
        best_drawdown,
        spy_metrics,
        gld_metrics,
    )

    st.dataframe(
        metrics_df.style.format(_get_format_spec()),
        width="stretch",
        hide_index=True,
    )


def render_heatmaps(
    grid_search_data,
    strategy_metrics,
    use_relative,
    strategy_t1_ratio,
    strategy_rebalance,
    best_sharpe,
    best_cagr,
    best_drawdown,
):
    """Render the grid search heatmaps with strategy markers."""
    st.subheader("Grid Search Results")

    # Prepare strategy markers with their positions
    strategy_markers = [
        {
            "name": "Your Strategy",
            "rebalance_rate": strategy_rebalance,
            "t1_ratio": strategy_t1_ratio,
        },
        {
            "name": "Max Sharpe Strategy",
            "rebalance_rate": float(best_sharpe["rebalance_rate"]),
            "t1_ratio": float(best_sharpe["t1_ratio"]),
        },
        {
            "name": "Max CAGR Strategy",
            "rebalance_rate": float(best_cagr["rebalance_rate"]),
            "t1_ratio": float(best_cagr["t1_ratio"]),
        },
        {
            "name": "Min Drawdown Strategy",
            "rebalance_rate": float(best_drawdown["rebalance_rate"]),
            "t1_ratio": float(best_drawdown["t1_ratio"]),
        },
    ]

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
                strategy_markers=strategy_markers,
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
                    strategy_markers=strategy_markers,
                )
