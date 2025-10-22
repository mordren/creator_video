#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import os
from dotenv import load_dotenv

load_dotenv()

def test_host_connectivity(hostname, port=5432):
    """Testa se consegue resolver o host e conectar na porta"""
    try:
        print(f"🔍 Resolvendo host: {hostname}")
        ip = socket.gethostbyname(hostname)
        print(f"✅ Host resolvido: {hostname} -> {ip}")
        
        print(f"🔌 Testando conexão na porta {port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Porta {port} acessível!")
            return True
        else:
            print(f"❌ Porta {port} inacessível (código: {result})")
            return False
            
    except socket.gaierror:
        print(f"❌ Não foi possível resolver o host: {hostname}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def main():
    # Extrai o host da DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL não definida no .env")
        return
    
    # Extrai o host da URL
    if "://" in database_url:
        host_part = database_url.split("://")[1].split("@")[1].split("/")[0]
        hostname = host_part.split(":")[0]
        port = int(host_part.split(":")[1]) if ":" in host_part else 5432
        
        print(f"📊 Analisando conexão:")
        print(f"   URL: {database_url}")
        print(f"   Host: {hostname}")
        print(f"   Porta: {port}")
        
        if test_host_connectivity(hostname, port):
            print("\n🎉 Conectividade OK! O problema pode ser nas credenciais.")
        else:
            print("\n💥 Problema de conectividade com o Supabase.")
            print("\n🔧 Soluções possíveis:")
            print("1. Verifique sua conexão com a internet")
            print("2. Verifique se o hostname está correto")
            print("3. Teste com VPN desativada (se estiver usando)")
            print("4. Verifique firewall/antivírus")
    else:
        print("❌ DATABASE_URL em formato inválido")

if __name__ == "__main__":
    main()