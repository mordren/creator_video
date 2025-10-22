#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import os
import re
import random
import sys
import json
import argparse
from pathlib import Path
from time import sleep, time
import google.generativeai as genai

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')

from read_config import carregar_config_canal, listar_canais_disponiveis

# -------------------------- Funções Utilitárias ----------------------------
def proximo_id(pasta_base: Path) -> str:
    existentes = [p.name for p in pasta_base.iterdir()
                  if p.is_dir() and re.fullmatch(r"\d+", p.name)]
    if not existentes:
        return "1"
    numeros = [int(n) for n in existentes]
    return str(max(numeros) + 1)

def _higieniza_texto(s: str) -> str:
    if not s:
        return s

    padroes = [
        r"\*\*(.+?)\*\*", r"\*(.+?)\*", r"__(.+?)__", r"_(.+?)_",
        r"~~(.+?)~~", r"`(.+?)`"
    ]
    for pat in padroes:
        s = re.sub(pat, r"\1", s)

    s = s.replace("•", "- ").replace("·", "- ").replace("—", "- ")
    s = s.replace("–", "- ")
    s = re.sub(r"[^\S\r\n]+", " ", s)
    s = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", " ", s)
    s = re.sub(r"\s+\n", "\n", s).strip()
    return s

def _extrai_json_da_resposta(texto: str) -> str:
    """Extrai JSON de possíveis blocos de código markdown"""
    texto = re.sub(r'^```json\s*', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'\s*```$', '', texto)
    
    match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}', texto, re.DOTALL)
    if not match:
        match = re.search(r'\{.*\}', texto, re.DOTALL)
    if match:
        return match.group()
    return texto

# -------------------------- Carregamento Modular ---------------------------
def carregar_agente(config: dict) -> str:
    """Carrega o prompt do agente específico do canal"""
    agente_path = config['PASTA_CANAL'] / config.get('AGENTE_FILE', 'agente.txt')
    
    if not agente_path.exists():
        raise FileNotFoundError(f"Arquivo do agente não encontrado: {agente_path}")
    
    agente = agente_path.read_text(encoding="utf-8")
    return agente

def carregar_schema(config: dict) -> dict:
    """Carrega a definição do schema de saída"""
    schema_path = config['PASTA_CANAL'] / config.get('SCHEMA_FILE', 'schema.json')
    
    if not schema_path.exists():
        # Schema padrão para canais sem schema específico
        return {
            "tipo": "json",
            "campos_obrigatorios": ["texto_pt", "descricao", "thumb", "tags"],
            "placeholder_tema": "{tema}",
            "placeholder_tamanho": "{TAMANHO_MAX}"
        }
    
    return json.loads(schema_path.read_text(encoding="utf-8"))

def carregar_temas(config: dict) -> list:
    """Carrega lista de temas, suportando formatos diferentes"""
    temas_path = config['PASTA_CANAL'] / config.get('TEMAS_FILE', 'temas.txt')
    
    if not temas_path.exists():
        raise FileNotFoundError(f"Arquivo de temas não encontrado: {temas_path}")
    
    temas = []
    with open(temas_path, 'r', encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith('#'):
                # Suporta tanto "autor, tema" quanto apenas "tema"
                partes = linha.split(',', 1)
                if len(partes) == 2:
                    autor, tema = partes[0].strip(), partes[1].strip()
                    temas.append((autor, tema))
                else:
                    # Apenas tema, sem autor
                    temas.append(("", linha.strip()))
    
    if not temas:
        raise ValueError(f"Arquivo de temas vazio: {temas_path}")
    
    return temas

def construir_prompt_final(agente: str, schema: dict, config: dict, tema: tuple) -> str:
    """Constrói o prompt final substituindo placeholders"""
    autor, tema_texto = tema
    prompt = agente
    
    # Substitui placeholders comuns
    substituicoes = {
        schema.get('placeholder_tamanho', '{TAMANHO_MAX}'): str(config.get('TAMANHO_MAX', 260)),
        schema.get('placeholder_tema', '{tema}'): tema_texto,
        schema.get('placeholder_autor', '{autor}'): autor,
        '{IDIOMA}': config.get('IDIOMA', 'pt'),
        '{ESTILO}': config.get('ESTILO', ''),
        '{campos_obrigatorios}': ', '.join(schema.get('campos_obrigatorios', []))
    }
    
    for placeholder, valor in substituicoes.items():
        prompt = prompt.replace(placeholder, str(valor))
    
    return prompt

def processar_resposta(texto: str, schema: dict, config: dict, tema: tuple) -> dict:
    """Processa a resposta do LLM baseado no schema"""
    tipo_saida = schema.get('tipo', 'json')
    autor, tema_texto = tema
    
    if tipo_saida == 'json':
        # Tenta extrair e parsear JSON
        texto_limpo = _extrai_json_da_resposta(texto)
        
        try:
            dados = json.loads(texto_limpo)
        except json.JSONDecodeError:
            dados = {}
            chave_texto = f"texto_{config.get('IDIOMA', 'pt')}"
            dados[chave_texto] = _higieniza_texto(texto)

        for campo, valor in dados.items():
            if isinstance(valor, str) and campo.startswith('texto_'):
                dados[campo] = _higieniza_texto(valor)
        
        for campo in schema.get('campos_obrigatorios', []):
            if campo not in dados:
                dados[campo] = ""
        
    else:  # tipo_saida == 'texto'
        # Encapsula texto puro em JSON
        chave_texto = f"texto_{config.get('IDIOMA', 'pt')}"
        dados = {
            chave_texto: _higieniza_texto(texto),
            'descricao': f"{config.get('ESTILO', 'Conteúdo')} sobre {tema_texto}",
            'thumb': tema_texto.split()[:3],
            'tags': [config.get('ESTILO', 'conteúdo'), tema_texto.split()[0]]
        }
    
    # Adiciona metadados padrão
    dados.update({
        'idioma': config.get('IDIOMA', 'pt'),
        'voz_tts': config.get('VOZ_TTS', ''),
        'canal': config['PASTA_CANAL'].name,
        'tema_original': tema_texto,
        'autor_original': autor
    })
    
    return dados

def gerar_roteiro(canal: str) -> tuple:
    """Gera roteiro para qualquer canal"""
    config = carregar_config_canal(canal)

    agente = carregar_agente(config)
    schema = carregar_schema(config)
    temas = carregar_temas(config)
    
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", config.get('API_KEY')))
    model = genai.GenerativeModel(config.get('MODEL_NAME', 'gemini-2.5-flash'))

    tema = random.choice(temas)
    
    prompt = construir_prompt_final(agente, schema, config, tema)

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=1.0,
            top_p=0.9
        )
    )

    texto_resposta = (getattr(response, "text", "") or "").strip()
    
    # Processa resposta baseado no schema
    dados = processar_resposta(texto_resposta, schema, config, tema)
    
    return dados, config

def main():
    parser = argparse.ArgumentParser(description='Gerar roteiro para qualquer canal')
    parser.add_argument('canal', help='Nome do canal', choices=listar_canais_disponiveis())
    args = parser.parse_args()

    
    # Gera roteiro
    dados, config = gerar_roteiro(args.canal)
    
    # Cria pasta e salva
    nova_pasta = config['PASTA_BASE'] / proximo_id(config['PASTA_BASE'])
    nova_pasta.mkdir(parents=True, exist_ok=True)

    dados['Id'] = nova_pasta.name
    caminho_json = nova_pasta / f"{nova_pasta.name}.json"

    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    # Encontra a chave de texto para contar palavras
    chave_texto = next((k for k in dados.keys() if k.startswith('texto_')), 'texto_pt')
    palavras_count = len(dados.get(chave_texto, '').split())
    
    print(f"✅ Roteiro {config.get('ESTILO', '')} salvo em: {caminho_json}")
    print(f"📊 Canal: {dados.get('canal', '')}")
    print(f"📊 Idioma: {dados.get('idioma', 'pt')}")
    print(f"📊 Palavras: {palavras_count}")
    print(f"🔊 Voz TTS: {dados.get('voz_tts', '')}")
    print(f"--- Conteúdo ---")
    print(json.dumps(dados, ensure_ascii=False, indent=2))
    
    return caminho_json

if __name__ == "__main__":
    main()