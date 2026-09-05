$ErrorActionPreference = 'Stop'

function Assert-Contains([string]$Path, [string]$Needle) {
    $text = Get-Content -LiteralPath $Path -Raw
    if (-not $text.Contains($Needle)) { throw "$Path must contain: $Needle" }
}

Assert-Contains 'jupyter/Dockerfile' 'pyspark==${PYSPARK_VERSION}'
Assert-Contains 'jupyter/Dockerfile' 'hadoop-aws-3.3.2.jar'
Assert-Contains 'jupyter/Dockerfile' 'aws-java-sdk-bundle-1.11.1026.jar'
Assert-Contains 'jupyter/Dockerfile' '/opt/conda-repaired'
Assert-Contains 'jupyter/spark-defaults.conf' 'spark.hadoop.fs.s3a.impl'
Assert-Contains 'jupyter/spark-defaults.conf' 'spark.hadoop.fs.s3a.endpoint'
Assert-Contains 'jupyter/spark-defaults.conf' 'spark.jars'
Assert-Contains 'jupyter/spark-defaults.conf' 'spark.files.io.connectionTimeout 600s'
Assert-Contains 'k8s/31-jupyter.yaml' 'bigdata-lab-jupyter:s3a-v4'
Assert-Contains 'k8s/31-jupyter.yaml' '/opt/conda-repaired/bin/python'
Assert-Contains 'k8s/31-jupyter.yaml' 'AWS_ACCESS_KEY_ID'
Assert-Contains 'k8s/31-jupyter.yaml' 'AWS_SECRET_ACCESS_KEY'
Assert-Contains 'k8s/31-jupyter.yaml' 'jupyter-spark-defaults'
Assert-Contains 'k8s/31-jupyter.yaml' 'status.podIP'
Assert-Contains 'k8s/31-jupyter.yaml' 'SPARK_LOCAL_IP'
Assert-Contains 'k8s/21-spark-workers.yaml' 'bootstrap-s3a-jars'
Assert-Contains 'k8s/21-spark-workers.yaml' 'aws-java-sdk-bundle-1.11.1026.jar'
Assert-Contains 'k8s/21-spark-workers.yaml' 'AWS_ACCESS_KEY_ID'
Assert-Contains 'k8s/21-spark-workers.yaml' 'AWS_SECRET_ACCESS_KEY'
Write-Output 'Jupyter S3A static configuration audit passed.'
