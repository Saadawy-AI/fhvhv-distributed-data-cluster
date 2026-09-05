import time
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def main():
    print("=" * 60)
    print("Starting Instant Distributed NYC TLC Taxi Benchmark")
    print("=" * 60)
    
    start_time = time.time()
    
    # Initialize Spark Session
    spark = SparkSession.builder \
        .appName("NYC-TLC-Taxi-Distributed-Analysis") \
        .config("spark.executor.memory", "2g") \
        .config("spark.executor.cores", "4") \
        .getOrCreate()
        
    print(f"Spark Version: {spark.version}")
    print(f"Master URL: {spark.sparkContext.master}")
    
    print("\n1. Generating 3 Million NYC Taxi Trip Rows natively in Spark RAM...")
    df_raw = spark.range(0, 3000000) \
        .withColumn("passenger_count", (F.col("id") % 6) + 1) \
        .withColumn("trip_distance", F.round((F.col("id") % 20) + 0.5, 2)) \
        .withColumn("fare_amount", F.round((F.col("id") % 50) + 2.5, 2)) \
        .withColumn("tip_amount", F.round((F.col("id") % 10) + 0.5, 2)) \
        .withColumn("total_amount", F.col("fare_amount") + F.col("tip_amount"))
        
    print("2. Distributing 3 Million rows across 12 partitions and all 3 Worker Nodes (32 Cores)...")
    df_dist = df_raw.repartition(12)
    
    # 1. Total Record Count
    total_records = df_dist.count()
    print(f"\n[Result] Total Records Processed across Workers: {total_records:,}")
    
    # 2. Distributed Aggregations: Revenue, Distance, and Tip stats by Passenger Count
    print("\n[Result] Computing Distributed Aggregations by Passenger Count:")
    agg_df = df_dist.groupBy("passenger_count").agg(
        F.count("*").alias("total_trips"),
        F.round(F.avg("trip_distance"), 2).alias("avg_distance_miles"),
        F.round(F.avg("fare_amount"), 2).alias("avg_fare_usd"),
        F.round(F.avg("tip_amount"), 2).alias("avg_tip_usd"),
        F.round(F.sum("total_amount"), 2).alias("total_revenue_usd")
    ).orderBy("passenger_count")
    
    agg_df.show(20, truncate=False)
    
    # 3. SAVE RESULTS DIRECTLY TO CSV OUTPUT FILE
    output_dir = "/tmp/nyc_taxi_results_csv"
    print(f"\n3. Saving Aggregation Results directly to CSV File: {output_dir}...")
    agg_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(output_dir)
    print("CSV File saved successfully!")
    
    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"JOB COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS!")
    print("=" * 60)
    
    spark.stop()

if __name__ == "__main__":
    main()
