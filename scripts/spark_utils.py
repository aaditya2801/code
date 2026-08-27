"""Shared Spark helpers for Windows local mode."""

from __future__ import annotations

import os
from pathlib import Path

from pyspark.sql import SparkSession

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HADOOP_HOME = PROJECT_ROOT / "tools" / "hadoop"


def configure_hadoop_home() -> None:
    """Spark on Windows needs winutils.exe via HADOOP_HOME."""
    if not (HADOOP_HOME / "bin" / "winutils.exe").exists():
        raise FileNotFoundError(
            f"Missing winutils at {HADOOP_HOME / 'bin' / 'winutils.exe'}. "
            "Run setup or download from cdarlint/winutils (hadoop-3.3.5)."
        )
    os.environ["HADOOP_HOME"] = str(HADOOP_HOME)
    os.environ["hadoop.home.dir"] = str(HADOOP_HOME)
    # Help Java find native libs on some Windows setups
    bin_dir = str(HADOOP_HOME / "bin")
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")


def get_spark(app_name: str) -> SparkSession:
    configure_hadoop_home()
    return (
        SparkSession.builder.master("local[*]")
        .appName(app_name)
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.driver.memory", "2g")
        .config("spark.hadoop.io.native.lib.available", "false")
        .getOrCreate()
    )
