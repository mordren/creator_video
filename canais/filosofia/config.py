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

# -------------------------- Parâmetros Comuns --------------------------------------
IDIOMA = "pt"
TAMANHO_MAX = 135
API_KEY = "SUA_API_KEY_DO_GEMINI"
LLM_PROVIDER = "gemini"
MODEL_NAME = "gemini-2.5-flash"

# -------------------------- Agente -------------------------------------------------
AGENTE_FILE = "agente.txt"
SCHEMA_FILE = "schema.json"
TEMAS_FILE = "temas.txt"

# -------------------------- TTS ----------------------------------------------------
TTS_PROVIDER = "edge"
EDGE_TTS_VOICE = "pt-BR-AntonioNeural"
EDGE_TTS_RATE = "+15%"
EDGE_TTS_PITCH = "-2Hz"
EDGE_TTS_LEGENDAS = True

# Compatibilidade
VOZ_TTS = "pt-BR-AntonioNeural"
TAXA_TTS = "+15%"
TOM_TTS = "-2Hz"

# -------------------------- Vídeo --------------------------------------------------
RESOLUCAO = "720x1280"
FPS = 60
FONTE = "Montserrat-Black"
TAMANHO_FONTE = 90