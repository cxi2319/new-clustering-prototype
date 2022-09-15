"""Functions to clean, process and manipulate data
"""
import pandas as pd
import streamlit as st

QUERY = """
with get_searches as (
    select
        business_id,
        experience_key,
        tokenizer_normalized_query as search_term,
        count(distinct query_id) as searches
    from prod_data_hub.answers.searches
    where date(timestamp) > dateadd(day, -30, current_date())
    group by 1,2,3
),
all_clusters as (
select
    cr.business_id,
    business_name as name,
    cr.experience_key,
    cluster_runs_id,
    cluster_id,
    cluster_name,
    array_contains(cluster_id, new_clusters) is_new,
    get_searches.search_term,
    sum(searches) as st_searches,
    sum(st_searches) over (partition by cluster_id) as cluster_searches
from prod_data_hub.answers.current_cluster_search_terms ccst
join prod_data_hub.answers.cluster_runs cr on ccst.cluster_runs_id = cr.id
join prod_data_science.public.nn_clusters nn on cr.id = nn.id_tested
join get_searches
    on cr.business_id = get_searches.business_id
    and cr.experience_key = get_searches.experience_key
    and ccst.search_term = get_searches.search_term
join prod_product.public.yext_accounts on cr.business_id = yext_accounts.business_id
group by 1,2,3,4,5,6,7,8
order by 1 desc, 10 desc, 9 desc
)

select
    business_id,
    name,
    experience_key,
    cluster_name,
    is_new,
    cluster_searches,
    count(distinct cluster_name) as num_clusters
from all_clusters
group by 1,2,3,4,5,6
order by 1 desc
"""


def process_full_df(df, business_id, experience_key):
    # Filter the entire main dataset to only contain data for that business/experience
    df_full_filtered = df.loc[
        (df["name"] == business_id) & (df["experience_key"] == experience_key)
    ]
    # Drop unneccesary columns
    df_full_processed = df_full_filtered.drop(["business_id", "name", "experience_key"], axis=1)
    # Sort by is_new = true, descending as the default sort order
    df_full_processed = df_full_processed.sort_values(by="is_new", ascending=False)
    return df_full_processed


st.cache()


def filter_clusters(df, filter):
    # Filter the main dataset to only include clusters based on user filter
    if filter == "New only":
        new = True
        df_filtered_cluster = df[df["is_new"] == new]
    elif filter == "Existing only":
        new = False
        df_filtered_cluster = df[df["is_new"] == new]
    return df_filtered_cluster
