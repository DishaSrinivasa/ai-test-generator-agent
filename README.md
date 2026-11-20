# AI Test Generator Agent

Generates pytest suites from an OpenAPI spec using RAG + Ollama, runs a fix loop, and gates approval before CI.

## Stack
Python · FastAPI · pytest · ChromaDB · Ollama · Docker · GitHub Actions

## Quick start

### 1. Install Ollama and pull model
```bash
# Install from https://ollama.com
ollama pull llama3.2
```

### 2. Install dependencies
```bash
pip install -e .
```

### 3. Start the sample API + review server
```bash
uvicorn sample_api.main:app --port 8000 &
uvicorn agent.review.server:app --port 9000 &
```

### 4. Run the agent
```bash
python -m agent.cli
```

### 5. Review and approve tests
```bash
# View pending tests
curl http://localhost:9000/pending

# Approve
curl -X POST http://localhost:9000/pending/pizza_api_tests/decision \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

### 6. Run with Docker
```bash
docker compose up sample-api review-server
docker compose --profile run-agent up agent
```

## How it works
1. **Ingest** — fetches `/openapi.json`, chunks by endpoint, stores in ChromaDB
2. **Generate** — Ollama (llama3.2) + RAG context → pytest functions
3. **Run-and-fix** — pytest in subprocess, failures fed back to Ollama (up to 3 iterations)
4. **Review gate** — POST to review server; human approves/rejects
5. **CI** — GitHub Actions runs approved tests on every push
