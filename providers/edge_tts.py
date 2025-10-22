import asyncio
from pathlib import Path
from typing import Dict, Any
import edge_tts

from .base import TTSProvider

class EdgeTTSProvider(TTSProvider):
    """Provedor Microsoft Edge TTS - Gratuito e com suporte a legendas SRT"""
    
    def sintetizar(self, texto: str, output_path: Path, config: Dict[str, Any]) -> bool:
        try:
            voice = config.get('EDGE_TTS_VOICE', 'pt-BR-AntonioNeural')
            rate = config.get('EDGE_TTS_RATE', '0%')
            pitch = config.get('EDGE_TTS_PITCH', '0Hz')
            gerar_legendas = config.get('EDGE_TTS_LEGENDAS', True)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if gerar_legendas:
                srt_path = output_path.with_suffix('.srt')
                success = loop.run_until_complete(
                    self._gerar_audio_e_legendas(texto, output_path, srt_path, voice, rate, pitch)
                )
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