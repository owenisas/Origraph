"""Wrap the OpenAI Python SDK to inject invisible watermarks into responses.

Usage::

    from openai import OpenAI
    from invisible_text_watermark import Watermarker
    from invisible_text_watermark.integrations.openai_wrapper import watermark_openai

    client = OpenAI()
    wm = Watermarker(issuer_id=1, model_id=100)
    client = watermark_openai(client, wm)

    # Every chat completion now carries an invisible watermark.
    resp = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": "hi"}]
    )
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

from ..watermark import Watermarker


class _WatermarkedCompletions:
    """Proxy around ``client.chat.completions`` that injects tags."""

    def __init__(self, original, wm: Watermarker):
        self._original = original
        self._wm = wm

    def create(self, **kwargs):
        resp = self._original.create(**kwargs)
        return _tag_chat_response(resp, self._wm)

    def __getattr__(self, name: str):
        return getattr(self._original, name)


class _WatermarkedChat:
    """Proxy around ``client.chat`` exposing wrapped completions."""

    def __init__(self, original, wm: Watermarker):
        self._original = original
        self.completions = _WatermarkedCompletions(original.completions, wm)

    def __getattr__(self, name: str):
        return getattr(self._original, name)


def _tag_chat_response(resp, wm: Watermarker):
    for choice in resp.choices:
        if choice.message and choice.message.content:
            choice.message.content = wm.apply(choice.message.content)
    return resp


def watermark_openai(client: "OpenAI", wm: Watermarker) -> "OpenAI":
    """Return a wrapped OpenAI client whose chat responses are watermarked.

    The original client object is not mutated.
    """
    wrapped = copy.copy(client)
    wrapped.chat = _WatermarkedChat(client.chat, wm)  # type: ignore[attr-defined]
    return wrapped
