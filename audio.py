#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de áudio do Creator Video
"""

import sys
import os
import argparse
from pathlib import Path

# Adiciona o diretório atual ao path do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from audio_manager import AudioManager

except ImportError as e:
    print(f"❌ Erro ao importar AudioManager: {e}")
    print("📁 Estrutura atual:")
    for root, dirs, files in os.walk("."):
        level = root.replace(".", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            if file.endswith(".py"):
                print(f"{subindent}{file}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Gerar áudio para roteiros - Creator Video')
    parser.add_argument('roteiro', help='Caminho para o arquivo JSON do roteiro')
    parser.add_argument('--canal', required=True, help='Nome do canal')
    parser.add_argument('--provider', help='Provedor TTS (edge)')
    
    args = parser.parse_args()
    
    roteiro_path = Path(args.roteiro)
    if not roteiro_path.exists():
        print(f"❌ Arquivo de roteiro não encontrado: {roteiro_path}")
        sys.exit(1)
    
    manager = AudioManager()
    success = manager.gerar_audio(roteiro_path, args.canal, args.provider)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()