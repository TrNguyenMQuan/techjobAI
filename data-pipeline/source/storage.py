import os 

class StorageConfig: # This pattern allow change backend where store data by env var
    backend: str = os.getenv("STORAGE_BACKEND", "minio")
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "admin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "admin123")

    # Azure config
    adls_account: str = os.getenv("ADLS_ACCOUNT", "")
    adls_sas_token: str = os.getenv("ADLS_SAS_TOKEN", "")

def bronze_path(dt: str):
    if StorageConfig.backend == "adls": # Azure
        return f"abfss://bronze@{StorageConfig.adls_account}.dfs.core.windows.net/jobs/dt={dt}/"
    return f"s3a://bronze/jobs/dt={dt}/" #MinIO with S3A

def silver_path(dt: str):
    if StorageConfig.backend == "adls":
        return f"abfss://silver@{StorageConfig.adls_account}.dfs.core.windows.net/jobs/dt={dt}/"
    return f"s3a://silver/jobs/dt={dt}/"

def s3a_spark_configs() -> dict:
    if StorageConfig.backend != "minio":
        return {}
    return {
        "spark.hadoop.fs.s3a.endpoint": StorageConfig.minio_endpoint,
        "spark.hadoop.fs.s3a.access.key": StorageConfig.minio_access_key,
        "spark.hadoop.fs.s3a.secret.key": StorageConfig.minio_secret_key,
        "spark.hadoop.fs.s3a.path.style.access": "true",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
    }