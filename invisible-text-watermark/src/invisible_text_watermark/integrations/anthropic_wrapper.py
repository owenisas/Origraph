"""Wrap the Anthropic Python SDK to inject invisible watermarks into responses.

Usage::

    from anthropic import Anthropic
    from invisible_text_watermark import Watermarker
    from invisible_text_watermark.integrations.anthropic_wrapper import watermark_anthropic

    client = Anthropic()
    wm = Watermarker(issuer_id=1, model_id=200)
    client = watermark_anthropic(client, wm)

    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[{"role": "user", "content": "hi"}],
    )
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anthropic import Anthropic

from ..watermark import Watermarker


class _WatermarkedMessages:
    """Proxy around ``client.messages`` that injects tags."""

    def __init__(self, original, wm: Watermarker):
        self._original = original
        self._wm = wm

    def create(self, **kwargs):
        resp = self._original.create(**kwargs)
        return _tag_messages_response(resp, self._wm)

    def __getattr__(self, name: str):
        return getattr(self._original, name)


def _tag_messages_response(resp, wm: Watermarker):
    for block in resp.content:
        if hasattr(block, "text") and block.text:
            block.text = wm.apply(block.text)
    return resp


def watermark_anthropic(client: "Anthropic", wm: Watermarker) -> "Anthropic":
    """Return a wrapped Anthropic client whose message responses are watermarked."""
    wrapped = copy.copy(client)
    wrapped.messages = _WatermarkedMessages(client.messages, wm)  # type: ignore[attr-defined]
    return wrapped
