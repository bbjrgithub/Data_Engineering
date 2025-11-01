from etls.redshift_etl_functions import (
    connect_to_redshift,
    copy_to_redshift_db,
)
from utils.constants import AWS_BUCKET_NAME


def copy_to_redshift_pipeline(task_instance):
    # From Browse -> XComs in Airflow UI
    file_path = task_instance.xcom_pull(
        task_ids="reddit_tcm_movies_extraction", key="return_value"
    )

    # Retrieve Redshift connection object
    redshift_conn = connect_to_redshift()
    """
    file_path is a tuple that contains the path to the .CSV and Parquet files
    so [0] is used to specify only the .CSV file and .split gets the last part
    of the file name
     
    Not using [0] will cause the Parquet file to be uploaded too for some
    reason, even though .split is used
    """
    # Copy .CSV to Redshift cluster
    copy_to_redshift_db(redshift_conn, AWS_BUCKET_NAME, file_path[0].split("/")[-1])
