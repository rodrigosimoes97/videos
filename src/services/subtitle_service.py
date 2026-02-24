from __future__ import annotations

from pathlib import Path

from src.models import Segment, Timing


def _fmt_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_ass(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


class SubtitleService:
    def write(self, segments: list[Segment], timings: list[Timing], out_dir: Path) -> tuple[Path, Path]:
        srt_path = out_dir / "subtitles.srt"
        ass_path = out_dir / "subtitles.ass"

        srt_lines = []
        for i, (segment, timing) in enumerate(zip(segments, timings), start=1):
            srt_lines.extend([str(i), f"{_fmt_srt(timing.start)} --> {_fmt_srt(timing.end)}", segment.text, ""])
        srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Montserrat,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,1,2,70,70,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for idx, (segment, timing) in enumerate(zip(segments, timings)):
            text = segment.text
            for word in segment.emphasis_words:
                if word in text:
                    text = text.replace(word, f"{{\\c&H0000FFFF&}}{word}{{\\c&H00FFFFFF&}}", 1)
            align_tag = "{\\an2}" if idx % 3 else "{\\an8}"
            events.append(
                f"Dialogue: 0,{_fmt_ass(timing.start)},{_fmt_ass(timing.end)},Main,,0,0,0,,{align_tag}{text}"
            )
        ass_path.write_text(header + "\n".join(events), encoding="utf-8")
        return srt_path, ass_path
