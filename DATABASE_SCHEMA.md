# Database schema

| Table | Purpose |
|---|---|
| users | Account identity and password hash |
| applications | User-owned AI applications |
| agents | Application agents and memory namespaces |
| memories | Durable context, metadata, tags, importance, expiration and vector |
| api_keys | Hashed developer credentials |
| usage_logs | Request telemetry |

`memories.embedding` is a pgvector column. The bootstrap SQL enables the `vector` extension.
