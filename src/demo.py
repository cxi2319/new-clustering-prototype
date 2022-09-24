"""Demo app in Streamlit for new cluster detection
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from numerize.numerize import numerize
from utils import loading, processing
from st_aggrid import GridOptionsBuilder, AgGrid
from os.path import exists

DEFAULT_DATE = "2022_09_12"

st.set_page_config(page_title="New Clustering Prototype", page_icon="gear")
st.title("New Clustering Prototype")

# Get the current date
today = date.today()
# Get the Monday of the current week
week_start = processing.first_day_of_week(today)

# Get the date for the clustering run
filepath_date = loading.get_dates(week_start)

# Get filepaths, first checking to see if the filepath exists. If not, set default date to 9/12
if exists(processing.get_filepath(filepath_date, type="Business Info")):
    business_info_fp = processing.get_filepath(filepath_date, type="Business Info")
else:
    st.markdown(
        "**Sorry! We have not yet loaded clustering data for {}. Setting date to default and loading data from the default date: 2022-09-12.**".format(
            week_start
        )
    )
    business_info_fp = processing.get_filepath(DEFAULT_DATE, type="Business Info")

if exists(processing.get_filepath(filepath_date, type="Group By")):
    groupby_fp = processing.get_filepath(filepath_date, type="Group By")
else:
    groupby_fp = processing.get_filepath(DEFAULT_DATE, type="Group By")

# Business selection widget
business_lookup = loading.initialize_businesses(business_info_fp)
accounts = business_lookup["name"]

st.sidebar.write("Business Filter Selection")
business_id = st.sidebar.selectbox("Select an account", options=accounts)

# Experience selection widget
filtered_business_lookup = loading.filter_businesses(business_lookup, business_id)
experiences = filtered_business_lookup["experience_key"]

experience_key = st.sidebar.selectbox("Select an experience key", options=experiences)

# Add additional filters
st.sidebar.write("Additional Filter Selection")
# Filter for cluster type: new or existing
is_new = st.sidebar.selectbox("Select a cluster type", options=["All", "New only", "Existing only"])

# Load full dataframe that contains all cluster data
df_full = loading.initialize_full_data(groupby_fp)
df_table_display = df_full.drop("num_clusters", axis=1)

# Filter the full dataframe based on the user inputs for business and experience
df_full_business = processing.process_full_df(df_table_display, business_id, experience_key)

# Separate into tabs
tab1, tab2, tab3 = st.tabs(["Business-Level Cluster Table", "Data Exploration", "Raw Data"])

with tab1:
    # Hero number columns
    col1, col2, col3, col4 = st.columns(4)
    # Get number of new clusters
    num_new_clusters = len(df_full_business[df_full_business["is_new"] == True])
    try:
        pct_new = "{}%".format(round(num_new_clusters / len(df_full_business) * 100), 2)
    except ZeroDivisionError:
        print(
            "No recent new clusters found for this business. Please select another business with clustering data from the past run."
        )

    # Get the highest 'table position' of a new cluster for a given account
    sort_searches_desc = df_full_business.sort_values(by="cluster_searches", ascending=False)
    try:
        top_nc_pos = processing.get_top_nc(sort_searches_desc)
    except ValueError:
        print(
            "No recent new clusters found for this business. Please select another business with clustering data from the past run."
        )

    # Display metrics
    try:
        col1.metric(
            "Top New Cluster Pos.",
            numerize(top_nc_pos),
            help="This measures the relative importance of the top-performing new cluster by determining where it would rank in a table sorted by all cluster searches, descending.",
        )
    except NameError:
        col1.header("N/A")
        st.write(
            "No recent new clusters found for this business. Please select another business with clustering data from the past run."
        )
    col2.metric("Count of New Clusters", numerize(num_new_clusters))
    col3.metric("Count of All Clusters", numerize(len(df_full_business)))
    try:
        col4.metric("% All Clusters", pct_new)
    except NameError:
        col4.header("N/A")
    # Additional configuration specific to any additional filters the user may have selected
    if is_new == "All":
        st.header("All Clusters")
        df_sorted_isnew = df_full_business.sort_values(by="cluster_searches", ascending=False)
        AgGrid(df_sorted_isnew, height=700, theme="dark", fit_columns_on_grid_load=True)

    if is_new == "New only":
        df_filtered_cluster = processing.filter_clusters(df_full_business, is_new)
        st.header("All New Clusters")
        df_sorted_cluster = df_filtered_cluster.sort_values(by="cluster_searches", ascending=False)
        AgGrid(df_sorted_cluster, height=700, theme="dark", fit_columns_on_grid_load=True)

    if is_new == "Existing only":
        df_filtered_cluster = processing.filter_clusters(df_full_business, is_new)
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
    df_hist_isnew = df_full[df_full["is_new"] == True]
    # Then group by name and experience key and find the sum of new clusters across each experience
    df_hist_isnew = df_hist_isnew.groupby(
        by=["business_id", "name", "experience_key"], as_index=False
    ).sum()
    # Limit the population to those with less than 200 new clusters to remove outliers
    df_lim = df_hist_isnew[df_hist_isnew["num_clusters"] <= 200]

    # Plot histogram of cluster count distribution
    fig, ax = plt.subplots()
    ax.hist(df_lim["num_clusters"])
    ax.set_xlabel("Number of New Clusters")
    ax.set_ylabel("Number of Experiences")
    st.markdown("**Distribution: Count of New Clusters, by Experience**")
    st.pyplot(fig)
    st.write(
        "Looks like the vast majority of accounts have 25 or fewer new clusters. This is helpful to know from a notifications perspective. We can group notifications in batches of 20, so it is about the size of a maximum batch."
    )

    # Calculate new clusters as a % of the total
    df_hist_all = df_full.groupby(
        by=["business_id", "name", "experience_key"], as_index=False
    ).sum()
    df_hist_all["pct_total_clusters"] = round(
        100 * (df_hist_all["is_new"] / df_hist_all["num_clusters"]), 2
    )
    # Plot histogram of cluster % distribution
    fig, ax = plt.subplots()
    ax.hist(df_hist_all["pct_total_clusters"])
    ax.set_xlabel("New Clusters as a % of All Clusters")
    ax.set_ylabel("Number of Experiences")
    st.markdown("**Distribution: New Clusters as a % of All Clusters, by Experience**")
    st.pyplot(fig)
    st.write(
        "Looks like new clusters generally account for less than 20% of all clusters. From a notifications perspective this is helpful to know for thresholding purposes."
    )

    # Calculate the search volume of new clusters relative to all cluster search volume
    # Get the total number of searches across all clusters for a business
    df_combined = pd.merge(
        df_hist_isnew,
        df_hist_all,
        how="inner",
        left_on=["business_id", "name", "experience_key"],
        right_on=["business_id", "name", "experience_key"],
        suffixes=["_new", "_all"],
    )
    df_combined["pct_total_cluster_searches"] = round(
        100 * (df_combined["cluster_searches_new"] / df_combined["cluster_searches_all"]), 2
    )

    fig, ax = plt.subplots()
    ax.hist(df_combined["pct_total_cluster_searches"])
    ax.set_xlabel("New Cluster Searches as a % of All Cluster Searches")
    ax.set_ylabel("Number of Experiences")
    st.markdown(
        "**Distribution: New Cluster Searches as a % of All Cluster Searches, by Experience**"
    )
    st.pyplot(fig)

    # Calculate the average search volume (size) of a new cluster compared to average volume of all clusters
    # Calculate avg cluster sizes
    df_combined["avg_new_cluster_size"] = round(
        df_combined["cluster_searches_new"] / df_combined["num_clusters_new"]
    )
    df_combined["avg_cluster_size_all"] = round(
        df_combined["cluster_searches_all"] / df_combined["num_clusters_all"]
    )
    # Calculate the ratio of average new cluster size to all clusters
    df_combined["ratio_new_all"] = round(
        df_combined["avg_new_cluster_size"] / df_combined["avg_cluster_size_all"], 2
    )
    # Limit ratios to those <=1, as most new clusters seem to be smaller
    df_combined_lim = df_combined[df_combined["ratio_new_all"] <= 1]
    fig, ax = plt.subplots()
    ax.hist(df_combined_lim["ratio_new_all"])
    ax.set_xlabel("Ratio of Avg. New Cluster Size to Avg. of All Cluster Size")
    ax.set_ylabel("Number of Experiences")
    st.markdown("**Ratio of Avg. New Cluster Size to Avg. of All Cluster Size**")
    st.pyplot(fig)
    st.write("It seems like new clusters are generally smaller than the average cluster.")

with tab3:
    # Raw Snowflake query
    st.header("Raw Snowflake Query")
    with st.expander("View Query"):
        st.code(processing.QUERY, language="sql")
    # Raw data table, all businesses, grouped by search cluster
    build_config = GridOptionsBuilder.from_dataframe(df_table_display)
    build_config.configure_pagination(paginationPageSize=200)
    build_config = build_config.build()
    st.header("Raw Data Table")
    AgGrid(df_table_display, height=1000, theme="dark", gridOptions=build_config)

    # Allow users to export raw data table to .csv table
    raw_data_csv = loading.convert_df(df_full)
    st.download_button(
        label="Download raw data as CSV",
        data=raw_data_csv,
        file_name="large_df.csv",
        mime="text/csv",
    )
