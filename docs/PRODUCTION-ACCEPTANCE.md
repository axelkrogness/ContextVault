# Production acceptance test

The ZIP is not the final proof. After deployment, verify all of the following against the live API and database:

1. `/health` returns 200.
2. `/docs` loads OpenAPI documentation.
3. PostgreSQL reports the `vector` extension installed.
4. Register and login a new user.
5. Create application, agent and namespace.
6. Create, edit, delete, archive and restore memories.
7. Verify metadata, tags, importance and expiration persist after refresh.
8. Verify keyword, semantic/vector and hybrid retrieval.
9. Verify start/end date filtering.
10. Submit a duplicate and verify duplicate handling.
11. Retrieve similar memories.
12. Run retrieval test and evaluation.
13. Generate an API key and ingest a memory externally.
14. Confirm API usage log entries are persisted.
15. Confirm 429 rate-limit behavior.
16. Create a second user; test viewer/editor permissions and privacy blocking.
17. Export memories.
18. Verify analytics and storage counts.
19. Enforce retention and confirm eligible memories archive.
20. Test mobile-width dashboard layout and expected error messages.
21. Confirm “Powered by Codyza” is visible.

Only after these pass should the deployed URL be submitted.
