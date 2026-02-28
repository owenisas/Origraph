from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TagConfig:
    """Zero-width character mapping and insertion behaviour."""

    repeat_interval_tokens: int = 160
    zero_char: str = "\u200b"   # ZWSP
    one_char: str = "\u200c"    # ZWNJ
    start_char: str = "\u2063"  # INVISIBLE SEPARATOR
    end_char: str = "\u2064"    # INVISIBLE PLUS


@dataclass(slots=True)
class WatermarkConfig:
    schema_version: int = 1
    issuer_id: int = 1
    active_key_id: int = 1
    model_id: int = 0
    model_version_id: int = 0
    tag: TagConfig = field(default_factory=TagConfig)
