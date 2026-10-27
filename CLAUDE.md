## What this project is

SecureShip is a customer-facing shipment support chatbot. Customers ask questions
about their own parcels and shipments. The backend looks up real data and answers
via an LLM. Each conversation is stored as a transcript in Postgres.

This is a learning project for the AI Literacy Workshop (Weeks 1–4).

## Stack

| Layer     | Tech                                      |
|-----------|-------------------------------------------|
| Backend   | Python / FastAPI                          |
| Frontend  | React + React Query (client via Orval)    |
| Database  | Postgres 16 + pgvector                    |
| LLM       | Ollama (primary) · DIAL (secondary)       |
| Dev env   | Docker Compose                            |

## How to run

# Start the database
docker compose up -d postgres   # runs on port 5432

# Backend (from /backend)
uv run uvicorn app.main:app --reload --port 8000

# Frontend (from /frontend)
npm install
npm run dev        # runs on port 3000

# Regenerate API client after backend schema changes
npx orval

Ollama must be running locally on port 11434.
From inside a Docker container, use host.docker.internal instead of localhost.

Project structure

backend/      FastAPI app, routes, LLM client
frontend/     React app, Orval-generated client in src/api/generated/
docs/         Architecture sketches, concept page, decision log
scripts/      seed_data.py, fixtures/demo-identities.json
corpus/       # for Week 3 retrieval
evals/        # for evaluation scripts

Key settings

- Default model: qwen3:8b
- Temperature: 0.2
- Context window (num_ctx): 8192

Rules for Claude Code

The rule that matters most

Access rules are enforced in code, never only in a prompt.

A customer must never see another customer's data. This is enforced by filtering
queries on the authenticated customer's ID in the backend. Never rely on the
system prompt alone to prevent data leakage.

Other rules

- Do not add authentication scaffolding until asked — keep it out of scope for now.
- Use plan mode before touching multiple files at once.
- Name every file you intend to change in your prompt. Say what not to touch.
- Do not add a retry loop without an upper limit.
- The DIAL allowance is limited — do not use it for bulk testing.
- Run npx orval and commit the output whenever the backend schema changes.
- Always store both sides of a chat turn (user + assistant) in the transcript.