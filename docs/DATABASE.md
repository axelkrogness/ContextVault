# Database schema

ContextVault uses PostgreSQL and the `vector` extension.

Core tables:
- `cv_users`
- `cv_applications`
- `cv_agents`
- `cv_namespaces`
- `cv_memories` — includes a native `vector(64)` embedding column
- `cv_api_keys`
- `cv_api_usage`
- `cv_permissions`
- `cv_rate_limit_events`

UUID identifiers are used throughout. Memory records include content, tags, JSON metadata, vector representation, importance, archive state, expiration, and timestamps.
