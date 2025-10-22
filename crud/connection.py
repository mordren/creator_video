#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de conexão com banco de dados PostgreSQL
"""

import os
from sqlmodel import create_engine, SQLModel, Session, text
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

def get_database_url():
    """
    Retorna a URL de conexão com o banco de dados
    Prioridade:
    1. DATABASE_URL do ambiente
    2. Variáveis individuais do .env
    3. SQLite local (fallback)
    """
    # Se DATABASE_URL estiver definida, usa ela
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Garante que é PostgreSQL
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url
    
    # Constrói a URL a partir de variáveis individuais
    user = os.getenv("user")
    password = os.getenv("password")
    host = os.getenv("host")
    port = os.getenv("port")
    dbname = os.getenv("dbname")
    
    if all([user, password, host, port, dbname]):
        return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    # Fallback para SQLite local
    print("⚠️  Usando SQLite local (postgresql não configurado)")
    return "sqlite:///creator_video.db"

# Cria a engine de conexão
engine = create_engine(
    get_database_url(),
    echo=True,  # Define como True para ver queries SQL no console (útil para debug)
    pool_size=10,
    max_overflow=20
)

def test_connection():
    """Testa a conexão com o banco de dados"""
    try:
        with Session(engine) as session:
            # Testa com uma query simples - usando text() para queries SQL puras
            if "postgresql" in get_database_url():
                result = session.exec(text("SELECT 1"))
                result.first()  # Executa a query
                print("✅ Conexão PostgreSQL bem-sucedida!")
            else:
                result = session.exec(text("SELECT 1"))
                result.first()
                print("✅ SQLite local conectado!")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão com o banco: {e}")
        return False

def criar_tabelas():
    """Cria todas as tabelas definidas nos models"""
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Tabelas criadas/verificadas com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def get_session():
    """Retorna uma sessão do banco de dados"""
    return Session(engine)