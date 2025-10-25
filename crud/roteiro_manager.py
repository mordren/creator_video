# crud/roteiro_manager.py
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import Roteiro, Canal
from .connection import engine

class RoteiroManager:
    def __init__(self):
        self.engine = engine
    
    # --- CRUD Básico ---
    def criar(self, roteiro: Roteiro) -> Roteiro:
        """Cria um novo roteiro a partir de um objeto Roteiro"""
        with Session(self.engine) as session:
            session.add(roteiro)
            session.commit()
            session.refresh(roteiro)
            return roteiro
    
    def salvar(self, roteiro: Roteiro) -> Roteiro:
        """Salva ou atualiza um roteiro existente"""
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
        """Busca roteiro pelo ID do vídeo (campo único)"""
        with Session(self.engine) as session:
            statement = select(Roteiro).where(Roteiro.id_video == id_video)
            return session.exec(statement).first()
    
    def listar_por_canal(self, canal_nome: str, limit: int = 100) -> List[Roteiro]:
        """Lista roteiros de um canal específico"""
        with Session(self.engine) as session:
            statement = select(Roteiro).join(Canal).where(
                Canal.nome == canal_nome
            ).order_by(Roteiro.data_criacao.desc()).limit(limit)
            return session.exec(statement).all()
    
    def deletar(self, roteiro: Roteiro) -> bool:
        """Remove um roteiro do banco"""
        with Session(self.engine) as session:
            session.delete(roteiro)
            session.commit()
            return True
    
    # --- Operações de Status ---
    def marcar_audio_gerado(self, roteiro_id: int) -> bool:
        """Marca que o áudio foi gerado para este roteiro"""
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)
            if roteiro:
                roteiro.audio_gerado = True
                session.commit()
                return True
            return False
    
    def marcar_video_gerado(self, roteiro_id: int) -> bool:
        """Marca que o vídeo foi gerado para este roteiro"""
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)
            if roteiro:
                roteiro.video_gerado = True
                session.commit()
                return True
            return False
    
    def marcar_finalizado(self, roteiro_id: int) -> bool:
        """Marca que o roteiro foi finalizado"""
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)
            if roteiro:
                roteiro.finalizado = True
                session.commit()
                return True
            return False
    
    # --- Estatísticas ---
    def estatisticas_canal(self, canal_nome: str) -> Dict[str, Any]:
        """Estatísticas de roteiros por canal"""
        roteiros = self.listar_por_canal(canal_nome)
        total_roteiros = len(roteiros)
        com_audio = len([r for r in roteiros if r.audio_gerado])
        com_video = len([r for r in roteiros if r.video_gerado])
        finalizados = len([r for r in roteiros if r.finalizado])
        
        return {
            "total_roteiros": total_roteiros,
            "roteiros_com_audio": com_audio,
            "roteiros_com_video": com_video,
            "roteiros_finalizados": finalizados,
            "taxa_audio": f"{(com_audio/total_roteiros)*100:.1f}%" if total_roteiros > 0 else "0%",
            "taxa_video": f"{(com_video/total_roteiros)*100:.1f}%" if total_roteiros > 0 else "0%",
            "taxa_finalizados": f"{(finalizados/total_roteiros)*100:.1f}%" if total_roteiros > 0 else "0%"
        }