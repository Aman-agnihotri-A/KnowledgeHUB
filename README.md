# KnowledgeHub

A multi-tenant AI-powered knowledge-assistance platform.

## Sprint 1
Engineering foundation: FastAPI, configuration, database layer,
health endpoint, testing, Docker, and CI.

The RAG implementation comes later.

## Request flow
Browser → API → Services → Repositories → Database

AI flow later:
Browser → API → Chat Service → RAG → Retrieval/Vector Store → LLM → API
