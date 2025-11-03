# video_controller.py
from crud.video_manager import VideoManager
from crud.roteiro_manager import RoteiroManager
from typing import Dict, Any

class VideoController:
    def __init__(self):
        self.video_manager = VideoManager()
        self.roteiro_manager = RoteiroManager()

    def get_video(self, roteiro_id: int):
        """Retorna vídeo com roteiro carregado"""
        return self.video_manager.get_video_by_roteiro(roteiro_id)
    
    def update_roteiro_and_video(self, roteiro_id: int, form_data: Dict[str, Any]):
        """Atualiza roteiro e vídeo com dados do formulário"""
        video = self.get_video(roteiro_id)
        
        if not video:
            raise ValueError("Vídeo não encontrado")
        
        # Dados do roteiro
        roteiro_data = {
            'titulo': form_data.get('titulo'),
            'id_video': form_data.get('id_video'),
            'texto': form_data.get('texto'),
            'descricao': form_data.get('descricao'),
            'tags': form_data.get('tags'),
            'audio_gerado': form_data.get('audio_gerado') == 'true',
            'video_gerado': form_data.get('video_gerado') == 'true',
            'finalizado': form_data.get('finalizado') == 'true'
        }
        
        # Remove valores None
        roteiro_data = {k: v for k, v in roteiro_data.items() if v is not None}
        
        # Atualiza roteiro
        self.roteiro_manager.atualizar(video.roteiro.id, **roteiro_data)
        
        # Dados do vídeo
        video_data = {
            'status_upload': form_data.get('status_upload'),
            'duracao': int(form_data.get('duracao')) if form_data.get('duracao') else None,
            'tts_provider': form_data.get('tts_provider'),
            'voz_tts': form_data.get('voz_tts'),
            'visualizacao_total': int(form_data.get('visualizacao_total')) if form_data.get('visualizacao_total') else 0,
            'arquivo_audio': form_data.get('arquivo_audio'),
            'arquivo_video': form_data.get('arquivo_video'),
            'arquivo_legenda': form_data.get('arquivo_legenda'),
            'audio_mixado': form_data.get('audio_mixado')
        }
        
        # Remove valores None
        video_data = {k: v for k, v in video_data.items() if v is not None}
        self.video_manager.update_video(video.id, video_data)
        
        return True