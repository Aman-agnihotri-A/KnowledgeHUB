# Initial Architecture

KnowledgeHub starts as a modular monolith.

## Main flow
Browser → API → Service → Repository → Database

## AI flow
Browser → API → Chat Service → RAG → Retrieval/Vector Store → LLM

## Module responsibilities

- `app/api` — HTTP/API boundary
- `app/core` — configuration and cross-cutting concerns
- `app/db` — database infrastructure
- `app/models` — persistence/domain models
- `app/schemas` — API request/response schemas
- `app/services` — business/application logic
- `app/repositories` — data access
- `app/rag` — retrieval/generation
- `app/workers` — background processing
- `tests` — automated tests
- `docs` — requirements and architecture
