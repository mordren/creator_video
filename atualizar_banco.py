#!/usr/bin/env python3
from crud.connection import recriar_tabelas

if __name__ == "__main__":
    print("🔄 Recriando tabelas do banco...")
    if recriar_tabelas():
        print("✅ Banco atualizado com sucesso!")
    else:
        print("❌ Falha ao atualizar banco")