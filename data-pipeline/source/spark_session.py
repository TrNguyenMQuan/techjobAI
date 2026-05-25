from pyspark.sql import SparkSession

def get_spark_session(app_name: str, extra_conf: dict | None = None):
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
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000")
        .config("spark.hadoop.fs.s3a.access.key", "admin")
        .config("spark.hadoop.fs.s3a.secret.key", "admin123")
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