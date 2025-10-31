# crud/youtube_manager.py
from sqlmodel import Session, select, text
from typing import Optional
from datetime import datetime
from .models import VideoYouTube, TipoConteudo, Video
from .connection import engine

class YouTubeManager:
    def __init__(self):
        self.engine = engine

    def buscar_por_video_id(self, video_id: int) -> Optional[VideoYouTube]:
        """Busca registro do YouTube pelo ID do vídeo"""
        try:
            with Session(self.engine) as session:
                statement = select(VideoYouTube).where(VideoYouTube.video_id == video_id)
                return session.exec(statement).first()
        except Exception as e:
            print(f"⚠️ Erro ao buscar vídeo YouTube: {e}")
            return None

    def criar(self, video_youtube: VideoYouTube) -> Optional[VideoYouTube]:
        """Cria um novo registro de VideoYouTube"""
        try:
            with Session(self.engine) as session:
                session.add(video_youtube)
                session.commit()
                session.refresh(video_youtube)
                return video_youtube
        except Exception as e:
            print(f"❌ Erro ao criar registro YouTube: {e}")
            session.rollback()
            return None

    def atualizar(self, video_youtube: VideoYouTube) -> Optional[VideoYouTube]:
        """Atualiza um registro existente de VideoYouTube"""
        try:
            with Session(self.engine) as session:
                session.merge(video_youtube)
                session.commit()
                session.refresh(video_youtube)
                return video_youtube
        except Exception as e:
            print(f"❌ Erro ao atualizar registro YouTube: {e}")
            session.rollback()
            return None

    def salvar_informacoes_upload(self, roteiro_id: int, youtube_video_id: str, 
                                agendamento=None, is_short: bool = False) -> bool:
        """Salva informações do vídeo do YouTube no banco de dados após upload"""
        try:
            with Session(self.engine) as session:
                # Busca o Video pelo roteiro_id
                video_statement = select(Video).where(Video.roteiro_id == roteiro_id)
                video = session.exec(video_statement).first()
                
                if not video:
                    print(f"❌ Vídeo não encontrado para roteiro_id {roteiro_id}")
                    return False

                # Determina tipo de conteúdo
                tipo_conteudo = TipoConteudo.SHORT if is_short else TipoConteudo.LONG
                
                # Gera o link do vídeo
                link = f"https://youtu.be/{youtube_video_id}"
                
                # Busca registro existente
                video_youtube = self.buscar_por_video_id(video.id)
                
                if video_youtube:
                    # Atualiza registro existente
                    video_youtube.youtube_video_id = youtube_video_id
                    video_youtube.link = link
                    video_youtube.hora_upload = datetime.utcnow()
                    video_youtube.tipo_conteudo = tipo_conteudo
                    
                    # Se houver agendamento, define hora_estreia
                    if agendamento:
                        data_publicacao = datetime.strptime(agendamento.data_publicacao, '%Y-%m-%d')
                        hora_publicacao = datetime.strptime(agendamento.hora_publicacao, '%H:%M').time()
                        video_youtube.hora_estreia = datetime.combine(data_publicacao, hora_publicacao)
                    
                    self.atualizar(video_youtube)
                    print(f"📝 Informações do YouTube atualizadas (ID: {video_youtube.id})")
                else:
                    # Prepara dados para novo registro
                    dados_youtube = {
                        'video_id': video.id,
                        'youtube_video_id': youtube_video_id,
                        'link': link,
                        'hora_upload': datetime.utcnow(),
                        'tipo_conteudo': tipo_conteudo
                    }
                    
                    # Se houver agendamento, define hora_estreia
                    if agendamento:
                        data_publicacao = datetime.strptime(agendamento.data_publicacao, '%Y-%m-%d')
                        hora_publicacao = datetime.strptime(agendamento.hora_publicacao, '%H:%M').time()
                        dados_youtube['hora_estreia'] = datetime.combine(data_publicacao, hora_publicacao)
                    
                    # Cria novo registro
                    video_youtube = VideoYouTube(**dados_youtube)
                    self.criar(video_youtube)
                    print(f"📹 Novo registro YouTube criado (ID: {video_youtube.id})")
                
                print(f"🔗 Link do vídeo: {link}")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao salvar informações do YouTube: {e}")
            import traceback
            traceback.print_exc()
            return False

    def verificar_tabela(self) -> bool:
        """Verifica se a tabela tem as colunas necessárias"""
        try:
            with Session(self.engine) as session:
                # Tenta buscar um registro com as novas colunas
                session.execute(text("SELECT youtube_video_id, link FROM videoyoutube LIMIT 1"))
                return True
        except Exception as e:
            print(f"❌ Tabela não tem as colunas necessárias: {e}")
            return False
        
    def buscar_por_id(self, youtube_id: int) -> Optional[VideoYouTube]:
        """Busca registro do YouTube pelo ID"""
        try:
            with Session(self.engine) as session:
                return session.get(VideoYouTube, youtube_id)
        except Exception as e:
            print(f"⚠️ Erro ao buscar YouTube por ID: {e}")
            return None
        
    def atualizar_campos(self, youtube_id: int, **dados) -> bool:
        """Atualiza campos específicos do registro YouTube"""
        try:
            with Session(self.engine) as session:
                youtube_info = session.get(VideoYouTube, youtube_id)
                if not youtube_info:
                    return False
                
                for campo, valor in dados.items():
                    if hasattr(youtube_info, campo):
                        setattr(youtube_info, campo, valor)
                
                session.commit()
                return True
        except Exception as e:
            print(f"❌ Erro ao atualizar YouTube: {e}")
            session.rollback()
            return False
        
    def deletar(self, youtube_id: int) -> bool:
        """Remove registro do YouTube"""
        try:
            with Session(self.engine) as session:
                youtube_info = session.get(VideoYouTube, youtube_id)
                if not youtube_info:
                    return False
                
                session.delete(youtube_info)
                session.commit()
                return True
        except Exception as e:
            print(f"❌ Erro ao deletar YouTube: {e}")
            session.rollback()
            return False