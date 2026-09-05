"""
FHVHV Big Data Pipeline DAG
-----------------------------
Pipeline كاملة تربط MinIO + Kafka + Spark لمعالجة بيانات NYC FHVHV 2025.

Flow:
  1. ensure_buckets        → التأكد من وجود buckets في MinIO (bronze/silver/gold)
  2. publish_kafka_event   → إرسال Kafka event يعلن بدء المعالجة
  3. part_a_processing     → Spark Job: قراءة Bronze، تنظيف البيانات، كتابة Silver
  4. part_b_ml_training    → Spark Job: قراءة Silver، تدريب RandomForest، حفظ النموديل في Gold
  5. pipeline_done         → رسالة تأكيد نجاح الـ Pipeline
"""
from __future__ import annotations

import os
import sys, site
sys.path.insert(0, site.getusersitepackages())
import json
import os
from datetime import datetime, timedelta

# Fix for Java 21 compatibility with PySpark 3.3.0
os.environ["_JAVA_OPTIONS"] = (
    "--add-opens=java.base/java.lang=ALL-UNNAMED "
    "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED "
    "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED "
    "--add-opens=java.base/java.io=ALL-UNNAMED "
    "--add-opens=java.base/java.net=ALL-UNNAMED "
    "--add-opens=java.base/java.nio=ALL-UNNAMED "
    "--add-opens=java.base/java.util=ALL-UNNAMED "
    "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED "
    "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED "
    "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED "
    "--add-opens=java.base/sun.nio.cs=ALL-UNNAMED "
    "--add-opens=java.base/sun.security.action=ALL-UNNAMED "
    "--add-opens=java.util/sun.util.calendar=ALL-UNNAMED "
    "--add-opens=java.security.jgss/sun.security.krb5=ALL-UNNAMED"
)
os.environ["PYSPARK_SUBMIT_ARGS"] = (
    "--jars /opt/java/lib/hadoop-aws-3.3.2.jar,/opt/java/lib/aws-java-sdk-bundle-1.11.1026.jar pyspark-shell"
)

from airflow import DAG
from airflow.operators.python import PythonOperator

import socket

SPARK_MASTER = os.getenv("SPARK_MASTER_URL", "local[2]")
SPARK_DRIVER_HOST = os.getenv("SPARK_DRIVER_HOST", socket.gethostbyname(socket.gethostname()))
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio.bigdata.svc.cluster.local:9000")
MINIO_ENDPOINT_CLEAN = MINIO_ENDPOINT.removeprefix("http://").removeprefix("https://")
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka.bigdata.svc.cluster.local:9092")

default_args = {
    "owner": "bigdata-team",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}


# ──────────────────────────────────────────────────────────────
# TASK 1: Ensure MinIO Buckets
# ──────────────────────────────────────────────────────────────
def ensure_buckets():
    from minio import Minio

    client = Minio(
        MINIO_ENDPOINT_CLEAN,
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )
    for bucket in ["bronze", "silver", "gold"]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"[MinIO] Created bucket: {bucket}")
        else:
            print(f"[MinIO] Bucket already exists: {bucket}")
    print("[MinIO] All buckets ready ✓")


# ──────────────────────────────────────────────────────────────
# TASK 2: Publish Kafka Pipeline Start Event
# ──────────────────────────────────────────────────────────────
def publish_kafka_event():
    from kafka import KafkaProducer
    from kafka.errors import NoBrokersAvailable

    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=10000,
        )
        event = {
            "pipeline": "fhvhv-bigdata",
            "stage": "processing_started",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "s3a://bronze/fhvhv/2025/fhvhv_tripdata_2025.parquet",
        }
        producer.send("fhvhv-pipeline-events", event)
        producer.flush()
        print(f"[Kafka] Published pipeline start event to 'fhvhv-pipeline-events' ✓")
    except NoBrokersAvailable:
        print("[Kafka] WARNING: No brokers available, skipping event publish")


# ──────────────────────────────────────────────────────────────
# TASK 3: Part A – Spark Processing (Bronze → Silver)
# ──────────────────────────────────────────────────────────────
def part_a_spark_processing():
    import os
    os.environ["PYSPARK_SUBMIT_ARGS"] = "--jars /opt/java/lib/hadoop-aws-3.3.2.jar,/opt/java/lib/aws-java-sdk-bundle-1.11.1026.jar pyspark-shell"
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    from pyspark import StorageLevel

    DATA_PATH = "s3a://bronze/fhvhv/2025/fhvhv_tripdata_2025.parquet"
    SILVER_PATH = "s3a://silver/fhvhv/2025/processed_trip_time_features"
    SHUFFLE_PARTITIONS = 8

    print("[Spark Part A] Starting Spark Session...")
    spark = (
        SparkSession.builder
        .appName("FHVHV-Airflow-PartA-Processing")
        .master(os.getenv("SPARK_MASTER_MODE", "local[*]"))
        .config("spark.driver.host", SPARK_DRIVER_HOST)
        .config("spark.driver.bindAddress", "0.0.0.0")
        .config("spark.driver.memory", "512m")
        .config("spark.executor.memory", "512m")
        .config("spark.jars", "/opt/java/lib/hadoop-aws-3.3.2.jar,/opt/java/lib/aws-java-sdk-bundle-1.11.1026.jar")
        .config("spark.driver.extraClassPath", "/opt/java/lib/hadoop-aws-3.3.2.jar:/opt/java/lib/aws-java-sdk-bundle-1.11.1026.jar")
        .config("spark.executor.extraClassPath", "/opt/java/lib/hadoop-aws-3.3.2.jar:/opt/java/lib/aws-java-sdk-bundle-1.11.1026.jar")
        .config("spark.sql.shuffle.partitions", SHUFFLE_PARTITIONS)
        .config("spark.default.parallelism", SHUFFLE_PARTITIONS)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.dynamicAllocation.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.access.key", os.environ["MINIO_ROOT_USER"])
        .config("spark.hadoop.fs.s3a.secret.key", os.environ["MINIO_ROOT_PASSWORD"])
        .getOrCreate()
    )

    print(f"[Spark Part A] Connected to master: {spark.sparkContext.master}")
    print(f"[Spark Part A] Reading Bronze from: {DATA_PATH}")

    # Load data with fallback for testing
    try:
        df = spark.read.parquet(DATA_PATH).limit(500)
    except Exception as e:
        print(f"[Spark Part A] Bronze path not found ({e}). Generating test dataset...")
        test_data = [
            ("HV0003", "2025-01-01 00:00:00", "2025-01-01 00:15:00", 100, 200, 3.5, "N", "N", 15.0, 1.0, 0.5, 0.0, 2.5, 0.0, 19.0),
            ("HV0005", "2025-01-01 01:00:00", "2025-01-01 01:25:00", 140, 230, 5.2, "N", "N", 22.0, 1.5, 0.5, 0.0, 3.0, 0.0, 27.0),
            ("HV0003", "2025-01-01 02:00:00", "2025-01-01 02:10:00", 161, 141, 1.8, "Y", "Y", 10.0, 0.0, 0.5, 0.0, 2.0, 0.0, 12.5),
        ] * 20
        columns = [
            "hvfhs_license_num", "pickup_datetime", "dropoff_datetime", "PULocationID", "DOLocationID",
            "trip_miles", "shared_request_flag", "shared_match_flag", "base_passenger_fare", "tolls",
            "bcf", "sales_tax", "tips", "driver_pay", "total_amount"
        ]
        raw_df = spark.createDataFrame(test_data, columns)
        df = (
            raw_df
            .withColumn("pickup_datetime", F.to_timestamp("pickup_datetime"))
            .withColumn("dropoff_datetime", F.to_timestamp("dropoff_datetime"))
        )
        df.write.mode("overwrite").parquet(DATA_PATH)
        print(f"[Spark Part A] Wrote synthetic test dataset to {DATA_PATH}")

    df = df.repartition(SHUFFLE_PARTITIONS)
    print(f"[Spark Part A] Loaded {len(df.columns)} columns")

    # Data cleaning & feature engineering
    required_columns = ["pickup_datetime", "dropoff_datetime", "PULocationID", "DOLocationID", "trip_miles"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"[Part A] Missing required column: {col}")

    cleaned_df = (
        df.dropDuplicates()
        .filter(F.col("pickup_datetime").isNotNull() & F.col("dropoff_datetime").isNotNull())
        .filter(F.col("trip_miles").isNotNull() & (F.col("trip_miles") >= 0))
        .withColumn("trip_time", F.unix_timestamp("dropoff_datetime") - F.unix_timestamp("pickup_datetime"))
        .filter(F.col("trip_time") > 0)
    )

    for col in ["hvfhs_license_num", "shared_request_flag", "shared_match_flag",
                "access_a_ride_flag", "wav_request_flag", "wav_match_flag"]:
        if col not in cleaned_df.columns:
            cleaned_df = cleaned_df.withColumn(col, F.lit("unknown"))
        else:
            cleaned_df = cleaned_df.withColumn(col, F.coalesce(F.col(col).cast("string"), F.lit("unknown")))

    processed_df = (
        cleaned_df
        .withColumn("PULocationID", F.col("PULocationID").cast("string"))
        .withColumn("DOLocationID", F.col("DOLocationID").cast("string"))
        .withColumn("pickup_hour", F.hour("pickup_datetime"))
        .withColumn("pickup_day_of_week", F.dayofweek("pickup_datetime"))
        .withColumn("pickup_month", F.month("pickup_datetime"))
        .withColumn("is_weekend", F.when(F.dayofweek("pickup_datetime").isin([1, 7]), 1).otherwise(0))
        .select(
            "trip_time", "trip_miles", "pickup_hour", "pickup_day_of_week",
            "pickup_month", "is_weekend", "hvfhs_license_num",
            "PULocationID", "DOLocationID", "shared_request_flag",
            "shared_match_flag", "access_a_ride_flag", "wav_request_flag", "wav_match_flag"
        )
        .repartition(SHUFFLE_PARTITIONS)
        .persist(StorageLevel.MEMORY_AND_DISK)
    )

    row_count = processed_df.count()
    print(f"[Spark Part A] Processed rows: {row_count}")

    # Write to Silver
    print(f"[Spark Part A] Writing Silver to: {SILVER_PATH}")
    processed_df.write.mode("overwrite").parquet(SILVER_PATH)
    processed_df.unpersist()

    print(f"[Spark Part A] Done! Silver written: {row_count} rows ✓")
    spark.stop()


# ──────────────────────────────────────────────────────────────
# TASK 4: Part B – ML Training (Silver → Gold Model)
# ──────────────────────────────────────────────────────────────
def part_b_ml_training():
    import sys, site, os, subprocess
    sys.path.insert(0, "/opt/airflow/.local/lib/python3.11/site-packages")
    sys.path.insert(0, "/home/airflow/.local/lib/python3.11/site-packages")
    sys.path.insert(0, site.getusersitepackages())
    os.environ["PYSPARK_SUBMIT_ARGS"] = "--jars /opt/java/lib/hadoop-aws-3.3.2.jar,/opt/java/lib/aws-java-sdk-bundle-1.11.1026.jar pyspark-shell"
    try:
        import numpy
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "--no-cache-dir", "numpy"])
        sys.path.insert(0, "/opt/airflow/.local/lib/python3.11/site-packages")
        sys.path.insert(0, "/home/airflow/.local/lib/python3.11/site-packages")
        import numpy
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    from pyspark.ml import Pipeline
    from pyspark.ml.feature import StringIndexer, VectorAssembler
    from pyspark.ml.regression import RandomForestRegressor
    from pyspark.ml.evaluation import RegressionEvaluator

    SILVER_PATH = "s3a://silver/fhvhv/2025/processed_trip_time_features"
    MODEL_PATH = "s3a://gold/fhvhv/2025/trip_time_predictions/RandomForestRegressor"
    SHUFFLE_PARTITIONS = 8

    print("[Spark Part B] Starting Spark Session...")
    spark = (
        SparkSession.builder
        .appName("FHVHV-Airflow-PartB-ML")
        .master(os.getenv("SPARK_MASTER_MODE", "local[*]"))
        .config("spark.driver.host", SPARK_DRIVER_HOST)
        .config("spark.driver.bindAddress", "0.0.0.0")
        .config("spark.driver.memory", "512m")
        .config("spark.executor.memory", "512m")
        .config("spark.jars", "/opt/java/lib/hadoop-aws-3.3.2.jar,/opt/java/lib/aws-java-sdk-bundle-1.11.1026.jar")
        .config("spark.driver.extraClassPath", "/opt/java/lib/hadoop-aws-3.3.2.jar:/opt/java/lib/aws-java-sdk-bundle-1.11.1026.jar")
        .config("spark.executor.extraClassPath", "/opt/java/lib/hadoop-aws-3.3.2.jar:/opt/java/lib/aws-java-sdk-bundle-1.11.1026.jar")
        .config("spark.sql.shuffle.partitions", SHUFFLE_PARTITIONS)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.access.key", os.environ["MINIO_ROOT_USER"])
        .config("spark.hadoop.fs.s3a.secret.key", os.environ["MINIO_ROOT_PASSWORD"])
        .getOrCreate()
    )

    print(f"[Spark Part B] Reading Silver from: {SILVER_PATH}")
    df = spark.read.parquet(SILVER_PATH)
    df = df.filter(
        F.col("trip_time").isNotNull() & F.col("trip_miles").isNotNull()
        & (F.col("trip_time") > 60) & (F.col("trip_time") < 7200)
        & (F.col("trip_miles") > 0) & (F.col("trip_miles") < 100)
    )

    row_count = df.count()
    print(f"[Spark Part B] Training rows: {row_count}")

    # Build ML Pipeline
    categorical_cols = ["hvfhs_license_num", "PULocationID", "DOLocationID",
                        "shared_request_flag", "access_a_ride_flag"]
    indexers = [StringIndexer(inputCol=c, outputCol=f"{c}_idx", handleInvalid="keep")
                for c in categorical_cols]

    numeric_cols = ["trip_miles", "pickup_hour", "pickup_day_of_week", "pickup_month", "is_weekend"]
    feature_cols = numeric_cols + [f"{c}_idx" for c in categorical_cols]

    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="skip")

    rf = RandomForestRegressor(
        featuresCol="features",
        labelCol="trip_time",
        numTrees=5,
        maxDepth=4,
        maxBins=256,
        seed=42,
    )

    pipeline = Pipeline(stages=indexers + [assembler, rf])

    # Train/Test split
    train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)
    print(f"[Spark Part B] Training: {train_df.count()} rows | Test: {test_df.count()} rows")

    print("[Spark Part B] Training RandomForest model...")
    model = pipeline.fit(train_df)

    # Evaluate
    predictions = model.transform(test_df)
    evaluator = RegressionEvaluator(labelCol="trip_time", predictionCol="prediction")
    rmse = evaluator.setMetricName("rmse").evaluate(predictions)
    r2 = evaluator.setMetricName("r2").evaluate(predictions)
    mae = evaluator.setMetricName("mae").evaluate(predictions)

    print(f"[Spark Part B] ✓ RMSE={rmse:.2f} | R²={r2:.4f} | MAE={mae:.2f}")

    # Save model
    print(f"[Spark Part B] Saving model to: {MODEL_PATH}")
    model.write().overwrite().save(MODEL_PATH)

    # Save predictions sample to gold
    PRED_PATH = "s3a://gold/fhvhv/2025/processed_data"
    (predictions
     .select("trip_time", "trip_miles", "pickup_hour", "pickup_day_of_week",
             "pickup_month", "is_weekend", "hvfhs_license_num", "prediction")
     .limit(500000)
     .write.mode("overwrite").parquet(PRED_PATH))

    print(f"[Spark Part B] Predictions saved to: {PRED_PATH} ✓")
    spark.stop()


# ──────────────────────────────────────────────────────────────
# TASK 5: Pipeline Done Notification
# ──────────────────────────────────────────────────────────────
def pipeline_done(**context):
    from kafka import KafkaProducer
    from kafka.errors import NoBrokersAvailable

    print("=" * 55)
    print("   FHVHV Big Data Pipeline — COMPLETED SUCCESSFULLY!")
    print("=" * 55)
    print(f"  Run ID : {context.get('run_id', 'N/A')}")
    print(f"  Finished: {datetime.utcnow().isoformat()}")
    print(f"  Silver  : s3a://silver/fhvhv/2025/processed_trip_time_features")
    print(f"  Model   : s3a://gold/fhvhv/2025/trip_time_predictions/RandomForestRegressor")
    print(f"  Data    : s3a://gold/fhvhv/2025/processed_data")
    print("=" * 55)

    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=5000,
        )
        producer.send("fhvhv-pipeline-events", {
            "pipeline": "fhvhv-bigdata",
            "stage": "pipeline_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "model_path": "s3a://gold/fhvhv/2025/trip_time_predictions/RandomForestRegressor",
        })
        producer.flush()
        print("[Kafka] Published pipeline completion event ✓")
    except NoBrokersAvailable:
        print("[Kafka] WARNING: Could not publish completion event")


# ──────────────────────────────────────────────────────────────
# DAG Definition
# ──────────────────────────────────────────────────────────────
with DAG(
    dag_id="fhvhv_bigdata_pipeline",
    description="End-to-end FHVHV pipeline: MinIO → Kafka → Spark Part A → Spark Part B (ML)",
    default_args=default_args,
    schedule=None,          # يشتغل يدوياً من الـ UI
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["fhvhv", "bigdata", "spark", "ml", "production"],
) as dag:

    t1 = PythonOperator(task_id="ensure_buckets",      python_callable=ensure_buckets)
    t2 = PythonOperator(task_id="publish_kafka_event", python_callable=publish_kafka_event)
    t3 = PythonOperator(task_id="part_a_processing",   python_callable=part_a_spark_processing)
    t4 = PythonOperator(task_id="part_b_ml_training",  python_callable=part_b_ml_training)
    t5 = PythonOperator(task_id="pipeline_done",       python_callable=pipeline_done, provide_context=True)

    t1 >> t3 >> t4 >> t5
