# ContextVault

Professional long-term memory infrastructure for AI agents and applications.

**Stack:** Next.js + TypeScript, Python FastAPI, PostgreSQL + pgvector, RAG retrieval, Docker Compose.

> The repository is production-oriented and includes real persistence and a working HTTP memory API. It is not a frontend-only simulation.

## Features
- Registration, login/logout and JWT-secured sessions
- Organizations, applications and agents
- Isolated memory namespaces
- Manual and API memory ingestion
- Tags, metadata, importance, expiration and retention
- Keyword + semantic hybrid search
- Duplicate detection and similar-memory suggestions
- Archive/restore and deletion
- Retrieval testing and search-quality evaluation
- API key generation, revocation and usage logs
- Rate limits and storage/usage analytics
- Privacy controls, namespace permissions and secure authorization
- Memory export
- PostgreSQL persistence with pgvector
- RAG-ready retrieval endpoint
- Responsive premium dashboard with ContextVault branding and “Powered by Codyza”

## Quick start
1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Open http://localhost:3000.
4. Register a user, create an application and agent, then ingest memories from the dashboard or API.

## API
API docs are available at http://localhost:8000/docs.

Core endpoints:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/applications`
- `POST /api/v1/agents`
- `POST /api/v1/memories`
- `POST /api/v1/memories/search`
- `POST /api/v1/memories/retrieve`
- `POST /api/v1/memories/{id}/archive`
- `POST /api/v1/memories/{id}/restore`
- `DELETE /api/v1/memories/{id}`
- `POST /api/v1/api-keys`
- `GET /api/v1/usage`
- `GET /api/v1/export`

## Production deployment
Deploy `api` to a Python container host and `web` to Vercel/another Next.js host. Provision managed PostgreSQL with pgvector. Set `DATABASE_URL`, `JWT_SECRET`, `NEXT_PUBLIC_API_URL`, CORS and optional embedding provider variables. The Dockerfiles and health checks are included.

## Important production note
The default semantic embedding service uses a deterministic local hashing embedder so the project works without an external AI vendor. For higher-quality semantic retrieval, set `EMBEDDING_PROVIDER=openai` and `OPENAI_API_KEY`, or replace `EmbeddingService` with your preferred model provider.

## Architecture
`Next.js UI -> FastAPI -> authorization/services -> PostgreSQL + pgvector`

Hybrid retrieval combines PostgreSQL full-text ranking with pgvector cosine similarity. Retrieval results can be fed directly into an agent's RAG prompt.
