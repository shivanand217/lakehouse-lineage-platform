# Build Roadmap

The platform is built in incremental stages. Each stage has a runbook in `runbooks/`
(commands, decisions, verification, failures).

| Stage | Name                     | Delivers                                        | Status |
|-------|--------------------------|-------------------------------------------------|--------|
| 00    | Scaffold & decisions     | repo layout, ADRs, README                       | ✅     |
| 01    | Infrastructure           | docker-compose: MinIO, Spark, Iceberg, etc.     | ✅     |
| 02    | Event generator          | synthetic streaming data source                 | 🔜     |
| 03    | Bronze/Silver/Gold ETL   | Spark jobs building the lakehouse               | 🔜     |
| 04    | Airflow orchestration    | DAGs chaining the pipeline                       | 🔜     |
| 05    | Lineage extractor        | column-level lineage from Spark plans           | 🔜     |
| 06    | Graph + search load      | Neo4j + OpenSearch population                    | 🔜     |
| 07    | GraphQL API              | impact / lineage / discovery endpoints          | 🔜     |

See the matching folder under `runbooks/` for the details of each stage.
