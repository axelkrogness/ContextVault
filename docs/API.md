# ContextVault API

FastAPI generates interactive OpenAPI documentation at `/docs` and the OpenAPI schema at `/openapi.json`.

## Endpoint groups
- Authentication: register, login, logout, current user
- Applications and agents
- Namespaces and retention
- Memory create/list/update/delete
- Archive/restore and similar-memory retrieval
- Search modes: keyword, semantic/vector and hybrid
- Date filtering and importance ranking
- Programmatic API-key ingestion
- Retrieval testing and search evaluation
- RAG context retrieval
- API key generation/list/revocation
- API usage logs
- Privacy and permissions
- Export and analytics

All protected endpoints enforce authenticated user ownership through backend database joins.
