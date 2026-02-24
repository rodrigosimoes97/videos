from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path

from src.models import AssetChoice, Timing


class VideoComposer:
    def __init__(self, seed: int | None = None):
        self.random = random.Random(seed)

    def compose(
        self,
        assets: list[AssetChoice],
        timings: list[Timing],
        narration_path: Path,
        subtitles_ass: Path,
        output_dir: Path,
        visual_intensity: str,
        music_on: bool,
        music_path: Path | None,
    ) -> tuple[Path, Path]:
        scenes_dir = output_dir / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        scene_files: list[Path] = []

        for asset, timing in zip(assets, timings):
            out = scenes_dir / f"scene_{asset.segment_index:02d}.mp4"
            zoom_to = {"low": 1.04, "medium": 1.06, "high": 1.08}.get(visual_intensity, 1.06)
            direction = 1 if asset.segment_index % 2 else -1
            zoom_expr = f"if(lte(on,1),1,zoom+0.0008*{direction})"
            base = ["-stream_loop", "-1", "-i", asset.path] if asset.media_type == "video" else ["-loop", "1", "-i", asset.path]
            vf = (
                f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                f"zoompan=z='min(max({zoom_expr},1),{zoom_to})':d=1:s=1080x1920:fps=30"
            )
            if asset.segment_index % 4 == 0:
                vf += ",eq=brightness=0.02"
            subprocess.run(
                ["ffmpeg", "-y", *base, "-t", f"{timing.duration}", "-vf", vf, "-an", str(out)],
                check=True,
                capture_output=True,
            )
            scene_files.append(out)

        concat_list = scenes_dir / "concat.txt"
        concat_list.write_text("\n".join(f"file '{f.name}'" for f in scene_files), encoding="utf-8")
        visual_mp4 = output_dir / "visual_only.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(visual_mp4)],
            cwd=scenes_dir,
            check=True,
            capture_output=True,
        )

        final_path = output_dir / "final.mp4"
        mix_cmd = ["ffmpeg", "-y", "-i", str(visual_mp4), "-i", str(narration_path)]
        if music_on and music_path and music_path.exists():
            mix_cmd.extend(["-stream_loop", "-1", "-i", str(music_path)])
            mix_filter = "[2:a]volume=0.08[bg];[bg][1:a]sidechaincompress=threshold=0.08:ratio=8[ducked]"
            mix_cmd.extend(["-filter_complex", mix_filter, "-map", "0:v", "-map", "[ducked]"])
        else:
            mix_cmd.extend(["-map", "0:v", "-map", "1:a"])

        mix_cmd.extend([
            "-vf",
            f"ass={subtitles_ass}",
            "-shortest",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            str(final_path),
        ])
        subprocess.run(mix_cmd, check=True, capture_output=True)

        metadata = output_dir / "metadata.json"
        metadata.write_text(
            json.dumps(
                {
                    "video": str(final_path),
                    "scene_count": len(scene_files),
                    "visual_intensity": visual_intensity,
                    "music_on": music_on,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return final_path, metadata
