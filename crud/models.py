from sqlmodel import SQLModel, Field, Relationship, select
from typing import Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy import Text

# Importa a conexão centralizada
from .connection import engine, criar_tabelas, get_session

class Plataforma(str, Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"

class StatusVideo(str, Enum):
    RASCUNHO = "rascunho"
    AGENDADO = "agendado"
    PUBLICADO = "publicado"
    ARQUIVADO = "arquivado"

class Canal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(unique=True, index=True)
    config_path: str
    ativo: bool = True
    data_criacao: datetime = Field(default_factory=datetime.now)
    
    roteiros: List["Roteiro"] = Relationship(back_populates="canal_obj")

class Roteiro(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_video: str = Field(unique=True, index=True)
    
    titulo_a: str = Field(sa_type=Text)
    titulo_b: Optional[str] = Field(default=None, sa_type=Text)
    titulo_escolhido: Optional[str] = Field(default=None, sa_type=Text)
    
    texto: str = Field(sa_type=Text)
    descricao: str = Field(sa_type=Text)
    tags: str = Field(sa_type=Text)
    
    thumb_a: str = Field(sa_type=Text)
    thumb_b: Optional[str] = Field(default=None, sa_type=Text)
    thumb_escolhida: Optional[str] = Field(default=None, sa_type=Text)
    
    canal_id: int = Field(foreign_key="canal.id")
    canal_obj: Canal = Relationship(back_populates="roteiros")
    
    # ✅ CORREÇÃO: Torna essas colunas opcionais
    arquivo_audio: Optional[str] = Field(default=None, sa_type=Text)
    arquivo_legenda: Optional[str] = Field(default=None, sa_type=Text)
    tts_provider: Optional[str] = Field(default=None, sa_type=Text)
    voz_tts: Optional[str] = Field(default=None, sa_type=Text)
    audio_gerado: bool = False
    video_gerado: bool = False    
    
    data_criacao: datetime = Field(default_factory=datetime.now)
    vertical: bool = True