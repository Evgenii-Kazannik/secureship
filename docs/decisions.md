1. Runtime: Ollama (primary)
   Ollama is local, free, and works offline — no cost risk while iterating.
   Rejected: DIAL as primary — limited USD allowance is too easy to burn during bulk testing.

2. Transport: HTTP
   A request/reply chatbot needs nothing more. HTTP is debuggable with curl and the browser network tab.
   Rejected: WebSockets — streaming and typing indicators add complexity with no real benefit this week.

3. Temperature 0.2, context window 8192
   Low temperature keeps answers factual and consistent for shipment queries.
   8192 tokens fits ~15 turns comfortably without hitting memory limits on a laptop.
   Rejected: higher temperature — creative variation is a bug, not a feature, for logistics answers.

4. System prompt
   Include: who the assistant is, what it may answer, the grounding sentence.
   Keep out: customer data, any access logic (that lives in code), internal field names.
   Rejected: putting access rules in the prompt — a jailbreak removes them; code does not.

5. What to store per turn
   role, content, timestamp, session_id.
   without timestamp, you cannot tell which turn caused a bad answer when debugging.

6. Seed data safety
   Fixed random seed for reproducibility.
   Upsert on a natural key (email for customers, tracking number for shipments) so running twice is safe.

7. Stack and session ID
   Keep the default stack (FastAPI + React/Vite + Postgres + Docker Compose).
   Store session ID in localStorage — survives page refresh, which matters for demo continuity.

8. TestClient / httpx2 (suppressed deprecation)
   Starlette added a deprecation warning for using httpx with TestClient, recommending httpx2 instead.
   httpx2 is not yet published on PyPI so the migration cannot happen now.
   The warning is suppressed in pyproject.toml [tool.pytest.ini_options].
   Raise when: httpx2 appears on PyPI and respx publishes a compatible release.

9. Auth0 token storage (Week 4, not yet built)
   Store Auth0 tokens in memory or httpOnly cookies — not localStorage.
   localStorage is readable by any JS on the page; an XSS vulnerability would expose the token.
   httpOnly cookies are invisible to JS and survive a refresh; in-memory tokens are safe but lost on refresh.
   Decision: revisit when implementing Week 4, but localStorage is ruled out.