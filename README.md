# Aprende Aqui — Auto Viral Vertical Video Engine (PT-BR)

Projeto Python completo para geração automática de vídeos verticais 9:16 (Shorts/Reels/TikTok) com foco em retenção, ritmo moderno e anti-repetição.

## Visão geral

O pipeline gera vídeos com:
- hook forte nos primeiros 1–2 segundos
- CTA inicial de retenção com variação inteligente
- cenas rápidas com movimento dinâmico
- zooms e micro-variações por cena
- pattern interrupts ocasionais
- legendas profissionais (`.srt` + `.ass`)
- CTA final de engajamento
- render final em `final.mp4`

Arquitetura preparada para evolução multi-idioma.

## Estrutura

```text
.
├─ src/
│  ├─ main.py
│  ├─ config.py
│  ├─ models.py
│  ├─ services/
│  │  ├─ gemini_service.py
│  │  ├─ elevenlabs_service.py
│  │  ├─ pexels_service.py
│  │  ├─ cta_manager.py
│  │  └─ subtitle_service.py
│  ├─ utils/
│  │  ├─ logging.py
│  │  ├─ retry.py
│  │  └─ cache.py
│  └─ video/
│     └─ composer.py
├─ .github/workflows/generate.yml
├─ output/
└─ assets/cache/
```

## Requisitos

- Python 3.10+
- FFmpeg e FFprobe instalados
- Chaves opcionais para qualidade máxima:
  - `GEMINI_API_KEY`
  - `ELEVENLABS_API_KEY`
  - `ELEVENLABS_VOICE_ID`
  - `PEXELS_API_KEY`

Sem chaves, o sistema roda em modo fallback (roteiro local + áudio sintético + placeholder visual).

## Instalação

```bash
python -m pip install --upgrade pip
pip install .
```

## CLI

Comando principal:

```bash
python -m src.main generate --topic "fatos curiosos sobre o cérebro" --style curiosity --length 40
```

Flags adicionais:

```bash
--style curiosity|tips|facts|top_list
--cta_variation on|off
--visual_intensity low|medium|high
--music on|off
--seed 42
```

### Exemplo completo

```bash
python -m src.main generate \
  --topic "fatos curiosos sobre o cérebro" \
  --style curiosity \
  --length 40 \
  --cta_variation on \
  --visual_intensity high \
  --music off \
  --seed 10
```

## Saídas por execução

Em `output/<style>_<topic>/`:
- `final.mp4`
- `metadata.json`
- `generation_report.json`
- `narration_full.mp3`
- `timing.json`
- `subtitles.srt`
- `subtitles.ass`
- `audio/segment_*.mp3`

## Regras de viralização implementadas

- **Primeiros segundos críticos**: hook + CTA inicial combinados automaticamente.
- **Anti-estático**: zoompan em todas as cenas (com direção variada).
- **Anti-repetição**:
  - cache de CTA recente
  - alternância de posição de legenda
  - variação de intensidade visual
  - histórico de assets usados
- **Alta densidade**: roteiro com 6–10 segmentos e frases curtas.
- **Open loops**: CTAs iniciais orientados para retenção.

## Estilos narrativos

- `curiosity`: intrigante, rápido, 30–45s
- `tips`: útil/prático, sequência de ações, 35–50s
- `facts`: fatos surpreendentes, ritmo acelerado, 30–45s
- `top_list`: estrutura de ranking, 45–60s

Cada estilo possui CTA inicial específico e tratamento automático no pipeline.

## Integrações

### Gemini (roteiro)
- prompt com JSON estrito
- validação via parsing
- fallback local resiliente

### ElevenLabs (TTS)
- áudio por segmento
- concatenação para `narration_full.mp3`
- normalização loudness (`loudnorm`)
- `timing.json` via duração real de áudio

### Pexels (assets)
- busca priorizando vídeo
- fallback para imagem
- cache local
- prevenção de reutilização recente

## Legendas

- `subtitles.srt`: baseline para compatibilidade
- `subtitles.ass`: estilo grande mobile-first com outline e sombra
- destaque de palavras de ênfase com cor

## Música de fundo

- ativar com `--music on`
- definir caminho via `BG_MUSIC_PATH`
- ducking automático com sidechain compress

## GitHub Actions

Workflow em `.github/workflows/generate.yml`:
- `workflow_dispatch` com inputs `topic`, `style`, `length`
- instala FFmpeg
- instala dependências
- gera 1 vídeo de teste
- publica artifacts (`final.mp4` + metadados)

## Observabilidade e robustez

- logs estruturados JSON
- retry nas integrações externas
- cache persistente para CTAs e assets
- tolerância a falhas com fallback

## Segurança de conteúdo

O payload de roteiro reserva `safety_flags` para regras de moderação e auditoria.

## Próximos upgrades sugeridos

- word-by-word subtitle timing
- scoring de qualidade por retenção estimada
- múltiplas vozes por estilo
- scheduler de publicação
- suporte completo multi-idioma
