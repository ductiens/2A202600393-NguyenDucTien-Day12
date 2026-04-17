# Vinmec AI API

Backend-only project for Vinmec booking assistant.

## Project structure

```text
your-repo/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── rate_limiter.py
│   └── cost_guard.py
├── utils/
│   └── mock_llm.py
├── tools/
├── data/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .dockerignore
├── railway.toml
└── README.md
```

## Local setup

1. Create env file:
```bash
cp .env.example .env
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run API:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Test:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Tôi bị đau đầu\",\"history\":[]}"
```

## Docker

Run with Docker Compose:

```bash
docker compose up --build
```

## Notes

- If `OPENAI_API_KEY` is missing, set `USE_MOCK_LLM=true` to run with mock response.
- Authentication is optional via `AUTH_ENABLED=true` and `x-api-key` header.
- Rate limiting and request-size cost guard are enabled by default.

