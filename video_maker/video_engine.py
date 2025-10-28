# video_maker/video_engine.py

import sys
import os
import inspect

# Factory de efeitos
_efeitos_registry = {}
_templates_registry = {}  # NOVO: Registry para templates

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

# NOVO: Funções para gerenciar templates
def registrar_template(nome, modulo_path):
    """Registra um template no factory"""
    _templates_registry[nome] = modulo_path

def obter_template(nome):
    """Obtém a função render de um template"""
    if nome not in _templates_registry:
        raise ValueError(f"Template '{nome}' não encontrado. Templates disponíveis: {list(_templates_registry.keys())}")
    
    modulo_path = _templates_registry[nome]
    modulo = __import__(modulo_path, fromlist=['render'])
    return getattr(modulo, 'render')

def listar_templates():
    """Lista todos os templates disponíveis"""
    return list(_templates_registry.keys())

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

# NOVO: Registrar templates disponíveis
try:
    registrar_template('short_filosofia', 'video_maker.templates.short_filosofia')
    print("✅ Template short_filosofia registrado")
except Exception as e:
    print(f"⚠️ Não foi possível registrar short_filosofia: {e}")

try:
    registrar_template('short_sequencial', 'video_maker.templates.short_sequencial')
    print("✅ Template short_sequencial registrado")
except Exception as e:
    print(f"⚠️ Não foi possível registrar short_sequencial: {e}")


try:
    registrar_template('long_filosofia', 'video_maker.templates.long_filosofia')
    print("✅ Template long_filosofia registrado")
except Exception as e:
    print(f"⚠️ Não foi possível registrar long_filosofia: {e}")

try:
    registrar_template('long_religioso', 'video_maker.templates.long_religioso')
    print("✅ Template long_religioso registrado")
except Exception as e:
    print(f"⚠️ Não foi possível registrar long_filosofia: {e}")

print(f"✅ Video Engine carregada com {len(_efeitos_registry)} efeitos e {len(_templates_registry)} templates")