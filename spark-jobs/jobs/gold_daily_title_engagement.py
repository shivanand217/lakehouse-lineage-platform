"""Gold: daily engagement per title.

Gold is the layer analysts and dashboards actually query. Aggregate sessions down to one row
per (event_date, title) with the headline numbers.

    lakehouse.marts.daily_title_engagement   (partitioned by event_date)

Run:
    spark-submit /opt/spark-jobs/jobs/gold_daily_title_engagement.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/opt/spark-jobs")

from pyspark.sql import functions as F

from common import get_spark, ensure_namespaces, CATALOG

SRC = f"{CATALOG}.core.sessions"
TABLE = f"{CATALOG}.marts.daily_title_engagement"


def main() -> None:
    spark = get_spark("gold_daily_title_engagement")
    ensure_namespaces(spark)

    sessions = spark.table(SRC)

    daily = (
        sessions.groupBy("event_date", "title_id", "title", "franchise", "content_type")
        .agg(
            F.sum("total_ms_watched").alias("total_ms_watched"),
            F.countDistinct("user_id").alias("unique_viewers"),
            F.count("session_id").alias("num_sessions"),
            F.sum("num_ads").alias("total_ad_impressions"),
        )
        .withColumn("total_hours_watched", F.round(F.col("total_ms_watched") / 3_600_000, 2))
        .withColumn(
            "avg_minutes_per_viewer",
            F.round((F.col("total_ms_watched") / 60_000) / F.col("unique_viewers"), 2),
        )
    )

    (
        daily.writeTo(TABLE)
        .using("iceberg")
        .partitionedBy("event_date")
        .tableProperty("format-version", "2")
        .createOrReplace()
    )

    n = spark.table(TABLE).count()
    print(f"[gold] wrote {n} rows -> {TABLE}")
    (
        spark.table(TABLE)
        .orderBy(F.col("event_date").desc(), F.col("total_hours_watched").desc())
        .show(20, truncate=False)
    )
    spark.stop()


if __name__ == "__main__":
    main()
