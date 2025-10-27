# crud/canal_manager.py
from sqlmodel import Session, select
from typing import List, Optional

from .models import Canal
from .connection import engine

class CanalManager:
    def __init__(self):
        self.engine = engine
    
    def criar(self, canal: Canal, config: dict) -> Canal:
        """Cria um novo canal no banco"""
        with Session(self.engine) as session:
            session.add(canal)
            session.commit()
            session.refresh(canal)
            return canal
    
    def buscar_por_nome(self, nome: str) -> Optional[Canal]:
        """Busca canal pelo nome"""
        with Session(self.engine) as session:
            statement = select(Canal).where(Canal.nome == nome)
            return session.exec(statement).first()
    
    def buscar_por_id(self, canal_id: int) -> Optional[Canal]:
        """Busca canal pelo ID"""
        with Session(self.engine) as session:
            return session.get(Canal, canal_id)
    
    def listar(self, apenas_ativos: bool = True) -> List[Canal]:
        """Lista todos os canais"""
        with Session(self.engine) as session:
            statement = select(Canal)
            if apenas_ativos:
                statement = statement.where(Canal.ativo == True)
            return session.exec(statement).all()
    
    def atualizar(self, canal_id: int, **dados) -> bool:
        """Atualiza qualquer campo do canal"""
        with Session(self.engine) as session:
            canal = session.get(Canal, canal_id)
            if not canal:
                return False
            
            for campo, valor in dados.items():
                if hasattr(canal, campo):
                    setattr(canal, campo, valor)
            
            session.commit()
            return True