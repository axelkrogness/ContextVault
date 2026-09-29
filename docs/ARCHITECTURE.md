# Architecture

Browser → Next.js → FastAPI → SQLAlchemy → PostgreSQL + pgvector.

Authentication uses JWT for users and hashed API keys for programmatic ingestion. Ownership joins isolate users. Application permissions provide viewer/editor sharing records.

Memory retrieval combines keyword matching, importance and cosine similarity over persisted vector embeddings. `/api/v1/context` exposes retrieved context for RAG workflows. Retention can be enforced from namespace retention days and explicit expiration timestamps.

## V5 production hardening
API requests authenticated by JWT are rate-limited using persisted PostgreSQL events and recorded in API usage logs. pgvector availability is validated at startup rather than silently ignored. Optional provider-backed embeddings allow genuine semantic vectors while retaining an offline fallback. Application sharing uses viewer/editor permission records, and owner privacy mode blocks shared access.
