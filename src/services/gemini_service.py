from __future__ import annotations

import json
import random
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from src.models import Script, Segment
from src.utils.retry import retry


class GeminiService:
    def __init__(self, api_key: str | None, seed: int | None = None):
        self.api_key = api_key
        self.random = random.Random(seed)

    @retry(max_attempts=3, exceptions=(urllib.error.URLError, ValueError))
    def generate_script(self, topic: str, style: str, length: int) -> Script:
        if not self.api_key:
            return self._fallback_script(topic, style, length)

        endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        prompt = self._build_prompt(topic=topic, style=style, length=length)
        url = f"{endpoint}?key={urllib.parse.quote(self.api_key)}"
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        cleaned = text.replace("```json", "").replace("```", "").strip()
        return self._to_script(json.loads(cleaned))

    def _build_prompt(self, topic: str, style: str, length: int) -> str:
        return f"""
Você é roteirista especialista em vídeos virais verticais para o canal Aprende Aqui (PT-BR).
Retorne APENAS JSON válido (sem markdown), no formato:
{{"title":"...","hook":"...","style":"{style}","segments":[{{"text":"...","keywords":["..."],"emphasis_words":["..."]}}],"hashtags":["#..."],"description":"...","cta_final":"...","safety_flags":{{"medical_claim":false,"financial_claim":false,"harmful":false}}}}
Regras: PT-BR natural, frases curtas, 6-10 segmentos, duração alvo {length}s, evitar repetição.
Tema: {topic}
""".strip()

    def _to_script(self, payload: dict[str, Any]) -> Script:
        segments = [Segment(**segment) for segment in payload["segments"]]
        return Script(payload["title"], payload["hook"], payload["style"], segments, payload["hashtags"], payload["description"], payload.get("cta_final"), payload.get("safety_flags", {}))

    def _fallback_script(self, topic: str, style: str, length: int) -> Script:
        count = {"curiosity": 7, "tips": 8, "facts": 7, "top_list": 9}.get(style, 7)
        templates = {
            "curiosity": "Curiosidade {i}: {topic} tem um detalhe que quase ninguém percebe.",
            "tips": "Dica {i}: ação prática sobre {topic} para aplicar hoje.",
            "facts": "Fato {i}: em {topic}, esse dado surpreende muita gente.",
            "top_list": "Posição {i}: ponto essencial sobre {topic} que merece destaque.",
        }
        segments = [Segment(templates[style].format(i=i + 1, topic=topic), [topic, style, f"item {i+1}"], ["surpreende" if style != "tips" else "prática"]) for i in range(count)]
        return Script(f"{topic.title()} em {count} pontos", f"Você vai ver {topic} de outro jeito em menos de {length} segundos.", style, segments, ["#aprendeaqui", "#curiosidades", "#shorts"], f"Vídeo sobre {topic} com estilo {style}.", None, {"fallback_mode": True})
