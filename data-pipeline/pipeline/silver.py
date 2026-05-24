from pathlib import Path
from pyspark.sql.functions import col, explode, to_timestamp, when
from pyspark.sql.types import(
    ArrayType,
    BooleanType,
    IntegerType,
    StringType,
    StructField,
    StructType
)
from source.spark_session import get_spark_session

def page_schema():
    job_schema = StructType([
        StructField("jobId",        IntegerType(), True),
        StructField("jobTitle",     StringType(), True),
        StructField("companyName",  StringType(), True),
        StructField("companyId",    IntegerType(), True),
        StructField("salaryMin",    IntegerType(), True),
        StructField("salaryMax",    IntegerType(), True),
        StructField("isSalaryVisible", BooleanType(), True),
        StructField("jobLevelId",   IntegerType(), True),
        StructField("typeWorkingId",    IntegerType(), True),
        StructField("createdOn",    StringType(), True),
        StructField("expiredOn", StringType(), True),
        StructField("approvedOn", StringType(), True),
        StructField("skills", ArrayType(StructType([
            StructField("skillId",     IntegerType(), True),
            StructField("skillName",   StringType(),  True),
            StructField("skillWeight", IntegerType(), True),
        ])), True),
        StructField("workingLocations", ArrayType(StructType([
            StructField("cityId",     IntegerType(), True),
            StructField("cityName",   StringType(),  True),
            StructField("cityNameVI", StringType(),  True),
            StructField("address",    StringType(),  True),
        ])), True),
        StructField("benefits", ArrayType(StructType([
            StructField("benefitId",      IntegerType(), True),
            StructField("benefitName",    StringType(),  True),
            StructField("benefitNameVI",  StringType(),  True),
            StructField("benefitValue",   StringType(),  True),
        ])), True),
        # jobFunctionsV3 là struct đơn (không phải array).
        StructField("jobFunctionsV3", StructType([
            StructField("jobFunctionV3Id",     IntegerType(), True),
            StructField("jobFunctionV3Name",   StringType(),  True),
            StructField("jobFunctionV3NameVI", StringType(),  True),
        ]), True),
    ])

    return StructType([
        StructField("meta", StructType([
            StructField("nbHits",  IntegerType(), True),
            StructField("page",    IntegerType(), True),
            StructField("nbPages", IntegerType(), True),
        ]), True),
        StructField("data", ArrayType(job_schema), True),
    ]) #meta + [{job1, job2, ...}]

def run(date_str: str, raw_dir: Path, staging_dir: Path):
    spark = get_spark_session("silver")
    input_path = str(raw_dir / f"dt={date_str}")

    #Each file is one row have two column is meta + data[]
    pages_df = spark.read.schema(page_schema()).option("multiLine", "true").json(input_path)

    jobs_df = (
        pages_df
        .select(explode(col("data")).alias("job"))
        .select("job.*")
    )

    jobs_df = (
        jobs_df
        .withColumn("salaryMin",
                    when(col("salaryMin") == 0, None).otherwise(col("salaryMin")))
        .withColumn("salaryMax",
                    when(col("salaryMax") == 0, None).otherwise(col("salaryMax")))
        .withColumn("createdOn", to_timestamp(col("createdOn")))
        .withColumn("expiredOn", to_timestamp(col("expiredOn")))
        .withColumn("approvedOn", to_timestamp(col("approvedOn")))
    )

    print(f"Total jobs: {jobs_df.count()}")
    jobs_df.printSchema()
    out_path = str(staging_dir / f"dt={date_str}")

    # mode("overwrite"): nếu chạy lại cùng ngày thì ghi đè — idempotent.
    jobs_df.write.mode("overwrite").parquet(out_path)

    print(f"Staging Parquet written to {out_path}")
    spark.stop()

