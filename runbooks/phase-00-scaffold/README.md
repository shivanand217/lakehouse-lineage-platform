# Phase 00 — Scaffold & Decisions

## Goal
Lay down the repo structure, capture the big architectural decisions as ADRs, and define the
phase plan — before writing any pipeline code.

## What was created
```
lakehouse-metadata-platform/
├── README.md                 # project overview + architecture + phase table
├── Makefile                  # operator interface (make up/down/ps/urls/...)
├── docker-compose.yml        # Phase 01 infra
├── .env.example / .env       # credentials + endpoints
├── config/spark-defaults.conf
├── docs/adr/                 # 0001 iceberg, 0002 graph-db, 0003 graphql
├── runbooks/                 # one folder per phase (this file)
├── generator/                # Phase 02
├── spark-jobs/               # Phase 03
├── airflow/                  # Phase 04
├── lineage/                  # Phase 05
└── api/                      # Phase 07
```

## Decisions (see docs/adr/)
| ADR  | Decision                           | One-line why                                  |
|------|------------------------------------|-----------------------------------------------|
| 0001 | Iceberg over Delta                 | cleanest metadata layer to read; engine-neutral |
| 0002 | Graph DB (Neo4j→Neptune) for lineage | impact analysis is recursive traversal       |
| 0003 | GraphQL over REST                  | nested, variable-depth lineage responses      |

## Verification
- `docker compose config --quiet` exits 0 (compose file is valid). ✅

## Failures / notes
- None. Chose to defer Airflow to its own Phase-04 compose overlay so the first boot stays
  light (Airflow pulls a lot and isn't needed until orchestration).
