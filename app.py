import streamlit as st

# st.set_page_config(layout="wide")

from data_downloader import get_two_series
from plotter import plot_2d_heatmap, plot_all_columns
from calculations import run_strategy, run_grid_search

st.write("Financial Analysis of SPY vs GLD")

data = get_two_series()

grid_search_data = run_grid_search(data)

for metric in ["sharpe", "num_rebalances", "max_drawdown", "cagr"]:
    plot_2d_heatmap(grid_search_data, "rebalance_rate", "t1_ratio", metric)

df = run_strategy(data)

plot_all_columns(df)

st.dataframe(grid_search_data)