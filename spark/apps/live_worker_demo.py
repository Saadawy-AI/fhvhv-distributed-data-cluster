"""
Lab Demo: Live Worker Execution Test
------------------------------------
Runs a 40-second Spark job with multiple stages so you can watch
the tasks executing live on the Spark Master UI and Worker logs.
"""
import time
from pyspark.sql import SparkSession

def main():
    spark = SparkSession.builder \
        .appName("LiveWorkerDemo") \
        .getOrCreate()

    print("\n=======================================================")
    print(">>> STARTING LIVE WORKER DEMO JOB (App Name: LiveWorkerDemo)")
    print("=======================================================\n")
    sc = spark.sparkContext

    for step in range(1, 6):
        print(f">>> Executing Step {step}/5 on remote Worker (sleeping ~5s)...")
        rdd = sc.parallelize(range(1, 101), numSlices=4)

        def work_fn(x):
            time.sleep(0.5)
            return x * 2

        result_sum = rdd.map(work_fn).sum()
        print(f">>> Step {step}/5 Finished! Sum result: {result_sum}")
        time.sleep(2)

    print("\n=======================================================")
    print(">>> DEMO JOB FINISHED SUCCESSFULLY ON WORKER!")
    print("=======================================================\n")
    spark.stop()

if __name__ == "__main__":
    main()
