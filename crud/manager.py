from sqlmodel import Session, select, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

# Importa do mesmo pacote
from .models import Roteiro, Canal, Plataforma, StatusVideo
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
                    titulo_a: str = None,
                    titulo_b: str = None,
                    titulo_escolhido: str = None,
                    texto: str = None,
                    descricao: str = None,
                    tags: str = None,
                    thumb_a: str = "",
                    thumb_b: str = "", 
                    thumb_escolhida: str = "",
                    canal_id: int = None,
                    arquivo_audio: str = None,
                    tts_provider: str = None,
                    voz_tts: str = None,
                    audio_gerado: bool = False,
                    arquivo_legenda: str = None,
                    vertical: bool = True) -> Roteiro:
        
        with Session(self.engine) as session:
            # Garante valores padrão para evitar NULL
            roteiro = Roteiro(
                id_video=id_video,
                titulo_a=titulo_a or "",
                titulo_b=titulo_b or "",
                titulo_escolhido=titulo_escolhido or "",
                texto=texto or "",
                descricao=descricao or "",
                tags=tags or "",
                thumb_a=thumb_a or "",
                thumb_b=thumb_b or "",
                thumb_escolhida=thumb_escolhida or "",
                canal_id=canal_id,
                arquivo_audio=arquivo_audio or "",  # ✅ String vazia em vez de None
                tts_provider=tts_provider or "",    # ✅ String vazia em vez de None
                voz_tts=voz_tts or "",              # ✅ String vazia em vez de None
                audio_gerado=audio_gerado,
                arquivo_legenda=arquivo_legenda or "",  # ✅ String vazia em vez de None
                vertical=vertical
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
    
    def atualizar_audio_roteiro(self, roteiro_id: int, arquivo_audio: str, provider: str) -> bool:
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)
            if roteiro:
                roteiro.arquivo_audio = arquivo_audio
                roteiro.tts_provider = provider
                roteiro.audio_gerado = True
                session.commit()
                return True
            return False
    
    def atualizar_roteiro_audio(self, id_roteiro: int, arquivo_audio: str, tts_provider: str, voz_tts: str, arquivo_legenda: str = None):
        """Atualiza informações de áudio do roteiro incluindo a voz TTS e legenda"""
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, id_roteiro)
            if roteiro:
                roteiro.arquivo_audio = arquivo_audio
                roteiro.tts_provider = tts_provider
                roteiro.voz_tts = voz_tts
                if arquivo_legenda:
                    roteiro.arquivo_legenda = arquivo_legenda
                session.commit()
                return True
            return False
    
    def atualizar_titulos_ab(self, roteiro_id: int, titulo_a: str, titulo_b: str) -> bool:
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)
            if roteiro:
                roteiro.titulo_a = titulo_a
                roteiro.titulo_b = titulo_b
                session.commit()
                return True
            return False
    
    def escolher_titulo_ab(self, roteiro_id: int, titulo_escolhido: str) -> bool:
        with Session(self.engine) as session:
            roteiro = session.get(Roteiro, roteiro_id)
            if roteiro:
                roteiro.titulo_escolhido = titulo_escolhido
                session.commit()
                return True
            return False
    
    # --- Estatísticas ---
    def estatisticas_canal(self, canal_nome: str) -> Dict[str, Any]:
        with Session(self.engine) as session:
            canal = self.buscar_canal_por_nome(canal_nome)
            if not canal:
                return {}
            
            roteiros = self.buscar_roteiros_por_canal(canal_nome)
            total_roteiros = len(roteiros)
            com_audio = len([r for r in roteiros if r.audio_gerado])
            
            return {
                "total_roteiros": total_roteiros,
                "roteiros_com_audio": com_audio,
                "taxa_conversao": f"{(com_audio/total_roteiros)*100:.1f}%" if total_roteiros > 0 else "0%"
            }