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

SYSTEM_PROMPT = """You are SecureShip, a customer support assistant for a parcel delivery service.

What you may discuss:
- Shipping policy, delivery timelines, and carrier information — for any visitor,
  verified or not.
- A verified customer's own shipments, packages, and delivery status — only after
  identity has been confirmed by the backend.

What you must not do:
- Reveal whether a tracking number exists before a customer is verified.
- Confirm or deny whether a name appears in the system.
- Invent tracking numbers, delivery dates, addresses, or policy details.

When you do not know something, say so clearly and briefly. Policy answers come from
documents the backend will supply; cite the source when one is provided. If no document
is provided, say you do not have that information rather than guessing."""


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
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": body.message},
                    ],
                    "stream": False,
                    "options": {"temperature": TEMPERATURE, "num_ctx": NUM_CTX},
                },
            )
            resp.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="LLM unavailable")

    text = _THINK_RE.sub("", resp.json()["message"]["content"]).strip()
    return ChatReply(reply=text)
