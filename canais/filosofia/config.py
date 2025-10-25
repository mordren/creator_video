#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações padrão para qualquer canal
"""

from pathlib import Path

# -------------------------- Pastas -------------------------------------------------
PASTA_BASE = Path(r"E:\Canal Dark\Vídeos Automáticos")
PASTA_CANAL = Path(__file__).parent  # Pasta atual do canal
PASTA_VIDEOS = Path(r"E:\Canal Dark\Vídeos Automáticos\Vídeos")
MUSICA = Path(r"C:\Users\mordren\Documents\creator\canais\filosofia\assets\music\filosofia.mp3")
IMAGES_DIR_SHORT = Path(r"C:\Users\mordren\Documents\creator\canais\filosofia\assets\imagens_template")
NOME = "Reflexões do Poder"
LINK = "@reflexoes_do_poder"


# Adicionar também templates específicos
TEMPLATE_SHORT = 'short_filosofia'
TEMPLATE_LONG = 'long_filosofia'  # Você pode criar este depois

# -------------------------- Parâmetros Comuns --------------------------------------
IDIOMA = "pt"
TAMANHO_MAX = 135
MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.8
TOP_P = 0.9

# -------------------------- Agente -------------------------------------------------
AGENTE_FILE = "agente.txt"
SCHEMA_FILE = "schema.json"
TEMAS_FILE = "temas.txt"

# -------------------------- TTS - CONFIGURAÇÕES MULTIPROVEDOR ----------------------
TTS_PROVIDER = "edge"  # edge, google, azure, gemini

# Edge TTS (gratuito - seu provedor atual)
EDGE_TTS_VOICE = "pt-BR-AntonioNeural"
EDGE_TTS_RATE = "+15%"
EDGE_TTS_PITCH = "-2Hz"
EDGE_TTS_LEGENDAS = True

# Gemini TTS (premium)
GEMINI_TTS_VOICE = "Algenib"  # ou outra voz disponível
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_TTS_BITRATE = "192k"
GEMINI_TTS_PROMPT = (
    "Leia em refletivo e informativo, sem muita animação, ritmo acelerado (~1.40x), como se fosse um short de youtube "
    "sem pausas longas. Narre em português do Brasil, com fluidez contínua, "
    "sem barulhos de respiração e sem hesitação."
)

# -------------------------- Vídeo --------------------------------------------------
RESOLUCAO = "720x1280"
FPS = 60
FONTE = "Montserrat-Black"
TAMANHO_FONTE = 90
