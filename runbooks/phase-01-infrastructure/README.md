# Phase 01 — Infrastructure

## Goal
Stand up the entire platform locally with one command. No external accounts or systems.

## Services (docker-compose.yml)
| Service                | Image                              | Purpose                        | Port(s)       |
|------------------------|------------------------------------|--------------------------------|---------------|
| minio                  | minio/minio                        | S3-compatible object store     | 9000, 9001    |
| minio-init             | minio/mc                           | one-shot: create warehouse bucket | —          |
| iceberg-rest           | tabulario/iceberg-rest:1.6.0       | Iceberg REST catalog           | 8181          |
| spark                  | tabulario/spark-iceberg            | Spark 3.5 + Iceberg + Jupyter  | 8888,8080,4040|
| neo4j                  | neo4j:5-community                  | lineage graph                  | 7474, 7687    |
| opensearch             | opensearchproject/opensearch:2.17  | discovery search               | 9200          |
| opensearch-dashboards  | opensearchproject/opensearch-dashboards:2.17 | search UI            | 5601          |

## Commands
```bash
cp .env.example .env     # first time only
make up                  # start everything (first run pulls images, several minutes)
make ps                  # check status
make urls                # print all web UIs + creds
make spark-sql           # Spark SQL shell inside the container
make down                # stop (keeps data)
make clean               # stop + wipe all volumes (full reset)
```

## Web UIs
| UI                 | URL                              | Credentials         |
|--------------------|----------------------------------|---------------------|
| MinIO console      | http://localhost:9001            | admin / password    |
| Iceberg REST config| http://localhost:8181/v1/config  | —                   |
| Jupyter (Spark)    | http://localhost:8888            | —                   |
| Neo4j browser      | http://localhost:7474            | neo4j / lineagepass |
| OpenSearch         | http://localhost:9200            | (security disabled) |
| OpenSearch Dash    | http://localhost:5601            | —                   |

## How the pieces connect
- Spark reads `config/spark-defaults.conf` → registers catalog `lakehouse` of type `rest`
  pointing at `http://iceberg-rest:8181`, with data in `s3://warehouse/` on MinIO.
- Iceberg REST catalog stores table pointers; actual Parquet/metadata files land in MinIO
  via `S3FileIO` (path-style access, since MinIO isn't virtual-hosted).
- Neo4j and OpenSearch are independent stores populated in later phases.

## Verification
```bash
# compose file valid
docker compose config --quiet            # exits 0

# after 'make up' and services healthy:
curl -s http://localhost:8181/v1/config                     # iceberg catalog responds
curl -s http://localhost:9200/_cluster/health | jq .status  # "green"/"yellow"
docker exec lh-spark spark-sql -e "SHOW NAMESPACES IN lakehouse;"   # runs w/o error
```

## Failures / notes
- (to be filled during first boot verification)
