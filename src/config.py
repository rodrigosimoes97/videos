from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    project_root: Path
    output_dir: Path
    cache_dir: Path
    pexels_api_key: str | None
    gemini_api_key: str | None
    elevenlabs_api_key: str | None
    elevenlabs_voice_id: str
    music_default_path: Path | None


    @classmethod
    def from_env(cls) -> "AppConfig":
        root = Path.cwd()
        output = root / "output"
        cache = root / "assets" / "cache"
        output.mkdir(parents=True, exist_ok=True)
        cache.mkdir(parents=True, exist_ok=True)

        music_path = os.getenv("BG_MUSIC_PATH")
        return cls(
            project_root=root,
            output_dir=output,
            cache_dir=cache,
            pexels_api_key=os.getenv("PEXELS_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
            elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
            music_default_path=Path(music_path) if music_path else None,
        )
