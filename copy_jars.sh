#!/bin/bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
JP=$(k3s kubectl get pod -n bigdata -l app=jupyter -o jsonpath='{.items[0].metadata.name}')
echo "Jupyter Pod: $JP"

k3s kubectl cp -n bigdata "$JP:/opt/conda-repaired/lib/python3.10/site-packages/pyspark/jars/hadoop-aws-3.3.2.jar" /tmp/hadoop-aws-3.3.2.jar
k3s kubectl cp -n bigdata "$JP:/opt/conda-repaired/lib/python3.10/site-packages/pyspark/jars/aws-java-sdk-bundle-1.11.1026.jar" /tmp/aws-java-sdk-bundle-1.11.1026.jar

echo "Extracted JARs to /tmp:"
ls -lh /tmp/*.jar

# Copy JARs to all Spark Worker pods in cluster
WORKERS=$(k3s kubectl get pods -n bigdata -l app=spark-worker -o jsonpath='{.items[*].metadata.name}')
for W in $WORKERS; do
    echo "Copying S3A JARs to worker $W ..."
    k3s kubectl cp /tmp/hadoop-aws-3.3.2.jar "bigdata/$W:/spark/jars/hadoop-aws-3.3.2.jar"
    k3s kubectl cp /tmp/aws-java-sdk-bundle-1.11.1026.jar "bigdata/$W:/spark/jars/aws-java-sdk-bundle-1.11.1026.jar"
    echo "Done for worker $W"
done

echo "All Spark Workers updated with S3A JARs successfully!"
