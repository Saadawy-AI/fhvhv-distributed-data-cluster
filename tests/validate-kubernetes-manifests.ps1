$ErrorActionPreference = 'Stop'

function Assert-Contains {
    param([string]$Path, [string]$Pattern)
    if (-not (Test-Path $Path)) { throw "Missing required file: $Path" }
    if (-not (Select-String -Path $Path -Pattern $Pattern -Quiet)) {
        throw "Expected '$Pattern' in $Path"
    }
}

Assert-Contains 'k8s/00-namespace.yaml' '^kind: Namespace$'
Assert-Contains 'k8s/00-namespace.yaml' '^  name: bigdata$'
Assert-Contains 'k8s/01-config.yaml' 'KAFKA_BOOTSTRAP_SERVERS'
Assert-Contains 'k8s/01-config.yaml' 'SPARK_MASTER_URL'
Assert-Contains 'k8s/01-config.yaml' 'MINIO_ENDPOINT'
Assert-Contains 'k8s/01-config.yaml' 'BRONZE_BUCKET'
Assert-Contains 'k8s/01-config.yaml' 'SILVER_BUCKET'
Assert-Contains 'k8s/01-config.yaml' 'GOLD_BUCKET'
Assert-Contains 'k8s/11-kafka.yaml' '^kind: StatefulSet$'
Assert-Contains 'k8s/11-kafka.yaml' 'name: KAFKA_PROCESS_ROLES'
Assert-Contains 'k8s/11-kafka.yaml' 'value: "broker,controller"'
Assert-Contains 'k8s/11-kafka.yaml' 'key: node-role'
Assert-Contains 'k8s/11-kafka.yaml' 'values: \[master\]'
Assert-Contains 'k8s/12-minio.yaml' '^kind: StatefulSet$'
Assert-Contains 'k8s/13-postgres.yaml' '^kind: StatefulSet$'
Assert-Contains 'k8s/20-spark-master.yaml' '^kind: Deployment$'
Assert-Contains 'k8s/20-spark-master.yaml' 'bde2020/spark-master:3.3.0-hadoop3.3'
Assert-Contains 'k8s/21-spark-workers.yaml' '^kind: DaemonSet$'
Assert-Contains 'k8s/21-spark-workers.yaml' 'key: node-role'
Assert-Contains 'k8s/21-spark-workers.yaml' 'values: \[worker\]'
Assert-Contains 'k8s/21-spark-workers.yaml' 'spark://spark-master.bigdata.svc.cluster.local:7077'
Assert-Contains 'k8s/21-spark-workers.yaml' 'bde2020/spark-worker:3.3.0-hadoop3.3'
Assert-Contains 'spark/apps/parallel_worker_probe.py' 'Expected tasks on 3 workers'
Assert-Contains 'k8s/30-airflow.yaml' '^kind: Deployment$'
Assert-Contains 'k8s/30-airflow.yaml' 'kafka.bigdata.svc.cluster.local:9092'
Assert-Contains 'k8s/31-jupyter.yaml' '^kind: Deployment$'
Assert-Contains 'k8s/31-jupyter.yaml' 'bigdata-lab-jupyter:s3a-v4'
Assert-Contains 'k8s/31-jupyter.yaml' 'imagePullPolicy: IfNotPresent'
Assert-Contains 'k8s/31-jupyter.yaml' 'readinessProbe:'
if (Select-String -Path 'k8s/31-jupyter.yaml' -Pattern 'pip install' -Quiet) {
    throw 'Jupyter must not install Python packages at pod startup.'
}
Assert-Contains 'k8s/40-kafka-ui.yaml' '^kind: Deployment$'
Assert-Contains 'k8s/kustomization.yaml' '40-kafka-ui.yaml'

$forbidden = rg -n -i 'datanode|namenode|HDFS_NAMENODE|hdfs://' k8s
if ($LASTEXITCODE -eq 0) { throw "Forbidden HDFS resource found:`n$forbidden" }

$nodePorts = Select-String -Path 'k8s/*.yaml' -Pattern 'nodePort:\s*(\d+)' -AllMatches
foreach ($matchInfo in $nodePorts) {
    foreach ($match in $matchInfo.Matches) {
        $port = [int]$match.Groups[1].Value
        if ($port -lt 30000 -or $port -gt 32767) { throw "Invalid Kubernetes NodePort $port in $($matchInfo.Path)" }
    }
}

Write-Host 'Kubernetes manifest validation passed.'
