# connection.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de conexão com banco de dados PostgreSQL
"""

import os
from sqlmodel import create_engine, SQLModel, Session, text
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url

    # mantém o fallback por variáveis soltas (melhor usar MAIÚSCULAS no .env)
    user = os.getenv("user") or os.getenv("USER")
    password = os.getenv("password") or os.getenv("PASSWORD")
    host = os.getenv("host") or os.getenv("HOST")
    port = os.getenv("port") or os.getenv("PORT")
    dbname = os.getenv("dbname") or os.getenv("DBNAME")

    if all([user, password, host, port, dbname]):
        return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

    print("⚠️  Usando SQLite local (postgresql não configurado)")
    return "sqlite:///creator_video.db"

# ===== Engine robusta contra conexões “stale” =====
_DB_URL = get_database_url()
_IS_PG = _DB_URL.startswith("postgresql")

_engine_kwargs = dict(
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,    # <- testa a conexão antes de emprestar do pool
)

if _IS_PG:
    _engine_kwargs.update(
        pool_recycle=1800,  # <- recicla conexões antigas (em segundos)
        connect_args={
            "connect_timeout": 5,
            # TCP keepalives (psycopg2/libpq)
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )

engine = create_engine(_DB_URL, **_engine_kwargs)

def test_connection():
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1")).first()
        print("✅ Conexão OK:", "PostgreSQL" if _IS_PG else "SQLite")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão com o banco: {e}")
        # recicla o pool para evitar conexões zumbis em próximas tentativas
        try:
            engine.dispose()
        except Exception:
            pass
        return False

def criar_tabelas():
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Tabelas criadas/verificadas com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def get_session():
    # sessão curtinha; abra/feche no ponto de uso
    return Session(engine)

def recriar_tabelas():
    try:
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        print("✅ Tabelas recriadas com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao recriar tabelas: {e}")
        return False
