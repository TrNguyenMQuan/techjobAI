from pyspark.sql import SparkSession

def get_spark_session(app_name: str, extra_conf: dict | None = None):
    builder = (
        SparkSession.builder
        .appName(app_name)
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