"""MiniMax API + Invisible Watermark test UI (FastAPI)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
import anthropic
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "invisible-text-watermark" / "src"))
from invisible_text_watermark import Watermarker, DetectResult

load_dotenv()

app = FastAPI(title="MiniMax Watermark Lab")

API_KEY = os.getenv("MINIMAX_API_KEY", "")
BASE_URL = "https://api.minimax.io/anthropic"

MODELS = [
    "MiniMax-M2.5",
    "MiniMax-M2.5-highspeed",
    "MiniMax-M2.1",
    "MiniMax-M2.1-highspeed",
    "MiniMax-M2",
]

STATIC_DIR = Path(__file__).resolve().parent / "static"


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)


def _get_watermarker(params: dict) -> Watermarker:
    return Watermarker(
        issuer_id=params.get("issuer_id", 1),
        model_id=params.get("model_id", 0),
        model_version_id=params.get("model_version_id", 0),
        key_id=params.get("key_id", 1),
        repeat_interval_tokens=params.get("repeat_interval_tokens", 160),
    )


# -- Request / response models -----------------------------------------------

class WmParams(BaseModel):
    issuer_id: int = 1
    model_id: int = 0
    model_version_id: int = 0
    key_id: int = 1
    repeat_interval_tokens: int = 160


class ChatRequest(BaseModel):
    model: str = "MiniMax-M2.1"
    messages: list[dict[str, Any]] = []
    system: str = "You are a helpful assistant."
    watermark: bool = True
    wm_params: WmParams = Field(default_factory=WmParams)
    stream: bool = False
    max_tokens: int = 2048
    temperature: float = 0.7


class TextRequest(BaseModel):
    text: str = ""
    wm_params: WmParams = Field(default_factory=WmParams)


class StripRequest(BaseModel):
    text: str = ""


# -- Routes -------------------------------------------------------------------

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/models")
async def list_models():
    return {"models": MODELS}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    client = _get_client()
    wm = _get_watermarker(req.wm_params.model_dump()) if req.watermark else None

    if req.stream:
        return StreamingResponse(
            _stream_response(client, req, wm),
            media_type="text/event-stream",
        )

    try:
        resp = client.messages.create(
            model=req.model,
            max_tokens=req.max_tokens,
            system=req.system,
            messages=req.messages,
            temperature=req.temperature,
        )
    except anthropic.APIError as e:
        return {"error": str(e)}

    thinking = ""
    text = ""
    for block in resp.content:
        if block.type == "thinking":
            thinking += block.thinking
        elif block.type == "text":
            text += block.text

    raw_text = text
    if wm and text:
        text = wm.apply(text)

    return {
        "thinking": thinking,
        "text": text,
        "raw_text": raw_text,
        "watermarked": wm is not None,
        "model": req.model,
        "usage": {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        },
    }


async def _stream_response(client, req: ChatRequest, wm):
    try:
        stream = client.messages.create(
            model=req.model,
            max_tokens=req.max_tokens,
            system=req.system,
            messages=req.messages,
            temperature=req.temperature,
            stream=True,
        )
    except anthropic.APIError as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        return

    text_buffer = ""
    for chunk in stream:
        if chunk.type == "content_block_delta":
            if hasattr(chunk, "delta") and chunk.delta:
                if chunk.delta.type == "thinking_delta":
                    yield f"data: {json.dumps({'type': 'thinking', 'content': chunk.delta.thinking})}\n\n"
                elif chunk.delta.type == "text_delta":
                    text_buffer += chunk.delta.text
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk.delta.text})}\n\n"
        elif chunk.type == "message_stop":
            if wm and text_buffer:
                watermarked = wm.apply(text_buffer)
                yield f"data: {json.dumps({'type': 'watermarked_full', 'content': watermarked})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@app.post("/api/detect")
async def detect(req: TextRequest):
    wm = _get_watermarker(req.wm_params.model_dump())
    result: DetectResult = wm.detect(req.text)
    return {
        "watermarked": result.watermarked,
        "tag_count": result.tag_count,
        "valid_count": result.valid_count,
        "invalid_count": result.invalid_count,
        "payloads": result.payloads,
    }


@app.post("/api/strip")
async def strip(req: StripRequest):
    cleaned = Watermarker.strip(req.text)
    return {"text": cleaned}


@app.post("/api/apply")
async def apply_watermark(req: TextRequest):
    wm = _get_watermarker(req.wm_params.model_dump())
    watermarked = wm.apply(req.text)
    return {"text": watermarked, "raw_text": req.text}


if __name__ == "__main__":
    if not API_KEY:
        print("WARNING: MINIMAX_API_KEY not set. Set it in .env or environment.")
    uvicorn.run("app:app", host="127.0.0.1", port=5050, reload=True)
