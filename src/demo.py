import streamlit as st
import pandas as pd
from utils import loading, processing
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode


st.set_page_config(page_title="New Clustering Prototype", page_icon="gear")
st.title("New Clustering Prototype")

# Set filepaths for .csv upload
BUSINESS_INFO_FP = r"/Users/cxi/datascience/clustering_prototype/cluster_names_experiences.csv"
FULL_DATA_FP = r"/Users/cxi/Downloads/full_cluster_data.csv"

# Business selection
BUSINESS_LOOKUP = loading.initialize_businesses(BUSINESS_INFO_FP)
ACCOUNTS = BUSINESS_LOOKUP["name"]

st.sidebar.write("Business Filter Selection")
business_id = st.sidebar.selectbox("Select an account", options=ACCOUNTS)

# Experience selection
FILTERED_BUSINESS_LOOKUP = loading.filter_businesses(BUSINESS_LOOKUP, business_id)
EXPERIENCES = FILTERED_BUSINESS_LOOKUP["experience_key"]

experience_key = st.sidebar.selectbox("Select an experience key", options=EXPERIENCES)

# Load filtered dataframe containing all cluster data for that business and experience
FULL_DF = loading.initialize_full_data(FULL_DATA_FP)
# Process and use AgGrid to visualize
df_full_processed = processing.process_full_df(FULL_DF, business_id, experience_key)
st.header("All Clusters:")
AgGrid(df_full_processed)
