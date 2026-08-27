# Architecture — Local PySpark Lakehouse (Path B)

## Data flow

```
┌─────────────────────────────┐
│  Social Media Dataset (CSV) │
│  Twitter brand sentiment    │
│  14,640 posts × 15 columns  │
└──────────────┬──────────────┘
               │ ingest (no transform)
               ▼
┌─────────────────────────────┐
│  BRONZE                     │
│  data/bronze/tweets_bronze  │
│  Raw snapshot (Parquet)     │
└──────────────┬──────────────┘
               │ clean: nulls, dups, types
               ▼
┌─────────────────────────────┐
│  SILVER                     │
│  data/silver/tweets_silver  │
│  Analytics-ready posts      │
└──────────────┬──────────────┘
               │ aggregate + business logic
               ▼
┌─────────────────────────────┐
│  GOLD                       │
│  brand_scoreboard           │
│  top_negative_reasons       │
│  activity_by_day/hour       │
│  fact_posts, trends, ...    │
└──────────────┬──────────────┘
               │ visualize
               ▼
┌─────────────────────────────┐
│  INSIGHTS                   │
│  docs/charts/*.png          │
│  Report + Demo Video        │
└─────────────────────────────┘
```

## Tech stack
- **Storage:** Local folders (Bronze / Silver / Gold)
- **Processing:** PySpark `local[*]`
- **Language:** Python
- **Charts:** Matplotlib / Seaborn

## Why this maps to Path B
Path B requires a lakehouse workflow:
1. Bronze = raw ingestion  
2. Silver = cleaning / schema correction  
3. Gold = fact/dimension style reporting tables  

This project implements exactly that on a local machine (no AWS/cloud).
