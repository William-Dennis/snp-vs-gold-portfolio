import streamlit as st

from data_downloader import get_two_series
from plotter import plot_3d

data = get_two_series()

# plot_3d(data, "SPY", "GLD", "VIX", mode="surface")

st.dataframe(data)