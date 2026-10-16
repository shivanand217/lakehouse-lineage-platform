"""Silver: roll events up into sessions and join the title dimension.

This is where the event-level bronze table turns into something usable: one row per viewing
session, with watch-time and ad counts, plus the title attributes joined in so the data reads
in plain language.

    lakehouse.core.sessions   (partitioned by event_date)

I've kept the column math explicit (the sums, the min/max, the join key) because that's exactly
what the lineage extractor reads back out of the query plan later.

Run:
    spark-submit /opt/spark-jobs/jobs/silver_sessions.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/opt/spark-jobs")

from pyspark.sql import functions as F

from common import get_spark, ensure_namespaces, CATALOG, RAW_BUCKET

SRC = f"{CATALOG}.raw.playback_events"
DIM = f"{RAW_BUCKET}/dim_title/"
TABLE = f"{CATALOG}.core.sessions"


def main() -> None:
    spark = get_spark("silver_sessions")
    ensure_namespaces(spark)

    events = spark.table(SRC)
    dim_title = spark.read.json(DIM)  # JSON-lines dimension from the landing zone

    # one row per session: watch-time summed, ads counted, bounds via min/max
    sessions = (
        events.groupBy("session_id", "user_id", "title_id", "device", "country", "event_date")
        .agg(
            F.min("event_time").alias("session_start"),
            F.max("event_time").alias("session_end"),
            F.sum(F.coalesce("ms_watched", F.lit(0))).alias("total_ms_watched"),
            F.sum(F.when(F.col("event_type") == "ad_impression", 1).otherwise(0)).alias("num_ads"),
            F.count("*").alias("event_count"),
        )
        .withColumn(
            "session_seconds",
            F.col("total_ms_watched") / 1000,
        )
    )

    # enrich with title attributes (title_id is the join key -> lineage edge)
    enriched = (
        sessions.join(F.broadcast(dim_title), on="title_id", how="left")
        .select(
            "session_id", "user_id", "title_id",
            "title", "content_type", "franchise",
            "device", "country",
            "session_start", "session_end",
            "total_ms_watched", "session_seconds", "num_ads", "event_count",
            "event_date",
        )
    )

    (
        enriched.writeTo(TABLE)
        .using("iceberg")
        .partitionedBy("event_date")
        .tableProperty("format-version", "2")
        .createOrReplace()
    )

    n = spark.table(TABLE).count()
    print(f"[silver] wrote {n} sessions -> {TABLE}")
    spark.table(TABLE).show(5, truncate=False)
    spark.stop()


if __name__ == "__main__":
    main()
