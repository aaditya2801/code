"""
Generate the capstone project report PDF (<10 pages).
Run: python scripts/generate_report_pdf.py
Output: docs/Project_Report.pdf
"""

from __future__ import annotations

import csv
import textwrap
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"
CHARTS_DIR = DOCS_DIR / "charts"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
OUTPUT_PDF = DOCS_DIR / "Project_Report.pdf"

GITHUB_LINK = "https://github.com/<your-username>/big-data-social-media-capstone"
DEMO_VIDEO_LINK = "https://youtu.be/<your-demo-video-id>"
STUDENT_NAME = "Student Name"
INSTITUTION = "Big Data Analytics Capstone"

NAVY = "#1a365d"
BLUE = "#2c5282"
GRAY = "#4a5568"


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def wrap(text: str, width: int = 95) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def add_title_page(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    ax.text(0.5, 0.72, "Big Data Analytics Capstone Project", ha="center", va="center", fontsize=13, color=GRAY)
    ax.text(
        0.5,
        0.62,
        "Social Media Brand Sentiment\n& Engagement Analytics",
        ha="center",
        va="center",
        fontsize=20,
        color=NAVY,
        fontweight="bold",
        linespacing=1.4,
    )
    ax.text(
        0.5,
        0.50,
        "Path B: PySpark Lakehouse (Bronze -> Silver -> Gold)\nLocal Machine Implementation",
        ha="center",
        va="center",
        fontsize=11,
        color=GRAY,
        linespacing=1.5,
    )
    ax.text(0.5, 0.34, f"Submitted by: {STUDENT_NAME}", ha="center", va="center", fontsize=11, color=GRAY)
    ax.text(0.5, 0.30, INSTITUTION, ha="center", va="center", fontsize=11, color=GRAY)
    ax.text(0.5, 0.26, f"Date: {date.today().strftime('%B %d, %Y')}", ha="center", va="center", fontsize=11, color=GRAY)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_text_page(pdf: PdfPages, title: str, paragraphs: list[str], code_block: str | None = None) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.08, 0.08, 0.84, 0.84])
    ax.axis("off")

    y = 0.98
    ax.text(0.0, y, title, fontsize=14, color=NAVY, fontweight="bold", transform=ax.transAxes)
    y -= 0.05

    for para in paragraphs:
        wrapped = wrap(para, 95)
        lines = wrapped.split("\n")
        needed = 0.028 * len(lines) + 0.02
        ax.text(0.0, y, wrapped, fontsize=10, color="black", va="top", transform=ax.transAxes, linespacing=1.45)
        y -= needed

    if code_block:
        y -= 0.01
        ax.text(0.0, y, "Code snippet:", fontsize=10, color=BLUE, fontweight="bold", transform=ax.transAxes)
        y -= 0.03
        code_wrapped = "\n".join(textwrap.wrap(code_block, width=88, break_long_words=False, replace_whitespace=False))
        ax.text(
            0.0,
            y,
            code_wrapped,
            fontsize=8,
            color="#1a202c",
            va="top",
            transform=ax.transAxes,
            family="monospace",
            linespacing=1.35,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#f7fafc", edgecolor="#cbd5e0"),
        )

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_table_page(pdf: PdfPages, title: str, intro: str, headers: list[str], rows: list[list[str]], finding: str | None = None) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.08, 0.12, 0.84, 0.78])
    ax.axis("off")

    ax.text(0.0, 1.02, title, fontsize=14, color=NAVY, fontweight="bold", transform=ax.transAxes)
    ax.text(0.0, 0.95, wrap(intro, 100), fontsize=10, color="black", va="top", transform=ax.transAxes, linespacing=1.4)

    table = ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc="center",
        loc="center",
        bbox=[0.0, 0.18, 1.0, 0.65],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor(BLUE)
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f7fafc")
        cell.set_edgecolor("#cbd5e0")

    if finding:
        ax.text(0.0, 0.06, f"Key finding: {finding}", fontsize=10, color=NAVY, fontweight="bold", transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_chart_page(pdf: PdfPages, title: str, chart_file: str, caption: str) -> None:
    path = CHARTS_DIR / chart_file
    if not path.exists():
        add_text_page(pdf, title, [f"Chart not found: {chart_file}"])
        return

    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.08, 0.18, 0.84, 0.68])
    ax.axis("off")
    ax_img = fig.add_axes([0.10, 0.22, 0.80, 0.62])
    ax_img.imshow(plt.imread(str(path)))
    ax_img.axis("off")

    ax.text(0.0, 0.98, title, fontsize=14, color=NAVY, fontweight="bold", transform=ax.transAxes)
    ax.text(0.0, 0.08, caption, fontsize=10, color=GRAY, transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def build_report() -> None:
    scoreboard = load_csv(GOLD_DIR / "brand_scoreboard.csv")
    reasons = load_csv(GOLD_DIR / "top_negative_reasons.csv")[:5]
    by_day = load_csv(GOLD_DIR / "activity_by_day.csv")
    worst = scoreboard[0]
    best = max(scoreboard, key=lambda x: float(x["positive_pct"]))
    peak = max(by_day, key=lambda x: int(x["post_count"]))

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    with PdfPages(str(OUTPUT_PDF)) as pdf:
        add_title_page(pdf)

        add_text_page(
            pdf,
            "1. Project Context",
            [
                "Organizations increasingly rely on social media platforms to understand customer perception, service quality, and brand reputation. Public posts on platforms such as Twitter provide real-time feedback that can influence business decisions in marketing, customer support, and operations.",
                "This project analyzes a large-scale social media dataset containing airline-related tweets from February 2015. Each record includes post text, sentiment label (positive, negative, neutral), brand (airline), engagement metrics (retweets), and complaint reasons for negative posts.",
            ],
        )

        add_text_page(
            pdf,
            "2. Objective",
            [
                "Ingest and store raw social media data using a Bronze layer without transformation.",
                "Clean and standardize data in a Silver layer by handling null values, duplicates, and schema issues.",
                "Build Gold-layer business tables for brand sentiment, complaint analysis, and activity patterns.",
                "Generate actionable insights to support reputation monitoring and customer experience improvement.",
            ],
        )

        add_text_page(
            pdf,
            "3. Architecture and Tech Stack",
            [
                "The solution follows Path B (PySpark Lakehouse) on a local machine. Data flows from raw CSV ingestion to cleaned Parquet files and finally to analytics-ready Gold tables.",
                "Bronze stores raw data as-is. Silver applies cleaning and schema correction. Gold creates fact and aggregate tables for reporting. Charts are generated from Gold outputs for the demo and report.",
                "Technologies used: Python, PySpark (local[*] mode), Jupyter Notebook, Matplotlib/Seaborn, and local folder-based storage (data/bronze, data/silver, data/gold).",
            ],
        )

        add_table_page(
            pdf,
            "4. Dataset Description",
            "Source: Twitter US Airline Sentiment dataset (CrowdFlower / Kaggle mirror). The dataset contains labeled tweets about major U.S. airlines collected in February 2015.",
            ["Metric", "Value"],
            [
                ["Total rows (raw)", "14,640"],
                ["Columns", "15"],
                ["Rows after cleaning (Silver)", "14,485"],
                ["Rows removed during cleaning", "155"],
                ["Brands analyzed", "6"],
                ["Sentiment classes", "positive, negative, neutral"],
            ],
        )

        add_text_page(
            pdf,
            "5.1 Bronze Layer - Raw Ingestion",
            [
                "The raw CSV is loaded into PySpark and written to Parquet without any transformation. This preserves the original source for auditability and reprocessing.",
            ],
            code_block='df = spark.read.option("header", True).csv("data/bronze/social_media_tweets_raw.csv")\nprint("Row count:", df.count())  # 14,640\ndf.write.mode("overwrite").parquet("data/bronze/tweets_bronze")',
        )

        add_text_page(
            pdf,
            "5.2 Silver Layer - Data Cleaning",
            [
                "Key cleaning steps include renaming columns for analytics, casting numeric fields, parsing timestamps, filtering invalid sentiment values, removing duplicates by post_id, and filling selected null values.",
            ],
            code_block='silver = bronze.select(\n    F.col("tweet_id").alias("post_id"),\n    F.lower(F.trim(F.col("airline_sentiment"))).alias("sentiment"),\n    F.col("airline").alias("brand"),\n)\nsilver = silver.filter(F.col("sentiment").isin("positive","negative","neutral"))\nsilver = silver.dropDuplicates(["post_id"])',
        )

        add_text_page(
            pdf,
            "5.3 Gold Layer - Business Tables",
            [
                "Gold tables include brand scoreboard (% negative/positive), top complaint reasons, activity by day and hour, daily sentiment trend, and top engagement posts.",
            ],
            code_block='brand_scoreboard = brand_totals.join(brand_neg, "brand", "left")\n    .withColumn("negative_pct", F.round(100 * F.col("negative_posts") / F.col("total_posts"), 2))\n    .orderBy(F.desc("negative_pct"))',
        )

        add_table_page(
            pdf,
            "6.1 Brand Sentiment Health",
            "Table 1 compares social sentiment across brands. Higher negative percentage indicates greater reputation risk on social media.",
            ["Brand", "Total Posts", "Negative %", "Positive %"],
            [[r["brand"], r["total_posts"], r["negative_pct"] + "%", r["positive_pct"] + "%"] for r in scoreboard],
            finding=f"{worst['brand']} shows the highest negative share ({worst['negative_pct']}%), while {best['brand']} has the strongest positive share ({best['positive_pct']}%).",
        )

        add_chart_page(
            pdf,
            "6.2 Brand Sentiment Visualization",
            "01_brand_negative_pct.png",
            "Figure 1: Brand health - percentage of negative social posts",
        )

        add_table_page(
            pdf,
            "6.3 Top Customer Pain Points",
            "Negative posts were grouped by complaint reason to identify the most common customer pain points.",
            ["Complaint Reason", "Count"],
            [[r["negative_reason"], r["complaint_count"]] for r in reasons],
            finding=f"'{reasons[0]['negative_reason']}' is the leading complaint category with {reasons[0]['complaint_count']} negative posts.",
        )

        add_chart_page(
            pdf,
            "6.4 Complaint Reasons Visualization",
            "02_top_negative_reasons.png",
            "Figure 2: Top negative complaint reasons from social media",
        )

        add_table_page(
            pdf,
            "6.5 Social Activity Patterns",
            "Understanding when customers post helps plan social response staffing and campaign timing.",
            ["Day", "Total Posts", "Negative Posts"],
            [[r["day_of_week"], r["post_count"], r["negative_count"]] for r in by_day],
            finding=f"{peak['day_of_week']} has the highest conversation volume ({peak['post_count']} posts).",
        )

        add_chart_page(
            pdf,
            "6.6 Activity by Weekday",
            "03_activity_by_day.png",
            "Figure 3: Social conversation volume by weekday",
        )

        add_text_page(
            pdf,
            "7. Conclusion and Business Takeaways",
            [
                f"Social sentiment varies significantly across brands. {worst['brand']} and American show the highest negative share and require priority reputation monitoring.",
                f"Customer Service Issue and Late Flight are the dominant complaint drivers with {reasons[0]['complaint_count']} and {reasons[1]['complaint_count']} complaints respectively.",
                f"Conversation volume peaks on {peak['day_of_week']}, suggesting higher staffing for social response at the start of the week.",
                "The Bronze-Silver-Gold lakehouse approach enables reproducible analytics from raw social data to business-ready KPIs.",
                "This project demonstrates end-to-end big data analytics using PySpark on a local machine, meeting capstone requirements for data cleaning, distributed processing workflow, and actionable insights generation.",
            ],
        )

        add_text_page(
            pdf,
            "8. Submission Links",
            [
                f"Demo Video (public link): {DEMO_VIDEO_LINK}",
                f"GitHub Repository (public link): {GITHUB_LINK}",
                "Note: Replace placeholder links above with actual public links before final submission.",
            ],
        )

        d = pdf.infodict()
        d["Title"] = "Social Media Brand Sentiment Analytics - Capstone Report"
        d["Author"] = STUDENT_NAME
        d["Subject"] = "Big Data Analytics Capstone Project"
        d["CreationDate"] = date.today().isoformat()

    print(f"Report generated: {OUTPUT_PDF}")


if __name__ == "__main__":
    build_report()
