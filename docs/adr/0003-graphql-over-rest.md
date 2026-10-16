# 0003 — GraphQL for the API

Status: accepted · 2026-10-11

## Context

The platform hands lineage, impact, schema history, and discovery to other teams and tools.
The responses are nested graphs of varying depth, like "this column, its upstreams three hops
out, and who owns each of them."

## Decision

GraphQL, served with FastAPI + Strawberry, over Neo4j and OpenSearch.

## Why

Nested, variable-depth responses are exactly what GraphQL is good at. The caller asks for the
shape and depth it wants in one request. The REST version is either a lot of chatty calls or
one bloated endpoint with home-grown depth parameters.

It also puts one typed schema in front of two different backends, so a consumer never has to
know whether the graph or the search index answered. And the schema doubles as the docs, which
helps when your users are other engineers.

## What I considered instead

- REST: simpler for flat CRUD, but lineage is neither flat nor fixed-depth, so I'd end up
  reinventing query flexibility, badly.
- gRPC: good service-to-service, poor for people and tools exploring graph shapes.

## Trade-offs

A bit more setup than a plain REST handler, and the resolvers have to cap traversal depth so a
query can't run away. Caching is per-field rather than per-URL, which is fine at this size.
