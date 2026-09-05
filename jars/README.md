# Required local S3A dependency

The project expects the following JAR when the Jupyter/Spark image is built:

- `aws-java-sdk-bundle-1.11.1026.jar`

It is intentionally not stored in this Git repository because its size is about
226 MB, which exceeds GitHub's normal single-file limit. Download the exact
version from Maven Central and save it in this folder before building the image:

```text
https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.1026/aws-java-sdk-bundle-1.11.1026.jar
```

Expected local path:

```text
jars/aws-java-sdk-bundle-1.11.1026.jar
```

`hadoop-aws-3.3.2.jar` remains in the repository. The two files must be used
together so Spark can access MinIO through the `s3a://` protocol.
