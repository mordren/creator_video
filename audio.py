#!/usr/bin/env python3
import json
import sys
import argparse
from pathlib import Path

from video_maker.video_components import mixar_audio_voz_trilha

sys.path.append(str(Path(__file__).parent))

try:
    from read_config import carregar_config_canal
    from providers import create_tts_provider
    from crud import DatabaseManager
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

class AudioSystem:
    def __init__(self):
        self.db = DatabaseManager() if DatabaseManager else None

    def generate_audio(self, video_id: str, channel: str, provider: str = None) -> bool:
        """Gera áudio para um roteiro pelo video_id"""
        print(f"🎵 Gerando áudio para: {channel}/{video_id}")
        
        config = carregar_config_canal(channel)
        provider = provider or config.get('TTS_PROVIDER', 'edge')
        
        # Busca roteiro
        pasta_base = config['PASTA_BASE']
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
            self._update_apos_audio_sucesso(data, str(audio_file), str(mixado),provider, channel, config, arquivo_json)
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
            'arquivo_legenda': arquivo_legenda  # ✅ Adiciona info da legenda no JSON
        })
        
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("📁 Arquivo JSON atualizado")
        
        # ✅ APENAS atualiza banco se existir e áudio foi gerado
        if self.db:
            try:
                # Busca roteiro existente
                roteiro_existente = self.db.buscar_roteiro_por_id_video(data['id_video'])
                
                if roteiro_existente:
                    # ✅ ATUALIZA com informações completas do áudio E legenda
                    self.db.atualizar_roteiro_audio(
                        roteiro_existente.id,
                        audio_file,
                        provider,
                        voz_tts,
                        arquivo_legenda,
                        mixado  # ✅ Agora inclui o caminho do .srt
                    )
                    print("💾 Banco ATUALIZADO com informações do áudio (incluindo voz TTS e legenda)")
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