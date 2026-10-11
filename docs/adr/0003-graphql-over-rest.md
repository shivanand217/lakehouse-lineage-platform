# ADR 0003 — GraphQL for the platform API (over REST)

**Status:** Accepted · **Date:** 2026-10-11

## Context
The platform serves lineage, impact, schema-history, and discovery to other teams and tools.
Responses are nested graphs of variable depth ("this column, its upstreams 3 hops deep, and
each of their owners").

## Decision
Expose a **GraphQL** API (FastAPI + Strawberry), backed by Neo4j and OpenSearch.

## Why
- **Variable-depth, nested responses are GraphQL's sweet spot.** A caller asks for exactly the
  shape and depth it needs in one round trip. The REST equivalent is either many chatty calls
  or one over-fetching mega-endpoint with ad-hoc depth params.
- **One typed schema over two backends.** Graph traversal (Neo4j) and discovery (OpenSearch)
  sit behind a single typed contract, so consumers never care which store answered.
- **Self-documenting contract.** The GraphQL schema *is* the API docs — valuable for a
  platform whose consumers are other engineering teams.

## Alternatives considered
- **REST** — simpler for flat CRUD, but lineage is neither flat nor fixed-depth; we'd
  reinvent query flexibility badly.
- **gRPC** — great for internal service-to-service, poor for exploratory human/tool queries
  of graph shapes. Rejected for the consumer-facing layer.

## Consequences
- Slightly more setup than a REST handler; resolver code must guard traversal depth to avoid
  runaway queries.
- Caching is per-field rather than per-URL; acceptable at this scale.
