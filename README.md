# KnowledgeHub

KnowledgeHub is a multi-tenant AI-powered knowledge-assistance platform that allows organizations to securely manage their documents and provide tenant-isolated, retrieval-augmented question answering.

The platform is being built using production-oriented software engineering practices, including layered architecture, role-based authorization, tenant isolation, database migrations, automated testing, CI, configurable AI providers, persistent conversations, and a React frontend.

## Current Status

KnowledgeHub currently includes:

- JWT authentication
- Role-based authorization
- Multi-tenant isolation
- Super Admin tenant management
- Tenant Admin user management
- Sub User access control
- PDF document upload
- Tenant-scoped document management
- Document lifecycle management
- PDF processing and text extraction
- Document chunking
- Deterministic document embeddings
- Tenant-safe semantic retrieval
- Grounded RAG question answering
- RAG abstention when relevant knowledge is unavailable
- Persistent conversations and messages
- Conversation-history-aware RAG
- Configurable answer-generation providers
- Deterministic local answer generation
- OpenAI answer generation
- Google Gemini answer generation
- React frontend
- Knowledge chat interface
- Tenant document workspace
- Tenant user management frontend
- Super Admin tenant management frontend
- Frontend API tests with Vitest
- Backend tests with pytest
- Frontend production builds with Vite
- GitHub Actions CI
- Docker-based PostgreSQL development environment

The project is still under active development. The current focus is completing and validating the end-to-end frontend workflow and strengthening the production-readiness of the platform.

---

# Development Progress

The project is being implemented incrementally through numbered development sprints.

## KH-001 → KH-008 — Engineering Foundation

Established the project foundation:

- Application structure
- PostgreSQL connectivity
- SQLAlchemy foundation
- Alembic migrations
- PostgreSQL-backed test infrastructure
- Automated testing
- Docker development setup
- GitHub Actions CI

## KH-009 — Core Domain Model

Established the initial relational domain model for:

- Tenants
- Users
- Documents
- Document chunks
- Domain relationships

## KH-010 → KH-018 — Repository and Service Layers

Implemented repository and service-layer foundations for:

- Tenant management
- User management
- Document management
- Database access
- Business rules
- API foundations

## KH-019 → KH-023 — Authentication and Authorization

Implemented:

- Authentication foundation
- JWT login
- Current-user authentication dependency
- Role-based authorization
- Tenant authorization
- Protected document APIs

## KH-024 → KH-028 — Tenant and Document Management

Implemented:

- Tenant management APIs
- Tenant user management APIs
- Document lifecycle management
- Tenant-safe document status transitions
- Tenant-safe document filtering
- Physical document storage
- Secure document downloads

## KH-029 — Document Processing

Implemented PDF document processing:

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
Persisted Document Chunks
```

## KH-030 — Document Embeddings

Implemented deterministic document embeddings for the RAG pipeline.

## KH-031 — Tenant-Safe Semantic Retrieval

Implemented tenant-scoped semantic retrieval using document chunk embeddings.

The retrieval layer ensures that chunks from another tenant cannot become part of a tenant's retrieval context.

## KH-032 — Grounded RAG Q&A

Implemented:

- RAG question answering
- Retrieved-context grounding
- Similarity thresholds
- Abstention when relevant knowledge is unavailable

The system does not treat unrelated knowledge as valid context simply because a question was submitted.

## KH-033 → KH-035 — Persistent Conversations

Implemented:

- Conversation persistence
- Message persistence
- Conversation-aware RAG Q&A
- Conversation history
- Conversational context for follow-up questions

Conversation history can help resolve conversational references, while retrieved document context remains the authoritative factual source.

## KH-036 — Configurable Answer Generation

Introduced a provider abstraction for answer generation.

Supported providers include:

```text
Deterministic
OpenAI
Gemini
```

The provider is selected through environment configuration.

## KH-037 — Provider Test Isolation

Improved RAG provider tests so they remain isolated from environment-specific configuration.

## KH-038 — Frontend Knowledge Chat

Implemented the initial React knowledge-assistance workflow:

- Authentication
- Conversation list
- Conversation selection
- New conversations
- Persistent message history
- RAG question submission
- Retrieved source display
- Tenant document integration

## KH-039 — Tenant User Management

Implemented Tenant Admin user management.

Tenant Admins can:

- View Sub Users
- Create Sub Users
- Activate Sub Users
- Deactivate Sub Users

Sub Users cannot access Tenant User Management.

## KH-040 — Super Admin Tenant Management

Implemented the Super Admin frontend workflow.

Super Admins can:

- View tenants
- Create tenants
- Select a tenant
- Create Tenant Admins
- Create Sub Users
- Activate users
- Deactivate users

Tenant Admin and Sub User workflows remain separated from Super Admin functionality.

## KH-041 — Tenant Document Workspace

Implemented the tenant document workspace for frontend document operations, including:

- Tenant-scoped document listing
- PDF upload
- Document status visibility
- Document processing
- Document download
- Document status filtering
- Processing and upload state handling

## KH-042 — Frontend Workflow Integration Tests

Added frontend workflow integration tests covering the major frontend API and workflow interactions.

## Latest — Gemini Answer Generation

Added Google Gemini as an additional answer-generation provider.

The provider follows the same grounded-generation contract as the existing deterministic and OpenAI providers.

The application can select the provider through:

```env
ANSWER_GENERATION_PROVIDER=gemini
```

with:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
```

---

# Product Roles

KnowledgeHub is designed around three application roles.

## SUPER_ADMIN

Platform-wide administrator.

Can:

- Create tenants
- List tenants
- Access authorized tenant management workflows
- Manage users across tenants
- Create Tenant Admins
- Create Sub Users

## TENANT_ADMIN

Administrator for one tenant.

Can:

- Access their own tenant
- Upload PDF documents
- Process documents
- View tenant documents
- Download authorized documents
- Manage Sub Users
- Create Sub Users
- Activate Sub Users
- Deactivate Sub Users
- Ask questions against tenant knowledge

Cannot:

- Access another tenant's resources
- Create another Super Admin
- Create another Super Admin-level account
- Manage users outside their authorized tenant

## SUB_USER

Regular tenant user.

Can:

- Access their own tenant
- View authorized tenant documents
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

KnowledgeHub follows a layered backend architecture.

```text
                    HTTP Request
                         │
                         ▼
                  FastAPI API Routes
                         │
                         ▼
              Authentication / Authorization
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

The RAG subsystem extends this architecture:

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
     ├── Deterministic
     ├── OpenAI
     └── Gemini
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
├── Dockerfile
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

Authenticated users without sufficient permissions receive:

```text
403 Forbidden
```

Authorization includes:

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
    → authorized cross-tenant administration

TENANT_ADMIN
    → own tenant only

SUB_USER
    → own tenant only
```

The API does not blindly trust tenant or uploader identities supplied by clients.

Tenant-scoped validation is applied to:

- Document listing
- Document upload
- Document processing
- Document downloading
- Document retrieval
- Semantic retrieval
- RAG requests
- Conversations
- Tenant user management

Conversation persistence is additionally user scoped.

---

# Document Lifecycle

Documents use the following lifecycle:

```text
UPLOADED
    │
    ▼
PROCESSING
    │
    ├──> READY
    │
    └──> FAILED
             │
             └──> PROCESSING
```

`READY` is currently terminal.

Repeatedly applying the same status is idempotent.

Invalid lifecycle transitions are rejected.

Processing performs the ingestion pipeline:

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

# RAG Pipeline

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
   │       │
   │       ▼
   │    Abstention
   │
   └── Relevant context
           │
           ▼
      Answer Provider
           │
           ▼
       Grounded Answer
```

Retrieved document context is treated as the factual grounding source.

Conversation history can be used to resolve conversational references such as:

```text
"it"
"they"
"that document"
"the previous topic"
```

Previous assistant responses are not treated as authoritative knowledge.

If the retrieved context does not contain enough information, the system abstains rather than inventing facts.

---

# Answer Generation Providers

KnowledgeHub uses a provider abstraction for answer generation.

## Deterministic Provider

The deterministic provider:

- Does not call an external AI service
- Produces predictable output
- Is useful for local development
- Is useful for automated tests

Configure:

```env
ANSWER_GENERATION_PROVIDER=deterministic
```

## OpenAI Provider

The OpenAI provider uses the OpenAI API for answer generation.

Configure:

```env
ANSWER_GENERATION_PROVIDER=openai

OPENAI_API_KEY=your-api-key
OPENAI_MODEL=your-model
```

## Gemini Provider

The Gemini provider uses Google's Gemini API.

Configure:

```env
ANSWER_GENERATION_PROVIDER=gemini

GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.6-flash
```

All providers follow the same grounded-answer contract.

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
- Source metadata for applicable assistant responses

The frontend provides:

- Conversation list
- New conversation
- Conversation selection
- Persistent message history
- RAG question submission
- Retrieved source display

---

# Current API Surface

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

## Retrieval

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

# Document Filtering

Documents can be filtered by lifecycle status:

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

# Local Development

## Prerequisites

Install:

- Python 3.12+
- Node.js
- npm
- Docker Desktop
- PostgreSQL, or use the provided Docker Compose setup

---

## 1. Clone the Repository

```bash
git clone https://github.com/Aman-agnihotri-A/KnowledgeHUB.git

cd KnowledgeHUB
```

---

## 2. Create Python Environment

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

---

## 3. Install Backend Dependencies

```bash
python -m pip install --upgrade pip

pip install -r requirements.txt
```

---

## 4. Configure Environment

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

Configure the required database and JWT settings.

For Gemini:

```env
ANSWER_GENERATION_PROVIDER=gemini
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.6-flash
```

For OpenAI:

```env
ANSWER_GENERATION_PROVIDER=openai
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=your-model
```

For local deterministic generation:

```env
ANSWER_GENERATION_PROVIDER=deterministic
```

---

# PostgreSQL with Docker

Start the database:

```bash
docker compose up -d db
```

Stop the database:

```bash
docker compose down
```

Run migrations:

```bash
alembic upgrade head
```

---

# Run the Backend

```bash
uvicorn app.main:app --reload
```

Application:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Run the Frontend

From the frontend directory:

```bash
cd frontend

npm install

npm run dev
```

The Vite development server will display the frontend URL.

The frontend API base URL can be configured through:

```text
frontend/.env
```

using:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

# Docker

The backend also includes a Dockerfile and Docker Compose development setup.

Start the complete stack:

```bash
docker compose up --build
```

The API is exposed on:

```text
http://127.0.0.1:8000
```

The PostgreSQL database is exposed on:

```text
localhost:5432
```

---

# Testing

## Backend Tests

Run the complete backend test suite:

```bash
python -m pytest -q
```

Run a focused test:

```bash
python -m pytest tests/<test_file>.py -q
```

The backend test suite covers areas including:

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
- Semantic retrieval
- RAG
- Abstention
- Conversations
- Conversation history
- Answer-generation providers
- Database integration
- Migration behavior

## Frontend Tests

From:

```text
frontend/
```

run:

```bash
npm test
```

## Frontend Production Build

```bash
npm run build
```

---

# Continuous Integration

GitHub Actions runs the backend test pipeline on pushes and pull requests targeting `main`.

The CI workflow:

1. Starts PostgreSQL 16
2. Sets up Python 3.12
3. Installs backend dependencies
4. Runs Alembic migrations
5. Executes the backend test suite

The project therefore validates database migrations and backend tests in CI rather than relying only on local development.

---

# Security Principles

KnowledgeHub is being developed around several security boundaries.

## Authentication

Every protected endpoint requires valid authentication.

## Role Authorization

Endpoints explicitly enforce the permissions associated with the authenticated user's role.

## Tenant Isolation

Tenant-scoped resources are validated against the authenticated user's authorized tenant.

## User Ownership

Conversation resources are additionally scoped to the authenticated user.

## Server-Side Authorization

The frontend is not considered a security boundary.

Authorization decisions are enforced by the backend.

## Secrets

API keys and application secrets are supplied through environment configuration and are intentionally excluded from source control.

---

# Technology Stack

## Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Pydantic Settings
- JWT
- Pytest

## RAG

- PDF text extraction
- Document chunking
- Deterministic embeddings
- Semantic retrieval
- Grounded question answering
- Conversation-aware retrieval
- Configurable AI providers
- OpenAI
- Google Gemini

## Frontend

- React
- Vite
- Vitest
- Testing Library

## Infrastructure

- Docker
- Docker Compose
- GitHub Actions

---

# Engineering Approach

The project is intentionally being developed incrementally instead of building the entire application in one step.

The development process emphasizes:

- Small implementation increments
- Layered architecture
- Explicit domain boundaries
- Repository/service separation
- Database migrations
- Automated tests
- CI validation
- Authentication before authorization
- Authorization before tenant-scoped functionality
- Backend-enforced security
- Provider abstraction
- Frontend/backend contract testing
- Incremental frontend integration

The sprint history in this README reflects the implementation sequence used during development.

---

# Roadmap

The project is still under active development.

Planned areas include:

- End-to-end frontend workflow validation
- RAG workflow hardening
- Improved document processing reliability
- Production-grade background processing
- Better observability
- More comprehensive integration testing
- Deployment configuration
- Production security hardening
- Additional AI provider improvements
- Improved document and conversation UX

---

# Project Status

KnowledgeHub has progressed from a backend foundation into a working multi-tenant RAG application with a React frontend.

The major architectural building blocks are now in place:

```text
Authentication
      │
      ▼
Authorization
      │
      ▼
Tenant Isolation
      │
      ▼
Document Management
      │
      ▼
Document Processing
      │
      ▼
Embeddings
      │
      ▼
Semantic Retrieval
      │
      ▼
Grounded RAG
      │
      ▼
Persistent Conversations
      │
      ▼
AI Answer Generation
      │
      ▼
React Frontend
```

The project is currently in the integration and hardening phase rather than being presented as a finished production product.

---

# Author

**Aman Agnihotri**

Backend/Python developer building KnowledgeHub as a hands-on production-oriented software engineering project.

The project is being used to explore:

- Multi-tenant SaaS architecture
- Backend engineering
- RAG systems
- AI provider abstraction
- Secure authorization
- PostgreSQL data modeling
- API design
- React integration
- Automated testing
- CI/CD practices

---

# License

This project is currently a personal development project.

A formal open-source license has not yet been added.