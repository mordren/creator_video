from sqlmodel import Session, select, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

# Importa do mesmo pacote
from .models import Roteiro, Canal, Video, VideoYouTube, VideoTikTok, StatusUpload
# Importa a conexão centralizada
from .connection import engine, criar_tabelas, get_session

class DatabaseManager:
    def __init__(self, db_url: str = None):
        # Usa a engine centralizada
        self.engine = engine
        # Garante que as tabelas existem
        criar_tabelas()
    
    def __enter__(self):
        self.session = get_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    # --- Operações para Canais ---
    def criar_canal(self, nome: str, config_path: str) -> Canal:
        with Session(self.engine) as session:
            canal = Canal(nome=nome, config_path=config_path)
            session.add(canal)
            session.commit()
            session.refresh(canal)
            return canal
    
    def buscar_canal_por_nome(self, nome: str) -> Optional[Canal]:
        with Session(self.engine) as session:
            statement = select(Canal).where(Canal.nome == nome)
            return session.exec(statement).first()
    
    def listar_canais(self, apenas_ativos: bool = True) -> List[Canal]:
        with Session(self.engine) as session:
            statement = select(Canal)
            if apenas_ativos:
                statement = statement.where(Canal.ativo == True)
            return session.exec(statement).all()
    
    # --- Operações para Roteiros ---
    def criar_roteiro(self, 
                    id_video: str,
                    titulo: str,
                    texto: str,
                    descricao: str,
                    tags: str,
                    thumb: str,
                    canal_id: int,
                    resolucao: str = "vertical") -> Roteiro:
        
        with Session(self.engine) as session:
            roteiro = Roteiro(
                id_video=id_video,
                titulo=titulo,
                texto=texto,
                descricao=descricao,
                tags=tags,
                thumb=thumb,
                canal_id=canal_id,
                resolucao=resolucao
            )
            
            session.add(roteiro)
            session.commit()
            session.refresh(roteiro)
            return roteiro
        
    def buscar_roteiro_por_id_video(self, id_video: str) -> Optional[Roteiro]:
        """Busca roteiro pelo ID único do vídeo"""
        with Session(self.engine) as session:
            statement = select(Roteiro).where(Roteiro.id_video == id_video)
            return session.exec(statement).first()
        
    def buscar_roteiro(self, roteiro_id: int) -> Optional[Roteiro]:
        with Session(self.engine) as session:
            return session.get(Roteiro, roteiro_id)
    
    def buscar_roteiro_por_db_id(self, db_id: int) -> Optional[Roteiro]:
        """Busca roteiro pelo ID do banco de dados"""
        with Session(self.engine) as session:
            return session.get(Roteiro, db_id)
    
    def buscar_roteiros_por_canal(self, canal_nome: str, limit: int = 100) -> List[Roteiro]:
        with Session(self.engine) as session:
            statement = select(Roteiro).join(Canal).where(
                Canal.nome == canal_nome
            ).order_by(Roteiro.data_criacao.desc()).limit(limit)
            return session.exec(statement).all()
    
    def atualizar_status_audio_roteiro(self, roteiro_id: int, audio_gerado: bool = True) -> bool:
        """Atualiza apenas o status de áudio do roteiro"""
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)
            if roteiro:
                roteiro.audio_gerado = audio_gerado
                session.commit()
                return True
            return False
    
    def atualizar_status_video_roteiro(self, roteiro_id: int, video_gerado: bool = True) -> bool:
        """Atualiza apenas o status de vídeo do roteiro"""
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)
            if roteiro:
                roteiro.video_gerado = video_gerado
                session.commit()
                return True
            return False
    
    # --- Operações para Vídeos ---
    def criar_video(self,
                   roteiro_id: int,
                   titulo: Optional[str] = None,
                   thumb: Optional[str] = None,
                   arquivo_audio: Optional[str] = None,
                   arquivo_legenda: Optional[str] = None,
                   arquivo_video: Optional[str] = None,
                   audio_mixado: Optional[str] = None,
                   tts_provider: Optional[str] = None,
                   voz_tts: Optional[str] = None,
                   duracao: Optional[int] = None) -> Video:
        
        with Session(self.engine) as session:
            video = Video(
                roteiro_id=roteiro_id,
                titulo=titulo,
                thumb=thumb,
                arquivo_audio=arquivo_audio,
                arquivo_legenda=arquivo_legenda,
                arquivo_video=arquivo_video,
                audio_mixado=audio_mixado,
                tts_provider=tts_provider,
                voz_tts=voz_tts,
                duracao=duracao
            )
            
            session.add(video)
            session.commit()
            session.refresh(video)
            return video
    
    def buscar_video_por_roteiro_id(self, roteiro_id: int) -> Optional[Video]:
        """Busca vídeo pelo ID do roteiro associado"""
        with Session(self.engine) as session:
            statement = select(Video).where(Video.roteiro_id == roteiro_id)
            return session.exec(statement).first()
    
    def atualizar_video_audio(self, 
                            roteiro_id: int, 
                            arquivo_audio: str, 
                            tts_provider: str, 
                            voz_tts: str, 
                            arquivo_legenda: str = None,
                            duracao: int = None) -> bool:
        """Atualiza informações de áudio do vídeo"""
        with Session(self.engine) as session:
            video = self.buscar_video_por_roteiro_id(roteiro_id)
            if not video:
                # Cria um novo vídeo se não existir
                roteiro = session.get(Roteiro, roteiro_id)
                if roteiro:
                    video = Video(
                        roteiro_id=roteiro_id,
                        titulo=roteiro.titulo,
                        thumb=roteiro.thumb,
                        arquivo_audio=arquivo_audio,
                        arquivo_legenda=arquivo_legenda,
                        tts_provider=tts_provider,
                        voz_tts=voz_tts,
                        duracao=duracao
                    )
                    session.add(video)
                else:
                    return False
            else:
                video.arquivo_audio = arquivo_audio
                video.arquivo_legenda = arquivo_legenda
                video.tts_provider = tts_provider
                video.voz_tts = voz_tts
                if duracao:
                    video.duracao = duracao
            
            session.commit()
            
            # Atualiza status do roteiro
            roteiro = session.get(Roteiro, roteiro_id)
            if roteiro:
                roteiro.audio_gerado = True
            
            session.commit()
            return True
    
    def atualizar_video_renderizado(self, 
                                  roteiro_id: int, 
                                  arquivo_video: str,
                                  audio_mixado: str = None) -> bool:
        """Atualiza informações de vídeo renderizado"""
        with Session(self.engine) as session:
            video = self.buscar_video_por_roteiro_id(roteiro_id)
            if video:
                video.arquivo_video = arquivo_video
                if audio_mixado:
                    video.audio_mixado = audio_mixado
                
                session.commit()
                
                # Atualiza status do roteiro
                roteiro = session.get(Roteiro, roteiro_id)
                if roteiro:
                    roteiro.video_gerado = True
                
                session.commit()
                return True
            return False
    
    # --- Operações para YouTube ---
    def criar_video_youtube(self, 
                          video_id: int,
                          tipo_conteudo: str = "short",
                          hora_upload: datetime = None) -> VideoYouTube:
        
        with Session(self.engine) as session:
            youtube = VideoYouTube(
                video_id=video_id,
                tipo_conteudo=tipo_conteudo,
                hora_upload=hora_upload or datetime.now()
            )
            
            session.add(youtube)
            session.commit()
            session.refresh(youtube)
            return youtube
    
    # --- Operações para TikTok ---
    def criar_video_tiktok(self, 
                          video_id: int,
                          hora_upload: datetime = None) -> VideoTikTok:
        
        with Session(self.engine) as session:
            tiktok = VideoTikTok(
                video_id=video_id,
                hora_upload=hora_upload or datetime.now()
            )
            
            session.add(tiktok)
            session.commit()
            session.refresh(tiktok)
            return tiktok
    
    # --- Estatísticas ---
    def estatisticas_canal(self, canal_nome: str) -> Dict[str, Any]:
        with Session(self.engine) as session:
            canal = self.buscar_canal_por_nome(canal_nome)
            if not canal:
                return {}
            
            roteiros = self.buscar_roteiros_por_canal(canal_nome)
            total_roteiros = len(roteiros)
            com_audio = len([r for r in roteiros if r.audio_gerado])
            com_video = len([r for r in roteiros if r.video_gerado])
            
            return {
                "total_roteiros": total_roteiros,
                "roteiros_com_audio": com_audio,
                "roteiros_com_video": com_video,
                "taxa_audio": f"{(com_audio/total_roteiros)*100:.1f}%" if total_roteiros > 0 else "0%",
                "taxa_video": f"{(com_video/total_roteiros)*100:.1f}%" if total_roteiros > 0 else "0%"
            }