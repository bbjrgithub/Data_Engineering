import redshift_connector

from utils.constants import (
    REDSHIFT_DB_NAME,
    REDSHIFT_HOSTNAME,
    REDSHIFT_IAM_ROLE,
    REDSHIFT_PASSWORD,
    REDSHIFT_PORT,
    REDSHIFT_USERNAME,
)


def connect_to_redshift():
    try:
        redshift_conn = redshift_connector.connect(
            host=REDSHIFT_HOSTNAME,
            database=REDSHIFT_DB_NAME,
            port=REDSHIFT_PORT,
            user=REDSHIFT_USERNAME,
            password=REDSHIFT_PASSWORD,
        )
        print("Connected to Redshift")
        return redshift_conn
    except Exception as e:
        print(e)


def copy_to_redshift_db(
    redshift_conn: redshift_connector.connect,
    bucket: str,
    s3_file_name: str,
):
    # Enable autocommit to commit changes to database
    redshift_conn.autocommit = True
    # Create a Cursor object
    cursor = redshift_conn.cursor()

    query = bucket + "/raw/" + s3_file_name

    # Check if forum_posts_data table exists and if not create it
    try:
        cursor.execute("select * from forum_posts_data limit 1")
        print('"forum_posts_data" table is already in Redshift database.')
    except redshift_connector.Error as e:
        print(e)
        cursor.execute(
            "create table forum_posts_data(id text not null, title text not null, selftext text, score integer, num_comments integer, author varchar(25) not null, created_utc text not null, url text not null, upvote_ratio integer, over_18 varchar(5), edited varchar(5),spoiler varchar(5), stickied varchar(5))"
        )
        print('"forum_posts_data" table has been created in Redshift database.')

    # Copy the .CSV to the forum_posts_data table. TRUNCATECOLUMNS is used as
    # Redshift doesn't have an unlimited text field so the selftext field can't
    # be fully stored
    cursor.execute(
        "copy forum_posts_data from "
        + "'s3://"
        + query
        + "' credentials "
        + "'aws_iam_role="
        + REDSHIFT_IAM_ROLE
        + "' csv ignoreheader 1 truncatecolumns"
    )
    print(".CSV file has been copied to Redshift database.")

    # Query the forum_posts_data table and retrieve the result to print to logs
    cursor.execute("select * from forum_posts_data limit 5")
    result: tuple = cursor.fetchall()
    print(result)
