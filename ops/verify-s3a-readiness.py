"""Small, non-mutating S3A readiness check for the Kubernetes Spark cluster."""

import os

from pyspark.sql import SparkSession

MASTER_URL = "spark://spark-master.bigdata.svc.cluster.local:7077"
BRONZE_PATH = "s3a://bronze/fhvhv/2025/fhvhv_tripdata_2025.parquet"


def main() -> None:
    spark = (
        SparkSession.builder.master(MASTER_URL)
        .appName("s3a-readiness-check")
        .config("spark.driver.host", os.environ["SPARK_DRIVER_HOST"])
        .config("spark.driver.bindAddress", "0.0.0.0")
        .getOrCreate()
    )
    try:
        hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
        print(f"S3A_IMPL={hadoop_conf.get('fs.s3a.impl')}")
        print(f"BRONZE_SAMPLE_ROWS={spark.read.parquet(BRONZE_PATH).limit(1).count()}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
