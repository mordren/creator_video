#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from read_config import carregar_config_canal
from video_maker import VideoMaker

def main():
    parser = argparse.ArgumentParser(description='Gerar vídeos por tipo específico')
    parser.add_argument('canal', help='Nome do canal')
    parser.add_argument('video_id', help='ID do vídeo')
    parser.add_argument('tipo', choices=['short_generico', 'short_sequencial', 'long_estatico'], 
                       help='Tipo de vídeo: short_generico, short_sequencial, long_estatico')
    
    args = parser.parse_args()
    
    # Carrega configuração do canal
    config = carregar_config_canal(args.canal)
    
    # Define as configurações
    video_config = {
        'video_type': args.tipo,
        'video_id': args.video_id,
        'canal': args.canal
    }
    
    # Inicializa o VideoMaker
    video_maker = VideoMaker(config, video_config)
    
    # Gera o vídeo
    success = video_maker.render()
    
    if success:
        print(f"✅ Vídeo {args.tipo} gerado com sucesso para {args.canal}/{args.video_id}")
    else:
        print(f"❌ Falha ao gerar vídeo {args.tipo} para {args.canal}/{args.video_id}")
        sys.exit(1)

if __name__ == "__main__":
    main()