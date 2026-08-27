"""
Step 3 - GOLD LAYER
Build business-ready fact/dimension style tables for reporting.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pyspark.sql import functions as F
from pyspark.sql.window import Window

from spark_utils import PROJECT_ROOT, get_spark

SILVER_PARQUET = PROJECT_ROOT / "data" / "silver" / "tweets_silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"


def write_table(df, name: str) -> None:
    path = GOLD_DIR / name
    if path.exists():
        import shutil

        shutil.rmtree(path)
    df.write.mode("overwrite").parquet(str(path))
    # Also CSV for easy screenshots / Excel
    csv_path = GOLD_DIR / f"{name}.csv"
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(str(csv_path) + "_tmp")
    # Move single part file to a clean CSV name
    import shutil
    from glob import glob

    parts = glob(str(csv_path) + "_tmp/part-*.csv")
    if parts:
        shutil.copy(parts[0], csv_path)
    shutil.rmtree(str(csv_path) + "_tmp")
    print(f"  OK {name}  ({df.count():,} rows) -> {path}")


def main() -> None:
    spark = get_spark("social-media-gold")
    spark.sparkContext.setLogLevel("WARN")

    print("=" * 60)
    print("GOLD LAYER - Business Tables & Aggregations")
    print("=" * 60)

    if not SILVER_PARQUET.exists():
        raise FileNotFoundError(
            f"Silver data missing: {SILVER_PARQUET}\nRun scripts/02_silver_clean.py first."
        )

    silver = spark.read.parquet(str(SILVER_PARQUET))
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Fact: posts (cleaned grain)
    fact_posts = silver.select(
        "post_id",
        "username",
        "brand",
        "sentiment",
        "sentiment_confidence",
        "negative_reason",
        "retweet_count",
        "text_length",
        "posted_at",
        "post_date",
        "post_hour",
        "day_of_week",
        "location",
    )
    write_table(fact_posts, "fact_posts")

    # 2) Sentiment summary by brand (airline = brand on social)
    sentiment_by_brand = (
        silver.groupBy("brand", "sentiment")
        .agg(
            F.count("*").alias("post_count"),
            F.round(F.avg("sentiment_confidence"), 3).alias("avg_confidence"),
            F.sum("retweet_count").alias("total_retweets"),
        )
        .orderBy("brand", F.desc("post_count"))
    )
    write_table(sentiment_by_brand, "sentiment_by_brand")

    # 3) Brand health scoreboard (% negative / positive)
    brand_totals = silver.groupBy("brand").agg(F.count("*").alias("total_posts"))
    brand_neg = (
        silver.filter(F.col("sentiment") == "negative")
        .groupBy("brand")
        .agg(F.count("*").alias("negative_posts"))
    )
    brand_pos = (
        silver.filter(F.col("sentiment") == "positive")
        .groupBy("brand")
        .agg(F.count("*").alias("positive_posts"))
    )
    brand_scoreboard = (
        brand_totals.join(brand_neg, "brand", "left")
        .join(brand_pos, "brand", "left")
        .fillna(0, subset=["negative_posts", "positive_posts"])
        .withColumn(
            "negative_pct",
            F.round(100 * F.col("negative_posts") / F.col("total_posts"), 2),
        )
        .withColumn(
            "positive_pct",
            F.round(100 * F.col("positive_posts") / F.col("total_posts"), 2),
        )
        .orderBy(F.desc("negative_pct"))
    )
    write_table(brand_scoreboard, "brand_scoreboard")

    # 4) Top negative reasons (customer pain points)
    negative_reasons = (
        silver.filter(
            (F.col("sentiment") == "negative")
            & F.col("negative_reason").isNotNull()
            & (F.trim(F.col("negative_reason")) != "")
        )
        .groupBy("negative_reason")
        .agg(
            F.count("*").alias("complaint_count"),
            F.round(F.avg("negative_reason_confidence"), 3).alias("avg_reason_confidence"),
        )
        .orderBy(F.desc("complaint_count"))
    )
    write_table(negative_reasons, "top_negative_reasons")

    # 5) Engagement leaders (most retweeted posts)
    w = Window.orderBy(F.desc("retweet_count"))
    top_engagement = (
        silver.select(
            "post_id",
            "brand",
            "username",
            "sentiment",
            "retweet_count",
            "post_text",
            "posted_at",
        )
        .withColumn("rank", F.row_number().over(w))
        .filter(F.col("rank") <= 20)
        .drop("rank")
    )
    write_table(top_engagement, "top_engagement_posts")

    # 6) Demand / activity pattern by day & hour
    activity_by_day = (
        silver.groupBy("day_of_week")
        .agg(
            F.count("*").alias("post_count"),
            F.sum(F.when(F.col("sentiment") == "negative", 1).otherwise(0)).alias("negative_count"),
            F.sum(F.when(F.col("sentiment") == "positive", 1).otherwise(0)).alias("positive_count"),
        )
        .orderBy(F.desc("post_count"))
    )
    write_table(activity_by_day, "activity_by_day")

    activity_by_hour = (
        silver.groupBy("post_hour")
        .agg(F.count("*").alias("post_count"))
        .orderBy("post_hour")
    )
    write_table(activity_by_hour, "activity_by_hour")

    # 7) Daily sentiment trend
    daily_trend = (
        silver.groupBy("post_date", "sentiment")
        .agg(F.count("*").alias("post_count"))
        .orderBy("post_date", "sentiment")
    )
    write_table(daily_trend, "daily_sentiment_trend")

    print("\nGold layer complete. Tables ready for insights & demo.\n")
    spark.stop()


if __name__ == "__main__":
    main()
