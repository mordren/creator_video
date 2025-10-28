from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
import json

from .models import Agendamento
from .connection import engine

class AgendamentoManager:
    def __init__(self):
        self.engine = engine

    def criar(self, agendamento: Agendamento) -> Agendamento:
        """Cria um novo agendamento"""
        with Session(self.engine) as session:
            session.add(agendamento)
            session.commit()
            session.refresh(agendamento)
            return agendamento

    def buscar_por_id(self, agendamento_id: int) -> Optional[Agendamento]:
        """Busca agendamento pelo ID"""
        with Session(self.engine) as session:
            return session.get(Agendamento, agendamento_id)

    def buscar_por_video_id(self, video_id: int) -> List[Agendamento]:
        """Busca todos os agendamentos de um vídeo"""
        with Session(self.engine) as session:
            statement = select(Agendamento).where(Agendamento.video_id == video_id)
            return session.exec(statement).all()

    def atualizar(self, agendamento_id: int, **dados) -> bool:
        """Atualiza um agendamento"""
        with Session(self.engine) as session:
            agendamento = session.get(Agendamento, agendamento_id)
            if not agendamento:
                return False

            for campo, valor in dados.items():
                if hasattr(agendamento, campo):
                    setattr(agendamento, campo, valor)
            agendamento.data_atualizacao = datetime.utcnow()

            session.commit()
            return True

    def deletar(self, agendamento_id: int) -> bool:
        """Remove um agendamento"""
        with Session(self.engine) as session:
            agendamento = session.get(Agendamento, agendamento_id)
            if not agendamento:
                return False

            session.delete(agendamento)
            session.commit()
            return True

    def deletar_por_video_id(self, video_id: int) -> bool:
        """Remove todos os agendamentos de um vídeo"""
        with Session(self.engine) as session:
            agendamentos = self.buscar_por_video_id(video_id)
            for agendamento in agendamentos:
                session.delete(agendamento)
            session.commit()
            return True