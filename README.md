# KnowledgeHub

A multi-tenant AI-powered knowledge-assistance platform.

## Project Status

KnowledgeHub is being developed incrementally using production-oriented
software engineering practices.

### Completed Sprints

- **KH-001 → KH-008** — Engineering foundation, database connectivity,
  PostgreSQL test infrastructure, automated testing, Docker and GitHub CI.
- **KH-009** — Core domain model and relational data model.

## KH-009 — Core Domain Model

The initial domain model establishes the tenant isolation boundary and the
relationships required for document-based knowledge assistance.

```text
Tenant
├── Users
└── Documents
    └── DocumentChunks