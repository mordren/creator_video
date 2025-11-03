# crud/roteiro_manager.py
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from .models import Roteiro, Canal
from .connection import engine

class RoteiroManager:
    def __init__(self):
        self.engine = engine

    def criar(self, roteiro: Roteiro) -> Roteiro:
        """Cria um novo roteiro"""
        with Session(self.engine) as session:
            session.add(roteiro)
            session.commit()
            session.refresh(roteiro)
            return roteiro

    def buscar_por_id(self, roteiro_id: int) -> Optional[Roteiro]:
        """Busca roteiro pelo ID do banco"""
        with Session(self.engine) as session:
            return session.get(Roteiro, roteiro_id)

    def buscar_por_id_video(self, id_video: str) -> Optional[Roteiro]:
        """Busca roteiro pelo ID do vídeo (pasta)"""
        with Session(self.engine) as session:
            statement = select(Roteiro).where(Roteiro.id_video == id_video)
            return session.exec(statement).first()

    def listar(self, canal_id: Optional[int] = None) -> List[Roteiro]:
        """Lista todos os roteiros, opcionalmente filtrando por canal"""
        with Session(self.engine) as session:
            statement = select(Roteiro)
            if canal_id:
                statement = statement.where(Roteiro.canal_id == canal_id)
            return session.exec(statement).all()

    def atualizar(self, roteiro_id: int, **dados) -> bool:
        """Atualiza qualquer campo do roteiro"""
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)
            if not roteiro:
                return False

            for campo, valor in dados.items():
                if hasattr(roteiro, campo):
                    setattr(roteiro, campo, valor)

            session.commit()
            return True

    def marcar_audio_gerado(self, roteiro_id: int) -> bool:
        """Marca o áudio como gerado para o roteiro"""
        return self.atualizar(roteiro_id, audio_gerado=True)

    def marcar_video_gerado(self, roteiro_id: int) -> bool:
        """Marca o vídeo como gerado para o roteiro"""
        return self.atualizar(roteiro_id, video_gerado=True)

    def marcar_finalizado(self, roteiro_id: int) -> bool:
        """Marca o roteiro como finalizado"""
        return self.atualizar(roteiro_id, finalizado=True)

    def deletar(self, roteiro_id: int) -> bool:
        """Remove um roteiro do banco"""
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)
            if not roteiro:
                return False

            session.delete(roteiro)
            session.commit()
            return True
        
    def get_roteiro_completo(self, roteiro_id: int):
        """Busca roteiro com vídeo relacionado"""
        statement = select(Roteiro).where(Roteiro.id == roteiro_id)
        roteiro = self.session.exec(statement).first()
        return roteiro

    def update_roteiro(self, roteiro_id: int, data: dict):
        """Atualiza dados do roteiro"""
        roteiro = self.session.get(Roteiro, roteiro_id)
        if roteiro:
            for key, value in data.items():
                if hasattr(roteiro, key):
                    setattr(roteiro, key, value)
            self.session.commit()
            self.session.refresh(roteiro)
        return roteiro