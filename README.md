# Brainbay

A self-contained chatbot application that runs a conversational AI model locally. It is composed of two services — a Python backend and a React frontend — orchestrated with Docker Compose.

---

## Architecture

```
brainbay/
├── chatbot_service/     # Python FastAPI backend
│   ├── api.py           # HTTP route definitions
│   ├── chat.py          # Entrypoint (init DB, expose `app`)
│   ├── db.py            # SQLite engine setup
│   ├── models.py        # SQLModel ORM models
│   ├── services.py      # AI inference + persistence logic
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   └── tests/
│       ├── conftest.py      
│       ├── test_services.py 
│       └── test_api.py      
├── frontend_service/    # React frontend (Create React App)
│   ├── src/
│   │   ├── api.js                  # All backend fetch calls, configurable base URL
│   │   ├── App.js                  # Root component, state and session logic
│   │   ├── App.css                 # WhatsApp-inspired styling
│   │   └── components/
│   │       ├── Header.jsx          # App bar with active-session delete button
│   │       ├── Sidebar.jsx         # Session list and new-session button
│   │       ├── ChatWindow.jsx      # Message bubbles and scroll-to-bottom
│   │       └── MessageInput.jsx    # Text input and send button
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

### Services

| Service | Stack | Port |
|---|---|---|
| `chatbot` | FastAPI + Uvicorn + PyTorch | 5000 |
| `frontend` | React 18 (CRA) | 3000 |

## Running the Application

### Prerequisites

- Docker and Docker Compose

### Start

```bash
docker compose up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:5000](http://localhost:5000)

Both services mount their source directory as a volume, so code changes are reflected without rebuilding the image.

> **Note:** On first startup the chatbot service will download the SmolLM2-1.7B-Instruct model (~3.5 GB) from Hugging Face. Subsequent starts use the cached model.

### Local development (backend only, without Docker)

```bash
cd chatbot_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn chat:app --host 0.0.0.0 --port 5000 --reload
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sessions` | List all session IDs |
| `GET` | `/sessions/{id}/messages` | Retrieve message history for a session |
| `DELETE` | `/sessions/{id}` | Delete a session and all its messages |
| `POST` | `/chat` | Send a message and receive a bot reply |

### POST /chat

```json
// Request
{ "prompt": "Hello!", "session_id": "abc123" }

// Response
{ "response": "Hi there!", "session_id": "abc123" }
```

---

## Key Design Decisions

### 1. SmolLM2-1.7B-Instruct for local inference

The backend uses HuggingFace's `SmolLM2-1.7B-Instruct` model loaded via the Transformers `pipeline` API. This was chosen to keep the entire stack self-hosted — no external API keys or network calls are required to generate responses.

The initial implementation used `microsoft/DialoGPT-small`. In practice the response quality was too poor to be useful — answers were short, repetitive, and frequently off-topic even for simple greetings. `SmolLM2-1.7B-Instruct` was chosen as a replacement: it is still small enough to run locally on a CPU, but as an instruction-tuned model it understands the standard `{"role", "content"}` chat format and produces significantly more coherent, contextually aware replies. `device_map="auto"` makes the pipeline automatically use a GPU if available, falling back to CPU otherwise.

**Trade-off:** The model requires ~3.5 GB of disk for weights and ~4 GB of RAM/VRAM at runtime. A CPU-only machine will produce responses significantly slower than a GPU-equipped one.

### 2. Transformers pipeline API + message-dict history

The inference layer uses `pipeline("text-generation")` instead of manually managing tokenizer and model objects. Conversation history is stored as a plain list of `{"role": "user"|"assistant", "content": "..."}` dicts per session — the format the pipeline expects natively.

This replaces the previous approach of concatenating raw token tensors by hand, which was error-prone and caused responses to repeat after the first turn. On service restart, history is lazily rebuilt from the database the first time a session receives a new message.

### 3. SQLite + SQLModel for persistence

Chat messages are stored in a local `chatbot.db` SQLite file. SQLModel was chosen as the ORM because it unifies SQLAlchemy table definitions with Pydantic-style field declarations in a single class, reducing boilerplate.

SQLite requires no separate database service, which keeps the Docker Compose setup simple (two containers instead of three). The trade-off is that the database is not suitable for multi-instance horizontal scaling.

### 4. Session-based conversations

Each conversation is identified by a UUID generated client-side (`crypto.randomUUID()`). Sessions are not tied to any user account, which keeps the system stateless from an authentication perspective. The session ID is passed on every request and stored alongside each message in the database.

### 5. FastAPI as the web framework

FastAPI provides automatic request parsing, async support, and an auto-generated OpenAPI spec at `/docs`. It was chosen over Flask for its modern design and native Pydantic integration, which aligns with SQLModel.

### 6. React (Create React App) for the frontend

The frontend is a single-page React application. CRA was used for its zero-configuration setup. The UI follows a WhatsApp-inspired layout (green header, bubble messages, session sidebar) implemented entirely with plain CSS — no UI library dependency.

The source is split into four focused components (`Header`, `Sidebar`, `ChatWindow`, `MessageInput`) with all backend communication isolated in `src/api.js`. The backend URL is read from the `REACT_APP_API_URL` environment variable, falling back to `http://localhost:5000` for local development. To point the frontend at a different backend, create a `.env` file in `frontend_service/`:

```
REACT_APP_API_URL=https://your-backend-host
```

Both services must be reachable from the browser. Without a reverse proxy this means running them on the same host, which is the default Docker Compose setup.

### 7. CORS open policy

The backend currently allows all origins (`allow_origins=["*"]`). This is intentional for local development convenience. In a production environment this should be restricted to the known frontend origin.

---

## Data Model

```
ChatMessage
├── id          INTEGER  (primary key, auto-increment)
├── session_id  TEXT
├── sender      TEXT     ("user" | "bot")
├── text        TEXT
└── timestamp   DATETIME (UTC, set on insert)
```

---

## Known Limitations

- The model requires ~4 GB of RAM/VRAM. On CPU-only machines responses can be slow (10–30 seconds per reply depending on hardware).
- There is no authentication or rate limiting on any endpoint.
- The SQLite database file (`chatbot.db`) is not excluded from git by the current `.gitignore`, so it may be accidentally committed with conversation data.

---

## Future Improvements

### Authentication & user accounts
Add a proper user registration and login system (e.g. JWT-based auth). Sessions would be tied to user accounts instead of anonymous UUIDs, enabling persistent history across devices and preventing unauthorized access to other users' conversations.

### Rate limiting
Introduce per-user or per-IP rate limiting on the `/chat` endpoint to prevent abuse and protect the inference server from being overloaded.

### Multilingual support
Switch to a multilingual instruction-tuned model (e.g. `Qwen2.5-1.5B-Instruct`, which supports 29 languages) or add automatic language detection to route prompts to the appropriate model. The frontend would also need locale-aware UI strings.

### Session naming
Allow users to give sessions a human-readable name instead of displaying the raw UUID in the sidebar. The name could be auto-generated from the first message or set manually.

### Database migration to external
Replace SQLite with an external DB (like PostgresSQL) for production deployments. This would support multiple concurrent backend instances and provide proper connection pooling.

