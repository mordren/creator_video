#!/usr/bin/env python3
import argparse
import json
import sys
import random
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.append(str(Path(__file__).parent))

from read_config import carregar_config_canal
from providers.base_texto import make_provider
from utils import count_words, extract_json_maybe, obter_proximo_id
from crud.roteiro_manager import RoteiroManager
from crud.canal_manager import CanalManager
from crud.models import Roteiro, Canal

class TextGenerator:
    def __init__(self):
        self.roteiro_manager = RoteiroManager()
        self.canal_manager = CanalManager()

    def gerar_roteiro(self, canal: str, linha_tema: Optional[str] = None, provider: Optional[str] = None) -> Dict[str, Any]:
        """Gera um roteiro completo"""
        config = carregar_config_canal(canal)
        provider_name = provider or config.get('TEXT_PROVIDER', 'gemini')
        
        # Carrega tema aleatório se não especificado
        if not linha_tema:
            temas_file = config['PASTA_CANAL'] / config.get('TEMAS_FILE', 'temas.txt')
            try:
                temas = [t.strip() for t in temas_file.read_text(encoding='utf-8').split('\n') if t.strip()]
                linha_tema = random.choice(temas) if temas else "Reflexão Filosófica"
                print(f"🎲 Tema aleatório: {linha_tema}")
            except Exception as e:
                print(f"❌ Erro ao carregar temas: {e}")
                return None

        # Prepara prompt
        partes = [p.strip() for p in linha_tema.split(',', 1)]
        tema = partes[0]
        autor = partes[1] if len(partes) > 1 else "Reflexão Filosófica"
        
        prompt = self._construir_prompt(config, tema, autor)
        if not prompt:
            return None
        
        # Gera conteúdo
        try:
            texto_provider = make_provider(provider_name)
            resultado = texto_provider.generate(prompt)
            dados_json = extract_json_maybe(resultado)
            
            # Ajusta tamanho se necessário
            dados_json = self._ajustar_tamanho_texto(dados_json, config.get('TAMANHO_MAX', 135), texto_provider)
            
            # Adiciona metadados
            dados_json.update({
                'canal': canal,
                'linha_tema': linha_tema,
                'provider': provider_name
            })
            
            return dados_json
        except Exception as e:
            print(f"❌ Erro na geração do roteiro: {e}")
            return None

    def _construir_prompt(self, config: Dict[str, Any], tema: str, autor: str) -> str:
        """Constroi o prompt personalizado"""
        try:
            agente_file = config['PASTA_CANAL'] / config.get('AGENTE_FILE', 'agente.txt')
            template = agente_file.read_text(encoding='utf-8')
            
            schema_file = config['PASTA_CANAL'] / config.get('SCHEMA_FILE', 'schema.json')
            schema_data = json.loads(schema_file.read_text(encoding='utf-8'))
            
            substituicoes = {
                '{tema}': tema,
                '{autor}': autor,
                '{TAMANHO_MAX}': str(config.get('TAMANHO_MAX', 135)),
                '{campos_obrigatorios}': str(schema_data.get('campos_obrigatorios', [])),
                '{exemplo_resposta}': schema_data.get('exemplo_resposta', '')
            }
            
            for placeholder, valor in substituicoes.items():
                template = template.replace(placeholder, str(valor))
            
            return template
        except Exception as e:
            print(f"❌ Erro ao construir prompt: {e}")
            return ""

    def _ajustar_tamanho_texto(self, dados_json: Dict[str, Any], tamanho_alvo: int, provider) -> Dict[str, Any]:
        """Ajusta o texto para o tamanho desejado"""
        faixa = [int(tamanho_alvo * 0.9), int(tamanho_alvo * 1.1)]
        texto_atual = dados_json.get('texto', '')
        
        for tentativa in range(3):  # Máximo 3 tentativas
            palavras = count_words(texto_atual)
            if faixa[0] <= palavras <= faixa[1]:
                break
                
            print(f"📏 Ajustando tamanho ({palavras} palavras, alvo: {tamanho_alvo})")
            
            if palavras < faixa[0]:
                prompt = f"Expanda este texto para cerca de {tamanho_alvo} palavras: {texto_atual}"
            else:
                prompt = f"Reduza este texto para cerca de {tamanho_alvo} palavras: {texto_atual}"
            
            try:
                novo_resultado = provider.generate(prompt)
                dados_json = extract_json_maybe(novo_resultado)
                texto_atual = dados_json.get('texto', '')
            except Exception as e:
                print(f"⚠️ Erro no ajuste de tamanho: {e}")
                break
        
        return dados_json

    def salvar_roteiro(self, dados: Dict, config: Dict) -> Dict:
        """Salva roteiro completo (arquivos + banco)"""
        try:
            pasta_base = Path(config['PASTA_BASE'])
            roteiro_id = dados.get('id_roteiro') or obter_proximo_id(pasta_base)
            pasta_roteiro = pasta_base / roteiro_id
            
            # Cria pasta e salva arquivos
            pasta_roteiro.mkdir(parents=True, exist_ok=True)
            dados['id_roteiro'] = roteiro_id
            
            # Salva JSON
            caminho_json = pasta_roteiro / f"{roteiro_id}.json"
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            
            # Salva TXT
            caminho_txt = pasta_roteiro / f"{roteiro_id}.txt"
            with open(caminho_txt, 'w', encoding='utf-8') as f:
                f.write(dados.get("texto_pt", dados.get("texto", "")))
            
            # Salva no banco - CORREÇÃO AQUI
            canal = self.canal_manager.buscar_por_nome(config.get('NOME'))
            if not canal:
                # CORREÇÃO: Passa os parâmetros corretos para criar
                canal = self.canal_manager.criar(
                    nome=config.get('NOME'),
                    config_path=str(config.get('PASTA_CANAL', ''))
                )
            
            # CORREÇÃO: Cria objeto Roteiro e salva
            roteiro = Roteiro(
                id_video=roteiro_id,
                titulo=dados.get('titulo', 'Título temporário'),
                texto=dados.get('texto', ''),
                descricao=dados.get('descricao', ''),
                tags=', '.join(dados.get('tags', [])),
                thumb=dados.get('thumb', 'thumb_temporaria'),
                canal_id=canal.id,
                resolucao=config.get('RESOLUCAO', 'vertical')
            )
            
            roteiro_salvo = self.roteiro_manager.criar(roteiro)
            
            return {
                'id_roteiro': roteiro_id,
                'pasta_roteiro': pasta_roteiro,
                'arquivo_json': caminho_json,
                'arquivo_txt': caminho_txt,
                'id_banco': roteiro_salvo.id
            }
        except Exception as e:
            print(f"❌ Erro ao salvar roteiro: {e}")
            return {}

def main():
    parser = argparse.ArgumentParser(description='Gerar roteiros usando IA')
    parser.add_argument('canal', help='Nome do canal')
    parser.add_argument('linha_tema', nargs='?', help='Tema "autor, assunto" (opcional)')
    parser.add_argument('--provider', help='Provedor de IA')    
    
    args = parser.parse_args()
    
    try:
        generator = TextGenerator()
        roteiro = generator.gerar_roteiro(args.canal, args.linha_tema, args.provider)
        
        if not roteiro:
            print("❌ Falha na geração do roteiro")
            return 1
        
        print(f"🎬 Roteiro gerado: {roteiro.get('titulo', 'N/A')}")
        
        # Salva o roteiro
        config = carregar_config_canal(args.canal)
        resultado = generator.salvar_roteiro(roteiro, config)
        
        if resultado:
            print(f"💾 Salvo: {resultado['id_roteiro']} (BD: {resultado['id_banco']})")
            return 0
        else:
            print("❌ Falha ao salvar roteiro")
            return 1
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())