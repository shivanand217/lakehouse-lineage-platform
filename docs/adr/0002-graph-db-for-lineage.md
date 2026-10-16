# 0002 — Graph database for lineage

Status: accepted · 2026-10-11

## Context

Lineage questions are recursive: "give me everything downstream of this column, however many
hops out." I need to store tables, columns, and jobs along with how they relate, and walk
those relationships cheaply.

## Decision

Keep lineage in a graph database. Neo4j locally, modeled so it maps onto AWS Neptune.

## Why

The work is traversal, not joins. Impact analysis means walking `derived_from` edges
transitively. In SQL that's a recursive CTE whose cost climbs with depth and fans out badly; in
a graph it's the native operation the engine is built around.

And the data genuinely is a graph. Tables and columns are nodes, `reads` / `writes` /
`derived_from` are edges. Modeling it any other way just adds an impedance mismatch.

Neptune is a realistic target in this kind of stack, so I'm sticking to portable concepts
(labeled nodes, typed edges) that carry over to its openCypher/Gremlin.

## What I considered instead

- Postgres with recursive CTEs: fine when small, but impact queries get slow as the graph
  deepens and the SQL hides the intent.
- A materialized closure table: fast to read, but you pay for it on every pipeline change with
  fragile maintenance.

## Trade-offs

It's another service to run, but it makes the headline feature (impact analysis) almost
trivial. Graphs are bad at fuzzy free-text search, so discovery goes to OpenSearch instead:
graph for relationships, search for finding things.
