# video.py
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Adiciona o diretório atual ao path para imports
sys.path.append(str(Path(__file__).parent))

class VideoGenerator:
    def __init__(self):
        # Importação tardia para evitar circular imports
        from crud.manager import DatabaseManager
        self.db = DatabaseManager()

    def gerar_video(self, canal: str, roteiro_id: int, tipo_forcado: str = None) -> bool:
        """Gera vídeo para um roteiro existente baseado na resolução ou tipo forçado"""
        print(f"🎬 Gerando vídeo para: {canal} (Roteiro ID: {roteiro_id})")
        
        try:
            # Carrega configuração do canal
            from read_config import carregar_config_canal
            config = carregar_config_canal(canal)
            
            # Busca roteiro no banco pelo ID
            roteiro = self.db.roteiros.buscar_por_id(roteiro_id)
            if not roteiro:
                print(f"❌ Roteiro não encontrado no banco com ID: {roteiro_id}")
                return False
            
            # Verifica se áudio foi gerado
            if not roteiro.audio_gerado:
                print("❌ Áudio não foi gerado para este roteiro")
                return False
            
            # Determina o tipo de vídeo (forçado ou pela resolução)
            if tipo_forcado:
                tipo_video = tipo_forcado.upper()
                print(f"🎯 Tipo forçado: {tipo_video}")
            else:
                tipo_video = self._determinar_tipo_video(roteiro.resolucao)
                print(f"🎯 Resolução: {roteiro.resolucao} -> {tipo_video}")
            
            template_name = self._determinar_template(tipo_video, config)
            print(f"📝 Template selecionado: {template_name}")
            
            # Busca informações do áudio no banco
            info_video = self.db.videos.buscar_por_roteiro_id(roteiro.id)
            if not info_video:
                print("❌ Informações de áudio não encontradas no banco")
                return False
            
            # Obtém caminho da pasta usando id_video do roteiro
            pasta_base = Path(config['PASTA_BASE'])
            pasta_video = pasta_base / roteiro.id_video
            
            if not pasta_video.exists():
                print(f"❌ Pasta do vídeo não encontrada: {pasta_video}")
                return False
            
            # Carrega e executa o template usando o sistema centralizado
            resultado = self._executar_template(
                template_name, 
                info_video.arquivo_audio or info_video.audio_mixado,
                config,
                pasta_video,
                roteiro
            )
            
            if resultado and resultado.exists():
                # Atualiza banco com sucesso
                success = self._atualizar_video_sucesso(
                    roteiro.id, 
                    str(resultado),
                    info_video.duracao or 0
                )
                
                if success:
                    print(f"✅ Vídeo {tipo_video} gerado com sucesso: {resultado}")
                    return True
            
            print("❌ Falha na geração do vídeo")
            return False
            
        except Exception as e:
            print(f"❌ Erro na geração do vídeo: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _determinar_tipo_video(self, resolucao: str) -> str:
        """Determina se é SHORT ou LONG baseado na resolução"""
        if resolucao == "vertical" or resolucao == "720x1280":
            return "SHORT"
        elif resolucao == "horizontal" or resolucao == "1280x720":
            return "LONG"
        else:
            # Default para SHORT se não reconhecer
            print(f"⚠️ Resolução '{resolucao}' não reconhecida, usando SHORT como padrão")
            return "SHORT"

    def _determinar_template(self, tipo_video: str, config: dict) -> str:
        """Determina qual template usar baseado no tipo de vídeo"""
        if tipo_video == "SHORT":
            return config.get('TEMPLATE_SHORT', 'short_filosofia')
        else:  # LONG
            return config.get('TEMPLATE_LONG', 'long_filosofia')

# video.py - na função _executar_template
    def _executar_template(self, template_name: str, audio_path: str, config: dict, 
                        pasta_video: Path, roteiro) -> Path:
        """Executa o template de vídeo específico usando o sistema centralizado"""
        try:
            # Usa o sistema centralizado do video_engine
            from video_maker.video_engine import obter_template
            
            # Obtém a função render do template
            render_func = obter_template(template_name)
            
            # Determina qual diretório de imagens usar baseado no tipo de vídeo
            tipo_video = self._determinar_tipo_video(roteiro.resolucao)
            if tipo_video == "SHORT":
                images_dir = config.get('IMAGES_DIR_SHORT', './imagens_short')
            else:  # LONG
                images_dir = config.get('IMAGES_DIR_LONG', './imagens_long')
            
            # Prepara configuração adicional para o template
            template_config = {
                'IMAGE_DIR': images_dir,
                'IMAGES_DIR_SHORT': config.get('IMAGES_DIR_SHORT'),
                'IMAGES_DIR_LONG': config.get('IMAGES_DIR_LONG'),
                'PASTA_VIDEOS': config.get('PASTA_VIDEOS'),
                'titulo': roteiro.titulo or f"Vídeo {pasta_video.name}",
                'hook': roteiro.hook if hasattr(roteiro, 'hook') else roteiro.titulo,  # NOVO: passa o hook
                'descricao': roteiro.descricao if hasattr(roteiro, 'descricao') else '',  # NOVO: passa a descrição
                'num_imagens': config.get('NUM_IMAGES', 18),
                'output_dir': str(pasta_video),
                'pasta_video': str(pasta_video),
                'resolucao': roteiro.resolucao,
                'tipo_video': tipo_video
            }
            
            # Executa o render
            print(f"🎨 Executando template {template_name}...")
            print(f"📁 Usando diretório de imagens: {images_dir}")
            print(f"🎯 Hook: {template_config['hook']}")  # DEBUG do hook
            resultado = render_func(audio_path, template_config)
            
            return Path(resultado) if resultado else None
            
        except Exception as e:
            print(f"❌ Erro ao executar template {template_name}: {e}")
            raise
                
    def _atualizar_video_sucesso(self, roteiro_id: int, arquivo_video: str, duracao: int) -> bool:
        """Atualiza banco de dados após sucesso na geração do vídeo"""
        try:
            # Marca roteiro como tendo vídeo gerado
            self.db.roteiros.marcar_video_gerado(roteiro_id)
            
            # Salva informações do vídeo
            success = self.db.videos.salvar_info_video(
                roteiro_id=roteiro_id,
                arquivo_video=arquivo_video,
                duracao=duracao
            )
            
            if success:
                print("💾 Banco atualizado com informações do vídeo")
            else:
                print("⚠️ Falha ao atualizar informações do vídeo no banco")
                
            return success
            
        except Exception as e:
            print(f"⚠️ Erro ao atualizar banco: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Gerar vídeo para roteiros')
    parser.add_argument('canal', help='Nome do canal')
    parser.add_argument('roteiro_id', type=int, help='ID do roteiro no banco de dados')
    parser.add_argument('tipo', nargs='?', help='Tipo de vídeo (short/long) - opcional')
    
    args = parser.parse_args()
    
    success = VideoGenerator().gerar_video(args.canal, args.roteiro_id, args.tipo)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()