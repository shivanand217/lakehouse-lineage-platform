# Lakehouse Metadata & Lineage Platform

A self-contained data platform. It generates its own streaming data, builds a real lakehouse on
top of it (Spark + Iceberg over S3-compatible storage), and then reads that lakehouse back to
answer questions about it: what a table's lineage is, how its schema changed, and what depends
on a given column. Everything is exposed over a GraphQL API.

The point of making it self-contained is that nothing external has to exist for it to run.
`make up` brings up the whole stack locally, and a generator seeds the data.

It's the same idea as DataHub, Amundsen, OpenMetadata, or Unity Catalog, built small enough to
understand every part of.

## The problem I'm solving

In a big data org there are thousands of tables and hundreds of pipelines, and three questions
keep coming up that are surprisingly hard to answer:

1. If I change or drop this column, what downstream tables and pipelines break?
2. A number on a dashboard looks wrong. Where did it actually come from?
3. Does a table for this already exist, or am I about to rebuild it?

The approach here is to derive the answers from the pipelines themselves rather than from docs
that someone has to remember to update. Metadata that comes from the code can't go stale.

## How it fits together

```
Event generator (Python)         synthetic streaming telemetry (plays, ads, sessions)
     |  writes Avro to object store
     v
bronze  (Spark)  ->  Iceberg  raw.playback_events            (Parquet, partitioned)
     v
silver  (Spark)  ->  Iceberg  core.sessions
     v
gold    (Spark)  ->  Iceberg  marts.daily_title_engagement
     |   (orchestrated by Airflow)
     v
lineage extractor (Spark)  reads each job's query plan -> column-level lineage
     v
Neo4j (graph)   +   OpenSearch (search)
     v
GraphQL API   ->   impact analysis, lineage, discovery
```

## What runs what

| Layer           | Technology            | Notes                                           |
|-----------------|-----------------------|-------------------------------------------------|
| Object store    | MinIO (S3 API)        | local stand-in for S3; keeps the code portable  |
| Compute / ETL   | Spark 3.5             | the lakehouse engine                            |
| Table format    | Iceberg               | snapshots, schema evolution, metadata I can read|
| Catalog         | Iceberg REST catalog  | catalog decoupled from the engine               |
| Serialization   | Avro in, Parquet out  | row format for landing, columnar for storage    |
| Orchestration   | Airflow               | scheduling, dependencies, retries               |
| Lineage graph   | Neo4j (maps to Neptune)| lineage is a graph; traversal is the workload  |
| Search          | OpenSearch            | free-text table/column discovery                |
| API             | GraphQL (FastAPI)     | nested, variable-depth responses                |

The reasoning behind the bigger choices (Iceberg, the graph DB, GraphQL) is written up in
[docs/adr/](docs/adr/).

## Running it

```bash
cp .env.example .env
make up          # start everything
make ps          # check status
make urls        # service URLs + credentials
```

Once it's up:

```bash
make seed        # generate events into MinIO
make pipeline    # bronze -> silver -> gold
make spark-sql   # poke at the tables
```

- Build plan and status: [docs/roadmap.md](docs/roadmap.md)
- Per-step commands, verification, and the things that broke: [runbooks/](runbooks/)
