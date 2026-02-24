from __future__ import annotations

import random
from pathlib import Path

from src.utils.cache import JsonCache

INITIAL_CTAS = {
    "curiosity": [
        "fica até o final porque a última vai te surpreender",
        "você provavelmente não sabia disso",
        "isso aqui quase ninguém te conta",
        "presta atenção nisso",
        "isso pode mudar como você vê esse tema",
        "espera a última, ela quebra qualquer expectativa",
        "eu duvido que você já tenha ouvido a última",
        "tem uma virada no final que vale cada segundo",
        "isso parece simples, mas guarda uma surpresa no fim",
        "fica comigo 30 segundos e você vai ver diferente",
        "essa sequência vai abrir sua cabeça",
        "se você curte curiosidade real, não pula",
    ],
    "tips": [
        "fica até o final porque a dica final é a mais prática",
        "se aplicar isso hoje, já sente resultado",
        "anota essas dicas porque funcionam de verdade",
        "essas dicas economizam tempo já no primeiro dia",
        "não pula, a última resolve um erro comum",
        "em menos de 1 minuto você aprende isso",
        "presta atenção que isso vale ouro",
        "você vai querer testar isso hoje",
        "essas dicas são simples e muito eficazes",
        "fica até o fim para pegar o passo mais forte",
        "isso aqui é direto ao ponto",
        "se você quer resultado rápido, continua",
    ],
    "facts": [
        "fato rápido: isso vai te surpreender",
        "em segundos você vai entender algo incrível",
        "isso é real e pouca gente sabe",
        "segura essa sequência de fatos",
        "o próximo fato já começa quebrando mito",
        "parece mentira, mas é comprovado",
        "fica até o final para o fato mais absurdo",
        "isso é mais comum do que parece",
        "presta atenção nesses dados",
        "esse fato muda totalmente a perspectiva",
        "se curte informação forte, continua",
        "você vai sair daqui sabendo algo raro",
    ],
    "top_list": [
        "hoje é top lista, e o número 1 é surreal",
        "fica até o final para ver o topo do ranking",
        "esse top vai te surpreender do início ao fim",
        "você não imagina quem está no primeiro lugar",
        "esse ranking tem uma virada no final",
        "acompanha a contagem porque melhora a cada posição",
        "já prepara o print desse top",
        "se você gosta de ranking, esse está forte",
        "não sai antes do top 1",
        "esse top está mais polêmico do que parece",
        "contagem regressiva começando agora",
        "espera o final porque o primeiro lugar é inesperado",
    ],
}

FINAL_CTAS = [
    "curte e segue para mais",
    "compartilha com alguém que vai gostar",
    "salva para ver depois",
    "segue o Aprende Aqui para não perder os próximos",
    "me diz nos comentários qual foi o melhor",
    "manda esse vídeo no grupo",
    "se ajudou, já deixa o like",
    "quer parte 2? comenta aqui",
    "se você chegou até aqui, já segue",
    "compartilha com quem precisa ver isso",
    "salva agora para aplicar depois",
    "segue e ativa as notificações para a próxima",
]


class CtaManager:
    def __init__(self, cache_dir: Path, seed: int | None = None):
        self.random = random.Random(seed)
        self.cache = JsonCache(cache_dir / "cta_history.json")

    def _pick_with_history(self, candidates: list[str], key: str) -> str:
        payload = self.cache.read()
        recent = payload.get(key, [])[-3:]
        filtered = [c for c in candidates if c not in recent] or candidates
        chosen = self.random.choice(filtered)
        payload[key] = (recent + [chosen])[-5:]
        self.cache.write(payload)
        return chosen

    def initial(self, style: str, enabled: bool = True) -> str:
        if not enabled:
            return INITIAL_CTAS[style][0]
        return self._pick_with_history(INITIAL_CTAS[style], f"initial_{style}")

    def final(self, enabled: bool = True) -> str:
        if not enabled:
            return FINAL_CTAS[0]
        return self._pick_with_history(FINAL_CTAS, "final")
