#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Adiciona o diretório atual ao path para imports
sys.path.append(str(Path(__file__).parent))

class VideoGenerator:
    def __init__(self):
        # Importação tardia para evitar circular imports
        from crud.roteiro_manager import RoteiroManager
        from crud.video_manager import VideoManager
        from crud.canal_manager import CanalManager        
        self.roteiro_manager = RoteiroManager()
        self.video_manager = VideoManager()
        self.canal_manager = CanalManager()

    def gerar_video(self, roteiro_id: int, tipo_forcado: str = None) -> bool:
        """Gera vídeo para um roteiro existente baseado na resolução ou tipo forçado"""
        print(f"🎬 Gerando vídeo para Roteiro ID: {roteiro_id}")
        
        try:
            # Busca roteiro no banco pelo ID
            roteiro = self.roteiro_manager.buscar_por_id(roteiro_id)
            if not roteiro:
                print(f"❌ Roteiro não encontrado no banco com ID: {roteiro_id}")
                return False
            
            # Busca canal para obter configuração
            canal = self.canal_manager.buscar_por_id(roteiro.canal_id)
            if not canal:
                print(f"❌ Canal com ID {roteiro.canal_id} não encontrado")
                return False

            # Carrega configuração do canal
            from read_config import carregar_config_canal
            config = carregar_config_canal(canal.config_path)
            

            # Verifica se áudio foi gerado
            if not roteiro.audio_gerado:
                print("❌ Áudio não foi gerado para este roteiro")
                return False
            
            # ✅ USA A RESOLUÇÃO DO ROTEIRO para determinar o tipo de vídeo
            if tipo_forcado:
                tipo_video = tipo_forcado.upper()
                print(f"🎯 Tipo forçado: {tipo_video}")
            else:
                tipo_video = self._determinar_tipo_video(roteiro.resolucao)
                print(f"🎯 Resolução do roteiro: '{roteiro.resolucao}' -> {tipo_video}")
            
            template_name = config.get(tipo_video)
            print(f"📝 Template selecionado: {template_name}")
            
            # ✅ BUSCA INFORMAÇÕES DO VÍDEO PELO ROTEIRO_ID
            info_video = self.video_manager.buscar_por_roteiro_id(roteiro.id)
            if not info_video:
                print("❌ Informações de áudio não encontradas no banco")
                return False
            
            # Verifica se temos arquivo de áudio
            arquivo_audio = info_video.audio_mixado or info_video.arquivo_audio
            if not arquivo_audio or not Path(arquivo_audio).exists():
                print(f"❌ Arquivo de áudio não encontrado: {arquivo_audio}")
                return False
            
            # ✅ Usa id_video do roteiro para construir o caminho
            pasta_base = Path(config['PASTA_BASE'])
            pasta_video = config.get('PASTA_VIDEOS') # ← id_video é o nome da pasta
            
            if not pasta_video.exists():
                print(f"❌ Pasta do vídeo não encontrada: {pasta_video}")
                return False
            
            # Carrega e executa o template usando o sistema centralizado
            resultado = self._executar_template(
                template_name, 
                arquivo_audio,
                config,
                pasta_video,
                roteiro,
                tipo_video  # ✅ Passa o tipo_video determinado
            )

            print('RESULTADO É ESSE:' + str(resultado))
            
            if resultado and resultado.exists():
                # Atualiza banco com sucesso
                success = self._atualizar_video_sucesso(
                    roteiro.id, 
                    str(resultado),
                    info_video.duracao or 0,                    
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
        """Determina se é SHORT ou LONG baseado na resolução do roteiro"""
        # Converte para minúsculas para comparação case-insensitive
        resolucao_lower = resolucao.lower().strip() if resolucao else ""
        
        # Verifica por padrões de vertical/short
        if (resolucao_lower == "vertical" or 
            resolucao_lower == "720x1280" or 
            resolucao_lower == "1080x1920" or
            "x1280" in resolucao_lower or  # captura 720x1280, 1080x1280, etc
            "x1920" in resolucao_lower or  # captura 1080x1920, etc
            "9:16" in resolucao_lower):
            return "TEMPLATE_SHORT"
        
        # Verifica por padrões de horizontal/long
        elif (resolucao_lower == "horizontal" or 
              resolucao_lower == "1280x720" or 
              resolucao_lower == "1920x1080" or
              "x720" in resolucao_lower or   # captura 1280x720, 1920x720, etc
              "x1080" in resolucao_lower or  # captura 1920x1080, etc
              "16:9" in resolucao_lower):
            return "TEMPLATE_LONG"
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

    def _executar_template(self, template_name: str, audio_path: str, config: dict, 
                        pasta_video: Path, roteiro, tipo_video: str) -> Path:
        """Executa o template de vídeo específico usando o sistema centralizado"""
        try:
            # Usa o sistema centralizado do video_engine
            from video_maker.video_engine import obter_template
            
            # Obtém a função render do template
            render_func = obter_template(template_name)
            
            # ✅ USA O TIPO_VIDEO PASSADO (já determinado) para definir diretório de imagens
            if tipo_video == "SHORT":
                images_dir = config.get('IMAGES_DIR_SHORT', './imagens_short')
            else:  # LONG
                images_dir = config.get('IMAGES_DIR_LONG', './imagens_long')
            
            # Executa o render
            print(f"🎨 Executando template {template_name}...")
            print(f"📁 Usando diretório de imagens: {images_dir}")
            print(f"📁 Pasta do vídeo: {pasta_video}")
            print(f"🎯 Tipo de vídeo: {tipo_video}")
            print(f"📐 Resolução: {roteiro.resolucao}")
            
            resultado = render_func(audio_path, config, roteiro)
            
            return Path(resultado) if resultado else None
            
        except Exception as e:
            print(f"❌ Erro ao executar template {template_name}: {e}")
            raise
                
    def _atualizar_video_sucesso(self, roteiro_id: int, arquivo_video: str, duracao: int) -> bool:
        try:
            self.roteiro_manager.marcar_video_gerado(roteiro_id)
            # carrega o roteiro para pegar titulo e thumb
            roteiro = self.roteiro_manager.buscar_por_id(roteiro_id)
            
            success = self.video_manager.salvar_info_video(
                roteiro_id=roteiro_id,
                arquivo_video=arquivo_video,
                duracao=duracao,                              
            )
            print("💾 Banco atualizado com informações do vídeo" if success else "⚠️ Falha ao atualizar informações do vídeo")
            return success
        except Exception as e:
            print(f"⚠️ Erro ao atualizar banco: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Gerar vídeo para roteiros')
    parser.add_argument('roteiro_id', type=int, help='ID do roteiro no banco de dados')
    parser.add_argument('--tipo', help='Tipo de vídeo (short/long) - opcional, será determinado pela resolução se não informado')
    
    args = parser.parse_args()
    
    success = VideoGenerator().gerar_video(args.roteiro_id, args.tipo)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()