"""Demo app in Streamlit for new cluster detection
"""
import streamlit as st
import matplotlib.pyplot as plt
from numerize.numerize import numerize
from utils import loading, processing
from st_aggrid import GridOptionsBuilder, AgGrid


st.set_page_config(page_title="New Clustering Prototype", page_icon="gear")
st.title("New Clustering Prototype")

# Set filepaths for .csv upload
BUSINESS_INFO_FP = r"/Users/cxi/datascience/clustering_prototype/cluster_names_experiences.csv"
# FULL_DATA_FP = r"/Users/cxi/Downloads/full_cluster_data.csv"
GROUPBY_FP = r"/Users/cxi/datascience/clustering_prototype/clusters_groupby.csv"

# Business selectio
BUSINESS_LOOKUP = loading.initialize_businesses(BUSINESS_INFO_FP)
ACCOUNTS = BUSINESS_LOOKUP["name"]

st.sidebar.write("Business Filter Selection")
business_id = st.sidebar.selectbox("Select an account", options=ACCOUNTS)

# Experience selection
FILTERED_BUSINESS_LOOKUP = loading.filter_businesses(BUSINESS_LOOKUP, business_id)
EXPERIENCES = FILTERED_BUSINESS_LOOKUP["experience_key"]

experience_key = st.sidebar.selectbox("Select an experience key", options=EXPERIENCES)

# Add additional filters
st.sidebar.write("Additional Filter Selection")
# Filter for cluster type: new or existing
is_new = st.sidebar.selectbox("Select a cluster type", options=["All", "New only", "Existing only"])

# Load filtered dataframe containing all cluster data
DF_FULL = loading.initialize_full_data(GROUPBY_FP)
DF_TABLE_DISPLAY = DF_FULL.drop("num_clusters", axis=1)

# Filter full dataframe containing all business-leve cluster and search term data
DF_FULL_BUSINESS = processing.process_full_df(DF_TABLE_DISPLAY, business_id, experience_key)

# Separate into tabs
tab1, tab2, tab3 = st.tabs(["Business-Level Cluster Table", "Data Exploration", "Raw Data"])

with tab1:
    # Hero numbers
    col1, col2, col3 = st.columns(3)
    # TODO: add more hero numbers
    # Get number of new clusters
    num_new_clusters = len(DF_FULL_BUSINESS[DF_FULL_BUSINESS["is_new"] == True])
    pct_new = "{}%".format(round(num_new_clusters / len(DF_FULL_BUSINESS) * 100), 2)
    col1.metric("Count of New Clusters", numerize(num_new_clusters))
    col2.metric("Count of All Clusters", numerize(len(DF_FULL_BUSINESS)))
    col3.metric("% All Clusters", pct_new)

    # Additional configuration specific to any additional filters the user may have selected
    if is_new == "All":
        st.header("All Clusters")
        df_sorted = DF_FULL_BUSINESS.sort_values(by="cluster_searches", ascending=False)
        AgGrid(df_sorted, height=700, theme="dark", fit_columns_on_grid_load=True)

    if is_new == "New only":
        df_filtered_cluster = processing.filter_clusters(DF_FULL_BUSINESS, is_new)
        st.header("All New Clusters")
        df_sorted_cluster = df_filtered_cluster.sort_values(by="cluster_searches", ascending=False)
        AgGrid(df_sorted_cluster, height=700, theme="dark", fit_columns_on_grid_load=True)

    if is_new == "Existing only":
        df_filtered_cluster = processing.filter_clusters(DF_FULL_BUSINESS, is_new)
        st.header("All Existing (Non-New) Clusters")
        df_sorted_cluster = df_filtered_cluster.sort_values(by="cluster_searches", ascending=False)
        AgGrid(df_sorted_cluster, height=700, theme="dark", fit_columns_on_grid_load=True)

with tab2:
    st.header("Data Exploration")
    st.write(
        "We want to get a better idea of the data we're working with. Things like distribution of new clusters across businesses, thresholding, etc."
    )

    # Filter dataframe for the histogram...grouping a .csv file is annoying
    # First filter for all new clusters, across all accounts
    df_hist_count = DF_FULL[DF_FULL["is_new"] == True]
    # Then group by name and experience key and find the sum of new clusters across each experience
    df_hist_count = df_hist_count.groupby(
        by=["business_id", "name", "experience_key"], as_index=False
    ).sum()
    df_lim = df_hist_count[df_hist_count["num_clusters"] <= 200]

    # Plot histogram of cluster count distribution
    fig, ax = plt.subplots()
    ax.hist(df_lim["num_clusters"])
    ax.set_xlabel("Number of New Clusters")
    ax.set_ylabel("Number of Experiences")
    st.markdown("**Distribution: Count of New Clusters, by Experience**")
    st.pyplot(fig)

    # Calculate new clusters as a % of the total
    df_hist_pct = DF_FULL.groupby(
        by=["business_id", "name", "experience_key"], as_index=False
    ).sum()
    df_hist_pct["pct_total"] = round(100 * (df_hist_pct["is_new"] / df_hist_pct["num_clusters"]), 2)

    # Plot histogram of cluster % distribution
    fig, ax = plt.subplots()
    ax.hist(df_hist_pct["pct_total"])
    ax.set_xlabel("New Clusters as a % of Total")
    ax.set_ylabel("Number of Experiences")
    st.markdown("**Distribution: New Clusters as a % of Total, by Experience**")
    st.pyplot(fig)

with tab3:
    # Raw Snowflake query
    st.header("Raw Snowflake Query")
    with st.expander("Raw Snowflake Query"):
        st.code(processing.QUERY, language="sql")
    # Raw data table, all businesses, grouped by search cluster
    build_config = GridOptionsBuilder.from_dataframe(DF_TABLE_DISPLAY)
    build_config.configure_pagination(paginationPageSize=200)
    build_config = build_config.build()
    st.header("Raw Data Table")
    AgGrid(DF_TABLE_DISPLAY, height=1000, theme="dark", gridOptions=build_config)

    # Allow users to export raw data table to .csv table
    raw_data_csv = loading.convert_df(DF_FULL)
    st.download_button(
        label="Download raw data as CSV",
        data=raw_data_csv,
        file_name="large_df.csv",
        mime="text/csv",
    )
