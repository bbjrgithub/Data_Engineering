FROM apache/airflow:3.0.6-python3.9

COPY requirements.txt /opt/airflow/

USER root
RUN apt-get update && apt-get install -y gcc python3-dev

USER airflow

RUN pip install apache-airflow==3.0.6 --no-cache-dir -r /opt/airflow/requirements.txt
