"""
Generate capstone demo video with AI voice (Microsoft Edge TTS).

Output: docs/demo_video.mp4 (~4-5 min)

Requirements:
  pip install pillow
  Optional AI voice: pip install edge-tts  (needs internet)
  Offline voice: pip install pyttsx3      (Windows built-in voice)
  ffmpeg on PATH (https://ffmpeg.org/download.html)

Usage:
  python scripts/generate_demo_video.py
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Install: pip install pillow")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHARTS_DIR = PROJECT_ROOT / "docs" / "charts"
OUTPUT_VIDEO = PROJECT_ROOT / "docs" / "demo_video.mp4"
WORK_DIR = PROJECT_ROOT / "docs" / ".video_build"

W, H = 1280, 720
VOICE = "en-IN-NeerjaNeural"  # clear Indian English; use en-US-JennyNeural if preferred

# (slide_type, content_key, narration)
SEGMENTS: list[tuple[str, dict, str]] = [
    (
        "title",
        {
            "title": "Social Media Brand Sentiment\n& Engagement Analytics",
            "subtitle": "Big Data Capstone — Path B: PySpark Lakehouse",
            "footer": "Bronze → Silver → Gold | Local PySpark",
        },
        (
            "This demo presents our Big Data Analytics capstone project. "
            "We analyze Twitter airline sentiment using a local PySpark lakehouse pipeline, "
            "from raw ingestion through cleaning to business insights."
        ),
    ),
    (
        "bullets",
        {
            "heading": "Project Context & Dataset",
            "bullets": [
                "Domain: Social media brand sentiment analytics",
                "Dataset: Twitter US Airline Sentiment, February 2015",
                "14,640 posts across 6 airlines, 15 columns",
                "Fields: post text, sentiment, brand, retweets, complaint reason",
            ],
            "highlight": "Goal: turn raw social data into actionable business KPIs.",
        },
        (
            "Brands monitor social media to understand customer perception. "
            "Our dataset contains real Twitter posts about US airlines with sentiment labels. "
            "We ingest over fourteen thousand records and build a reproducible analytics pipeline."
        ),
    ),
    (
        "bullets",
        {
            "heading": "Lakehouse Architecture",
            "bullets": [
                "Bronze: raw CSV → Parquet (no cleaning)",
                "Silver: nulls, duplicates, schema fixes → 14,485 rows",
                "Gold: brand scoreboard, complaints, activity tables",
                "Insights: Matplotlib charts in docs/charts",
            ],
            "highlight": "Tech stack: Python, PySpark local mode, Parquet storage.",
        },
        (
            "The architecture follows the medallion pattern. "
            "Bronze preserves the raw source for audit. "
            "Silver applies data quality rules and removes one hundred fifty-five invalid rows. "
            "Gold creates business tables for reporting and visualization."
        ),
    ),
    (
        "code",
        {
            "heading": "Pipeline Execution",
            "code": (
                "python scripts/run_all.py\n\n"
                "01_bronze_ingest.py\n"
                "02_silver_clean.py\n"
                "03_gold_transform.py\n"
                "04_insights_charts.py"
            ),
            "footer": "Single command runs the full Bronze to Gold workflow.",
        },
        (
            "The pipeline runs in four steps. "
            "First, bronze ingestion loads the CSV into Parquet. "
            "Second, silver cleaning standardizes columns and removes duplicates. "
            "Third, gold transformation builds KPI tables. "
            "Finally, charts are generated for the report and this demo."
        ),
    ),
    (
        "chart",
        {
            "heading": "Insight: Brand Sentiment Health",
            "chart": CHARTS_DIR / "01_brand_negative_pct.png",
            "caption": "US Airways highest negative % | Virgin America best positive sentiment",
        },
        (
            "Brand scoreboard shows US Airways and American Airlines with the worst sentiment, "
            "above seventy percent negative posts. "
            "Virgin America performs best with the lowest negative rate and highest positive share. "
            "Operations and customer service teams can prioritize brands with the highest reputation risk."
        ),
    ),
    (
        "chart",
        {
            "heading": "Insight: Top Complaint Reasons",
            "chart": CHARTS_DIR / "02_top_negative_reasons.png",
            "caption": "Customer Service Issue is the number one pain point",
        },
        (
            "Negative posts are categorized by complaint reason. "
            "Customer service issues dominate, followed by late flights and cancellations. "
            "These insights guide where airlines should invest in process improvement."
        ),
    ),
    (
        "chart",
        {
            "heading": "Insight: Activity Patterns",
            "chart": CHARTS_DIR / "03_activity_by_day.png",
            "caption": "Peak social volume on Monday",
        },
        (
            "Activity analysis shows conversation volume peaks on Monday, "
            "with over three thousand five hundred posts. "
            "Social response teams can align staffing to high-traffic days and hours."
        ),
    ),
    (
        "chart",
        {
            "heading": "Sentiment Mix by Brand",
            "chart": CHARTS_DIR / "04_sentiment_by_brand.png",
            "caption": "Positive, neutral, and negative breakdown per brand",
        },
        (
            "The stacked sentiment chart compares positive, neutral, and negative mix across brands. "
            "Delta and Southwest show healthier sentiment profiles than legacy carriers in this sample."
        ),
    ),
    (
        "title",
        {
            "title": "Conclusion",
            "subtitle": "Path B capstone complete: raw social data → lakehouse → insights",
            "footer": "Reproducible local Big Data analytics without cloud dependency",
        },
        (
            "In summary, we built an end-to-end local lakehouse for social media analytics. "
            "Bronze, silver, and gold layers deliver clean KPIs and visual insights. "
            "Thank you for watching this demo."
        ),
    ),
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_gradient(img: Image.Image, top: tuple, bottom: tuple) -> None:
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / max(H - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=color)


def make_title_slide(data: dict, path: Path) -> None:
    img = Image.new("RGB", (W, H), (255, 255, 255))
    _draw_gradient(img, (26, 54, 93), (44, 82, 130))
    draw = ImageDraw.Draw(img)
    title_font = _font(44, bold=True)
    sub_font = _font(26)
    foot_font = _font(22)

    title_lines = data["title"].split("\n")
    y = 200
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, y), line, fill=(255, 255, 255), font=title_font)
        y += 52

    for text, font, y_pos in [
        (data.get("subtitle", ""), sub_font, y + 30),
        (data.get("footer", ""), foot_font, H - 80),
    ]:
        if not text:
            continue
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, y_pos), text, fill=(230, 240, 255), font=font)

    img.save(path)


def make_bullets_slide(data: dict, path: Path) -> None:
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W, 8)], fill=(49, 130, 206))

    h_font = _font(36, bold=True)
    b_font = _font(26)
    hi_font = _font(22, bold=True)

    draw.text((60, 40), data["heading"], fill=(26, 54, 93), font=h_font)
    y = 120
    for bullet in data["bullets"]:
        draw.text((70, y), "•", fill=(49, 130, 206), font=b_font)
        draw.text((100, y), bullet, fill=(45, 55, 72), font=b_font)
        y += 48

    highlight = data.get("highlight", "")
    if highlight:
        wrapped = textwrap.fill(highlight, width=70)
        draw.rounded_rectangle([(50, H - 120), (W - 50, H - 40)], radius=12, fill=(235, 248, 255))
        draw.text((70, H - 105), wrapped, fill=(26, 54, 93), font=hi_font)

    img.save(path)


def make_code_slide(data: dict, path: Path) -> None:
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    h_font = _font(36, bold=True)
    c_font = _font(24)
    f_font = _font(22)

    draw.text((60, 40), data["heading"], fill=(26, 54, 93), font=h_font)
    draw.rounded_rectangle([(60, 110), (W - 60, 420), radius=12, fill=(247, 250, 252), outline=(203, 213, 224))
    y = 130
    for line in data["code"].split("\n"):
        draw.text((80, y), line, fill=(26, 32, 44), font=c_font)
        y += 36

    footer = data.get("footer", "")
    if footer:
        draw.text((60, H - 80), footer, fill=(74, 85, 104), font=f_font)

    img.save(path)


def make_chart_slide(data: dict, path: Path) -> None:
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    h_font = _font(34, bold=True)
    c_font = _font(20)

    draw.text((60, 30), data["heading"], fill=(26, 54, 93), font=h_font)

    chart_path = Path(data["chart"])
    if chart_path.exists():
        chart = Image.open(chart_path).convert("RGB")
        chart.thumbnail((W - 120, H - 180), Image.Resampling.LANCZOS)
        x = (W - chart.width) // 2
        y = 90 + (H - 180 - chart.height) // 2
        img.paste(chart, (x, y))
    else:
        draw.text((60, 200), f"Chart missing: {chart_path.name}\nRun: python scripts/run_all.py", fill=(229, 62, 62), font=c_font)

    caption = data.get("caption", "")
    if caption:
        bbox = draw.textbbox((0, 0), caption, font=c_font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, H - 50), caption, fill=(74, 85, 104), font=c_font)

    img.save(path)


def render_slide(slide_type: str, data: dict, path: Path) -> None:
    makers = {
        "title": make_title_slide,
        "bullets": make_bullets_slide,
        "code": make_code_slide,
        "chart": make_chart_slide,
    }
    makers[slide_type](data, path)


async def synthesize_edge(text: str, mp3_path: Path) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(str(mp3_path))


def synthesize_pyttsx3(text: str, wav_path: Path) -> None:
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    for voice in engine.getProperty("voices"):
        if "english" in voice.name.lower() or "zira" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            break
    engine.save_to_file(text, str(wav_path))
    engine.runAndWait()


async def synthesize(text: str, mp3_path: Path) -> None:
    if HAS_EDGE_TTS:
        await synthesize_edge(text, mp3_path)
        return

    if HAS_PYTTSX3:
        wav = mp3_path.with_suffix(".wav")
        synthesize_pyttsx3(text, wav)
        run_ffmpeg(["-i", str(wav), "-c:a", "aac", "-b:a", "192k", str(mp3_path)])
        wav.unlink(missing_ok=True)
        return

    print("Install a TTS engine:")
    print("  pip install edge-tts   (AI voice, needs internet)")
    print("  pip install pyttsx3    (offline Windows voice)")
    sys.exit(1)


def run_ffmpeg(args: list[str]) -> None:
    cmd = ["ffmpeg", "-y", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("ffmpeg failed — install ffmpeg and add to PATH")


def ensure_charts() -> None:
    needed = [
        CHARTS_DIR / "01_brand_negative_pct.png",
        CHARTS_DIR / "02_top_negative_reasons.png",
        CHARTS_DIR / "03_activity_by_day.png",
        CHARTS_DIR / "04_sentiment_by_brand.png",
    ]
    if all(p.exists() for p in needed):
        return
    print("Charts missing — running insights step...")
    script = PROJECT_ROOT / "scripts" / "04_insights_charts.py"
    subprocess.run([sys.executable, str(script)], check=True, cwd=str(PROJECT_ROOT))


async def build_video() -> None:
    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found. Install from https://ffmpeg.org/download.html")
        print("Then re-run: python scripts/generate_demo_video.py")
        sys.exit(1)

    ensure_charts()
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    segment_files: list[Path] = []

    for i, (slide_type, data, narration) in enumerate(SEGMENTS):
        prefix = WORK_DIR / f"seg_{i:02d}"
        png = prefix.with_suffix(".png")
        mp3 = prefix.with_suffix(".mp3")
        mp4 = prefix.with_suffix(".mp4")

        print(f"[{i + 1}/{len(SEGMENTS)}] Slide + voice...")
        render_slide(slide_type, data, png)
        await synthesize(narration, mp3)

        run_ffmpeg(
            [
                "-loop", "1",
                "-i", str(png),
                "-i", str(mp3),
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                str(mp4),
            ]
        )
        segment_files.append(mp4)

    concat_list = WORK_DIR / "concat.txt"
    concat_list.write_text("\n".join(f"file '{p.as_posix()}'" for p in segment_files), encoding="utf-8")

    print("Merging segments...")
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(OUTPUT_VIDEO)])

    print(f"\nDone: {OUTPUT_VIDEO}")
    print(f"Duration ~{len(SEGMENTS) * 30}s | Voice: {VOICE}")


def main() -> None:
    asyncio.run(build_video())


if __name__ == "__main__":
    main()
