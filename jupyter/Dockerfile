ARG PYSPARK_VERSION=3.3.0
FROM jupyter/base-notebook:python-3.10

ARG PYSPARK_VERSION
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl openjdk-11-jre-headless procps && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pyspark==${PYSPARK_VERSION} \
    kafka-python-ng \
    minio \
    pandas \
    pyarrow \
    matplotlib \
    requests

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64 \
    SPARK_HOME=/opt/conda/lib/python3.10/site-packages/pyspark

RUN curl --fail --location --retry 3 \
      --output ${SPARK_HOME}/jars/hadoop-aws-3.3.2.jar \
      https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.2/hadoop-aws-3.3.2.jar && \
    curl --fail --location --retry 3 \
      --output ${SPARK_HOME}/jars/aws-java-sdk-bundle-1.11.1026.jar \
      https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.1026/aws-java-sdk-bundle-1.11.1026.jar && \
    mkdir -p ${SPARK_HOME}/conf

COPY jupyter/spark-defaults.conf ${SPARK_HOME}/conf/spark-defaults.conf

# K3s has a corrupt cache for the original /opt/conda base layers. Copy the
# complete environment to a new path: the new file paths force a real image
# layer rather than referring back to those stale blobs during import.
RUN cp -a /opt/conda /opt/conda-repaired

ENV PATH=/opt/conda-repaired/bin:${PATH} \
    SPARK_HOME=/opt/conda-repaired/lib/python3.10/site-packages/pyspark

USER ${NB_UID}
