#!/usr/bin/env python3
import json
import sys
import argparse
import subprocess
from pathlib import Path

from video_maker.video_utils import mixar_audio_voz_trilha

sys.path.append(str(Path(__file__).parent))

try:
    from read_config import carregar_config_canal
    from providers import create_tts_provider
    from crud.roteiro_manager import RoteiroManager
    from crud.video_manager import VideoManager
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

class AudioSystem:
    def __init__(self):
        self.roteiro_manager = RoteiroManager()
        self.video_manager = VideoManager()

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

    def generate_audio(self, video_id: str, channel: str, provider: str = None) -> bool:
        """Gera áudio para um roteiro pelo video_id"""
        print(f"🎵 Gerando áudio para: {channel}/{video_id}")
        
        config = carregar_config_canal(channel)
        provider = provider or config.get('TTS_PROVIDER', 'edge')
        
        # Busca roteiro
        pasta_base = Path(config['PASTA_BASE'])
        pasta_video = pasta_base / video_id
        arquivo_json = pasta_video / f"{video_id}.json"
        
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
        audio_file = pasta_video / f"{video_id}.mp3"
        print(f"📝 {len(text)} chars | 🔊 {provider} | 📺 {data.get('titulo', 'Sem título')}")
                
        tts = create_tts_provider(provider)
        success = tts.sintetizar(text, audio_file, config)
        
        mixado = mixar_audio_voz_trilha(audio_file, config.get('MUSICA'))

        if mixado.exists() and success and audio_file.exists():
            self._update_apos_audio_sucesso(data, str(audio_file), str(mixado), provider, channel, config, arquivo_json)
            print(f"✅ Áudio gerado: {audio_file}")
            return True
        
        print("❌ Falha na geração")
        return False

    def _update_apos_audio_sucesso(self, data: dict, audio_file: str, mixado: str, provider: str, channel: str, config: dict, arquivo_json: Path):
        """Atualiza APENAS se o áudio foi gerado com sucesso"""
        
        # Obtém a voz TTS baseada no provider
        voz_tts = None
        if provider == "edge":
            voz_tts = config.get('EDGE_TTS_VOICE', 'N/A')
        elif provider == "gemini":
            voz_tts = config.get('GEMINI_TTS_VOICE', 'N/A')
        else:
            voz_tts = f"{provider}_voice"
        
        # ✅ VERIFICA SE EXISTE ARQUIVO .SRT (apenas para Edge TTS com legendas habilitadas)
        arquivo_legenda = None
        if provider == "edge" and config.get('EDGE_TTS_LEGENDAS', False):
            srt_path = Path(audio_file).with_suffix('.srt')
            if srt_path.exists():
                arquivo_legenda = str(srt_path)
                print(f"📝 Legenda SRT encontrada: {srt_path}")

        # Atualiza JSON
        data.update({
            'audio_gerado': True,
            'arquivo_audio': audio_file,
            'tts_provider': provider,
            'voz_tts': voz_tts,
            'arquivo_legenda': arquivo_legenda
        })
        
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("📁 Arquivo JSON atualizado")
        
        # ✅ ABORDAGEM COM MANAGERS ESPECÍFICOS
        try:
            # Busca roteiro existente
            roteiro = self.roteiro_manager.buscar_por_id_video(data['id_roteiro'])
            
            if roteiro:
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
                    audio_mixado=mixado,
                    duracao=duracao
                )
                
                if success:
                    print("💾 Banco atualizado com sucesso usando managers específicos!")
                else:
                    print("❌ Falha ao salvar informações de áudio no banco")
                    
            else:
                print("⚠️ Roteiro não encontrado no banco - não foi criado pelo texto.py?")
                    
        except Exception as e:
            print(f"⚠️ Erro ao atualizar banco: {e}")

def main():
    parser = argparse.ArgumentParser(description='Gerar áudio para roteiros')
    parser.add_argument('canal', help='Nome do canal')
    parser.add_argument('video_id', help='ID do vídeo')
    parser.add_argument('--provider', help='Provedor TTS (edge, gemini)')
    
    args = parser.parse_args()
    
    success = AudioSystem().generate_audio(args.video_id, args.canal, args.provider)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()