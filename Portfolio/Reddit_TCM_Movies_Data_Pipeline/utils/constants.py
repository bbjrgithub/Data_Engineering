import configparser
import os

parser = configparser.RawConfigParser()
"""
".." reads one directory up from the "utils" directory so goes to
/config and then read config.conf in /config
"""
parser.read(os.path.join(os.path.dirname(__file__), "../config/config.conf"))

REDDIT_SECRET_KEY = parser.get("api_keys", "reddit_secret_key")
REDDIT_CLIENT_ID = parser.get("api_keys", "reddit_client_id")

DATABASE_HOST = parser.get("database", "database_host")
DATABASE_NAME = parser.get("database", "database_name")
DATABASE_PORT = parser.get("database", "database_port")
DATABASE_USER = parser.get("database", "database_username")
DATABASE_PASSWORD = parser.get("database", "database_password")

AWS_ACCESS_KEY_ID = parser.get("aws", "aws_access_key_id")
AWS_SECRET_ACCESS_KEY = parser.get("aws", "aws_secret_access_key")
AWS_REGION = parser.get("aws", "aws_region")
AWS_BUCKET_NAME = parser.get("aws", "aws_bucket_name")

# For saving output from DAG input from AWS
DATA_INPUT_PATH = parser.get("file_paths", "input_path")
DATA_OUTPUT_PATH = parser.get("file_paths", "output_path")

POST_FIELDS = (
    "id",
    "title",
    "selftext",
    "score",
    "num_comments",
    "author",
    "created_utc",
    "url",
    "upvote_ratio",
    "over_18",
    "edited",
    "spoiler",
    "stickied",
)

# Redshift cluster config
REDSHIFT_HOSTNAME = parser.get("aws", "redshift_hostname")
REDSHIFT_DB_NAME = parser.get("aws", "redshift_db_name")
REDSHIFT_PORT = parser.get("aws", "redshift_port")
REDSHIFT_USERNAME = parser.get("aws", "redshift_username")
REDSHIFT_PASSWORD = parser.get("aws", "redshift_password")
REDSHIFT_IAM_ROLE = parser.get("aws", "redshift_iam_role")
