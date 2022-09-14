"""Functions to load/filter datasets.
"""

import pandas as pd

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
def filter_businesses(df, business):
    df_filtered = df[df["name"] == business]
    return df_filtered
