# providers/gemini_tts.py
import os
import sys
import base64
import wave
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ Biblioteca do Gemini não encontrada. Instale com: pip install google-genai")

from .base_audio import TTSProvider

class GeminiTTSProvider(TTSProvider):
    """Provedor Google Gemini TTS"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não encontrada")
    
    def sintetizar(self, texto: str, output_path: Path, config: Dict[str, Any]) -> bool:
        """Sintetiza áudio usando Gemini TTS"""
        try:
            voz = config.get('GEMINI_TTS_VOICE', 'Algenib')
            modelo = config.get('GEMINI_TTS_MODEL', 'gemini-2.5-flash-preview-tts')
            
            client = genai.Client(api_key=self.api_key)
            
            print(f"🔊 Gerando áudio Gemini TTS com voz: {voz}")
            
            resp = client.models.generate_content(
                model=modelo,
                contents=texto,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voz
                            )
                        )
                    ),
                ),
            )

            # Extrai o áudio
            data = resp.candidates[0].content.parts[0].inline_data.data
            pcm = self._to_pcm_bytes(data)

            # Salva como WAV temporário
            temp_wav = str(output_path.with_suffix('.wav'))
            self._wave_file(temp_wav, pcm)

            # Converte para MP3
            try:
                self._wav_to_mp3_ffmpeg(temp_wav, str(output_path))
                print(f"✅ MP3 salvo: {output_path}")
                os.remove(temp_wav)
            except Exception as e:
                print(f"⚠️ FFmpeg indisponível? Mantendo WAV. Detalhe: {e}")
                os.rename(temp_wav, str(output_path))

            return True

        except Exception as e:
            print(f"❌ Erro no Gemini TTS: {e}")
            return False

    def _wave_file(self, filename: str, pcm, channels=1, rate=24000, sample_width=2):
        """Salva dados PCM em arquivo WAV"""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)

    def _to_pcm_bytes(self, data):
        """Converte dados de áudio para bytes PCM"""
        if isinstance(data, (bytes, bytearray)):
            return data
        if isinstance(data, str):
            return base64.b64decode(data)
        raise TypeError(f"Tipo inesperado para audio inline_data: {type(data)}")

    def _wav_to_mp3_ffmpeg(self, wav_in: str, mp3_out: str, bitrate="192k"):
        """Converte WAV para MP3 usando FFmpeg"""
        if not shutil.which("ffmpeg"):
            raise RuntimeError("FFmpeg não encontrado no PATH.")
        
        result = subprocess.run([
            "ffmpeg", "-y", "-i", wav_in,
            "-c:a", "libmp3lame", "-b:a", bitrate, mp3_out
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr}")