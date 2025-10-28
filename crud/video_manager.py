# crud/video_manager.py
from sqlmodel import Session, select
from typing import List, Optional
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
    
    def salvar(self, video: Video) -> Video:
        """Salva ou atualiza um vídeo existente"""
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
    
    def deletar(self, video: Video) -> bool:
        """Remove um vídeo do banco"""
        with Session(self.engine) as session:
            session.delete(video)
            session.commit()
            return True
    
    # --- Operações Específicas de Áudio ---
    def salvar_info_audio(self, 
                         roteiro_id: int, 
                         arquivo_audio: str, 
                         tts_provider: str, 
                         voz_tts: str, 
                         arquivo_legenda: str = None,
                         audio_mixado: str = None,
                         duracao: int = None) -> bool:
        """Salva todas as informações do áudio gerado"""
        with Session(self.engine) as session:
            try:
                # Busca vídeo existente ou cria novo
                video = self.buscar_por_roteiro_id(roteiro_id)
                
                if video:
                    # Atualiza vídeo existente
                    video.arquivo_audio = arquivo_audio
                    video.arquivo_legenda = arquivo_legenda
                    video.tts_provider = tts_provider
                    video.voz_tts = voz_tts
                    video.audio_mixado = audio_mixado
                    if duracao:
                        video.duracao = duracao
                else:
                    # Cria novo vídeo
                    video = Video(
                        roteiro_id=roteiro_id,
                        arquivo_audio=arquivo_audio,
                        arquivo_legenda=arquivo_legenda,
                        tts_provider=tts_provider,
                        voz_tts=voz_tts,
                        audio_mixado=audio_mixado,
                        duracao=duracao
                    )
                    session.add(video)
                
                session.commit()
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ Erro ao salvar info áudio: {e}")
                return False
    
    # --- Operações Específicas de Vídeo ---
    def salvar_info_video(
        self,
        roteiro_id: int,
        arquivo_video: str,
        duracao: int | None = None,                
    ) -> bool:
        """Salva informações do vídeo renderizado (inclui titulo e thumb)."""
        with Session(self.engine) as session:
            try:
                video = self.buscar_por_roteiro_id(roteiro_id)

                if video:
                    video.arquivo_video = arquivo_video
                    if duracao is not None:
                        video.duracao = duracao                    
                    session.commit()
                    return True
                else:
                    video = Video(
                        roteiro_id=roteiro_id,
                        arquivo_video=arquivo_video,
                        duracao=duracao,                                                
                    )
                    session.add(video)
                    session.commit()
                    return True

            except Exception as e:
                session.rollback()
                print(f"❌ Erro ao salvar info vídeo: {e}")
                return False
    
    def atualizar_status_upload(self, 
                              roteiro_id: int, 
                              status: str,
                              plataforma: str = "youtube") -> bool:
        """Atualiza status de upload para uma plataforma"""
        with Session(self.engine) as session:
            try:
                video = self.buscar_por_roteiro_id(roteiro_id)
                if video:
                    video.status_upload = status
                    session.commit()
                    return True
                return False
                
            except Exception as e:
                session.rollback()
                print(f"❌ Erro ao atualizar status upload: {e}")
                return False
    
    def atualizar_metricas(self, 
                          roteiro_id: int, 
                          visualizacao_total: int = None) -> bool:
        """Atualiza métricas do vídeo"""
        with Session(self.engine) as session:
            try:
                video = self.buscar_por_roteiro_id(roteiro_id)
                if video:
                    if visualizacao_total is not None:
                        video.visualizacao_total = visualizacao_total
                    session.commit()
                    return True
                return False
                
            except Exception as e:
                session.rollback()
                print(f"❌ Erro ao atualizar métricas: {e}")
                return False