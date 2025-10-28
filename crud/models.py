from sqlmodel import SQLModel, Field, Relationship, select
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from sqlalchemy import Text

# Importa a conexão centralizada
from .connection import engine, criar_tabelas, get_session


class Canal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(unique=True, index=True)
    config_path: str
    link: Optional[str] = Field(default=None, sa_type=Text)
    ativo: bool = True
    data_criacao: datetime = Field(default_factory=datetime.now)    
    
    roteiros: List["Roteiro"] = Relationship(back_populates="canal_obj")

class StatusUpload(str, Enum):
    RASCUNHO = "rascunho"
    ENVIANDO = "enviando" 
    PUBLICADO = "publicado"
    ERRO = "erro"

class TipoConteudo(str, Enum):
    SHORT = "short"
    LONG = "long"
    REEL = "reel"

class Roteiro(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_video: str = Field(unique=True, index=True)  # ID interno do canal
    titulo: str = Field(sa_type=Text)
    texto: str = Field(sa_type=Text)
    descricao: str = Field(sa_type=Text)
    tags: str = Field(sa_type=Text)
    thumb: str = Field(sa_type=Text)
    canal_id: int = Field(foreign_key="canal.id")
    canal_obj: Canal = Relationship(back_populates="roteiros")
    audio_gerado: bool = False
    video_gerado: bool = False
    finalizado: bool = False
    data_criacao: datetime = Field(default_factory=datetime.now)
    resolucao: Optional[str] = Field(default="vertical", sa_type=Text) 
    
    # Relação 1:1 com Video
    video: Optional["Video"] = Relationship(back_populates="roteiro")

class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roteiro_id: int = Field(foreign_key="roteiro.id", unique=True)
    
    # Metadados do vídeo    
    arquivo_audio: Optional[str] = Field(default=None, sa_type=Text)
    arquivo_legenda: Optional[str] = Field(default=None, sa_type=Text)
    arquivo_video: Optional[str] = Field(default=None, sa_type=Text)
    audio_mixado: Optional[str] = Field(default=None, sa_type=Text)
    tts_provider: Optional[str] = Field(default=None, sa_type=Text)
    voz_tts: Optional[str] = Field(default=None, sa_type=Text)
    duracao: Optional[int] = Field(default=None)  # em segundos
    status_upload: StatusUpload = Field(default=StatusUpload.RASCUNHO)
    
    # Métricas consolidadas (soma de todas as plataformas)
    visualizacao_total: int = Field(default=0)
    
    data_criacao: datetime = Field(default_factory=datetime.now)
    
    # Relações
    roteiro: Roteiro = Relationship(back_populates="video")
    youtube: Optional["VideoYouTube"] = Relationship(back_populates="video")
    tiktok: Optional["VideoTikTok"] = Relationship(back_populates="video")

class VideoYouTube(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="video.id")
    
    # Timestamps
    hora_upload: Optional[datetime] = Field(default=None)
    hora_estreia: Optional[datetime] = Field(default=None)
    
    # Métricas
    visualizacoes: int = Field(default=0)
    likes: int = Field(default=0)
    comentarios: int = Field(default=0)
    impressoes: Optional[int] = Field(default=0)
    
    # Tipo de conteúdo
    tipo_conteudo: TipoConteudo = Field(default=TipoConteudo.SHORT)
    
    video: Video = Relationship(back_populates="youtube")

class VideoTikTok(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="video.id")
    
    # Timestamps
    hora_upload: Optional[datetime] = Field(default=None)
    hora_estreia: Optional[datetime] = Field(default=None)
    
    # Métricas básicas (sem API oficial)
    visualizacoes: int = Field(default=0)
    likes: int = Field(default=0)
    
    video: Video = Relationship(back_populates="tiktok")

class Agendamento(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    canal: str
    plataforma: str
    dia_da_semana: int  # 0-6 (domingo=0, sábado=6)
    hora: str  # formato 'HH:MM'
    tipo_video: str  # 'short' ou 'long'
    ativo: bool = True

class AgendamentoExecutado(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agendamento_id: int = Field(foreign_key="agendamento.id")
    data_execucao: Optional[datetime] = Field(default=None)  # data em que foi executado
    roteiro_id: int = Field(foreign_key="roteiro.id")
    sucesso: bool = True
    data_criacao: datetime = Field(default_factory=datetime.now)