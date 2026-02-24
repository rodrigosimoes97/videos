from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from src.models import AssetChoice
from src.utils.cache import JsonCache
from src.utils.retry import retry


class PexelsService:
    def __init__(self, api_key: str | None, cache_dir: Path):
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.asset_dir = cache_dir / "pexels"
        self.asset_dir.mkdir(parents=True, exist_ok=True)
        self.history = JsonCache(cache_dir / "asset_history.json")

    def pick_asset(self, segment_index: int, keywords: list[str]) -> AssetChoice:
        for keyword in keywords:
            cached = self._find_in_cache(keyword)
            if cached:
                return AssetChoice(segment_index, keyword, self._media_type(cached), str(cached), None)
            if self.api_key:
                video = self._search_video(keyword)
                if video:
                    path = self._download(video["url"], keyword)
                    self._remember(path)
                    return AssetChoice(segment_index, keyword, "video", str(path), video["url"])
                image = self._search_image(keyword)
                if image:
                    path = self._download(image["url"], keyword)
                    self._remember(path)
                    return AssetChoice(segment_index, keyword, "image", str(path), image["url"])
        fallback = self._placeholder_video(segment_index)
        return AssetChoice(segment_index, keywords[0], "video", str(fallback), None)

    def _find_in_cache(self, keyword: str) -> Path | None:
        candidates = sorted(self.asset_dir.glob(f"{self._slug(keyword)}_*"))
        if not candidates:
            return None
        payload = self.history.read()
        recent = payload.get("recent_assets", [])[-6:]
        for candidate in candidates:
            if str(candidate) not in recent:
                self._remember(candidate)
                return candidate
        return candidates[0]

    def _remember(self, path: Path) -> None:
        payload = self.history.read()
        recent = payload.get("recent_assets", [])[-6:]
        payload["recent_assets"] = (recent + [str(path)])[-12:]
        self.history.write(payload)

    @retry(max_attempts=3, exceptions=(urllib.error.URLError,))
    def _search_video(self, keyword: str) -> dict | None:
        params = urllib.parse.urlencode({"query": keyword, "per_page": 8, "orientation": "portrait"})
        req = urllib.request.Request(
            f"https://api.pexels.com/videos/search?{params}",
            headers={"Authorization": self.api_key or ""},
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            videos = json.loads(response.read().decode("utf-8")).get("videos", [])
        ranked = []
        for item in videos:
            files = item.get("video_files", [])
            best = next((f for f in files if f.get("height", 0) >= 1080), files[0] if files else None)
            if best:
                score = best.get("height", 0) + (1000 if item.get("duration", 0) >= 4 else 0)
                ranked.append({"url": best["link"], "score": score})
        return sorted(ranked, key=lambda x: x["score"], reverse=True)[0] if ranked else None

    @retry(max_attempts=3, exceptions=(urllib.error.URLError,))
    def _search_image(self, keyword: str) -> dict | None:
        params = urllib.parse.urlencode({"query": keyword, "per_page": 5, "orientation": "portrait"})
        req = urllib.request.Request(
            f"https://api.pexels.com/v1/search?{params}",
            headers={"Authorization": self.api_key or ""},
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            photos = json.loads(response.read().decode("utf-8")).get("photos", [])
        if not photos:
            return None
        src = photos[0]["src"]
        return {"url": src.get("large2x") or src.get("original")}

    def _download(self, url: str, keyword: str) -> Path:
        ext = ".mp4" if ".mp4" in url else ".jpg"
        digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:10]
        path = self.asset_dir / f"{self._slug(keyword)}_{digest}{ext}"
        if path.exists():
            return path
        with urllib.request.urlopen(url, timeout=60) as response:
            path.write_bytes(response.read())
        return path

    def _placeholder_video(self, idx: int) -> Path:
        out = self.asset_dir / f"placeholder_{idx}.mp4"
        if out.exists():
            return out
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30", "-t", "4", str(out)], check=True, capture_output=True)
        return out

    def _slug(self, text: str) -> str:
        return "".join(ch.lower() if ch.isalnum() else "_" for ch in text)[:40]

    def _media_type(self, path: Path) -> str:
        return "video" if path.suffix.lower() in {".mp4", ".mov"} else "image"
