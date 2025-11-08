
from sqlmodel import SQLModel, Field, Relationship, select
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import relationship

# Importa a conexão centralizada
from .connection import engine, criar_tabelas, get_session


class Canal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(unique=True, index=True)
    config_path: str
    link: Optional[str] = Field(default=None, sa_type=Text)
    ativo: bool = True
    data_criacao: datetime = Field(default_factory=datetime.now)    
    
    roteiros: List["Roteiro"] = Relationship(
        back_populates="canal_obj",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

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
    id_video: str = Field(index=True, sa_type=Text)
    titulo: str = Field(sa_type=Text)
    texto: str = Field(sa_type=Text)
    descricao: str = Field(sa_type=Text)
    tags: str = Field(sa_type=Text)
    thumb: str = Field(sa_type=Text)
    canal_id: int = Field(foreign_key="canal.id")
    canal_obj: Optional["Canal"] = Relationship(back_populates="roteiros")
    
    # Campos de processamento de vídeo (antiga tabela Video)
    arquivo_audio: Optional[str] = Field(default=None, sa_type=Text)
    arquivo_legenda: Optional[str] = Field(default=None, sa_type=Text)
    arquivo_video: Optional[str] = Field(default=None, sa_type=Text)
    audio_mixado: Optional[str] = Field(default=None, sa_type=Text)
    tts_provider: Optional[str] = Field(default=None, sa_type=Text)
    voz_tts: Optional[str] = Field(default=None, sa_type=Text)
    duracao: Optional[int] = Field(default=None)
    
    # Status e flags
    audio_gerado: bool = False
    video_gerado: bool = False
    finalizado: bool = False
    status_upload: StatusUpload = Field(default=StatusUpload.RASCUNHO)
    
    # Métricas
    visualizacao_total: int = Field(default=0)
    
    # Configurações
    resolucao: Optional[str] = Field(default="vertical", sa_type=Text)
    data_criacao: datetime = Field(default_factory=datetime.now)
    
    # Relação com YouTube - CORRIGIDA
    youtube: Optional["VideoYouTube"] = Relationship(
        back_populates="roteiro_obj",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "uselist": False  # Para relação 1:1
        }
    )
    
    # Relação com agendamentos
    agendamentos: List["Agendamento"] = Relationship(back_populates="roteiro_obj")

class VideoYouTube(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roteiro_id: int = Field(
        foreign_key="roteiro.id", 
        unique=True,
        nullable=False
    )
    
    # Link do vídeo no YouTube
    link: Optional[str] = Field(default=None, sa_type=Text)
    
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
    
    # Relação corrigida
    roteiro_obj: Optional["Roteiro"] = Relationship(back_populates="youtube")


class Agendamento(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roteiro_id: int = Field(foreign_key="roteiro.id")
    plataformas: str  # JSON string para armazenar múltiplas plataformas
    data_publicacao: str  # YYYY-MM-DD
    hora_publicacao: str  # HH:MM
    recorrente: bool = Field(default=False)
    status: str = Field(default="agendado")  # agendado, publicado, cancelado
    
    # Campos de auditoria
    data_criacao: datetime = Field(default_factory=datetime.utcnow)
    data_atualizacao: datetime = Field(default_factory=datetime.utcnow)
    
    # Relação com roteiro
    roteiro_obj: Optional["Roteiro"] = Relationship(back_populates="agendamentos")

class AgendamentoExecutado(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agendamento_id: int = Field(foreign_key="agendamento.id")
    data_execucao: Optional[datetime] = Field(default=None)
    roteiro_id: int = Field(foreign_key="roteiro.id")
    sucesso: bool = True
    data_criacao: datetime = Field(default_factory=datetime.now)

