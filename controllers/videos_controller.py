

from crud.roteiro_manager import RoteiroManager

class VideosController:
    def __init__(self):
        self.roteiro = RoteiroManager()

    def list_roteiros(self):
        """Lista todos os vídeos - usa método existente"""
        return self.roteiro.get_all_Roteiros()
    
    def delete_video(self, video_id: int) -> bool:
        return self.roteiro.deletar(video_id)