# ContextVault

Long-term memory infrastructure for AI agents and applications.

**Stack:** Next.js + TypeScript, FastAPI, PostgreSQL + pgvector.

## Production
Deploy `api` as a Python/FastAPI service and `web` to Vercel.

API environment:
- `DATABASE_URL`
- `JWT_SECRET`
- `CORS_ORIGINS`

Web environment:
- `NEXT_PUBLIC_API_URL`

`NEXT_PUBLIC_API_URL` must be the public API URL without a trailing slash.

## Local
Copy `.env.example` to `.env`, then run `docker compose up --build`.

Frontend: http://localhost:3000
API docs: http://localhost:8000/docs

ContextVault — Powered by Codyza.
