"""High-level watermark and detect API.

Usage::

    from invisible_text_watermark import Watermarker

    wm = Watermarker(issuer_id=1, model_id=42)
    tagged = wm.apply("Hello, world!")
    result = wm.detect(tagged)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .config import TagConfig, WatermarkConfig
from .payload import PackedMetadata, pack_payload, unpack_payload
from .zero_width import (
    TagInjector,
    decode_tags_from_text,
    encode_payload_to_tag,
)


@dataclass(slots=True)
class DetectResult:
    watermarked: bool
    tag_count: int
    valid_count: int
    invalid_count: int
    payloads: list[dict[str, Any]]


class Watermarker:
    """Stateless invisible-text watermarker.

    Parameters
    ----------
    schema_version : int
        Protocol version (default 1).
    issuer_id : int
        Identifies the organisation / deployment (12-bit, 0-4095).
    model_id : int
        Identifies the model (16-bit).
    model_version_id : int
        Identifies the model revision (16-bit).
    key_id : int
        Key rotation identifier (8-bit).
    repeat_interval_tokens : int
        Approximate whitespace-delimited token count between tag insertions.
        Lower values = more redundant copies.
    tag_config : TagConfig | None
        Override zero-width character mapping if needed.
    """

    def __init__(
        self,
        *,
        schema_version: int = 1,
        issuer_id: int = 1,
        model_id: int = 0,
        model_version_id: int = 0,
        key_id: int = 1,
        repeat_interval_tokens: int = 160,
        tag_config: TagConfig | None = None,
    ):
        self.cfg = WatermarkConfig(
            schema_version=schema_version,
            issuer_id=issuer_id,
            active_key_id=key_id,
            model_id=model_id,
            model_version_id=model_version_id,
            tag=tag_config or TagConfig(repeat_interval_tokens=repeat_interval_tokens),
        )
        self._payload64 = pack_payload(
            PackedMetadata(
                schema_version=self.cfg.schema_version,
                issuer_id=self.cfg.issuer_id,
                model_id=self.cfg.model_id,
                model_version_id=self.cfg.model_version_id,
                key_id=self.cfg.active_key_id,
            )
        )
        self._tag = encode_payload_to_tag(self._payload64, self.cfg.tag)

    def apply(self, text: str) -> str:
        """Embed invisible watermark tag(s) into *text* and return the result."""
        injector = TagInjector(self._tag, self.cfg.tag.repeat_interval_tokens)
        return injector.inject_delta(text, finalize=True)

    def detect(self, text: str) -> DetectResult:
        """Scan *text* for watermark tags and return structured results."""
        raw_payloads = decode_tags_from_text(text, self.cfg.tag)
        payloads: list[dict[str, Any]] = []
        valid_count = 0
        invalid_count = 0

        for raw in raw_payloads:
            meta, valid = unpack_payload(raw)
            entry = asdict(meta)
            entry["crc_valid"] = valid
            entry["raw_payload_hex"] = f"0x{raw:016x}"
            payloads.append(entry)
            if valid:
                valid_count += 1
            else:
                invalid_count += 1

        return DetectResult(
            watermarked=valid_count > 0,
            tag_count=len(raw_payloads),
            valid_count=valid_count,
            invalid_count=invalid_count,
            payloads=payloads,
        )

    @staticmethod
    def strip(text: str, tag_config: TagConfig | None = None) -> str:
        """Remove all watermark tags from *text*."""
        cfg = tag_config or TagConfig()
        import re

        start = re.escape(cfg.start_char)
        end = re.escape(cfg.end_char)
        zero = re.escape(cfg.zero_char)
        one = re.escape(cfg.one_char)
        pattern = re.compile(f"{start}[{zero}{one}]{{64}}{end}")
        return pattern.sub("", text)
