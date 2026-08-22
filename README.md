# KnowledgeHub

KnowledgeHub is a multi-tenant AI-powered knowledge-assistance platform built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT authentication, React, and a tenant-isolated RAG pipeline.

The project is being developed incrementally using production-oriented engineering practices: layered architecture, explicit authorization boundaries, tenant isolation, migrations, automated tests, CI, configurable AI providers, and a frontend that reflects the backend security model.

---

## Current Status

The current system provides:

- JWT authentication
- Role-based authorization
- Multi-tenant isolation
- Super Admin tenant management
- Tenant Admin user management
- Sub User access control
- PDF document upload and storage
- Document lifecycle management
- Document processing and chunking
- Deterministic document embeddings
- Tenant-safe semantic retrieval
- Grounded RAG question answering
- Abstention when relevant knowledge is unavailable
- Persistent conversations and messages
- Conversation-history-aware RAG
- Configurable deterministic/OpenAI answer generation
- React frontend integration for authentication, documents, RAG conversations, tenant users, and Super Admin tenant management
- Frontend API tests with Vitest
- Backend tests with pytest
- Frontend production build with Vite
- GitHub Actions CI

The latest completed frontend milestone is Super Admin tenant management.

---

## Completed Development Sequence

The sprint identifiers below describe the development sequence we have actually implemented. They are not GitHub Issues or a GitHub-maintained sprint board.

### KH-001 → KH-008
Engineering foundation:

- Project structure
- PostgreSQL connectivity
- SQLAlchemy foundation
- Alembic migrations
- PostgreSQL-backed test infrastructure
- Automated testing
- Docker development setup
- GitHub Actions CI

### KH-009
Core domain and relational data model.

### KH-010 → KH-018
Repository and service-layer development for:

- Tenants
- Users
- Documents
- Database access
- Business rules
- API foundations

### KH-019
Authentication foundation.

### KH-020
JWT authentication and login.

### KH-021
JWT request authentication and current-user dependency.

### KH-022
Role-based authorization.

### KH-023
Tenant authorization and protected document APIs.

### KH-024
Tenant and user management APIs.

### KH-025
Document lifecycle management and tenant-safe status transitions.

### KH-026
Tenant user lifecycle management and role-safe user creation.

### KH-027
Tenant-safe document status filtering.

### KH-028
Physical document storage and secure document download.

### KH-029
Document processing and PDF chunking.

### KH-030
Document embeddings.

### KH-031
Tenant-safe semantic retrieval.

### KH-032
Grounded RAG question answering and abstention.

### KH-033
Conversation persistence foundation.

### KH-034
Conversation-aware RAG Q&A persistence.

### KH-035
Conversation-history-aware RAG context.

### KH-036
Configurable answer-generation providers, including deterministic local generation and OpenAI generation.

### KH-037
RAG provider test isolation from environment configuration.

### KH-038
Frontend knowledge chat, document management integration, and frontend API tests.

### KH-039
Tenant User Management frontend.

Tenant Admin can:

- View Sub Users
- Create Sub Users
- Activate Sub Users
- Deactivate Sub Users

Sub Users cannot access Tenant User Management.

### KH-040
Super Admin tenant management frontend.

Super Admin can:

- View tenants
- Create tenants
- Select a tenant
- Create Tenant Admins
- Create Sub Users
- Activate users
- Deactivate users

Tenant Admin and Sub User workflows remain separated from Super Admin functionality.

---

# Product Roles

## SUPER_ADMIN

Platform-wide administrator.

Can:

- Create tenants
- List tenants
- Access any tenant through authorized APIs
- Manage users in any tenant
- Create Tenant Admins
- Create Sub Users

The frontend provides a dedicated Super Admin tenant-management interface.

## TENANT_ADMIN

Administrator for one tenant.

Can:

- Access only their tenant
- Upload PDF documents
- Process documents
- View tenant documents
- Manage Sub Users
- Create Sub Users
- Activate/deactivate Sub Users
- Ask questions against tenant knowledge

Cannot:

- Access another tenant
- Create another Tenant Admin
- Create a Super Admin
- Manage users outside their tenant

## SUB_USER

Regular tenant user.

Can:

- Access only their own tenant
- View tenant documents
- Download authorized tenant documents
- Ask questions against tenant knowledge
- Use persistent conversations

Cannot:

- Create tenants
- Manage tenant users
- Create privileged users
- Process documents
- Change document lifecycle state

---

# Architecture

KnowledgeHub follows a layered architecture:

```text
                    HTTP Request
                         │
                         ▼
                  FastAPI API Routes
                         │
                         ▼
                Authentication /
                  Authorization
                         │
                         ▼
                      Services
                 Business Rules
                         │
                         ▼
                   Repositories
                  Database Access
                         │
                         ▼
                 SQLAlchemy Models
                         │
                         ▼
                    PostgreSQL
```

The RAG subsystem adds:

```text
User Question
     │
     ▼
RAG API
     │
     ▼
Conversation Context
     │
     ▼
Tenant-Safe Retrieval
     │
     ▼
Retrieved Document Chunks
     │
     ▼
Answer Generation Provider
     │
     ├── Deterministic Provider
     │
     └── OpenAI Provider
     │
     ▼
Grounded Answer
     │
     ▼
Conversation Persistence
```

---

# Application Structure

```text
KnowledgeHUB/
│
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── conversations.py
│   │   ├── documents.py
│   │   ├── rag.py
│   │   └── tenants.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── db/
│   │   └── session.py
│   │
│   ├── dependencies/
│   │   ├── auth.py
│   │   └── authorization.py
│   │
│   ├── models/
│   │   ├── base.py
│   │   ├── conversation.py
│   │   ├── document.py
│   │   ├── document_chunk.py
│   │   ├── enums.py
│   │   ├── tenant.py
│   │   └── user.py
│   │
│   ├── repositories/
│   │   ├── conversation.py
│   │   ├── document.py
│   │   ├── document_chunk.py
│   │   ├── tenant.py
│   │   └── user.py
│   │
│   ├── rag/
│   │   ├── answer_generation.py
│   │   └── qa.py
│   │
│   ├── schemas/
│   │   ├── conversation.py
│   │   ├── document.py
│   │   ├── rag.py
│   │   ├── retrieval.py
│   │   ├── tenant.py
│   │   └── user.py
│   │
│   ├── services/
│   │   ├── conversation.py
│   │   ├── document.py
│   │   ├── embedding.py
│   │   ├── retrieval.py
│   │   ├── storage.py
│   │   ├── tenant.py
│   │   └── user.py
│   │
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── api.test.js
│   │   ├── main.jsx
│   │   ├── styles.css
│   │   └── testSetup.js
│   ├── package.json
│   └── vite.config.js
│
├── alembic/
├── tests/
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Domain Model

```text
Tenant
├── Users
└── Documents
    └── DocumentChunks

Tenant
└── Conversations
    └── ConversationMessages
```

Users belong to a tenant except for Super Admin users.

Documents belong to exactly one tenant and record the authenticated uploader.

Document chunks belong to one document.

Conversations belong to one tenant and one user.

Conversation messages belong to one conversation.

---

# Authentication

KnowledgeHub uses JWT bearer authentication.

```text
User credentials
      │
      ▼
POST /auth/login
      │
      ▼
JWT access token
      │
      ▼
Authorization: Bearer <token>
      │
      ▼
Current-user dependency
```

Missing or invalid authentication returns:

```text
401 Unauthorized
```

---

# Authorization

Authorization is enforced through FastAPI dependencies.

The security boundary is:

```text
Authentication
      ↓
Role Authorization
      ↓
Tenant Authorization
      ↓
Endpoint
```

Unauthorized authenticated users receive:

```text
403 Forbidden
```

The authorization layer includes:

- Role checks
- Tenant ownership checks
- Tenant Admin management checks
- Conversation ownership checks
- Document tenant isolation

---

# Tenant Isolation

Tenant isolation is a core security boundary.

For tenant-scoped resources:

```text
SUPER_ADMIN
    → may access any tenant

TENANT_ADMIN
    → own tenant only

SUB_USER
    → own tenant only
```

The API never trusts a client-provided tenant or uploader identity without authorization validation.

Document retrieval, document listing, document processing, document downloading, semantic retrieval, RAG requests, and conversations are tenant scoped.

Conversation persistence is additionally user scoped.

---

# Document Lifecycle

Documents use:

```text
UPLOADED
    │
    ├──> PROCESSING
    │       │
    │       ├──> READY
    │       │
    │       └──> FAILED
    │
    └──> FAILED
             │
             └──> PROCESSING
```

`READY` is currently terminal.

Repeatedly applying the same status is idempotent.

Invalid lifecycle transitions are rejected.

Processing currently performs the document ingestion pipeline required by the RAG subsystem:

```text
PDF
 │
 ▼
Text Extraction
 │
 ▼
Chunking
 │
 ▼
Embedding Generation
 │
 ▼
Persisted Document Chunks
```

---

# RAG

The current RAG pipeline is tenant safe.

```text
Question
   │
   ▼
Question Embedding
   │
   ▼
Tenant-Scoped Ready Chunks
   │
   ▼
Cosine Similarity
   │
   ▼
Top-K Retrieved Chunks
   │
   ▼
Similarity Threshold
   │
   ├── No relevant context
   │       ↓
   │    Abstain
   │
   └── Relevant context
           ↓
      Answer Provider
           ↓
       Grounded Answer
```

The answer-generation layer supports:

- Deterministic local provider
- OpenAI provider

The OpenAI provider is configurable through environment settings.

Retrieved document context is treated as the factual grounding source.

Conversation history may be used for conversational continuity, but previous assistant responses are not treated as authoritative knowledge.

---

# Conversations

Users can create persistent conversations.

Each conversation belongs to:

- One tenant
- One user

Messages contain:

- Role
- Content
- Timestamp
- Persisted source metadata for assistant answers where applicable

The frontend provides:

- Conversation list
- New conversation
- Conversation selection
- Persistent message history
- Source display for RAG answers

---

# Current APIs

## Authentication

```text
POST /auth/login
```

## Tenants

```text
POST /tenants
GET  /tenants
GET  /tenants/{tenant_id}
```

Tenant creation and tenant-wide listing are Super Admin operations.

## Tenant Users

```text
POST  /tenants/{tenant_id}/users
GET   /tenants/{tenant_id}/users
PATCH /tenants/{tenant_id}/users/{user_id}/status
```

## Documents

```text
POST  /documents/{tenant_id}
POST  /documents/{tenant_id}/upload
GET   /documents/{tenant_id}
GET   /documents/{tenant_id}/{document_id}
GET   /documents/{tenant_id}/{document_id}/download
POST  /documents/{tenant_id}/{document_id}/process
PATCH /documents/{tenant_id}/{document_id}/status
```

## Document Retrieval

```text
GET /documents/{tenant_id}/retrieve?query=<query>&top_k=<n>
```

## RAG

```text
POST /rag/{tenant_id}/ask
```

## Conversations

```text
POST /conversations/{tenant_id}
GET  /conversations/{tenant_id}
GET  /conversations/{tenant_id}/{conversation_id}
```

## Health

```text
GET /health
```

---

# Document Status Filtering

The document listing endpoint supports:

```text
GET /documents/{tenant_id}
```

or:

```text
GET /documents/{tenant_id}?status=uploaded
GET /documents/{tenant_id}?status=processing
GET /documents/{tenant_id}?status=ready
GET /documents/{tenant_id}?status=failed
```

Filtering is performed through the repository/service layers and remains tenant scoped.

---

# Database and Migrations

KnowledgeHub uses:

- PostgreSQL
- SQLAlchemy
- Alembic

Run migrations:

```bash
alembic upgrade head
```

---

# Local Setup

## 1. Clone

```bash
git clone https://github.com/Aman-agnihotri-A/KnowledgeHUB.git
cd KnowledgeHUB
```

## 2. Create Python environment

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. Install backend dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure environment

Copy:

```text
.env.example
```

to:

```text
.env
```

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Linux/macOS

```bash
cp .env.example .env
```

Configure the PostgreSQL connection and JWT settings.

If OpenAI generation is enabled, configure the OpenAI API key and model.

---

# PostgreSQL

Start the development database:

```bash
docker compose up -d
```

Stop it:

```bash
docker compose down
```

Run migrations:

```bash
alembic upgrade head
```

---

# Run Backend

```bash
uvicorn app.main:app --reload
```

Application:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

# Run Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite development server will display the frontend URL in the terminal.

If the backend is not served from the same origin, configure:

```text
VITE_API_BASE_URL
```

in the frontend environment.

---

# Testing

## Backend

Run the complete backend suite:

```bash
python -m pytest -q
```

Focused test:

```bash
python -m pytest tests/<test_file>.py -q
```

The backend suite covers:

- Authentication
- JWT validation
- Authorization
- Tenant isolation
- Tenant management
- User management
- Document management
- Document lifecycle
- Document filtering
- Document storage
- Document processing
- Embeddings
- Retrieval
- RAG
- Abstention
- Conversations
- Conversation history
- Answer-generation providers
- Database integration
- Migration behavior

## Frontend

From `frontend/`:

```bash
npm test
```

Run the production build:

```bash
npm run build
```

The frontend test suite covers the API client behavior and authentication/session handling.

---

# CI

GitHub Actions runs the backend test suite on pushes and pull requests targeting `main`.

The CI pipeline:

1. Starts PostgreSQL.
2. Installs Python.
3. Installs dependencies.
4. Runs Alembic migrations.
5. Runs pytest.

Frontend validation is also part of local sprint completion:

```bash
cd frontend
npm test
npm run build
```

A sprint is considered complete only after the relevant backend tests, frontend tests, frontend build, and affected workflow have been verified locally.

---

# Security Rules

Current security semantics:

```text
Missing / invalid JWT
        ↓
401 Unauthorized

Authenticated but unauthorized
        ↓
403 Forbidden

Authenticated and authorized
        ↓
Endpoint executes
```

Important rules:

- Never trust a client-provided uploader identity.
- Never trust a tenant identifier without authorization validation.
- Never return another tenant's documents.
- Never allow a Sub User to manage tenant users.
- Never allow a Tenant Admin to manage another tenant.
- Conversation access is restricted to the owning tenant user.
- RAG retrieval is tenant scoped.
- RAG only retrieves chunks from READY documents.
- Grounded answer generation must not invent knowledge outside retrieved context.

---

# Frontend Role Experience

## Super Admin

Dedicated tenant-management interface:

```text
Tenant Management
├── Create Tenant
├── Tenant List
└── Selected Tenant
    └── User Management
        ├── Create Tenant Admin
        ├── Create Sub User
        ├── Activate User
        └── Deactivate User
```

## Tenant Admin

```text
KnowledgeHub
├── Documents
│   ├── Upload PDF
│   ├── Process
│   └── Document status
├── Tenant Users
│   ├── Create Sub User
│   ├── Activate
│   └── Deactivate
└── RAG Conversations
```

## Sub User

```text
KnowledgeHub
├── Documents
└── RAG Conversations
```

Tenant User Management controls are not exposed to Sub Users.

---

# Current Scope

KnowledgeHub has progressed beyond the initial authentication and CRUD foundation.

The current implementation now includes the core product loop:

```text
Tenant
  │
  ├── Users
  │
  └── Documents
        │
        ▼
     Processing
        │
        ▼
      Chunks
        │
        ▼
    Embeddings
        │
        ▼
     Retrieval
        │
        ▼
   Grounded RAG
        │
        ▼
  Conversations
```

The frontend provides role-aware access to the major product capabilities.

---

# Intentionally Deferred / Future Work

The following capabilities are not yet part of the completed implementation:

- Refresh tokens
- Token revocation / server-side logout
- Background document-processing workers
- Asynchronous job queues
- Production vector database integration
- Advanced hybrid retrieval
- Reranking
- Citation-quality evaluation
- RAG evaluation datasets
- Rate limiting
- Advanced observability
- Metrics and tracing
- Audit logging
- Fine-grained permission tables
- Production object storage
- Multi-file bulk ingestion
- Production deployment infrastructure
- Automated end-to-end browser testing
- CI frontend test/build enforcement
- Advanced administrative analytics

These should be introduced only after their prerequisites are implemented and validated.

---

# Engineering Principles

KnowledgeHub is intentionally being built with production-oriented practices.

Key principles:

- One complete sprint at a time
- Inspect the existing implementation before changing it
- Preserve working architecture
- Keep business rules in services
- Keep database access in repositories
- Keep authentication/authorization in dependencies
- Keep tenant isolation explicit
- Test behavior rather than implementation details
- Prefer deterministic local behavior for tests
- Keep external AI providers configurable
- Validate locally before pushing to GitHub
- Keep GitHub as the source-of-reference for the shared project state
- Do not introduce speculative infrastructure before the application requires it

---

# Project Goal

The long-term goal is to evolve KnowledgeHub into a production-oriented multi-tenant AI knowledge platform where:

- Super Admins manage tenants.
- Tenant Admins manage their organization's knowledge and users.
- Sub Users consume approved tenant knowledge.
- Documents are securely processed and indexed.
- Retrieval is tenant isolated.
- Answers are grounded in tenant-provided knowledge.
- Conversations preserve useful context.
- AI providers can be replaced without rewriting the application.
- The system can eventually support production-scale asynchronous processing, observability, evaluation, and deployment.

The RAG subsystem is a core capability of KnowledgeHub, but it is not the entire product.
