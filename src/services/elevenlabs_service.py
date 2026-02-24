from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from src.models import Timing
from src.utils.retry import retry


class ElevenLabsService:
    def __init__(self, api_key: str | None, voice_id: str):
        self.api_key = api_key
        self.voice_id = voice_id

    @retry(max_attempts=3, exceptions=(urllib.error.URLError, subprocess.CalledProcessError))
    def synthesize_segments(self, texts: list[str], output_dir: Path) -> tuple[list[Path], Path, Path]:
        audio_dir = output_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        segment_files: list[Path] = []

        for idx, text in enumerate(texts, start=1):
            seg_path = audio_dir / f"segment_{idx:02d}.mp3"
            if self.api_key:
                self._elevenlabs_tts(text, seg_path)
            else:
                self._fallback_tone(text, seg_path)
            segment_files.append(seg_path)

        concat_file = audio_dir / "concat.txt"
        concat_file.write_text("\n".join([f"file '{p.name}'" for p in segment_files]), encoding="utf-8")

        full_raw = output_dir / "narration_raw.mp3"
        full_norm = output_dir / "narration_full.mp3"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(full_raw)], cwd=audio_dir, check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-i", str(full_raw), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(full_norm)], check=True, capture_output=True)

        timings = self._build_timing(segment_files)
        timing_path = output_dir / "timing.json"
        timing_path.write_text(json.dumps([t.__dict__ for t in timings], indent=2), encoding="utf-8")
        return segment_files, full_norm, timing_path

    def _elevenlabs_tts(self, text: str, out_path: Path) -> None:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        payload = json.dumps({"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.45, "similarity_boost": 0.8}}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"xi-api-key": self.api_key or "", "Content-Type": "application/json", "Accept": "audio/mpeg"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            out_path.write_bytes(response.read())

    def _fallback_tone(self, text: str, out_path: Path) -> None:
        seconds = max(1.8, len(text.split()) * 0.38)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=220:duration={seconds}", "-af", "volume=0.03", str(out_path)], check=True, capture_output=True)

    def _build_timing(self, segment_files: list[Path]) -> list[Timing]:
        timings: list[Timing] = []
        current = 0.0
        for idx, seg in enumerate(segment_files):
            probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(seg)], check=True, capture_output=True, text=True)
            duration = float(probe.stdout.strip())
            timings.append(Timing(segment_index=idx, start=current, end=current + duration, duration=duration))
            current += duration
        return timings
