# Vision AI Extractor — Backend

FastAPI API for restaurant menu extraction (OCR + LLM), PostgreSQL, JWT auth.

## Stack

- FastAPI, SQLAlchemy, Alembic
- PaddleOCR
- Ollama (OpenAI-compatible `/v1`)

## Develop

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# set DATABASE_URL, SECRET_KEY, LLM_* in .env
uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
docker build -t vidahedayati/vision-ai-backend .
```

Companion frontend: https://github.com/vidaHd/vision-ai-frontend
