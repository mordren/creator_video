import asyncio
from pathlib import Path
from typing import Dict, Any
import edge_tts

from .base_audio import TTSProvider
# CORREÇÃO: Importar do video_utils (que está no diretório raiz)
from video_maker.video_utils import ajustar_timestamps_srt, analisar_gaps_srt

class EdgeTTSProvider(TTSProvider):
    """Provedor Microsoft Edge TTS - Gratuito e com suporte a legendas SRT"""
    
    def sintetizar(self, texto: str, output_path: Path, config: Dict[str, Any]) -> bool:
        try:
            voice = config.get('EDGE_TTS_VOICE', 'pt-BR-AntonioNeural')
            rate = config.get('EDGE_TTS_RATE', '0%')
            pitch = config.get('EDGE_TTS_PITCH', '0Hz')
            gerar_legendas = config.get('EDGE_TTS_LEGENDAS', True)
            ajustar_timestamps = config.get('EDGE_TTS_AJUSTAR_TIMESTAMPS', True)  # Nova configuração
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if gerar_legendas:
                srt_path = output_path.with_suffix('.srt')
                success = loop.run_until_complete(
                    self._gerar_audio_e_legendas(texto, output_path, srt_path, voice, rate, pitch)
                )
                
                # Ajustar timestamps se configurado
                if success and ajustar_timestamps:
                    self._ajustar_legendas_apos_geracao(srt_path)
            else:
                success = loop.run_until_complete(
                    self._gerar_apenas_audio(texto, output_path, voice, rate, pitch)
                )
            
            loop.close()
            
            if success:
                print(f"✅ Áudio Edge TTS gerado: {output_path}")
                if gerar_legendas:
                    print(f"✅ Legendas SRT geradas: {srt_path}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Erro no Edge TTS: {e}")
            return False
    
    def _ajustar_legendas_apos_geracao(self, srt_path: Path):
        """
        Ajusta os timestamps das legendas após a geração para remover gaps
        """
        try:
            if not srt_path.exists():
                print(f"❌ Arquivo de legenda não encontrado: {srt_path}")
                return
            
            print("🔧 Analisando gaps nas legendas geradas...")
            analise = analisar_gaps_srt(str(srt_path))
            
            if analise['total_gaps'] > 0:
                print(f"📊 Detectados {analise['total_gaps']} gaps totalizando {analise['tempo_total_gaps_segundos']:.2f}s")
                
                # Criar backup antes de ajustar
                backup_path = srt_path.with_suffix('.srt.backup')
                import shutil
                shutil.copy2(srt_path, backup_path)
                
                # Ajustar timestamps
                arquivo_ajustado = ajustar_timestamps_srt(str(srt_path), str(srt_path))
                
                print(f"✅ Legendas ajustadas: {arquivo_ajustado}")
                print(f"💾 Backup salvo em: {backup_path}")
            else:
                print("✅ Nenhum gap significativo detectado nas legendas")
                
        except Exception as e:
            print(f"❌ Erro ao ajustar legendas: {e}")
    
    async def _gerar_audio_e_legendas(self, texto: str, mp3_path: Path, srt_path: Path, 
                                    voice: str, rate: str, pitch: str) -> bool:
        communicate = edge_tts.Communicate(texto, voice=voice, rate=rate, pitch=pitch)
        sub = edge_tts.SubMaker()
        
        with open(mp3_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    sub.feed(chunk)
        
        srt_content = sub.get_srt()
        srt_path.write_text(srt_content, encoding="utf-8")
        return True
    
    async def _gerar_apenas_audio(self, texto: str, mp3_path: Path, 
                                voice: str, rate: str, pitch: str) -> bool:
        communicate = edge_tts.Communicate(texto, voice=voice, rate=rate, pitch=pitch)
        
        with open(mp3_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
        return True