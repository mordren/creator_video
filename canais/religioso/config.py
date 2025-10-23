#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from pathlib import Path

# -------------------------- Pastas -------------------------------------------------
PASTA_BASE = Path(r"E:\Canal Religioso\roteiros")
PASTA_CANAL = Path(r"C:\Users\mordren\Documents\creator\canais\filosofia")
PASTA_VIDEOS = Path(r"E:\Canal Religioso\Vídeos")

# -------------------------- Parâmetros Comuns --------------------------------------
IDIOMA = "en"
TAMANHO_MAX = 3300
DURACAO_MIN = 30


# -------------------------- Agente -------------------------------------------------
AGENTE_FILE = "agente.txt"      # Prompt principal do agente
SCHEMA_FILE = "schema.json"     # Definição do formato de saída
TEMAS_FILE = "temas.txt"        # Lista de temas

# -------------------------- TTS ----------------------------------------------------
EDGE_TTS_VOICE = "en-US-AndrewNeural"
EDGE_TTS_RATE = "-6%"
EDGE_TTS_PITCH = "+0Hz"
EDGE_TTS_LEGENDAS = True

# Gemini TTS (premium)
GEMINI_TTS_VOICE = "Algenib"  # ou outra voz disponível
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_TTS_BITRATE = "192k"
GEMINI_TTS_PROMPT = (
    "Leia em refletivo e informativo, como se fosse uma narração de um vídeo de inspiração e restropecção"
    "sem pausas longas. Inglês americano, com fluidez contínua, "
    "sem barulhos de respiração e sem hesitação."
)

# -------------------------- Vídeo --------------------------------------------------
RESOLUCAO = "1280x720"
FPS = 60
FONTE = "Montserrat-Black"
TAMANHO_FONTE = 90
MUSICA = Path(r"C:\Users\mordren\Documents\creator\canais\filosofia\assets\music\filosofia.mp3")