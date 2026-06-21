import os
from pyspark.sql import SparkSession

def get_spark_session(app_name: str, extra_conf: dict | None = None):
    # Read from env — inside Docker: "http://minio:9000", local dev: "http://localhost:9000"
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    minio_access_key = os.getenv("MINIO_ACCESS_KEY", "admin")
    minio_secret_key = os.getenv("MINIO_SECRET_KEY", "admin123")

    builder = (
        SparkSession.builder
        .appName(app_name)
        .config(
            "spark.jars.packages",
            # Nhiều packages ngăn cách bởi dấu phẩy.
            # hadoop-aws: S3A connector để đọc/ghi MinIO.
            # postgresql: JDBC driver để Spark ghi vào PostgreSQL.
            "org.apache.hadoop:hadoop-aws:3.3.4,org.postgresql:postgresql:42.7.3"
        )
        .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint)
        .config("spark.hadoop.fs.s3a.access.key", minio_access_key)
        .config("spark.hadoop.fs.s3a.secret.key", minio_secret_key)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config(
            "spark.hadoop.fs.s3a.impl",
            "org.apache.hadoop.fs.s3a.S3AFileSystem"
        )
        .master("local[*]")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.ui.showConsoleProgress", "false")
    )

    if extra_conf:
        for key, value in extra_conf.items():
            builder = builder.config(key, value)
    
    return builder.getOrCreate()