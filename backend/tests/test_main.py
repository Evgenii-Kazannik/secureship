from unittest.mock import AsyncMock, patch

import httpx
import respx
from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import OLLAMA_HOST, app

OLLAMA_CHAT = f"{OLLAMA_HOST}/api/chat"


def ollama_ok(content: str) -> httpx.Response:
    return httpx.Response(200, json={"message": {"role": "assistant", "content": content}})


def mock_db(state: str = "anonymous", transcript: list | None = None):
    """Override get_connection with an async mock that returns an empty session."""
    conn = AsyncMock()

    async def _get_or_create(c, session_id):
        return state, transcript or []

    async def _save_turns(c, session_id, user_msg, reply):
        pass

    patcher_session = patch("app.main.get_or_create_session", side_effect=_get_or_create)
    patcher_save = patch("app.main.save_turns", side_effect=_save_turns)

    async def _override():
        yield conn

    app.dependency_overrides[get_connection] = _override
    return patcher_session, patcher_save


def setup_db(state="anonymous", transcript=None):
    p1, p2 = mock_db(state, transcript)
    p1.start()
    p2.start()
    return p1, p2


def teardown_db(p1, p2):
    p1.stop()
    p2.stop()
    app.dependency_overrides.clear()


client = TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_returns_ok(self):
        assert client.get("/health").json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Chat — happy path
# ---------------------------------------------------------------------------


class TestChat:
    def setup_method(self):
        self.p1, self.p2 = setup_db()

    def teardown_method(self):
        teardown_db(self.p1, self.p2)

    @respx.mock
    def test_returns_reply(self):
        respx.post(OLLAMA_CHAT).mock(return_value=ollama_ok("Hello"))
        resp = client.post("/chat", json={"session_id": "s1", "message": "hi"})
        assert resp.status_code == 200
        assert resp.json()["reply"] == "Hello"

    @respx.mock
    def test_strips_thinking_tags(self):
        respx.post(OLLAMA_CHAT).mock(
            return_value=ollama_ok("<think>private reasoning</think>The answer is 42")
        )
        resp = client.post("/chat", json={"session_id": "s1", "message": "what is 42?"})
        body = resp.json()["reply"]
        assert "<think>" not in body
        assert "private reasoning" not in body
        assert body == "The answer is 42"

    @respx.mock
    def test_strips_multiline_thinking_tags(self):
        respx.post(OLLAMA_CHAT).mock(
            return_value=ollama_ok("<think>\nstep 1\nstep 2\n</think>\nResult")
        )
        body = client.post("/chat", json={"session_id": "s1", "message": "calc"}).json()["reply"]
        assert "step 1" not in body
        assert body == "Result"

    @respx.mock
    def test_history_is_sent_to_ollama(self):
        """Full conversation history must be forwarded so the model has context."""
        respx.post(OLLAMA_CHAT).mock(return_value=ollama_ok("Got it"))
        teardown_db(self.p1, self.p2)
        p1, p2 = setup_db(
            transcript=[
                {"role": "user", "content": "first"},
                {"role": "assistant", "content": "reply"},
            ]
        )
        client.post("/chat", json={"session_id": "s1", "message": "second"})
        payload = respx.calls.last.request
        import json

        messages = json.loads(payload.content)["messages"]
        roles = [m["role"] for m in messages]
        assert roles == ["system", "user", "assistant", "user"]
        teardown_db(p1, p2)
        self.p1, self.p2 = setup_db()


# ---------------------------------------------------------------------------
# Chat — error handling
# ---------------------------------------------------------------------------


class TestChatErrors:
    def setup_method(self):
        self.p1, self.p2 = setup_db()

    def teardown_method(self):
        teardown_db(self.p1, self.p2)

    @respx.mock
    def test_503_when_ollama_unreachable(self):
        respx.post(OLLAMA_CHAT).mock(side_effect=httpx.ConnectError("refused"))
        resp = client.post("/chat", json={"session_id": "s1", "message": "hi"})
        assert resp.status_code == 503

    @respx.mock
    def test_503_detail_does_not_leak_internal_url(self):
        """Error responses must never expose internal hostnames or stack traces."""
        respx.post(OLLAMA_CHAT).mock(side_effect=httpx.ConnectError("refused"))
        detail = client.post("/chat", json={"session_id": "s1", "message": "hi"}).text
        assert "localhost" not in detail
        assert "11434" not in detail
        assert "Traceback" not in detail

    def test_rejects_missing_session_id(self):
        assert client.post("/chat", json={"message": "hi"}).status_code == 422

    def test_rejects_missing_message(self):
        assert client.post("/chat", json={"session_id": "s1"}).status_code == 422

    def test_rejects_empty_body(self):
        assert client.post("/chat", json={}).status_code == 422

    def test_rejects_non_json(self):
        resp = client.post(
            "/chat", content=b"not json", headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# CORS — only the configured origin is reflected
# ---------------------------------------------------------------------------


class TestCORS:
    def test_allowed_origin_reflected(self):
        resp = client.options(
            "/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_unknown_origin_not_reflected(self):
        """A foreign origin must never be reflected back — open CORS is a security bug."""
        resp = client.get(
            "/health",
            headers={"Origin": "http://attacker.example.com"},
        )
        assert resp.headers.get("access-control-allow-origin") != "http://attacker.example.com"
