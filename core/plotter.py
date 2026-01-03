"""Plotting utilities for visualizing portfolio data."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd


# Strategy marker configuration
MARKER_COLORS = {
    "Your Strategy": "#FF6B6B",
    "Max Sharpe Strategy": "#4ECDC4",
    "Max CAGR Strategy": "#FFD93D",
    "Min Drawdown Strategy": "#95E1D3",
}

MARKER_SYMBOLS = {
    "Your Strategy": "star",
    "Max Sharpe Strategy": "diamond",
    "Max CAGR Strategy": "square",
    "Min Drawdown Strategy": "circle",
}

# Parameters that should be displayed as percentages
PERCENTAGE_PARAMS = ["rebalance_rate", "t1_ratio"]


def plot_all_columns(
    df: pd.DataFrame,
    x_label="Date",
    y_label="Price",
    title="",
    height=800,
    rebalance_dates=None,
):
    """Plot all numeric columns as line charts with optional rebalancing markers."""
    fig = go.Figure()

    color_map = {
        "SPY": "#1f77b4",  # Blue
        "GLD": "#FFD700",  # Gold
        "Your Strategy": "#FF6B6B",  # Red (consistent with marker colors)
    }

    for col in df.select_dtypes(include="number").columns:
        series = df[col]
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines",
                name=col,
                line=dict(color=color_map.get(col)),
            )
        )

    if rebalance_dates is not None and len(rebalance_dates) > 0:
        for date in rebalance_dates:
            fig.add_shape(
                type="line",
                x0=date,
                x1=date,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(color="rgba(128, 128, 128, 0.3)", width=1, dash="dot"),
            )

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=height,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    st.plotly_chart(fig, width="stretch")


def _get_heatmap_style(z_label, baseline_value, z, use_relative):
    """Get heatmap styling configuration."""
    if use_relative and baseline_value is not None:
        formatted_baseline = _format_value(z, baseline_value)
        title = f"{z_label}<br><sub>% vs Your Strategy: {formatted_baseline}</sub>"
        return title, "% Difference", "RdBu", 0, "%"
    elif baseline_value is not None:
        formatted_baseline = _format_value(z, baseline_value)
        title = f"{z_label}<br><sub>Your Strategy: {formatted_baseline}</sub>"
        return title, z_label, "RdYlGn", None, ""
    else:
        return z_label, z_label, "RdYlGn", None, ""


def _prepare_heatmap_data(df, x, y, z, baseline_value, use_relative):
    """Prepare data and styling for heatmap."""
    pivot_table = df.pivot(index=y, columns=x, values=z).sort_index().sort_index(axis=1)

    if pivot_table.isna().any().any():
        raise ValueError(f"Incomplete data in '{z}'")

    x_label = _get_label(x)
    y_label = _get_label(y)
    z_label = _get_label(z)

    display_values = (
        _calc_relative(pivot_table.values, baseline_value)
        if (use_relative and baseline_value is not None)
        else pivot_table.values
    )
    title, colorbar_title, colorscale, zmid, value_suffix = _get_heatmap_style(
        z_label, baseline_value, z, use_relative
    )

    return (
        pivot_table,
        display_values,
        title,
        colorbar_title,
        colorscale,
        zmid,
        value_suffix,
        x_label,
        y_label,
        z_label,
    )


def _create_heatmap_figure(
    pivot_table,
    display_values,
    colorscale,
    zmid,
    colorbar_title,
    value_suffix,
    use_relative,
    hover_text,
):
    """Create the plotly heatmap figure."""
    return go.Figure(
        go.Heatmap(
            z=display_values,
            x=pivot_table.columns.values,
            y=pivot_table.index.values,
            colorscale=colorscale,
            zmid=zmid,
            colorbar=dict(
                title=dict(text=colorbar_title, side="right"),
                ticksuffix=value_suffix if use_relative else "",
            ),
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
        )
    )


def _update_heatmap_layout(fig, title, x_label, y_label, x, y):
    """Update heatmap figure layout."""
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center"),
        height=600,
        margin=dict(l=60, r=60, b=120, t=80),
        xaxis=dict(
            title=x_label,
            side="bottom",
            tickformat=".1%" if x in PERCENTAGE_PARAMS else ".2f",
        ),
        yaxis=dict(
            title=y_label,
            autorange="reversed",
            tickformat=".1%" if y in PERCENTAGE_PARAMS else ".2f",
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
        font=dict(size=12),
    )


def _add_strategy_markers(fig, strategy_markers, x, y):
    """Add scatter plot markers for strategies on the heatmap.

    Args:
        fig: Plotly figure to add markers to
        strategy_markers: List of dicts with 'name', x, and y keys for each strategy
        x: Name of x-axis parameter (must match key in strategy_markers dicts)
        y: Name of y-axis parameter (must match key in strategy_markers dicts)
    """
    for marker in strategy_markers:
        name = marker["name"]
        x_val = marker[x]
        y_val = marker[y]

        # Format labels for hover template
        x_label = _get_label(x)
        y_label = _get_label(y)
        x_formatted = _format_param_value(x, x_val)
        y_formatted = _format_param_value(y, y_val)
        hover_text = f"<b>{name}</b><br>{x_label}: {x_formatted}<br>{y_label}: {y_formatted}<extra></extra>"

        fig.add_trace(
            go.Scatter(
                x=[x_val],
                y=[y_val],
                mode="markers",
                name=name,
                marker=dict(
                    size=15,
                    color=MARKER_COLORS.get(name, "#000000"),
                    symbol=MARKER_SYMBOLS.get(name, "circle"),
                    line=dict(width=2, color="white"),
                ),
                hovertemplate=hover_text,
                showlegend=True,
            )
        )


def plot_2d_heatmap(
    df: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    baseline_value: float = None,
    use_relative: bool = False,
    strategy_markers: list = None,
):
    """Plot professional square 2D heatmap with proper labels and strategy markers."""
    (
        pivot_table,
        display_values,
        title,
        colorbar_title,
        colorscale,
        zmid,
        value_suffix,
        x_label,
        y_label,
        z_label,
    ) = _prepare_heatmap_data(df, x, y, z, baseline_value, use_relative)

    hover_text = _create_hover_text(
        pivot_table, x, y, z, display_values, use_relative, value_suffix
    )

    fig = _create_heatmap_figure(
        pivot_table,
        display_values,
        colorscale,
        zmid,
        colorbar_title,
        value_suffix,
        use_relative,
        hover_text,
    )

    if strategy_markers:
        _add_strategy_markers(fig, strategy_markers, x, y)

    _update_heatmap_layout(fig, title, x_label, y_label, x, y)
    st.plotly_chart(fig, width="stretch")


def _get_label(param: str) -> str:
    """Convert parameter name to human-readable label."""
    labels = {
        "rebalance_rate": "Rebalance Threshold",
        "t1_ratio": "SPY Allocation",
        "sharpe": "Sharpe Ratio",
        "cagr": "CAGR",
        "max_drawdown": "Max Drawdown",
        "num_rebalances": "Number of Rebalances",
    }
    return labels.get(param, param)


def _format_param_value(param: str, value: float) -> str:
    """Format parameter value for display."""
    if param in PERCENTAGE_PARAMS:
        return f"{value:.1%}"
    else:
        return f"{value:.2f}"


def _format_value(metric: str, value: float) -> str:
    """Format value based on metric type."""
    if metric in ["cagr", "max_drawdown"]:
        return f"{value:.2%}"
    elif metric == "sharpe":
        return f"{value:.4f}"
    elif metric == "num_rebalances":
        return f"{int(value)}"
    else:
        return f"{value:.4f}"


def _format_cell_hover(
    x,
    y,
    z,
    x_val,
    y_val,
    display_val,
    pivot_table,
    i,
    j,
    use_relative,
    value_suffix,
    x_label,
    y_label,
    z_label,
):
    """Format hover text for a single cell."""
    x_formatted = _format_param_value(x, x_val)
    y_formatted = _format_param_value(y, y_val)

    if use_relative:
        z_formatted = f"{display_val:+.2f}{value_suffix}"
    else:
        original_val = pivot_table.iloc[i, j]
        z_formatted = _format_value(z, original_val)

    return (
        f"<b>{x_label}:</b> {x_formatted}<br>"
        f"<b>{y_label}:</b> {y_formatted}<br>"
        f"<b>{z_label}:</b> {z_formatted}"
    )


def _create_hover_text(
    pivot_table, x, y, z, display_values, use_relative, value_suffix
):
    """Create formatted hover text for each heatmap cell."""
    hover_text = []
    x_label = _get_label(x)
    y_label = _get_label(y)
    z_label = _get_label(z)

    for i, y_val in enumerate(pivot_table.index):
        row = []
        for j, x_val in enumerate(pivot_table.columns):
            hover = _format_cell_hover(
                x,
                y,
                z,
                x_val,
                y_val,
                display_values[i, j],
                pivot_table,
                i,
                j,
                use_relative,
                value_suffix,
                x_label,
                y_label,
                z_label,
            )
            row.append(hover)
        hover_text.append(row)

    return hover_text


def _calc_relative(values, baseline):
    """Calculate percentage difference from baseline."""
    if baseline == 0:
        return values - baseline
    return ((values - baseline) / abs(baseline)) * 100
