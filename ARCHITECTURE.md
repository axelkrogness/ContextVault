# Architecture

```text
Browser (Next.js)
      |
      | HTTPS / JWT or API key
      v
FastAPI control/data plane
  ├─ auth + ownership authorization
  ├─ memory lifecycle
  ├─ hybrid retrieval / RAG
  ├─ API key + usage layer
  └─ analytics/export
      |
      +-------------------+
      |                   |
      v                   v
PostgreSQL            pgvector
users/apps/agents     128-dim memory vectors
memories/keys/logs
```

The API stores every memory durably in PostgreSQL. Each memory has an embedding column suitable for pgvector indexing. The retrieval layer combines semantic similarity, keyword matching, tags and importance. Namespaces are scoped to an agent and ownership is checked through the application's user before data access.

## Security model
- Passwords are bcrypt-hashed.
- Access tokens are signed JWTs.
- Application/agent ownership is checked server-side.
- API secrets are generated with cryptographic randomness and only their SHA-256 hash is persisted.
- CORS is explicit.
- API keys can be revoked by adding a revocation route or through the data model; production deployments should also add a gateway-level rate limiter.

## RAG flow
1. Agent submits a query to `/api/v1/memories/retrieve`.
2. Query is embedded.
3. Candidate memories are filtered by agent/namespace/archive/importance.
4. Candidates receive a blended semantic + lexical + tag + importance score.
5. Top memories are returned as grounded context.
