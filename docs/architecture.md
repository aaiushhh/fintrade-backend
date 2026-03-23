# FItTrade LMS — Architecture

## Overview

The FItTrade LMS backend is a **Modular Monolith** built with FastAPI. Each business domain is isolated into its own module with clear boundaries, while sharing a single database and deployment unit. This architecture provides the simplicity of a monolith with the organizational benefits of microservices — and can be split into true microservices later with minimal refactoring.

## Technology Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.109 |
| Language | Python 3.11 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt |
| AI / LLM | OpenAI API (optional) |
| Vector Store | In-memory (Milvus optional) |
| Logging | structlog |
| Containerization | Docker + Docker Compose |

## Module Structure

```
lms-backend/
├── app/
│   ├── main.py                 # FastAPI entry point, lifespan, routers
│   ├── config.py               # Pydantic settings from .env
│   │
│   ├── core/                   # Cross-cutting concerns
│   │   ├── security.py         # JWT, password hashing, auth deps
│   │   └── dependencies.py     # Shared FastAPI dependencies (pagination)
│   │
│   ├── db/                     # Database layer
│   │   ├── database.py         # Async engine, session factory, init_db
│   │   └── base.py             # Model discovery for Alembic
│   │
│   ├── modules/                # Feature modules
│   │   ├── auth/               # Users, roles, sessions, devices
│   │   ├── courses/            # Courses, modules, lessons, enrollments
│   │   ├── exams/              # Entrance exams, questions, attempts, results
│   │   ├── offers/             # Discount offers, redemptions
│   │   ├── lectures/           # Scheduled lectures, recordings
│   │   ├── ai/                 # AI chatbot sessions, messages, FAQs
│   │   └── admin/              # Admin dashboard, aggregated management
│   │
│   ├── ai/                     # AI infrastructure
│   │   ├── rag_pipeline.py     # Retrieval-Augmented Generation pipeline
│   │   ├── embeddings.py       # Embedding generation (OpenAI + fallback)
│   │   └── vector_store.py     # In-memory vector store (Milvus fallback)
│   │
│   ├── integrations/           # External service stubs
│   │   ├── email_service.py    # SMTP email (stub)
│   │   └── notification_service.py  # Push notifications (stub)
│   │
│   └── utils/                  # Shared utilities
│       ├── logger.py           # structlog configuration
│       └── helpers.py          # UUID, slugify, UTC helpers
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── migrations/                 # Alembic migration scripts
├── docs/                       # Documentation
├── uploads/                    # User-uploaded files
├── requirements.txt
├── alembic.ini
└── .env.example
```

Each module follows the internal structure:
```
module_name/
├── __init__.py
├── models.py      # SQLAlchemy ORM models
├── schemas.py     # Pydantic request/response schemas
├── routes.py      # FastAPI router endpoints
└── services.py    # Business logic layer
```

## Database Schema

### Entity Relationship Summary

```
users ──< user_roles >── roles
users ──< sessions
users ──< devices
users ──< course_enrollments >── courses
users ──< exam_attempts >── entrance_exams
users ──< chat_sessions ──< chat_messages
users ──< offer_redemptions >── offers

courses ──< course_modules ──< lessons
courses ──< entrance_exams ──< exam_questions ──< exam_options
courses ──< lectures ──< lecture_recordings

exam_attempts ──< exam_answers
exam_attempts ──< exam_results
```

### Key Tables

| Table | Purpose |
|---|---|
| `users` | User accounts (email, password, profile) |
| `roles` / `user_roles` | RBAC: student, faculty, admin, distributor |
| `sessions` | JWT session tracking with revocation |
| `courses` | Course catalog with pricing |
| `course_modules` / `lessons` | Course content hierarchy |
| `course_enrollments` | Student ↔ Course mapping |
| `entrance_exams` | Exam definitions with passing score |
| `exam_questions` / `exam_options` | MCQ questions and answer options |
| `exam_attempts` / `exam_answers` | Per-student attempt tracking |
| `exam_results` | Score, percentage, pass/fail |
| `offers` / `offer_redemptions` | Discount codes and usage tracking |
| `lectures` / `lecture_recordings` | Scheduled sessions + recordings |
| `chat_sessions` / `chat_messages` | AI chatbot conversation history |
| `faq_entries` / `doubt_categories` | Knowledge base for RAG |

## Authentication & Authorization

- **JWT** tokens (access + refresh) with configurable expiry
- **Session tracking** in DB — allows server-side revocation
- **RBAC** via `require_roles()` dependency factory
- Roles: `student`, `faculty`, `admin`, `distributor`

## AI Chatbot Pipeline

```
User Question
    ↓
Generate Embedding (OpenAI / fallback hash)
    ↓
Search Vector Store (cosine similarity)
    ↓
Retrieve Top-K Context Chunks
    ↓
Generate Answer (OpenAI ChatCompletion / offline fallback)
    ↓
Persist to chat_sessions + chat_messages
    ↓
Return Answer + Sources
```

## Extensibility (Phase 2+)

The architecture is designed so these features can be added as new modules without changes to existing code:

- **Trading Simulator** → `app/modules/simulator/`
- **Monthly Exam System** → extend `exams/` or new module
- **Payment Gateway** → `app/modules/payments/`
- **Placement Evaluation** → `app/modules/placement/`
