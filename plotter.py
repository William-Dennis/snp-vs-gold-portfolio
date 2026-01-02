import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from scipy.interpolate import griddata


def plot_all_columns(
    df: pd.DataFrame, x_label="Date", y_label="Normalised Price", title="", height=400
):
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


def plot_2d_heatmap(
    df,
    x: str,
    y: str,
    z: str,
    height: int = 700,
    central_point = None
):
    """
    Plot helper for Streamlit supporting scatter or heatmap.

    mode:
        - "scatter": 3D scatter plot (x,y,z)
        - "heatmap": 2D heatmap of z values over x and y
    """
    title = z

    pivot_table = df.pivot(index=y, columns=x, values=z).sort_index().sort_index(axis=1)

    if pivot_table.isna().any().any():
        raise ValueError(f"Heatmap data incomplete: NaNs detected in '{z}'. Ensure full grid coverage.")

    fig = go.Figure(
        go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns.values,
            y=pivot_table.index.values,
            colorscale="RdYlGn",
            colorbar=dict(title=z),
        )
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))



    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=0, r=0, b=0, t=40),
        xaxis_title=x,
        yaxis_title=y,
    )

    st.plotly_chart(fig, use_container_width=True)