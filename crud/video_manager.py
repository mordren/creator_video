# crud/video_manager.py
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import Video, Roteiro
from .connection import engine

class VideoManager:
    def __init__(self):
        self.engine = engine
    
    # --- CRUD Básico ---
    def criar(self, video: Video) -> Video:
        """Cria um novo vídeo a partir de um objeto Video"""
        with Session(self.engine) as session:
            session.add(video)
            session.commit()
            session.refresh(video)
            return video
    
    def buscar_por_id(self, video_id: int) -> Optional[Video]:
        """Busca vídeo pelo ID do banco"""
        with Session(self.engine) as session:
            return session.get(Video, video_id)
    
    def buscar_por_roteiro_id(self, roteiro_id: int) -> Optional[Video]:
        """Busca vídeo associado a um roteiro específico"""
        with Session(self.engine) as session:
            statement = select(Video).where(Video.roteiro_id == roteiro_id)
            return session.exec(statement).first()
    
    def deletar(self, video_id: int) -> bool:
        """Remove um vídeo do banco"""
        with Session(self.engine) as session:
            video = session.get(Video, video_id)
            if video:
                session.delete(video)
                session.commit()
                return True
            return False
    
    # --- MÉTODO GENÉRICO PRINCIPAL ---
    def salvar_info(self, roteiro_id: int, **dados: Dict[str, Any]) -> bool:
        """
        Salva ou atualiza informações do vídeo para um roteiro.
        Aceita qualquer campo do modelo Video como argumento nomeado.
        """
        with Session(self.engine) as session:
            try:
                # Busca vídeo existente dentro da mesma sessão
                statement = select(Video).where(Video.roteiro_id == roteiro_id)
                video = session.exec(statement).first()
                
                if video:
                    # Atualiza vídeo existente
                    print(f"📹 Atualizando vídeo existente (ID: {video.id})")
                    for campo, valor in dados.items():
                        if hasattr(video, campo):
                            setattr(video, campo, valor)
                            print(f"   📝 {campo}: {valor}")
                else:
                    # Cria novo vídeo
                    print(f"📹 Criando novo registro de vídeo para roteiro {roteiro_id}")
                    video = Video(roteiro_id=roteiro_id, **dados)
                    session.add(video)
                    print(f"   📝 Campos: {list(dados.keys())}")
                
                session.commit()
                print("✅ Informações salvas com sucesso!")
                return True

            except Exception as e:
                session.rollback()
                print(f"❌ Erro ao salvar info vídeo: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    # --- MÉTODOS ESPECÍFICOS (agora são apenas wrappers do método genérico) ---
    
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
        # Remove None values para não sobrescrever com None
        dados = {k: v for k, v in dados.items() if v is not None}
        return self.salvar_info(roteiro_id, **dados)
    
    def salvar_info_video(self,
                         roteiro_id: int,
                         arquivo_video: str,
                         duracao: int = None) -> bool:
        """Salva informações do vídeo renderizado"""
        dados = {
            'arquivo_video': arquivo_video,
            'duracao': duracao
        }
        dados = {k: v for k, v in dados.items() if v is not None}
        return self.salvar_info(roteiro_id, **dados)
    
    def atualizar_status_upload(self, 
                              roteiro_id: int, 
                              status: str,
                              plataforma: str = "youtube") -> bool:
        """Atualiza status de upload para uma plataforma"""
        return self.salvar_info(roteiro_id, status_upload=status)
    
    def atualizar_metricas(self, 
                          roteiro_id: int, 
                          visualizacao_total: int = None) -> bool:
        """Atualiza métricas do vídeo"""
        return self.salvar_info(roteiro_id, visualizacao_total=visualizacao_total)