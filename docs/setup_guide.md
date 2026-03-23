# FItTrade LMS — Setup Guide

## Prerequisites

- **Docker** & **Docker Compose** (recommended)
- OR: Python 3.11+, PostgreSQL 16+

---

## Option 1: Docker (Recommended)

### 1. Clone and configure

```bash
cd lms-backend
cp .env.example .env
# Edit .env if needed (defaults work for local development)
```

### 2. Start all services

```bash
cd docker
docker-compose up --build
```

This starts:
- **PostgreSQL** on port `5432`
- **FastAPI backend** on port `8000`

### 3. Verify

Open http://localhost:8000/docs — you should see the Swagger UI with all endpoints.

Health check: http://localhost:8000/health

### 4. Stop

```bash
docker-compose down
# To also remove data volumes:
docker-compose down -v
```

---

## Option 2: Local Development (without Docker)

### 1. Install Python dependencies

```bash
cd lms-backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Set up PostgreSQL

Create database and user:

```sql
CREATE USER lms_user WITH PASSWORD 'lms_password';
CREATE DATABASE lms_db OWNER lms_user;
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL to point to your local PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://lms_user:lms_password@localhost:5432/lms_db
```

### 4. Run database migrations

```bash
# Generate initial migration (first time only):
alembic revision --autogenerate -m "initial"

# Apply migrations:
alembic upgrade head
```

Note: The app also auto-creates tables on startup via `init_db()` for convenience during development.

### 5. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Verify

Open http://localhost:8000/docs

---

## Running Migrations

### Create a new migration after model changes

```bash
alembic revision --autogenerate -m "describe your changes"
```

### Apply pending migrations

```bash
alembic upgrade head
```

### Rollback one migration

```bash
alembic downgrade -1
```

---

## Optional: Enable Milvus (Vector Database)

1. In `docker/docker-compose.yml`, uncomment the `milvus` service section
2. In `.env`, set:
   ```
   USE_MILVUS=true
   MILVUS_HOST=milvus
   MILVUS_PORT=19530
   ```
3. Restart: `docker-compose up --build`

Without Milvus, the AI chatbot uses an **in-memory vector store** (works fine for development).

---

## Optional: Enable Redis (Caching)

1. Uncomment the `redis` service in `docker-compose.yml`
2. In `.env`, set: `REDIS_URL=redis://redis:6379/0`
3. Restart

---

## Optional: Configure OpenAI (AI Chatbot)

Set your API key in `.env`:

```
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-ada-002
```

Without an API key, the chatbot uses a **fallback mode** that returns context from the knowledge base without LLM generation.

---

## Project Structure Quick Reference

```
lms-backend/
├── app/
│   ├── main.py          # Entry point
│   ├── config.py        # Settings
│   ├── core/            # Security, dependencies
│   ├── db/              # Database engine
│   ├── modules/         # Feature modules (auth, courses, exams, ...)
│   ├── ai/              # RAG pipeline, embeddings, vector store
│   ├── integrations/    # Email, notifications
│   └── utils/           # Logger, helpers
├── docker/              # Dockerfile + compose
├── migrations/          # Alembic migrations
├── docs/                # This documentation
├── requirements.txt
├── alembic.ini
└── .env.example
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `connection refused` to PostgreSQL | Ensure PostgreSQL is running and DATABASE_URL is correct |
| `relation does not exist` | Run `alembic upgrade head` or restart the app (auto-creates tables) |
| AI chatbot returns generic answers | Set `OPENAI_API_KEY` in `.env` |
| Docker build fails | Ensure Docker Desktop is running and you have internet |
