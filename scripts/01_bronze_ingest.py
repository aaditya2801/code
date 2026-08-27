"""
Step 1 - BRONZE LAYER
Ingest raw social media tweets into the Bronze lakehouse folder.
No cleaning is performed here - data is stored as-is.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spark_utils import PROJECT_ROOT, get_spark

BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
RAW_CSV = BRONZE_DIR / "social_media_tweets_raw.csv"
BRONZE_PARQUET = BRONZE_DIR / "tweets_bronze"


def main() -> None:
    spark = get_spark("social-media-bronze")
    spark.sparkContext.setLogLevel("WARN")

    print("=" * 60)
    print("BRONZE LAYER - Raw Ingestion")
    print("=" * 60)

    if not RAW_CSV.exists():
        raise FileNotFoundError(
            f"Raw CSV not found: {RAW_CSV}\n"
            "Place the Twitter US Airline Sentiment CSV in data/bronze/"
        )

    df = (
        spark.read.option("header", True)
        .option("multiLine", True)
        .option("quote", '"')
        .option("escape", '"')
        .csv(str(RAW_CSV))
    )

    print(f"\nSource file : {RAW_CSV.name}")
    print(f"Row count   : {df.count():,}")
    print(f"Column count: {len(df.columns)}")
    print("\nSchema:")
    df.printSchema()
    print("\nSample rows:")
    df.show(5, truncate=40)

    # Persist raw snapshot as Parquet (still Bronze - no transforms)
    if BRONZE_PARQUET.exists():
        import shutil

        shutil.rmtree(BRONZE_PARQUET)

    df.write.mode("overwrite").parquet(str(BRONZE_PARQUET))
    print(f"\nBronze Parquet written -> {BRONZE_PARQUET}")
    print("Bronze layer complete.\n")
    spark.stop()


if __name__ == "__main__":
    main()
