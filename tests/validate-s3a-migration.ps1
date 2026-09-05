$ErrorActionPreference = 'Stop'
$files = @(
    'spark/apps/batch_wordcount.py',
    'spark/apps/streaming_kafka_to_hdfs.py',
    'spark/apps/spark_sql_demo.py',
    'airflow/dags/pipeline_hdfs_kafka_spark.py'
)

foreach ($file in $files) {
    $content = Get-Content -Raw $file
    if ($content -match 'hdfs://') { throw "HDFS endpoint remains in $file" }
    if ($content -notmatch 's3a://') { throw "Missing S3A endpoint in $file" }
}

$sparkApps = Get-Content -Raw 'spark/apps/streaming_kafka_to_hdfs.py'
if ($sparkApps -notmatch 'fs\.s3a\.endpoint') { throw 'Missing Spark S3A endpoint configuration' }

Write-Host 'S3A migration validation passed.'
