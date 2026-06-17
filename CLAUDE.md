# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

### Environment Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Authenticate with Google (creates token.json)
python src/auth_setup.py

# 3. Run ChromaDB (required for RAG)
docker-compose up -d chroma

# 4. Start API server
python src/app/main.py
```

### Development Commands

| Task | Command |
|------|---------|
| **Install deps** | `pip install -r requirements.txt` |
| **Run tests** | `pytest tests/ -v` |
| **Run single test** | `pytest tests/test_api.py::test_health_check -v` |
| **Test with coverage** | `pytest tests/ --cov=src/app --cov-report=html` |
| **Run dev server** | `python src/app/main.py` |
| **Setup Google OAuth** | `python src/auth_setup.py` |
| **Docker (all services)** | `docker-compose up --build` |
| **Docker (dev, API only)** | `docker-compose up app` |

## Project Architecture

**Gemini Research & Docs Writer** — RAG system using Gemini + ChromaDB, with auto-save to Google Docs.

### Core Components

**FastAPI Server** (`src/app/main.py`)
- Receives research/content requests
- Orchestrates RAG workflow
- Serves UI chat interface (`/ui/chat`)
- Health check at `/health`
- Swagger docs at `/docs`
- Daily scheduler (default 07:00) for auto-knowledge updates

**Services** (`src/app/services/`)
- `gemini_service.py` — Gemini API calls for generation/embedding; RAG retrieval using user prompt + knowledge base
- `chroma_service.py` — ChromaDB operations: upsert documents, semantic search, collection stats
- `gdocs_service.py` — Google Docs API: create/append reports; uses OAuth token from `token.json`

**RAG Module** (`src/app/rag/`)
- `chunking.py` — Text splitting into semantic chunks for embedding
- `prompts.py` — System prompts for Gemini (configure temperature, model, grounding)

**Core** (`src/app/core/`)
- `config.py` — Settings from `.env` (Gemini key, API key, Google Drive folder ID, etc.)
- `security.py` — API key auth via header `X-API-Key`

**Models** (`src/app/models/`)
- `schemas.py` — Request/response Pydantic models (ContentRequest, IngestRequest, etc.)

### Data Flow

```
User Request
    → API (with API-Key auth)
    → Gemini generate + ChromaDB semantic search (RAG context)
    → Generate response with grounding
    → Auto-save to Google Docs (if enabled)
    → Return JSON response
```

### Configuration

All settings come from `.env` (see README for setup):
- `GEMINI_API_KEY` — Google AI API key
- `GEMINI_MODEL` — Model selection (default: gemini-2.5-flash-lite)
- `GEMINI_EMBEDDING_MODEL` — Embedding model (default: models/gemini-embedding-001)
- `CHROMA_HOST`, `CHROMA_PORT` — ChromaDB connection
- `GOOGLE_DRIVE_FOLDER_ID` — Where to save docs
- `APP_API_KEY` — Required for API requests (header: `X-API-Key`)

### Dependencies to Watch

- **FastAPI** — Web framework
- **Gemini SDK** (`google-generativeai`) — LLM calls and embeddings
- **ChromaDB** — Vector store for semantic search
- **Google APIs** (`google-auth-oauthlib`, `google-api-python-client`) — OAuth + Docs API
- **APScheduler** — Background job scheduler
- **Pydantic** — Request validation

## File Structure

```
src/app/
├── main.py                 # FastAPI app entry, scheduler setup, routes
├── core/
│   ├── config.py           # Environment-based settings
│   └── security.py         # API key validation
├── models/
│   └── schemas.py          # Request/response models
├── services/
│   ├── gemini_service.py   # RAG generation, embeddings
│   ├── chroma_service.py   # Vector DB operations
│   └── gdocs_service.py    # Google Docs integration
├── rag/
│   ├── chunking.py         # Text segmentation for embeddings
│   └── prompts.py          # LLM system prompts
├── utils/
│   ├── logger.py           # Logging setup
│   ├── formatters.py       # Output formatting
│   └── validators.py       # Input validation
└── templates/              # HTML for /ui/chat

tests/
├── conftest.py             # Pytest fixtures
├── test_api.py             # API endpoint tests
├── test_services.py        # Service logic tests
├── test_rag.py             # RAG pipeline tests
└── test_utils.py           # Utility function tests
```

## Security & Secrets

**Never commit:**
- `.env` (contains API keys)
- `credentials.json` (Google OAuth client ID)
- `token.json` (user auth token)
- `.venv/` (Python virtual env)

All are in `.gitignore` — verify before commits.

For deployment (Cloud Run):
- Store `token.json` content in Secret Manager as `USER_TOKEN_JSON` env var
- API keys must come from secrets, not hardcoded

## Testing

Tests live in `tests/` and use:
- **pytest** — test runner
- **httpx** — async HTTP client for API testing (via `TestClient`)
- **pytest-asyncio** — async test support
- **conftest.py** — shared fixtures (mocked services, test client)

Run tests before commits. Coverage report goes to `htmlcov/index.html`.

## Common Workflows

**Add new API endpoint:**
1. Add Pydantic schema to `models/schemas.py`
2. Implement business logic in relevant service (`services/`)
3. Add route to `main.py` with `@app.post()` etc.
4. Add tests to `tests/test_api.py`
5. Test: `pytest tests/test_api.py -v`

**Add new RAG feature:**
1. Update prompt/chunking in `rag/`
2. Wire into `gemini_service.py`
3. Test with `pytest tests/test_rag.py -v`

**Debug scheduler:**
- Manually trigger daily job: `POST /daily-job` (returns task ID for polling)
- Check logs for errors (APScheduler logs + Gemini errors)

## Notes

- ChromaDB **must run** (docker-compose or external instance) — embedded mode is not used
- Async server: use `await` with Gemini/Chroma calls
- Authentication: All endpoints require `X-API-Key: <APP_API_KEY>` header
- Google Docs: Requires token.json (run `src/auth_setup.py` first)
- Temperature/model tuning: Edit `.env` and restart; changes persist to next run
