# ADR 0002 — Graph database for lineage (over a relational store)

**Status:** Accepted · **Date:** 2026-10-11

## Context
Lineage answers recursive questions: "give me everything downstream of this column, however
many hops away." We must store tables, columns, and jobs plus the relationships between them,
and traverse those relationships cheaply.

## Decision
Store lineage in a **graph database** (Neo4j locally; modeled to port to **AWS Neptune**).

## Why
- **The workload is traversal, not joins.** Impact analysis is "walk all `derived_from` edges
  transitively." In SQL that is a recursive CTE whose cost grows with depth and fans out
  badly; in a graph it is a native, index-free adjacency traversal — the operation graph
  engines are built for.
- **The data *is* a graph.** Tables/columns = nodes; `reads`, `writes`, `derived_from` =
  edges. Modeling it as a graph removes an impedance mismatch instead of creating one.
- **Neptune is in the target stack.** We model with portable concepts (labeled nodes, typed
  edges) so the same design maps onto Neptune's openCypher/Gremlin in a real deployment.

## Alternatives considered
- **Postgres with recursive CTEs** — fine at small scale, but impact queries degrade as the
  lineage graph deepens, and the query code obscures the intent.
- **Materialized closure table** — fast reads but expensive, error-prone maintenance on every
  pipeline change. Rejected.

## Consequences
- One more service to run. Worth it: the central feature (impact analysis) becomes trivial.
- Discovery/free-text search is *not* a graph strength → handled by OpenSearch (see ADR 0003
  context). Graph for relationships, search for discovery.
