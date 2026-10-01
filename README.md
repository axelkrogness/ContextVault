# ContextVault — Long-Term Memory Platform for AI Agents

ContextVault is a full-stack memory infrastructure platform for AI agents and applications. It lets authenticated users organize applications and agents, isolate memories in namespaces, ingest memory manually or through an API, retrieve context, and manage memory lifecycle and access.

## Technology
Python, FastAPI, SQLAlchemy, PostgreSQL, pgvector, Next.js, React, TypeScript and RAG-style retrieval.

## Features
Registration, login/logout, dashboard, applications, agents, namespaces, memory CRUD, tags, metadata, importance, expiration, retention, duplicate detection, similar-memory suggestions, archive/restore, keyword/vector/hybrid search, date filters, retrieval testing, evaluation, API keys, usage logs, rate limiting, privacy settings, permissions, export, analytics, storage tracking and backend authorization.

The website visibly displays **Powered by Codyza**.

## Documentation
- `docs/API.md`
- `docs/DATABASE.md`
- `docs/ARCHITECTURE.md`
- `docs/SETUP.md`
- `docs/REQUIREMENTS-CHECKLIST.md`
- `api/schema.sql`

## Production
The code is designed for separate Vercel API and web deployments. Production functionality must be verified after deployment; a ZIP by itself cannot prove the live API requirement.

## Semantic embeddings
For genuine semantic retrieval in production, configure `EMBEDDING_API_URL` and optionally `EMBEDDING_API_KEY`. If no provider is configured, ContextVault uses a deterministic offline fallback so memory ingestion remains available. The persisted representation is still a native PostgreSQL pgvector column.

## Production acceptance
See `docs/PRODUCTION-ACCEPTANCE.md`. Production behavior is not claimed until the deployed API passes those tests.

## Deployment
See `docs/DEPLOYMENT.md` for the Vercel API/web configuration and production environment variables.

## API ingestion example
After generating an API key in the dashboard, call `POST /api/v1/memories/ingest` with `Authorization: Bearer <api-key>` and a JSON body containing `agent_id`, optional `namespace_id`, `content`, `tags`, `metadata`, `importance`, and optional `expires_at`.

## Final submission fields
- Live web URL: https://web-axel-bdef.vercel.app/
- Live API URL: https://api-axel-bdef.vercel.app/
- GitHub repository: https://github.com/axelkrogness/ContextVault

## V9 production hardening
V9 adds automatic retention-derived expiry, exact-content plus vector duplicate detection, database indexes, rate-limit event cleanup, a readiness endpoint, and a submission manifest. The known live URLs are not marked V9-verified until redeployment and smoke testing.
