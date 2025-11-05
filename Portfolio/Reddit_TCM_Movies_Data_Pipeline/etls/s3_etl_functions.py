import s3fs

from utils.constants import AWS_ACCESS_KEY_ID, AWS_REGION, AWS_SECRET_ACCESS_KEY


# Connect to S3
def connect_to_s3():
    try:
        s3 = s3fs.S3FileSystem(
            anon=False,
            key=AWS_ACCESS_KEY_ID,
            secret=AWS_SECRET_ACCESS_KEY,
            client_kwargs={"region_name": AWS_REGION},
        )
        return s3
    except Exception as e:
        print(e)


# Check if the bucket exists. If not create the bucket
def create_bucket_if_not_exist(s3: s3fs.S3FileSystem, bucket: str):
    try:
        if not s3.exists(bucket):
            s3.mkdir(bucket, region_name=AWS_REGION)
            print('Bucket "' + bucket + '" created.')
        else:
            print("Bucket already exists.")
    except Exception as e:
        print(e)


# Try to upload the .CSV file
def upload_to_s3(s3: s3fs.S3FileSystem, file_path: str, bucket: str, s3_file_name: str):
    try:
        # "bucket +'/raw/' + s3_file_name" is the destination file
        s3.put(file_path, bucket + "/raw/" + s3_file_name)
        print(".CSV file has been uploaded to S3.")
    except FileNotFoundError:
        print("The .CSV file was not found.")
