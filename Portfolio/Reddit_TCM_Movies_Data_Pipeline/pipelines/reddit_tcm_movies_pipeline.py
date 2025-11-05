import pandas as pd

from etls.reddit_tcm_movies_etl import (
    connect_to_reddit,
    extract_posts,
    load_data_to_csv,
    load_data_to_parquet,
    transform_data,
)
from utils.constants import DATA_OUTPUT_PATH, REDDIT_CLIENT_ID, REDDIT_SECRET_KEY


def reddit_tcm_movies_pipeline(
    csv_file_name: str,
    parquet_file_name: str,
    subreddit: str,
    time_filter="month",  # Changed from "day" to get more than one day's worth of data
    limit=None,
):
    # Connect to Reddit instance
    instance = connect_to_reddit(REDDIT_CLIENT_ID, REDDIT_SECRET_KEY, "Scrape Agent")

    # Extract: Extract posts from the TurnerClassicMovies subreddit
    posts = extract_posts(instance, subreddit, time_filter, limit)
    post_dataframe = pd.DataFrame(posts)
    # Transform:
    post_dataframe = transform_data(post_dataframe)

    # Load:
    csv_file_path = f"{DATA_OUTPUT_PATH}/{csv_file_name}.csv"
    load_data_to_csv(post_dataframe, csv_file_path)
    parquet_file_path = f"{DATA_OUTPUT_PATH}/{parquet_file_name}.parquet"
    load_data_to_parquet(post_dataframe, parquet_file_path)

    return csv_file_path, parquet_file_path
