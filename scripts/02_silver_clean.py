"""
Step 2 - SILVER LAYER
Clean Bronze data: nulls, duplicates, schema/types, invalid rows.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pyspark.sql import functions as F

from spark_utils import PROJECT_ROOT, get_spark

BRONZE_PARQUET = PROJECT_ROOT / "data" / "bronze" / "tweets_bronze"
SILVER_PARQUET = PROJECT_ROOT / "data" / "silver" / "tweets_silver"


def main() -> None:
    spark = get_spark("social-media-silver")
    spark.sparkContext.setLogLevel("WARN")

    print("=" * 60)
    print("SILVER LAYER - Cleaning & Schema Correction")
    print("=" * 60)

    if not BRONZE_PARQUET.exists():
        raise FileNotFoundError(
            f"Bronze data missing: {BRONZE_PARQUET}\nRun scripts/01_bronze_ingest.py first."
        )

    bronze = spark.read.parquet(str(BRONZE_PARQUET))
    before = bronze.count()
    print(f"Bronze rows (before clean): {before:,}")

    # Select relevant social-media columns and standardize names
    silver = bronze.select(
        F.col("tweet_id").alias("post_id"),
        F.col("airline_sentiment").alias("sentiment"),
        F.col("airline_sentiment_confidence").cast("double").alias("sentiment_confidence"),
        F.col("negativereason").alias("negative_reason"),
        F.col("negativereason_confidence").cast("double").alias("negative_reason_confidence"),
        F.col("airline").alias("brand"),
        F.col("name").alias("username"),
        F.col("retweet_count").cast("int").alias("retweet_count"),
        F.col("text").alias("post_text"),
        F.col("tweet_created").alias("posted_at_raw"),
        F.col("tweet_location").alias("location"),
        F.col("user_timezone").alias("user_timezone"),
    )

    # Parse timestamp (format like: 2015-02-24 11:35:52 -0800)
    silver = silver.withColumn(
        "posted_at",
        F.to_timestamp(F.col("posted_at_raw"), "yyyy-MM-dd HH:mm:ss Z"),
    )

    # Normalize sentiment labels
    silver = silver.withColumn("sentiment", F.lower(F.trim(F.col("sentiment"))))

    # Derived fields useful for Gold analytics
    silver = (
        silver.withColumn("post_date", F.to_date("posted_at"))
        .withColumn("post_hour", F.hour("posted_at"))
        .withColumn("day_of_week", F.date_format("posted_at", "EEEE"))
        .withColumn("text_length", F.length("post_text"))
        .withColumn(
            "has_negative_reason",
            F.when(
                (F.col("negative_reason").isNotNull())
                & (F.trim(F.col("negative_reason")) != ""),
                F.lit(True),
            ).otherwise(F.lit(False)),
        )
    )

    # Cleaning rules
    silver = silver.filter(F.col("post_id").isNotNull())
    silver = silver.filter(F.col("post_text").isNotNull() & (F.trim(F.col("post_text")) != ""))
    silver = silver.filter(F.col("sentiment").isin("positive", "negative", "neutral"))
    silver = silver.filter(
        (F.col("sentiment_confidence").isNull())
        | ((F.col("sentiment_confidence") >= 0) & (F.col("sentiment_confidence") <= 1))
    )
    silver = silver.filter(
        (F.col("retweet_count").isNull()) | (F.col("retweet_count") >= 0)
    )

    # Deduplicate by post_id (keep highest confidence if duplicates)
    silver = (
        silver.orderBy(F.col("sentiment_confidence").desc_nulls_last())
        .dropDuplicates(["post_id"])
    )

    # Fill mild nulls for analytics friendliness
    silver = silver.fillna(
        {
            "retweet_count": 0,
            "location": "Unknown",
            "user_timezone": "Unknown",
            "brand": "Unknown",
            "username": "unknown_user",
        }
    )

    after = silver.count()
    print(f"Silver rows (after clean)  : {after:,}")
    print(f"Rows removed               : {before - after:,}")

    print("\nNull check (key columns):")
    silver.select(
        [F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in ["post_id", "sentiment", "post_text", "posted_at"]]
    ).show()

    print("\nSentiment distribution:")
    silver.groupBy("sentiment").count().orderBy(F.desc("count")).show()

    print("\nSchema:")
    silver.printSchema()

    if SILVER_PARQUET.exists():
        import shutil

        shutil.rmtree(SILVER_PARQUET)

    SILVER_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    silver.write.mode("overwrite").parquet(str(SILVER_PARQUET))
    print(f"\nSilver Parquet written -> {SILVER_PARQUET}")
    print("Silver layer complete.\n")
    spark.stop()


if __name__ == "__main__":
    main()
