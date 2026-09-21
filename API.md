# ContextVault API

Base URL: `http://localhost:8000`

Swagger UI: `/docs`

## Authentication
Register/login returns a Bearer JWT. Send it as `Authorization: Bearer <token>`.

## Ingest
`POST /api/v1/memories`
```json
{"agent_id":"uuid","content":"Customer prefers concise replies","namespace":"default","tags":["preference"],"metadata":{"source":"crm"},"importance":0.8}
```

## Search
`POST /api/v1/memories/search`
```json
{"agent_id":"uuid","query":"reply style preference","namespace":"default","limit":8}
```

## RAG retrieve
`POST /api/v1/memories/retrieve` uses the same request and returns ranked context suitable for an agent prompt.

## Lifecycle
- `POST /api/v1/memories/{id}/archive`
- `POST /api/v1/memories/{id}/restore`
- `DELETE /api/v1/memories/{id}`

## Developer operations
- `POST /api/v1/api-keys?application_id=<uuid>&name=Production`
- `GET /api/v1/usage`
- `GET /api/v1/export`

## Health
`GET /health`
