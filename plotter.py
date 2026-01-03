import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def plot_all_columns(df: pd.DataFrame, x_label="Date", y_label="Price", 
                    title="", height=800):
    """Plot all numeric columns as line charts."""
    fig = go.Figure()

    for col in df.select_dtypes(include="number").columns:
        series = df[col]
        fig.add_trace(
            go.Scatter(x=series.index, y=series.values, mode="lines", name=col)
        )

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=height,
        margin=dict(l=40, r=40, t=40, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_2d_heatmap(df: pd.DataFrame, x: str, y: str, z: str,
                   baseline_value: float = None, use_relative: bool = False):
    """Plot professional square 2D heatmap with proper labels."""
    pivot_table = df.pivot(index=y, columns=x, values=z).sort_index().sort_index(axis=1)

    if pivot_table.isna().any().any():
        raise ValueError(f"Incomplete data in '{z}'")

    # Get human-readable labels
    x_label = _get_label(x)
    y_label = _get_label(y)
    z_label = _get_label(z)
    
    # Calculate display values and title
    if use_relative and baseline_value is not None:
        display_values = _calc_relative(pivot_table.values, baseline_value)
        formatted_baseline = _format_value(z, baseline_value)
        title = f"{z_label}<br><sub>% vs Your Strategy: {formatted_baseline}</sub>"
        colorbar_title = "% Difference"
        colorscale = "RdBu"
        zmid = 0
        value_suffix = "%"
    else:
        display_values = pivot_table.values
        if baseline_value is not None:
            formatted_baseline = _format_value(z, baseline_value)
            title = f"{z_label}<br><sub>Your Strategy: {formatted_baseline}</sub>"
        else:
            title = z_label
        colorbar_title = z_label
        colorscale = "RdYlGn"
        zmid = None
        value_suffix = ""

    # Create hover text
    hover_text = _create_hover_text(
        pivot_table, x, y, z, display_values, use_relative, value_suffix
    )

    fig = go.Figure(
        go.Heatmap(
            z=display_values,
            x=pivot_table.columns.values,
            y=pivot_table.index.values,
            colorscale=colorscale,
            zmid=zmid,
            colorbar=dict(
                title=colorbar_title,
                ticksuffix=value_suffix if use_relative else "",
            ),
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center"),
        height=600,
        margin=dict(l=60, r=60, b=60, t=80),
        xaxis=dict(
            title=x_label,
            side="bottom",
            tickformat=".3f" if x == "rebalance_rate" else ".2f",
        ),
        yaxis=dict(
            title=y_label,
            autorange="reversed",
            tickformat=".2f",
        ),
        font=dict(size=12),
    )

    st.plotly_chart(fig, use_container_width=True)


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


def _create_hover_text(pivot_table, x, y, z, display_values, use_relative, value_suffix):
    """Create formatted hover text for each heatmap cell."""
    hover_text = []
    x_label = _get_label(x)
    y_label = _get_label(y)
    z_label = _get_label(z)
    
    for i, y_val in enumerate(pivot_table.index):
        row = []
        for j, x_val in enumerate(pivot_table.columns):
            # Format parameter values
            x_formatted = f"{x_val:.3f}" if x == "rebalance_rate" else f"{x_val:.2f}"
            y_formatted = f"{y_val:.2f}"
            
            # Format metric value
            if use_relative:
                z_formatted = f"{display_values[i, j]:+.2f}{value_suffix}"
            else:
                original_val = pivot_table.iloc[i, j]
                z_formatted = _format_value(z, original_val)
            
            hover = (
                f"<b>{x_label}:</b> {x_formatted}<br>"
                f"<b>{y_label}:</b> {y_formatted}<br>"
                f"<b>{z_label}:</b> {z_formatted}"
            )
            row.append(hover)
        hover_text.append(row)
    
    return hover_text


def _calc_relative(values, baseline):
    """Calculate percentage difference from baseline."""
    if baseline == 0:
        return values - baseline
    return ((values - baseline) / abs(baseline)) * 100