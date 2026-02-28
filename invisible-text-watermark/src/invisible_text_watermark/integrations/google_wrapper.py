"""Wrap the Google Generative AI (Gemini) SDK to inject invisible watermarks.

Usage::

    import google.generativeai as genai
    from invisible_text_watermark import Watermarker
    from invisible_text_watermark.integrations.google_wrapper import watermark_gemini

    genai.configure(api_key="...")
    model = genai.GenerativeModel("gemini-2.0-flash")
    wm = Watermarker(issuer_id=1, model_id=300)
    model = watermark_gemini(model, wm)

    resp = model.generate_content("hi")
    print(resp.text)  # contains invisible watermark
"""

from __future__ import annotations

from typing import Any

from ..watermark import Watermarker


class _WatermarkedGenerativeModel:
    """Proxy around a ``GenerativeModel`` that tags generated content."""

    def __init__(self, original: Any, wm: Watermarker):
        self._original = original
        self._wm = wm

    def generate_content(self, *args: Any, **kwargs: Any) -> Any:
        resp = self._original.generate_content(*args, **kwargs)
        return _tag_generate_response(resp, self._wm)

    def __getattr__(self, name: str):
        return getattr(self._original, name)


def _tag_generate_response(resp: Any, wm: Watermarker) -> Any:
    try:
        for candidate in resp.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    part.text = wm.apply(part.text)
    except (AttributeError, TypeError):
        pass
    return resp


def watermark_gemini(model: Any, wm: Watermarker) -> Any:
    """Return a wrapped Gemini model whose responses are watermarked."""
    return _WatermarkedGenerativeModel(model, wm)
