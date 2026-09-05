"""
Lab: Batch processing with Spark + MinIO
----------------------------------------
Reads a text file from the shared Bronze bucket, counts word frequency, and
writes the result to the shared Silver bucket.

Setup (run once, from your host terminal):
    docker exec -it namenode hdfs dfs -mkdir -p /labs/batch/input
    echo "spark is great spark is fast hdfs is reliable" > /tmp/sample.txt
    docker cp /tmp/sample.txt namenode:/tmp/sample.txt
    docker exec -it namenode hdfs dfs -put /tmp/sample.txt /labs/batch/input/sample.txt

Run:
    docker exec -it spark-master spark-submit \
        --master spark://spark-master:7077 \
        /opt/spark-apps/batch_wordcount.py

Check the output:
    docker exec -it namenode hdfs dfs -cat /labs/batch/output/part-*
"""
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, split, col

INPUT_PATH = os.getenv("BATCH_INPUT_PATH", "s3a://bronze/batch/input/sample.txt")
OUTPUT_PATH = os.getenv("BATCH_OUTPUT_PATH", "s3a://silver/batch/output")


def s3a_builder(builder):
    endpoint = os.getenv("MINIO_ENDPOINT", "http://minio.bigdata.svc.cluster.local:9000")
    return (builder
            .config("spark.hadoop.fs.s3a.endpoint", endpoint)
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.access.key", os.environ["MINIO_ROOT_USER"])
            .config("spark.hadoop.fs.s3a.secret.key", os.environ["MINIO_ROOT_PASSWORD"]))

def main():
    spark = s3a_builder(SparkSession.builder.appName("BatchWordCount")).getOrCreate()

    df = spark.read.text(INPUT_PATH)
    words = df.select(explode(split(col("value"), r"\s+")).alias("word"))
    counts = words.groupBy("word").count().orderBy(col("count").desc())

    counts.show(truncate=False)

    (
        counts.coalesce(1)
        .write.mode("overwrite")
        .option("header", "true")
        .csv(OUTPUT_PATH)
    )
    print(f"Wrote results to {OUTPUT_PATH}")

    spark.stop()

if __name__ == "__main__":
    main()
