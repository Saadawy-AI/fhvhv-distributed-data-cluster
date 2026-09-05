"""Verify that a Spark job executes tasks on each of the three worker pods."""

import socket

from pyspark.sql import SparkSession


def main() -> None:
    spark = SparkSession.builder.appName("parallel-worker-probe").getOrCreate()
    hosts = (
        spark.sparkContext.parallelize(range(96), 96)
        .map(lambda _: socket.gethostname())
        .distinct()
        .collect()
    )
    print("Workers that executed tasks:", sorted(hosts))
    if len(hosts) < 3:
        raise RuntimeError(f"Expected tasks on 3 workers, observed: {hosts}")
    spark.stop()


if __name__ == "__main__":
    main()
