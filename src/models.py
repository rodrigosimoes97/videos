from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Segment:
    text: str
    keywords: list[str]
    emphasis_words: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Script:
    title: str
    hook: str
    style: str
    segments: list[Segment]
    hashtags: list[str]
    description: str
    cta_final: str | None
    safety_flags: dict[str, Any]


@dataclass(slots=True)
class Timing:
    segment_index: int
    start: float
    end: float
    duration: float


@dataclass(slots=True)
class AssetChoice:
    segment_index: int
    keyword: str
    media_type: str
    path: str
    source_url: str | None
