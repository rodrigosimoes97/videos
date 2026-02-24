from __future__ import annotations

import json
from pathlib import Path


class JsonCache:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def read(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, payload: dict) -> None:
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
