from etls.s3_etl_functions import (
    connect_to_s3,
    create_bucket_if_not_exist,
    upload_to_s3,
)
from utils.constants import AWS_BUCKET_NAME


def upload_to_s3_pipeline(task_instance):
    # From Browse -> XComs in Airflow UI
    file_path = task_instance.xcom_pull(
        task_ids="reddit_tcm_movies_extraction", key="return_value"
    )

    s3 = connect_to_s3()
    create_bucket_if_not_exist(s3, AWS_BUCKET_NAME)
    """
    file_path is a tuple that contains the path to the .CSV and Parquet files
    so [0] is used to specify only the .CSV file and .split gets the last part
    of the file name
     
    Not using [0] will cause the Parquet file to be uploaded too for some
    reason, even though .split is used
    """
    upload_to_s3(s3, file_path[0], AWS_BUCKET_NAME, file_path[0].split("/")[-1])
