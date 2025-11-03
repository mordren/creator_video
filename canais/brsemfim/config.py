#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

# -------------------------- Pastas -------------------------------------------------
PASTA_BASE = Path(r"G:\Brsemfim\Roteiros")
PASTA_CANAL = Path(r"C:\Users\mordren\Documents\creator\canais\brsemfim")
PASTA_VIDEOS = Path(r"G:\Brsemfim\Vídeos")
MUSICA_SHORT = Path(r"C:\Users\mordren\Documents\creator\canais\brsemfim\assets\music\musica.mp3")
MUSICA_LONG = Path(r"C:\Users\mordren\Documents\creator\canais\brsemfim\assets\music\musica.mp3")
NOME = "BR sem Fim"
LINK = "@brsemfim"
# -------------------------- Parâmetros Comuns --------------------------------------
IDIOMA = "pt"
TAMANHO_MAX_SHORT = 130
TAMANHO_MAX_LONG = 1300

# ✅ NOVO: Durações separadas para short e long
DURACAO_MIN_SHORT = 1
DURACAO_MIN_LONG = 25

# -------------------------- Agente -------------------------------------------------
AGENTE_FILE = "agente.txt"
SCHEMA_FILE = "schema.json"
TEMAS_FILE = "temas.txt"

# -------------------------- TTS ----------------------------------------------------
EDGE_TTS_VOICE = "pt-BR-AntonioNeural"
EDGE_TTS_RATE = "-6%"
EDGE_TTS_PITCH = "+2Hz"
EDGE_TTS_LEGENDAS = True
EDGE_TTS_AJUSTAR_TIMESTAMPS: True  

# Gemini TTS (premium)
GEMINI_TTS_VOICE = "Algenib"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_TTS_BITRATE = "192k"
GEMINI_TTS_PROMPT = (
    "Leia em tom sombrio e misterioso, como uma narração de conto de terror. "
    "Português brasileiro, fluidez contínua, sem pausas longas."
)

# -------------------------- Vídeo --------------------------------------------------
RESOLUCAO = "720x1280"  # Vertical para shorts
FPS = 60
FONTE = "Montserrat-Black"
TAMANHO_FONTE = 90

# -------------------------- Imagens ------------------------------------------------
IMAGES_DIR_SHORT = PASTA_BASE / "imagens_short"
IMAGES_DIR_LONG = PASTA_BASE / "imagens_long"

# -------------------------- Templates ----------------------------------------------
TEMPLATE_SHORT = "short_sequencial"
TEMPLATE_LONG = "long_estatico"
RESOLUCAO_SHORT = "720x1280"  # Vertical para shorts
RESOLUCAO_LONG = "1280x720"   # Horizontal para vídeos longos

