CREATE EXTENSION IF NOT EXISTS vector;

-- SQLAlchemy creates the cv_* tables on API startup.
-- These idempotent indexes support the most common production access paths.
CREATE INDEX IF NOT EXISTS ix_cv_memories_created_at ON cv_memories (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_cv_memories_agent_archived ON cv_memories (agent_id, archived);
CREATE INDEX IF NOT EXISTS ix_cv_usage_user_created ON cv_api_usage (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_cv_rate_user_created ON cv_rate_limit_events (user_id, created_at DESC);

-- Native vector storage is cv_memories.embedding vector(64).
-- If the tables do not exist yet, start the API once after enabling vector,
-- then re-run the index statements if your database role cannot create them.
