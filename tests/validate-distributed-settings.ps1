$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

foreach ($relativePath in @(
    'spark/apps/batch_wordcount.py',
    'spark/apps/streaming_kafka_to_hdfs.py',
    'spark/apps/spark_sql_demo.py'
)) {
    $contents = Get-Content -Raw (Join-Path $root $relativePath)
    if ($contents -notmatch 's3a://') {
        throw "$relativePath must use shared MinIO S3A storage for Kubernetes workers."
    }
}

$sparkWorkers = Get-Content -Raw (Join-Path $root 'k8s/21-spark-workers.yaml')
if ($sparkWorkers -notmatch 'kind: DaemonSet' -or $sparkWorkers -notmatch 'values: \[worker\]') {
    throw 'Spark workers must be a worker-only DaemonSet for three-device parallel processing.'
}

$readme = Get-Content -Raw (Join-Path $root 'README.md')
if ($readme -notmatch 'Additional Workers') {
    throw 'The operating guide must explain how to add additional Workers.'
}
