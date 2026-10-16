# 00 — Scaffold & decisions

Laying down the repo structure and writing down the big decisions before any pipeline code
gets written.

## What's here

```
lakehouse-metadata-platform/
├── README.md                 project overview + architecture
├── Makefile                  the commands I actually run (up/down/ps/urls/...)
├── docker-compose.yml        the infrastructure
├── .env.example / .env       credentials + endpoints
├── config/spark-defaults.conf
├── docs/adr/                 the decisions: 0001 iceberg, 0002 graph-db, 0003 graphql
├── docs/roadmap.md           build plan + status
├── runbooks/                 working notes, one folder per step (this is one)
├── generator/                data generator
├── spark-jobs/               the ETL jobs
├── airflow/                  DAGs (later)
├── lineage/                  lineage extractor (later)
└── api/                      GraphQL API (later)
```

## Decisions (full writeups in docs/adr/)

- **0001** — Iceberg over Delta. Cleanest metadata to read, and it isn't tied to one engine.
- **0002** — graph DB for lineage. Impact analysis is a recursive traversal, which is what
  graphs are good at.
- **0003** — GraphQL over REST. Lineage responses are nested and vary in depth.

## Check

`docker compose config --quiet` exits 0, so the compose file is valid.

## Notes

Decided to keep Airflow out of the first compose file and add it in its own overlay later. It
pulls a lot and isn't needed until there's a pipeline to orchestrate.
