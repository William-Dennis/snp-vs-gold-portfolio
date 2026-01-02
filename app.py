import streamlit as st

from data_downloader import get_two_series
from plotter import plot_3d
from calculations import run_strategy

st.write("Financial Analysis of SPY vs GLD")

data = get_two_series()

df = run_strategy(data)

# plot_3d(data, "SPY", "GLD", "VIX", mode="surface")

st.dataframe(df)
