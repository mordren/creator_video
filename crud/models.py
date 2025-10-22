from sqlmodel import SQLModel, Field, Relationship, select
from typing import Optional, List
from datetime import datetime
from enum import Enum

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
    titulo_a: str
    titulo_b: Optional[str] = None
    titulo_escolhido: Optional[str] = None
    
    texto_pt: str
    texto_en: str = ""
    descricao: str = ""
    tags: str = ""
    
    thumb_a: str = ""
    thumb_b: Optional[str] = None
    thumb_escolhida: Optional[str] = None
    
    canal_id: int = Field(foreign_key="canal.id")
    canal_obj: Canal = Relationship(back_populates="roteiros")
    
    arquivo_audio: str = ""
    tts_provider: str = ""
    voz_tts: str = ""
    audio_gerado: bool = False
    arquivo_legenda: str = ""
    
    data_criacao: datetime = Field(default_factory=datetime.now)
    vertical: bool = True

# Remove as funções get_engine e criar_tabelas duplicadas
# Agora usamos as do connection.py