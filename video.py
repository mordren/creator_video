#!/usr/bin/env python3
import argparse
import sys
import shutil  # ✅ ADICIONADO: Para mover arquivos entre unidades
from pathlib import Path

# Adiciona o diretório atual ao path para imports
sys.path.append(str(Path(__file__).parent))

class VideoGenerator:
    def __init__(self):
        from crud.roteiro_manager import RoteiroManager
        from crud.canal_manager import CanalManager        
        self.roteiro_manager = RoteiroManager()        
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

            # ✅ CORREÇÃO: Verificar se o arquivo de áudio existe
            arquivo_audio = roteiro.audio_mixado or roteiro.arquivo_audio
            if not arquivo_audio or not Path(arquivo_audio).exists():
                print(f"❌ Arquivo de áudio não encontrado: {arquivo_audio}")
                return False

            # Carrega configuração e determina tipo
            from read_config import carregar_config_canal
            config = carregar_config_canal(canal.config_path)
            
            # ✅ CORREÇÃO: Determinar tipo corretamente
            if tipo_forcado:
                tipo_video = tipo_forcado.upper()
            else:
                tipo_video = self._determinar_tipo_video(roteiro.resolucao)
            
            # ✅ CORREÇÃO: Obter template correto baseado no tipo
            template_key = f"TEMPLATE_{tipo_video}"
            template_name = config.get(template_key)
            
            if not template_name:
                print(f"❌ Template não configurado para {template_key}")
                return False

            print(f"🎯 Tipo: {tipo_video}, Template: {template_name}")

            arquivo_saida = Path(config['PASTA_VIDEOS']) / f"{roteiro.id_video}.mp4"            
            # Executa template
            resultado = self._executar_template(template_name, arquivo_audio, config, roteiro, str(arquivo_saida))

            if resultado and resultado.exists():
                # ✅ CORREÇÃO: Obter duração real do vídeo gerado
                duracao_video = self._get_video_duration(resultado)
                return self._finalizar_geracao(roteiro.id, str(resultado), duracao_video)
            
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
            return "SHORT"
        elif any(pattern in resolucao_lower for pattern in long_patterns):
            return "LONG"
        else:
            print(f"⚠️ Resolução '{resolucao}' não reconhecida, usando SHORT")
            return "SHORT"

    def _executar_template(self, template_name: str, audio_path: str, config: dict, roteiro, output_path: str) -> Path:
        """Executa o template de vídeo específico"""
        try:
            from video_maker.video_engine import obter_template
            import inspect
            
            render_func = obter_template(template_name)
            print(f"🎨 Executando template {template_name}...")
            
            # ✅ CORREÇÃO: Verificar a assinatura da função
            sig = inspect.signature(render_func)
            num_params = len(sig.parameters)
            
            if num_params == 3:
                # Template antigo: render(audio_path, config, roteiro)
                resultado = render_func(audio_path, config, roteiro)
                resultado_path = Path(resultado) if resultado else None
                
                if resultado_path and resultado_path.exists() and resultado_path != Path(output_path):
                    print(f"📦 Movendo arquivo entre unidades: {resultado_path} -> {output_path}")
                    shutil.move(str(resultado_path), output_path)
                    return Path(output_path)
                return resultado_path
                
            elif num_params == 4:
                # Template novo: render(audio_path, config, roteiro, output_path)
                resultado = render_func(audio_path, config, roteiro, output_path)
                return Path(resultado) if resultado else None
                
            else:
                print(f"❌ Assinatura não suportada para template {template_name}: {num_params} parâmetros")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao executar template {template_name}: {e}")
            raise

    def _get_video_duration(self, video_path: Path) -> int:
        """Obtém a duração do vídeo em segundos usando ffprobe"""
        try:
            import subprocess
            result = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            return int(float(result.stdout.strip()))
        except Exception as e:
            print(f"⚠️ Erro ao obter duração do vídeo: {e}")
            # Fallback: usar duração do áudio se disponível
            roteiro = self.roteiro_manager.buscar_por_id(self.roteiro_id) if hasattr(self, 'roteiro_id') else None
            return roteiro.duracao if roteiro and roteiro.duracao else 0
                
    def _finalizar_geracao(self, roteiro_id: int, arquivo_video: str, duracao: int) -> bool:
        """Finaliza a geração atualizando todos os status"""
        try:
            # ✅ CORREÇÃO: Primeiro salvar informações do vídeo
            success = self.roteiro_manager.salvar_info(
                roteiro_id=roteiro_id,
                arquivo_video=arquivo_video,
                duracao=duracao,
                video_gerado=True  # ✅ CORREÇÃO: Marcar como gerado aqui também
            )
            
            # ✅ CORREÇÃO: Depois marcar como video_gerado no banco
            if success:
                self.roteiro_manager.marcar_video_gerado(roteiro_id)
                print(f"✅ Vídeo gerado e salvo: {arquivo_video}")
                print(f"📊 Duração: {duracao} segundos")
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