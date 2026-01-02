import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from scipy.interpolate import griddata


def plot_3d(
    df: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    mode: str = "scatter",  # "scatter" | "surface"
    color: str | None = None,
    grid_size: int = 50,
    title: str | None = None,
    height: int = 700,
):
    """
    Unified 3D plot helper for Streamlit.

    mode:
        - "scatter": interactive point cloud
        - "surface": interpolated surface from scattered data
    """

    if mode == "scatter":
        fig = px.scatter_3d(
            df,
            x=x,
            y=y,
            z=z,
            color=color,
            opacity=0.85,
        )

    elif mode == "surface":
        X = df[x].values
        Y = df[y].values
        Z = df[z].values

        xi = np.linspace(X.min(), X.max(), grid_size)
        yi = np.linspace(Y.min(), Y.max(), grid_size)
        Xi, Yi = np.meshgrid(xi, yi)

        Zi = griddata(
            (X, Y),
            Z,
            (Xi, Yi),
            method="cubic",
        )

        fig = go.Figure(
            data=go.Surface(
                x=Xi,
                y=Yi,
                z=Zi,
                colorscale="Viridis",
            )
        )

    else:
        raise ValueError("mode must be 'scatter' or 'surface'")

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=0, r=0, b=0, t=40),
        scene=dict(
            xaxis_title=x,
            yaxis_title=y,
            zaxis_title=z,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)
