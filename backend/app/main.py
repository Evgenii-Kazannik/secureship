import os
import re

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="SecureShip")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
TEMPERATURE = 0.2
NUM_CTX = 8192
OLLAMA_TIMEOUT = 60.0
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatReply(BaseModel):
    reply: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatReply)
async def chat(body: ChatRequest) -> ChatReply:
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": body.message}],
                    "stream": False,
                    "options": {"temperature": TEMPERATURE, "num_ctx": NUM_CTX},
                },
            )
            resp.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="LLM unavailable")

    text = _THINK_RE.sub("", resp.json()["message"]["content"]).strip()
    return ChatReply(reply=text)
