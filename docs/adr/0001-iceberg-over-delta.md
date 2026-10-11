# ADR 0001 — Apache Iceberg as the table format (over Delta Lake)

**Status:** Accepted · **Date:** 2026-10-11

## Context
We need an open table format over Parquet files in object storage that gives us ACID writes,
schema evolution, and snapshot history. The two realistic choices are Delta Lake and Apache
Iceberg (both appear in the target JD).

## Decision
Use **Apache Iceberg** with a **REST catalog**.

## Why
- **Metadata is the product here.** This platform's whole job is reading table metadata.
  Iceberg exposes an exceptionally clean, well-documented metadata layer — snapshots,
  manifest lists, partition specs, and a full schema-evolution history with schema IDs — all
  as plain JSON/Avro we can read directly. That makes it the better teaching + building target
  for a *metadata* platform specifically.
- **Engine-neutral by design.** Iceberg deliberately avoids coupling to one engine; Delta's
  richest features historically lean toward Databricks/Spark. For a platform meant to serve
  "all data pipelines" regardless of engine, engine-neutrality matches the mandate.
- **Catalog decoupling.** The REST catalog separates "where tables live" from "who reads
  them," which is the modern production pattern and keeps the demo honest.

## Consequences
- We run an extra service (Iceberg REST catalog). Acceptable — it mirrors production.
- Lineage/metadata code targets Iceberg's API; porting to Delta would mean a new reader.
- Delta remains a valid choice in Databricks-centric shops; this is not a quality judgment,
  it's a fit judgment for a *metadata-platform* build.
