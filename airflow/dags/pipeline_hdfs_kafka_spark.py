"""
Lab: End-to-end pipeline orchestrated by Airflow
--------------------------------------------------
Ties together MinIO, Kafka and Spark in one DAG so students can see how a
real pipeline is scheduled and monitored, not just how each tool works alone.

Flow:
  1. ensure_buckets     -> create shared MinIO buckets for this run
  2. produce_kafka_events -> push a handful of JSON events to Kafka via kafka-python
  3. spark_batch_job    -> a PySpark job (run in-process via the pyspark pip
                           package installed in the Airflow image) that reads
                           from shared object storage and writes a summary back

This intentionally avoids SparkSubmitOperator/DockerOperator so it works
out of the box without extra Airflow connections - good enough for teaching.
Once students are comfortable, point them at SparkSubmitOperator or
DockerOperator as a "level up" exercise.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "instructor",
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}


def ensure_buckets():
    from minio import Minio

    client = Minio(
        os.getenv("MINIO_ENDPOINT", "minio.bigdata.svc.cluster.local:9000").removeprefix("http://"),
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )
    for bucket in ["bronze", "silver", "gold"]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    print("MinIO buckets ready")


def produce_kafka_events():
    from kafka import KafkaProducer

    producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka.bigdata.svc.cluster.local:9092"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    events = [
        {"user_id": i, "action": "purchase", "amount": 10 + i, "ts": datetime.utcnow().isoformat()}
        for i in range(1, 6)
    ]
    for event in events:
        producer.send("pipeline-events", event)
    producer.flush()
    print(f"Sent {len(events)} events to topic 'pipeline-events'")


def spark_batch_job():
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .appName("AirflowTriggeredBatchJob")
        .master(os.environ["SPARK_MASTER"])
        .config("spark.hadoop.fs.s3a.endpoint", os.environ["MINIO_ENDPOINT"])
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.access.key", os.environ["MINIO_ROOT_USER"])
        .config("spark.hadoop.fs.s3a.secret.key", os.environ["MINIO_ROOT_PASSWORD"])
        .getOrCreate()
    )

    data = [("purchase", 5), ("click", 12), ("view", 30)]
    df = spark.createDataFrame(data, ["action", "count"])
    df.show()

    df.coalesce(1).write.mode("overwrite").option("header", "true").csv(
        "s3a://gold/pipeline/output"
    )
    spark.stop()
    print("Spark batch job complete, results in s3a://gold/pipeline/output")


with DAG(
    dag_id="pipeline_minio_kafka_spark",
    description="End-to-end lab: MinIO + Kafka + Spark orchestrated by Airflow",
    default_args=default_args,
    schedule=None,  # trigger manually for labs
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["lab", "integration"],
) as dag:

    t1 = PythonOperator(task_id="ensure_buckets", python_callable=ensure_buckets)
    t2 = PythonOperator(task_id="produce_kafka_events", python_callable=produce_kafka_events)
    t3 = PythonOperator(task_id="spark_batch_job", python_callable=spark_batch_job)

    t1 >> t2 >> t3
