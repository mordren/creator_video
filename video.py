#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

# Adiciona o diretório atual ao path para imports
sys.path.append(str(Path(__file__).parent))

class VideoGenerator:
    def __init__(self):
        from crud.roteiro_manager import RoteiroManager
        from crud.video_manager import VideoManager
        from crud.canal_manager import CanalManager        
        self.roteiro_manager = RoteiroManager()
        self.video_manager = VideoManager()
        self.canal_manager = CanalManager()

    def gerar_video(self, roteiro_id: int, tipo_forcado: str = None) -> bool:
        """Gera vídeo para um roteiro existente"""
        print(f"🎬 Gerando vídeo para Roteiro ID: {roteiro_id}")
        
        try:
            # Busca dados básicos
            roteiro = self.roteiro_manager.buscar_por_id(roteiro_id)
            if not roteiro:
                print(f"❌ Roteiro não encontrado")
                return False
            
            canal = self.canal_manager.buscar_por_id(roteiro.canal_id)
            if not canal:
                print(f"❌ Canal não encontrado")
                return False

            # Verifica pré-condições
            if not roteiro.audio_gerado:
                print("❌ Áudio não foi gerado")
                return False

            # Carrega configuração e determina tipo
            from read_config import carregar_config_canal
            config = carregar_config_canal(canal.config_path)
            
            tipo_video = tipo_forcado.upper() if tipo_forcado else self._determinar_tipo_video(roteiro.resolucao)
            template_name = config.get(tipo_video)
            
            print(f"🎯 Tipo: {tipo_video}, Template: {template_name}")

            # Busca informações do áudio
            info_video = self.video_manager.buscar_por_roteiro_id(roteiro.id)
            if not info_video:
                print("❌ Informações de áudio não encontradas")
                return False
            
            arquivo_audio = info_video.audio_mixado or info_video.arquivo_audio
            if not arquivo_audio or not Path(arquivo_audio).exists():
                print(f"❌ Arquivo de áudio não encontrado: {arquivo_audio}")
                return False

            # Executa template
            resultado = self._executar_template(template_name, arquivo_audio, config, roteiro, tipo_video)

            if resultado and resultado.exists():
                return self._finalizar_geracao(roteiro.id, str(resultado), info_video.duracao or 0)
            
            print("❌ Falha na geração do vídeo")
            return False
            
        except Exception as e:
            print(f"❌ Erro na geração do vídeo: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _determinar_tipo_video(self, resolucao: str) -> str:
        """Determina se é SHORT ou LONG baseado na resolução"""
        if not resolucao:
            return "SHORT"
            
        resolucao_lower = resolucao.lower().strip()
        
        # Padrões para Short (vertical)
        short_patterns = ['vertical', '720x1280', '1080x1920', 'x1280', 'x1920', '9:16']
        # Padrões para Long (horizontal)  
        long_patterns = ['horizontal', '1280x720', '1920x1080', 'x720', 'x1080', '16:9']
        
        if any(pattern in resolucao_lower for pattern in short_patterns):
            return "TEMPLATE_SHORT"
        elif any(pattern in resolucao_lower for pattern in long_patterns):
            return "TEMPLATE_LONG"
        else:
            print(f"⚠️ Resolução '{resolucao}' não reconhecida, usando SHORT")
            return "SHORT"

    def _executar_template(self, template_name: str, audio_path: str, config: dict, roteiro, tipo_video: str) -> Path:
        """Executa o template de vídeo específico"""
        try:
            from video_maker.video_engine import obter_template
            
            render_func = obter_template(template_name)
            print(f"🎨 Executando template {template_name}...")
            
            resultado = render_func(audio_path, config, roteiro)
            return Path(resultado) if resultado else None
            
        except Exception as e:
            print(f"❌ Erro ao executar template {template_name}: {e}")
            raise
                
    def _finalizar_geracao(self, roteiro_id: int, arquivo_video: str, duracao: int) -> bool:
        """Finaliza a geração atualizando todos os status"""
        try:
            # Marca roteiro como tendo vídeo gerado
            self.roteiro_manager.marcar_video_gerado(roteiro_id)
            
            # Salva informações do vídeo usando o método genérico
            success = self.video_manager.salvar_info_video(
                roteiro_id=roteiro_id,
                arquivo_video=arquivo_video,
                duracao=duracao
            )
            
            if success:
                print(f"✅ Vídeo gerado e salvo: {arquivo_video}")
            else:
                print("⚠️ Vídeo gerado mas falha ao salvar informações")
                
            return success
            
        except Exception as e:
            print(f"⚠️ Erro ao finalizar geração: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Gerar vídeo para roteiros')
    parser.add_argument('roteiro_id', type=int, help='ID do roteiro no banco de dados')
    parser.add_argument('--tipo', help='Tipo de vídeo (short/long) - opcional')
    
    args = parser.parse_args()
    
    success = VideoGenerator().gerar_video(args.roteiro_id, args.tipo)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()