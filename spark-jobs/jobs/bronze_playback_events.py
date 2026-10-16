"""Bronze: land the raw Avro events into an Iceberg table, mostly untouched.

Bronze just captures the source with as little change as possible. Read the Avro files from the
object store, add a couple of ingestion-audit columns, write a partitioned Iceberg table. Any
real logic waits for silver.

    lakehouse.raw.playback_events   (partitioned by event_date)

Run:
    spark-submit /opt/spark-jobs/jobs/bronze_playback_events.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/opt/spark-jobs")

from pyspark.sql import functions as F

from common import get_spark, ensure_namespaces, CATALOG, RAW_BUCKET

TABLE = f"{CATALOG}.raw.playback_events"


def main() -> None:
    spark = get_spark("bronze_playback_events")
    ensure_namespaces(spark)

    # event_date comes from the directory layout (.../event_date=YYYY-MM-DD/...), so Spark
    # picks it up as a partition column automatically.
    raw = (
        spark.read.format("avro")
        .load(f"{RAW_BUCKET}/playback_events/")
    )

    bronze = (
        raw
        # ingestion audit columns, so there's some provenance to see downstream
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source", F.input_file_name())
        # Avro timestamp-millis is read by Spark as a real TIMESTAMP already; expose it under
        # a stable name for downstream jobs.
        .withColumn("event_time", F.col("event_ts").cast("timestamp"))
    )

    (
        bronze.writeTo(TABLE)
        .using("iceberg")
        .partitionedBy("event_date")
        .tableProperty("format-version", "2")
        .createOrReplace()
    )

    n = spark.table(TABLE).count()
    print(f"[bronze] wrote {n} rows -> {TABLE}")
    spark.table(TABLE).groupBy("event_date").count().orderBy("event_date").show()
    spark.stop()


if __name__ == "__main__":
    main()
