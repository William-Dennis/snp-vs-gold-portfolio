import streamlit as st

from data_downloader import get_two_series

st.write("Hi!")

data = get_two_series()

st.dataframe(data)