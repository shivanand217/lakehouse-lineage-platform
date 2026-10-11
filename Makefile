SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help up down ps logs restart clean spark-sql psql-neo4j urls

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up:  ## Start all infrastructure
	@test -f .env || (echo "No .env found. Run: cp .env.example .env" && exit 1)
	docker compose up -d
	@echo "Services starting. Run 'make ps' then 'make urls'."

down:  ## Stop all services (keeps volumes/data)
	docker compose down

ps:  ## Show service status
	docker compose ps

logs:  ## Tail logs for all services (CTRL-C to exit)
	docker compose logs -f

restart:  ## Restart all services
	docker compose restart

clean:  ## Stop AND delete all data volumes (full reset)
	docker compose down -v

spark-sql:  ## Open a Spark SQL shell inside the spark container
	docker exec -it lh-spark spark-sql

urls:  ## Print the web UIs
	@echo "MinIO console       http://localhost:9001   (admin / password)"
	@echo "Iceberg REST        http://localhost:8181/v1/config"
	@echo "Spark / Jupyter     http://localhost:8888"
	@echo "Neo4j browser       http://localhost:7474    (neo4j / lineagepass)"
	@echo "OpenSearch          http://localhost:9200"
	@echo "OpenSearch Dash     http://localhost:5601"
