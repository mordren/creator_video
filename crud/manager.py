# crud/manager.py
from .roteiro_manager import RoteiroManager
from .video_manager import VideoManager
from .canal_manager import CanalManager

class DatabaseManager:
    """Manager unificado para compatibilidade com código existente"""
    
    def __init__(self):
        self.roteiros = RoteiroManager()
        self.videos = VideoManager()
        self.canais = CanalManager()
    
    # Métodos de compatibilidade para código legado
    def criar_roteiro(self, **kwargs):
        from .models import Roteiro
        roteiro = Roteiro(**kwargs)
        return self.roteiros.criar(roteiro)
    
    def buscar_roteiro_por_id_video(self, id_video: str):
        return self.roteiros.buscar_por_id_video(id_video)
    
    def atualizar_roteiro_audio(self, roteiro_id: int, arquivo_audio: str, tts_provider: str, 
                               voz_tts: str, arquivo_legenda: str = None, audio_mixado: str = None):
        return self.videos.salvar_info_audio(
            roteiro_id, arquivo_audio, tts_provider, voz_tts, arquivo_legenda, audio_mixado
        )
    
    