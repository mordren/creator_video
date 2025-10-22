#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from pathlib import Path

# -------------------------- Pastas -------------------------------------------------
PASTA_BASE = Path(r"E:\Canal Religioso\roteiros")
PASTA_CANAL = Path(r"C:\Users\mordren\Documents\creator\canais\filosofia")
PASTA_VIDEOS = Path(r"E:\Canal Religioso\Vídeos")

# -------------------------- Parâmetros Comuns --------------------------------------
IDIOMA = "en"
TAMANHO_MAX = 3650
API_KEY = "SUA_API_KEY_DO_GEMINI"
LLM_PROVIDER = "gemini"
MODEL_NAME = "gemini-2.5-flash"

# -------------------------- Agente -------------------------------------------------
AGENTE_FILE = "agente.txt"      # Prompt principal do agente
SCHEMA_FILE = "schema.json"     # Definição do formato de saída
TEMAS_FILE = "temas.txt"        # Lista de temas

# -------------------------- TTS ----------------------------------------------------
VOZ_TTS = "en-US-AndrewNeural"
TAXA_TTS = "-6%"
TOM_TTS = "+0Hz"

# -------------------------- Vídeo --------------------------------------------------
RESOLUCAO = "1280x720"
FPS = 60
FONTE = "Montserrat-Black"
TAMANHO_FONTE = 90