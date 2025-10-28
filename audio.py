# audio.py (apenas shorts terão otimização de áudio)

#!/usr/bin/env python3
import json
import sys
import argparse
import subprocess
from pathlib import Path

from video_maker.video_utils import mixar_audio_com_musica

sys.path.append(str(Path(__file__).parent))

try:
    from read_config import carregar_config_canal
    from providers import create_tts_provider
    from crud.roteiro_manager import RoteiroManager
    from crud.video_manager import VideoManager
    from crud.canal_manager import CanalManager
    # ✅ NOVA IMPORTAÇÃO
    from utils import otimizar_audio_e_legenda, vertical_horizontal
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

class AudioSystem:
    def __init__(self):
        self.roteiro_manager = RoteiroManager()
        self.video_manager = VideoManager()
        self.canal_manager = CanalManager()

    def _get_audio_duration(self, audio_path: str) -> int:
        """Obtém a duração do áudio em segundos"""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", audio_path
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            return int(float(result.stdout.strip()))
        except Exception as e:
            print(f"⚠️ Erro ao obter duração do áudio: {e}")
            return 0

    def generate_audio(self, roteiro_id: int, provider: str = None) -> bool:
        """Gera áudio para um roteiro pelo ID do banco"""
        print(f"🎵 Gerando áudio para roteiro ID: {roteiro_id}")
        
        # Busca roteiro no banco
        roteiro = self.roteiro_manager.buscar_por_id(roteiro_id)
        if not roteiro:
            print(f"❌ Roteiro com ID {roteiro_id} não encontrado")
            return False
        
        # Busca canal para obter configuração
        canal = self.canal_manager.buscar_por_id(roteiro.canal_id)
        if not canal:
            print(f"❌ Canal com ID {roteiro.canal_id} não encontrado")
            return False
        
        config = carregar_config_canal(canal.config_path)
        provider = provider or config.get('TTS_PROVIDER', 'edge')
        
        # ✅ CORREÇÃO: Usa id_video do roteiro para construir o caminho
        pasta_base = Path(config['PASTA_BASE'])
        pasta_video = pasta_base / roteiro.id_video  # ← id_video é o nome da pasta
        arquivo_json = pasta_video / f"{roteiro.id_video}.json"
        
        if not arquivo_json.exists():
            print(f"❌ Arquivo não encontrado: {arquivo_json}")
            return False
        
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extrai texto
        lang = data.get('idioma', config.get('IDIOMA', 'pt'))
        text = data.get(f"texto_{lang}") or data.get('texto', '')
        
        if not text or len(text.strip()) < 10:
            print("❌ Texto muito curto ou vazio")
            return False
        
        # Gera áudio
        audio_file = pasta_video / f"{roteiro.id_video}.mp3"
        print(f"📝 {len(text)} chars | 🔊 {provider} | 📺 {data.get('titulo', 'Sem título')}")
        print(f"📁 Pasta: {pasta_video}")
                
        tts = create_tts_provider(provider)
        success = tts.sintetizar(text, audio_file, config)
        
        # ✅ MODIFICADO: Otimizar áudio APENAS para shorts (vídeos verticais)
        srt_file = None
        if provider == "edge" and config.get('EDGE_TTS_LEGENDAS', False):
            srt_file = Path(audio_file).with_suffix('.srt')
        
        # Verifica se é short (vertical) antes de otimizar
        resolucao = data.get('resolucao', config.get('RESOLUCAO', '1920x1080'))
        is_short = (vertical_horizontal(resolucao) == "vertical")
        
        if success and audio_file.exists() and is_short:
            print("🎵 Otimizando áudio para short (cortando pausas longas)...")
            audio_otimizado, srt_ajustado = otimizar_audio_e_legenda(str(audio_file), str(srt_file) if srt_file else None)
            
            # Usa o áudio otimizado se foi criado
            if audio_otimizado != str(audio_file):
                audio_file = Path(audio_otimizado)
                if srt_ajustado:
                    srt_file = Path(srt_ajustado)
        elif success and audio_file.exists() and not is_short:
            print("ℹ️  Otimização de áudio skipped (não é short)")
        
        # ✅ CORRIGIDO: Mixar com música de fundo com nome correto
        arquivo_mixado = pasta_video / f"{roteiro.id_video}_com_musica.mp3"
        musica_path = config.get('MUSICA')
        
        if musica_path and Path(musica_path).exists():
            print("🎵 Mixando áudio com música...")
            
            # Se já existe um arquivo mixado, remove antes de criar novo
            if arquivo_mixado.exists():
                arquivo_mixado.unlink()
                
            # Chama a função de mixagem
            mixado_temp = mixar_audio_com_musica(audio_file, musica_path)
            
            # ✅ CORREÇÃO: Renomeia para o nome padrão se necessário
            if mixado_temp != str(arquivo_mixado):
                Path(mixado_temp).rename(arquivo_mixado)
                print(f"✅ Áudio mixado renomeado para: {arquivo_mixado}")
            else:
                print(f"✅ Áudio mixado: {arquivo_mixado}")
        else:
            print("ℹ️  Nenhuma música configurada ou arquivo não encontrado")
            arquivo_mixado = audio_file

        if success and audio_file.exists():
            self._update_apos_audio_sucesso(roteiro, data, str(audio_file), str(arquivo_mixado), provider, config, arquivo_json, srt_file, is_short)
            print(f"✅ Áudio gerado{' e otimizado' if is_short else ''}: {audio_file}")
            print(f"✅ Áudio mixado: {arquivo_mixado}")
            return True
        
        print("❌ Falha na geração")
        return False

    def _update_apos_audio_sucesso(self, roteiro, data: dict, audio_file: str, mixado: str, provider: str, config: dict, arquivo_json: Path, srt_file: Path = None, is_short: bool = False):
        """Atualiza APENAS se o áudio foi gerado com sucesso"""
        
        # Obtém a voz TTS baseada no provider
        voz_tts = None
        if provider == "edge":
            voz_tts = config.get('EDGE_TTS_VOICE', 'N/A')
        elif provider == "gemini":
            voz_tts = config.get('GEMINI_TTS_VOICE', 'N/A')
        else:
            voz_tts = f"{provider}_voice"
        
        # ✅ ATUALIZADO: Usa SRT ajustado se disponível (apenas para shorts)
        arquivo_legenda = None
        if srt_file and srt_file.exists():
            arquivo_legenda = str(srt_file)
            print(f"📝 Legenda SRT {'otimizada' if is_short else 'original'}: {srt_file}")
        elif provider == "edge" and config.get('EDGE_TTS_LEGENDAS', False):
            srt_path = Path(audio_file).with_suffix('.srt')
            if srt_path.exists():
                arquivo_legenda = str(srt_path)
                print(f"📝 Legenda SRT original: {srt_path}")

        # Atualiza JSON
        data.update({
            'audio_gerado': True,
            'arquivo_audio': audio_file,
            'tts_provider': provider,
            'voz_tts': voz_tts,
            'arquivo_legenda': arquivo_legenda,
            'audio_otimizado': is_short  # ✅ NOVO: indica se foi otimizado
        })
        
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("📁 Arquivo JSON atualizado")
        
        try:
            print(f"🔄 Atualizando roteiro: {roteiro.id}")
            
            # Marca áudio como gerado no roteiro
            self.roteiro_manager.marcar_audio_gerado(roteiro.id)
            
            # Obtém duração do áudio mixado
            duracao = self._get_audio_duration(mixado)
            
            # Salva informações do áudio usando o VideoManager
            success = self.video_manager.salvar_info_audio(
                roteiro_id=roteiro.id,
                arquivo_audio=audio_file,
                tts_provider=provider,
                voz_tts=voz_tts,
                arquivo_legenda=arquivo_legenda,
                audio_mixado=mixado if mixado != audio_file else None,
                duracao=duracao
            )
            
            if success:
                print("💾 Banco atualizado com sucesso!")
            else:
                print("❌ Falha ao salvar informações de áudio no banco")
                    
        except Exception as e:
            print(f"⚠️ Erro ao atualizar banco: {e}")

def main():
    parser = argparse.ArgumentParser(description='Gerar áudio para roteiros')
    parser.add_argument('roteiro_id', type=int, help='ID do roteiro no banco')
    parser.add_argument('--provider', help='Provedor TTS (edge, gemini)')
    
    args = parser.parse_args()
    
    success = AudioSystem().generate_audio(args.roteiro_id, args.provider)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()