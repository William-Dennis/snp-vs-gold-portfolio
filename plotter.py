import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def plot_all_columns(df: pd.DataFrame, x_label="Date", y_label="Price", 
                    title="", height=400):
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
    """Plot square 2D heatmap with strategy metric in title."""
    pivot_table = df.pivot(index=y, columns=x, values=z).sort_index().sort_index(axis=1)

    if pivot_table.isna().any().any():
        raise ValueError(f"Incomplete data in '{z}'")

    # Calculate display values and title
    if use_relative and baseline_value is not None:
        display_values = _calc_relative(pivot_table.values, baseline_value)
        title = f"{z} (% vs Your Strategy: {baseline_value:.4f})"
        colorscale = "RdBu"
        zmid = 0
    else:
        display_values = pivot_table.values
        title = f"{z} (Your Strategy: {baseline_value:.4f})" if baseline_value else z
        colorscale = "RdYlGn"
        zmid = None

    fig = go.Figure(
        go.Heatmap(
            z=display_values,
            x=pivot_table.columns.values,
            y=pivot_table.index.values,
            colorscale=colorscale,
            zmid=zmid,
        )
    )

    fig.update_layout(
        title=title,
        height=600,
        margin=dict(l=0, r=0, b=0, t=40),
        yaxis=dict(autorange="reversed"),
    )

    st.plotly_chart(fig, use_container_width=True)


def _calc_relative(values, baseline):
    """Calculate percentage difference from baseline."""
    if baseline == 0:
        return values - baseline
    return ((values - baseline) / abs(baseline)) * 100