from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


from src.config import AppConfig
from src.services.cta_manager import CtaManager
from src.services.elevenlabs_service import ElevenLabsService
from src.services.gemini_service import GeminiService
from src.services.pexels_service import PexelsService
from src.services.subtitle_service import SubtitleService
from src.utils.logging import setup_logger
from src.video.composer import VideoComposer

STYLES = {"curiosity", "tips", "facts", "top_list"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aprende Aqui - gerador de vídeos virais")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="Gera um vídeo vertical")
    generate.add_argument("--topic", required=True)
    generate.add_argument("--style", choices=sorted(STYLES), required=True)
    generate.add_argument("--length", type=int, default=40)
    generate.add_argument("--cta_variation", choices=["on", "off"], default="on")
    generate.add_argument("--visual_intensity", choices=["low", "medium", "high"], default="medium")
    generate.add_argument("--music", choices=["on", "off"], default="off")
    generate.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def run_generate(args: argparse.Namespace) -> None:
    config = AppConfig.from_env()
    logger = setup_logger()
    random.seed(args.seed)

    run_name = f"{args.style}_{args.topic[:18].replace(' ', '_')}"
    output_dir = config.output_dir / run_name
    output_dir.mkdir(parents=True, exist_ok=True)

    cta = CtaManager(config.cache_dir, seed=args.seed)
    gemini = GeminiService(config.gemini_api_key, seed=args.seed)
    tts = ElevenLabsService(config.elevenlabs_api_key, config.elevenlabs_voice_id)
    pexels = PexelsService(config.pexels_api_key, config.cache_dir)
    subtitles = SubtitleService()
    composer = VideoComposer(seed=args.seed)

    logger.info("Gerando roteiro")
    script = gemini.generate_script(args.topic, args.style, args.length)

    initial_cta = cta.initial(args.style, enabled=args.cta_variation == "on")
    final_cta = script.cta_final or cta.final(enabled=args.cta_variation == "on")

    script.segments[0].text = f"{script.hook} {initial_cta}. {script.segments[0].text}"
    script.segments[-1].text = f"{script.segments[-1].text} {final_cta}."

    logger.info("Gerando áudio de narração")
    _, narration_full, timing_path = tts.synthesize_segments([s.text for s in script.segments], output_dir)
    timings_payload = json.loads(timing_path.read_text(encoding="utf-8"))

    from src.models import Timing  # local import for lean startup

    timings = [Timing(**item) for item in timings_payload]

    logger.info("Buscando assets")
    asset_choices = [pexels.pick_asset(i, segment.keywords) for i, segment in enumerate(script.segments)]

    logger.info("Gerando legendas")
    srt_path, ass_path = subtitles.write(script.segments, timings, output_dir)

    logger.info("Compondo vídeo final")
    final_mp4, metadata_path = composer.compose(
        assets=asset_choices,
        timings=timings,
        narration_path=narration_full,
        subtitles_ass=ass_path,
        output_dir=output_dir,
        visual_intensity=args.visual_intensity,
        music_on=args.music == "on",
        music_path=config.music_default_path,
    )

    report = {
        "title": script.title,
        "topic": args.topic,
        "style": args.style,
        "length_target": args.length,
        "assets": [asset.__dict__ for asset in asset_choices],
        "final_video": str(final_mp4),
        "subtitles_srt": str(srt_path),
        "subtitles_ass": str(ass_path),
        "metadata": str(metadata_path),
        "hashtags": script.hashtags,
        "description": script.description,
    }
    (output_dir / "generation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Concluído em: {final_mp4}")


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.command == "generate":
        run_generate(arguments)
