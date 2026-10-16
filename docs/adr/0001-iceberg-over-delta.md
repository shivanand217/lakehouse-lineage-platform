# 0001 — Iceberg for the table format

Status: accepted · 2026-10-11

## Context

I need an open table format over Parquet in object storage, with ACID writes, schema
evolution, and snapshot history. Realistically that's Delta Lake or Iceberg.

## Decision

Iceberg, with a REST catalog.

## Why

The whole point of this project is reading table metadata, and Iceberg's metadata is the
easiest to read: snapshots, manifest lists, partition specs, and the full schema history (with
schema IDs) all sit there as plain JSON/Avro. For a metadata tool that matters more than
anything else.

It also isn't tied to one engine. Delta's best features have historically leaned toward
Databricks and Spark; Iceberg was built engine-neutral from the start, which fits a platform
meant to serve pipelines regardless of what runs them.

The REST catalog keeps "where tables live" separate from "who reads them," which is how this
runs in production anyway.

## Trade-offs

Running the REST catalog is one more service, but it mirrors a real setup so I'll take it. The
metadata-reading code targets Iceberg's API; pointing it at Delta would mean a different
reader. Delta is still the right call in a Databricks-heavy shop — this is about fit, not which
one is "better."
