# 03 — Bronze / silver / gold

Turning the raw Avro that lands in MinIO into clean Iceberg tables, in the usual three layers.

## The jobs (spark-jobs/jobs/)

| Job                              | Reads                               | Writes                                   | Does |
|----------------------------------|-------------------------------------|------------------------------------------|------|
| `bronze_playback_events.py`      | `s3a://raw/playback_events/` (Avro) | `lakehouse.raw.playback_events`          | lands events as-is, adds ingest-audit columns |
| `silver_sessions.py`             | `raw.playback_events` + `dim_title` | `lakehouse.core.sessions`                | one row per session, watch-time, title join |
| `gold_daily_title_engagement.py` | `core.sessions`                     | `lakehouse.marts.daily_title_engagement` | daily engagement per title |

Every table is Iceberg v2, partitioned by `event_date`.

## Commands

```bash
make seed        # generate events into the MinIO raw bucket (uses the host venv)
make pipeline    # bronze -> silver -> gold in order
# or one at a time: make bronze / make silver / make gold
make spark-sql   # ad-hoc queries
```

## What I got

```
bronze   1932 rows  -> lakehouse.raw.playback_events
silver    202 rows  -> lakehouse.core.sessions
gold       24 rows  -> lakehouse.marts.daily_title_engagement
```

The gold table reads sensibly: unique_viewers, total_hours_watched and total_ad_impressions
per title per day, top titles first.

## What broke (and the fixes)

- **`Failed to find data source: avro`.** The image has the core Avro libs but not the
  `spark-avro` connector. Added `org.apache.spark:spark-avro_2.12:3.5.5` to
  `spark.jars.packages`.
- **Conf edits weren't reaching the container.** `spark-defaults.conf` is bind-mounted as a
  single file, so editing it on the host swaps the inode and the running container keeps the
  old copy. Have to `docker compose up -d --force-recreate spark` after a conf change. The job
  files are under a directory mount, so those changes show up live.
- **`ClassNotFoundException: S3AFileSystem`.** Iceberg writes go through its own S3FileIO, but
  reading raw `s3a://` Avro needs Hadoop's S3A. Added `org.apache.hadoop:hadoop-aws:3.3.4`
  (matching the image's Hadoop) to the packages; it brings the AWS SDK bundle with it.
- **`DATATYPE_MISMATCH` on `event_ts / 1000`.** Spark reads the Avro `timestamp-millis` field
  as a real timestamp already, so there was nothing to divide. Just cast it.
- Added an `ivy-cache` volume on the spark container so those Maven packages resolve once
  instead of on every recreate.
