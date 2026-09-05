"""Upload the Spark S3A runtime JARs to the in-cluster MinIO dependency cache."""

import os

from minio import Minio


SPARK_JARS = "/opt/conda-repaired/lib/python3.10/site-packages/pyspark/jars"
OBJECTS = {
    "dependencies/spark/hadoop-aws-3.3.2.jar": f"{SPARK_JARS}/hadoop-aws-3.3.2.jar",
    "dependencies/spark/aws-java-sdk-bundle-1.11.1026.jar": f"{SPARK_JARS}/aws-java-sdk-bundle-1.11.1026.jar",
}


def main() -> None:
    client = Minio(
        "minio.bigdata.svc.cluster.local:9000",
        access_key=os.environ["AWS_ACCESS_KEY_ID"],
        secret_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        secure=False,
    )
    for object_name, file_path in OBJECTS.items():
        client.fput_object("bronze", object_name, file_path)
        print(f"uploaded s3a://bronze/{object_name}")


if __name__ == "__main__":
    main()
