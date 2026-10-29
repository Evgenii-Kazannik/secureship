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
- Do not add a retry loop without an upper limit.
- The DIAL allowance is limited — do not use it for bulk testing.
- Run npx orval and commit the output whenever the backend schema changes.
- Always store both sides of a chat turn (user + assistant) in the transcript.

## Security and privacy rules

### Credentials and secrets

- Never hardcode API keys, DIAL keys, database passwords, or session secrets in
  source code, comments, or commit messages.
- All secrets belong in `.env` (gitignored). Keep `.env.example` committed with
  placeholder values so the required keys are visible without exposing real ones.
- `VITE_` environment variables are compiled into the browser bundle and visible
  in page source. Never put a secret there — only public URLs and non-sensitive
  feature flags.
- If a secret is accidentally committed, treat it as compromised immediately:
  rotate it before rewriting history.

### PII (Personally Identifiable Information)

This project stores synthetic-but-realistic customer data: names, addresses,
phone numbers, and tracking numbers. Treat every field as real PII in all code.

- Never log PII. Logging calls, exception payloads, and structured log fields
  must not contain names, addresses, phone numbers, or tracking numbers.
- Never include PII in error messages returned to clients. "We couldn't verify
  that." is the required copy. "No customer found for <name>" leaks record
  existence to an attacker.
- Never surface one customer's PII to another session regardless of what the
  model or user requests. This is the gating rule above, restated for logging.

### Dependency security

Before adding or upgrading a frontend dependency, run `npm audit` in `frontend/`.
Before adding a backend dependency, run `uv run pip-audit` in `backend/`.
A clean audit is required before committing the change.

If a vulnerability exists in a dependency this project uses:
- Fix it if a non-breaking upgrade is available.
- If only a breaking upgrade is available, take it and document the migration
  rationale in `docs/decisions.md`.
- If no fix exists yet (upstream-only), document the CVE, affected component,
  risk in this context, and any available mitigations in `docs/decisions.md`.
  Do not proceed as if the issue does not exist.

### Week 4 auth reminder

When Auth0 work begins, read decision 8 in `docs/decisions.md` before writing
any token storage code. `localStorage` is ruled out.