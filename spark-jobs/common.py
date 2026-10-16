"""Shared helpers for the Spark jobs.

The session picks up the catalog and S3 settings from /opt/spark/conf/spark-defaults.conf
(mounted from config/spark-defaults.conf), so none of that is repeated here. Config stays in
one place and the jobs stay about the data.
"""
from __future__ import annotations

from pyspark.sql import SparkSession

CATALOG = "lakehouse"
RAW_BUCKET = "s3a://raw"  # landing area written by the event generator


def get_spark(app_name: str) -> SparkSession:
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def ensure_namespaces(spark: SparkSession) -> None:
    for ns in ("raw", "core", "marts"):
        spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {CATALOG}.{ns}")
