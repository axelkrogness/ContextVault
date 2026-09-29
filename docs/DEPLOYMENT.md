# Vercel deployment

## API project
Root directory: `api`

Required environment variables:
- `DATABASE_URL`
- `JWT_SECRET`
- `CORS_ORIGINS`
- `RATE_LIMIT_PER_MINUTE` (optional; defaults to 60)
- `EMBEDDING_API_URL` (recommended for genuine semantic embeddings)
- `EMBEDDING_API_KEY` (when required by the embedding provider)

Before the first API deployment, ensure the PostgreSQL `vector` extension is enabled. `api/schema.sql` contains the bootstrap statement.

The Vercel Python entrypoint is `api/index.py`, which exports the FastAPI `app`.

## Web project
Root directory: `web`

Required:
- `NEXT_PUBLIC_API_URL=https://<production-api-host>`

## CORS
`CORS_ORIGINS` must include the exact production web origin. The API must be reachable without a login redirect so browser OPTIONS preflight requests can succeed.

## Production verification
Follow `docs/PRODUCTION-ACCEPTANCE.md`. Do not claim the production requirement from local/static checks alone.
