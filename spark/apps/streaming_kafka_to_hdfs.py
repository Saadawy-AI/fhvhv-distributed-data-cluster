"""
Lab: Streaming with Spark Structured Streaming + Kafka + MinIO
---------------------------------------------------------------
Reads JSON events from a Kafka topic and writes them to the shared Bronze
bucket as they arrive.

Setup (create the topic once):
    docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --create \
        --topic events --bootstrap-server kafka:9092 \
        --partitions 1 --replication-factor 1

Produce a few test messages (from your host terminal):
    docker exec -it kafka /opt/kafka/bin/kafka-console-producer.sh \
        --topic events --bootstrap-server kafka:9092
    > {"user_id": 1, "action": "click", "ts": "2026-07-08T10:00:00"}
    > {"user_id": 2, "action": "view",  "ts": "2026-07-08T10:00:05"}

Run this job (it keeps running until you stop it, Ctrl+C):
    docker exec -it spark-master spark-submit \
        --master spark://spark-master:7077 \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0 \
        /opt/spark-apps/streaming_kafka_to_hdfs.py

Check results while it runs:
    docker exec -it namenode hdfs dfs -ls /labs/streaming/output
    docker exec -it namenode hdfs dfs -cat /labs/streaming/output/*.json
"""
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka.bigdata.svc.cluster.local:9092")
TOPIC = "events"
OUTPUT_PATH = os.getenv("STREAM_OUTPUT_PATH", "s3a://bronze/streaming/output")
CHECKPOINT_PATH = os.getenv("STREAM_CHECKPOINT_PATH", "s3a://bronze/streaming/checkpoint")

schema = StructType([
    StructField("user_id", IntegerType()),
    StructField("action", StringType()),
    StructField("ts", StringType()),
])

def main():
    endpoint = os.getenv("MINIO_ENDPOINT", "http://minio.bigdata.svc.cluster.local:9000")
    spark = (SparkSession.builder.appName("KafkaToMinIOStreaming")
             .config("spark.hadoop.fs.s3a.endpoint", endpoint)
             .config("spark.hadoop.fs.s3a.path.style.access", "true")
             .config("spark.hadoop.fs.s3a.access.key", os.environ["MINIO_ROOT_USER"])
             .config("spark.hadoop.fs.s3a.secret.key", os.environ["MINIO_ROOT_PASSWORD"])
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")

    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )

    parsed = (
        raw.selectExpr("CAST(value AS STRING) as json_str")
        .select(from_json(col("json_str"), schema).alias("data"))
        .select("data.*")
    )

    query = (
        parsed.writeStream
        .format("json")
        .option("path", OUTPUT_PATH)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .outputMode("append")
        .trigger(processingTime="10 seconds")
        .start()
    )

    query.awaitTermination()

if __name__ == "__main__":
    main()
