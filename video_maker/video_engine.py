# video_maker/video_engine.py

import sys
import os
import inspect

# Factory de efeitos
_efeitos_registry = {}

def registrar_efeito(nome, funcao):
    """Registra um efeito no factory"""
    _efeitos_registry[nome] = funcao

def aplicar_efeito(nome_efeito, imagem_path, duracao):
    """Aplica um efeito usando o factory - versão simples compatível"""
    if nome_efeito not in _efeitos_registry:
        raise ValueError(f"Efeito '{nome_efeito}' não encontrado. Efeitos disponíveis: {list(_efeitos_registry.keys())}")
    
    return _efeitos_registry[nome_efeito](imagem_path, duracao)

def listar_efeitos():
    """Lista todos os efeitos disponíveis"""
    return list(_efeitos_registry.keys())

# Registrar efeitos disponíveis (usando os nomes das funções originais)
try:
    from .efeitos.camera_instavel import criar_video_camera_instavel
    registrar_efeito('camera_instavel', criar_video_camera_instavel)
except ImportError as e:
    print(f"⚠️ Não foi possível registrar camera_instavel: {e}")

try:
    from .efeitos.pan import criar_video_pan
    registrar_efeito('pan', criar_video_pan)
except ImportError as e:
    print(f"⚠️ Não foi possível registrar pan: {e}")

try:
    from .efeitos.depth_3d import criar_video_depth_3d
    registrar_efeito('depth_3d', criar_video_depth_3d)
except ImportError as e:
    print(f"⚠️ Não foi possível registrar depth_3d: {e}")

try:
    from .efeitos.panoramica_vertical import criar_video_panoramica_vertical
    registrar_efeito('panoramica_vertical', criar_video_panoramica_vertical)
except ImportError as e:
    print(f"⚠️ Não foi possível registrar panoramica_vertical: {e}")

try:
    from .efeitos.zoom_invertido import criar_video_zoom_invertido
    registrar_efeito('zoom_invertido', criar_video_zoom_invertido)
except ImportError as e:
    print(f"⚠️ Não foi possível registrar zoom_invertido: {e}")

try:
    from .efeitos.zoom_pulse import criar_video_pulse
    registrar_efeito('zoom_pulse', criar_video_pulse)
except ImportError as e:
    print(f"⚠️ Não foi possível registrar zoom_pulse: {e}")

print(f"✅ Video Engine carregada com {len(_efeitos_registry)} efeitos")