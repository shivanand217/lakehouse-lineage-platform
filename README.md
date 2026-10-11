# Lakehouse Metadata & Lineage Platform

A **self-contained** data platform that generates its own streaming data, builds a real
lakehouse (Spark + Iceberg on S3-compatible storage), and then **automatically understands
that lakehouse** — its tables, schema evolution, and column-level lineage — exposing it all
through a searchable GraphQL API.

This is a working miniature of the product category that includes DataHub, Amundsen,
OpenMetadata, and Databricks Unity Catalog. Nothing external is required: `make up` stands up
the entire platform locally.

---

## Why this exists (the problem)

In a large data org there are thousands of tables and hundreds of pipelines. Three questions
get asked constantly and are painfully hard to answer:

1. **Impact** — "If I change or drop this column, what downstream tables/pipelines break?"
2. **Lineage** — "This dashboard number is wrong. Where did the value actually come from?"
3. **Discovery** — "Does a table for X already exist, or am I about to rebuild it?"

This platform answers all three by deriving metadata **automatically from the pipelines
themselves** (not hand-maintained docs that go stale).

---

## Architecture

```
[1] Event Generator (Python)         synthetic streaming telemetry (plays, ads, sessions)
        │  writes Avro to object store
        ▼
[2] Bronze ingest   (Spark)  ──►  Iceberg  raw.playback_events     (Parquet, partitioned)
        ▼
[3] Silver transform(Spark)  ──►  Iceberg  core.sessions
        ▼
[4] Gold aggregate  (Spark)  ──►  Iceberg  marts.daily_title_engagement
        │
        │   (all orchestrated by Airflow)
        ▼
[5] Lineage Extractor (Spark)  reads each job's query plan → column-level lineage
        ▼
[6] Graph DB (nodes+edges)   +   OpenSearch (searchable catalog)
        ▼
[7] GraphQL API  ◄── impact analysis · root-cause lineage · discovery search
```

### Component / technology map

| Layer              | Technology            | Why (see `docs/adr/`)                              |
|--------------------|-----------------------|----------------------------------------------------|
| Object store       | MinIO (S3 API)        | Local stand-in for S3; code stays cloud-portable   |
| Compute / ETL      | Apache Spark 3.5      | Industry-standard lakehouse engine                 |
| Table format       | Apache Iceberg        | Snapshots, schema evolution, rich metadata to read |
| Catalog            | Iceberg REST catalog  | Decoupled catalog, the modern Iceberg pattern      |
| Serialization      | Avro (ingest) → Parquet (store) | Row format for writes, columnar for reads|
| Orchestration      | Apache Airflow        | Scheduling, dependencies, retries                  |
| Lineage graph      | Neo4j (Neptune-ready) | Recursive relationship traversal                   |
| Discovery search   | OpenSearch            | Fuzzy free-text catalog search                     |
| API                | GraphQL (FastAPI + Strawberry) | Nested, variable-depth graph responses    |

---

## Build phases

Each phase has a runbook in `runbooks/` (commands, decisions, verification, failures).

| Phase | Name                     | Delivers                                        | Status |
|-------|--------------------------|-------------------------------------------------|--------|
| 00    | Scaffold & decisions     | repo layout, ADRs, this README                  | ✅     |
| 01    | Infrastructure           | docker-compose: MinIO, Spark, Iceberg, etc.     | ✅     |
| 02    | Event generator          | synthetic streaming data source                 | 🔜     |
| 03    | Bronze/Silver/Gold ETL   | Spark jobs building the lakehouse               | 🔜     |
| 04    | Airflow orchestration    | DAGs chaining the pipeline                       | 🔜     |
| 05    | Lineage extractor        | column-level lineage from Spark plans           | 🔜     |
| 06    | Graph + search load      | Neo4j + OpenSearch population                    | 🔜     |
| 07    | GraphQL API              | impact / lineage / discovery endpoints          | 🔜     |

---

## Quick start

```bash
cp .env.example .env
make up          # start all infrastructure
make ps          # verify services are healthy
```

See `runbooks/phase-01-infrastructure/README.md` for service URLs and verification steps.
