# KnowledgeHub

KnowledgeHub is a multi-tenant AI-powered knowledge-assistance platform built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT authentication, role-based authorization, and tenant isolation.

The project is being developed incrementally using production-oriented software engineering practices.

## Current Status

The current implementation includes the authentication, authorization, tenant-management, user-management, document-management, and document-lifecycle foundations required before the RAG subsystem is introduced.

### Completed Sprints

- **KH-001 → KH-008** — Engineering foundation, PostgreSQL connectivity, PostgreSQL test infrastructure, automated testing, Docker, and GitHub Actions CI.
- **KH-009** — Core domain model and relational data model.
- **KH-010 → KH-018** — Repository and service-layer development for tenants, users, and documents.
- **KH-019** — Authentication foundation.
- **KH-020** — JWT authentication and login.
- **KH-021** — JWT request authentication and current-user dependency.
- **KH-022** — Role-based authorization.
- **KH-023** — Tenant authorization and protected document APIs.
- **KH-024** — Tenant and user management APIs.
- **KH-025** — Document lifecycle management and tenant-safe document status transitions.

> Earlier sprint ranges are summarized here where the repository history contains the corresponding implementation sequence. The Git history is the authoritative source for individual sprint commits.

## Architecture

KnowledgeHub follows a layered architecture:

```text
HTTP Request
    │
    ▼
FastAPI API Routes
    │
    ▼
Dependencies
(Authentication + Authorization)
    │
    ▼
Services
(Business Rules)
    │
    ▼
Repositories
(Database Access)
    │
    ▼
SQLAlchemy Models
    │
    ▼
PostgreSQL

Application structure
app/
├── api/
│   ├── auth.py
│   ├── documents.py
│   └── tenants.py
│
├── core/
│   ├── config.py
│   └── security.py
│
├── db/
│   └── session.py
│
├── dependencies/
│   ├── auth.py
│   └── authorization.py
│
├── models/
│   ├── base.py
│   ├── document.py
│   ├── document_chunk.py
│   ├── enums.py
│   ├── tenant.py
│   └── user.py
│
├── repositories/
│   ├── document.py
│   ├── tenant.py
│   └── user.py
│
├── schemas/
│   ├── document.py
│   ├── tenant.py
│   └── user.py
│
├── services/
│   ├── document.py
│   ├── tenant.py
│   └── user.py
│
└── main.py
Domain Model

The current domain model contains:

Tenant
├── Users
└── Documents
    └── DocumentChunks

Users belong to a tenant except for SUPER_ADMIN users.

Documents belong to exactly one tenant and record the user who uploaded them.

Document chunks belong to a document.

Roles
SUPER_ADMIN

Platform-wide administrator.

Capabilities include:

Create tenants.
List tenants.
Access any tenant.
Manage users in any tenant.
Create tenant users.
Create Tenant Admins and Sub Users.
TENANT_ADMIN

Administrator for one tenant.

Capabilities include:

Access only their own tenant.
Manage Sub Users in their own tenant.
Create Sub Users.
Upload documents.
Read documents belonging to their tenant.
Manage document lifecycle status for their tenant.

Tenant Admins cannot:

Access another tenant.
Create another Tenant Admin.
Create a Super Admin.
Manage users outside their tenant.
SUB_USER

Regular tenant user.

Capabilities include:

Access only their own tenant.
Read documents belonging to their tenant.

Sub Users cannot:

Create tenants.
Manage tenant users.
Create privileged users.
Update document lifecycle status.
Authentication

KnowledgeHub uses JWT bearer authentication.

The authentication flow is:

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

Authentication failures return:

401 Unauthorized for missing or invalid authentication credentials.
Authorization

Authorization is enforced through FastAPI dependencies.

The current authorization model distinguishes:

Authentication
    ↓
Role Authorization
    ↓
Tenant Authorization

Unauthorized users receive:

403 Forbidden

The authorization layer includes:

role-based access checks;
tenant ownership checks;
tenant-admin management checks.
Tenant Isolation

Tenant isolation is a core security boundary.

For tenant-scoped requests:

SUPER_ADMIN may access any tenant.
TENANT_ADMIN may access only their own tenant.
SUB_USER may access only their own tenant.

Document retrieval and listing are tenant-scoped.

A document belonging to another tenant cannot be accessed through a tenant-scoped document request.

Document uploads use the authenticated user's identity rather than trusting an arbitrary uploaded_by value from the request.

Current APIs
Authentication
POST /auth/login

Authenticates a user and returns a JWT access token.

Tenants
POST /tenants
GET  /tenants
GET  /tenants/{tenant_id}

Tenant creation and tenant-wide listing are restricted to Super Admins.

Tenant users
POST /tenants/{tenant_id}/users
GET  /tenants/{tenant_id}/users

Tenant user management is restricted according to the current role and tenant authorization rules.

Documents
POST  /documents/{tenant_id}
GET   /documents/{tenant_id}
GET   /documents/{tenant_id}/{document_id}
PATCH /documents/{tenant_id}/{document_id}/status

All document endpoints are tenant protected.

Document upload identity comes from the authenticated user.

Health
GET /health

Returns the current application health response.

Document Lifecycle

Documents use the following statuses:

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

READY is currently terminal.

Repeatedly setting a document to its current status is idempotent.

Invalid lifecycle transitions are rejected.

The current lifecycle implementation is intentionally separate from the future document-processing and RAG pipelines.

Database and Migrations

KnowledgeHub uses:

PostgreSQL
SQLAlchemy ORM
Alembic

The current migration history starts with the initial domain model migration.

Run migrations with:

alembic upgrade head
Local Setup
1. Clone the repository
git clone https://github.com/Aman-agnihotri-A/KnowledgeHUB.git
cd KnowledgeHUB
2. Create a virtual environment

Linux/macOS:

python -m venv .venv
source .venv/bin/activate

Windows PowerShell:

python -m venv .venv
.venv\Scripts\Activate.ps1
3. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
4. Configure environment variables

Copy the example environment file:

cp .env.example .env

On Windows PowerShell:

Copy-Item .env.example .env

Configure the database connection and JWT secret for local development.

PostgreSQL

The project includes Docker Compose configuration for local PostgreSQL development.

Start the services:

docker compose up -d

Stop the services:

docker compose down
Run Migrations
alembic upgrade head
Run the Application
uvicorn app.main:app --reload

The application will be available at:

http://127.0.0.1:8000

FastAPI documentation:

http://127.0.0.1:8000/docs
Testing

Run the complete test suite:

python -m pytest -q

Run a focused test module:

python -m pytest tests/<test_file>.py -q

The project uses PostgreSQL-backed test infrastructure and mocks dependencies at the service/API unit-test boundary where appropriate.

CI

GitHub Actions runs on pushes and pull requests targeting main.

The CI pipeline:

Starts PostgreSQL 16.
Installs Python 3.12.
Installs project dependencies.
Runs Alembic migrations.
Runs the full pytest suite.

Workflow:

.github/workflows/ci.yml

CI must remain green before a sprint is considered complete.

Security Rules

Current security semantics are:

Missing/invalid JWT
        ↓
401 Unauthorized


Authenticated but unauthorized
        ↓
403 Forbidden


Authenticated and authorized
        ↓
Endpoint executes

Tenant-scoped resources must never trust a tenant identifier or user identity without validating it through the authorization layer.

Current Scope

The current project focuses on the secure multi-tenant application foundation.

The following are intentionally not part of the current implementation:

Refresh tokens.
Logout/token revocation.
Document downloading.
Physical document storage implementation.
RAG retrieval.
Embedding generation.
Vector database integration.
Permission tables.

Those capabilities will be introduced only in later sprints when their prerequisites are complete.