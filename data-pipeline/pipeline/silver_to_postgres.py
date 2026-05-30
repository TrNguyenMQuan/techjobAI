import os 
from dotenv import load_dotenv
from pyspark.sql.functions import col, to_json
from source.spark_session import get_spark_session
from source.storage import silver_path

load_dotenv()

def jdbc_url():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db   = os.getenv("POSTGRES_DB", "techjob_ai")
    return f"jdbc:postgresql://{host}:{port}/{db}?stringtype=unspecified"

def jdbc_props() -> dict:
    return {
        "user":   os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
        "driver": "org.postgresql.Driver",
    }


def run(date_str: str):
    spark = get_spark_session("silver-to-postgres")

    df = spark.read.parquet(silver_path(date_str))

    # camelCase to snake_case to match DDL 
    # convert complex types to JSON string 
    df = (
        df
        .withColumnRenamed("jobId",           "job_id")
        .withColumnRenamed("jobTitle",         "job_title")
        .withColumnRenamed("companyName",      "company_name")
        .withColumnRenamed("companyId",        "company_id")
        .withColumnRenamed("salaryMin",        "salary_min")
        .withColumnRenamed("salaryMax",        "salary_max")
        .withColumnRenamed("isSalaryVisible",  "is_salary_visible")
        .withColumnRenamed("prettySalary",    "pretty_salary")
        .withColumnRenamed("salaryCurrency",  "salary_currency")
        .withColumnRenamed("companyLogo",     "company_logo")
        .withColumnRenamed("jobUrl",          "job_url")
        .withColumnRenamed("jobLevel",        "job_level")
        .withColumnRenamed("jobLevelVI",      "job_level_vi")
        .withColumnRenamed("jobLevelId",       "job_level_id")
        .withColumnRenamed("typeWorkingId",    "type_working_id")
        .withColumnRenamed("createdOn",        "created_on")
        .withColumnRenamed("expiredOn",        "expired_on")
        .withColumnRenamed("approvedOn",       "approved_on")
        .withColumnRenamed("jobDescription", "job_description")
        .withColumnRenamed("jobRequirement",  "job_requirement")
        # to_json: ArrayType/StructType to JSON string to save in PostgreSQL JSONB
        .withColumn("skills",            to_json(col("skills")))
        .withColumn("working_locations", to_json(col("workingLocations")))
        .withColumn("benefits",          to_json(col("benefits")))
        .withColumn("job_functions_v3",  to_json(col("jobFunctionsV3")))
        .drop("workingLocations", "jobFunctionsV3")
    )

    (
        df.write
        .option("truncate", "true")  
        .jdbc(
            url=jdbc_url(),
            table="silver.jobs",
            mode="overwrite",
            properties=jdbc_props(),
        )
    )

    print(f"Wrote {df.count()} rows to silver.jobs")
    spark.stop()


if __name__ == "__main__":
    from datetime import date
    run(date.today().isoformat())
