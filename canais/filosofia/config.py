#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações padrão para qualquer canal
"""

from pathlib import Path

# -------------------------- Pastas -------------------------------------------------
PASTA_BASE = Path(r"E:\Canal Dark\Vídeos Automáticos")
PASTA_CANAL = Path(r"C:\Users\mordren\Documents\creator\canais\filosofia")
PASTA_VIDEOS = Path(r"E:\Canal Dark\Vídeos Automáticos\Vídeos")

# -------------------------- Parâmetros Comuns --------------------------------------
IDIOMA = "pt"
TAMANHO_MAX = 135
API_KEY = "SUA_API_KEY_DO_GEMINI"
LLM_PROVIDER = "gemini"
MODEL_NAME = "gemini-2.5-flash"

# -------------------------- Agente -------------------------------------------------
AGENTE_FILE = "agente.txt"      # Prompt principal do agente
SCHEMA_FILE = "schema.json"     # Definição do formato de saída
TEMAS_FILE = "temas.txt"        # Lista de temas

# -------------------------- TTS ----------------------------------------------------
VOZ_TTS = "pt-BR-AntonioNeural"
TAXA_TTS = "+15%"
TOM_TTS = "-2Hz"

# -------------------------- Vídeo --------------------------------------------------
RESOLUCAO = "720x1280"
FPS = 60
FONTE = "Montserrat-Black"
TAMANHO_FONTE = 90