"""
Generate the capstone project report as Word (.docx).
Student can edit name, GitHub link, demo video link directly in Word.

Run: python scripts/generate_report_docx.py
Output: docs/Project_Report.docx
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"
CHARTS_DIR = DOCS_DIR / "charts"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
OUTPUT_DOCX = DOCS_DIR / "Project_Report.docx"

# Edit these before generating, or edit directly in Word after opening
STUDENT_NAME = "<< Student Name >>"
GITHUB_LINK = "<< GitHub Repository URL >>"
DEMO_VIDEO_LINK = "<< Demo Video URL >>"
INSTITUTION = "Big Data Analytics Capstone"

NAVY = RGBColor(0x1A, 0x36, 0x5D)
BLUE = RGBColor(0x2C, 0x52, 0x82)


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def set_margins(doc: Document) -> None:
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = NAVY if level == 1 else BLUE


def add_body(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    for run in p.runs:
        run.font.size = Pt(11)


def add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    for run in p.runs:
        run.font.size = Pt(11)


def add_code(doc: Document, code: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.1
    run = p.add_run(code)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")


def add_table(doc: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = h
        for p in hdr[i].paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(10)
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, val in enumerate(row):
            cell = table.rows[r_idx].cells[c_idx]
            cell.text = str(val)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_chart(doc: Document, filename: str, caption: str, width_in: float = 5.8) -> None:
    path = CHARTS_DIR / filename
    if path.exists():
        doc.add_picture(str(path), width=Inches(width_in))
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_after = Pt(8)
        for run in cap.runs:
            run.font.size = Pt(9)
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x71, 0x80, 0x96)
    else:
        add_body(doc, f"[Chart not found: {filename}]")


def add_page_break(doc: Document) -> None:
    doc.add_page_break()


def build_report() -> None:
    scoreboard = load_csv(GOLD_DIR / "brand_scoreboard.csv")
    reasons = load_csv(GOLD_DIR / "top_negative_reasons.csv")[:5]
    by_day = load_csv(GOLD_DIR / "activity_by_day.csv")
    worst = scoreboard[0]
    best = max(scoreboard, key=lambda x: float(x["positive_pct"]))
    peak = max(by_day, key=lambda x: int(x["post_count"]))

    doc = Document()
    set_margins(doc)

    # --- Cover ---
    for _ in range(3):
        doc.add_paragraph()
    t = doc.add_paragraph("Big Data Analytics Capstone Project")
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in t.runs:
        run.font.size = Pt(13)
        run.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = title.add_run("Social Media Brand Sentiment\n& Engagement Analytics")
    r1.bold = True
    r1.font.size = Pt(20)
    r1.font.color.rgb = NAVY

    sub = doc.add_paragraph("Path B: PySpark Lakehouse (Bronze -> Silver -> Gold)\nLocal Machine Implementation")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in sub.runs:
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

    doc.add_paragraph()
    for label, value in [
        ("Submitted by:", STUDENT_NAME),
        ("Institution:", INSTITUTION),
        ("Date:", date.today().strftime("%B %d, %Y")),
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(f"{label} {value}")
        r.font.size = Pt(11)

    add_page_break(doc)

    # --- 1. Context ---
    add_heading(doc, "1. Project Context")
    add_body(
        doc,
        "Organizations increasingly rely on social media platforms to understand customer perception, "
        "service quality, and brand reputation. Public posts on platforms such as Twitter provide "
        "real-time feedback that can influence business decisions in marketing, customer support, "
        "and operations.",
    )
    add_body(
        doc,
        "This project analyzes a large-scale social media dataset containing airline-related tweets "
        "from February 2015. Each record includes post text, sentiment label (positive, negative, "
        "neutral), brand (airline), engagement metrics (retweets), and complaint reasons for negative posts.",
    )

    # --- 2. Objective ---
    add_heading(doc, "2. Objective")
    for obj in [
        "Ingest and store raw social media data using a Bronze layer (no transformation).",
        "Clean and standardize data in a Silver layer (nulls, duplicates, schema correction).",
        "Build Gold-layer business tables for brand sentiment, complaints, and activity patterns.",
        "Generate actionable insights to support reputation monitoring and customer experience improvement.",
    ]:
        add_bullet(doc, obj)

    # --- 3. Architecture ---
    add_heading(doc, "3. Architecture & Tech Stack")
    add_body(
        doc,
        "The solution follows Path B (PySpark Lakehouse) on a local machine. Data flows from raw CSV "
        "ingestion to cleaned Parquet files and finally to analytics-ready Gold tables.",
    )
    add_table(
        doc,
        ["Layer", "Purpose", "Output"],
        [
            ["Bronze", "Raw ingestion, preserve source as-is", "data/bronze/tweets_bronze"],
            ["Silver", "Cleaning, deduplication, type casting", "data/silver/tweets_silver"],
            ["Gold", "Business logic, aggregations, KPIs", "data/gold/*.parquet + CSV"],
        ],
    )
    add_body(doc, "Technologies: Python, PySpark (local[*]), Jupyter, Matplotlib/Seaborn, local folders.")

    # --- 4. Dataset ---
    add_heading(doc, "4. Dataset Description")
    add_body(doc, "Source: Twitter US Airline Sentiment dataset (CrowdFlower / Kaggle mirror), February 2015.")
    add_table(
        doc,
        ["Metric", "Value"],
        [
            ["Total rows (raw)", "14,640"],
            ["Columns", "15"],
            ["Rows after cleaning (Silver)", "14,485"],
            ["Rows removed", "155"],
            ["Brands analyzed", "6"],
            ["Sentiment classes", "positive, negative, neutral"],
        ],
    )

    add_page_break(doc)

    # --- 5. Methodology ---
    add_heading(doc, "5. Data Processing Methodology")
    add_heading(doc, "5.1 Bronze Layer - Raw Ingestion", level=2)
    add_body(doc, "Raw CSV is loaded into PySpark and written to Parquet without any transformation.")
    add_code(
        doc,
        'df = spark.read.option("header", True).csv("data/bronze/social_media_tweets_raw.csv")\n'
        'print("Row count:", df.count())  # 14,640\n'
        'df.write.mode("overwrite").parquet("data/bronze/tweets_bronze")',
    )

    add_heading(doc, "5.2 Silver Layer - Data Cleaning", level=2)
    add_body(doc, "Cleaning: rename columns, cast types, parse timestamps, filter invalid rows, deduplicate by post_id.")
    add_code(
        doc,
        'silver = bronze.select(\n'
        '    F.col("tweet_id").alias("post_id"),\n'
        '    F.lower(F.trim(F.col("airline_sentiment"))).alias("sentiment"),\n'
        '    F.col("airline").alias("brand"),\n'
        ')\n'
        'silver = silver.filter(F.col("sentiment").isin("positive","negative","neutral"))\n'
        'silver = silver.dropDuplicates(["post_id"])',
    )

    add_heading(doc, "5.3 Gold Layer - Business Tables", level=2)
    add_body(doc, "Gold tables: brand scoreboard, top complaint reasons, activity by day/hour, engagement posts.")
    add_code(
        doc,
        'brand_scoreboard = brand_totals.join(brand_neg, "brand", "left")\n'
        '    .withColumn("negative_pct", F.round(100 * F.col("negative_posts") / F.col("total_posts"), 2))\n'
        '    .orderBy(F.desc("negative_pct"))',
    )

    # --- 6. Results ---
    add_heading(doc, "6. Results & Insights")
    add_heading(doc, "6.1 Brand Sentiment Health", level=2)
    add_table(
        doc,
        ["Brand", "Total Posts", "Negative %", "Positive %"],
        [[r["brand"], r["total_posts"], r["negative_pct"] + "%", r["positive_pct"] + "%"] for r in scoreboard],
    )
    add_body(
        doc,
        f"Key finding: {worst['brand']} shows the highest negative share ({worst['negative_pct']}%), "
        f"while {best['brand']} has the strongest positive share ({best['positive_pct']}%).",
    )
    add_chart(doc, "01_brand_negative_pct.png", "Figure 1: Brand health - % negative social posts")

    add_heading(doc, "6.2 Top Customer Pain Points", level=2)
    add_table(
        doc,
        ["Complaint Reason", "Count"],
        [[r["negative_reason"], r["complaint_count"]] for r in reasons],
    )
    add_body(
        doc,
        f"Key finding: '{reasons[0]['negative_reason']}' is the leading complaint "
        f"({reasons[0]['complaint_count']} negative posts).",
    )
    add_chart(doc, "02_top_negative_reasons.png", "Figure 2: Top negative complaint reasons", width_in=5.5)

    add_page_break(doc)

    add_heading(doc, "6.3 Social Activity Patterns", level=2)
    add_table(
        doc,
        ["Day", "Total Posts", "Negative Posts"],
        [[r["day_of_week"], r["post_count"], r["negative_count"]] for r in by_day],
    )
    add_body(doc, f"Key finding: {peak['day_of_week']} has the highest conversation volume ({peak['post_count']} posts).")
    add_chart(doc, "03_activity_by_day.png", "Figure 3: Conversation volume by weekday", width_in=5.5)
    add_chart(doc, "04_sentiment_by_brand.png", "Figure 4: Sentiment mix by brand", width_in=5.5)

    # --- 7. Conclusion ---
    add_heading(doc, "7. Conclusion & Business Takeaways")
    for t in [
        f"{worst['brand']} and American show the highest negative share — priority reputation monitoring needed.",
        f"Customer Service Issue ({reasons[0]['complaint_count']}) and Late Flight ({reasons[1]['complaint_count']}) are top complaint drivers.",
        f"Conversation volume peaks on {peak['day_of_week']} — plan social response staffing accordingly.",
        "Bronze-Silver-Gold lakehouse enables reproducible analytics from raw social data to business KPIs.",
    ]:
        add_bullet(doc, t)

    add_page_break(doc)

    # --- 8. Links (editable in Word) ---
    add_heading(doc, "8. Submission Links")
    add_body(doc, "Demo Video (public link):")
    p1 = doc.add_paragraph(DEMO_VIDEO_LINK)
    p1.paragraph_format.space_after = Pt(10)
    for run in p1.runs:
        run.font.color.rgb = BLUE
        run.underline = True

    add_body(doc, "GitHub Repository (public link):")
    p2 = doc.add_paragraph(GITHUB_LINK)
    p2.paragraph_format.space_after = Pt(10)
    for run in p2.runs:
        run.font.color.rgb = BLUE
        run.underline = True

    note = doc.add_paragraph("Replace the placeholder links above with your actual public links before submission.")
    for run in note.runs:
        run.font.italic = True
        run.font.size = Pt(10)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT_DOCX))
    print(f"Report generated: {OUTPUT_DOCX}")
    print("Open in Word and edit: Student Name (cover page), GitHub link, Demo video link.")


if __name__ == "__main__":
    build_report()
