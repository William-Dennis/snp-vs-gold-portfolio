"""UI components for the Streamlit app."""

import streamlit as st
import pandas as pd

from .plotter import plot_2d_heatmap, plot_all_columns


def _render_preset_buttons(
    best_sharpe, best_cagr, best_drawdown, best_weekly_dd, best_monthly_dd
):
    """Render preset strategy buttons."""
    show_weekly = st.session_state.get("show_weekly_drawdown", False)
    show_monthly = st.session_state.get("show_monthly_drawdown", False)

    num_cols = 3 + (1 if show_weekly else 0) + (1 if show_monthly else 0)
    cols = st.columns(num_cols + 2)

    with cols[2]:
        if st.button("Max Sharpe Strategy", width="stretch"):
            st.session_state.t1_slider = float(best_sharpe["t1_ratio"]) * 100.0
            st.session_state.rebalance_slider = (
                float(best_sharpe["rebalance_rate"]) * 100.0
            )
            st.rerun()

    with cols[3]:
        if st.button("Max CAGR Strategy", width="stretch"):
            st.session_state.t1_slider = float(best_cagr["t1_ratio"]) * 100.0
            st.session_state.rebalance_slider = (
                float(best_cagr["rebalance_rate"]) * 100.0
            )
            st.rerun()

    with cols[4]:
        if st.button("Min Drawdown Strategy", width="stretch"):
            st.session_state.t1_slider = float(best_drawdown["t1_ratio"]) * 100.0
            st.session_state.rebalance_slider = (
                float(best_drawdown["rebalance_rate"]) * 100.0
            )
            st.rerun()

    col_idx = 5
    if show_weekly:
        with cols[col_idx]:
            if st.button("Min Weekly DD Strategy", width="stretch"):
                st.session_state.t1_slider = float(best_weekly_dd["t1_ratio"]) * 100.0
                st.session_state.rebalance_slider = (
                    float(best_weekly_dd["rebalance_rate"]) * 100.0
                )
                st.rerun()
        col_idx += 1

    if show_monthly:
        with cols[col_idx]:
            if st.button("Min Monthly DD Strategy", width="stretch"):
                st.session_state.t1_slider = float(best_monthly_dd["t1_ratio"]) * 100.0
                st.session_state.rebalance_slider = (
                    float(best_monthly_dd["rebalance_rate"]) * 100.0
                )
                st.rerun()

    return cols[0], cols[1]


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


def render_strategy_controls(
    best_sharpe, best_cagr, best_drawdown, best_weekly_dd, best_monthly_dd
):
    """Render strategy configuration controls."""
    col1, col2 = _render_preset_buttons(
        best_sharpe, best_cagr, best_drawdown, best_weekly_dd, best_monthly_dd
    )
    return _render_sliders(col1, col2)


def render_settings():
    """Render settings in sidebar with advanced options."""
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.checkbox(
            "Show Rebalancing Lines",
            value=False,
            key="show_rebalance_lines",
            help="Display vertical lines on the chart indicating when rebalancing occurred",
        )
        st.markdown("### 📊 Advanced Metrics")
        st.checkbox(
            "Show Weekly Drawdown",
            value=False,
            key="show_weekly_drawdown",
            help="Display maximum weekly drawdown metrics",
        )
        st.checkbox(
            "Show Monthly Drawdown",
            value=False,
            key="show_monthly_drawdown",
            help="Display maximum monthly drawdown metrics",
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


def _get_allocation_values(
    strategy_t1_ratio,
    best_sharpe,
    best_cagr,
    best_drawdown,
    best_weekly_dd=None,
    best_monthly_dd=None,
):
    """Get SPY allocation values for all strategies."""
    values = [
        strategy_t1_ratio,
        float(best_sharpe["t1_ratio"]),
        float(best_cagr["t1_ratio"]),
        float(best_drawdown["t1_ratio"]),
    ]
    if best_weekly_dd:
        values.append(float(best_weekly_dd["t1_ratio"]))
    if best_monthly_dd:
        values.append(float(best_monthly_dd["t1_ratio"]))
    values.extend([1.0, 0.0])
    return values


def _get_rebalance_values(
    strategy_rebalance,
    best_sharpe,
    best_cagr,
    best_drawdown,
    best_weekly_dd=None,
    best_monthly_dd=None,
):
    """Get rebalance threshold values for all strategies."""
    values = [
        strategy_rebalance,
        float(best_sharpe["rebalance_rate"]),
        float(best_cagr["rebalance_rate"]),
        float(best_drawdown["rebalance_rate"]),
    ]
    if best_weekly_dd:
        values.append(float(best_weekly_dd["rebalance_rate"]))
    if best_monthly_dd:
        values.append(float(best_monthly_dd["rebalance_rate"]))
    values.extend([0.0, 0.0])
    return values


def _get_metric_values(
    metric_key,
    strategy_metrics,
    best_sharpe,
    best_cagr,
    best_drawdown,
    spy_metrics,
    gld_metrics,
    best_weekly_dd=None,
    best_monthly_dd=None,
):
    """Get metric values for all strategies."""
    values = [
        strategy_metrics[metric_key],
        best_sharpe[metric_key],
        best_cagr[metric_key],
        best_drawdown[metric_key],
    ]
    if best_weekly_dd:
        values.append(best_weekly_dd[metric_key])
    if best_monthly_dd:
        values.append(best_monthly_dd[metric_key])
    values.extend([spy_metrics[metric_key], gld_metrics[metric_key]])
    return values


def _create_metrics_dataframe(
    strategy_t1_ratio,
    strategy_rebalance,
    strategy_metrics,
    best_sharpe,
    best_cagr,
    best_drawdown,
    spy_metrics,
    gld_metrics,
    best_weekly_dd=None,
    best_monthly_dd=None,
):
    """Create metrics comparison dataframe."""
    strategies = [
        "Your Strategy",
        "Max Sharpe Strategy",
        "Max CAGR Strategy",
        "Min Drawdown Strategy",
    ]
    if best_weekly_dd:
        strategies.append("Min Weekly DD Strategy")
    if best_monthly_dd:
        strategies.append("Min Monthly DD Strategy")
    strategies.extend(["SPY Only", "GLD Only"])

    data = {
        "Strategy": strategies,
        "SPY Allocation": _get_allocation_values(
            strategy_t1_ratio,
            best_sharpe,
            best_cagr,
            best_drawdown,
            best_weekly_dd,
            best_monthly_dd,
        ),
        "Rebalance Threshold": _get_rebalance_values(
            strategy_rebalance,
            best_sharpe,
            best_cagr,
            best_drawdown,
            best_weekly_dd,
            best_monthly_dd,
        ),
        "Sharpe": _get_metric_values(
            "sharpe",
            strategy_metrics,
            best_sharpe,
            best_cagr,
            best_drawdown,
            spy_metrics,
            gld_metrics,
            best_weekly_dd,
            best_monthly_dd,
        ),
        "CAGR": _get_metric_values(
            "cagr",
            strategy_metrics,
            best_sharpe,
            best_cagr,
            best_drawdown,
            spy_metrics,
            gld_metrics,
            best_weekly_dd,
            best_monthly_dd,
        ),
        "Max Drawdown": _get_metric_values(
            "max_drawdown",
            strategy_metrics,
            best_sharpe,
            best_cagr,
            best_drawdown,
            spy_metrics,
            gld_metrics,
            best_weekly_dd,
            best_monthly_dd,
        ),
        "Rebalances": _get_metric_values(
            "num_rebalances",
            strategy_metrics,
            best_sharpe,
            best_cagr,
            best_drawdown,
            spy_metrics,
            gld_metrics,
            best_weekly_dd,
            best_monthly_dd,
        ),
    }

    if best_weekly_dd:
        data["Max Weekly Drawdown"] = _get_metric_values(
            "max_weekly_drawdown",
            strategy_metrics,
            best_sharpe,
            best_cagr,
            best_drawdown,
            spy_metrics,
            gld_metrics,
            best_weekly_dd,
            best_monthly_dd,
        )

    if best_monthly_dd:
        data["Max Monthly Drawdown"] = _get_metric_values(
            "max_monthly_drawdown",
            strategy_metrics,
            best_sharpe,
            best_cagr,
            best_drawdown,
            spy_metrics,
            gld_metrics,
            best_weekly_dd,
            best_monthly_dd,
        )

    return pd.DataFrame(data)


def _get_format_spec(show_weekly=False, show_monthly=False):
    """Get format specification for metrics table."""
    spec = {
        "Sharpe": "{:.4f}",
        "CAGR": "{:.2%}",
        "Max Drawdown": "{:.2%}",
        "Rebalances": "{:.0f}",
        "SPY Allocation": "{:.1%}",
        "Rebalance Threshold": "{:.1%}",
    }
    if show_weekly:
        spec["Max Weekly Drawdown"] = "{:.2%}"
    if show_monthly:
        spec["Max Monthly Drawdown"] = "{:.2%}"
    return spec


def render_metrics_table(
    strategy_t1_ratio,
    strategy_rebalance,
    strategy_metrics,
    best_sharpe,
    best_cagr,
    best_drawdown,
    spy_metrics,
    gld_metrics,
    best_weekly_dd=None,
    best_monthly_dd=None,
):
    """Render the metrics comparison table."""
    st.subheader("Performance Metrics")

    show_weekly = best_weekly_dd is not None
    show_monthly = best_monthly_dd is not None

    metrics_df = _create_metrics_dataframe(
        strategy_t1_ratio,
        strategy_rebalance,
        strategy_metrics,
        best_sharpe,
        best_cagr,
        best_drawdown,
        spy_metrics,
        gld_metrics,
        best_weekly_dd,
        best_monthly_dd,
    )

    st.dataframe(
        metrics_df.style.format(_get_format_spec(show_weekly, show_monthly)),
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
    best_weekly_dd=None,
    best_monthly_dd=None,
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

    if best_weekly_dd:
        strategy_markers.append(
            {
                "name": "Min Weekly DD Strategy",
                "rebalance_rate": float(best_weekly_dd["rebalance_rate"]),
                "t1_ratio": float(best_weekly_dd["t1_ratio"]),
            }
        )
        metrics.append("max_weekly_drawdown")

    if best_monthly_dd:
        strategy_markers.append(
            {
                "name": "Min Monthly DD Strategy",
                "rebalance_rate": float(best_monthly_dd["rebalance_rate"]),
                "t1_ratio": float(best_monthly_dd["t1_ratio"]),
            }
        )
        metrics.append("max_monthly_drawdown")

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
