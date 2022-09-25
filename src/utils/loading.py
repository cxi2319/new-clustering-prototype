"""Functions to load/filter datasets.
"""
import pandas as pd
import streamlit as st
from utils import processing


def get_dates(week_start):
    # User-selected input for cluster run date
    cluster_run = st.date_input(
        label="Select an weekly cluster run. Please select the Monday of the week you'd like to view clustering data from:",
        value=week_start,
    )
    # Check to see if the inputted date is the Monday of the week to view clustering for, to make reading the file easier
    if cluster_run != week_start:
        # Check to see if the inputted date is a previous Monday. If not, then set it to the Monday of the week the user selected.
        if cluster_run not in pd.date_range(start="2022/09/12", periods=1000, freq="W-MON"):
            cluster_run = processing.first_day_of_week(cluster_run)

    # Convert input date to a string, and replace the default slashes with the '_' used in the filepath since slashes are not compatible
    filepath_date = processing.clean_dates(cluster_run)
    return filepath_date


# initialize_businesses loads name and experience data to populate the select boxes.
def initialize_businesses(filepath):
    df = pd.read_csv(filepath)
    df = df.rename(str.lower, axis="columns")
    return df


# initialize_full_data loads the entire clustering dataframe - we needed separate loading for
# businesses because the full dataset is too large and loads too slowly for user inputs.
def initialize_full_data(filepath):
    df = pd.read_csv(filepath)
    df = df.rename(str.lower, axis="columns")
    return df


# filter_businesses takes a selected business and filters the dataset to only include the experiences
# that belong to that business
st.cache()


def filter_businesses(df, business):
    df_filtered = df[df["name"] == business]
    return df_filtered


@st.cache
def convert_df(df):
    # Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")


# Load raw data Snowflake query
def raw_query():
    st.header("Raw Snowflake Query")
    with st.expander("View Query"):
        code = st.code(processing.QUERY, language="sql")
    return code
