# Setup instructions

## PostgreSQL
ContextVault requires PostgreSQL with the `vector` extension. The API attempts `CREATE EXTENSION IF NOT EXISTS vector` on startup. If your managed database does not allow this, enable pgvector from the provider dashboard or run `api/schema.sql` with an authorized database account.

## API
1. `cd api`
2. `python -m venv .venv`
3. Windows: `.venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env`
6. Configure `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`
7. `uvicorn app.main:app --reload`

## Web
1. `cd web`
2. `npm install`
3. Copy `.env.example` to `.env.local`
4. Set `NEXT_PUBLIC_API_URL`
5. `npm run dev`

## Production
Deploy `api` and `web` as separate Vercel projects. Set `NEXT_PUBLIC_API_URL` to the production API URL and `CORS_ORIGINS` to the production frontend origin. Deployment Protection must not redirect API OPTIONS requests.

Production acceptance requires testing registration, login, application/agent/namespace creation, memory CRUD, search, API-key ingestion, permissions, retention, export, analytics, `/health`, and `/docs`.
