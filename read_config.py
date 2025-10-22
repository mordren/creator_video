#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Carregador dinâmico de configurações por canal
"""

import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any

def carregar_config_canal(canal: str) -> Dict[str, Any]:
    """
    Carrega dinamicamente o config.py de um canal específico
    """
    canal_path = Path(f"canais/{canal}")
    
    

    if not canal_path.exists():
        raise ValueError(f"Canal '{canal}' não encontrado em {canal_path}")
    
    config_path = canal_path / "config.py"
    
    if not config_path.exists():
        raise ValueError(f"Arquivo config.py não encontrado para canal '{canal}'")
    
    # Carrega o módulo dinamicamente
    spec = importlib.util.spec_from_file_location(f"config_{canal}", config_path)
    config_module = importlib.util.module_from_spec(spec)
    sys.modules[f"config_{canal}"] = config_module
    spec.loader.exec_module(config_module)
    
    # Extrai todas as variáveis UPPERCASE do módulo
    config = {}
    for key in dir(config_module):
        if key.isupper() and not key.startswith('_'):
            config[key] = getattr(config_module, key)
    
    # ✅ CORREÇÃO: Adiciona PASTA_CANAL e PASTA_BASE explicitamente
    # Estas são as chaves ESSENCIAIS que o código principal espera
    config['PASTA_CANAL'] = canal_path
    config['PASTA_BASE'] = getattr(config_module, 'PASTA_BASE', 
                                  Path(__file__).parent.parent / "conteudo_gerado")
    
    # ✅ DEBUG: Verifique se está carregando corretamente
    print(f"🔧 Configuração carregada para canal: {canal}")
    print(f"📁 PASTA_CANAL: {config['PASTA_CANAL']}")
    print(f"📁 PASTA_BASE: {config['PASTA_BASE']}")
    print(f"🔧 MODEL_NAME: {config.get('MODEL_NAME', 'N/D')}")
    print(f"🎭 ESTILO: {config.get('ESTILO', 'N/D')}")
    
    return config

def listar_canais_disponiveis() -> list:
    """Lista todos os canais disponíveis"""
    canais_path = Path("canais")
    if not canais_path.exists():
        return []
    
    return [p.name for p in canais_path.iterdir() if p.is_dir()]