"""
Step 4 - INSIGHTS & CHARTS
Read Gold tables, print key findings, save charts for report/demo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pyspark.sql import SparkSession

from spark_utils import PROJECT_ROOT, get_spark

GOLD_DIR = PROJECT_ROOT / "data" / "gold"
CHARTS_DIR = PROJECT_ROOT / "docs" / "charts"


def load_gold(spark: SparkSession, name: str):
    return spark.read.parquet(str(GOLD_DIR / name))


def main() -> None:
    spark = get_spark("social-media-insights")
    spark.sparkContext.setLogLevel("WARN")
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    print("=" * 60)
    print("INSIGHTS - Social Media Brand Sentiment Analytics")
    print("=" * 60)

    scoreboard = load_gold(spark, "brand_scoreboard").toPandas()
    reasons = load_gold(spark, "top_negative_reasons").toPandas()
    by_day = load_gold(spark, "activity_by_day").toPandas()
    by_hour = load_gold(spark, "activity_by_hour").toPandas()
    sentiment_brand = load_gold(spark, "sentiment_by_brand").toPandas()

    # --- Insight 1: Brand health ---
    print("\n[Insight 1] Brand sentiment health (higher negative % = worse social perception)")
    print(scoreboard.sort_values("negative_pct", ascending=False).to_string(index=False))

    worst = scoreboard.sort_values("negative_pct", ascending=False).iloc[0]
    best = scoreboard.sort_values("positive_pct", ascending=False).iloc[0]
    print(
        f"\n-> Worst social sentiment: {worst['brand']} "
        f"({worst['negative_pct']}% negative of {int(worst['total_posts'])} posts)"
    )
    print(
        f"-> Best positive share: {best['brand']} "
        f"({best['positive_pct']}% positive of {int(best['total_posts'])} posts)"
    )

    # --- Insight 2: Pain points ---
    print("\n[Insight 2] Top customer complaint reasons on social media")
    print(reasons.head(10).to_string(index=False))
    top_reason = reasons.iloc[0]
    print(
        f"\n-> #1 pain point: '{top_reason['negative_reason']}' "
        f"({int(top_reason['complaint_count'])} complaints)"
    )

    # --- Insight 3: Activity patterns ---
    print("\n[Insight 3] Posting / conversation volume by weekday")
    print(by_day.to_string(index=False))
    peak_day = by_day.sort_values("post_count", ascending=False).iloc[0]
    print(f"\n-> Peak conversation day: {peak_day['day_of_week']} ({int(peak_day['post_count'])} posts)")

    peak_hour = by_hour.sort_values("post_count", ascending=False).iloc[0]
    print(f"-> Peak hour (0-23): {int(peak_hour['post_hour'])}:00 ({int(peak_hour['post_count'])} posts)")

    # --- Charts ---
    fig, ax = plt.subplots(figsize=(9, 5))
    plot_df = scoreboard.sort_values("negative_pct", ascending=True)
    ax.barh(plot_df["brand"], plot_df["negative_pct"], color="#c0392b")
    ax.set_xlabel("Negative posts (%)")
    ax.set_title("Social Media Brand Health - % Negative Sentiment")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "01_brand_negative_pct.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    top10 = reasons.head(10)
    ax.barh(top10["negative_reason"][::-1], top10["complaint_count"][::-1], color="#2980b9")
    ax.set_xlabel("Complaint count")
    ax.set_title("Top Negative Reasons (Social Complaints)")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "02_top_negative_reasons.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day["day_of_week"] = pd.Categorical(by_day["day_of_week"], categories=order, ordered=True)
    by_day = by_day.sort_values("day_of_week")
    ax.bar(by_day["day_of_week"].astype(str), by_day["post_count"], color="#27ae60")
    ax.set_ylabel("Posts")
    ax.set_title("Social Conversation Volume by Weekday")
    plt.xticks(rotation=30)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "03_activity_by_day.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    pivot = sentiment_brand.pivot_table(
        index="brand", columns="sentiment", values="post_count", fill_value=0
    )
    pivot.plot(kind="bar", stacked=True, ax=ax, color=["#c0392b", "#7f8c8d", "#27ae60"])
    ax.set_ylabel("Posts")
    ax.set_title("Sentiment Mix by Brand")
    ax.legend(title="Sentiment")
    plt.xticks(rotation=30)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "04_sentiment_by_brand.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(by_hour["post_hour"], by_hour["post_count"], marker="o", color="#8e44ad")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Posts")
    ax.set_title("Social Activity by Hour of Day")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "05_activity_by_hour.png", dpi=150)
    plt.close(fig)

    print(f"\nCharts saved to: {CHARTS_DIR}")
    print("\nBusiness takeaways:")
    print("1. Monitor brands with highest negative % for reputation risk.")
    print("2. Prioritize ops fixes for the top complaint reason.")
    print("3. Staff social response teams around peak day/hour windows.")
    print("Insights step complete.\n")
    spark.stop()


if __name__ == "__main__":
    main()
