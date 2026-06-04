# Graphify Guide

## What graphify gives you

- a structural graph of the repository
- an interactive HTML view
- a report of high-connectivity nodes and import relationships

## When to use it

- at the start of a new project
- after major refactors
- before security or RBAC reviews
- before writing knowledge docs for a copilot or RAG system

## How to read the graph

- high-edge nodes are usually core abstractions
- import cycles can reveal structural smell
- strongly connected areas show where rules are likely shared
- security-sensitive nodes should be easy to identify from the graph

## Practical extraction

Use the graph to discover:
- auth helpers
- error types
- base repositories
- core domain models
- service hubs

Then write docs and skills from the actual structure, not from memory.

## Workflow

1. generate the graph
2. inspect the report
3. extract the hub nodes
4. update documentation or skill references
5. regenerate after major refactors
