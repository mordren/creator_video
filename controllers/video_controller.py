# video_controller.py
from typing import Dict, Any
from crud.roteiro_manager import RoteiroManager

class VideoController:
    def __init__(self):
        self.roteiro_manager = RoteiroManager()

    def get_roteiro(self, roteiro_id: int):
        """Retorna vídeo com roteiro carregado"""
        return self.roteiro_manager.buscar_por_id(roteiro_id)

    def update_roteiro_and_video(self, roteiro_id: int, roteiro_data: Dict[str, Any]) -> bool:
        """Atualiza o Roteiro usando dados já validados (rota faz o parse)."""
        roteiro = self.get_roteiro(roteiro_id)
        if not roteiro:
            raise ValueError("Vídeo não encontrado")

        # dados já vêm limpos do validator
        self.roteiro_manager.atualizar(roteiro.id, **roteiro_data)
        return True
