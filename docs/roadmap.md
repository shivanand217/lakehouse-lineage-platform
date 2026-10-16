# Build plan

I'm building this in order, one piece at a time. Each numbered piece has a folder under
`runbooks/` with the commands I ran, what I decided, how I checked it, and anything that broke.

| #  | What                     | Delivers                                        | Done |
|----|--------------------------|-------------------------------------------------|------|
| 00 | Scaffold & decisions     | repo layout, ADRs, README                       | yes  |
| 01 | Infrastructure           | docker-compose: MinIO, Spark, Iceberg, Neo4j, OpenSearch | yes  |
| 02 | Event generator          | synthetic streaming data source                 | yes  |
| 03 | Bronze / silver / gold   | Spark jobs that build the lakehouse             | yes  |
| 04 | Airflow                  | DAGs that chain the pipeline                    | no   |
| 05 | Lineage extractor        | column-level lineage pulled from Spark plans    | no   |
| 06 | Graph + search load      | populate Neo4j and OpenSearch                   | no   |
| 07 | GraphQL API              | impact, lineage, and discovery endpoints        | no   |

The matching folder under `runbooks/` has the details for anything marked done.
