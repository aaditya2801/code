"""Run the full local lakehouse pipeline: Bronze -> Silver -> Gold -> Insights."""

import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    "01_bronze_ingest.py",
    "02_silver_clean.py",
    "03_gold_transform.py",
    "04_insights_charts.py",
]


def main() -> None:
    scripts_dir = Path(__file__).resolve().parent
    for name in SCRIPTS:
        path = scripts_dir / name
        print(f"\n>>> Running {name} ...\n")
        result = subprocess.run([sys.executable, str(path)], check=False)
        if result.returncode != 0:
            print(f"Pipeline stopped: {name} failed with exit code {result.returncode}")
            sys.exit(result.returncode)
    print("\n=== FULL PIPELINE COMPLETE ===")
    print("Check data/bronze, data/silver, data/gold and docs/charts")


if __name__ == "__main__":
    main()
