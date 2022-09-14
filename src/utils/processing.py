"""Functions to clean, process and manipulate data
"""
import pandas as pd


def process_full_df(df, business_id, experience_key):
    # Filter the entire main dataset to only contain data for that business/experience
    df_full_filtered = df.loc[
        (df["name"] == business_id) & (df["experience_key"] == experience_key)
    ]
    # Drop unneccesary columns
    df_full_processed = df_full_filtered.drop(
        ["business_id", "name", "experience_key", "cluster_runs_id", "cluster_id"], axis=1
    )
    return df_full_processed
