import sys

import numpy as np
import pandas as pd
import praw
from praw import Reddit

from utils.constants import POST_FIELDS


def connect_to_reddit(reddit_client_id, reddit_secret_key, user_agent) -> Reddit:
    try:
        reddit = praw.Reddit(
            client_id=reddit_client_id,
            client_secret=reddit_secret_key,
            user_agent=user_agent,
        )
        print("Connection to Reddit established.")
        return reddit
    except Exception as error:
        print(error)
        sys.exit(1)


def extract_posts(
    reddit_instance: Reddit, subreddit: str, time_filter: str, limit=None
):
    subreddit = reddit_instance.subreddit(subreddit)
    posts = subreddit.top(time_filter=time_filter, limit=limit)

    post_lists = []

    for post in posts:
        post_dict = vars(post)
        post = {key: post_dict[key] for key in POST_FIELDS}
        post_lists.append(post)

    return post_lists


# Clean data
def transform_data(post_dataframe: pd.DataFrame):
    post_dataframe["created_utc"] = pd.to_datetime(
        post_dataframe["created_utc"], unit="s"
    )
    post_dataframe["over_18"] = np.where(
        (post_dataframe["over_18"] == False), True, False
    )
    # Ruff said to do it this way but it doesn't work:
    # post_dataframe["over_18"] = np.where(not post_dataframe["over_18"])
    post_dataframe["author"] = post_dataframe["author"].astype(str)
    edited_mode = post_dataframe["edited"].mode()
    # If edited_mode is True/False convert to boolean
    post_dataframe["edited"] = np.where(
        post_dataframe["edited"].isin([True, False]),
        post_dataframe["edited"],
        edited_mode,
    ).astype(bool)
    post_dataframe["num_comments"] = post_dataframe["num_comments"].astype(int)
    post_dataframe["score"] = post_dataframe["score"].astype(int)
    post_dataframe["upvote_ratio"] = post_dataframe["upvote_ratio"].astype(int)
    post_dataframe["selftext"] = post_dataframe["selftext"].astype(str)
    post_dataframe["title"] = post_dataframe["title"].astype(str)

    return post_dataframe


def load_data_to_csv(data: pd.DataFrame, path: str):
    data.to_csv(path, index=False)


def load_data_to_parquet(data: pd.DataFrame, path: str):
    data.to_parquet(path, engine="pyarrow", compression="snappy")
