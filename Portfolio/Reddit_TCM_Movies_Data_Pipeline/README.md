# Reddit TCM Movies Data Pipeline Project

Technologies used: *Airflow*, *Docker*, *Python*, *AWS S3 & Redshift*
&nbsp;

This is a re-implementation of Yusuf Ganiyu's (CodeWithYu) [Reddit Data Pipeline Engineering](https://github.com/airscholar/RedditDataEngineering) project. The pipeline extracts data from the /r/TurnerClassicMovies subreddit and loads it into Redshift.

I followed along with the project, typing in the code by hand and changing the names of various variables/functions so that I could understand the flow of the code. I made the following adjustments/additions:

1. Updated the code to use an Airflow 3.0.6 Docker image and Python 3.9.
   - Python 3.9 had to be used because current version of ```flask_appbuilder``` used in Airflow doesn't support a later version.
2. As I am running Fedora I edited the ```docker-compose.yaml``` and added SELinux permissions for the volume mounts.
3. Added support to output the posts to parquet format.
4. Did not remove any of the parsed fields from the Reddit posts and did not use Glue/Athena to perform any transformations. Instead added code to load the .CSV into Redshift.
5. Changed ```constants.py``` to use ```RawConfigParser``` instead of ```ConfigParser``` so that special characters could be used in the Redshift cluster password without escaping them.

## Prerequisites

- Fedora or other distributive that uses SELinux.
  - If SELinux is not being used the permissions for the volume mounts need to be removed from ```docker-compose.yaml```.
- Docker and Docker Compose.
- Python 3.9.
- An AWS account with appropriate permissions for S3 and Redshift.
- An existing Redshift cluster.
- A [Reddit API key and OAUTH Client ID/App ID](https://www.reddit.com/r/reddit.com/wiki/api/) (Also see [here.](https://www.reddit.com/r/redditdev/comments/hasnnc/comment/ijwbc20/))

## Installation

1. [Create](S3_And_Redshift_Setup.md) the S3 bucket and Redshift cluster if they are not already created.

2. Clone the repository.

3. Create and activate a virtual environment:

       $ virtualenv -p python3.9 .venv39
       $ source .venv39/bin/activate

4. Install the Python dependencies:

       $ pip install -r requirements.txt

5. Rename the ```config.conf.example``` file and input configuration:

       $ mv config/config.conf.example config/config.conf

6. May need to run the following:

       (Allow Airflow to read it's configuration)
       $ chmod a+rw config/airflow.cfg

       (Allow Airflow to write logs)
       $ chmod 777 ./logs"

7. Start the containers:

       $ docker-compose up -d

8. Launch the Airflow web UI:

       http://localhost:8080

## Demo

![](Reddit_TCM_Movies_Data_Pipeline_Project__10-31-2025.gif)