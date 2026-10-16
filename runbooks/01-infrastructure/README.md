# 01 — Infrastructure

The whole platform comes up with one command. No external accounts, no cloud.

## Services (docker-compose.yml)

| Service               | Image                                | What it is                    | Ports           |
|-----------------------|--------------------------------------|-------------------------------|-----------------|
| minio                 | bitnamilegacy/minio                  | S3-compatible object store    | 9000, 9001      |
| iceberg-rest          | tabulario/iceberg-rest:1.6.0         | Iceberg REST catalog          | 8181            |
| spark                 | tabulario/spark-iceberg              | Spark 3.5 + Iceberg + Jupyter | 8888, 8089, 4040|
| neo4j                 | neo4j:5-community                    | lineage graph                 | 7474, 7687      |
| opensearch            | opensearchproject/opensearch:2.17    | search                        | 9200            |
| opensearch-dashboards | opensearchproject/opensearch-dashboards:2.17 | search UI             | 5601            |

MinIO creates the `warehouse` bucket itself on startup (`MINIO_DEFAULT_BUCKETS`), so there's no
separate bucket-init step.

## Commands

```bash
cp .env.example .env     # first time only
make up                  # start everything (first run pulls images, a few minutes)
make ps                  # status
make urls                # all URLs + creds
make spark-sql           # SQL shell inside the spark container
make down                # stop, keep data
make clean               # stop and wipe all volumes
```

## URLs

| UI                  | URL                             | Login               |
|---------------------|---------------------------------|---------------------|
| MinIO console       | http://localhost:9001           | admin / password    |
| Iceberg REST config | http://localhost:8181/v1/config | —                   |
| Jupyter (Spark)     | http://localhost:8888           | —                   |
| Neo4j browser       | http://localhost:7474           | neo4j / lineagepass |
| OpenSearch          | http://localhost:9200           | security disabled   |
| OpenSearch dash     | http://localhost:5601           | —                   |

## How it wires up

Spark reads `config/spark-defaults.conf`, which registers a REST catalog called `lakehouse`
pointing at `http://iceberg-rest:8181`, with data under `s3://warehouse/` on MinIO. The catalog
holds the table pointers; the actual Parquet and metadata files land in MinIO through Iceberg's
`S3FileIO` with path-style access (MinIO isn't virtual-hosted). Neo4j and OpenSearch stand on
their own and get populated later.

## Checks

```bash
docker compose config --quiet                               # compose is valid (exit 0)
curl -s http://localhost:8181/v1/config                     # catalog answers
curl -s http://localhost:9200/_cluster/health | jq .status  # green / yellow
docker exec lh-spark spark-sql -e "SHOW NAMESPACES IN lakehouse;"
```

## What broke

- **MinIO's own images are gated now.** `minio/minio` and `minio/mc` on Docker Hub need a
  login as of their 2025 licensing change, even for old pinned tags. Switched to
  `bitnamilegacy/minio`, which is the same server and still public. Using `MINIO_DEFAULT_BUCKETS`
  to auto-create the bucket meant I could drop the `mc` init container entirely.
- **Port 8080 was taken.** Spark wouldn't start because something on the host already had 8080.
  Remapped its master UI to `8089:8080`. Jupyter (8888) and the app UI (4040) were fine.
- First boot pulls a few GB (spark-iceberg is the big one). After that it's quick.
