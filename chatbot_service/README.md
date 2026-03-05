# chatbot_service

FastAPI backend for Brainbay. Handles chat sessions, message persistence, and local LLM inference via HuggingFace Transformers.

---

## Project Structure

```
chatbot_service/
├── api.py              # FastAPI app and route handlers
├── services.py         # Business logic (generate_response, session management)
├── models.py           # SQLModel ORM model (ChatMessage)
├── db.py               # DB engine and init_db()
├── requirements.txt    # Runtime + test dependencies
├── Dockerfile
├── .dockerignore
└── tests/
    ├── __init__.py
    ├── conftest.py         # Test infrastructure (mocks, fixtures)
    ├── test_services.py    # Unit tests for services.py
    └── test_api.py         # Integration tests for api.py endpoints
```

---

## Running the Service

```bash
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 5000
```

---

## Running the Tests

```bash
cd chatbot_service
pip install -r requirements.txt
pytest tests/ -v
```

Tests are isolated and do not require a GPU, internet access, or a real database file. No model weights are downloaded.

---


## Test Modules

### `tests/test_services.py` — Unit tests

Tests each function in `services.py` in isolation.

| Group | What is tested |
|---|---|
| `save_message` | Returns the saved object with correct fields; DB assigns an `id` |
| `get_messages` | Empty for unknown session; ordered by insertion; scoped to session |
| `get_sessions` | Empty when no messages; returns distinct IDs; no duplicates |
| `delete_session` | Removes messages and session; clears in-memory cache; safe on nonexistent ID; does not affect other sessions |
| `build_history` | Empty list for new session; maps `user`→`user` and `bot`→`assistant`; preserves content and insertion order |
| `generate_response` | Returns pipe output; calls pipe with correct history (user message last); persists both user and bot messages; updates in-memory cache; rebuilds history from DB on cache miss; passes full history on multi-turn; persists all messages across turns |

### `tests/test_api.py` — Integration tests

Tests all HTTP endpoints via FastAPI's `TestClient`. The DB engine and `services.pipe` are replaced by the same test doubles as the unit tests. For `/chat` tests, `api.generate_response` is additionally patched to make responses deterministic without relying on the pipeline mock.

| Endpoint | What is tested |
|---|---|
| `POST /sessions` | Returns a `session_id`; valid UUID format; unique per call |
| `GET /sessions` | Empty list with no data; returns existing session IDs; no duplicates |
| `GET /sessions/{id}/messages` | Empty list for unknown session; returns all messages; correct shape (`sender`, `text`, `timestamp`); insertion order preserved; scoped to session |
| `DELETE /sessions/{id}` | Returns `{"status": "ok", "session_id": "..."}` ; removes messages; removes from sessions list; safe on nonexistent ID; does not affect other sessions |
| `POST /chat` | Returns `{"response": "...", "session_id": "..."}` ; calls `generate_response` with correct args; defaults `session_id` to `"default"`; defaults `prompt` to `""`; returns correct session ID |

---

## Docker

The `tests/` directory is excluded from the Docker image via `.dockerignore`. The production image only contains the service source files needed at runtime.
