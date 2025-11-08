# crud/roteiro_manager.py
from sqlmodel import Session, desc, select
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import Roteiro, Canal
from .connection import engine, get_session

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

    def atualizar(self, roteiro_id: int, **kwargs):
        """Atualiza um roteiro existente"""
        with Session(self.engine) as session:  # ✅ CORREÇÃO: Usar sessão de contexto
            roteiro = session.get(Roteiro, roteiro_id)
            if roteiro:
                for key, value in kwargs.items():
                    setattr(roteiro, key, value)
                session.commit()
                session.refresh(roteiro)
                return roteiro
            return None
    
    def get_all_Roteiros(self) -> List[Roteiro]:
        with Session(self.engine) as session:  # ✅ CORREÇÃO: Usar sessão de contexto
            stmt = select(Roteiro).order_by(desc(Roteiro.id))
            roteiros = session.exec(stmt).all()
            for roteiro in roteiros:
                if roteiro and hasattr(roteiro, 'canal_obj'):
                    roteiro.canal_obj
            return roteiros
    
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
        with Session(self.engine) as session:  # ✅ CORREÇÃO: Usar sessão de contexto
            statement = select(Roteiro).where(Roteiro.id == roteiro_id)
            roteiro = session.exec(statement).first()
            return roteiro

    def update_roteiro(self, roteiro_id: int, data: dict):
        """Atualiza dados do roteiro"""
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)            
            if roteiro:
                for key, value in data.items():
                    if hasattr(roteiro, key):
                        setattr(roteiro, key, value)
                session.commit()
                session.refresh(roteiro)
            return roteiro    

    def salvar_info_audio(self, 
                         roteiro_id: int, 
                         arquivo_audio: str, 
                         tts_provider: str, 
                         voz_tts: str, 
                         arquivo_legenda: str = None,
                         audio_mixado: str = None,
                         duracao: int = None) -> bool:
        """Salva informações do áudio gerado"""
        dados = {
            'arquivo_audio': arquivo_audio,
            'tts_provider': tts_provider,
            'voz_tts': voz_tts,
            'arquivo_legenda': arquivo_legenda,
            'audio_mixado': audio_mixado,
            'duracao': duracao
        }     
        dados = {k: v for k, v in dados.items() if v is not None}
        return self.salvar_info(roteiro_id, **dados)
    

    def salvar_info(self, roteiro_id: int, **dados: Dict[str, Any]) -> bool:
        """
        Salva ou atualiza informações do vídeo para um roteiro.
        Aceita qualquer campo do modelo Roteiro como argumento nomeado.
        """
        with Session(self.engine) as session:
            try:
                # Busca roteiro existente dentro da mesma sessão
                statement = select(Roteiro).where(Roteiro.id == roteiro_id)
                roteiro = session.exec(statement).first()
                
                if roteiro:
                    # Atualiza roteiro existente
                    print(f"📝 Atualizando roteiro existente (ID: {roteiro.id})")
                    for campo, valor in dados.items():
                        if hasattr(roteiro, campo):
                            setattr(roteiro, campo, valor)
                            print(f"   ✏️ {campo}: {valor}")
                else:
                    # Cria novo roteiro (caso não exista)
                    print(f"📝 Criando novo registro de roteiro (ID: {roteiro_id})")
                    roteiro = Roteiro(id=roteiro_id, **dados)
                    session.add(roteiro)
                    print(f"   ✏️ Campos: {list(dados.keys())}")
                
                session.commit()
                print("✅ Informações salvas com sucesso!")
                return True

            except Exception as e:
                session.rollback()
                print(f"❌ Erro ao salvar info roteiro: {e}")
                import traceback
                traceback.print_exc()
                return False