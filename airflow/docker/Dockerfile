FROM --platform=linux/amd64 python:3.11-slim-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    libpq-dev \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Set Airflow version and home
ENV AIRFLOW_VERSION=2.9.3
ENV AIRFLOW_HOME=/opt/airflow
ENV PYTHONPATH=/opt/airflow/dags

# Install Airflow with its extras
RUN pip install --no-cache-dir \
    "apache-airflow[postgres]==${AIRFLOW_VERSION}" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.11.txt"

# Install project-specific Python libs
RUN pip install --no-cache-dir \
    kafka-python==2.0.2 \
    minio==7.2.9 \
    pyspark==3.3.0 \
    boto3==1.34.0 \
    numpy==1.26.4

# Create airflow user (uid=50000 matches the original)
RUN useradd -m -u 50000 -g 0 airflow && \
    mkdir -p ${AIRFLOW_HOME}/dags ${AIRFLOW_HOME}/logs ${AIRFLOW_HOME}/plugins && \
    chown -R 50000:0 ${AIRFLOW_HOME}

USER 50000
WORKDIR ${AIRFLOW_HOME}

# Copy DAG files (build context is airflow/ directory)
COPY --chown=50000:0 dags/ ${AIRFLOW_HOME}/dags/

EXPOSE 8080
